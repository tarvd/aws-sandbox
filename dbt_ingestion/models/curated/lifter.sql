{{ config(
  materialized='table',
  table_type='iceberg',
  format='parquet'
) }}
WITH t AS (
  SELECT
    *,
    row_number() over (partition by primary_key order by source_record_date desc) as row_num
  FROM {{ ref('stg_openpowerlifting_lifter') }}
)
SELECT
  primary_key,
  name,
  sex,
  event_lifts,
  equipment,
  age,
  age_class,
  birth_year_class,
  division,
  bodyweight_kg,
  weight_class_kg,
  squat1_kg,
  squat2_kg,
  squat3_kg,
  squat4_kg,
  squat_best_of_3_kg,
  bench1_kg,
  bench2_kg,
  bench3_kg,
  bench4_kg,
  bench_best_of_3_kg,
  deadlift1_kg,
  deadlift2_kg,
  deadlift3_kg,
  deadlift4_kg,
  deadlift_best_of_3_kg,
  total_kg,
  place,
  dots,
  wilks,
  glossbrenner,
  goodlift,
  tested_meet,
  country,
  state,
  federation,
  parent_federation,
  meet_date,
  meet_country,
  meet_state,
  meet_town,
  meet_name,
  sanctioned,
  source_record_date
FROM t
WHERE row_num = 1
