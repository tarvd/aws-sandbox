import awswrangler as wr

"Name,Sex,Event,Equipment,Age,AgeClass,BirthYearClass,Division,BodyweightKg,WeightClassKg,Squat1Kg,Squat2Kg,Squat3Kg,Squat4Kg,Best3SquatKg,Bench1Kg,Bench2Kg,Bench3Kg,Bench4Kg,Best3BenchKg,Deadlift1Kg,Deadlift2Kg,Deadlift3Kg,Deadlift4Kg,Best3DeadliftKg,TotalKg,Place,Dots,Wilks,Glossbrenner,Goodlift,Tested,Country,State,Federation,ParentFederation,Date,MeetCountry,MeetState,MeetTown,MeetName,Sanctioned"


def convert_csv_to_parquet(source_s3_uri: str, target_s3_uri: str) -> None:
    """
    Converts CSV files in S3 to Parquet format.
    """

    # Read the S3 CSV data
    df = wr.s3.read_csv(source_s3_uri)

    # Convert the data to Parquet
    wr.s3.to_parquet(df, target_s3_uri)


def main() -> None:
    source_bucket = "ted-sand-dev-s3-use2-data"
    source_key = "openpowerlifting/openpowerlifting-2025-05-12-7d08e04b.csv"
    source_s3_uri = f"s3://{source_bucket}/{source_key}"

    target_bucket = "ted-sand-dev-s3-use2-data"
    target_key = "openpowerlifting/openpowerlifting-2025-05-12-7d08e04b.parquet"
    target_s3_uri = f"s3://{target_bucket}/{target_key}"

    convert_csv_to_parquet(source_s3_uri, target_s3_uri)


if __name__ == "__main__":
    main()
