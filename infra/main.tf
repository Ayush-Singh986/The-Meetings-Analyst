terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    archive = {
      source  = "hashicorp/archive"
      version = "~> 2.4"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

data "aws_caller_identity" "current" {}
data "aws_partition" "current" {}

data "archive_file" "lambda" {
  type        = "zip"
  source_dir  = "${path.module}/../backend"
  output_path = "${path.module}/.terraform/briefly-lambda.zip"
  excludes    = ["tests", "tests/**", "__pycache__", "**/__pycache__/**", "*.pyc", "**/*.pyc"]
}

locals {
  name = var.project_name
  tags = {
    Project   = local.name
    ManagedBy = "Terraform"
  }
}

resource "random_id" "suffix" {
  byte_length = 4
}

resource "aws_s3_bucket" "meetings" {
  bucket        = "${local.name}-meetings-${random_id.suffix.hex}"
  force_destroy = false
  tags          = local.tags
}

resource "aws_s3_bucket" "web" {
  bucket        = "${local.name}-web-${random_id.suffix.hex}"
  force_destroy = true
  tags          = local.tags
}

resource "aws_s3_bucket_public_access_block" "meetings" {
  bucket                  = aws_s3_bucket.meetings.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_public_access_block" "web" {
  bucket                  = aws_s3_bucket.web.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "meetings" {
  bucket = aws_s3_bucket.meetings.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = "aws:kms"
      kms_master_key_id = aws_kms_key.meetings.arn
    }
    bucket_key_enabled = true
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "web" {
  bucket = aws_s3_bucket.web.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = "aws:kms"
      kms_master_key_id = aws_kms_key.web.arn
    }
    bucket_key_enabled = true
  }
}

resource "aws_s3_bucket_versioning" "meetings" {
  bucket = aws_s3_bucket.meetings.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_cors_configuration" "meetings" {
  bucket = aws_s3_bucket.meetings.id

  cors_rule {
    allowed_headers = ["*"]
    allowed_methods = ["GET", "POST", "HEAD"]
    allowed_origins = ["https://${aws_cloudfront_distribution.web.domain_name}"]
    expose_headers  = ["ETag"]
    max_age_seconds = 3600
  }
}

resource "aws_s3_object" "index" {
  bucket       = aws_s3_bucket.web.id
  key          = "index.html"
  source       = "${path.module}/../web/index.html"
  etag         = filemd5("${path.module}/../web/index.html")
  content_type = "text/html; charset=utf-8"
  cache_control = "no-cache, no-store, must-revalidate"
}

resource "aws_s3_object" "styles" {
  bucket        = aws_s3_bucket.web.id
  key           = "styles.css"
  source        = "${path.module}/../web/styles.css"
  etag          = filemd5("${path.module}/../web/styles.css")
  content_type  = "text/css; charset=utf-8"
  cache_control = "public, max-age=300"
}

resource "aws_s3_object" "app" {
  bucket        = aws_s3_bucket.web.id
  key           = "app.js"
  source        = "${path.module}/../web/app.js"
  etag          = filemd5("${path.module}/../web/app.js")
  content_type  = "text/javascript; charset=utf-8"
  cache_control = "public, max-age=300"
}

resource "aws_s3_object" "config" {
  bucket        = aws_s3_bucket.web.id
  key           = "config.js"
  content_type  = "text/javascript; charset=utf-8"
  cache_control = "no-cache, no-store, must-revalidate"
  content = "window.BRIEFLY_CONFIG = ${jsonencode({
    apiUrl          = aws_apigatewayv2_api.http.api_endpoint
    region          = var.aws_region
    userPoolClientId = aws_cognito_user_pool_client.dashboard.id
    userPoolDomain   = aws_cognito_user_pool_domain.workspace.domain
    dashboardUrl    = "https://${aws_cloudfront_distribution.web.domain_name}/"
  })};"
}

resource "aws_cloudfront_origin_access_control" "web" {
  name                              = "${local.name}-web-oac"
  description                       = "Private access to the Briefly static website bucket"
  origin_access_control_origin_type = "s3"
  signing_behavior                  = "always"
  signing_protocol                  = "sigv4"
}

