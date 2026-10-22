import base64
import json
import logging
import os
import re
import time
import uuid
from datetime import datetime, timezone
from urllib.parse import unquote

import boto3
from boto3.dynamodb.conditions import Attr

import platform_webhooks

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3 = boto3.client("s3")
dynamodb = boto3.resource("dynamodb")
meetings = dynamodb.Table(os.environ["MEETINGS_TABLE"])
transcript_search = dynamodb.Table(os.environ["SEARCH_TABLE"])
bucket = os.environ["MEETINGS_BUCKET"]
allowed_extensions = {"mp3", "mp4", "wav", "flac", "ogg", "webm", "amr", "m4a"}
max_upload_bytes = 500 * 1024 * 1024


class RequestError(Exception):
    def __init__(self, status_code, message):
        super().__init__(message)
        self.status_code = status_code


def response(status_code, payload):
    return {
        "statusCode": status_code,
        "headers": {"content-type": "application/json; charset=utf-8"},
        "body": json.dumps(payload, ensure_ascii=False),
    }


def parse_body(event):
    body = event.get("body") or "{}"
    if event.get("isBase64Encoded"):
        body = base64.b64decode(body).decode("utf-8")
    try:
        value = json.loads(body)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise RequestError(400, "Request body must be valid JSON.") from exc
    if not isinstance(value, dict):
        raise RequestError(400, "Request body must be a JSON object.")
    return value


def current_user(event):
    claims = (
        event.get("requestContext", {})
        .get("authorizer", {})
        .get("jwt", {})
        .get("claims", {})
    )
    user_id = claims.get("sub")
    if not isinstance(user_id, str) or not re.fullmatch(r"[A-Za-z0-9-]{1,128}", user_id):
        raise RequestError(401, "A valid authenticated workspace account is required.")
    return user_id


def scan_all(table, **kwargs):
    items = []
    scan_kwargs = dict(kwargs)
    while True:
        result = table.scan(**scan_kwargs)
        items.extend(result.get("Items", []))
        last_key = result.get("LastEvaluatedKey")
        if not last_key:
            return items
        scan_kwargs["ExclusiveStartKey"] = last_key


def handle_upload_url(body, owner_id):
    file_name = body.get("fileName")
    content_type = body.get("contentType") or "application/octet-stream"
    file_size = body.get("fileSize")
    if not isinstance(file_name, str) or not file_name.strip():
        raise RequestError(400, "Choose a recording with a file name.")
    file_name = unquote(file_name).replace("\\", "/").split("/")[-1].strip()
    file_name = re.sub(r"[\x00-\x1f\x7f]", "", file_name)[:160]
    extension = file_name.rsplit(".", 1)[-1].lower() if "." in file_name else ""
    if extension not in allowed_extensions:
        raise RequestError(415, "Use MP3, MP4, WAV, FLAC, OGG, WebM, AMR, or M4A audio.")
    if not isinstance(file_size, int) or isinstance(file_size, bool) or file_size < 1 or file_size > max_upload_bytes:
        raise RequestError(413, "Recordings must be between 1 byte and 500 MB.")

    if not isinstance(content_type, str):
        raise RequestError(400, "Provide a valid recording content type.")
    safe_content_type = content_type.split(";", 1)[0].strip().lower()
    if (
        len(safe_content_type) > 100
        or not re.fullmatch(r"[a-z0-9!#$&^_.+-]+/[a-z0-9!#$&^_.+-]+", safe_content_type)
    ):
        raise RequestError(400, "Provide a valid recording content type.")

    meeting_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    object_key = f"uploads/{owner_id}/{meeting_id}.{extension}"
    upload = s3.generate_presigned_post(
        Bucket=bucket,
        Key=object_key,
        Fields={"Content-Type": safe_content_type},
        Conditions=[
            {"Content-Type": safe_content_type},
            ["content-length-range", 1, max_upload_bytes],
        ],
        ExpiresIn=300,
    )
    meetings.put_item(
        Item={
            "meetingId": meeting_id,
            "ownerId": owner_id,
            "title": file_name.rsplit(".", 1)[0],
            "fileName": file_name,
            "s3Key": object_key,
            "status": "UPLOADING",
            "createdAt": now,
            "searchText": file_name.lower(),
        }
    )
    return {
        "meetingId": meeting_id,
        "uploadUrl": upload["url"],
        "uploadFields": upload["fields"],
        "expiresIn": 300,
    }


