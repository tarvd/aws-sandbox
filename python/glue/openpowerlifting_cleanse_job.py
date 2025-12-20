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


# Logging
MSG_FORMAT = "%(asctime)s %(levelname)s %(name)s: %(message)s"
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
logging.basicConfig(format=MSG_FORMAT, datefmt=DATETIME_FORMAT)
logger = logging.getLogger("glue-log")
logger.setLevel(logging.INFO)


# Constants and Config
SOURCE_DB = "raw"
SOURCE_TABLE = "openpowerlifting"
SOURCE_SYSTEM = "Openpowerlifting.org"
TARGET_DB = "cleansed"
TARGET_TABLE = "openpowerlifting"
CONTEXT = "RawToIcebergCleanseJob"

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


def main():
    try:
        logger.info("Beginning job, loading arguments.")

        sc = SparkContext.getOrCreate()
        glueContext = GlueContext(sc)
        spark = glueContext.spark_session
        glue = boto3.client("glue")
        s3 = boto3.client("s3")
        sns = boto3.client("sns")

        args = getResolvedOptions(sys.argv, ["JOB_NAME", "sns_topic_arn"])
        job_name = args["JOB_NAME"]
        job_id = args["JOB_ID"]
        job_run_id = args["JOB_RUN_ID"]
        sns_topic_arn = args["sns_topic_arn"]
        total_rows_processed = 0

        logger.info(f"Reading list of files for {SOURCE_DB}.{SOURCE_TABLE}")

        source_location = glue.get_table(DatabaseName=SOURCE_DB, Name=SOURCE_TABLE)[
            "Table"
        ]["StorageDescriptor"]["Location"]
        split = source_location.split("/")
        source_bucket = split[2]
        source_prefix = "/".join(split[3:])

        response = s3.list_objects_v2(Bucket=source_bucket, Prefix=source_prefix)
        source_objects = [obj["Key"] for obj in response["Contents"]]
        while response["IsTruncated"]:
            token = response["NextContinuationToken"]
            response = s3.list_objects_v2(
                Bucket=source_bucket, Prefix=source_prefix, NextContinuationToken=token
            )
            source_objects.extend([obj["Key"] for obj in response["Contents"]])

        skip_files_df = spark.sql(
            f"SELECT file_key FROM glue_catalog.metadata.processed_data_log WHERE job_name='{job_name}' AND context='{CONTEXT}'"
        )
        skip_files_list = (
            skip_files_df.select("file_key").rdd.flatMap(lambda x: x).collect()
        )
        source_file_list = sorted(
            [
                f"s3://{source_bucket}/{path}"
                for path in source_objects
                if f"s3://{source_bucket}/{path}" not in skip_files_list
                and path[-4:] == ".csv"
            ]
        )

        if len(source_file_list) == 0:
            logger.info("No new data to process, ending job.")
            job_status = "NO NEW DATA"
            sns_message = "No new data to process."
            return

        logger.info(f"Files to process: {source_file_list}")

        # Process each file
        for filename in source_file_list:
            logger.info(f"Processing file: {filename}")

            # Keep track of processed files
            processing_timestamp = datetime.now(timezone.utc)
            processed_data_row = [
                (filename, job_name, CONTEXT, processing_timestamp, job_id, job_run_id)
            ]
            processed_data_df = spark.createDataFrame(
                processed_data_row, PROCESSED_DATA_COLS
            )

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
            if filename == source_file_list[-1]:
                df.createOrReplaceTempView("latest_data")
                spark.sql(f"""
                    UPDATE glue_catalog.{TARGET_DB}.{TARGET_TABLE}
                    SET is_deleted = true
                    WHERE row_hash NOT IN (SELECT row_hash FROM latest_data)
                """)

            logger.info(f"Adding row to metadata.processed_data_log for {filename}")
            processed_data_df.writeTo(
                "glue_catalog.metadata.processed_data_log"
            ).tableProperty("format-version", "2").append()

            total_rows_processed += filtered_num_rows

        logger.info(f"Job {job_name} completed successfully")
        job_status = "SUCCEEDED"
        sns_message = (
            f"\n\n{total_rows_processed} rows added to {TARGET_DB}.{TARGET_TABLE}"
        )

    except Exception as e:
        logger.error(f"Error: {e}")

        job_status = "FAILED"
        sns_message = f"\n\nJob failed:\n\n{error_message}"
        error_message = traceback.format_exc()

        raise e

    finally:
        logger.info("Sending SNS notification")
        sns.publish(
            TopicArn=sns_topic_arn,
            Subject=f"Glue Job {job_name}: {job_status}",
            Message=sns_message,
        )


if __name__ == "__main__":
    main()
