import json
import logging
import os
import re
import time
from datetime import datetime, timezone
from urllib.parse import unquote_plus

import boto3
from boto3.dynamodb.conditions import Attr

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3 = boto3.client("s3")
transcribe = boto3.client("transcribe")
bedrock = boto3.client("bedrock-runtime")
sns = boto3.client("sns")
dynamodb = boto3.resource("dynamodb")
meetings = dynamodb.Table(os.environ["MEETINGS_TABLE"])
transcript_search = dynamodb.Table(os.environ["SEARCH_TABLE"])
bucket = os.environ["MEETINGS_BUCKET"]
language_code = os.environ.get("TRANSCRIBE_LANGUAGE_CODE", "en-US")

search_chunk_chars = 16000
search_chunk_overlap = 250
max_summary_chars = 60000


def mark_failed(meeting_id, message):
    meetings.update_item(
        Key={"meetingId": meeting_id},
        UpdateExpression="SET #status = :status, errorMessage = :message, updatedAt = :updated",
        ExpressionAttributeNames={"#status": "status"},
        ExpressionAttributeValues={
            ":status": "FAILED",
            ":message": message[:500],
            ":updated": datetime.now(timezone.utc).isoformat(),
        },
    )


def start_transcription(record):
    object_key = unquote_plus(record["s3"]["object"]["key"])
    match = re.fullmatch(
        r"uploads/([A-Za-z0-9-]{1,128})/([0-9a-f-]{36})\.(mp3|mp4|wav|flac|ogg|webm|amr|m4a)",
        object_key,
        flags=re.IGNORECASE,
    )
    if not match:
        logger.warning("Skipping upload with an unexpected meeting ID: %s", object_key)
        return
    owner_id, meeting_id, extension = match.groups()

    result = meetings.get_item(Key={"meetingId": meeting_id})
    meeting = result.get("Item")
    if not meeting:
        logger.warning("No meeting record exists for uploaded object %s", object_key)
        return
    if (
        meeting.get("ownerId") != owner_id
        or meeting.get("s3Key") != object_key
        or meeting.get("status") not in {"UPLOADING", "PROCESSING"}
    ):
        return

    try:
        head = s3.head_object(Bucket=bucket, Key=object_key)
    except Exception:
        logger.exception("Could not inspect uploaded recording %s", object_key)
        raise

    if head.get("ContentLength", 0) > 500 * 1024 * 1024:
        mark_failed(meeting_id, "This recording exceeds the 500 MB upload limit.")
        return

    extension = extension.lower()
    media_format = "mp4" if extension == "m4a" else extension
    job_name = f"mtg-{meeting_id}"
    try:
        transcribe.start_transcription_job(
            TranscriptionJobName=job_name,
            Media={"MediaFileUri": f"s3://{bucket}/{object_key}"},
            MediaFormat=media_format,
            LanguageCode=language_code,
            OutputBucketName=bucket,
            OutputKey=f"transcribe-output/{owner_id}/{job_name}.json",
            Settings={"ShowSpeakerLabels": True, "MaxSpeakerLabels": 10},
            JobExecutionSettings={
                "AllowDeferredExecution": True,
                "DataAccessRoleArn": os.environ["TRANSCRIBE_ROLE_ARN"],
            },
        )
    except transcribe.exceptions.ConflictException:
        logger.info("Transcription job %s already exists", job_name)
    except Exception:
        logger.exception("Could not start transcription job %s", job_name)
        mark_failed(meeting_id, "Amazon Transcribe could not start this recording.")
        return

    meetings.update_item(
        Key={"meetingId": meeting_id},
        UpdateExpression="SET #status = :status, updatedAt = :updated",
        ExpressionAttributeNames={"#status": "status"},
        ExpressionAttributeValues={
            ":status": "PROCESSING",
            ":updated": datetime.now(timezone.utc).isoformat(),
        },
    )


def _timestamp(seconds):
    if seconds is None:
        return "00:00:00"
    whole_seconds = int(float(seconds))
    return f"{whole_seconds // 3600:02}:{(whole_seconds % 3600) // 60:02}:{whole_seconds % 60:02}"


