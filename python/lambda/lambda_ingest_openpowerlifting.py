import os
import time
import json
import logging
import traceback
from datetime import datetime, timezone
from typing import Any
from zipfile import ZipFile
from io import BytesIO
from hashlib import md5

import boto3
import requests


BUCKET = os.environ["BUCKET"]
LAMBDA = os.environ["LAMBDA"]
S3_OUTPUT_LOCATION = os.environ["S3_OUTPUT_LOCATION"]
SNS_TOPIC_ARN = os.environ["SNS_TOPIC_ARN"]
URL = os.environ["URL"]

athena = boto3.client("athena")
s3 = boto3.client("s3")
sns = boto3.client("sns")


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
    database: str,
    output_location: str,
    return_result: bool = True,
    poll_interval: float = 1.0,
    page_size: int = 1000,
) -> dict:
    # Initiate query
    start_args = {
        "QueryString": query,
        "QueryExecutionContext": {"Database": database},
        "ResultConfiguration": {"OutputLocation": output_location},
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
            "ColumnInfo": column_info,
            "Rows": all_rows,
        }


def compare_ingestion_hash(
    hash: str,
    athena_client,
    s3_output_location: str,
    log_table: str = "metadata.data_ingest_log",
    hash_column: str = "file_md5_hash",
    database: str = "metadata",
) -> bool:
    hash_exists = False
    query = f"select count(*) > 0 as hash_exists from {log_table} where {hash_column} = '{hash}'"
    query_results = run_athena_query(
        query, athena_client, database, s3_output_location
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
    output_location: str,
    database: str = "metadata",
    log_table: str = "metadata.data_ingest_log",
) -> None:
    insert_sql = f"""
        insert into {log_table} (event_id, ingest_ts, event_type, source_system, file_md5_hash, payload)
        select 
            coalesce(max(event_id)+1,0) as event_id,
            cast('{payload["ingest_ts"]}' as timestamp) as ingest_ts,
            '{payload["event_type"]}' as event_type,
            '{payload["source_system"]}' as source_system,
            '{payload["file_md5_hash"]}' as file_md5_hash,
            '{json.dumps(payload)}' as payload
        from {log_table};
    """
    run_athena_query(insert_sql, athena_client, database, output_location, False)


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """
    Ingests the latest Open Powerlifting CSV file from openpowerlifting.org and uploads it to S3.
    Parameters:
        event: Dict containing the Lambda function event data
        context: Lambda runtime context
    Returns:
        Dict containing status message
    """

    logger = logging.getLogger(__name__)
    logging.basicConfig(
        filename=f"{LAMBDA}.log",
        encoding="utf-8",
        level=logging.INFO,
    )
    logger.info(
        f"Lambda function {LAMBDA} started. URL: {URL}, Bucket: {BUCKET}"
    )

    try:
        zip_file = get_file_from_url(URL)
        hash = get_md5_from_buffer(zip_file)
        hash_exists = compare_ingestion_hash(hash, athena, S3_OUTPUT_LOCATION)

        logger.info(
            f"Zip file downloaded. MD5 hash: {hash} , Hash exists in data ingestion log: {hash_exists}"
        )

        if hash_exists:
            lambda_status = "NO NEW DATA"
            message = "No new data to ingest."
            status = {"statusCode": 200, "message": message}
            return status
        
        logger.info("Ingesting file obtained from URL.")
        s3_location = ingest_opl_zip(zip_file, BUCKET, s3)

        payload = {
            "ingest_ts": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S.%f"),
            "event_type": "new_file",
            "source_system": "Openpowerlifting.org",
            "file_md5_hash": hash,
            "s3_location": s3_location,
        }
        logger.info(f"File ingested, sending payload to Ingest Data Log: {payload}")
        insert_row_data_ingest_log(
            payload,
            athena,
            S3_OUTPUT_LOCATION
        )


        lambda_status = "SUCCESS"
        message = "File ingested successfully."
        status = {"statusCode": 200, "message": message}
        return status

    except Exception as e:
        logger.error(f"Error: {e}")

        lambda_status = "FAILURE"
        message = f"\n\nLambda failed:\n\n{traceback.format_exc()}"
        status = {"statusCode": 500, "message": message}
        return status
    
    finally:
        logger.info(status)
        logger.info("Sending SNS notification")
        sns.publish(
            TopicArn=SNS_TOPIC_ARN,
            Subject=f"Lambda {LAMBDA}: {lambda_status}",
            Message=message
        )
