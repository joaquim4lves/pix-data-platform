locals {
  function_name = "${var.name}-bcb-ingest"
}

resource "aws_sqs_queue" "dlq" {
  name                      = "${local.function_name}-dlq"
  message_retention_seconds = 1209600
  sqs_managed_sse_enabled   = true
}

resource "aws_cloudwatch_log_group" "bcb" {
  #checkov:skip=CKV_AWS_158:Log groups use the default AWS encryption. A customer CMK is a monthly charge this stack avoids.
  name              = "/aws/lambda/${local.function_name}"
  retention_in_days = var.log_retention_days
}

resource "aws_iam_role" "bcb" {
  name = local.function_name
  path = "/pix-data/"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Action    = "sts:AssumeRole"
      Principal = { Service = "lambda.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy" "bcb" {
  name   = local.function_name
  role   = aws_iam_role.bcb.id
  policy = data.aws_iam_policy_document.bcb.json
}

data "aws_iam_policy_document" "bcb" {
  statement {
    sid       = "Logs"
    actions   = ["logs:CreateLogStream", "logs:PutLogEvents"]
    resources = ["${aws_cloudwatch_log_group.bcb.arn}:*"]
  }

  statement {
    sid       = "ListLake"
    actions   = ["s3:ListBucket", "s3:GetBucketLocation"]
    resources = [var.bucket_arn]
  }

  statement {
    sid = "WriteRawAndQuarantine"
    actions = [
      "s3:GetObject",
      "s3:PutObject",
      "s3:DeleteObject",
    ]
    resources = [
      "${var.bucket_arn}/raw/bcb/*",
      "${var.bucket_arn}/quarantine/*",
    ]
  }

  statement {
    sid       = "DeadLetter"
    actions   = ["sqs:SendMessage"]
    resources = [aws_sqs_queue.dlq.arn]
  }
}

resource "aws_iam_role" "scheduler" {
  name = "${var.name}-bcb-scheduler"
  path = "/pix-data/"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Action    = "sts:AssumeRole"
      Principal = { Service = "scheduler.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy" "scheduler" {
  name = "${var.name}-bcb-scheduler"
  role = aws_iam_role.scheduler.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid      = "InvokeIngest"
        Effect   = "Allow"
        Action   = "lambda:InvokeFunction"
        Resource = aws_lambda_function.bcb.arn
      },
      {
        Sid      = "ScheduleDeadLetter"
        Effect   = "Allow"
        Action   = "sqs:SendMessage"
        Resource = aws_sqs_queue.dlq.arn
      },
    ]
  })
}

resource "aws_s3_object" "zip" {
  bucket = var.bucket_name
  key    = "artifacts/bcb_ingest.zip"
  source = var.zip_path
  etag   = filemd5(var.zip_path)

  tags = {
    BucketVersioning = var.bucket_versioning_id
  }
}

resource "aws_lambda_function" "bcb" {
  #checkov:skip=CKV_AWS_117:The function calls a public API. A VPC would require a NAT gateway.
  #checkov:skip=CKV_AWS_173:Environment values are a bucket name and a sentinel, not secrets.
  #checkov:skip=CKV_AWS_272:Code signing is out of scope for this portfolio slice.
  #checkov:skip=CKV_AWS_50:X-Ray is a separate meter. CloudWatch Logs cover a daily run.
  function_name = local.function_name
  role          = aws_iam_role.bcb.arn
  handler       = "ingestion.bcb.handler.handler"
  runtime       = "python3.12"
  architectures = ["x86_64"]
  memory_size   = var.memory_mb
  timeout       = var.timeout_seconds

  reserved_concurrent_executions = var.reserved_concurrency

  s3_bucket         = aws_s3_object.zip.bucket
  s3_key            = aws_s3_object.zip.key
  s3_object_version = aws_s3_object.zip.version_id
  source_code_hash  = filebase64sha256(var.zip_path)

  dead_letter_config {
    target_arn = aws_sqs_queue.dlq.arn
  }

  environment {
    variables = {
      S3_BUCKET        = var.bucket_name
      AWS_ENDPOINT_URL = "aws"
      LOOKBACK_MONTHS  = tostring(var.lookback_months)
      LOG_LEVEL        = "INFO"
    }
  }

  depends_on = [
    aws_cloudwatch_log_group.bcb,
    aws_iam_role_policy.bcb,
  ]
}

resource "aws_scheduler_schedule" "bcb" {
  for_each = var.schedules

  name                         = "${var.name}-bcb-${each.key}"
  schedule_expression          = each.value
  schedule_expression_timezone = var.schedule_timezone

  flexible_time_window {
    mode = "OFF"
  }

  target {
    arn      = aws_lambda_function.bcb.arn
    role_arn = aws_iam_role.scheduler.arn
    input    = jsonencode({ mode = "ingest" })

    dead_letter_config {
      arn = aws_sqs_queue.dlq.arn
    }

    retry_policy {
      maximum_event_age_in_seconds = 3600
      maximum_retry_attempts       = 2
    }
  }

  depends_on = [aws_iam_role_policy.scheduler]
}

resource "aws_lambda_permission" "scheduler" {
  for_each = aws_scheduler_schedule.bcb

  statement_id  = "AllowScheduler${each.key}"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.bcb.function_name
  principal     = "scheduler.amazonaws.com"
  source_arn    = each.value.arn
}
