resource "aws_glue_catalog_database" "raw" {
  name = var.glue_database_raw.name
  create_table_default_permission {
    permissions = var.glue_database_raw.default_permissions
    principal {
      data_lake_principal_identifier = var.glue_database_raw.lf_principal
    }
  }
}

resource "aws_glue_catalog_database" "cleansed" {
  name = var.glue_database_cleansed.name
  create_table_default_permission {
    permissions = var.glue_database_cleansed.default_permissions
    principal {
      data_lake_principal_identifier = var.glue_database_cleansed.lf_principal
    }
  }
}

resource "aws_glue_catalog_database" "metadata" {
  name = var.glue_database_metadata.name
  create_table_default_permission {
    permissions = var.glue_database_metadata.default_permissions
    principal {
      data_lake_principal_identifier = var.glue_database_metadata.lf_principal
    }
  }
}

resource "aws_glue_catalog_database" "dbt" {
  name = var.glue_database_dbt.name
  create_table_default_permission {
    permissions = var.glue_database_dbt.default_permissions
    principal {
      data_lake_principal_identifier = var.glue_database_dbt.lf_principal
    }
  }
}

resource "aws_glue_catalog_table" "openpowerlifting" {
  name          = var.glue_table_openpowerlifting_raw.name
  database_name = var.glue_table_openpowerlifting_raw.database
  table_type    = var.glue_table_openpowerlifting_raw.table_type

  parameters = {
    classification           = var.glue_table_openpowerlifting_raw.classification
    "skip.header.line.count" = var.glue_table_openpowerlifting_raw.skip_header_line_count
  }

  storage_descriptor {
    location      = "s3://${aws_s3_bucket.raw_data.bucket}/${var.glue_table_openpowerlifting_raw.s3_prefix}/"
    input_format  = var.glue_table_openpowerlifting_raw.input_format
    output_format = var.glue_table_openpowerlifting_raw.output_format
    compressed    = var.glue_table_openpowerlifting_raw.compressed

    ser_de_info {
      serialization_library = var.glue_table_openpowerlifting_raw.serialization_library
      parameters            = {
        "separatorChar" = var.glue_table_openpowerlifting_raw.separation_char
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

  dynamic "partition_keys" {
    for_each = ["year", "month", "day"]
    content {
      name = partition_keys.value
      type = "string"
    }
  }

}
