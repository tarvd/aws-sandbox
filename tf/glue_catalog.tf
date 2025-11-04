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

resource "aws_glue_catalog_database" "metadata" {
  name = "metadata"
  create_table_default_permission {
    permissions = ["SELECT"]
    principal {
      data_lake_principal_identifier = "IAM_ALLOWED_PRINCIPALS"
    }
  }
}

resource "aws_glue_catalog_table" "openpowerlifting" {
  name          = "openpowerlifting"
  database_name = aws_glue_catalog_database.raw.name
  table_type    = "EXTERNAL_TABLE"

  parameters = {
    classification = "csv"
    "skip.header.line.count" = "1" 
  }

  storage_descriptor {
    location      = "s3://${aws_s3_bucket.raw_data.bucket}/openpowerlifting/"
    input_format  = "org.apache.hadoop.mapred.TextInputFormat"
    output_format = "org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat"
    compressed    = false

    ser_de_info {
      serialization_library = "org.apache.hadoop.hive.serde2.OpenCSVSerde"

      parameters = {
        "separatorChar" = ","
      }
    }

    dynamic "columns" {
      for_each = [
        "name", "sex", "event", "equipment", "age", "ageclass", "birthyearclass",
        "division", "bodyweightkg", "weightclasskg", "squat1kg", "squat2kg",
        "squat3kg", "squat4kg", "best3squatkg", "bench1kg", "bench2kg", "bench3kg",
        "bench4kg", "best3benchkg", "deadlift1kg", "deadlift2kg", "deadlift3kg",
        "deadlift4kg", "best3deadliftkg", "totalkg", "place", "dots", "wilks",
        "glossbrenner", "goodlift", "tested", "country", "state", "federation",
        "parentfederation", "date", "meetcountry", "meetstate", "meettown",
        "meetname", "sanctioned"
      ]
      content {
        name    = columns.value
        type    = "string"
        comment = ""
      }
    }
  }

  partition_keys {
    name = "year"
    type = "string"
  }

  partition_keys {
    name = "month"
    type = "string"
  }

  partition_keys {
    name = "day"
    type = "string"
  }

}

resource "aws_glue_catalog_table" "processed_data_log" {
  name          = "processsed_data_log"
  database_name = aws_glue_catalog_database.metadata.name
  table_type    = "EXTERNAL_TABLE"

  parameters    = {
    "format"            = "parquet"
  }

  open_table_format_input {
    iceberg_input {
      metadata_operation = "CREATE"
    }
  }


  storage_descriptor {
    location = "s3://dev-use2-tedsand-iceberg-s3/warehouse/metadata.db/processed_data_log/"

  }
}