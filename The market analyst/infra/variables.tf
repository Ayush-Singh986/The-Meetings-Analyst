variable "aws_region" {
  description = "AWS region for the application resources."
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Lowercase prefix used to name application resources."
  type        = string
  default     = "briefly-meeting-analyst"

  validation {
    condition     = can(regex("^[a-z][a-z0-9-]{2,30}$", var.project_name))
    error_message = "project_name must be 3-31 lowercase letters, digits, or hyphens and start with a letter."
  }
}

variable "notification_email" {
  description = "Optional email address subscribed to meeting-ready notifications."
  type        = string
  default     = ""
}

variable "bedrock_model_id" {
  description = "Bedrock model ID used to analyze a completed transcript."
  type        = string
  default     = "anthropic.claude-3-haiku-20240307-v1:0"
}

variable "transcribe_language_code" {
  description = "Amazon Transcribe language code for meeting recordings."
  type        = string
  default     = "en-US"
}
