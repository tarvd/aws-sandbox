import logging

import awswrangler as wr
import pandas as pd


def find_duplicate_zips_in_s3(s3_path: str) -> None:
    logging.info(f"Program starting with s3_path={s3_path}")
    files = wr.s3.list_objects(s3_path, suffix="zip")
    descriptions = wr.s3.describe_objects(
        "s3://tdouglas-data-prod-useast2/data/raw/openpowerlifting/lifter"
    )
    s3_data = pd.DataFrame(
        [
            {
                "id": file,
                "last_modified_at": pd.to_datetime(
                    descriptions[file]["ResponseMetadata"]["HTTPHeaders"][
                        "last-modified"
                    ],
                    format="%a, %d %b %Y %H:%M:%S %Z",
                ),
                "etag": descriptions[file]["ResponseMetadata"]["HTTPHeaders"]["etag"],
            }
            for file in files
        ]
    )
    keep_id = (
        s3_data.groupby("etag", as_index=True)["last_modified_at"].max().to_frame()
    )
    keep_data = s3_data[s3_data["last_modified_at"].isin(keep_id["last_modified_at"])]
    duplicate_list = s3_data[~(s3_data["id"].isin(keep_data["id"]))]["id"].tolist()
    logging.info(f"Found {len(duplicate_list)} duplicates in path")
    return duplicate_list

def print_duplicates(duplicate_list: list[str]) -> None:
    for item in duplicate_list:
        logging.info(f"Duplicate: {item}")
        print(item)


def main() -> None:
    logging.basicConfig(
        filename="openpowerlifting_lifter_prune_zip_logfile.log",
        level=logging.INFO,
        format="%(asctime)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    s3_path = "s3://tdouglas-data-prod-useast2/data/raw/openpowerlifting/lifter"
    duplicate_list = find_duplicate_zips_in_s3(s3_path)

    print_duplicates(duplicate_list)


if __name__ == "__main__":
    main()
