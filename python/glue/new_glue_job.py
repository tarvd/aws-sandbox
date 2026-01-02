import sys
import logging
import boto3
import traceback
from datetime import datetime, timezone

from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from pyspark.sql.functions import lit, concat_ws, current_timestamp, coalesce, sha2

from utils import get_event_id_hwm, set_event_id_hwm, get_latest_event_id, run_athena_query, insert_row_data_process_log

# Logging
MSG_FORMAT = "%(asctime)s %(levelname)s %(name)s: %(message)s"
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
logging.basicConfig(format=MSG_FORMAT, datefmt=DATETIME_FORMAT)
logger = logging.getLogger("glue-log")
logger.setLevel(logging.INFO)


# Constants and Config
LOG_DB = "metadata"
EVENTS_LOG = "data_ingest_log"
PROCESS_LOG = "data_process_log"
SOURCE_SYSTEM = "Openpowerlifting.org"
TARGET_DB = "cleansed"
TARGET_TABLE = "openpowerlifting"

PROCESSED_DATA_COLS = [
    "file_key",
    "job_name",
    "context",
    "processed_at",
    "job_id",
    "job_run_id",
]

RENAME_COLS_MAP = {
    "Name": "name",
    "Sex": "sex",
    "Event": "event",
    "Equipment": "equipment",
    "Age": "age",
    "AgeClass": "age_class",
    "BirthYearClass": "birth_year_class",
    "Division": "division",
    "BodyweightKg": "bodyweight_kg",
    "WeightClassKg": "weightclass_kg",
    "Squat1Kg": "squat_1_kg",
    "Squat2Kg": "squat_2_kg",
    "Squat3Kg": "squat_3_kg",
    "Squat4Kg": "squat_4_kg",
    "Best3SquatKg": "best_3_squat_kg",
    "Bench1Kg": "bench_1_kg",
    "Bench2Kg": "bench_2_kg",
    "Bench3Kg": "bench_3_kg",
    "Bench4Kg": "bench_4_kg",
    "Best3BenchKg": "best_3_bench_kg",
    "Deadlift1Kg": "deadlift_1_kg",
    "Deadlift2Kg": "deadlift_2_kg",
    "Deadlift3Kg": "deadlift_3_kg",
    "Deadlift4Kg": "deadlift_4_kg",
    "Best3DeadliftKg": "best_3_deadlift_kg",
    "TotalKg": "total_kg",
    "Place": "place",
    "Dots": "dots",
    "Wilks": "wilks",
    "Glossbrenner": "glossbrenner",
    "Goodlift": "goodlift",
    "Tested": "tested",
    "Country": "country",
    "State": "state",
    "Federation": "federation",
    "ParentFederation": "parent_federation",
    "Date": "date",
    "MeetCountry": "meet_country",
    "MeetState": "meet_state",
    "MeetTown": "meet_town",
    "MeetName": "meet_name",
    "Sanctioned": "sanctioned",
}

athena = boto3.client("athena")
glue = boto3.client("glue")
s3 = boto3.client("s3")
sns = boto3.client("sns")

