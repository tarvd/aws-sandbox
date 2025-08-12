from typing import Any
import logging
from zipfile import ZipFile
from io import BytesIO

import boto3
import requests


URL = "https://openpowerlifting.gitlab.io/opl-csv/files/openpowerlifting-latest.zip"
BUCKET = "ted-sand-dev-s3-use2-data"


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
        filename="lambda_ingest_openpowerlifting.log",
        encoding="utf-8",
        level=logging.INFO,
    )
    logger.info(
        f"Lambda function for Openpowerlifting data ingestion started. URL: {URL}, Bucket: {BUCKET}"
    )

    s3 = boto3.client("s3")

    try:
        response = requests.get(URL)
        response.raise_for_status()

        with ZipFile(BytesIO(response.content)) as z:
            csv_files = [name for name in z.namelist() if name.endswith(".csv")]
            if not csv_files:
                raise ValueError("No CSV files found in the ZIP archive.")

            csv_path = csv_files[0]
            csv_fn = csv_path.split("/")[-1]
            key = f"openpowerlifting/{csv_fn}"
            with z.open(csv_path, "r") as csv_file:
                s3.upload_fileobj(csv_file, BUCKET, key)

        logger.info(
            "Lambda function for Openpowerlifting data ingestion ended: Success!"
        )
        return {"statusCode": 200, "message": "File ingested successfully."}

    except Exception as e:
        logger.error(
            f"Lambda function for Openpowerlifting data ingestion ended: Failure. {str(e)}"
        )
        return {"statusCode": 500, "message": "File ingestion failed."}
