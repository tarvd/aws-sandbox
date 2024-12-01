import sys
import logging

import requests
import awswrangler as wr
import pandas as pd


def download_zip(url: str, zip_file: str) -> None:
    try:
        # Get a response from the url
        response = requests.get(url)
        logging.info(f"Response received from: {url}")
    except Exception as e:
        logging.info(f"An error occurred when connecting to the website: {e}")

    # Save the response as an archive
    with open(zip_file, "wb") as file:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                file.write(chunk)
    logging.info(f"Archive saved to: {zip_file}")


def upload_to_s3(zip_file: str, s3_path: str) -> None:
    wr.s3.upload(zip_file, s3_path)
    logging.info(f"Data uploaded to: {s3_path}")


def main():
    log_file = "openpowerlifting_lifter_ingestion_logfile.log"
    logging.basicConfig(
        filename=log_file,
        level=logging.INFO,
        format="%(asctime)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    url = "https://openpowerlifting.gitlab.io/opl-csv/files/openpowerlifting-latest.zip"
    filename = f"openpowerlifting-lifter-{pd.Timestamp.now().strftime('%Y%m%d')}.zip"
    s3_path = (
        f"s3://tdouglas-data-prod-useast2/data/raw/openpowerlifting/lifter/{filename}"
    )
    logging.info(f"Program started with url={url} and zip_file={filename}")
    download_zip(url, filename)
    logging.info(f"Download complete, upload started to s3_path={s3_path}")
    if wr.s3.does_object_exist(s3_path):
        # if 1 == 2:
        logging.info(f"File already exists on S3: {s3_path}")
        logging.info(f"Program ended after finding an S3 object at {s3_path}")
        sys.exit()
    else:
        upload_to_s3(filename, s3_path)
        logging.info(f"S3 object uploaded at {s3_path}")


if __name__ == "__main__":
    main()
