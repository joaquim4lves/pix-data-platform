# catalog

Glue databases for the PIX schemas and external tables over `raw/bcb` and `raw/app`.

BCB partitions are an enum of real `YYYYMM` values, so Athena does not list months such as `202013`. App partitions are a date projection on `dt`. There is no crawler. Column names and types come from `columns.json`, which is checked against the Parquet writers.
