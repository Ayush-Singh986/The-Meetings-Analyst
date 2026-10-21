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

provider "aws" {
  alias  = "cloudfront"
  region = "us-east-1"
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

resource "aws_s3_bucket_ownership_controls" "meetings" {
  bucket = aws_s3_bucket.meetings.id

  rule {
    object_ownership = "BucketOwnerEnforced"
  }
}

resource "aws_s3_bucket_ownership_controls" "web" {
  bucket = aws_s3_bucket.web.id

  rule {
    object_ownership = "BucketOwnerEnforced"
  }
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

resource "aws_kms_key" "meetings" {
  description             = "${local.name} recordings and transcripts"
  enable_key_rotation     = true
  deletion_window_in_days = 30
  tags                    = local.tags
}

resource "aws_kms_alias" "meetings" {
  name          = "alias/${local.name}-meetings"
  target_key_id = aws_kms_key.meetings.key_id
}

resource "aws_kms_key" "web" {
  description             = "${local.name} dashboard assets"
  enable_key_rotation     = true
  deletion_window_in_days = 30
  tags                    = local.tags
}

resource "aws_kms_alias" "web" {
  name          = "alias/${local.name}-web"
  target_key_id = aws_kms_key.web.key_id
}

resource "aws_kms_key" "events" {
  description             = "${local.name} event and notification payloads"
  enable_key_rotation     = true
  deletion_window_in_days = 30
  tags                    = local.tags
}

resource "aws_kms_alias" "events" {
  name          = "alias/${local.name}-events"
  target_key_id = aws_kms_key.events.key_id
}

resource "aws_kms_key_policy" "events" {
  key_id = aws_kms_key.events.key_id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "EnableAccountIamPermissions"
        Effect    = "Allow"
        Principal = { AWS = "arn:${data.aws_partition.current.partition}:iam::${data.aws_caller_identity.current.account_id}:root" }
        Action    = "kms:*"
        Resource  = "*"
      },
      {
        Sid       = "AllowSnsUseForReadyNotifications"
        Effect    = "Allow"
        Principal = { Service = "sns.amazonaws.com" }
        Action    = ["kms:Decrypt", "kms:GenerateDataKey*"]
        Resource  = "*"
        Condition = {
          StringEquals = {
            "kms:EncryptionContext:aws:sns:topicArn" = "arn:${data.aws_partition.current.partition}:sns:${var.aws_region}:${data.aws_caller_identity.current.account_id}:${local.name}-meeting-ready"
          }
        }
      }
    ]
  })
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
      Condition = { Bool = { "aws:SecureTransport" = "false" } }
    }]
  })
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
    allowed_methods = ["GET", "PUT", "HEAD"]
    allowed_origins = ["https://${aws_cloudfront_distribution.web.domain_name}"]
    expose_headers  = ["ETag"]
    max_age_seconds = 3600
  }
}

resource "aws_s3_object" "index" {
  bucket                 = aws_s3_bucket.web.id
  key                    = "index.html"
  source                 = "${path.module}/../web/index.html"
  etag                   = filemd5("${path.module}/../web/index.html")
  content_type           = "text/html; charset=utf-8"
  server_side_encryption = "aws:kms"
  kms_key_id             = aws_kms_key.web.arn
  cache_control          = "no-cache, no-store, must-revalidate"
}

resource "aws_s3_object" "styles" {
  bucket                 = aws_s3_bucket.web.id
  key                    = "styles.css"
  source                 = "${path.module}/../web/styles.css"
  etag                   = filemd5("${path.module}/../web/styles.css")
  content_type           = "text/css; charset=utf-8"
  server_side_encryption = "aws:kms"
  kms_key_id             = aws_kms_key.web.arn
  cache_control          = "public, max-age=300"
}

resource "aws_s3_object" "app" {
  bucket                 = aws_s3_bucket.web.id
  key                    = "app.js"
  source                 = "${path.module}/../web/app.js"
  etag                   = filemd5("${path.module}/../web/app.js")
  content_type           = "text/javascript; charset=utf-8"
  server_side_encryption = "aws:kms"
  kms_key_id             = aws_kms_key.web.arn
  cache_control          = "public, max-age=300"
}

resource "aws_s3_object" "architecture_html" {
  bucket                 = aws_s3_bucket.web.id
  key                    = "architecture.html"
  source                 = "${path.module}/../web/architecture.html"
  etag                   = filemd5("${path.module}/../web/architecture.html")
  content_type           = "text/html; charset=utf-8"
  server_side_encryption = "aws:kms"
  kms_key_id             = aws_kms_key.web.arn
  cache_control          = "public, max-age=300"
}

resource "aws_s3_object" "architecture_css" {
  bucket                 = aws_s3_bucket.web.id
  key                    = "architecture.css"
  source                 = "${path.module}/../web/architecture.css"
  etag                   = filemd5("${path.module}/../web/architecture.css")
  content_type           = "text/css; charset=utf-8"
  server_side_encryption = "aws:kms"
  kms_key_id             = aws_kms_key.web.arn
  cache_control          = "public, max-age=300"
}

