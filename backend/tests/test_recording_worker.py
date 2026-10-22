import importlib.util
import os
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import Mock, patch


class FakeTable:
    def __init__(self):
        self.items = {}

    def put_item(self, Item, ConditionExpression=None):
        self.items[Item["meetingId"]] = Item

    def get_item(self, Key):
        item = self.items.get(Key.get("meetingId"))
        if Key.get("integrationId"):
            return {}
        return {"Item": item} if item else {}

    def update_item(self, Key, **_kwargs):
        self.items[Key["meetingId"]]["status"] = "UPLOADING"


def load_worker():
    fake_boto3 = types.ModuleType("boto3")
    fake_table = FakeTable()
    fake_boto3.client = lambda *_args, **_kwargs: object()
    fake_boto3.resource = lambda *_args, **_kwargs: types.SimpleNamespace(
        Table=lambda _name: fake_table
    )
    path = Path(__file__).resolve().parents[1] / "recording_worker.py"
    spec = importlib.util.spec_from_file_location("briefly_test_recording_worker", path)
    module = importlib.util.module_from_spec(spec)
    with patch.dict(
        os.environ,
        {
            "MEETINGS_TABLE": "meetings",
            "INTEGRATION_STATE_TABLE": "integration-state",
            "MEETINGS_BUCKET": "bucket",
            "USER_POOL_ID": "pool",
        },
    ), patch.dict(sys.modules, {"boto3": fake_boto3}):
        spec.loader.exec_module(module)
    return module


class RecordingWorkerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.worker = load_worker()

    def test_download_url_allows_only_https_provider_hosts(self):
        self.assertEqual(
            self.worker.safe_url("https://us02.zoom.us/file", "zoom.us").hostname,
            "us02.zoom.us",
        )
        for url in (
            "http://zoom.us/file",
            "https://zoom.us.attacker.example/file",
            "https://attacker.zoom.us.example/file",
            "https://user@zoom.us/file",
        ):
            with self.subTest(url=url), self.assertRaises(ValueError):
                self.worker.safe_url(url, "zoom.us")

    def test_meeting_id_is_stable_and_separated_by_provider(self):
        first = self.worker.meeting_uuid("zoom", "event-1")
        self.assertEqual(first, self.worker.meeting_uuid("zoom", "event-1"))
        self.assertNotEqual(first, self.worker.meeting_uuid("teams", "event-1"))
        self.assertEqual(len(first), 36)

    def test_zoom_recording_is_owner_scoped_and_uploaded_to_the_pipeline_prefix(self):
        table = FakeTable()
        storage = Mock()
        self.worker.meetings = table
        self.worker.s3 = storage
        self.worker.cognito = Mock(
            list_users=Mock(
                return_value={
                    "Users": [
                        {
                            "UserStatus": "CONFIRMED",
                            "Attributes": [
                                {"Name": "email", "Value": "owner@example.com"},
                                {"Name": "email_verified", "Value": "true"},
                                {"Name": "sub", "Value": "owner-sub"},
                            ],
                        }
                    ]
                }
            )
        )
        with tempfile.NamedTemporaryFile(delete=False) as media:
            media.write(b"sample audio")
            media_path = media.name
        try:
            with patch.object(self.worker, "zoom_access_token", return_value="access-token"), patch.object(
                self.worker, "fetch_to_file", return_value=media_path
            ):
                self.worker.process_recording(
                    {
                        "provider": "zoom",
                        "eventId": "event-42",
                        "ownerEmail": "owner@example.com",
                        "extension": "m4a",
                        "title": "Budget review",
                        "meetingId": "zoom-meeting-42",
                        "recordingId": "zoom-recording-42",
                        "downloadUrl": "https://zoom.us/recording",
                    }
                )
        finally:
            if os.path.exists(media_path):
                os.unlink(media_path)

        item = next(iter(table.items.values()))
        self.assertEqual(item["ownerId"], "owner-sub")
        self.assertEqual(item["sourceProvider"], "zoom")
        self.assertTrue(item["s3Key"].startswith("uploads/owner-sub/"))
        self.assertTrue(item["s3Key"].endswith(".m4a"))
        storage.upload_file.assert_called_once_with(
            media_path,
            "bucket",
            item["s3Key"],
            ExtraArgs={"ContentType": "audio/mp4"},
        )


if __name__ == "__main__":
    unittest.main()
