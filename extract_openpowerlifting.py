import logging
import requests
from os import remove
from zipfile import ZipFile
from pathlib import Path

from awswrangler import s3


def init_logging() -> None:
    logging.basicConfig(
        filename=Path("log", "pipeline.log"),
        level=logging.INFO,
        format="%(asctime)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def download_url_zip(url: str, filename: Path) -> None:
    logging.info(f"Download started with url={url} and filename={filename}")
    # Get a response from the url
    try:
        response = requests.get(url)
        logging.info(f"Response received from: {url}")
    except Exception as e:
        logging.exception(f"An error occurred when connecting to the website: {e}")
    # Save the response.
    with open(filename, "wb") as file:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                file.write(chunk)
    logging.info(f"File saved to: {filename}")


def extract_zip(filename: Path) -> Path:
    try:
        with ZipFile(filename, "r") as z:
            z.extractall(Path("data"))
        logging.info(f"Zip extracted to: {filename}")
        for fn in Path("data").rglob("*"):
            if fn.name[-4:] == ".csv":
                logging.info(f"CSV found at: {fn}")
                return fn
    except Exception as e:
        logging.exception(f"An error occurred when extracting the zip: {e}")


def upload_file_to_s3(filename: str, s3_path: str, overwrite: bool = False) -> None:
    # Upload to file to S3, choosing to overwrite or not
    try:
        if s3.does_object_exist(s3_path) and not overwrite:
            logging.info(f"File already exists on S3.")
            logging.info(f"Upload aborted after finding an S3 object at {s3_path}")
            upload_status = "Abort"
        elif s3.does_object_exist(s3_path) and overwrite:
            logging.info(f"Overwriting existing file on S3.")
            s3.upload(filename, s3_path)
            logging.info(f"File uploaded, overwriting {s3_path}")
            upload_status = "Success"
        else:
            logging.info(f"Upload started to s3_path={s3_path}")
            s3.upload(filename, s3_path)
            logging.info(f"File upload complete.")
            upload_status = "Success"
    except Exception as e:
        logging.info(f"File upload failed, reason: {e}")
        upload_status = "Failure"
    return upload_status


def cleanup(data_filename) -> None:
    # Cleanup
    remove(data_filename)
    for fn in Path("data").rglob("*"):
        if not fn.is_dir():
            remove(fn)


def main() -> None:
    # Logging
    init_logging()
    logging.info(f"Extract started")

    # Constants
    data_url = (
        "https://openpowerlifting.gitlab.io/opl-csv/files/openpowerlifting-latest.zip"
    )
    data_filename = Path("data.zip")
    csv_s3_dir = f"s3://tdouglas-data-prod-useast2/data/raw/openpowerlifting/lifter"

    # Extraction
    logging.info("-- DOWNLOADING DATA TO ZIP --")
    download_url_zip(data_url, data_filename)
    logging.info("-- EXTRACTING ZIP TO CSV --")
    csv_filename = extract_zip(data_filename)
    logging.info("-- UPLOADING CSV TO S3 --")
    upload_file_to_s3(str(csv_filename), csv_s3_dir)
    logging.info("-- CLEANING UP FILES --")
    cleanup(data_filename)

    logging.info(f"Extract ended")


if __name__ == "__main__":
    main()
