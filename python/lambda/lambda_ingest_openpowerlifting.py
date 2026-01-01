import os
import logging
import traceback

from typing import Any
from zipfile import ZipFile
from io import BytesIO

import boto3
import requests

BUCKET = os.environ["BUCKET"]
LAMBDA = os.environ["LAMBDA"]
PREFIX = os.environ["PREFIX"]
SNS_TOPIC_ARN = os.environ["SNS_TOPIC_ARN"]
URL = os.environ["URL"]


s3 = boto3.client("s3")
sns = boto3.client("sns")


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


    try:
        response = requests.get(URL)
        response.raise_for_status()

        with ZipFile(BytesIO(response.content)) as z:
            csv_files = [name for name in z.namelist() if name.endswith(".csv")]
    
            if not csv_files:
                raise ValueError("No CSV files found in the ZIP archive.")
            csv_path = csv_files[0]

            csv_fn = csv_path.split("/")[-1]
            csv_fn_split = csv_fn.split("-")
            if len(csv_fn_split) >= 4:
                year_val, month_val, day_val = csv_fn.split("-")[1:4]
                if (
                    len(year_val) == 4
                    and len(month_val) == 2
                    and len(day_val) == 2
                    and year_val.isdigit()
                    and month_val.isdigit()
                    and day_val.isdigit()
                    and year_val >= "2000"
                    and year_val <= "3000"
                    and month_val >= "01"
                    and month_val <= "12"
                    and day_val >= "01"
                    and day_val <= "31"
                ):
                    prefix = f"openpowerlifting/year={year_val}/month={month_val}/day={day_val}/"
            else:
                prefix = "openpowerlifting/year=__HIVE_DEFAULT_PARTITION__/month=__HIVE_DEFAULT_PARTITION__/day=__HIVE_DEFAULT_PARTITION__/"
            key = prefix + csv_fn

            with z.open(csv_path, "r") as csv_file:
                s3.upload_fileobj(csv_file, BUCKET, key)

        logger.info(
            "Lambda function for Openpowerlifting data ingestion ended: Success!"
        )

        
        sns.publish(
            TopicArn = SNS_TOPIC_ARN,
            Subject = f"Lambda Success - {LAMBDA}",
            Message = f"{LAMBDA}\n\nFunction succeeded, {csv_file} added to s3://{BUCKET}/{key}"
        )

        return {"statusCode": 200, "message": "File ingested successfully."}

    except Exception as e:
        logger.error(
            f"Lambda function for Openpowerlifting data ingestion ended: Failure. {str(e)}"
        )

        error_message = traceback.format_exc()
        sns.publish(
            TopicArn = SNS_TOPIC_ARN,
            Subject = f"Lambda Failure Alert - {LAMBDA}",
            Message = f"{LAMBDA}\n\nFunction failed:\n\n{error_message}"
        )

        return {"statusCode": 500, "message": f"File ingestion failed, {error_message}"}
