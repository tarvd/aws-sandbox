import json
from io import BytesIO
from hashlib import md5
import requests

from utils.common import run_athena_query


def get_file_from_url(url: str) -> BytesIO:
    response = requests.get(url, stream=True, timeout=300)
    response.raise_for_status()
    buffer = BytesIO(response.content)
    buffer.seek(0)
    return buffer


def get_md5_from_buffer(buffer: BytesIO) -> str:
    buffer.seek(0)
    return md5(buffer.read()).hexdigest()


def compare_ingestion_hash(
    hash: str,
    lambda_function: str,
    athena_client,
    log_table: str = "metadata.data_ingest_log",
) -> bool:
    hash_exists = False
    query = f"""
        select count(*) > 0 as hash_exists 
        from {log_table}
        where file_md5_hash = '{hash}'
        and event_producer = '{lambda_function}'
    """
    query_results = run_athena_query(query, athena_client)["Rows"][0][0]["VarCharValue"]
    if query_results != "false":
        hash_exists = True

    return hash_exists


def insert_row_to_ingest_log(
    payload: dict,
    athena_client,
    log_table: str = "metadata.data_ingest_log",
) -> None:
    insert_sql = f"""
        insert into {log_table} (event_id, ingest_ts, event_producer, event_type, source_system, file_md5_hash, payload)
        select 
            coalesce(max(event_id)+1,0) as event_id,
            cast('{payload["ingest_ts"]}' as timestamp) as ingest_ts,
            '{payload["event_producer"]}' as event_producer,
            '{payload["event_type"]}' as event_type,
            '{payload["source_system"]}' as source_system,
            '{payload["file_md5_hash"]}' as file_md5_hash,
            '{json.dumps(payload)}' as payload
        from {log_table};
    """
    run_athena_query(insert_sql, athena_client, False)
    return