resource "aws_s3_object" "architecture_js" {
  bucket                 = aws_s3_bucket.web.id
  key                    = "architecture.js"
  source                 = "${path.module}/../web/architecture.js"
  etag                   = filemd5("${path.module}/../web/architecture.js")
  content_type           = "text/javascript; charset=utf-8"
  server_side_encryption = "aws:kms"
  kms_key_id             = aws_kms_key.web.arn
  cache_control          = "public, max-age=300"
}

resource "aws_cognito_user_pool" "workspace" {
  name                     = "${local.name}-users"
  auto_verified_attributes = ["email"]
  mfa_configuration        = "OPTIONAL"
  deletion_protection      = "ACTIVE"

  software_token_mfa_configuration {
    enabled = true
  }

  password_policy {
    minimum_length                   = 12
    require_lowercase                = true
    require_numbers                  = true
    require_symbols                  = true
    require_uppercase                = true
    temporary_password_validity_days = 1
    password_history_size            = 8
  }

  account_recovery_setting {
    recovery_mechanism {
      name     = "verified_email"
      priority = 1
    }
  }

  user_attribute_update_settings {
    attributes_require_verification_before_update = ["email"]
  }

  schema {
    name                     = "email"
    attribute_data_type      = "String"
    required                 = true
    mutable                  = true
    developer_only_attribute = false
    string_attribute_constraints {
      min_length = 5
      max_length = 2048
    }
  }

  tags = local.tags
}

resource "aws_cognito_user_pool_domain" "workspace" {
  domain       = "${var.project_name}-${random_id.suffix.hex}"
  user_pool_id = aws_cognito_user_pool.workspace.id
}

resource "aws_cognito_user_pool_client" "dashboard" {
  name                                 = "${local.name}-dashboard"
  user_pool_id                         = aws_cognito_user_pool.workspace.id
  generate_secret                      = false
  prevent_user_existence_errors        = "ENABLED"
  enable_token_revocation              = true
  allowed_oauth_flows_user_pool_client = true
  allowed_oauth_flows                  = ["code"]
  allowed_oauth_scopes                 = ["openid", "email", "profile"]
  supported_identity_providers         = ["COGNITO"]
  callback_urls                        = ["https://${aws_cloudfront_distribution.web.domain_name}/"]
  logout_urls                          = ["https://${aws_cloudfront_distribution.web.domain_name}/"]
  access_token_validity                = 60
  id_token_validity                    = 60
  refresh_token_validity               = 5
  token_validity_units {
    access_token  = "minutes"
    id_token      = "minutes"
    refresh_token = "days"
  }
}

resource "aws_s3_object" "config" {
  bucket                 = aws_s3_bucket.web.id
  key                    = "config.js"
  content_type           = "text/javascript; charset=utf-8"
  server_side_encryption = "aws:kms"
  kms_key_id             = aws_kms_key.web.arn
  cache_control          = "no-cache, no-store, must-revalidate"
  content                = <<-CONFIG
    window.BRIEFLY_CONFIG = ${jsonencode({
      apiUrl           = aws_apigatewayv2_api.http.api_endpoint
      region           = var.aws_region
      userPoolClientId = aws_cognito_user_pool_client.dashboard.id
      userPoolDomain   = aws_cognito_user_pool_domain.workspace.domain
      dashboardUrl     = "https://${aws_cloudfront_distribution.web.domain_name}/"
    })};
  CONFIG
}

resource "aws_cloudfront_origin_access_control" "web" {
  name                              = "${local.name}-web-oac"
  description                       = "Private access to the Briefly static website bucket"
  origin_access_control_origin_type = "s3"
  signing_behavior                  = "always"
  signing_protocol                  = "sigv4"
}

resource "aws_cloudfront_response_headers_policy" "web" {
  name = "${local.name}-security-headers"

  security_headers_config {
    content_security_policy {
      content_security_policy = "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; connect-src 'self' ${aws_apigatewayv2_api.http.api_endpoint} https://${aws_cognito_user_pool_domain.workspace.domain}.auth.${var.aws_region}.amazoncognito.com https://${aws_s3_bucket.meetings.bucket}.s3.${var.aws_region}.amazonaws.com; img-src 'self' data:; media-src 'self' https://${aws_s3_bucket.meetings.bucket}.s3.${var.aws_region}.amazonaws.com; object-src 'none'; base-uri 'self'; frame-ancestors 'none'; form-action 'self' https://${aws_cognito_user_pool_domain.workspace.domain}.auth.${var.aws_region}.amazoncognito.com; upgrade-insecure-requests"
      override                  = true
    }

    content_type_options {
      override = true
    }

    frame_options {
      frame_option = "DENY"
      override     = true
    }

    referrer_policy {
      referrer_policy = "strict-origin-when-cross-origin"
      override        = true
    }

    strict_transport_security {
      access_control_max_age_sec = 63072000
      include_subdomains         = true
      preload                    = true
      override                   = true
    }

    xss_protection {
      mode_block = true
      protection = true
      override   = true
    }
  }
}