resource "aws_cloudfront_distribution" "web" {
  enabled             = true
  default_root_object = "index.html"
  price_class         = "PriceClass_100"
  web_acl_id          = aws_wafv2_web_acl.edge.arn
  tags                = local.tags

  origin {
    domain_name              = aws_s3_bucket.web.bucket_regional_domain_name
    origin_id                = "web-${aws_s3_bucket.web.id}"
    origin_access_control_id = aws_cloudfront_origin_access_control.web.id
  }

  default_cache_behavior {
    allowed_methods        = ["GET", "HEAD", "OPTIONS"]
    cached_methods         = ["GET", "HEAD"]
    target_origin_id       = "web-${aws_s3_bucket.web.id}"
    viewer_protocol_policy = "redirect-to-https"
    compress                = true
    response_headers_policy_id = aws_cloudfront_response_headers_policy.web.id

    forwarded_values {
      query_string = false
      cookies {
        forward = "none"
      }
    }

    min_ttl     = 0
    default_ttl = 60
    max_ttl     = 300
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  viewer_certificate {
    cloudfront_default_certificate = true
  }
}

resource "aws_s3_bucket_policy" "web" {
  bucket = aws_s3_bucket.web.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "AllowCloudFrontRead"
        Effect    = "Allow"
        Principal = { Service = "cloudfront.amazonaws.com" }
        Action    = "s3:GetObject"
        Resource  = "${aws_s3_bucket.web.arn}/*"
        Condition = {
          StringEquals = {
            "AWS:SourceArn" = aws_cloudfront_distribution.web.arn
          }
        }
      },
      {
        Sid       = "DenyInsecureTransport"
        Effect    = "Deny"
        Principal = "*"
        Action    = "s3:*"
        Resource  = [aws_s3_bucket.web.arn, "${aws_s3_bucket.web.arn}/*"]
        Condition = {
          Bool = { "aws:SecureTransport" = "false" }
        }
      }
    ]
  })
}

resource "aws_s3_bucket_policy" "meetings_tls" {
  bucket = aws_s3_bucket.meetings.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Sid       = "DenyInsecureTransport"
      Effect    = "Deny"
      Principal = "*"
      Action    = "s3:*"
      Resource  = [aws_s3_bucket.meetings.arn, "${aws_s3_bucket.meetings.arn}/*"]
      Condition = {
        Bool = { "aws:SecureTransport" = "false" }
      }
    }]
  })
}

resource "aws_s3_bucket_lifecycle_configuration" "meetings" {
  bucket = aws_s3_bucket.meetings.id

  rule {
    id     = "abort-incomplete-uploads"
    status = "Enabled"

    filter {}

    abort_incomplete_multipart_upload {
      days_after_initiation = 7
    }
  }
}

resource "aws_dynamodb_table" "meetings" {
  name         = "${local.name}-meetings"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "meetingId"

  attribute {
    name = "meetingId"
    type = "S"
  }

  server_side_encryption {
    enabled     = true
    kms_key_arn = aws_kms_key.meetings.arn
  }

  point_in_time_recovery {
    enabled = true
  }

  tags = local.tags
}

resource "aws_dynamodb_table" "transcript_search" {
  name         = "${local.name}-transcript-search"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "meetingId"
  range_key    = "chunkId"

  attribute {
    name = "meetingId"
    type = "S"
  }

  attribute {
    name = "chunkId"
    type = "N"
  }

  server_side_encryption {
    enabled     = true
    kms_key_arn = aws_kms_key.meetings.arn
  }

  tags = local.tags
}

resource "aws_dynamodb_table" "integration_state" {
  name         = "${local.name}-integration-state"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "integrationId"

  attribute {
    name = "integrationId"
    type = "S"
  }

  server_side_encryption {
    enabled     = true
    kms_key_arn = aws_kms_key.meetings.arn
  }

  point_in_time_recovery {
    enabled = true
  }

  tags = local.tags
}

resource "aws_sqs_queue" "recording_events_dlq" {
  name                      = "${local.name}-recording-events-dlq"
  message_retention_seconds = 1209600
  sqs_managed_sse_enabled   = true
  tags                      = local.tags
}

resource "aws_sqs_queue" "recording_events" {
  name                       = "${local.name}-recording-events"
  visibility_timeout_seconds = 5400
  message_retention_seconds  = 345600
  sqs_managed_sse_enabled    = true
  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.recording_events_dlq.arn
    maxReceiveCount     = 3
  })
  tags = local.tags
}

