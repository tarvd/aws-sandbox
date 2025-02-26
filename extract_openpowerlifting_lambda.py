import os
import requests
from zipfile import ZipFile
from pathlib import Path
from awswrangler import s3


def download_url_zip(url: str, filename: str) -> None:
    # Get a response from the url
    try:
        response = requests.get(url)
    except Exception as e:
        print(e)
    # Save the response.
    with open(filename, "wb") as file:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                file.write(chunk)


def extract_zip(filename: str) -> Path:
    try:
        with ZipFile(filename, "r") as z:
            z.extractall(Path("/tmp/"))
        for fn in Path("/tmp/").rglob("*"):
            if fn.name[-4:] == ".csv":
                return fn
    except Exception as e:
        print(e)


def upload_file_to_s3(filename: str, s3_path: str, overwrite: bool = False) -> None:
    # Upload to file to S3, choosing to overwrite or not
    try:
        if s3.does_object_exist(s3_path) and not overwrite:
            upload_status = "Abort"
        elif s3.does_object_exist(s3_path) and overwrite:
            s3.upload(filename, s3_path)
            upload_status = "Success"
        else:
            s3.upload(filename, s3_path)
            upload_status = "Success"
    except Exception as e:
        upload_status = "Failure"
    return upload_status


def lambda_handler(event, context):  # Constants
    data_url = (
        "https://openpowerlifting.gitlab.io/opl-csv/files/openpowerlifting-latest.zip"
    )
    data_filename = "/tmp/data.zip"
    csv_s3_dir = "s3://tdouglas-data-prod-useast2/data/raw/openpowerlifting/lifter/"

    download_url_zip(data_url, data_filename)
    csv_path = extract_zip(data_filename)
    csv_filename = os.path.basename(csv_path)
    s3_path = str("s3://aws-athena-query-results-820242901733-engineer-us-east-2/dbt/")
    upload_status = upload_file_to_s3(csv_path, csv_s3_dir)

    response = {
        "data_url": data_url,
        "csv_path": csv_path,
        "s3_path": s3_path,
        "upload_status": upload_status,
    }
    print(response)
    return response
