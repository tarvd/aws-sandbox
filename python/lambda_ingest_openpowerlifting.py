from typing import Dict, Any
import logging
from zipfile import ZipFile
from io import BytesIO

import boto3
import requests


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Main Lambda handler function
    Parameters:
        event: Dict containing the Lambda function event data
        context: Lambda runtime context
    Returns:
        Dict containing status message
    """

    try:
        logger = logging.getLogger(__name__)
        logging.basicConfig(filename=f"lambda_ingest_openpowerlifting.log", encoding='utf-8', level=logging.INFO)
        logger.info("Starting Lambda function")
        s3 = boto3.client("s3")

        url = "https://openpowerlifting.gitlab.io/opl-csv/files/openpowerlifting-latest.zip"
        bucket = "ted-sand-dev-s3-use2-data"

        logger.info("Requesting response from HTTP endpoint")
        logger.info(f"URL: {url}")
        response = requests.get(url)
        response.raise_for_status()

        logger.info("Opening ZIP file")
        with ZipFile(BytesIO(response.content)) as z:
            csv_files = [name for name in z.namelist() if name.endswith(".csv")]

            if not csv_files:
                raise ValueError("No CSV files found in the ZIP archive.")

            csv_path = csv_files[0]
            csv_fn = csv_path.split("/")[-1]
            key = f"openpowerlifting/{csv_fn}"

            logger.info("Uploading CSV file to S3")
            logger.info(f"Bucket: {bucket}")
            logger.info(f"Key: {key}")
            with z.open(csv_path, "r") as csv_file:
                s3.upload_fileobj(csv_file, bucket, key)

        logger.info("File ingested successfully")
        logger.info("Ending Lambda function")
        return {"statusCode": 200, "message": f"File ingested successfully."}

    except Exception as e:
        logger.error(f"Error loading file: {str(e)}")
        logger.info("Ending Lambda function")
        return {"statusCode": 500, "message": f"File ingestion failed."}
