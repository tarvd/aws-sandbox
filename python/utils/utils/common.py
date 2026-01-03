import time
import boto3


def run_athena_query(
    query: str,
    athena_client=None,
    return_result: bool = True,
    poll_interval: float = 1.0,
    page_size: int = 1000,
) -> dict:
    if athena_client is None:
        athena_client = boto3.client("athena")

    # Initiate query
    start_args = {
        "QueryString": query,
        "QueryExecutionContext": {"Database": "metadata"},
        "WorkGroup": "primary",
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
            raise RuntimeError(f"Athena query {status.lower()}: {reason}")

        time.sleep(poll_interval)

    # Paginate results
    if return_result:
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
                column_info = response["ResultSet"]["ResultSetMetadata"]["ColumnInfo"]
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
            "Status": status,
            "ColumnInfo": column_info,
            "Rows": all_rows,
        }
    else:
        return {"Status": status}
