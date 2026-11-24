FROM apache/airflow:3.4.0-python3.12

USER airflow
COPY --chown=airflow:root requirements/airflow-image.txt /tmp/airflow-image.txt
RUN pip install --no-cache-dir "apache-airflow==${AIRFLOW_VERSION}" -r /tmp/airflow-image.txt

ENV PYTHONPATH=/opt/airflow/project \
    AIRFLOW__CORE__LOAD_EXAMPLES=false \
    AIRFLOW__CORE__DAGS_FOLDER=/opt/airflow/dags
