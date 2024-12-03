import os
import logging

import awswrangler as wr
import pandas as pd


def read_csv_to_df(s3_path: str) -> pd.DataFrame:
    df = pd.read_csv(s3_path)
    df["load_at"] = pd.Timestamp.now().strftime('%Y%m%d')
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
    logging.info(f"Iceberg table created at: {database}.{table}")


def initialize_iceberg_table(
    s3_path: str, database: str, table: str, table_location: str, temp_path: str
) -> None:
    if wr.catalog.does_table_exist(database, table):
        logging.info(f"Table already exists in Glue catalog.")
        logging.info(
            f"Program ended after finding a Glue catalog table {database}.{table}"
        )
    else:
        df = read_csv_to_df(s3_path)
        create_iceberg_from_df(df, database, table, table_location, temp_path)


def main() -> None:
    logging.basicConfig(
        filename=os.path.join("log", "initialize_iceberg_table.log"),
        level=logging.INFO,
        format="%(asctime)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    s3_path = "s3://tdouglas-data-prod-useast2/data/raw/openpowerlifting/lifter/csv/openpowerlifting-2024-11-30-a70793a3.csv"
    database = "openpowerlifting"
    table = "lifter"
    table_location = (
        "s3://tdouglas-data-prod-useast2/data/raw/openpowerlifting/lifter/iceberg/"
    )
    temp_path = "s3://tdouglas-data-prod-useast2/data/temp/"

    initialize_iceberg_table(s3_path, database, table, table_location, temp_path)


if __name__ == "__main__":
    main()
