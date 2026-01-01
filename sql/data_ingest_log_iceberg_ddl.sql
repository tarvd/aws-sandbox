CREATE TABLE metadata.data_ingest_log (
    event_id        int,
    ingest_ts       timestamp,
    event_type      string,
    source_system   string,
    file_md5_hash   string,
    payload         string
)
PARTITIONED BY (bucket(16, event_id)) 
LOCATION 's3://dev-use2-tedsand-iceberg-s3/warehouse/metadata.db/data_ingest_log' 
TBLPROPERTIES (
  'table_type'='ICEBERG',
  'format'='parquet',
  'write_compression'='snappy'
)
