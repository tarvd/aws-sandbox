import os
import logging

import awswrangler as wr
import pandas as pd

def main() -> None:
    logging.basicConfig(
        filename=os.path.join("log", "athena_operations.log"),
        level=logging.INFO,
        format="%(asctime)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    logging.info(f"Program start at {pd.Timestamp.now()}")

    temp_path = "s3://tdouglas-data-prod-useast2/data/temp/"
    database = "openpowerlifting"
    table = "lifter"
    temp_database = "temp"

    query = """
        with t1 as (
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
            from 
                lifter
        ),
        t2 as (
            select
                row_number() over (partition by lifter_id) as rownum,
                *
            from 
                t1
        )
        select 
            lifter_id,
            name,
            sex,
            event,
            equipment,
            age,
            ageclass,
            birthyearclass,
            division,
            bodyweightkg,
            weightclasskg,
            squat1kg,
            squat2kg,
            squat3kg,
            squat4kg,
            best3squatkg,
            bench1kg,
            bench2kg,
            bench3kg,
            bench4kg,
            best3benchkg,
            deadlift1kg,
            deadlift2kg,
            deadlift3kg,
            deadlift4kg,
            best3deadliftkg,
            totalkg,
            place,
            dots,
            wilks,
            glossbrenner,
            goodlift,
            tested,
            country,
            state,
            federation,
            parentfederation,
            date,
            meetcountry,
            meetstate,
            meettown,
            meetname,
            sanctioned
        from 
            t
        where 
            rownum = 1
    """
    result = wr.athena.create_ctas_table(
        sql=query,
        database="temp",  # Athena database
        ctas_table="lifter_with_id",  # New table name
        ctas_database="temp",  # Target database for the new table
    )
    print(result)
    print(result.keys())


if __name__ == "__main__":
    main()
