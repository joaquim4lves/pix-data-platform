#!/usr/bin/env bash
# Build the two Lambda zips Terraform uploads to s3://<lake>/artifacts/.
# The packages target the Amazon Linux Python 3.12 runtime (x86_64).
# boto3 is omitted: the Lambda runtime provides it.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
BUILD="${ROOT}/infra/build"
PYTHON="${PYTHON:-python3}"
PLATFORM="${LAMBDA_PLATFORM:-manylinux2014_x86_64}"
PYARROW_SPEC="${PYARROW_SPEC:-pyarrow==17.0.0}"

rm -rf "${BUILD}"
mkdir -p "${BUILD}"

vendor() {
  local dest="$1"
  shift
  mkdir -p "${dest}"
  "${PYTHON}" -m pip install \
    --platform "${PLATFORM}" \
    --implementation cp \
    --python-version 3.12 \
    --only-binary=:all: \
    --upgrade \
    --target "${dest}" \
    "$@"
  rm -rf "${dest}/boto3" "${dest}/botocore" "${dest}/s3transfer"
  find "${dest}" -type d \( -name "__pycache__" -o -name "boto3-*.dist-info" -o -name "botocore-*.dist-info" -o -name "s3transfer-*.dist-info" \) -prune -exec rm -rf {} +
}

copy_tree() {
  local src="$1"
  local dest="$2"
  mkdir -p "${dest}"
  cp -a "${src}/." "${dest}/"
  find "${dest}" -type d -name "__pycache__" -prune -exec rm -rf {} +
}

BCB="${BUILD}/bcb_src"
vendor "${BCB}" "httpx==0.27.2" "pydantic==2.9.2" "${PYARROW_SPEC}"
copy_tree "${ROOT}/ingestion" "${BCB}/ingestion"
(
  cd "${BCB}"
  zip -qr "${BUILD}/bcb_ingest.zip" .
)

# cdc.settings imports ingestion.bcb.settings and payments.settings.
# The handler does not import the FastAPI app or the pgoutput consumer.
CDC="${BUILD}/cdc_src"
vendor "${CDC}" "${PYARROW_SPEC}"
mkdir -p "${CDC}/ingestion/bcb" "${CDC}/payments"
cp "${ROOT}/ingestion/__init__.py" "${CDC}/ingestion/__init__.py"
cp "${ROOT}/ingestion/bcb/__init__.py" "${CDC}/ingestion/bcb/__init__.py"
cp "${ROOT}/ingestion/bcb/settings.py" "${CDC}/ingestion/bcb/settings.py"
cp "${ROOT}/payments/__init__.py" "${CDC}/payments/__init__.py"
cp "${ROOT}/payments/settings.py" "${CDC}/payments/settings.py"
copy_tree "${ROOT}/cdc" "${CDC}/cdc"
(
  cd "${CDC}"
  zip -qr "${BUILD}/cdc_sink.zip" .
)

echo "Wrote ${BUILD}/bcb_ingest.zip ($(wc -c < "${BUILD}/bcb_ingest.zip") bytes)"
echo "Wrote ${BUILD}/cdc_sink.zip ($(wc -c < "${BUILD}/cdc_sink.zip") bytes)"
