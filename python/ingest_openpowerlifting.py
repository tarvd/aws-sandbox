
from zipfile import ZipFile
from io import BytesIO

import boto3
import requests


def main():
    url = "https://openpowerlifting.gitlab.io/opl-csv/files/openpowerlifting-latest.zip"
    bucket = "ted-sand-dev-s3-use2-data"

    response = requests.get(url)
    response.raise_for_status()

    with ZipFile(BytesIO(response.content)) as z:

        csv_files = [name for name in z.namelist() if name.endswith(".csv")]

        if not csv_files:
            raise ValueError("No CSV files found in the ZIP archive.")

        csv_path = csv_files[0]
        csv_fn = csv_path.split("/")[-1]
        key = f"openpowerlifting/{csv_fn}"
        print(key)


        s3 = boto3.client("s3")

        with z.open(csv_path, "r") as csv_file:
            s3.upload_fileobj(csv_file, bucket, key)


if __name__ == "__main__":
    main()
