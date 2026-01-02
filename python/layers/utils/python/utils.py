import time
import json
from datetime import datetime
from zipfile import ZipFile
from io import BytesIO
from hashlib import md5
import requests


def get_file_from_url(url: str) -> BytesIO:
    response = requests.get(url, stream=True, timeout=300)
    response.raise_for_status()
    buffer = BytesIO(response.content)
    buffer.seek(0)
    return buffer


def get_md5_from_buffer(buffer: BytesIO) -> str:
    buffer.seek(0)
    return md5(buffer.read()).hexdigest()


def run_athena_query(
    query: str,
    athena_client,
    return_result: bool = True,
    poll_interval: float = 1.0,
    page_size: int = 1000,
) -> dict:
    # Initiate query
    start_args = {
        "QueryString": query,
        "QueryExecutionContext": {"Database": "metadata"},
        "WorkGroup": "primary"
    }

    response = athena_client.start_query_execution(**start_args)
    execution_id = response["QueryExecutionId"]

    # Poll for completion
    while True:
        status_response = athena_client.get_query_execution(
            QueryExecutionId=execution_id
        )
        status = status_response["QueryExecution"]["Status"]["State"]

        if status == "SUCCEEDED":
            break
        if status in ("FAILED", "CANCELLED"):
            reason = status_response["QueryExecution"]["Status"].get(
                "StateChangeReason", "Unknown error"
            )
            raise RuntimeError(f"Athena query {status.lower()}: {reason}")

        time.sleep(poll_interval)

    # Paginate results
    if return_result:
        all_rows = []
        column_info = None
        next_token = None
        is_first_page = True

        page_args = {
            "QueryExecutionId": execution_id,
            "MaxResults": page_size,
        }

        while True:
            response = athena_client.get_query_results(**page_args)

            if is_first_page:
                column_info = response["ResultSet"]["ResultSetMetadata"]["ColumnInfo"]
                all_rows.extend([x["Data"] for x in response["ResultSet"]["Rows"][1:]])
                is_first_page = False
            else:
                all_rows.extend([x["Data"] for x in response["ResultSet"]["Rows"][1:]])

            next_token = response.get("NextToken")
            if not next_token:
                break
            else:
                page_args["NextToken"] = next_token

        return {
            "Status": status,
            "ColumnInfo": column_info,
            "Rows": all_rows,
        }
    else:
        return {"Status": status}


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
    query_results = run_athena_query(
        query, athena_client
    )["Rows"][0][0]["VarCharValue"]
    if query_results != "false":
        hash_exists = True

    return hash_exists


def ingest_opl_zip(zip_file: BytesIO, bucket: str, s3_client) -> str:
    with ZipFile(zip_file) as z:
        csv_files = [name for name in z.namelist() if name.endswith(".csv")]

    if not csv_files:
        raise ValueError("No CSV files found in the ZIP archive.")
    csv_path = csv_files[0]

    csv_fn = csv_path.split("/")[-1]
    current_time = datetime.now()
    prefix = f"openpowerlifting/year={current_time.strftime('%Y')}/month={current_time.strftime('%m')}/day={current_time.strftime('%d')}/"
    key = prefix + csv_fn

    with ZipFile(zip_file) as z:
        with z.open(csv_path, "r") as csv_file:
            s3_client.upload_fileobj(csv_file, bucket, key)

    return f"s3://{bucket}/{key}"


def insert_row_data_ingest_log(
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


def get_event_hwm(event_consumer: str, athena_client, log_table: str = "metadata.data_process_log") -> int:
    read_sql = f"""
        select current_event_hwm
        from {log_table}
        where event_consumer = '{event_consumer}'
        limit 1
    """
    event_hwm = int(run_athena_query(read_sql, athena_client)["Rows"][0][0]["VarCharValue"])
    return event_hwm


def set_event_hwm(event_consumer: str, event_hwm: int, athena_client, log_table: str = "metadata.data_process_log") -> None:
    update_sql = f"""
        update {log_table}
        set current_event_hwm = {event_hwm}
        where event_consumer = '{event_consumer}'
    """
    run_athena_query(update_sql, athena_client, False)
    return
