# bcb_ingest

Lambda for `ingestion.bcb.handler.handler`, plus EventBridge Scheduler entries and a dead-letter queue.

The package is uploaded to `artifacts/bcb_ingest.zip` because a PyArrow zip can exceed Lambda's 50 MB direct-upload limit. `AWS_ENDPOINT_URL=aws` selects real AWS: Lambda rejects an empty environment value, and the handler treats `aws` the same as an empty string. The function is not in a VPC.