resource "aws_wafv2_web_acl" "edge" {
  provider    = aws.cloudfront
  name        = "${local.name}-edge"
  description = "Managed exploit protections and per-IP request limits for the public dashboard."
  scope       = "CLOUDFRONT"

  default_action {
    allow {}
  }

  rule {
    name     = "RateLimit"
    priority = 0

    action {
      block {}
    }

    statement {
      rate_based_statement {
        limit                 = 2000
        aggregate_key_type    = "IP"
        evaluation_window_sec = 300
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "${local.name}-edge-rate"
      sampled_requests_enabled   = true
    }
  }

  rule {
    name     = "AWSManagedCommonRules"
    priority = 1

    override_action {
      none {}
    }

    statement {
      managed_rule_group_statement {
        name        = "AWSManagedRulesCommonRuleSet"
        vendor_name = "AWS"
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "${local.name}-edge-common"
      sampled_requests_enabled   = true
    }
  }

  visibility_config {
    cloudwatch_metrics_enabled = true
    metric_name                = "${local.name}-edge"
    sampled_requests_enabled   = true
  }

  tags = local.tags
}

resource "aws_cloudfront_distribution" "web" {
  enabled             = true
  default_root_object = "index.html"
  price_class         = "PriceClass_100"
  tags                = local.tags
  web_acl_id          = aws_wafv2_web_acl.edge.arn

  origin {
    domain_name              = aws_s3_bucket.web.bucket_regional_domain_name
    origin_id                = "web-${aws_s3_bucket.web.id}"
    origin_access_control_id = aws_cloudfront_origin_access_control.web.id
  }

  default_cache_behavior {
    allowed_methods        = ["GET", "HEAD", "OPTIONS"]
    cached_methods         = ["GET", "HEAD"]
    target_origin_id       = "web-${aws_s3_bucket.web.id}"
    response_headers_policy_id = aws_cloudfront_response_headers_policy.web.id
    viewer_protocol_policy = "redirect-to-https"
    compress                = true

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
        Condition = { Bool = { "aws:SecureTransport" = "false" } }
      }
    ]
  })
}

resource "aws_kms_key_policy" "web" {
  key_id = aws_kms_key.web.key_id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "EnableAccountIamPermissions"
        Effect    = "Allow"
        Principal = { AWS = "arn:${data.aws_partition.current.partition}:iam::${data.aws_caller_identity.current.account_id}:root" }
        Action    = "kms:*"
        Resource  = "*"
      },
      {
        Sid       = "AllowCloudFrontToDecryptDashboardAssets"
        Effect    = "Allow"
        Principal = { Service = "cloudfront.amazonaws.com" }
        Action    = "kms:Decrypt"
        Resource  = "*"
        Condition = {
          StringEquals = {
            "AWS:SourceArn" = aws_cloudfront_distribution.web.arn
          }
        }
      }
    ]
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
    enabled = true
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
    enabled = true
  }

  tags = local.tags
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

resource "aws_iam_role_policy" "api" {
  name = "${local.name}-api-access"
  role = aws_iam_role.lambda_api.id
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
        Action   = ["s3:GetObject"]
        Resource = [
          "${aws_s3_bucket.meetings.arn}/uploads/*",
          "${aws_s3_bucket.meetings.arn}/transcripts/*",
        ]
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
        Action   = ["kms:GenerateDataKey", "kms:Decrypt"]
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
        Action   = ["kms:GenerateDataKey", "kms:Decrypt"]
        Resource = aws_kms_key.events.arn
      },
      {
        Effect   = "Allow"
        Action   = ["kms:Decrypt"]
        Resource = aws_kms_key.meetings.arn
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
        Action   = ["kms:Decrypt", "kms:GenerateDataKey"]
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
      MEETINGS_BUCKET = aws_s3_bucket.meetings.bucket
      MEETINGS_TABLE  = aws_dynamodb_table.meetings.name
      SEARCH_TABLE    = aws_dynamodb_table.transcript_search.name
    }
  }

  tags = local.tags

  reserved_concurrent_executions = 20

  depends_on = [aws_iam_role_policy_attachment.api_logs, aws_iam_role_policy.api]
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
    allow_origins = ["*"]
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
  api_id    = aws_apigatewayv2_api.http.id
  route_key = "$default"
  target    = "integrations/${aws_apigatewayv2_integration.api.id}"
  authorization_type = "JWT"
  authorizer_id      = aws_apigatewayv2_authorizer.cognito.id
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
