import importlib.util
import json
import os
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import patch


class FakeSecrets:
    def get_secret_value(self, SecretId):
        values = {
            "zoom-secret": "zoom-verification-secret",
            "teams-secret": json.dumps({"client_state": "a" * 32}),
        }
        return {"SecretString": values[SecretId]}


class FakeQueue:
    def __init__(self):
        self.messages = []

    def send_message(self, QueueUrl, MessageBody):
        self.messages.append(json.loads(MessageBody))


def load_webhooks():
    fake_boto3 = types.ModuleType("boto3")
    fake_queue = FakeQueue()
    fake_boto3.client = lambda service, **_kwargs: (
        FakeSecrets() if service == "secretsmanager" else fake_queue
    )
    path = Path(__file__).resolve().parents[1] / "platform_webhooks.py"
    spec = importlib.util.spec_from_file_location("briefly_test_platform_webhooks", path)
    module = importlib.util.module_from_spec(spec)
    with patch.dict(
        os.environ,
        {
            "ZOOM_WEBHOOK_SECRET_ARN": "zoom-secret",
            "TEAMS_GRAPH_SECRET_ARN": "teams-secret",
            "INTEGRATION_QUEUE_URL": "https://sqs.example/queue",
        },
    ), patch.dict(sys.modules, {"boto3": fake_boto3}):
        spec.loader.exec_module(module)
    return module, fake_queue


class PlatformWebhookTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.webhooks, cls.queue = load_webhooks()

    def test_zoom_signature_rejects_stale_timestamp_and_accepts_valid_signature(self):
        body = '{"event":"recording.completed"}'
        timestamp = "1700000000"
        message = f"v0:{timestamp}:{body}".encode()
        import hashlib
        import hmac

        signature = "v0=" + hmac.new(
            b"zoom-verification-secret", message, hashlib.sha256
        ).hexdigest()
        headers = {
            "x-zm-request-timestamp": timestamp,
            "x-zm-signature": signature,
        }

        self.assertTrue(
            self.webhooks.zoom_signature_is_valid(headers, body, "zoom-verification-secret", 1700000000)
        )
        self.assertFalse(
            self.webhooks.zoom_signature_is_valid(headers, body, "zoom-verification-secret", 1700001000)
        )

    def test_zoom_recording_webhook_is_verified_then_queued(self):
        body = json.dumps(
            {
                "event": "recording.completed",
                "event_id": "zoom-event-1",
                "payload": {
                    "object": {
                        "id": "meeting-123",
                        "host_email": "host@example.com",
                        "topic": "Budget review",
                        "recording_files": [
                            {
                                "id": "audio-1",
                                "file_type": "M4A",
                                "download_url": "https://zoom.us/audio",
                                "recording_type": "audio_only",
                            },
                            {
                                "id": "video-1",
                                "file_type": "MP4",
                                "download_url": "https://zoom.us/video",
                                "recording_type": "shared_screen_with_speaker_view",
                            },
                        ],
                    }
                },
            }
        )
        timestamp = str(int(__import__("time").time()))
        message = f"v0:{timestamp}:{body}".encode()
        import hashlib
        import hmac

        signature = "v0=" + hmac.new(
            b"zoom-verification-secret", message, hashlib.sha256
        ).hexdigest()
        with patch.dict(
            os.environ,
            {
                "ZOOM_WEBHOOK_SECRET_ARN": "zoom-secret",
                "INTEGRATION_QUEUE_URL": "https://sqs.example/queue",
            },
        ):
            result = self.webhooks.handler(
                {
                    "requestContext": {"http": {"method": "POST"}},
                    "rawPath": "/webhooks/zoom",
                    "headers": {
                        "x-zm-request-timestamp": timestamp,
                        "x-zm-signature": signature,
                    },
                    "body": body,
                },
                None,
            )

        self.assertEqual(result["statusCode"], 202)
        self.assertEqual(len(self.queue.messages), 1)
        self.assertEqual(self.queue.messages[0]["provider"], "zoom")
        self.assertEqual(self.queue.messages[0]["ownerEmail"], "host@example.com")
        self.assertEqual(self.queue.messages[0]["recordingId"], "video-1")

    def test_teams_validation_handshake_returns_plain_text_token(self):
        result = self.webhooks.handler(
            {
                "requestContext": {"http": {"method": "POST"}},
                "rawPath": "/webhooks/teams",
                "queryStringParameters": {"validationToken": "challenge-token"},
                "body": "",
            },
            None,
        )

        self.assertEqual(result["statusCode"], 200)
        self.assertEqual(result["body"], "challenge-token")
        self.assertEqual(result["headers"]["content-type"], "text/plain; charset=utf-8")

    def test_teams_notifications_require_client_state_and_queue_recording_ids(self):
        valid = self.webhooks.teams_notifications(
            {
                "value": [
                    {
                        "subscriptionId": "sub-1",
                        "clientState": "a" * 32,
                        "changeType": "created",
                        "resource": (
                            "users('organizer-1')/onlineMeetings('meeting-1')/"
                            "recordings('recording-1')"
                        ),
                        "resourceData": {"id": "recording-1"},
                    }
                ]
            },
            "a" * 32,
        )
        self.assertEqual(valid[0]["organizerId"], "organizer-1")
        self.assertEqual(valid[0]["platformMeetingId"], "meeting-1")
        self.assertEqual(valid[0]["recordingId"], "recording-1")

        with self.assertRaises(PermissionError):
            self.webhooks.teams_notifications(
                {"value": [{"clientState": "wrong"}]}, "a" * 32
            )


if __name__ == "__main__":
    unittest.main()
