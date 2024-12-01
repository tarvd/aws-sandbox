import os
import sys
import logging
from zipfile import ZipFile

import awswrangler as wr
import pandas as pd


def find_last_modified_file_in_s3(s3_path: str) -> None:
    files = wr.s3.list_objects(s3_path, suffix="zip")
    descriptions = wr.s3.describe_objects(
        "s3://tdouglas-data-prod-useast2/data/raw/openpowerlifting/lifter"
    )
    last_modified_at_dict = {
        file: pd.to_datetime(
            descriptions[file]["ResponseMetadata"]["HTTPHeaders"]["last-modified"],
            format="%a, %d %b %Y %H:%M:%S %Z",
        )
        for file in files
    }
    return max(last_modified_at_dict, key=last_modified_at_dict.get)


def extract_zip(s3_zip_path: str) -> None:
    filename = "opl_lifter.zip"
    try:
        # Download zip file from S3
        wr.s3.download(s3_zip_path, filename)
        logging.info(f"Data downloaded from: {s3_zip_path}")
    except Exception as e:
        logging.info(f"An error occurred when connecting to the S3 bucket: {e}")

    with ZipFile(filename, "r") as z:
        # Find the data file in the archive
        data_archive_path = [
            x for x in z.namelist() if os.path.splitext(x)[-1] == ".csv"
        ][0]
        data_archive_file = os.path.basename(data_archive_path)
        s3_csv_path = f"s3://tdouglas-data-prod-useast2/data/raw/openpowerlifting/lifter/csv/{data_archive_file}"
        logging.info(f"Data found at: $archive/{data_archive_path}")

        # Extract the csv from the zip and upload to S3
        if wr.s3.does_object_exist(s3_csv_path):
            logging.info(f"File already exists on S3: {s3_csv_path}")
            logging.info(f"Program ended after finding an S3 object at {s3_csv_path}")
            sys.exit()
        else:
            with z.open(data_archive_path, "r") as csv_in_zip:
                wr.s3.upload(csv_in_zip, s3_csv_path)
            logging.info(f"Data uploaded to: {s3_csv_path}")


def main():
    log_file = "openpowerlifting_lifter_extraction_logfile.log"
    logging.basicConfig(
        filename=log_file,
        level=logging.INFO,
        format="%(asctime)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    s3_path = "s3://tdouglas-data-prod-useast2/data/raw/openpowerlifting/lifter"
    s3_zip_path = find_last_modified_file_in_s3(s3_path)
    logging.info(f"Program started with s3_zip_path={s3_zip_path}")
    extract_zip(s3_zip_path)


if __name__ == "__main__":
    main()
