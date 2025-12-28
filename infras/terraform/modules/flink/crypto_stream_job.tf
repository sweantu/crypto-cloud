resource "aws_cloudwatch_log_stream" "crypto_stream_log_stream" {
  name           = "crypto-stream-job-logs"
  log_group_name = aws_cloudwatch_log_group.flink_logs.name
}

resource "aws_kinesisanalyticsv2_application" "crypto_stream_job" {
  name                   = "${var.project_prefix}-crypto-stream-job"
  runtime_environment    = "FLINK-1_20"
  service_execution_role = aws_iam_role.flink_role.arn

  application_configuration {
    application_code_configuration {
      code_content {
        s3_content_location {
          bucket_arn = var.scripts_bucket_arn
          file_key   = "crypto_stream/target/crypto-stream-1.0.0.zip"
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
        property_group_id = "InputStream0"
        property_map = {
          "stream.arn"                 = var.stream_arns["ExampleInputStream"]
          "aws.region"                 = var.region
          "flink.source.init.position" = "TRIM_HORIZON"
        }
      }

      property_group {
        property_group_id = "OutputStream0"
        property_map = {
          "stream.arn"    = var.stream_arns["ExampleOutputStream"]
          "aws.region"    = var.region
          "clickhouse.ip" = "54.179.214.203"
        }
      }
    }

  }

  cloudwatch_logging_options {
    log_stream_arn = aws_cloudwatch_log_stream.crypto_stream_log_stream.arn
  }

}
