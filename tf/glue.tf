resource "aws_glue_catalog_database" "raw" {
  name = "raw"
  create_table_default_permission {
    permissions = ["SELECT"]
    principal {
      data_lake_principal_identifier = "IAM_ALLOWED_PRINCIPALS"
    }
  }
}

resource "aws_glue_catalog_database" "cleansed" {
  name = "cleansed"
  create_table_default_permission {
    permissions = ["SELECT"]
    principal {
      data_lake_principal_identifier = "IAM_ALLOWED_PRINCIPALS"
    }
  }
}

# resource "aws_glue_catalog_table" "raw_openpowerlifting" {
#   name          = "openpowerlifting"
#   database_name = aws_glue_catalog_database.raw.name
# }

# resource "aws_glue_catalog_table" "cleansed_openpowerlifting" {
#   name          = "openpowerlifting"
#   database_name = aws_glue_catalog_database.cleansed.name

#   table_type = "ICEBERG"

#   parameters = {
#     "table_type"                        = "ICEBERG"
#     "classification"                    = "iceberg"
#     "write.format.default"               = "parquet" # Iceberg can store in parquet/orc/avro
#     "format"                             = "iceberg"
#     "EXTERNAL"                           = "TRUE"
#     "metadata_location"                  = "s3://ted-sand-dev-s3-use2-cleansed-data/openpowerlifting/metadata/metadata.json"=
#   }

#   storage_descriptor {
#     location      = "s3://ted-sand-dev-s3-use2-cleansed-data/openpowerlifting/"
#     input_format  = "org.apache.iceberg.mr.hive.HiveIcebergInputFormat"
#     output_format = "org.apache.iceberg.mr.hive.HiveIcebergOutputFormat"

#     ser_de_info {
#       serialization_library = "org.apache.iceberg.mr.hive.HiveIcebergSerDe"
#     }

#     columns {
#       name = "id"
#       type = "int"
#     }
#     columns {
#       name = "name"
#       type = "string"
#     }
#     columns {
#       name = "event_time"
#       type = "timestamp"
#     }
#   }
# }
