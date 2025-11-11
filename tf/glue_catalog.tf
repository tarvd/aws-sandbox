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

resource "aws_glue_catalog_table" "openpowerlifting" {
  name          = var.glue_table_openpowerlifting_raw.name
  database_name = aws_glue_catalog_database.raw.name
  table_type    = var.glue_table_openpowerlifting_raw.table_type

  parameters = {
    classification = var.glue_table_openpowerlifting_raw.classification
    "skip.header.line.count" = var.glue_table_openpowerlifting_raw.skip_header_line_count
  }

  storage_descriptor {
    location      = "s3://${aws_s3_bucket.raw_data.bucket}/${var.glue_table_openpowerlifting_raw.s3_prefix}/"
    input_format  = var.glue_table_openpowerlifting_raw.input_format
    output_format = var.glue_table_openpowerlifting_raw.output_format
    compressed    = var.glue_table_openpowerlifting_raw.compressed

    ser_de_info {
      serialization_library = var.glue_table_openpowerlifting_raw.serialization_library

      parameters = {
        "separatorChar" = "${var.glue_table_openpowerlifting_raw.separation_char}"
      }
    }

    dynamic "columns" {
      for_each = var.glue_table_openpowerlifting_raw.column_list
      content {
        name    = columns.value
        type    = "string"
        comment = ""
      }
    }
  }

  dynamic "partition_keys" {
    for_each = var.glue_table_openpowerlifting_raw.partition_column_list
    content {
      name = partition_keys.value
      type = "string"
    }
  }

}
