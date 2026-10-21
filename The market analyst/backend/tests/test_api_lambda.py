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

class FakeAttribute:
    def eq(self, _value):
        return self

    def contains(self, _value):
        return self

    def __and__(self, _other):
        return self


class FakeS3:
    def generate_presigned_url(self, operation, Params, ExpiresIn):
        return f"https://uploads.example/{operation}/{Params['Key']}?expires={ExpiresIn}"


def load_api():
    fake_boto3 = types.ModuleType("boto3")
    fake_boto3.client = lambda *_args, **_kwargs: FakeS3()
    table = FakeTable()
    fake_boto3.resource = lambda *_args, **_kwargs: types.SimpleNamespace(Table=lambda _name: table)
    fake_dynamodb = types.ModuleType("boto3.dynamodb")
    fake_conditions = types.ModuleType("boto3.dynamodb.conditions")
    fake_conditions.Attr = lambda *_args, **_kwargs: FakeAttribute()
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

    def test_api_rejects_requests_without_a_verified_cognito_identity(self):
        result = self.api.handler(
            {
                "headers": {"authorization": "Bearer incorrect-token"},
                "requestContext": {"http": {"method": "GET"}, "authorizer": {"jwt": {"claims": {}}}},
                "rawPath": "/meetings",
            },
            None,
        )

        self.assertEqual(result["statusCode"], 401)
        self.assertIn("Sign in", result["body"])

    def test_malformed_base64_request_body_returns_a_client_error(self):
        result = self.api.handler(
            {
                "body": "not base64!",
                "isBase64Encoded": True,
                "requestContext": {
                    "http": {"method": "POST"},
                    "authorizer": {"jwt": {"claims": {"sub": "12345678-1234-1234-1234-123456789abc"}}},
                },
                "rawPath": "/upload-url",
            },
            None,
        )

        self.assertEqual(result["statusCode"], 400)
        self.assertIn("valid JSON", result["body"])

    def test_user_identity_is_read_from_verified_jwt_claims(self):
        owner_id = "12345678-1234-1234-1234-123456789abc"

        self.assertEqual(
            self.api.current_user(
                {
                    "requestContext": {
                        "authorizer": {"jwt": {"claims": {"sub": owner_id}}}
                    }
                }
            ),
            owner_id,
        )

    def test_unowned_meeting_detail_is_not_disclosed(self):
        owner_id = "12345678-1234-1234-1234-123456789abc"
        self.table.items[:] = [{"meetingId": "meeting-123", "ownerId": owner_id}]
        self.table.get_item = lambda **_kwargs: {"Item": self.table.items[0]}

        with self.assertRaises(self.api.RequestError) as error:
            self.api.handle_meeting_detail(
                "meeting-123",
                "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
            )

        self.assertEqual(error.exception.status_code, 404)

    def test_upload_url_uses_a_safe_random_key_and_persists_meeting(self):
        owner_id = "12345678-1234-1234-1234-123456789abc"
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
        self.assertTrue(result["uploadUrl"].startswith("https://uploads.example/put_object/"))

    def test_upload_url_rejects_unsupported_recording_formats(self):
        with self.assertRaises(self.api.RequestError) as error:
            self.api.handle_upload_url(
                {"fileName": "agenda.pdf", "contentType": "application/pdf", "fileSize": 100},
                "12345678-1234-1234-1234-123456789abc",
            )

        self.assertEqual(error.exception.status_code, 415)


if __name__ == "__main__":
    unittest.main()
