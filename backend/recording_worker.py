import json
import logging
import mimetypes
import os
import re
import tempfile
import uuid
from datetime import datetime, timedelta, timezone
from urllib.error import HTTPError
from urllib.parse import quote, urlencode, urljoin, urlparse
from urllib.request import HTTPRedirectHandler, Request, build_opener

import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)

secrets = boto3.client("secretsmanager")
s3 = boto3.client("s3")
dynamodb = boto3.resource("dynamodb")
cognito = boto3.client("cognito-idp")
meetings = dynamodb.Table(os.environ["MEETINGS_TABLE"])
integration_state = dynamodb.Table(os.environ["INTEGRATION_STATE_TABLE"])
bucket = os.environ["MEETINGS_BUCKET"]
user_pool_id = os.environ["USER_POOL_ID"]
max_recording_bytes = 500 * 1024 * 1024
allowed_extensions = {"mp3", "mp4", "wav", "flac", "ogg", "webm", "amr", "m4a"}
secret_cache = {}


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, request, file_pointer, code, message, headers, new_url):
        return None


def read_secret(secret_arn):
    if secret_arn not in secret_cache:
        secret_cache[secret_arn] = secrets.get_secret_value(SecretId=secret_arn)["SecretString"]
    return secret_cache[secret_arn]


def safe_url(url, allowed_domain):
    parsed = urlparse(url)
    hostname = (parsed.hostname or "").lower()
    try:
        port = parsed.port
    except ValueError as exc:
        raise ValueError("Recording download URL has an invalid port.") from exc
    if (
        parsed.scheme != "https"
        or not hostname
        or parsed.username
        or parsed.password
        or port not in (None, 443)
        or not (hostname == allowed_domain or hostname.endswith("." + allowed_domain))
    ):
        raise ValueError("Recording download URL is not from an approved HTTPS provider.")
    return parsed


def request_without_redirects(request, timeout=30):
    opener = build_opener(NoRedirect)
    try:
        return opener.open(request, timeout=timeout), None
    except HTTPError as exc:
        if exc.code in {301, 302, 303, 307, 308}:
            return None, exc.headers.get("Location")
        raise


def fetch_to_file(url, authorization, provider_domain):
    current_url = url
    current_authorization = authorization
    current_domain = provider_domain
    with tempfile.NamedTemporaryFile(prefix="meeting-", delete=False) as output:
        file_path = output.name
    try:
        for _ in range(4):
            safe_url(current_url, current_domain)
            headers = {}
            if current_authorization:
                headers["Authorization"] = current_authorization
            request = Request(current_url, headers=headers)
            response, redirect = request_without_redirects(request, timeout=60)
            if redirect:
                current_url = urljoin(current_url, redirect)
                if provider_domain == "graph.microsoft.com":
                    current_domain = "sharepoint.com"
                    current_authorization = None
                continue
            if not response:
                raise RuntimeError("Provider returned an empty recording response.")
            with response, open(file_path, "wb") as destination:
                length = response.headers.get("Content-Length")
                if length and int(length) > max_recording_bytes:
                    raise ValueError("Recording exceeds the 500 MB processing limit.")
                total = 0
                while True:
                    chunk = response.read(1024 * 1024)
                    if not chunk:
                        break
                    total += len(chunk)
                    if total > max_recording_bytes:
                        raise ValueError("Recording exceeds the 500 MB processing limit.")
                    destination.write(chunk)
            if total < 1:
                raise ValueError("Provider returned an empty recording.")
            return file_path
        raise ValueError("Provider recording URL redirected too many times.")
    except Exception:
        try:
            os.unlink(file_path)
        except OSError:
            logger.warning("Could not remove incomplete temporary recording file.")
        raise


def request_json(url, method="GET", headers=None, body=None):
    payload = None if body is None else json.dumps(body).encode("utf-8")
    request_headers = {"Accept": "application/json", **(headers or {})}
    if payload is not None:
        request_headers["Content-Type"] = "application/json"
    request = Request(url, data=payload, headers=request_headers, method=method)
    result, redirect = request_without_redirects(request, timeout=30)
    if redirect:
        raise ValueError("Provider API unexpectedly redirected a request.")
    with result:
        response_body = result.read(1024 * 1024 + 1)
    if len(response_body) > 1024 * 1024:
        raise ValueError("Provider returned an unexpectedly large API response.")
    return json.loads(response_body.decode("utf-8")) if response_body else {}


def zoom_access_token():
    config = json.loads(read_secret(os.environ["ZOOM_OAUTH_SECRET_ARN"]))
    account_id = config["account_id"]
    client_id = config["client_id"]
    client_secret = config["client_secret"]
    from base64 import b64encode

    credentials = b64encode(f"{client_id}:{client_secret}".encode("utf-8")).decode("ascii")
    query = urlencode({"grant_type": "account_credentials", "account_id": account_id})
    result = request_json(
        f"https://zoom.us/oauth/token?{query}",
        method="POST",
        headers={"Authorization": f"Basic {credentials}"},
    )
    token = result.get("access_token")
    if not isinstance(token, str) or not token:
        raise ValueError("Zoom did not return an OAuth access token.")
    return token


