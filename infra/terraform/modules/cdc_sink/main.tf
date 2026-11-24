locals {
  function_name = "${var.name}-cdc-sink"
  queue_name    = "${var.name}-cdc"
}

resource "aws_sqs_queue" "dlq" {
  name                      = "${local.queue_name}-dlq"
  message_retention_seconds = 1209600
  sqs_managed_sse_enabled   = true

  lifecycle {
    precondition {
      condition     = var.visibility_timeout_seconds >= var.timeout_seconds
      error_message = "SQS visibility timeout must be at least the sink Lambda timeout."
    }
  }
}

resource "aws_sqs_queue" "cdc" {
  name                       = local.queue_name
  visibility_timeout_seconds = var.visibility_timeout_seconds
  sqs_managed_sse_enabled    = true

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.dlq.arn
    maxReceiveCount     = var.max_receive_count
  })
}

resource "aws_sqs_queue_policy" "dlq" {
  queue_url = aws_sqs_queue.dlq.id
  policy    = data.aws_iam_policy_document.dlq.json
}

data "aws_iam_policy_document" "dlq" {
  statement {
    sid       = "AllowSourceRedrive"
    actions   = ["sqs:SendMessage"]
    resources = [aws_sqs_queue.dlq.arn]

    principals {
      type        = "Service"
      identifiers = ["sqs.amazonaws.com"]
    }

    condition {
      test     = "ArnEquals"
      variable = "aws:SourceArn"
      values   = [aws_sqs_queue.cdc.arn]
    }
  }
}

resource "aws_cloudwatch_log_group" "sink" {
  #checkov:skip=CKV_AWS_158:Log groups use the default AWS encryption. A customer CMK is a monthly charge this stack avoids.
  name              = "/aws/lambda/${local.function_name}"
  retention_in_days = var.log_retention_days
}

resource "aws_iam_role" "sink" {
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

resource "aws_iam_role_policy" "sink" {
  name   = local.function_name
  role   = aws_iam_role.sink.id
  policy = data.aws_iam_policy_document.sink.json
}

data "aws_iam_policy_document" "sink" {
  statement {
    sid       = "Logs"
    actions   = ["logs:CreateLogStream", "logs:PutLogEvents"]
    resources = ["${aws_cloudwatch_log_group.sink.arn}:*"]
  }

  statement {
    sid       = "ListLake"
    actions   = ["s3:ListBucket", "s3:GetBucketLocation"]
    resources = [var.bucket_arn]
  }

  statement {
    sid = "WriteAppRaw"
    actions = [
      "s3:GetObject",
      "s3:PutObject",
    ]
    resources = ["${var.bucket_arn}/raw/app/*"]
  }

  statement {
    sid = "ConsumeQueue"
    actions = [
      "sqs:ReceiveMessage",
      "sqs:DeleteMessage",
      "sqs:GetQueueAttributes",
      "sqs:ChangeMessageVisibility",
    ]
    resources = [aws_sqs_queue.cdc.arn]
  }

  statement {
    sid       = "DeadLetter"
    actions   = ["sqs:SendMessage"]
    resources = [aws_sqs_queue.dlq.arn]
  }
}

resource "aws_s3_object" "zip" {
  bucket = var.bucket_name
  key    = "artifacts/cdc_sink.zip"
  source = var.zip_path
  etag   = filemd5(var.zip_path)

  tags = {
    BucketVersioning = var.bucket_versioning_id
  }
}

resource "aws_lambda_function" "sink" {
  #checkov:skip=CKV_AWS_117:The sink only talks to S3 and SQS. A VPC would require a NAT gateway.
  #checkov:skip=CKV_AWS_173:Environment values are a bucket name and a sentinel, not secrets.
  #checkov:skip=CKV_AWS_272:Code signing is out of scope for this portfolio slice.
  #checkov:skip=CKV_AWS_50:X-Ray is a separate meter. CloudWatch Logs and the DLQ cover this path.
  function_name = local.function_name
  role          = aws_iam_role.sink.arn
  handler       = "cdc.handler.handler"
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
      LOG_LEVEL        = "INFO"
    }
  }

  depends_on = [
    aws_cloudwatch_log_group.sink,
    aws_iam_role_policy.sink,
  ]
}

resource "aws_lambda_event_source_mapping" "cdc" {
  event_source_arn        = aws_sqs_queue.cdc.arn
  function_name           = aws_lambda_function.sink.arn
  batch_size              = var.batch_size
  function_response_types = ["ReportBatchItemFailures"]

  scaling_config {
    maximum_concurrency = var.reserved_concurrency
  }

  depends_on = [aws_iam_role_policy.sink]
}
