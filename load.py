import os
import logging
import time

import awswrangler as wr
import pandas as pd


def init_logging() -> None:
    logging.basicConfig(
        filename=os.path.join("log", "pipeline.log"),
        level=logging.INFO,
        format="%(asctime)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

        
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


def create_iceberg_ddl(
        database: str, 
        table: str, 
        schema_dict: dict, 
        s3_iceberg_location: str
    ) -> str:
    logging.info(f"Constructing Athena SQL to create Iceberg table: {database}.{table} at {s3_iceberg_location}")
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
        database: str, 
        table: str, 
        schema_dict: dict, 
        s3_csv_location: str
    ) -> str:
    logging.info(f"Constructing Athena SQL to create CSV table: {database}.{table} at {s3_csv_location}")
    columns_str = ",\n\t\t".join([f"{col[0]} {col[1]}" for col in schema_dict.items()])
    ddl = f"""
    CREATE EXTERNAL TABLE IF NOT EXISTS {database}.{table} (
        {columns_str}
    )
    ROW FORMAT SERDE 'org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe'
    WITH SERDEPROPERTIES ('field.delim' = ',')
    LOCATION '{s3_csv_location}';
    """
    return ddl


def drop_csv_ddl(
        database: str, 
        table: str
    ) -> str:
    logging.info(f"Creating Athena SQL to drop CSV table: {database}.{table}")    
    ddl = f"""
    DROP TABLE {database}.{table} 
    """
    return ddl


def create_iceberg_insert(
        iceberg_database: str, 
        iceberg_table: str, 
        data_database: str, 
        data_table: str
    ) -> str:
    logging.info(f"Constructing Athena SQL to insert into Iceberg table: {data_database}.{data_table} into {iceberg_database}.{iceberg_table}")
    dml = f"""
        INSERT INTO {iceberg_database}.{iceberg_table} 
        WITH t_latest_date as (
            SELECT coalesce(max(sourcerecorddate),19000101) AS last_load_date
            FROM {iceberg_database}.{iceberg_table}
        )
        SELECT ti.* 
        FROM {data_database}.{data_table} ti, t_latest_date
        WHERE ti.sourcerecorddate > t_latest_date.last_load_date
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

    database = "openpowerlifting"
    csv_table = "lifter_csv"
    iceberg_table = "lifter_iceberg"
    csv_file = "s3://tdouglas-data-prod-useast2/data/raw/openpowerlifting/lifter/csv/"
    iceberg_s3_dir = "s3://tdouglas-data-prod-useast2/data/raw/openpowerlifting/lifter/iceberg/"

    logging.info(f"-- INFERRING DATA SCHEMA FROM CSV --")
    schema_dict = infer_schema(csv_file)

    if not wr.catalog.does_table_exist(database, csv_table):
        logging.info(f"-- CREATING CSV EXTERNAL TABLE --")
        csv_ddl = create_csv_ddl(database, csv_table, schema_dict, csv_file)
        run_athena_query(csv_ddl)

    if not wr.catalog.does_table_exist(database, iceberg_table):
        logging.info(f"-- CREATING ICEBERG TABLE --")
        iceberg_ddl = create_iceberg_ddl(database, iceberg_table, schema_dict, iceberg_s3_dir)
        run_athena_query(iceberg_ddl)
    
    logging.info(f"-- INSERTING DATA INTO ICEBERG TABLE --")
    iceberg_dml = create_iceberg_insert(database, iceberg_table, database, csv_table)
    run_athena_query(iceberg_dml)
    logging.info(f"Iceberg table updated")

    logging.info(f"Load ended at {pd.Timestamp.now()}")


if __name__ == "__main__":
    main()
