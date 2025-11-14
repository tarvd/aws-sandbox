
{{ config(materialized='table') }}

select 
    row_hash,
    name,
    age,
    date
from {{source('cleansed', 'openpowerlifting')}}
limit 50