def build_transcript(transcribe_result):
    results = transcribe_result.get("results", {})
    speaker_labels = results.get("speaker_labels", {}).get("speakers", [])
    speaker_numbers = {
        speaker.get("speaker_label"): index + 1
        for index, speaker in enumerate(speaker_labels)
        if speaker.get("speaker_label")
    }
    speaker_by_start = {}
    for segment in results.get("speaker_labels", {}).get("segments", []):
        for item in segment.get("items", []):
            if item.get("start_time") is not None:
                speaker_by_start[item["start_time"]] = segment.get("speaker_label")
    words = []
    for item in results.get("items", []):
        alternatives = item.get("alternatives") or []
        if not alternatives:
            continue
        word = alternatives[0].get("content", "")
        if not word:
            continue
        punctuation = item.get("type") == "punctuation"
        speaker = item.get("speaker_label") or speaker_by_start.get(item.get("start_time"))
        if punctuation and speaker is None and words:
            speaker = words[-1]["speaker"]
        words.append(
            {
                "word": word,
                "punctuation": punctuation,
                "speaker": speaker,
                "start": item.get("start_time"),
                "end": item.get("end_time"),
            }
        )

    segments = []
    current = None
    for word in words:
        speaker = word["speaker"]
        if current is None or speaker != current["speaker"]:
            if current:
                segments.append(current)
            current = {
                "speaker": speaker,
                "start": word["start"],
                "end": word["end"],
                "text": "",
            }
        if word["punctuation"]:
            current["text"] = current["text"].rstrip() + word["word"]
        else:
            current["text"] += (" " if current["text"] else "") + word["word"]
        current["end"] = word["end"] or current["end"]
    if current:
        segments.append(current)

    formatted_segments = []
    for segment in segments:
        number = speaker_numbers.get(segment["speaker"])
        formatted_segments.append(
            {
                "start": segment["start"],
                "end": segment["end"],
                "speaker": f"Speaker {number}" if number else None,
                "text": segment["text"].strip(),
            }
        )

    transcript_text = "\n".join(
        f"{segment['speaker'] + ' · ' if segment['speaker'] else ''}"
        f"[{_timestamp(segment['start'])}] {segment['text']}"
        for segment in formatted_segments
    )
    if not transcript_text.strip():
        transcripts = results.get("transcripts", [])
        transcript_text = transcripts[0].get("transcript", "").strip() if transcripts else ""
    if not transcript_text:
        raise ValueError("Amazon Transcribe returned an empty transcript.")
    return transcript_text, formatted_segments


def analyze_transcript(transcript_text):
    prompt = """Analyze this meeting transcript. Return only one valid JSON object with this exact shape:
{"summary":"2-4 concise sentences","key_decisions":["decision"],"action_items":[{"owner":"person or Unassigned","task":"specific action","due_date":"date or Not specified"}],"topics":["topic"],"participants":["speaker name or label"]}
Use only facts stated in the transcript. Do not invent decisions, owners, or deadlines. Keep arrays empty when no evidence exists. Preserve speaker labels when names are unknown.

Transcript:
"""
    response = bedrock.converse(
        modelId=os.environ["BEDROCK_MODEL_ID"],
        messages=[
            {
                "role": "user",
                "content": [{"text": prompt + transcript_text[:max_summary_chars]}],
            }
        ],
        inferenceConfig={"maxTokens": 2500, "temperature": 0.2},
    )
    text = response["output"]["message"]["content"][0]["text"].strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.IGNORECASE)
    summary = json.loads(text)
    if not isinstance(summary, dict) or not isinstance(summary.get("summary"), str):
        raise ValueError("Amazon Bedrock returned an unexpected summary format.")
    for field in ("key_decisions", "action_items", "topics", "participants"):
        if not isinstance(summary.get(field), list):
            raise ValueError(f"Amazon Bedrock omitted the {field} list.")
    return summary


def index_transcript(meeting_id, owner_id, transcript_text):
    normalized = transcript_text.lower()
    chunks = []
    offset = 0
    while offset < len(normalized):
        end = min(offset + search_chunk_chars, len(normalized))
        chunks.append(
            {
                "meetingId": meeting_id,
                "chunkId": len(chunks),
                "ownerId": owner_id,
                "content": normalized[offset:end],
            }
        )
        if end == len(normalized):
            break
        offset = end - search_chunk_overlap

    with transcript_search.batch_writer(overwrite_by_pkeys=["meetingId", "chunkId"]) as batch:
        for chunk in chunks:
            batch.put_item(Item=chunk)


