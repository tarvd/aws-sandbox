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
    # init_logging()
    # logging.info(f"Transform started at {pd.Timestamp.now()}")

    csv_s3_path = "openpowerlifting-2024-12-28-acdecc3a.csv"
    df = pd.read_csv(csv_s3_path, nrows=10000)
    schema_dict = (
        df.dtypes.copy()
        .replace("object", "string")
        .replace("float64", "float")
        .replace("int64", "int")
        .to_dict()
    )
    print(df.head())
    for item in schema_dict.items():
        print(item)

    # logging.info(f"Transform ended at {pd.Timestamp.now()}")


if __name__ == "__main__":
    main()
