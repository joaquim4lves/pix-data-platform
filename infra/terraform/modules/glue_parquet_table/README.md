# glue_parquet_table

One external Parquet table with partition projection. The caller supplies the columns, the S3 location template, and the projection parameters. This module does not create a crawler and does not run `MSCK REPAIR`.