def graph_config():
    config = json.loads(read_secret(os.environ["TEAMS_GRAPH_SECRET_ARN"]))
    for key in ("tenant_id", "client_id", "client_secret", "client_state"):
        if not isinstance(config.get(key), str) or not config[key]:
            raise ValueError("Microsoft Graph app credentials are incomplete.")
    if not 16 <= len(config["client_state"]) <= 128:
        raise ValueError("Microsoft Graph client_state must be 16-128 characters.")
    return config


def graph_access_token(config):
    tenant_id = quote(config["tenant_id"], safe="")
    url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
    form = urlencode(
        {
            "client_id": config["client_id"],
            "client_secret": config["client_secret"],
            "scope": "https://graph.microsoft.com/.default",
            "grant_type": "client_credentials",
        }
    ).encode("utf-8")
    request = Request(
        url,
        data=form,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    result, redirect = request_without_redirects(request, timeout=30)
    if redirect:
        raise ValueError("Microsoft identity platform unexpectedly redirected a token request.")
    with result:
        response_body = result.read(1024 * 1024 + 1)
    if len(response_body) > 1024 * 1024:
        raise ValueError("Microsoft identity platform returned an unexpectedly large response.")
    token = json.loads(response_body.decode("utf-8")).get("access_token")
    if not isinstance(token, str) or not token:
        raise ValueError("Microsoft identity platform did not return an access token.")
    return token


def cognito_owner(email):
    if (
        not isinstance(email, str)
        or len(email) > 254
        or not re.fullmatch(r"[^@\s\"<>]+@[^@\s\"<>]+\.[^@\s\"<>]+", email)
    ):
        raise ValueError("Recording host email is not a valid email address.")
    email = email.lower()
    result = cognito.list_users(
        UserPoolId=user_pool_id,
        Filter=f'email = "{email}"',
        Limit=10,
    )
    matches = [
        user
        for user in result.get("Users", [])
        if user.get("UserStatus") == "CONFIRMED"
        and any(
            attribute.get("Name") == "email_verified"
            and attribute.get("Value") == "true"
            for attribute in user.get("Attributes", [])
        )
        and any(
            attribute.get("Name") == "email"
            and attribute.get("Value", "").lower() == email.lower()
            for attribute in user.get("Attributes", [])
        )
    ]
    if len(matches) != 1:
        raise ValueError("Recording host email must match one verified workspace account.")
    owner_id = next(
        (attribute.get("Value") for attribute in matches[0].get("Attributes", []) if attribute.get("Name") == "sub"),
        None,
    )
    if not isinstance(owner_id, str) or not re.fullmatch(r"[A-Za-z0-9-]{1,128}", owner_id):
        raise ValueError("The matching Cognito account does not have a valid owner ID.")
    return owner_id


def graph_user_email(organizer_id, token):
    user = request_json(
        f"https://graph.microsoft.com/v1.0/users/{quote(organizer_id, safe='')}?$select=mail,userPrincipalName",
        headers={"Authorization": f"Bearer {token}"},
    )
    email = user.get("mail") or user.get("userPrincipalName")
    if not isinstance(email, str) or "@" not in email:
        raise ValueError("Microsoft Graph could not resolve the meeting organizer email.")
    return email.lower()


def graph_recording_url(organizer_id, meeting_id, recording_id, token):
    organizer, meeting, recording = (
        quote(part, safe="") for part in (organizer_id, meeting_id, recording_id)
    )
    return (
        "https://graph.microsoft.com/v1.0/users/"
        f"{organizer}/onlineMeetings/{meeting}/recordings/{recording}/content"
    ), f"Bearer {token}"


def meeting_uuid(provider, event_id):
    namespace = uuid.UUID("8406237e-60ba-4d68-a319-63bc7c161b61")
    return str(uuid.uuid5(namespace, f"{provider}:{event_id}"))


def put_meeting_if_missing(meeting):
    try:
        meetings.put_item(
            Item=meeting,
            ConditionExpression="attribute_not_exists(meetingId)",
        )
        return meeting
    except Exception as exc:
        code = getattr(exc, "response", {}).get("Error", {}).get("Code")
        if code != "ConditionalCheckFailedException":
            raise
        existing = meetings.get_item(Key={"meetingId": meeting["meetingId"]}).get("Item")
        if not existing:
            raise RuntimeError("Duplicate meeting could not be loaded after a conditional write.")
        return existing


def process_recording(message):
    provider = message.get("provider")
    event_id = message.get("eventId")
    if provider not in {"zoom", "teams"} or not isinstance(event_id, str) or not event_id:
        raise ValueError("Invalid platform recording queue message.")
    meeting_id = meeting_uuid(provider, event_id)
    now = datetime.now(timezone.utc).isoformat()

    if provider == "zoom":
        owner_id = cognito_owner(message["ownerEmail"])
        extension = message["extension"].lower()
        if extension not in allowed_extensions:
            raise ValueError("Zoom recording format is not supported.")
        title = message.get("title", "Zoom meeting")
        file_name = f"{title}.{extension}"[:160]
        download_url = message["downloadUrl"]
        authorization = f"Bearer {zoom_access_token()}"
        allowed_domain = "zoom.us"
        platform_meeting_id = message.get("meetingId", "")
    else:
        config = graph_config()
        token = graph_access_token(config)
        owner_email = graph_user_email(message["organizerId"], token)
        owner_id = cognito_owner(owner_email)
        download_url, authorization = graph_recording_url(
            message["organizerId"],
            message["platformMeetingId"],
            message["recordingId"],
            token,
        )
        extension = "mp4"
        file_name = f"Teams meeting {message['platformMeetingId']}.mp4"[:160]
        title = f"Microsoft Teams meeting {message['platformMeetingId']}"[:160]
        allowed_domain = "graph.microsoft.com"
        platform_meeting_id = message["platformMeetingId"]

    item = {
        "meetingId": meeting_id,
        "ownerId": owner_id,
        "title": title,
        "fileName": file_name,
        "s3Key": f"uploads/{owner_id}/{meeting_id}.{extension}",
        "status": "UPLOADING",
        "createdAt": now,
        "searchText": file_name.lower(),
        "sourceProvider": provider,
        "platformMeetingId": str(platform_meeting_id),
        "sourceEventId": event_id,
    }
    existing = put_meeting_if_missing(item)
    if (
        existing.get("ownerId") != owner_id
        or existing.get("sourceProvider") != provider
        or existing.get("sourceEventId") != event_id
    ):
        raise RuntimeError("Recording event collided with an existing workspace meeting.")
    if existing.get("status") in {"PROCESSING", "READY"}:
        return

    file_path = fetch_to_file(download_url, authorization, allowed_domain)
    try:
        meetings.update_item(
            Key={"meetingId": meeting_id},
            UpdateExpression="SET #status = :status, updatedAt = :updated",
            ExpressionAttributeNames={"#status": "status"},
            ExpressionAttributeValues={":status": "UPLOADING", ":updated": now},
        )
        content_type = mimetypes.guess_type(file_name)[0] or "application/octet-stream"
        s3.upload_file(
            file_path,
            bucket,
            item["s3Key"],
            ExtraArgs={"ContentType": content_type},
        )
    finally:
        try:
            os.unlink(file_path)
        except OSError:
            logger.warning("Could not remove downloaded meeting recording.")


def renew_teams_subscription():
    config = graph_config()
    organizer_ids = config.get("organizer_user_ids")
    if (
        not isinstance(organizer_ids, list)
        or not organizer_ids
        or len(organizer_ids) > 100
        or any(not isinstance(user_id, str) or not user_id for user_id in organizer_ids)
    ):
        raise ValueError(
            "Microsoft Graph integration requires 1-100 organizer_user_ids."
        )
    token = graph_access_token(config)
    authorization = {"Authorization": f"Bearer {token}"}
    expiration = (
        datetime.now(timezone.utc) + timedelta(hours=23)
    ).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    callback = f"{os.environ['API_URL'].rstrip('/')}/webhooks/teams"
    for organizer_id in organizer_ids:
        state_key = f"teams-recordings-subscription#{organizer_id}"
        existing = integration_state.get_item(
            Key={"integrationId": state_key}
        ).get("Item")
        subscription_id = existing.get("subscriptionId") if existing else None
        subscription = None
        if subscription_id:
            try:
                subscription = request_json(
                    f"https://graph.microsoft.com/v1.0/subscriptions/{quote(subscription_id, safe='')}",
                    method="PATCH",
                    headers=authorization,
                    body={"expirationDateTime": expiration},
                )
                if "id" not in subscription:
                    subscription["id"] = subscription_id
            except HTTPError as exc:
                if exc.code != 404:
                    raise

        if subscription is None:
            subscription = request_json(
                "https://graph.microsoft.com/v1.0/subscriptions",
                method="POST",
                headers=authorization,
                body={
                    "changeType": "created",
                    "notificationUrl": callback,
                    "resource": f"/users/{quote(organizer_id, safe='')}/onlineMeetings/getAllRecordings",
                    "expirationDateTime": expiration,
                    "clientState": config["client_state"],
                },
            )
        if not isinstance(subscription.get("id"), str):
            raise ValueError("Microsoft Graph did not return a subscription ID.")
        integration_state.put_item(
            Item={
                "integrationId": state_key,
                "organizerId": organizer_id,
                "subscriptionId": subscription["id"],
                "expirationDateTime": subscription.get("expirationDateTime", expiration),
                "updatedAt": datetime.now(timezone.utc).isoformat(),
            }
        )


def handler(event, context):
    if event.get("source") == "briefly.integrations":
        if (event.get("detail") or {}).get("action") == "renew-teams-subscription":
            renew_teams_subscription()
            return {"renewed": True}
        raise ValueError("Unsupported integration schedule event.")

    records = event.get("Records", [])
    for record in records:
        message = json.loads(record["body"])
        process_recording(message)
    return {"processed": len(records)}
