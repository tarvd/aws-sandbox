import logging
import requests
import awswrangler as wr
import pandas as pd


def download_file_from_url(url: str, filename: str) -> None:    
    logging.info(f"Program started with url={url} and filename={filename}")
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
    logging.info(f"Archive saved to: {filename}")


def upload_to_s3(filename: str, s3_path: str, overwrite=False) -> None:
    if not overwrite and wr.s3.does_object_exist(s3_path):
        logging.info(f"File already exists on S3.")
        logging.info(f"Program ended after finding an S3 object at {s3_path}")
    else:
        logging.info(f"Upload started to s3_path={s3_path}")
        wr.s3.upload(filename, s3_path)
        logging.info(f"Data upload complete.")


def main() -> None:
    logging.basicConfig(
        filename="ingestion.log",
        level=logging.INFO,
        format="%(asctime)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    url = "https://openpowerlifting.gitlab.io/opl-csv/files/openpowerlifting-latest.zip"
    filename = f"openpowerlifting-lifter-{pd.Timestamp.now().strftime('%Y%m%d')}.zip"
    s3_path = (
        f"s3://tdouglas-data-prod-useast2/data/raw/openpowerlifting/lifter/{filename}"
    )

    download_file_from_url(url, filename)
    upload_to_s3(filename, s3_path)


if __name__ == "__main__":
    main()
