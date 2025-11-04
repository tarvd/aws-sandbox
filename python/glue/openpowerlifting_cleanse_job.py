
# %idle_timeout 20
# %glue_version 5.0
# %worker_type G.1X
# %number_of_workers 2


# %%configure 
# {
#     "--conf": "spark.sql.extensions=org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions \
#                 --conf spark.sql.catalog.glue_catalog=org.apache.iceberg.spark.SparkCatalog \
#                 --conf spark.sql.catalog.glue_catalog.warehouse=s3://dev-use2-tedsand-iceberg-s3/warehouse/ \
#                 --conf spark.sql.catalog.glue_catalog.catalog-impl=org.apache.iceberg.aws.glue.GlueCatalog \
#                 --conf spark.sql.catalog.glue_catalog.io-impl=org.apache.iceberg.aws.s3.S3FileIO",
#     "--datalake-formats": "iceberg",
#     "--JOB_NAME": "iceberg-test",
#     "--JOB_ID": "j_123",
#     "--JOB_RUN_ID": "jr_456"
# }

# TODO: Create Glue job in TF with above settings
# TODO: Add output logging
# TODO: Clean up constants


import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job


import boto3
from datetime import datetime, timezone
from pyspark.sql.functions import lit, concat_ws, current_timestamp, coalesce, sha2
  

# Load Constants and Config
source_db = "raw"
source_table = "openpowerlifting"
source_system = "Openpowerlifting.org"
target_db = "cleansed"
target_table = "openpowerlifting_test"
context = "RawToIcebergCleanseJob"
processed_data_cols = ["file_key", "job_name", "context", "processed_at", "job_id", "job_run_id"]
rename_cols_map = {
    "Name":"name",
    "Sex":"sex",
    "Event":"event",
    "Equipment":"equipment",
    "Age":"age",
    "AgeClass":"age_class",
    "BirthYearClass":"birth_year_class",
    "Division":"division",
    "BodyweightKg":"bodyweight_kg",
    "WeightClassKg":"weightclass_kg",
    "Squat1Kg":"squat_1_kg",
    "Squat2Kg":"squat_2_kg",
    "Squat3Kg":"squat_3_kg",
    "Squat4Kg":"squat_4_kg",
    "Best3SquatKg":"best_3_squat_kg",
    "Bench1Kg":"bench_1_kg",
    "Bench2Kg":"bench_2_kg",
    "Bench3Kg":"bench_3_kg",
    "Bench4Kg":"bench_4_kg",
    "Best3BenchKg":"best_3_bench_kg",
    "Deadlift1Kg":"deadlift_1_kg",
    "Deadlift2Kg":"deadlift_2_kg",
    "Deadlift3Kg":"deadlift_3_kg",
    "Deadlift4Kg":"deadlift_4_kg",
    "Best3DeadliftKg":"best_3_deadlift_kg",
    "TotalKg":"total_kg",
    "Place":"place",
    "Dots":"dots",
    "Wilks":"wilks",
    "Glossbrenner":"glossbrenner",
    "Goodlift":"goodlift",
    "Tested":"tested",
    "Country":"country",
    "State":"state",
    "Federation":"federation",
    "ParentFederation":"parent_federation",
    "Date":"date",
    "MeetCountry":"meet_country",
    "MeetState":"meet_state",
    "MeetTown":"meet_town",
    "MeetName":"meet_name",
    "Sanctioned":"sanctioned"
}


def main():

    sc = SparkContext.getOrCreate()
    glueContext = GlueContext(sc)
    spark = glueContext.spark_session

    args = getResolvedOptions(sys.argv, ['JOB_NAME'])
    job_name = args['JOB_NAME']
    job_id = args['JOB_ID']
    job_run_id = args['JOB_RUN_ID']

    glue = boto3.client('glue')
    s3 = boto3.client('s3')


    # Get list of table S3 files
    source_location = glue.get_table(DatabaseName=source_db, Name=source_table)['Table']['StorageDescriptor']['Location']
    split = source_location.split('/')
    source_bucket = split[2]
    source_prefix = '/'.join(split[3:])

    response = s3.list_objects_v2(Bucket=source_bucket, Prefix=source_prefix)
    source_objects = [obj['Key'] for obj in response['Contents']]
    while response['IsTruncated']:
        token = response['NextContinuationToken']
        response = s3.list_objects_v2(Bucket=source_bucket, Prefix=source_prefix, NextContinuationToken=token)
        source_objects.extend([obj['Key'] for obj in response['Contents']])

    skip_files_df = spark.sql(f"SELECT file_key FROM glue_catalog.metadata.processed_data_log WHERE job_name='{job_name}' AND context='{context}'")
    skip_files_list = skip_files_df.select("file_key").rdd.flatMap(lambda x: x).collect()
    source_file_list = sorted([f"s3://{source_bucket}/{path}" for path in source_objects if f"s3://{source_bucket}/{path}" not in skip_files_list])

    # Loop through files to read
    for filename in source_file_list:

        # Data to insert into Processed Data Log table (replicating functionality of Glue Job Bookmark)
        processing_timestamp = datetime.now(timezone.utc)
        processed_data_row = [(filename, job_name, context, processing_timestamp, job_id, job_run_id)]

        # Read source data
        df = glueContext.create_data_frame.from_options(
            connection_type='s3',
            connection_options={"paths":[filename]},
            format='csv',
            format_options={
                "withHeader": True
            }
        )

        processed_data_df = spark.createDataFrame(processed_data_row, processed_data_cols)

        # Get already-existing row hashes from target table to filter source data
        target_rows_df = spark.sql(f"SELECT row_hash FROM glue_catalog.{target_db}.{target_table}")

        # Hash the source data rows, deduplicate on hash, and remove rows that already exist in the target
        df = df.withColumn("row_hash", sha2(concat_ws(':', *[coalesce(col, lit('')).alias(col) for col in df.schema.names]), 256))
        df = df.dropDuplicates(["row_hash"])
        df = df.join(target_rows_df, ["row_hash"], "leftouter").where(target_rows_df["row_hash"].isNull()).drop(target_rows_df["row_hash"])

        # Add audit columns
        df = df.withColumn("source_system", lit(source_system))
        df = df.withColumn("source_table", lit(f"{source_db}.{source_table}"))
        df = df.withColumn("inserted_at", current_timestamp())
        df = df.withColumn("job_name", lit(job_name))
        df = df.withColumn("job_id", lit(job_id))
        df = df.withColumn("job_run_id", lit(job_run_id))

        # Rename camel case to snake case
        df = df.withColumnsRenamed(rename_cols_map)


        # Write data to target
        df.writeTo(f"glue_catalog.{target_db}.{target_table}") \
        .tableProperty("format-version", "2") \
        .append()

        # Write row to Processed Data Log
        processed_data_df.writeTo("glue_catalog.metadata.processed_data_log") \
        .tableProperty("format-version", "2") \
        .append()
