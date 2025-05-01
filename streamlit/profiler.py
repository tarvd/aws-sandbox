import streamlit as st
import duckdb
import os

def main() -> None:
    print("start")
    st.markdown("## Lifter Data Profiler")
    col1, col2 = st.columns([1,2])


    @st.cache_data
    def read_columns(parquet_file):
        # Read column data from parquet 
        return duckdb.sql(f"DESCRIBE SELECT * FROM '{parquet_file}'").df()

    @st.cache_data
    def read_data(parquet_file):
        # Read data from parquet
        return duckdb.sql(f"SELECT * FROM '{parquet_file}'").df()

    # Read columns and add columns.
    filename = "lifter.parquet"
    filesize = os.path.getsize(filename)
    col1.write(f"File name: {filename}")
    col1.write(f"File size: {round(filesize/1000000)}MB")

    cols_df = read_columns(filename)
    cols_df["formatted_name"] = cols_df["column_name"].str.replace("_"," ").str.title()
    cols_df["is_numeric"] = [True if x in ["INTEGER", "FLOAT"] else False for x in cols_df["column_type"]]


    grouping_options = cols_df[~cols_df["is_numeric"]]["formatted_name"].to_list()
    col_name_grouping = col1.selectbox(label="Grouping", options=grouping_options)
    function_options = ["Count", "Sum", "Mean", "Median", "Min", "Max", "Std Dev", "Variance"]
    col_name_function = col1.selectbox(label="Function", options=function_options)
    argument_options = cols_df[cols_df["is_numeric"]]["formatted_name"].to_list()
    if col_name_function == "Count":
        argument_options = ["*"] + argument_options
    col_name_argument = col1.selectbox(label="Argument", options=argument_options)

    col_grouping = cols_df.loc[cols_df["formatted_name"] == col_name_grouping, "column_name"].item()
    sql_function = {
        "Count": "COUNT",
        "Sum": "SUM",
        "Mean": "AVG",
        "Median": "MEDIAN",
        "Min": "MIN",
        "Max": "MAX",
        "Std Dev": "STDDEV",
        "Variance": "VARIANCE"
    }[col_name_function]
    if col_name_argument == "*":
        col_argument = "*"
    else:
        col_argument = cols_df.loc[cols_df["formatted_name"] == col_name_argument, "column_name"].item()
    calculation_col = f"{sql_function.lower()}_{col_argument}".replace("*", "all")

    result_sql = f"SELECT {col_grouping}, {sql_function}({col_argument}) as {calculation_col} FROM 'lifter.parquet' WHERE {col_grouping} IS NOT NULL GROUP BY 1 ORDER BY 2 DESC"
    result_df = duckdb.sql(result_sql).df().set_index(col_grouping)
    col2.markdown(f":blue-background[{result_sql}]")
    col2.write(result_df)
    col2.write(result_df.dtypes)
    # col2.bar_chart(data=result_df, horizontal=True)

    print("done")

if __name__ == '__main__':
    main()