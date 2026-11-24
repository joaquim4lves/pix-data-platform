# lake

One data-lake bucket and a separate access-log bucket.

Prefixes, by convention rather than by empty marker objects:

- `raw/bcb/` and `raw/app/` are the Parquet zones
- `curated/` is reserved for a later dbt or CTAS layer
- `athena-results/` expires after a week
- `quarantine/` expires after 30 days
- `artifacts/` holds the Lambda zip packages

Encryption is SSE-S3. Public access is blocked. Versioning is on so a bad overwrite can be recovered, and noncurrent versions expire so that safety does not become a storage bill. `raw/` and `curated/` current objects are not expired.