resource "aws_secretsmanager_secret" "zoom_webhook" {
  name                    = "${local.name}/integrations/zoom-webhook-secret"
  description             = "Zoom webhook verification token. Set its value in Secrets Manager."
  recovery_window_in_days = 7
  tags                    = local.tags
}

resource "aws_secretsmanager_secret" "zoom_oauth" {
  name                    = "${local.name}/integrations/zoom-oauth"
  description             = "Zoom Server-to-Server OAuth JSON credentials. Set its value in Secrets Manager."
  recovery_window_in_days = 7
  tags                    = local.tags
}

resource "aws_secretsmanager_secret" "teams_graph" {
  name                    = "${local.name}/integrations/teams-graph"
  description             = "Microsoft Graph app credentials and webhook client state JSON. Set its value in Secrets Manager."
  recovery_window_in_days = 7
  tags                    = local.tags
}

resource "aws_sns_topic" "ready" {
  name              = "${local.name}-meeting-ready"
  kms_master_key_id = aws_kms_key.events.arn
  tags              = local.tags
}

resource "aws_iam_role" "lambda_api" {
  name = "${local.name}-api-lambda"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
    }]
  })
  tags = local.tags
}

resource "aws_iam_role" "lambda_pipeline" {
  name = "${local.name}-pipeline-lambda"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
    }]
  })
  tags = local.tags
}

resource "aws_iam_role" "lambda_recordings" {
  name = "${local.name}-recording-integrations"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
    }]
  })
  tags = local.tags
}

resource "aws_iam_role" "transcribe" {
  name = "${local.name}-transcribe-data"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "transcribe.amazonaws.com" }
    }]
  })
  tags = local.tags
}

resource "aws_iam_role_policy_attachment" "api_logs" {
  role       = aws_iam_role.lambda_api.name
  policy_arn = "arn:${data.aws_partition.current.partition}:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy_attachment" "pipeline_logs" {
  role       = aws_iam_role.lambda_pipeline.name
  policy_arn = "arn:${data.aws_partition.current.partition}:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy_attachment" "recordings_logs" {
  role       = aws_iam_role.lambda_recordings.name
  policy_arn = "arn:${data.aws_partition.current.partition}:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy" "api" {
  name = "${local.name}-api-access"
  role = aws_iam_role.lambda_api.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["s3:PutObject", "s3:AbortMultipartUpload"]
        Resource = "${aws_s3_bucket.meetings.arn}/uploads/*"
      },
      {
        Effect   = "Allow"
        Action   = ["s3:GetObject"]
        Resource = "${aws_s3_bucket.meetings.arn}/transcripts/*"
      },
      {
        Effect   = "Allow"
        Action   = ["dynamodb:GetItem", "dynamodb:PutItem", "dynamodb:Scan", "dynamodb:BatchGetItem"]
        Resource = aws_dynamodb_table.meetings.arn
      },
      {
        Effect   = "Allow"
        Action   = ["dynamodb:Scan"]
        Resource = aws_dynamodb_table.transcript_search.arn
      },
      {
        Effect   = "Allow"
        Action   = ["kms:Decrypt", "kms:GenerateDataKey"]
        Resource = aws_kms_key.meetings.arn
      },
      {
        Effect   = "Allow"
        Action   = ["sqs:SendMessage"]
        Resource = aws_sqs_queue.recording_events.arn
      },
      {
        Effect   = "Allow"
        Action   = ["secretsmanager:GetSecretValue"]
        Resource = [aws_secretsmanager_secret.zoom_webhook.arn, aws_secretsmanager_secret.teams_graph.arn]
      }
    ]
  })
}