def main():
    try:
        logger.info("Beginning job, loading arguments.")

        sc = SparkContext.getOrCreate()
        glueContext = GlueContext(sc)
        spark = glueContext.spark_session
        args = getResolvedOptions(sys.argv, ["JOB_NAME", "sns_topic_arn"])
        job_name = args["JOB_NAME"]
        job_id = args["JOB_ID"]
        job_run_id = args["JOB_RUN_ID"]
        sns_topic_arn = args["sns_topic_arn"]

        total_events_processed = 0
        total_opl_events_processed = 0
        total_rows_processed = 0

        logger.info(f"Reading list of files for {SOURCE_DB}.{SOURCE_TABLE}")

        event_id_hwm = get_event_id_hwm(job_name, athena)
        latest_event_id = get_latest_event_id(athena)

        if latest_event_id == -1:
            raise ValueError("The event log is empty.")

        if event_id_hwm == latest_event_id:
            job_status = "NO NEW EVENTS"
            message = "No new events to process."
            return

        events_to_process = list(range(event_id_hwm+1, latest_event_id+1))

        for event_id in events_to_process:
            s3_location_sql = f"""
                select coalesce(json_extract_scalar(payload, '$.s3_location'), 'invalid') as filename
                from {LOG_DB}.{EVENTS_LOG} 
                where event_id = '{event_id}'
                limit 1
            """
            filename = run_athena_query(s3_location_sql, athena)["Rows"][0][0]["VarCharValue"]

            if filename == 'invalid':
                logger.info(f"Adding row to metadata.data_process_log for event #{event_id}, filename: {filename}")
                insert_row_data_process_log(job_name, event_id, event_id_hwm, job_run_id, athena)
                total_events_processed += 1
                if event_id > event_id_hwm:
                    logger.info(f"Updating event HWM for {job_name} to {event_id}")
                    set_event_id_hwm(job_name, event_id, athena)
                continue

            logger.info(f"Processing file: {filename}")
            logger.info("Reading source file into Spark DF")
            df = glueContext.create_data_frame.from_options(
                connection_type="s3",
                connection_options={"paths": [filename]},
                format="csv",
                format_options={"withHeader": True},
            )
            source_num_rows = df.count()
            logger.info(f"Number of rows in source {filename}: {source_num_rows}")

            logger.info("Dropping duplicates and rows existing in target")
            df = df.withColumn(
                "row_hash",
                sha2(
                    concat_ws(
                        ":",
                        *[coalesce(col, lit("")).alias(col) for col in df.schema.names],
                    ),
                    256,
                ),
            )
            df = df.dropDuplicates(["row_hash"])
            target_rows_df = spark.sql(
                f"SELECT row_hash FROM glue_catalog.{TARGET_DB}.{TARGET_TABLE}"
            )
            df = (
                df.join(target_rows_df, ["row_hash"], "leftouter")
                .where(target_rows_df["row_hash"].isNull())
                .drop(target_rows_df["row_hash"])
            )
            filtered_num_rows = df.count()
            logger.info(
                f"Number of rows that will be loaded to target: {filtered_num_rows}"
            )

            logger.info("Adding audit columns")
            df = df.withColumn("source_system", lit(SOURCE_SYSTEM))
            df = df.withColumn("source_table", lit(f"{SOURCE_DB}.{SOURCE_TABLE}"))
            df = df.withColumn("inserted_at", current_timestamp())
            df = df.withColumn("job_name", lit(job_name))
            df = df.withColumn("job_id", lit(job_id))
            df = df.withColumn("job_run_id", lit(job_run_id))
            df = df.withColumn("is_deleted", lit(False))

            logger.info("Renaming columns from camel to snake case")
            df = df.withColumnsRenamed(RENAME_COLS_MAP)

            logger.info(f"Writing data to target {TARGET_DB}.{TARGET_TABLE}")
            df.writeTo(f"glue_catalog.{TARGET_DB}.{TARGET_TABLE}").tableProperty(
                "format-version", "2"
            ).append()

            # Mark records not in latest file as deleted
            if event_id == latest_event_id:
                df.createOrReplaceTempView("latest_data")
                spark.sql(f"""
                    UPDATE glue_catalog.{TARGET_DB}.{TARGET_TABLE}
                    SET is_deleted = true
                    WHERE row_hash NOT IN (SELECT row_hash FROM latest_data)
                """)

            logger.info(f"Adding row to metadata.data_process_log for event #{event_id}, filename: {filename}")
            insert_row_data_process_log(job_name, event_id, event_id_hwm, job_run_id, athena)
            total_events_processed += 1
            total_opl_events_processed += 1
            total_rows_processed += filtered_num_rows
            if event_id > event_id_hwm:
                logger.info(f"Updating event HWM for {job_name} to {event_id}")
                set_event_id_hwm(job_name, event_id, athena)


        job_status = "SUCCESS"
        message = (
            f"\n\n{total_rows_processed} rows added to {TARGET_DB}.{TARGET_TABLE}"
        )
        return

    except Exception as e:
        logger.error(f"Error: {e}")

        job_status = "FAILURE"
        message = f"\n\nJob failed:\n\n{traceback.format_exc()}"
        raise e

    finally:
        logger.info(message)
        logger.info("Sending SNS notification")
        sns.publish(
            TopicArn=sns_topic_arn,
            Subject=f"Glue Job {job_name}: {job_status}",
            Message=message,
        )


if __name__ == "__main__":
    main()
