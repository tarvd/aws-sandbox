import logging
from datetime import datetime, timezone
from pathlib import Path
from dataclasses import dataclass
from zipfile import ZipFile

import boto3
from awswrangler import s3
import requests

logging.basicConfig(
    filename=Path("logs", "opl_pipeline.log"),
    level=logging.INFO,
    format="%(asctime)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


@dataclass
class HttpRequest:
    url: str
    destination: Path = Path("tmp", "data.zip")
    download_start_at: str = None
    download_end_at: str = None
    response: requests.Response = None

    def __post_init__(self) -> None:
        logging.info(f"Data source built: {self}")

    def make_request(self) -> None:
        logging.info(f"Download started from: {self.url}")
        self.download_start_at = datetime.now(timezone.utc).strftime(
            "%Y-%m-%d %H:%M:%S %Z"
        )
        try:
            self.response = requests.get(self.url)
            self.download_end_at = datetime.now(timezone.utc).strftime(
                "%Y-%m-%d %H:%M:%S %Z"
            )
            logging.info(f"Response received from: {self.url}")
            logging.info(f"{self}")
        except Exception as e:
            self.download_end_at = datetime.now(timezone.utc).strftime(
                "%Y-%m-%d %H:%M:%S %Z"
            )
            logging.info(f"Download failed with message {e}")
            logging.info(f"{self}")
        with open(self.destination, "wb") as file:
            for chunk in self.response.iter_content(chunk_size=8192):
                if chunk:
                    file.write(chunk)
        logging.info(f"File saved to: {self.destination}")


@dataclass
class S3Upload:
    filename: str
    s3_path: str
    overwrite: bool = False
    boto3_session: boto3.session.Session = boto3.session.Session()
    upload_status: str = None
    upload_start_at: str = None
    upload_end_at: str = None

    def __post_init__(self) -> None:
        logging.info(f"Data sink built: {self}")

    def upload_file(self) -> None:
        logging.info(f"Upload started to s3_path: {self.s3_path}")
        self.upload_start_at = datetime.now(timezone.utc).strftime(
            "%Y-%m-%d %H:%M:%S %Z"
        )
        try:
            if s3.does_object_exist(self.s3_path) and not self.overwrite:
                self.upload_status = "Abort"
            else:
                s3.upload(self.filename, self.s3_path)
                self.upload_status = "Success"
            self.upload_end_at = datetime.now(timezone.utc).strftime(
                "%Y-%m-%d %H:%M:%S %Z"
            )
            logging.info(f"Upload finished with status: {self.upload_status}")
            logging.info(f"{self}")
        except Exception as e:
            self.upload_end_at = datetime.now(timezone.utc).strftime(
                "%Y-%m-%d %H:%M:%S %Z"
            )
            self.upload_status = "Failure"
            logging.info(f"Upload failed with message {e}")
            logging.info(f"{self}")


def extract_zip(filename: Path) -> str:
    logging.info(f"Extract Zip transformation started with filename: {filename}")
    try:
        with ZipFile(filename, "r") as z:
            z.extractall(Path("tmp"))
        for fn in Path("tmp").rglob("*"):
            if fn.name[-4:] == ".csv":
                logging.info(f"Data extracted to: {fn}")
                return str(fn)
    except Exception as e:
        logging.info(f"extract_zip failed with message {e}")


def clean_up(start_directory: Path = Path("tmp")) -> None:
    for path in start_directory.iterdir():
        if path.is_file():
            path.unlink()
        else:
            clean_up(path)
    for path in start_directory.iterdir():
        path.rmdir()


def main() -> None:
    logging.info("Pipeline started")

    # Extract
    request = HttpRequest(
        url="https://openpowerlifting.gitlab.io/opl-csv/files/openpowerlifting-latest.zip",
    )
    request.make_request()

    # Transform
    csv_path = extract_zip(request.destination)
    year = csv_path.split("-")[-4]
    month = csv_path.split("-")[-3]
    day = csv_path.split("-")[-2]
    csv_filename = "openpowerlifting" + csv_path.split("openpowerlifting")[-1]

    # Load
    s3_bucket = "tdouglas-data-prod-useast2"
    s3_dir = f"data/raw/openpowerlifting/lifter/{year}/{month}/{day}/{csv_filename}"
    s3_path = f"s3://{s3_bucket}/{s3_dir}"
    s3_upload = S3Upload(
        filename=csv_path,
        s3_path=s3_path,
    )
    s3_upload.upload_file()

    # Clean up
    clean_up()
    logging.info("Files removed from tmp/")
    logging.info("Pipeline ended")


if __name__ == "__main__":
    main()