resource "aws_iam_role_policy" "recordings" {
  name = "${local.name}-recording-integrations-access"
  role = aws_iam_role.lambda_recordings.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["s3:PutObject"]
        Resource = "${aws_s3_bucket.meetings.arn}/uploads/*"
      },
      {
        Effect   = "Allow"
        Action   = ["dynamodb:GetItem", "dynamodb:PutItem", "dynamodb:UpdateItem"]
        Resource = [aws_dynamodb_table.meetings.arn, aws_dynamodb_table.integration_state.arn]
      },
      {
        Effect   = "Allow"
        Action   = ["cognito-idp:ListUsers"]
        Resource = aws_cognito_user_pool.workspace.arn
      },
      {
        Effect   = "Allow"
        Action   = ["secretsmanager:GetSecretValue"]
        Resource = [aws_secretsmanager_secret.zoom_oauth.arn, aws_secretsmanager_secret.teams_graph.arn]
      },
      {
        Effect   = "Allow"
        Action   = ["sqs:ReceiveMessage", "sqs:DeleteMessage", "sqs:ChangeMessageVisibility", "sqs:GetQueueAttributes", "sqs:GetQueueUrl"]
        Resource = aws_sqs_queue.recording_events.arn
      },
      {
        Effect   = "Allow"
        Action   = ["kms:Decrypt", "kms:DescribeKey", "kms:GenerateDataKey", "kms:Encrypt"]
        Resource = aws_kms_key.meetings.arn
      }
    ]
  })
}

resource "aws_iam_role_policy" "pipeline" {
  name = "${local.name}-pipeline-access"
  role = aws_iam_role.lambda_pipeline.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["s3:GetObject"]
        Resource = ["${aws_s3_bucket.meetings.arn}/uploads/*", "${aws_s3_bucket.meetings.arn}/transcribe-output/*"]
      },
      {
        Effect   = "Allow"
        Action   = ["s3:PutObject"]
        Resource = "${aws_s3_bucket.meetings.arn}/transcripts/*"
      },
      {
        Effect   = "Allow"
        Action   = ["transcribe:StartTranscriptionJob", "transcribe:GetTranscriptionJob"]
        Resource = "*"
      },
      {
        Effect   = "Allow"
        Action   = ["iam:PassRole"]
        Resource = aws_iam_role.transcribe.arn
        Condition = {
          StringEquals = {
            "iam:PassedToService" = "transcribe.amazonaws.com"
          }
        }
      },
      {
        Effect   = "Allow"
        Action   = ["bedrock:InvokeModel"]
        Resource = "arn:${data.aws_partition.current.partition}:bedrock:${var.aws_region}::foundation-model/${var.bedrock_model_id}"
      },
      {
        Effect   = "Allow"
        Action   = ["dynamodb:GetItem", "dynamodb:UpdateItem"]
        Resource = aws_dynamodb_table.meetings.arn
      },
      {
        Effect   = "Allow"
        Action   = ["dynamodb:BatchWriteItem"]
        Resource = aws_dynamodb_table.transcript_search.arn
      },
      {
        Effect   = "Allow"
        Action   = ["sns:Publish"]
        Resource = aws_sns_topic.ready.arn
      },
      {
        Effect   = "Allow"
        Action   = ["kms:Decrypt", "kms:GenerateDataKey"]
        Resource = [aws_kms_key.meetings.arn, aws_kms_key.events.arn]
      }
    ]
  })
}

resource "aws_iam_role_policy" "transcribe" {
  name = "${local.name}-transcribe-s3"
  role = aws_iam_role.transcribe.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["s3:GetObject"]
        Resource = "${aws_s3_bucket.meetings.arn}/uploads/*"
      },
      {
        Effect   = "Allow"
        Action   = ["s3:PutObject"]
        Resource = "${aws_s3_bucket.meetings.arn}/transcribe-output/*"
      },
      {
        Effect   = "Allow"
        Action   = ["s3:ListBucket"]
        Resource = aws_s3_bucket.meetings.arn
        Condition = {
          StringLike = {
            "s3:prefix" = ["uploads/*"]
          }
        }
      },
      {
        Effect   = "Allow"
        Action   = ["s3:GetBucketLocation"]
        Resource = aws_s3_bucket.meetings.arn
      },
      {
        Effect   = "Allow"
        Action   = ["kms:Decrypt", "kms:Encrypt", "kms:GenerateDataKey*"]
        Resource = aws_kms_key.meetings.arn
      },
    ]
  })
}

