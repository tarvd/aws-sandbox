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


def upload_file_to_s3(
    filename: str, s3_path: str, overwrite: bool = False, cleanup: bool = True
) -> None:
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
    if cleanup:
        os.remove(filename)


def download_file_from_s3(s3_path: str, filename: str) -> None:
    logging.info(f"Download started with s3_path={s3_path}")
    try:
        # Download zip file from S3
        wr.s3.download(s3_path, filename)
        logging.info(f"File downloaded from: {s3_path}")
        logging.info(f"File saved to: {filename}")
    except Exception as e:
        logging.info(f"An error occurred when connecting to S3: {e}")


def find_last_modified_file_in_s3(s3_path: str, suffix: str) -> str:
    files = wr.s3.list_objects(s3_path, suffix=suffix)
    descriptions = wr.s3.describe_objects(s3_path)
    last_modified_at_dict = {
        file: pd.to_datetime(
            descriptions[file]["ResponseMetadata"]["HTTPHeaders"]["last-modified"],
            format="%a, %d %b %Y %H:%M:%S %Z",
        )
        for file in files
    }
    return max(last_modified_at_dict, key=last_modified_at_dict.get)


def find_duplicate_files_in_s3(s3_path: str, suffix: str = "zip") -> None:
    logging.info(f"Program starting with s3_path={s3_path} and suffix={suffix}")
    files = wr.s3.list_objects(s3_path, suffix=suffix)
    descriptions = wr.s3.describe_objects(s3_path)
    s3_data = pd.DataFrame(
        [
            {
                "id": file,
                "last_modified_at": pd.to_datetime(
                    descriptions[file]["ResponseMetadata"]["HTTPHeaders"][
                        "last-modified"
                    ],
                    format="%a, %d %b %Y %H:%M:%S %Z",
                ),
                "etag": descriptions[file]["ResponseMetadata"]["HTTPHeaders"]["etag"],
            }
            for file in files
        ]
    )
    keep_id = (
        s3_data.groupby("etag", as_index=True)["last_modified_at"].max().to_frame()
    )
    keep_data = s3_data[s3_data["last_modified_at"].isin(keep_id["last_modified_at"])]
    duplicate_list = s3_data[~(s3_data["id"].isin(keep_data["id"]))]["id"].tolist()
    logging.info(f"Found {len(duplicate_list)} duplicates in path")
    return duplicate_list


def print_duplicates(duplicate_list: list[str] = None) -> None:
    if duplicate_list is None or duplicate_list == []:
        print("No duplicates found")
    else:
        for item in duplicate_list:
            logging.info(f"Duplicate: {item}")
            print(item)


def extract_and_upload_csv_from_zip(
    filename: str, s3_path: str, cleanup: bool = True
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
            upload_file_to_s3(csv_in_zip, csv_s3_path, overwrite=False, cleanup=False)
    os.remove(filename)
    return csv_s3_path


def read_csv_to_df(s3_path: str) -> pd.DataFrame:
    csv_created_date = (
        s3_path.split("/")[-1].replace("openpowerlifting-", "")[:10].replace("-", "")
    )
    df = pd.read_csv(s3_path)
    df["load_at"] = csv_created_date
    logging.info(f"Dataframe formed from: {s3_path}")
    return df


def create_iceberg_from_df(
    df: pd.DataFrame,
    database: str,
    table: str,
    table_location: str,
    temp_path: str,
    cleanup: bool = True,
) -> None:
    wr.athena.to_iceberg(
        df=df,
        database=database,
        table=table,
        table_location=table_location,
        temp_path=temp_path,
    )
    if cleanup:
        logging.info(f"Cleaning up files at {temp_path}")
        wr.s3.delete_objects(temp_path[:-1])


def add_data_to_iceberg(
    database: str, table: str, csv_s3_path: str, table_location: str, temp_path: str
) -> None:
    csv_created_date = (
        csv_s3_path.split("/")[-1]
        .replace("openpowerlifting-", "")[:10]
        .replace("-", "")
    )
    if wr.catalog.does_table_exist(database, table):
        logging.info(f"Glue catalog table found: {database}.{table}")
        iceberg_last_load_at = wr.athena.read_sql_query(
            sql=f"select max(load_at) as last_load_at from {database}.{table}",
            database=database,
            ctas_approach=False,
        )["last_load_at"][0]
        if csv_created_date > iceberg_last_load_at:
            logging.info(f"Uploading {csv_created_date} data")
            df = read_csv_to_df(csv_s3_path)
            create_iceberg_from_df(df, database, table, None, temp_path)
            logging.info(f"Data inserted into {database}.{table}")
        else:
            logging.info(
                f"{database}.{table} contains most recent data of {csv_created_date}, upload aborted."
            )
    else:
        logging.info(f"Creating Iceberg table with {csv_created_date} data")
        df = read_csv_to_df(csv_s3_path)
        create_iceberg_from_df(df, database, table, table_location, temp_path)
        logging.info(f"Iceberg table created: {database}.{table}")


def main() -> None:
    logging.basicConfig(
        filename=os.path.join("log", "pipeline.log"),
        level=logging.INFO,
        format="%(asctime)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    logging.info(f"Program start at {pd.Timestamp.now()}")

    temp_path = "s3://tdouglas-data-prod-useast2/data/temp/"
    temp_database = "temp"
    database = "openpowerlifting"
    table = "lifter"
    data_url = (
        "https://openpowerlifting.gitlab.io/opl-csv/files/openpowerlifting-latest.zip"
    )

    data_filename = f"{database}-{table}-{pd.Timestamp.now().strftime('%Y%m%d')}.zip"
    data_s3_dir = f"s3://tdouglas-data-prod-useast2/data/raw/{database}/{table}/zip"
    csv_s3_dir = f"s3://tdouglas-data-prod-useast2/data/raw/{database}/{table}/csv"
    table_location = (
        f"s3://tdouglas-data-prod-useast2/data/raw/{database}/{table}/iceberg/"
    )

    logging.info("-- DOWNLOAD ZIP FROM HTTPS --")
    download_file_from_url(data_url, data_filename)
    logging.info("-- EXTRACT CSV FROM ZIP AND UPLOAD TO S3 --")
    csv_s3_path = extract_and_upload_csv_from_zip(data_filename, csv_s3_dir)
    # logging.info("-- CREATE TEMP TABLE -")
    # add_data_to_iceberg(temp_database, table, csv_s3_path, table_location, temp_path)
    # logging.info("-- ATTEMPT DATA INSERT INTO ICEBERG ON S3 --")
    # add_data_to_iceberg(database, table, csv_s3_path, table_location, temp_path)


if __name__ == "__main__":
    main()
