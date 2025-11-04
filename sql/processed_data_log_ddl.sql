CREATE TABLE metadata.processed_data_log (
  file_key string,
  job_name string,
  context string,
  processed_at timestamp,
  job_id string,
  job_run_id string
 ) 
PARTITIONED BY (job_name, context) 
LOCATION 's3://dev-use2-tedsand-iceberg-s3/warehouse/metadata.db/processed_data_log' 
TBLPROPERTIES (
  'table_type'='ICEBERG',
  'format'='parquet',
  'write_compression'='snappy'
)
