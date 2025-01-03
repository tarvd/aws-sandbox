import os
import logging
import time
import json

import awswrangler as wr
import pandas as pd


def init_logging() -> None:
    logging.basicConfig(
        filename=os.path.join("log", "pipeline.log"),
        level=logging.INFO,
        format="%(asctime)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def get_schema(metadata_s3_path: str) -> dict:
    logging.info(f"Reading schema of file from metadata: {metadata_s3_path}")
    metadata_filename = "metadata.json"
    wr.s3.download(metadata_s3_path, metadata_filename)
    with open(metadata_filename, "r") as file:
        metadata = json.load(file)
    last_upload_time = max([item[1]["upload_at"] for item in metadata.items()])
    schema = [item[1]["schema"] for item in metadata.items() if item[1]["upload_at"] == last_upload_time][0]
    return schema


def create_iceberg_ddl(
    database: str, table: str, schema_dict: dict, s3_iceberg_location: str
) -> str:
    logging.info(
        f"Constructing Athena SQL to create Iceberg table: {database}.{table} at {s3_iceberg_location}"
    )
    columns_str = ",\n\t\t".join([f"{col[0]} {col[1]}" for col in schema_dict.items()])
    ddl_str = f"""
    CREATE TABLE IF NOT EXISTS {database}.{table} (
        {columns_str}
    ) 
    LOCATION '{s3_iceberg_location}' 
    TBLPROPERTIES (
    'table_type'='ICEBERG',
    'format'='parquet',
    'write_compression'='snappy',
    'optimize_rewrite_delete_file_threshold'='10'
    );
    """
    return ddl_str


def create_csv_ddl(
    database: str, table: str, schema_dict: dict, s3_csv_location: str
) -> str:
    logging.info(
        f"Constructing Athena SQL to create CSV table: {database}.{table} at {s3_csv_location}"
    )
    columns_str = ",\n\t\t".join([f"{col[0]} {col[1]}" for col in schema_dict.items()])
    ddl = f"""
    CREATE EXTERNAL TABLE IF NOT EXISTS {database}.{table} (
        {columns_str}
    )
    ROW FORMAT SERDE 'org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe'
    WITH SERDEPROPERTIES ('field.delim' = ',')
    LOCATION '{s3_csv_location}'
    TBLPROPERTIES ("skip.header.line.count" = "1");
    """
    return ddl


def create_load_view_ddl(database: str, table: str, view: str) -> str:
    logging.info(f"Constructing Athena SQL to create view: {database}.{view}")
    ddl = f"""
    CREATE OR REPLACE VIEW {database}.{view} AS
    WITH t AS (
        SELECT
            *,
            date(substring(element_at(split("$path", 'openpowerlifting-'), 2),1,10)) as source_record_date
        FROM {database}.{table}
    )
    SELECT 
        *
    FROM t
    WHERE source_record_date = (SELECT MAX(source_record_date) FROM t)
    """
    return ddl


def drop_csv_ddl(database: str, table: str) -> str:
    logging.info(f"Creating Athena SQL to drop table: {database}.{table}")
    ddl = f"""
    DROP TABLE {database}.{table} 
    """
    return ddl


def create_iceberg_insert(
    iceberg_database: str, iceberg_table: str, data_database: str, data_table: str
) -> str:
    logging.info(
        f"Constructing Athena SQL to insert into Iceberg table: {data_database}.{data_table} into {iceberg_database}.{iceberg_table}"
    )
    dml = f"""
        INSERT INTO {iceberg_database}.{iceberg_table} 
        SELECT *
        FROM {data_database}.{data_table}
        WHERE source_record_date > (SELECT COALESCE(MAX(source_record_date),DATE('1900-01-01')) FROM {iceberg_database}.{iceberg_table})
    """
    return dml


def run_athena_query(ddl_sql: str):
    logging.info(f"Running Athena query")
    query_execution_id = wr.athena.start_query_execution(ddl_sql)
    logging.info(f"Query started with id: {query_execution_id}")
    loop_condition = True
    while loop_condition:
        time.sleep(2)
        status = wr.athena.get_query_execution(query_execution_id)["Status"]
        logging.info(f"Query status: {status['State']}")
        if status["State"] in ("SUCCEEDED", "FAILED", "CANCELLED"):
            loop_condition = False
        if status["State"] == "FAILED":
            logging.info(str(status))
    logging.info(f"Query execution ended with status: {status['State']}")
    return status


def main() -> None:
    init_logging()
    logging.info(f"Load started at {pd.Timestamp.now()}")

    raw_database = "openpowerlifting"
    raw_table = "lifter"
    raw_files = f"s3://tdouglas-data-prod-useast2/data/raw/{raw_database}/{raw_table}/"
    metadata_s3_path = f"s3://tdouglas-data-prod-useast2/metadata/raw/{raw_database}/{raw_table}/metadata.json"
    raw_view = "v_lifter"
    curated_database = "curated"
    curated_table = "lifter"
    curated_dir = "s3://tdouglas-data-prod-useast2/data/curated/lifter/"

    logging.info(f"-- INFERRING DATA SCHEMA FROM CSV --")
    schema_dict = get_schema(metadata_s3_path)

    if not wr.catalog.does_table_exist(raw_database, raw_table):
        logging.info(f"-- CREATING CSV EXTERNAL TABLE --")
        csv_ddl = create_csv_ddl(raw_database, raw_table, schema_dict, raw_files)
        run_athena_query(csv_ddl)
        logging.info(f"Raw data table created: {raw_database}.{raw_table}")

    if not wr.catalog.does_table_exist(raw_database, raw_view):
        logging.info(f"-- CREATING DATA LOAD VIEW ON EXTERNAL TABLE --")
        data_load_view_ddl = create_load_view_ddl(raw_database, raw_table, raw_view)
        run_athena_query(data_load_view_ddl)
        logging.info(f"Most recent raw data view created: {raw_database}.{raw_view}")

    if not wr.catalog.does_table_exist(curated_database, curated_table):
        logging.info(f"-- CREATING ICEBERG TABLE --")
        schema_dict.update({"source_record_date":"date"})
        iceberg_ddl = create_iceberg_ddl(
            curated_database, curated_table, schema_dict, curated_dir
        )
        run_athena_query(iceberg_ddl)
        logging.info(f"Iceberg table created: {curated_database}.{curated_table}")

    logging.info(f"-- INSERTING DATA INTO ICEBERG TABLE --")
    iceberg_dml = create_iceberg_insert(
        curated_database, curated_table, raw_database, raw_view
    )
    run_athena_query(iceberg_dml)
    logging.info(
        f"Data inserted into Iceberg table: {curated_database}.{curated_table}"
    )

    logging.info(f"Load ended at {pd.Timestamp.now()}")


if __name__ == "__main__":
    main()
