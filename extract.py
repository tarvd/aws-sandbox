import os
import time
import logging
import requests
import json
from zipfile import ZipFile

import awswrangler as wr


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
    filename: str, s3_path: str, overwrite: bool = False
) -> str:
    with ZipFile(filename, "r") as z:
        # Find the data file in the archive
        data_archive_path = [
            x for x in z.namelist() if os.path.splitext(x)[-1] == ".csv"
        ][0]
        data_archive_file = os.path.basename(data_archive_path)
        year = data_archive_file.split("-")[1]
        month = data_archive_file.split("-")[2]
        day = data_archive_file.split("-")[3]
        csv_s3_path = f"{s3_path}/{year}/{month}/{day}/{data_archive_file}"
        logging.info(f"Data found at: $file/{data_archive_path}")

        # Extract the csv from the zip and upload to S3
        with z.open(data_archive_path, "r") as csv_in_zip:
            upload_file_to_s3(csv_in_zip, csv_s3_path, overwrite=overwrite)
        upload_at = time.strftime("%Y-%m-%d %H:%M:%S.%f")
        os.remove(filename)
    return (data_archive_file, csv_s3_path, upload_at)


def infer_schema(csv_s3_path: str) -> dict:
    logging.info(f"Inferring schema of file: {csv_s3_path}")
    df = wr.s3.read_csv(csv_s3_path, nrows=10000)
    schema_dict = (
        df.dtypes.copy()
        .replace("object", "string")
        .replace("float64", "float")
        .replace("int64", "int")
        .to_dict()
    )
    logging.info(f"Schema inferred for file with {len(schema_dict)} columns")
    return schema_dict


def upload_metadata(
    csv_filename: str,
    csv_s3_path: str,
    csv_upload_at: str,
    csv_schema_dict: dict,
    json_s3_path: str,
    json_filename: str,
) -> None:
    logging.info(f"Uploading metadata for {csv_filename}")
    json_to_add = {
        "filename": csv_filename,
        "s3_path": csv_s3_path,
        "upload_at": csv_upload_at,
        "schema": csv_schema_dict,
    }

    if not wr.s3.does_object_exist(json_s3_path):
        with open(json_filename, "w") as file:
            json.dump([], file)
    else:
        wr.s3.download(json_s3_path, json_filename)

    with open(json_filename, "r") as file:
        metadata = json.load(file)
    metadata.append(json_to_add)
    with open(json_filename, "w") as file:
        json.dump(metadata, file, indent=4)
    upload_file_to_s3(json_filename, json_s3_path, overwrite=True)
    os.remove(json_filename)
    logging.info(f"Metadata updated at {json_s3_path}")


def main() -> None:
    init_logging()
    logging.info(f"Extract started")

    database = "openpowerlifting"
    table = "lifter"
    data_url = (
        "https://openpowerlifting.gitlab.io/opl-csv/files/openpowerlifting-latest.zip"
    )
    data_filename = f"{database}-{table}-{time.strftime('%Y%m%d')}.zip"
    csv_s3_dir = f"s3://tdouglas-data-prod-useast2/data/raw/{database}/{table}"
    json_filename = "metadata.json"
    json_s3_path = f"s3://tdouglas-data-prod-useast2/metadata/raw/{database}/{table}/{json_filename}"

    logging.info("-- DOWNLOADING ZIP FROM HTTPS --")
    download_file_from_url(data_url, data_filename)

    logging.info("-- EXTRACTING CSV FROM ZIP AND UPLOADING TO S3 --")
    (csv_filename, csv_s3_path, csv_upload_at) = extract_and_upload_csv_from_zip(
        data_filename, csv_s3_dir
    )

    logging.info("-- INFERRING DATA SCHEMA FROM CSV FILE --")
    csv_schema_dict = infer_schema(csv_s3_path)

    logging.info("-- UPLOADING FILE EXTRACTION METADATA --")
    upload_metadata(
        csv_filename,
        csv_s3_path,
        csv_upload_at,
        csv_schema_dict,
        json_s3_path,
        json_filename,
    )

    logging.info(f"Extract ended")


if __name__ == "__main__":
    main()
