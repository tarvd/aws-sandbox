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

        
def create_curated_ddl(curated_database: str, curated_table: str, raw_database: str, raw_table: str):
    return f"""
            CREATE TABLE {curated_database}.{curated_table} AS
            WITH t_latest_date AS (
                SELECT max(sourcerecorddate) as max_date
                FROM {raw_database}.{raw_table}
            )
            SELECT rt.*
            FROM {raw_database}.{raw_table} rt, t_latest_date
            WHERE rt.sourcerecorddate = t_latest_date.max_date
        """
        
def drop_curated_ddl(curated_database: str, curated_table: str):
    return f"""DROP TABLE {curated_database}.{curated_table}"""


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
    logging.info(f"Transform started at {pd.Timestamp.now()}")

    curated_database = "curated"
    curated_table = "lifter"
    raw_database = "openpowerlifting"
    raw_table = "lifter_iceberg"

    if wr.catalog.does_table_exist(curated_database, curated_table):
        logging.info(f"-- DROPPING TRANSFORMED TABLE --")
        curated_drop = drop_curated_ddl(curated_database, curated_table)
        run_athena_query(curated_drop)
    
    logging.info(f"-- CREATING TRANSFORMED TABLE --")
    curated_ddl = create_curated_ddl(curated_database, curated_table, raw_database, raw_table)
    run_athena_query(curated_ddl)

    logging.info(f"Transform ended at {pd.Timestamp.now()}")


if __name__ == "__main__":
    main()
