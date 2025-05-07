resource "aws_glue_catalog_database" "glue_db_staging" {
  name = "staging"
  create_table_default_permission {
    permissions = ["SELECT"]
    principal {
      data_lake_principal_identifier = "IAM_ALLOWED_PRINCIPALS"
    }
  }
}

resource "aws_glue_catalog_table" "glue_table_openpowerlifting" {
  name          = "openpowerlifting"
  database_name = aws_glue_catalog_database.glue_db_staging.name
}
