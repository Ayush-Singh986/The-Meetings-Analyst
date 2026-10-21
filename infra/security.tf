provider "aws" {
  alias  = "us_east_1"
  region = "us-east-1"
}

resource "aws_kms_key" "meetings" {
  description             = "Encrypt Briefly meeting recordings, transcripts, and records"
  enable_key_rotation     = true
  deletion_window_in_days = 30
  tags                    = local.tags
}

resource "aws_kms_alias" "meetings" {
  name          = "alias/${local.name}-meetings"
  target_key_id = aws_kms_key.meetings.key_id
}

resource "aws_kms_key" "web" {
  description             = "Encrypt Briefly dashboard assets"
  enable_key_rotation     = true
  deletion_window_in_days = 30
  tags                    = local.tags
}

resource "aws_kms_alias" "web" {
  name          = "alias/${local.name}-web"
  target_key_id = aws_kms_key.web.key_id
}

resource "aws_kms_key" "events" {
  description             = "Encrypt Briefly ready notifications"
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
        Sid       = "EnableAccountAdministration"
        Effect    = "Allow"
        Principal = { AWS = "arn:${data.aws_partition.current.partition}:iam::${data.aws_caller_identity.current.account_id}:root" }
        Action    = "kms:*"
        Resource  = "*"
      },
      {
        Sid       = "AllowSnsForThisAccount"
        Effect    = "Allow"
        Principal = { Service = "sns.amazonaws.com" }
        Action    = ["kms:Decrypt", "kms:GenerateDataKey*"]
        Resource  = "*"
        Condition = {
          StringEquals = {
            "aws:SourceAccount" = data.aws_caller_identity.current.account_id
          }
        }
      }
    ]
  })
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
    temporary_password_validity_days = 3
    password_history_size            = 5
  }

  verification_message_template {
    default_email_option = "CONFIRM_WITH_CODE"
  }

  schema {
    attribute_data_type = "String"
    name                = "email"
    required            = true
    mutable             = true
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
  access_token_validity                = 15
  id_token_validity                    = 15
  refresh_token_validity               = 1
  token_validity_units {
    access_token  = "minutes"
    id_token      = "minutes"
    refresh_token = "days"
  }
  allowed_oauth_flows_user_pool_client = true
  allowed_oauth_flows                  = ["code"]
  allowed_oauth_scopes                 = ["openid", "email", "profile"]
  supported_identity_providers         = ["COGNITO"]
  callback_urls                        = ["https://${aws_cloudfront_distribution.web.domain_name}/"]
  logout_urls                          = ["https://${aws_cloudfront_distribution.web.domain_name}/"]
}

resource "aws_wafv2_web_acl" "edge" {
  provider    = aws.us_east_1
  name        = "${local.name}-edge"
  description = "Managed protections and request-rate limits for the Briefly dashboard."
  scope       = "CLOUDFRONT"

  default_action {
    allow {}
  }

  rule {
    name     = "AWSManagedCommonRules"
    priority = 10
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
      metric_name                = "${local.name}-managed-rules"
      sampled_requests_enabled   = true
    }
  }

  rule {
    name     = "PerIpRateLimit"
    priority = 20
    action {
      block {}
    }
    statement {
      rate_based_statement {
        limit              = 2000
        aggregate_key_type = "IP"
      }
    }
    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "${local.name}-rate-limit"
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

resource "aws_kms_key_policy" "web" {
  key_id = aws_kms_key.web.key_id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "EnableAccountAdministration"
        Effect    = "Allow"
        Principal = { AWS = "arn:${data.aws_partition.current.partition}:iam::${data.aws_caller_identity.current.account_id}:root" }
        Action    = "kms:*"
        Resource  = "*"
      },
      {
        Sid       = "AllowCloudFrontDecryptAssets"
        Effect    = "Allow"
        Principal = { Service = "cloudfront.amazonaws.com" }
        Action    = ["kms:Decrypt", "kms:DescribeKey"]
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
