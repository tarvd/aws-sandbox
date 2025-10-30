from awsglue.context import GlueContext
from pyspark.context import SparkContext
import boto3

# Initialize Spark and Glue context
sc = SparkContext.getOrCreate()
glueContext = GlueContext(sc)
spark = glueContext.spark_session

# Parameters
RAW_DATA_PATH = "s3://ted-sand-dev-s3-use2-data/openpowerlifting/"
CLEANSED_DB = "cleansed"
CLEANSED_TBL = "openpowerlifting"

# Read CSV with Spark to infer schema
df = spark.read.option("header", "true").csv(RAW_DATA_PATH)


# Get schema as list of Glue-compatible columns
def spark_type_to_glue_type(spark_type):
    # Map Spark SQL types to Glue types (Hive types)
    mapping = {
        "StringType": "string",
        "IntegerType": "int",
        "LongType": "bigint",
        "DoubleType": "double",
        "FloatType": "float",
        "BooleanType": "boolean",
        "TimestampType": "timestamp",
        "DateType": "date",
    }
    return mapping.get(spark_type, "string")  # default string if unknown


columns = []
for field in df.schema.fields:
    glue_type = spark_type_to_glue_type(field.dataType.typeName())
    columns.append({"Name": field.name, "Type": glue_type})

# Initialize boto3 Glue client
glue = boto3.client("glue")

# Define table input with inferred schema
table_input = {
    "Name": CLEANSED_TBL,
    "TableType": "EXTERNAL_TABLE",
    "Parameters": {
        "classification": "csv",
        "skip.header.line.count": "1",
        "EXTERNAL": "TRUE",
        "typeOfData": "file",
    },
    "StorageDescriptor": {
        "Columns": columns,
        "Location": RAW_DATA_PATH,  # folder containing CSV
        "InputFormat": "org.apache.hadoop.mapred.TextInputFormat",
        "OutputFormat": "org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat",
        "SerdeInfo": {
            "Name": "csv",
            "SerializationLibrary": "org.apache.hadoop.hive.serde2.lazy.LazySerDe",
            "Parameters": {"field.delim": ",", "skip.header.line.count": "1"},
        },
    },
}

glue.create_table(DatabaseName=CLEANSED_DB, TableInput=table_input)