resource "aws_lambda_function" "api" {
  function_name    = "${local.name}-api"
  role             = aws_iam_role.lambda_api.arn
  handler          = "api_lambda.handler"
  runtime          = "python3.12"
  timeout          = 30
  memory_size      = 512
  filename         = data.archive_file.lambda.output_path
  source_code_hash = data.archive_file.lambda.output_base64sha256

  environment {
    variables = {
      MEETINGS_BUCKET          = aws_s3_bucket.meetings.bucket
      MEETINGS_TABLE           = aws_dynamodb_table.meetings.name
      SEARCH_TABLE             = aws_dynamodb_table.transcript_search.name
      INTEGRATION_QUEUE_URL    = aws_sqs_queue.recording_events.url
      ZOOM_WEBHOOK_SECRET_ARN  = aws_secretsmanager_secret.zoom_webhook.arn
      TEAMS_GRAPH_SECRET_ARN   = aws_secretsmanager_secret.teams_graph.arn
    }
  }

  tags = local.tags

  reserved_concurrent_executions = 20
  depends_on = [aws_iam_role_policy_attachment.api_logs, aws_iam_role_policy.api]
}

resource "aws_lambda_function" "recordings" {
  function_name    = "${local.name}-recording-integrations"
  role             = aws_iam_role.lambda_recordings.arn
  handler          = "recording_worker.handler"
  runtime          = "python3.12"
  timeout          = 900
  memory_size      = 2048
  filename         = data.archive_file.lambda.output_path
  source_code_hash = data.archive_file.lambda.output_base64sha256

  ephemeral_storage {
    size = 1024
  }

  environment {
    variables = {
      MEETINGS_BUCKET         = aws_s3_bucket.meetings.bucket
      MEETINGS_TABLE          = aws_dynamodb_table.meetings.name
      INTEGRATION_STATE_TABLE = aws_dynamodb_table.integration_state.name
      USER_POOL_ID            = aws_cognito_user_pool.workspace.id
      ZOOM_OAUTH_SECRET_ARN   = aws_secretsmanager_secret.zoom_oauth.arn
      TEAMS_GRAPH_SECRET_ARN  = aws_secretsmanager_secret.teams_graph.arn
      API_URL                 = aws_apigatewayv2_api.http.api_endpoint
    }
  }

  tags = local.tags

  reserved_concurrent_executions = 5
  depends_on = [aws_iam_role_policy_attachment.recordings_logs, aws_iam_role_policy.recordings]
}

resource "aws_lambda_event_source_mapping" "recordings" {
  event_source_arn = aws_sqs_queue.recording_events.arn
  function_name    = aws_lambda_function.recordings.arn
  batch_size       = 1
  enabled          = true
}

resource "aws_cloudwatch_event_rule" "teams_subscription_renewal" {
  name                = "${local.name}-teams-subscription-renewal"
  description         = "Create and renew Microsoft Graph meeting recording notifications."
  schedule_expression = "rate(12 hours)"
  tags                = local.tags
}

resource "aws_lambda_permission" "teams_subscription_renewal" {
  statement_id  = "AllowTeamsSubscriptionSchedule"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.recordings.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.teams_subscription_renewal.arn
}

resource "aws_cloudwatch_event_target" "teams_subscription_renewal" {
  rule      = aws_cloudwatch_event_rule.teams_subscription_renewal.name
  target_id = "renew-teams-recording-subscription"
  arn       = aws_lambda_function.recordings.arn
  input     = jsonencode({ source = "briefly.integrations", detail = { action = "renew-teams-subscription" } })

  depends_on = [aws_lambda_permission.teams_subscription_renewal]
}

resource "aws_lambda_function" "pipeline" {
  function_name    = "${local.name}-pipeline"
  role             = aws_iam_role.lambda_pipeline.arn
  handler          = "pipeline.handler"
  runtime          = "python3.12"
  timeout          = 300
  memory_size      = 1024
  filename         = data.archive_file.lambda.output_path
  source_code_hash = data.archive_file.lambda.output_base64sha256

  environment {
    variables = {
      MEETINGS_BUCKET          = aws_s3_bucket.meetings.bucket
      MEETINGS_TABLE           = aws_dynamodb_table.meetings.name
      SEARCH_TABLE             = aws_dynamodb_table.transcript_search.name
      READY_TOPIC_ARN          = aws_sns_topic.ready.arn
      TRANSCRIBE_ROLE_ARN      = aws_iam_role.transcribe.arn
      BEDROCK_MODEL_ID         = var.bedrock_model_id
      TRANSCRIBE_LANGUAGE_CODE = var.transcribe_language_code
    }
  }

  tags = local.tags

  reserved_concurrent_executions = 10
  depends_on = [aws_iam_role_policy_attachment.pipeline_logs, aws_iam_role_policy.pipeline]
}

