import os
import logging
import requests
from zipfile import ZipFile

import awswrangler as wr
import pandas as pd


def init_logging() -> None:
    logging.basicConfig(
        filename=os.path.join("log", "pipeline.log"),
        level=logging.INFO,
        format="%(asctime)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


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


def enrich_csv(csv_s3_path: str) -> None:
    logging.info(f"Data to enrich: {csv_s3_path}")
    df = wr.s3.read_csv(csv_s3_path)
    df["filename"] = csv_s3_path.split("/")[-1]
    df["sourcerecorddate"] = pd.Timestamp.now().strftime("%Y%m%d")
    wr.s3.to_csv(df, csv_s3_path, index=False)
    logging.info(f"Enriched data uploaded to: {csv_s3_path}")
    return None


def main() -> None:
    init_logging()
    logging.info(f"Extract started at {pd.Timestamp.now()}")
    
    database = "openpowerlifting"
    table = "lifter"
    data_url = (
        "https://openpowerlifting.gitlab.io/opl-csv/files/openpowerlifting-latest.zip"
    )
    data_filename = f"{database}-{table}-{pd.Timestamp.now().strftime('%Y%m%d')}.zip"
    csv_s3_dir = f"s3://tdouglas-data-prod-useast2/data/raw/{database}/{table}/csv"

    logging.info("-- DOWNLOADING ZIP FROM HTTPS --")
    download_file_from_url(data_url, data_filename)

    logging.info("-- EXTRACTING CSV FROM ZIP AND UPLOADING TO S3 --")
    csv_s3_path = extract_and_upload_csv_from_zip(data_filename, csv_s3_dir)

    logging.info("-- ENRICHING CSV WITH METADATA --")
    enrich_csv(csv_s3_path)

    logging.info(f"Extract ended at {pd.Timestamp.now()}")


if __name__ == "__main__":
    main()
