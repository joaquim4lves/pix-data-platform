"""Asset URIs shared by the DAGs.

The bucket name is configuration (``S3_BUCKET``), read when the module is
imported. It is not a credential. Cosmos model assets stay off: Airflow 3
rejects some of the OpenLineage URIs Cosmos would emit. These URIs are the
contract downstream DAGs schedule on.
"""

from __future__ import annotations

import os

from airflow.sdk import Asset


def _bucket() -> str:
    return os.environ.get("S3_BUCKET", "pix-data-local")


RAW_BCB = Asset(f"s3://{_bucket()}/raw/bcb/")
RAW_APP = Asset(f"s3://{_bucket()}/raw/app/")
BCB_MARTS = Asset("dbt://pix_data_platform/bcb_marts")
CUR_APP = Asset("dbt://pix_data_platform/cur_app")
