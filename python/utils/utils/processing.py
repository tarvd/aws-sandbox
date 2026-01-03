
from utils.common import run_athena_query


def get_process_event_id_hwm(event_consumer: str, athena_client, log_table: str = "metadata.data_process_log") -> int:
    read_sql = f"""
        select current_event_hwm
        from {log_table}
        where event_consumer = '{event_consumer}'
        limit 1
    """
    result = run_athena_query(read_sql, athena_client)
    rows = result.get("Rows", [])
    if len(rows) > 0:
        event_id_hwm = int(rows[0][0].get("VarCharValue", -1))
    else:
        event_id_hwm = -1
    return event_id_hwm


def set_process_event_id_hwm(event_consumer: str, event_hwm: int, athena_client, log_table: str = "metadata.data_process_log") -> None:
    update_sql = f"""
        update {log_table}
        set current_event_hwm = {event_hwm}
        where event_consumer = '{event_consumer}'
    """
    run_athena_query(update_sql, athena_client, False)
    return


def get_latest_ingest_event_id(athena_client, log_table: str = "metadata.data_ingest_log") -> int:
    read_sql = f"""
        select coalesce(max(event_id),-1)
        from {log_table}
    """
    latest_event_id = int(run_athena_query(read_sql, athena_client)["Rows"][0][0]["VarCharValue"])
    return latest_event_id


def insert_row_to_process_log(event_consumer: str, event_id: int, process_detail: str, athena_client, log_table: str = "metadata.data_process_log") -> None:
    event_id_hwm = get_process_event_id_hwm(event_consumer, athena_client, log_table)
    
    insert_sql = f"""
        insert into {log_table} (process_id, event_consumer, event_id, current_event_hwm, process_ts, process_detail)
        select 
            '{event_consumer}' || '_' || cast({event_id} as varchar) as process_id,
            '{event_consumer}' as event_consumer,
            {event_id} as event_id,
            {event_id_hwm} as current_event_hwm,
            current_timestamp as process_ts,
            '{process_detail}' as process_detail;
    """
    run_athena_query(insert_sql, athena_client, False)

    if event_id > event_id_hwm:
        set_process_event_id_hwm(event_consumer, event_id, athena_client, log_table)

    return
