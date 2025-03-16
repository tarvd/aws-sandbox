import awswrangler as wr

def main():
    df = wr.athena.read_sql_query(
        sql="SELECT * FROM data_lake_curated.lifter", 
        database="data_lake_curated", 
        ctas_approach=True
    )
    df.to_parquet("lifter.parquet")

if __name__ == "__main__":
    main()