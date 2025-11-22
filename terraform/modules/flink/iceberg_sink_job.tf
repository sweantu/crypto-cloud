resource "aws_cloudwatch_log_stream" "iceberg_sink_log_stream" {
  name           = "iceberg-sink-job-logs"
  log_group_name = aws_cloudwatch_log_group.flink_logs.name
}

resource "aws_kinesisanalyticsv2_application" "iceberg_sink_job" {
  name                   = "${var.project_prefix}-iceberg-sink-job"
  runtime_environment    = "FLINK-1_20"
  service_execution_role = aws_iam_role.flink_role.arn

  application_configuration {
    application_code_configuration {
      code_content {
        s3_content_location {
          bucket_arn = var.scripts_bucket_arn
          file_key   = "iceberg_sink/target/managed-flink-pyfink-iceberg-sink-example-1.0.0.zip"
        }
      }
      code_content_type = "ZIPFILE"
    }

    flink_application_configuration {
      parallelism_configuration {
        configuration_type   = "CUSTOM"
        parallelism          = 1
        parallelism_per_kpu  = 1
        auto_scaling_enabled = false
      }
    }

    environment_properties {
      property_group {
        property_group_id = "kinesis.analytics.flink.run.options"
        property_map = {
          "python"  = "main.py"
          "jarfile" = "lib/pyflink-dependencies.jar"
        }
      }

      property_group {
        property_group_id = "IcebergTable0"
        property_map = {
          "catalog.name"   = "glue_catalog"
          "warehouse.path" = "s3://${var.data_lake_bucket}/"
          "database.name"  = "my_database"
          "table.name"     = "my_table"
          "aws.region"     = var.region
        }
      }
    }
  }

  cloudwatch_logging_options {
    log_stream_arn = aws_cloudwatch_log_stream.iceberg_sink_log_stream.arn
  }
}
