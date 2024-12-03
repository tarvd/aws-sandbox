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
    

    data_filename = f"{database}-{table}-{pd.Timestamp.now().strftime('%Y%m%d')}.zip"
    data_s3_dir = f"s3://tdouglas-data-prod-useast2/data/raw/{database}/{table}/zip"
    data_s3_path = f"{data_s3_dir}/{data_filename}"
    temp_zip_filename = f"{database}-{table}.zip"
    csv_s3_dir = f"s3://tdouglas-data-prod-useast2/data/raw/{database}/{table}/csv"
    table_location = (
        f"s3://tdouglas-data-prod-useast2/data/raw/{database}/{table}/iceberg/"
    )

    


if __name__ == "__main__":
    main()
