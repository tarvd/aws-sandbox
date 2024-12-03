import os
import logging

import awswrangler as wr
import pandas as pd


def find_last_modified_file_in_s3(s3_path: str) -> str:
    files = wr.s3.list_objects(s3_path, suffix="csv")
    descriptions = wr.s3.describe_objects(s3_path)
    last_modified_at_dict = {
        file: pd.to_datetime(
            descriptions[file]["ResponseMetadata"]["HTTPHeaders"]["last-modified"],
            format="%a, %d %b %Y %H:%M:%S %Z",
        )
        for file in files
    }
    return max(last_modified_at_dict, key=last_modified_at_dict.get)


def read_csv_to_df(s3_path: str) -> pd.DataFrame:
    csv_created_date = s3_path.split("/")[-1].replace("openpowerlifting-","")[:10].replace("-","")
    df = pd.read_csv(s3_path)
    df["load_at"] = csv_created_date
    logging.info(f"Data downloaded from: {s3_path}")
    return df


def create_iceberg_from_df(
    df: pd.DataFrame, database: str, table: str, table_location: str, temp_path: str
) -> None:
    wr.athena.to_iceberg(
        df=df,
        database=database,
        table=table,
        table_location=table_location,
        temp_path=temp_path,
    )


def add_raw_data_to_iceberg(database: str, table: str, s3_csv_path: str, table_location: str, temp_path: str) -> None:
    csv_created_date = s3_csv_path.split("/")[-1].replace("openpowerlifting-","")[:10].replace("-","")
    if wr.catalog.does_table_exist(database, table):
        logging.info(f"Glue catalog table found: {database}.{table}")
        iceberg_last_load_at = wr.athena.read_sql_query(sql=f"select max(load_at) as last_load_at from {database}.{table}",
            database=database,  
            ctas_approach=False,      
        )["last_load_at"][0]
        if csv_created_date > iceberg_last_load_at:
            logging.info(f"Uploading {csv_created_date} data")
            df = read_csv_to_df(s3_csv_path)   
            create_iceberg_from_df(df, database, table, None, temp_path)
            logging.info(f"Data inserted into {database}.{table}")
        else:
            logging.info(f"{database}.{table} contains most recent data, upload aborted.")
            return None
    else:
        logging.info(f"Uploading {csv_created_date} data")   
        df = read_csv_to_df(s3_csv_path)
        create_iceberg_from_df(df, database, table, table_location, temp_path)
        logging.info(f"Iceberg table created: {database}.{table}")


def main() -> None:
    logging.basicConfig(
        filename=os.path.join("log", "insert_into_iceberg_table.log"),
        level=logging.INFO,
        format="%(asctime)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    temp_path = "s3://tdouglas-data-prod-useast2/data/temp/"
    database = "openpowerlifting"
    table = "lifter"
    table_location = f"s3://tdouglas-data-prod-useast2/data/raw/{database}/{table}/iceberg/"
    s3_csv_path = find_last_modified_file_in_s3(f"s3://tdouglas-data-prod-useast2/data/raw/{database}/{table}/csv/")

    add_raw_data_to_iceberg(database, table, s3_csv_path, table_location, temp_path)


if __name__ == "__main__":
    main()
