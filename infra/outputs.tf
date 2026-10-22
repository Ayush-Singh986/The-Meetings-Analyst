output "dashboard_url" {
  description = "HTTPS URL for the Briefly dashboard."
  value       = "https://${aws_cloudfront_distribution.web.domain_name}"
}

output "api_url" {
  description = "Base URL for the Briefly HTTP API."
  value       = aws_apigatewayv2_api.http.api_endpoint
}

output "zoom_webhook_url" {
  description = "Zoom recording.completed webhook URL."
  value       = "${aws_apigatewayv2_api.http.api_endpoint}/webhooks/zoom"
}

output "teams_webhook_url" {
  description = "Microsoft Graph recording notification URL."
  value       = "${aws_apigatewayv2_api.http.api_endpoint}/webhooks/teams"
}

output "zoom_webhook_secret_arn" {
  description = "Secrets Manager ARN for the Zoom webhook verification token."
  value       = aws_secretsmanager_secret.zoom_webhook.arn
}

output "zoom_oauth_secret_arn" {
  description = "Secrets Manager ARN for Zoom Server-to-Server OAuth credentials."
  value       = aws_secretsmanager_secret.zoom_oauth.arn
}

output "teams_graph_secret_arn" {
  description = "Secrets Manager ARN for Microsoft Graph app credentials and webhook client state."
  value       = aws_secretsmanager_secret.teams_graph.arn
}

output "cognito_user_pool_id" {
  description = "Amazon Cognito user pool ID for workspace sign-in."
  value       = aws_cognito_user_pool.workspace.id
}

output "cognito_app_client_id" {
  description = "Public OAuth client ID configured for the dashboard."
  value       = aws_cognito_user_pool_client.dashboard.id
}

output "cognito_hosted_ui_url" {
  description = "Managed sign-in and self-service user registration URL."
  value       = "https://${aws_cognito_user_pool_domain.workspace.domain}.auth.${var.aws_region}.amazoncognito.com"
}

output "meetings_bucket" {
  description = "Private S3 bucket for uploaded recordings and transcripts."
  value       = aws_s3_bucket.meetings.bucket
}

output "meetings_table" {
  description = "DynamoDB table containing meeting metadata and summaries."
  value       = aws_dynamodb_table.meetings.name
}

output "transcript_search_table" {
  description = "DynamoDB table containing searchable transcript chunks."
  value       = aws_dynamodb_table.transcript_search.name
}

output "notification_topic_arn" {
  description = "SNS topic for meeting-ready notifications."
  value       = aws_sns_topic.ready.arn
}