def handle_list_meetings(query_params, owner_id):
    query = (query_params.get("search") or "").strip().lower()
    if len(query) > 200:
        raise RequestError(400, "Search phrases can be at most 200 characters.")
    summary_filter = Attr("ownerId").eq(owner_id)
    if query:
        summary_filter = summary_filter & Attr("searchText").contains(query)
    metadata_matches = scan_all(meetings, FilterExpression=summary_filter)

    if query:
        matching_ids = {item["meetingId"] for item in metadata_matches}
        transcript_matches = scan_all(
            transcript_search,
            FilterExpression=Attr("ownerId").eq(owner_id) & Attr("content").contains(query),
            ProjectionExpression="meetingId, ownerId",
        )
        matching_ids.update(item["meetingId"] for item in transcript_matches)

        if matching_ids:
            metadata_by_id = {item["meetingId"]: item for item in metadata_matches}
            missing_ids = matching_ids.difference(metadata_by_id)
            id_batches = [list(missing_ids)[i : i + 100] for i in range(0, len(missing_ids), 100)]
            for batch in id_batches:
                request_items = {
                    meetings.name: {
                        "Keys": [{"meetingId": meeting_id} for meeting_id in batch]
                    }
                }
                for attempt in range(5):
                    result = dynamodb.batch_get_item(RequestItems=request_items)
                    metadata_by_id.update({
                        item["meetingId"]: item
                        for item in result.get("Responses", {}).get(meetings.name, [])
                        if item.get("ownerId") == owner_id
                    })
                    request_items = result.get("UnprocessedKeys", {})
                    if not request_items:
                        break
                    time.sleep(0.025 * (2**attempt))
                if request_items:
                    raise RuntimeError("DynamoDB could not finish loading matching meeting records.")
            items = list(metadata_by_id.values())
        else:
            items = []
    else:
        items = metadata_matches

    items.sort(key=lambda item: item.get("createdAt", ""), reverse=True)
    return {"items": items, "count": len(items)}


def handle_meeting_detail(meeting_id, owner_id):
    result = meetings.get_item(Key={"meetingId": meeting_id})
    item = result.get("Item")
    if not item or item.get("ownerId") != owner_id:
        raise RequestError(404, "Meeting not found.")
    if item.get("s3Key"):
        item["audioUrl"] = s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket, "Key": item["s3Key"]},
            ExpiresIn=900,
        )
    if item.get("transcriptKey"):
        item["transcriptUrl"] = s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket, "Key": item["transcriptKey"]},
            ExpiresIn=900,
        )
    return item


def handler(event, context):
    method = event.get("requestContext", {}).get("http", {}).get("method", "")
    path = event.get("rawPath", "/").rstrip("/")
    if path in {"/webhooks/zoom", "/webhooks/teams"}:
        return platform_webhooks.handler(event, context)

    try:
        owner_id = current_user(event)
        path = path or "/"
        query_params = event.get("queryStringParameters") or {}

        if method == "POST" and path == "/upload-url":
            return response(200, handle_upload_url(parse_body(event), owner_id))
        if method == "GET" and path == "/meetings":
            return response(200, handle_list_meetings(query_params, owner_id))
        match = re.fullmatch(r"/meetings/([0-9a-fA-F-]{36})", path)
        if method == "GET" and match:
            return response(200, handle_meeting_detail(match.group(1), owner_id))
        raise RequestError(404, "That API route does not exist.")
    except RequestError as exc:
        return response(exc.status_code, {"error": str(exc)})
    except Exception:
        logger.exception("Meeting API request failed")
        return response(500, {"error": "The meeting request could not be completed. Try again."})
