CREATE TABLE metadata.data_process_log (
    process_id            string,
    event_consumer        string,
    event_id              int,  
    current_event_hwm     int,
    process_ts            timestamp,
    process_detail        string
)
PARTITIONED BY (event_consumer, bucket(16, event_id)) 
LOCATION 's3://dev-use2-tedsand-iceberg-s3/warehouse/metadata.db/data_process_log' 
TBLPROPERTIES (
  'table_type'='ICEBERG',
  'format'='parquet',
  'write_compression'='snappy'
)
