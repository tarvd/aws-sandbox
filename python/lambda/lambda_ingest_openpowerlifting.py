import os
import logging
import traceback
from datetime import datetime, timezone
from typing import Any

import boto3

from utils.ingestion import get_file_from_url, get_md5_from_buffer, compare_ingestion_hash, ingest_opl_zip, insert_row_to_ingest_log


BUCKET = os.environ["BUCKET"]
LAMBDA = os.environ["LAMBDA"]
SNS_TOPIC_ARN = os.environ["SNS_TOPIC_ARN"]
URL = os.environ["URL"]

athena = boto3.client("athena")
s3 = boto3.client("s3")
sns = boto3.client("sns")

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """
    Ingests the latest Open Powerlifting CSV file from openpowerlifting.org and uploads it to S3.
    Parameters:
        event: Dict containing the Lambda function event data
        context: Lambda runtime context
    Returns:
        Dict containing status message
    """

    logger.info(
        f"Lambda function {LAMBDA} started. URL: {URL}, Bucket: {BUCKET}"
    )

    try:
        zip_file = get_file_from_url(URL)
        hash = get_md5_from_buffer(zip_file)
        hash_exists = compare_ingestion_hash(hash, LAMBDA, athena)

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
            "event_producer": LAMBDA,
            "event_type": "new_file",
            "source_system": "Openpowerlifting.org",
            "file_md5_hash": hash,
            "s3_location": s3_location,
        }
        logger.info(f"File ingested, sending payload to Ingest Data Log: {payload}")
        insert_row_to_ingest_log(
            payload,
            athena
        )


        lambda_status = "SUCCESS"
        message = "File ingested successfully."
        status = {"statusCode": 200, "message": message}
        return status

    except Exception as e:
        logger.error(f"Error: {e}")

        lambda_status = "FAILURE"
        message = f"\n\nLambda failed:\n\n{traceback.format_exc()}"
        raise e
    
    finally:
        logger.info(status)
        logger.info("Sending SNS notification")
        sns.publish(
            TopicArn=SNS_TOPIC_ARN,
            Subject=f"Lambda {LAMBDA}: {lambda_status}",
            Message=message
        )
