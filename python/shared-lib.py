from hashlib import md5
from io import BytesIO
from zipfile import ZipFile
import time

import boto3
import requests


def get_file_from_url(url: str) -> BytesIO:
    response = requests.get(url)
    response.raise_for_status()
    return BytesIO(response.content)


def get_file_md5_hash(file, chunk_size: int = 1024) -> str:
    m = md5()
    with open(file, 'rb') as f:
        data = f.read(chunk_size)
        m.update(data)

    return m.hexdigest()
    

def run_athena_query(
    query: str,
    athena_client,
    database: str,
    output_location: str,
    poll_interval: float = 3.0,
    page_size: int = 1000
) -> dict:
    
    # Initiate query
    start_args = {
        "QueryString": query,
        "QueryExecutionContext": {"Database": database},
        "ResultConfiguration": {"OutputLocation": output_location},
    }

    response = athena_client.start_query_execution(**start_args)
    execution_id = response["QueryExecutionId"]

    # Poll for completion
    while True:
        status_response = athena_client.get_query_execution(
            QueryExecutionId=execution_id
        )
        status = status_response["QueryExecution"]["Status"]["State"]

        if status == "SUCCEEDED":
            break
        if status in ("FAILED", "CANCELLED"):
            reason = status_response["QueryExecution"]["Status"].get(
                "StateChangeReason", "Unknown error"
            )
            raise RuntimeError(
                f"Athena query {status.lower()}: {reason}"
            )

        time.sleep(poll_interval)

    # Paginate results
    all_rows = []
    column_info = None
    next_token = None
    is_first_page = True

    page_args = {
        "QueryExecutionId": execution_id,
        "MaxResults": page_size,
    }

    while True:
        response = athena_client.get_query_results(**page_args)

        if is_first_page:
            column_info = (
                response["ResultSet"]["ResultSetMetadata"]["ColumnInfo"]
            )
            all_rows.extend([x["Data"] for x in response["ResultSet"]["Rows"][1:]])
            is_first_page = False
        else:
            all_rows.extend([x["Data"] for x in response["ResultSet"]["Rows"][1:]])

        next_token = response.get("NextToken")
        if not next_token:
            break
        else:
            page_args["NextToken"] = next_token

    return {
        "ColumnInfo": column_info,
        "Rows": all_rows,
    }


def compare_ingestion_hash(hash: str, athena_client, **kwargs) -> bool:
    log_table = kwargs.get("log_table", "metadata.data_ingest_log")
    hash_column = kwargs.get("hash_column", "file_md5_hash")
    database = kwargs.get("database", "metadata")
    s3_output_location = kwargs.get("s3_output_location", "s3://dev-use2-tedsand-athena-results-s3/primary/")
    poll_interval = kwargs.get("poll_interval", 3.0)
    page_size = kwargs.get("page_size", 1000)

    hash_exists = False
    query = f"select count(*) > 0 as hash_exists from {log_table} where {hash_column} = '{hash}'"
    query_results = run_athena_query(query, athena_client, database, s3_output_location, poll_interval, page_size)["Rows"][0][0]["VarCharValue"]
    if query_results != 'false':
        hash_exists = True

    return hash_exists

    
def inspect_opl_zip(zip_file) -> tuple[str, str]:
    
    with ZipFile(zip_file) as z:
        csv_files = [name for name in z.namelist() if name.endswith(".csv")]
    
    if not csv_files:
        raise ValueError("No CSV files found in the ZIP archive.")
    csv_path = csv_files[0]

    csv_fn = csv_path.split("/")[-1]
    csv_fn_split = csv_fn.split("-")
    if len(csv_fn_split) >= 4:
        year_val, month_val, day_val = csv_fn.split("-")[1:4]
        if (
            len(year_val) == 4
            and len(month_val) == 2
            and len(day_val) == 2
            and year_val.isdigit()
            and month_val.isdigit()
            and day_val.isdigit()
            and year_val >= "2000"
            and year_val <= "3000"
            and month_val >= "01"
            and month_val <= "12"
            and day_val >= "01"
            and day_val <= "31"
        ):
            prefix = f"openpowerlifting/year={year_val}/month={month_val}/day={day_val}/"
    else:
        prefix = "openpowerlifting/year=__HIVE_DEFAULT_PARTITION__/month=__HIVE_DEFAULT_PARTITION__/day=__HIVE_DEFAULT_PARTITION__/"
    key = prefix + csv_fn

    return csv_path, key
    

def upload_csv_in_zip_to_s3(zip_file, s3_client, csv_path: str, bucket: str, key: str) -> dict:
    
    with ZipFile(zip_file) as z:
        with z.open(csv_path, "rb") as csv_file:
            s3_client.upload_fileobj(csv_file, bucket, key)



athena = boto3.client("athena")
s3 = boto3.client("s3")

# query = "select * from metadata.processed_data_log limit 5"
# result = run_athena_query(query, athena, "metadata", "s3://dev-use2-tedsand-athena-results-s3/primary/")
# print(result["Rows"][0][0]["VarCharValue"])

# result = compare_ingestion_hash("asdf", athena, s3_output_location="s3://dev-use2-tedsand-athena-results-s3/primary/")
# print(result)