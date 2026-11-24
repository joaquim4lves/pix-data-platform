# Cost estimate

Planning prices for the v0.4 account. They are the long-standing us-east-1 list prices used to size this stack, not a quote from the AWS Price List API. Check the billing console before leaving the stack applied for months. The budget in Terraform is the alarm.

The workload is three monthly public extracts, a small CDC log from a laptop, one ingest a day, and ad hoc Athena queries. The Parquet history from 2020-11 to the present fits in well under 1 GB.

| Line | What this stack does | Planning rate (us-east-1) | Expected month |
| --- | --- | --- | --- |
| S3 Standard storage | Lake plus access logs, under 1 GB | $0.023 / GB-month | $0 in the 12-month 5 GB allotment. A few cents after that |
| S3 requests | Partition overwrites and Athena reads | $0.005 / 1,000 PUT, $0.0004 / 1,000 GET | $0 inside the request allotment, otherwise cents |
| Lambda | Daily ingest at 1024 MB for a few minutes, plus small CDC batches | 400,000 GB-seconds and 1M requests free, then about $0.0000166667 / GB-second | $0 |
| EventBridge Scheduler | About 32 invocations a month | 14 million invocations free | $0 |
| SQS | Laptop to sink, including the dead-letter queues | 1 million requests free | $0 |
| Glue Data Catalog | Six databases, six external tables, no crawler | 1 million metadata objects free | $0 |
| Glue crawlers | Not created | about $0.44 / DPU-hour | $0 |
| Athena | Workgroup cutoff 1 GiB per query | $5 / TB scanned, no free tier | A query that hits the cap is about half a cent. A filtered month is less |
| CloudWatch Logs | 14-day retention | about $0.50 / GB ingested after the free allotment | $0 to a few cents |
| Budgets | One monthly budget | First two budgets free | $0 |
| NAT gateway | Not created | about $0.045 / hour plus data | about $32 avoided |
| Application load balancer | Not created | about $0.0225 / hour plus LCUs | about $16 avoided |
| RDS or EC2 | Not created | always-on instance hours | avoided |
| KMS customer-managed keys | Not created. SSE-S3 and SQS-managed keys instead | $1 / key-month plus requests | avoided |
| Data transfer in | Olinda responses into Lambda | inbound is free | $0 |

A quiet month is about $0 while the 12-month free tier lasts, and it should stay under $1 after that, as long as nobody raises the Athena cutoff and nobody adds a NAT gateway, a database, or a load balancer. The USD 5 budget is there for that mistake. It covers the whole account, so it is only the right number when the account is dedicated to this portfolio.

São Paulo (`sa-east-1`) has higher list prices. S3 Standard there has historically been on the order of one and a half to two times the us-east-1 storage rate. The same architecture at this volume still fits under $5. It does not fit if the free-tier assumption was doing all of the work and the account is already past month 12 and also scanning terabytes. The cutoff prevents the terabytes.

Athena CloudWatch metrics published by the workgroup are AWS service metrics. This stack does not create custom metrics, X-Ray traces, or a Kinesis stream.
