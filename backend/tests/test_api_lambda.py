import importlib.util
import os
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import patch


class FakeTable:
    def __init__(self):
        self.items = []

    def put_item(self, Item):
        self.items.append(Item)

    def get_item(self, Key):
        item = next((record for record in self.items if record["meetingId"] == Key["meetingId"]), None)
        return {"Item": item} if item else {}


class FakeCondition:
    def __and__(self, other):
        return self


class FakeS3:
    def generate_presigned_post(self, Bucket, Key, Fields, Conditions, ExpiresIn):
        return {
            "url": "https://uploads.example/",
            "fields": {"key": Key, **Fields, "policy": "signed-policy"},
        }


def load_api():
    fake_boto3 = types.ModuleType("boto3")
    fake_boto3.client = lambda *_args, **_kwargs: FakeS3()
    table = FakeTable()
    fake_boto3.resource = lambda *_args, **_kwargs: types.SimpleNamespace(Table=lambda _name: table)
    fake_dynamodb = types.ModuleType("boto3.dynamodb")
    fake_conditions = types.ModuleType("boto3.dynamodb.conditions")
    fake_conditions.Attr = lambda *_args, **_kwargs: FakeCondition()
    path = Path(__file__).resolve().parents[1] / "api_lambda.py"
    spec = importlib.util.spec_from_file_location("briefly_test_api", path)
    module = importlib.util.module_from_spec(spec)
    with patch.dict(
        os.environ,
        {
            "MEETINGS_TABLE": "meetings",
            "SEARCH_TABLE": "search",
            "MEETINGS_BUCKET": "bucket",
        },
    ), patch.dict(
        sys.modules,
        {
            "boto3": fake_boto3,
            "boto3.dynamodb": fake_dynamodb,
            "boto3.dynamodb.conditions": fake_conditions,
        },
    ):
        spec.loader.exec_module(module)
    return module, table


class ApiLambdaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.api, cls.table = load_api()

    def test_api_rejects_requests_without_authenticated_cognito_claims(self):
        result = self.api.handler(
            {
                "requestContext": {"http": {"method": "GET"}},
                "rawPath": "/meetings",
            },
            None,
        )

        self.assertEqual(result["statusCode"], 401)
        self.assertIn("authenticated workspace account", result["body"])

    def test_upload_post_is_scoped_and_size_limited_to_authenticated_owner(self):
        owner_id = "workspace-owner"
        result = self.api.handle_upload_url(
            {
                "fileName": "..\\recordings\\Budget review.wav",
                "contentType": "audio/wav",
                "fileSize": 1024,
            },
            owner_id,
        )

        meeting = self.table.items[-1]
        self.assertEqual(meeting["fileName"], "Budget review.wav")
        self.assertTrue(meeting["s3Key"].startswith(f"uploads/{owner_id}/"))
        self.assertEqual(meeting["ownerId"], owner_id)
        self.assertEqual(meeting["status"], "UPLOADING")
        self.assertEqual(result["uploadUrl"], "https://uploads.example/")
        self.assertIn("policy", result["uploadFields"])
        self.assertEqual(result["uploadFields"]["key"], meeting["s3Key"])

    def test_upload_url_rejects_unsupported_recording_formats(self):
        with self.assertRaises(self.api.RequestError) as error:
            self.api.handle_upload_url(
                {"fileName": "agenda.pdf", "contentType": "application/pdf", "fileSize": 100},
                "workspace-owner",
            )

        self.assertEqual(error.exception.status_code, 415)

    def test_upload_url_rejects_boolean_file_size(self):
        with self.assertRaises(self.api.RequestError) as error:
            self.api.handle_upload_url(
                {"fileName": "recording.wav", "contentType": "audio/wav", "fileSize": True},
                "workspace-owner",
            )

        self.assertEqual(error.exception.status_code, 413)

    def test_upload_url_rejects_malformed_content_type(self):
        with self.assertRaises(self.api.RequestError) as error:
            self.api.handle_upload_url(
                {"fileName": "recording.wav", "contentType": {"invalid": "type"}, "fileSize": 100},
                "workspace-owner",
            )

        self.assertEqual(error.exception.status_code, 400)

    def test_meeting_detail_is_not_visible_to_a_different_owner(self):
        self.table.items.append({
            "meetingId": "12345678-1234-1234-1234-123456789abc",
            "ownerId": "owner-one",
            "s3Key": "uploads/owner-one/12345678-1234-1234-1234-123456789abc.wav",
        })

        with self.assertRaises(self.api.RequestError) as error:
            self.api.handle_meeting_detail(
                "12345678-1234-1234-1234-123456789abc",
                "owner-two",
            )

        self.assertEqual(error.exception.status_code, 404)


if __name__ == "__main__":
    unittest.main()
