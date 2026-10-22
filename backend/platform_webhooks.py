import base64
import hashlib
import hmac
import json
import logging
import os
import re
import time
from urllib.parse import unquote

import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)

secrets = boto3.client("secretsmanager")
sqs = boto3.client("sqs")
secret_cache = {}
max_webhook_bytes = 1024 * 1024


def response(status_code, body="", content_type="application/json; charset=utf-8"):
    headers = {"content-type": content_type}
    return {
        "statusCode": status_code,
        "headers": headers,
        "body": body if isinstance(body, str) else json.dumps(body),
    }


def read_secret(secret_arn):
    if secret_arn not in secret_cache:
        result = secrets.get_secret_value(SecretId=secret_arn)
        secret_cache[secret_arn] = result["SecretString"]
    return secret_cache[secret_arn]


def raw_body(event):
    body = event.get("body") or ""
    if event.get("isBase64Encoded"):
        try:
            body = base64.b64decode(body, validate=True).decode("utf-8")
        except (ValueError, UnicodeDecodeError) as exc:
            raise ValueError("Invalid encoded request body.") from exc
    if not isinstance(body, str) or len(body.encode("utf-8")) > max_webhook_bytes:
        raise ValueError("Webhook request exceeds the size limit.")
    return body


def decode_json(body):
    try:
        value = json.loads(body)
    except json.JSONDecodeError as exc:
        raise ValueError("Webhook body must be valid JSON.") from exc
    if not isinstance(value, dict):
        raise ValueError("Webhook body must be a JSON object.")
    return value


def enqueue(provider, event_id, payload):
    queue_url = os.environ["INTEGRATION_QUEUE_URL"]
    sqs.send_message(
        QueueUrl=queue_url,
        MessageBody=json.dumps(
            {"provider": provider, "eventId": event_id, **payload},
            separators=(",", ":"),
        ),
    )