resource "aws_lambda_permission" "s3" {
  statement_id  = "AllowMeetingsBucketInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.pipeline.function_name
  principal     = "s3.amazonaws.com"
  source_arn    = aws_s3_bucket.meetings.arn
}

resource "aws_s3_bucket_notification" "meetings" {
  bucket = aws_s3_bucket.meetings.id

  lambda_function {
    lambda_function_arn = aws_lambda_function.pipeline.arn
    events              = ["s3:ObjectCreated:*"]
    filter_prefix       = "uploads/"
  }

  depends_on = [aws_lambda_permission.s3]
}

resource "aws_cloudwatch_event_rule" "transcribe" {
  name        = "${local.name}-transcribe-status"
  description = "Send completed and failed Transcribe jobs to the processor."
  event_pattern = jsonencode({
    source        = ["aws.transcribe"]
    "detail-type" = ["Transcribe Job State Change"]
    detail = {
      TranscriptionJobName   = [{ prefix = "mtg-" }]
      TranscriptionJobStatus = ["COMPLETED", "FAILED"]
    }
  })
  tags = local.tags
}

resource "aws_lambda_permission" "transcribe_events" {
  statement_id  = "AllowTranscribeEventsInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.pipeline.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.transcribe.arn
}

resource "aws_cloudwatch_event_target" "transcribe" {
  rule      = aws_cloudwatch_event_rule.transcribe.name
  target_id = "meeting-processor"
  arn       = aws_lambda_function.pipeline.arn

  retry_policy {
    maximum_event_age_in_seconds = 3600
    maximum_retry_attempts       = 5
  }

  depends_on = [aws_lambda_permission.transcribe_events]
}

resource "aws_sns_topic_subscription" "email" {
  count     = var.notification_email == "" ? 0 : 1
  topic_arn = aws_sns_topic.ready.arn
  protocol  = "email"
  endpoint  = var.notification_email
}

resource "aws_apigatewayv2_api" "http" {
  name          = "${local.name}-api"
  protocol_type = "HTTP"
  cors_configuration {
    allow_origins = ["https://${aws_cloudfront_distribution.web.domain_name}"]
    allow_methods = ["GET", "POST", "OPTIONS"]
    allow_headers = ["authorization", "content-type"]
    max_age       = 3600
  }
  tags = local.tags
}

resource "aws_apigatewayv2_authorizer" "cognito" {
  api_id           = aws_apigatewayv2_api.http.id
  name             = "${local.name}-user-pool-jwt"
  authorizer_type  = "JWT"
  identity_sources = ["$request.header.Authorization"]

  jwt_configuration {
    audience = [aws_cognito_user_pool_client.dashboard.id]
    issuer   = "https://cognito-idp.${var.aws_region}.amazonaws.com/${aws_cognito_user_pool.workspace.id}"
  }
}

resource "aws_apigatewayv2_integration" "api" {
  api_id                 = aws_apigatewayv2_api.http.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.api.invoke_arn
  payload_format_version = "2.0"
  timeout_milliseconds   = 29000
}

resource "aws_apigatewayv2_route" "default" {
  api_id             = aws_apigatewayv2_api.http.id
  route_key          = "$default"
  target             = "integrations/${aws_apigatewayv2_integration.api.id}"
  authorization_type = "JWT"
  authorizer_id      = aws_apigatewayv2_authorizer.cognito.id
}

resource "aws_apigatewayv2_route" "zoom_webhook" {
  api_id             = aws_apigatewayv2_api.http.id
  route_key          = "POST /webhooks/zoom"
  target             = "integrations/${aws_apigatewayv2_integration.api.id}"
  authorization_type = "NONE"
}

resource "aws_apigatewayv2_route" "teams_webhook" {
  api_id             = aws_apigatewayv2_api.http.id
  route_key          = "POST /webhooks/teams"
  target             = "integrations/${aws_apigatewayv2_integration.api.id}"
  authorization_type = "NONE"
}

resource "aws_apigatewayv2_stage" "default" {
  api_id      = aws_apigatewayv2_api.http.id
  name        = "$default"
  auto_deploy = true

  default_route_settings {
    throttling_burst_limit = 50
    throttling_rate_limit  = 25
  }

  tags = local.tags
}

resource "aws_lambda_permission" "api_gateway" {
  statement_id  = "AllowHttpApiInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.api.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.http.execution_arn}/*/*"
}
