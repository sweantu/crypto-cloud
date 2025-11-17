variable "project_prefix" { type = string }
variable "environment" { type = string }
variable "project" { type = string }
# variable "clickhouse_public_ip" { type = string }

variable "flink_scripts_bucket_name" {
  type    = string
  default = "flink-scripts"
}

variable "job_key" {
  type    = string
  default = "managed-flink-pyflink-getting-started-1.0.0-v3.zip"
}


# -------------------------
# S3 bucket for job scripts
# -------------------------
resource "aws_s3_bucket" "flink_scripts" {
  bucket        = "${var.project_prefix}-${var.flink_scripts_bucket_name}"
  force_destroy = true
  tags = {
    Project     = var.project
    Environment = var.environment
  }
}


# -------------------------
# Flink IAM role
# -------------------------
resource "aws_iam_role" "flink_role" {
  name = "${var.project_prefix}-flink-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Effect    = "Allow",
      Principal = { Service = "kinesisanalytics.amazonaws.com" },
      Action    = "sts:AssumeRole"
    }]
  })
}


# -------------------------
# Flink IAM Role Policy
# -------------------------
resource "aws_iam_role_policy" "flink_policy" {
  name = "${var.project_prefix}-flink-policy"
  role = aws_iam_role.flink_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow",
        Action = [
          "s3:*",
          "logs:*",
          "glue:*",
          "kinesis:*"
        ],
        Resource = "*"
      }
    ]
  })
}

resource "aws_cloudwatch_log_group" "flink_log_group" {
  name              = "/aws/kinesis-analytics/${var.project_prefix}-flink-app"
  retention_in_days = 14
}

resource "aws_cloudwatch_log_stream" "flink_log_stream" {
  name           = "application-logs"
  log_group_name = aws_cloudwatch_log_group.flink_log_group.name
}



# -------------------------
# Kinesis Data Analytics v2 App (Managed Apache Flink)
# -------------------------
resource "aws_kinesisanalyticsv2_application" "flink_app" {
  name                   = "${var.project_prefix}-flink-app"
  runtime_environment    = "FLINK-1_20"
  service_execution_role = aws_iam_role.flink_role.arn

  application_configuration {

    # --- Code Configuration ---
    application_code_configuration {
      code_content {
        s3_content_location {
          bucket_arn = aws_s3_bucket.flink_scripts.arn
          file_key   = var.job_key
        }
      }
      code_content_type = "ZIPFILE"
    }

    # --- Flink Parallelism Config ---
    flink_application_configuration {
      parallelism_configuration {
        configuration_type   = "CUSTOM"
        parallelism          = 1
        parallelism_per_kpu  = 1
        auto_scaling_enabled = false
      }
    }

    # --- Runtime Environment Properties ---
    environment_properties {

      # Runtime Options (Python entrypoint)
      property_group {
        property_group_id = "kinesis.analytics.flink.run.options"
        property_map = {
          "python"  = "main.py"
          "jarfile" = "lib/pyflink-dependencies.jar"
        }
      }

      # Input Stream Configuration
      property_group {
        property_group_id = "InputStream0"
        property_map = {
          "stream.arn"                 = "arn:aws:kinesis:ap-southeast-1:650251698703:stream/ExampleInputStream"
          "aws.region"                 = "ap-southeast-1"
          "flink.source.init.position" = "LATEST"
        }
      }

      # Output Stream Configuration
      property_group {
        property_group_id = "OutputStream0"
        property_map = {
          "stream.arn" = "arn:aws:kinesis:ap-southeast-1:650251698703:stream/ExampleOutputStream"
          "aws.region" = "ap-southeast-1"
          # "clickhouse.ip" = var.clickhouse_public_ip
        }
      }
    }

  }

  # --- CloudWatch Logging ---
  cloudwatch_logging_options {
    log_stream_arn = aws_cloudwatch_log_stream.flink_log_stream.arn
  }

}

resource "aws_kinesisanalyticsv2_application" "flink_app_iceberg" {
  name                   = "${var.project_prefix}-flink-app-iceberg"
  runtime_environment    = "FLINK-1_20"
  service_execution_role = aws_iam_role.flink_role.arn

  application_configuration {

    # -------------------------------------------------------
    # Code (ZIP/JAR) Configuration
    # -------------------------------------------------------
    application_code_configuration {
      code_content {
        s3_content_location {
          bucket_arn = aws_s3_bucket.flink_scripts.arn
          file_key   = "managed-flink-pyfink-iceberg-sink-example-1.0.0.zip"
        }
      }
      code_content_type = "ZIPFILE"
    }

    # -------------------------------------------------------
    # Flink Parallelism
    # -------------------------------------------------------
    flink_application_configuration {
      parallelism_configuration {
        configuration_type   = "CUSTOM"
        parallelism          = 1
        parallelism_per_kpu  = 1
        auto_scaling_enabled = false
      }
    }

    # -------------------------------------------------------
    # Runtime Properties (Application Properties JSON)
    # -------------------------------------------------------
    environment_properties {

      # Runtime Options (Python Entrypoint)
      property_group {
        property_group_id = "kinesis.analytics.flink.run.options"
        property_map = {
          "python"  = "main.py"
          "jarfile" = "lib/pyflink-dependencies.jar"
        }
      }

      # Iceberg Catalog Table Properties
      property_group {
        property_group_id = "IcebergTable0"
        property_map = {
          "catalog.name"   = "glue_catalog"
          "warehouse.path" = "s3a://crypto-cloud-dev-650251698703-data-lake-bucket/"
          "database.name"  = "my_database"
          "table.name"     = "my_table_v2"
          "aws.region"     = "ap-southeast-1"
        }
      }
    }
  }

  # -------------------------------------------------------
  # CloudWatch Logging
  # -------------------------------------------------------
  cloudwatch_logging_options {
    log_stream_arn = aws_cloudwatch_log_stream.flink_log_stream.arn
  }
}
