# cdc_sink

SQS queue, dead-letter queue, and the Lambda that writes `raw/app/<table>/dt=YYYY-MM-DD/`.

The event source mapping sets `ReportBatchItemFailures`, which is the response the handler already returns as `batchItemFailures`. The local pgoutput consumer publishes to this queue. Postgres stays in Docker.
