insert into metadata.data_ingest_log
select 
    row_number() over (partition by 1 order by file_key) - 1 as event_id,
    cast(substring(file_key, 95, 10) || ' 18:00:00.000' as timestamp) as ingest_ts,
    'new_file' as event_type,
    'Openpowerlifting.org' as source_system,
    null as file_md5_hash,
    null as payload
from processed_data_log



merge into metadata.data_ingest_log l
using metadata.processed_data_log p
on cast(date(l.ingest_ts) as varchar) = substring(p.file_key, 95, 10)
when matched then
update set
payload = '{"ingest_ts":"' || cast(l.ingest_ts as varchar) || '","event_type":"' || l.event_type || '","source_system":"' || l.source_system || '","file_md5_hash":"' || l.file_md5_hash || '","s3_location":"' || p.file_key || '"}'


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
