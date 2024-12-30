import os
import logging
import requests
from zipfile import ZipFile

import awswrangler as wr
import pandas as pd

# Ideals to stick to:
# 1. The pipeline is idempotent. It can be run multiple times without affecting the dataset adversely: F(X) = X', F(X') = X'
# 2. The pipeline attempt to minimize memory usage whenever possible.
# 3. The pipeline is self-cleaning. Delete temporary files after done with them, unless in a lambda instance.
# 4. The pipeline contains logging. A user should be able to read the log file to step through exactly what happened.
# 5. Currently, past the initial ingestion, pandas is only used to automatically infer schema.
#    If we can infer schema of a csv file on S3 (python library pyiceberg?, S3 service that doesn't suck as much as Glue?),
#    we can eliminate this step which takes a lot of Lambda compute)


def download_file_from_url(url: str, filename: str) -> None:
    logging.info(f"Download started with url={url} and filename={filename}")
    try:
        # Get a response from the url
        response = requests.get(url)
        logging.info(f"Response received from: {url}")
    except Exception as e:
        logging.info(f"An error occurred when connecting to the website: {e}")

    # Save the response.
    with open(filename, "wb") as file:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                file.write(chunk)
    logging.info(f"File saved to: {filename}")


def upload_file_to_s3(filename: str, s3_path: str, overwrite: bool = False) -> None:
    # Upload to file to S3, choosing to overwrite or not
    if wr.s3.does_object_exist(s3_path) and not overwrite:
        logging.info(f"File already exists on S3.")
        logging.info(f"Upload aborted after finding an S3 object at {s3_path}")
    elif wr.s3.does_object_exist(s3_path) and overwrite:
        logging.info(f"Overwriting existing file on S3.")
        wr.s3.upload(filename, s3_path)
        logging.info(f"File uploaded, overwriting {s3_path}")
    else:
        logging.info(f"Upload started to s3_path={s3_path}")
        wr.s3.upload(filename, s3_path)
        logging.info(f"File upload complete.")


def extract_and_upload_csv_from_zip(
    filename: str, s3_path: str, overwrite: bool = False, cleanup: bool = True
) -> str:
    with ZipFile(filename, "r") as z:
        # Find the data file in the archive
        data_archive_path = [
            x for x in z.namelist() if os.path.splitext(x)[-1] == ".csv"
        ][0]
        data_archive_file = os.path.basename(data_archive_path)
        csv_s3_path = f"{s3_path}/{data_archive_file}"
        logging.info(f"Data found at: $file/{data_archive_path}")

        # Extract the csv from the zip and upload to S3
        with z.open(data_archive_path, "r") as csv_in_zip:
            upload_file_to_s3(csv_in_zip, csv_s3_path, overwrite=overwrite)
    return csv_s3_path


def main() -> None:
    logging.basicConfig(
        filename=os.path.join("log", "pipeline.log"),
        level=logging.INFO,
        format="%(asctime)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    logging.info(f"Extract started at {pd.Timestamp.now()}")

    database = "openpowerlifting"
    table = "lifter"
    data_url = (
        "https://openpowerlifting.gitlab.io/opl-csv/files/openpowerlifting-latest.zip"
    )

    data_filename = f"{database}-{table}-{pd.Timestamp.now().strftime('%Y%m%d')}.zip"
    csv_s3_dir = f"s3://tdouglas-data-prod-useast2/data/raw/{database}/{table}/csv"

    logging.info("-- DOWNLOAD ZIP FROM HTTPS --")
    download_file_from_url(data_url, data_filename)
    logging.info("-- EXTRACT CSV FROM ZIP AND UPLOAD TO S3 --")
    extract_and_upload_csv_from_zip(data_filename, csv_s3_dir)
    logging.info(f"Extract ended at {pd.Timestamp.now()}")


if __name__ == "__main__":
    main()
