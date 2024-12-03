create table openpowerlifting.lifter_with_id
with (table_type = 'ICEBERG',
      format = 'PARQUET', 
      location = 's3://tdouglas-data-prod-useast2/data/raw/openpowerlifting/lifter_with_id/iceberg/',
      is_external= false
   ) 
as
select 
    sha256(
        cast(
            concat(
                concat(coalesce(cast(name as varchar),'Null'),'-'),
                concat(coalesce(cast(sex as varchar),'Null'),'-'),
                concat(coalesce(cast(event as varchar),'Null'),'-'),
                concat(coalesce(cast(equipment as varchar),'Null'),'-'),
                concat(coalesce(cast(age as varchar),'Null'),'-'),
                concat(coalesce(cast(ageclass as varchar),'Null'),'-'),
                concat(coalesce(cast(birthyearclass as varchar),'Null'),'-'),
                concat(coalesce(cast(division as varchar),'Null'),'-'),
                concat(coalesce(cast(bodyweightkg as varchar),'Null'),'-'),
                concat(coalesce(cast(weightclasskg as varchar),'Null'),'-'),
                concat(coalesce(cast(squat1kg as varchar),'Null'),'-'),
                concat(coalesce(cast(squat2kg as varchar),'Null'),'-'),
                concat(coalesce(cast(squat3kg as varchar),'Null'),'-'),
                concat(coalesce(cast(squat4kg as varchar),'Null'),'-'),
                concat(coalesce(cast(best3squatkg as varchar),'Null'),'-'),
                concat(coalesce(cast(bench1kg as varchar),'Null'),'-'),
                concat(coalesce(cast(bench2kg as varchar),'Null'),'-'),
                concat(coalesce(cast(bench3kg as varchar),'Null'),'-'),
                concat(coalesce(cast(bench4kg as varchar),'Null'),'-'),
                concat(coalesce(cast(best3benchkg as varchar),'Null'),'-'),
                concat(coalesce(cast(deadlift1kg as varchar),'Null'),'-'),
                concat(coalesce(cast(deadlift2kg as varchar),'Null'),'-'),
                concat(coalesce(cast(deadlift3kg as varchar),'Null'),'-'),
                concat(coalesce(cast(deadlift4kg as varchar),'Null'),'-'),
                concat(coalesce(cast(best3deadliftkg as varchar),'Null'),'-'),
                concat(coalesce(cast(totalkg as varchar),'Null'),'-'),
                concat(coalesce(cast(place as varchar),'Null'),'-'),
                concat(coalesce(cast(dots as varchar),'Null'),'-'),
                concat(coalesce(cast(wilks as varchar),'Null'),'-'),
                concat(coalesce(cast(glossbrenner as varchar),'Null'),'-'),
                concat(coalesce(cast(goodlift as varchar),'Null'),'-'),
                concat(coalesce(cast(tested as varchar),'Null'),'-'),
                concat(coalesce(cast(country as varchar),'Null'),'-'),
                concat(coalesce(cast(state as varchar),'Null'),'-'),
                concat(coalesce(cast(federation as varchar),'Null'),'-'),
                concat(coalesce(cast(parentfederation as varchar),'Null'),'-'),
                concat(coalesce(cast(date as varchar),'Null'),'-'),
                concat(coalesce(cast(meetcountry as varchar),'Null'),'-'),
                concat(coalesce(cast(meetstate as varchar),'Null'),'-'),
                concat(coalesce(cast(meettown as varchar),'Null'),'-'),
                concat(coalesce(cast(meetname as varchar),'Null'),'-'),
                concat(coalesce(cast(sanctioned as varchar),'Null'),'')
            ) as varbinary
        )
    ) as lifter_id,
    *
from openpowerlifting.lifter