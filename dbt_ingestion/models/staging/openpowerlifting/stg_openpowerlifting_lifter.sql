SELECT
     MD5(TO_UTF8(CONCAT(COALESCE(name, 'Null'), '-', COALESCE(event, 'Null'), '-', COALESCE(equipment, 'Null'), '-', COALESCE(division, 'Null'), '-', COALESCE(place, 'Null'), '-', COALESCE("date", 'Null'), '-', COALESCE(meetname, 'Null')))) primary_key
   , name
   , sex
   , event event_lifts
   , equipment
   , age
   , NULLIF(ageclass, '') age_class
   , NULLIF(birthyearclass, '') birth_year_class
   , NULLIF(division, '') division
   , bodyweightkg bodyweight_kg
   , NULLIF(weightclasskg, '') weight_class_kg
   , squat1kg squat1_kg
   , squat2kg squat2_kg
   , squat3kg squat3_kg
   , squat4kg squat4_kg
   , best3squatkg squat_best_of_3_kg
   , bench1kg bench1_kg
   , bench2kg bench2_kg
   , bench3kg bench3_kg
   , bench4kg bench4_kg
   , best3benchkg bench_best_of_3_kg
   , deadlift1kg deadlift1_kg
   , deadlift2kg deadlift2_kg
   , deadlift3kg deadlift3_kg
   , deadlift4kg deadlift4_kg
   , best3deadliftkg deadlift_best_of_3_kg
   , totalkg total_kg
   , place
   , dots
   , wilks
   , glossbrenner
   , goodlift
   , COALESCE(tested, 'No') tested_meet
   , NULLIF(country, '') country
   , NULLIF(state, '') state
   , NULLIF(federation, '') federation
   , NULLIF(parentfederation, '') parent_federation
   , date("date") meet_date
   , NULLIF(meetcountry, '') meet_country
   , NULLIF(meetstate, '') meet_state
   , NULLIF(meettown, '') meet_town
   , NULLIF(meetname, '') meet_name
   , sanctioned
   , date(substring(element_at(split("$path", 'openpowerlifting-'), 2), 1, 10)) source_record_date
   FROM
     {{ source('openpowerlifting', 'lifter') }}