def zoom_signature_is_valid(headers, body, secret, now=None):
    timestamp = headers.get("x-zm-request-timestamp", "")
    signature = headers.get("x-zm-signature", "")
    if not timestamp.isdigit() or not re.fullmatch(r"v0=[0-9a-f]{64}", signature):
        return False
    current_time = int(time.time() if now is None else now)
    if abs(current_time - int(timestamp)) > 300:
        return False
    message = f"v0:{timestamp}:{body}".encode("utf-8")
    expected = "v0=" + hmac.new(
        secret.encode("utf-8"), message, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(signature, expected)


def zoom_recording(payload):
    meeting = payload.get("object") or {}
    if not isinstance(meeting, dict):
        raise ValueError("Invalid Zoom recording object.")
    owner_email = meeting.get("host_email") or meeting.get("user_email")
    if not isinstance(owner_email, str) or not owner_email.strip():
        raise ValueError("Zoom event is missing the recording host email.")
    files = meeting.get("recording_files")
    if not isinstance(files, list):
        raise ValueError("Zoom event is missing recording files.")

    candidates = []
    for recording in files:
        if not isinstance(recording, dict) or recording.get("status", "completed") != "completed":
            continue
        file_type = str(recording.get("file_type", "")).lower()
        extension = file_type.rsplit(".", 1)[-1]
        download_url = recording.get("download_url")
        recording_id = recording.get("id")
        if extension not in {"mp3", "mp4", "wav", "flac", "ogg", "webm", "amr", "m4a"}:
            continue
        if not isinstance(download_url, str) or not recording_id:
            continue
        kind = recording.get("recording_type", "")
        preference = 0 if kind == "shared_screen_with_speaker_view" else 1
        candidates.append((preference, recording, extension))
    if not candidates:
        raise ValueError("Zoom event does not contain a supported completed recording.")
    _, recording, extension = sorted(candidates, key=lambda item: item[0])[0]
    return {
        "ownerEmail": owner_email.strip().lower(),
        "downloadUrl": recording["download_url"],
        "extension": extension,
        "recordingId": str(recording["id"]),
        "meetingId": str(meeting.get("id", "")),
        "title": str(meeting.get("topic") or "Zoom meeting")[:160],
    }


def handle_zoom(headers, body):
    secret_arn = os.environ.get("ZOOM_WEBHOOK_SECRET_ARN")
    if not secret_arn:
        return response(503, {"error": "Zoom webhook integration is not configured."})
    secret = read_secret(secret_arn)
    if not zoom_signature_is_valid(headers, body, secret):
        return response(401, {"error": "Invalid Zoom webhook signature."})

    payload = decode_json(body)
    event_type = payload.get("event")
    if event_type == "endpoint.url_validation":
        plain_token = (payload.get("payload") or {}).get("plainToken")
        if not isinstance(plain_token, str) or not plain_token:
            return response(400, {"error": "Zoom validation token is missing."})
        encrypted_token = hmac.new(
            secret.encode("utf-8"), plain_token.encode("utf-8"), hashlib.sha256
        ).hexdigest()
        return response(200, {"plainToken": plain_token, "encryptedToken": encrypted_token})

    if event_type != "recording.completed":
        return response(202, {"accepted": True})

    recording = zoom_recording(payload.get("payload") or {})
    event_id = payload.get("event_id")
    if not isinstance(event_id, str) or not event_id:
        event_id = hashlib.sha256(body.encode("utf-8")).hexdigest()
    enqueue("zoom", event_id, recording)
    return response(202, {"accepted": True})


def teams_notifications(payload, client_state):
    notifications = payload.get("value")
    if not isinstance(notifications, list) or len(notifications) > 100:
        raise ValueError("Invalid Microsoft Graph notification batch.")
    pending = []
    for notification in notifications:
        if not isinstance(notification, dict):
            raise ValueError("Invalid Microsoft Graph notification.")
        received_state = notification.get("clientState")
        if not isinstance(received_state, str) or not hmac.compare_digest(
            received_state, client_state
        ):
            raise PermissionError("Invalid Microsoft Graph client state.")
        resource = notification.get("resource", "")
        resource_data = notification.get("resourceData") or {}
        if not isinstance(resource, str) or not isinstance(resource_data, dict):
            raise ValueError("Invalid Microsoft Graph recording resource.")
        resource = unquote(resource)
        match = re.search(
            r"(?:^|/)users(?:/([^/?]+)|\('([^']+)'\))"
            r"/onlineMeetings(?:/([^/?]+)|\('([^']+)'\))"
            r"/recordings(?:/([^/?]+)|\('([^']+)'\))",
            resource,
            flags=re.IGNORECASE,
        )
        if not match:
            logger.warning("Skipping an unsupported Microsoft Graph recording resource.")
            continue
        organizer_id, meeting_id, recording_id = (
            next(value for value in match.groups()[start:end] if value)
            for start, end in ((0, 2), (2, 4), (4, 6))
        )
        if notification.get("changeType") not in {None, "created"}:
            continue
        event_id = hashlib.sha256(
            f"{notification.get('subscriptionId', '')}:{resource}".encode("utf-8")
        ).hexdigest()
        pending.append(
            {
                "provider": "teams",
                "eventId": event_id,
                "organizerId": organizer_id,
                "platformMeetingId": meeting_id,
                "recordingId": recording_id,
            }
        )
    return pending


def handle_teams(event, body):
    query = event.get("queryStringParameters") or {}
    validation_token = query.get("validationToken")
    if validation_token:
        return response(200, validation_token, "text/plain; charset=utf-8")

    secret_arn = os.environ.get("TEAMS_GRAPH_SECRET_ARN")
    if not secret_arn:
        return response(503, {"error": "Microsoft Teams webhook integration is not configured."})
    try:
        config = json.loads(read_secret(secret_arn))
    except json.JSONDecodeError as exc:
        logger.error("Microsoft Teams integration secret is not valid JSON.")
        return response(503, {"error": "Microsoft Teams webhook integration is not configured."})
    if not isinstance(config, dict):
        return response(503, {"error": "Microsoft Teams webhook integration is not configured."})
    client_state = config.get("client_state")
    if not isinstance(client_state, str) or len(client_state) < 16:
        return response(503, {"error": "Microsoft Teams webhook integration is not configured."})

    notifications = teams_notifications(decode_json(body), client_state)
    for notification in notifications:
        data = dict(notification)
        data.pop("provider", None)
        data.pop("eventId", None)
        enqueue("teams", notification["eventId"], data)
    return response(202, {"accepted": True})


def handler(event, context):
    method = event.get("requestContext", {}).get("http", {}).get("method", "")
    path = event.get("rawPath", "").rstrip("/")
    if method != "POST" or path not in {"/webhooks/zoom", "/webhooks/teams"}:
        return response(404, {"error": "Webhook route not found."})
    headers = {
        str(key).lower(): str(value)
        for key, value in (event.get("headers") or {}).items()
    }
    try:
        body = raw_body(event)
        if path == "/webhooks/zoom":
            return handle_zoom(headers, body)
        return handle_teams(event, body)
    except PermissionError:
        return response(401, {"error": "Invalid Microsoft Graph notification."})
    except ValueError as exc:
        return response(400, {"error": str(exc)})
    except Exception:
        logger.exception("Platform webhook request could not be accepted.")
        return response(500, {"error": "Webhook could not be processed."})
