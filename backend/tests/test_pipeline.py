import importlib.util
import os
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import patch


class FakeWriter:
    def __init__(self):
        self.items = []

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def put_item(self, Item):
        self.items.append(Item)


class FakeTable:
    def __init__(self):
        self.writer = FakeWriter()
        self.item = None
        self.updated = False

    def batch_writer(self, **_kwargs):
        return self.writer

    def get_item(self, Key):
        return {"Item": self.item} if self.item else {}

    def update_item(self, **_kwargs):
        self.updated = True


class FakeS3:
    def __init__(self):
        self.head_calls = 0

    def head_object(self, **_kwargs):
        self.head_calls += 1
        return {"ContentLength": 1024}


def load_pipeline():
    fake_boto3 = types.ModuleType("boto3")
    fake_boto3.client = lambda *_args, **_kwargs: object()
    fake_boto3.resource = lambda *_args, **_kwargs: types.SimpleNamespace(
        Table=lambda _name: FakeTable()
    )
    fake_dynamodb = types.ModuleType("boto3.dynamodb")
    fake_conditions = types.ModuleType("boto3.dynamodb.conditions")
    fake_conditions.Attr = lambda *_args, **_kwargs: None
    path = Path(__file__).resolve().parents[1] / "pipeline.py"
    spec = importlib.util.spec_from_file_location("briefly_test_pipeline", path)
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
    return module


class PipelineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pipeline = load_pipeline()

    def test_transcript_keeps_speaker_labels_timestamps_and_punctuation(self):
        result = {
            "results": {
                "speaker_labels": {
                    "speakers": [{"speaker_label": "spk_0"}, {"speaker_label": "spk_1"}],
                    "segments": [
                        {
                            "speaker_label": "spk_0",
                            "items": [{"start_time": "0.00"}, {"start_time": "0.31"}],
                        },
                        {
                            "speaker_label": "spk_1",
                            "items": [{"start_time": "1.00"}],
                        },
                    ],
                },
                "items": [
                    {
                        "type": "pronunciation",
                        "start_time": "0.00",
                        "end_time": "0.30",
                        "alternatives": [{"content": "Budget"}],
                    },
                    {
                        "type": "pronunciation",
                        "start_time": "0.31",
                        "end_time": "0.60",
                        "alternatives": [{"content": "approval"}],
                    },
                    {
                        "type": "punctuation",
                        "alternatives": [{"content": "."}],
                    },
                    {
                        "type": "pronunciation",
                        "start_time": "1.00",
                        "end_time": "1.45",
                        "alternatives": [{"content": "Confirmed"}],
                    },
                ],
            }
        }

        transcript, segments = self.pipeline.build_transcript(result)

        self.assertEqual(len(segments), 2)
        self.assertEqual(segments[0]["speaker"], "Speaker 1")
        self.assertEqual(segments[0]["text"], "Budget approval.")
        self.assertEqual(segments[1]["speaker"], "Speaker 2")
        self.assertIn("[00:00:01] Confirmed", transcript)

    def test_search_index_chunks_long_transcripts_with_overlap(self):
        meeting_id = "meeting-123"
        transcript = ("A" * 15999) + " Budget approval confirmed."
        table = FakeTable()
        self.pipeline.transcript_search = table

        self.pipeline.index_transcript(meeting_id, "workspace-owner", transcript)

        self.assertEqual(len(table.writer.items), 2)
        self.assertEqual(table.writer.items[0]["chunkId"], 0)
        self.assertEqual(table.writer.items[1]["chunkId"], 1)
        self.assertIn("budget approval", table.writer.items[1]["content"])
        self.assertEqual(table.writer.items[0]["meetingId"], meeting_id)
        self.assertEqual(table.writer.items[0]["ownerId"], "workspace-owner")

    def test_eventbridge_transcribe_completion_reaches_processor(self):
        event = {
            "source": "aws.transcribe",
            "detail-type": "Transcribe Job State Change",
            "detail": {
                "TranscriptionJobName": "mtg-12345678-1234-1234-1234-123456789abc",
                "TranscriptionJobStatus": "COMPLETED",
            },
        }
        original = self.pipeline.process_transcribe_event
        calls = []
        self.pipeline.process_transcribe_event = lambda received: calls.append(received)
        try:
            result = self.pipeline.handler(event, None)
        finally:
            self.pipeline.process_transcribe_event = original

        self.assertEqual(result, {"processed": 1})
        self.assertEqual(calls, [event])

    def test_s3_recording_event_starts_transcription(self):
        record = {
            "eventSource": "aws:s3",
            "s3": {"object": {"key": "uploads/workspace-owner/12345678-1234-1234-1234-123456789abc.wav"}},
        }
        original = self.pipeline.start_transcription
        calls = []
        self.pipeline.start_transcription = lambda received: calls.append(received)
        try:
            result = self.pipeline.handler({"Records": [record]}, None)
        finally:
            self.pipeline.start_transcription = original

        self.assertEqual(result, {"started": 1})
        self.assertEqual(calls, [record])

    def test_s3_event_cannot_access_another_owners_meeting(self):
        meeting_id = "12345678-1234-1234-1234-123456789abc"
        record = {
            "s3": {"object": {"key": f"uploads/owner-two/{meeting_id}.wav"}},
        }
        table = FakeTable()
        table.item = {
            "meetingId": meeting_id,
            "ownerId": "owner-one",
            "s3Key": f"uploads/owner-one/{meeting_id}.wav",
            "status": "UPLOADING",
        }
        s3 = FakeS3()
        self.pipeline.meetings = table
        self.pipeline.s3 = s3

        self.pipeline.start_transcription(record)

        self.assertEqual(s3.head_calls, 0)
        self.assertFalse(table.updated)


if __name__ == "__main__":
    unittest.main()