def process_transcribe_event(event):
    message = event.get("detail") or {}
    job_name = message.get("TranscriptionJobName", "")
    match = re.fullmatch(r"mtg-([0-9a-f-]{36})", job_name)
    if not match:
        logger.warning("Ignoring an unrelated Transcribe job notification: %s", job_name)
        return
    meeting_id = match.group(1)
    status = message.get("TranscriptionJobStatus")
    existing = meetings.get_item(Key={"meetingId": meeting_id}).get("Item")
    owner_id = existing.get("ownerId") if existing else None
    if (
        not owner_id
        or not re.fullmatch(
            rf"uploads/{re.escape(owner_id)}/{meeting_id}\.(mp3|mp4|wav|flac|ogg|webm|amr|m4a)",
            existing.get("s3Key", ""),
            flags=re.IGNORECASE,
        )
    ):
        logger.warning("Ignoring Transcribe event for an unowned meeting %s", meeting_id)
        return
    if status == "FAILED":
        reason = message.get("FailureReason", "Amazon Transcribe could not process this recording.")
        mark_failed(meeting_id, reason)
        logger.error("Transcription failed for %s: %s", meeting_id, reason)
        return
    if status != "COMPLETED":
        logger.info("Transcription job %s is not complete yet", job_name)
        return

    if not existing or existing.get("status") == "READY":
        return

    job = transcribe.get_transcription_job(TranscriptionJobName=job_name)
    job_status = job.get("TranscriptionJob", {}).get("TranscriptionJobStatus")
    if job_status != "COMPLETED":
        raise RuntimeError(f"Transcribe notified completion but the job is {job_status}.")

    output_key = f"transcribe-output/{owner_id}/{job_name}.json"
    raw = s3.get_object(Bucket=bucket, Key=output_key)["Body"].read()
    transcribe_result = json.loads(raw)
    transcript_text, segments = build_transcript(transcribe_result)
    analysis = analyze_transcript(transcript_text)
    transcript_key = f"transcripts/{owner_id}/{meeting_id}.json"
    s3.put_object(
        Bucket=bucket,
        Key=transcript_key,
        Body=json.dumps(
            {
                "meetingId": meeting_id,
                "text": transcript_text,
                "segments": segments,
            },
            ensure_ascii=False,
        ).encode("utf-8"),
        ContentType="application/json; charset=utf-8",
    )
    index_transcript(meeting_id, owner_id, transcript_text)

    action_items = [
        item
        for item in analysis["action_items"]
        if isinstance(item, dict) and isinstance(item.get("task"), str)
    ]
    key_decisions = [item for item in analysis["key_decisions"] if isinstance(item, str)]
    topics = [item for item in analysis["topics"] if isinstance(item, str)]
    participants = [item for item in analysis["participants"] if isinstance(item, str)]
    searchable_summary = " ".join(
        [existing.get("title", ""), analysis["summary"], *key_decisions, *topics]
        + [
            " ".join(
                str(action.get(field, ""))
                for field in ("owner", "task", "due_date")
            )
            for action in action_items
        ]
    ).lower()
    now = datetime.now(timezone.utc).isoformat()
    meetings.update_item(
        Key={"meetingId": meeting_id},
        UpdateExpression=(
            "SET #status = :status, summary = :summary, keyDecisions = :decisions, "
            "actionItems = :actions, topics = :topics, participants = :participants, "
            "transcriptKey = :transcript, searchText = :search, updatedAt = :updated "
            "REMOVE errorMessage"
        ),
        ExpressionAttributeNames={"#status": "status"},
        ExpressionAttributeValues={
            ":status": "READY",
            ":summary": analysis["summary"],
            ":decisions": key_decisions,
            ":actions": action_items,
            ":topics": topics,
            ":participants": participants,
            ":transcript": transcript_key,
            ":search": searchable_summary,
            ":updated": now,
        },
    )

    sns.publish(
        TopicArn=os.environ["READY_TOPIC_ARN"],
        Subject="Your meeting transcript is ready",
        Message=json.dumps(
            {
                "meetingId": meeting_id,
                "title": existing.get("title", "Meeting"),
                "status": "READY",
            }
        ),
    )
    logger.info("Meeting %s is ready", meeting_id)


def handler(event, context):
    records = event.get("Records", [])
    if records and records[0].get("eventSource") == "aws:s3":
        for record in records:
            start_transcription(record)
        return {"started": len(records)}

    if event.get("source") == "aws.transcribe" and event.get("detail-type") == "Transcribe Job State Change":
        try:
            process_transcribe_event(event)
        except Exception:
            detail = event.get("detail") or {}
            job_name = detail.get("TranscriptionJobName", "")
            match = re.fullmatch(r"mtg-([0-9a-f-]{36})", job_name)
            if match and detail.get("TranscriptionJobStatus") == "COMPLETED":
                mark_failed(
                    match.group(1),
                    "Transcript analysis could not be completed. Check the processor Lambda logs.",
                )
            raise
        return {"processed": 1}

    logger.error("Received an unsupported pipeline event")
    raise ValueError("The pipeline received an unsupported event.")
