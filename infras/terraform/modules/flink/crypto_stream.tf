resource "aws_cloudwatch_log_stream" "crypto_stream_log_stream" {
  name           = "crypto-stream-logs"
  log_group_name = aws_cloudwatch_log_group.flink_logs.name
}

resource "aws_kinesisanalyticsv2_application" "crypto_stream" {
  name                   = "${var.project_prefix}-crypto-stream"
  runtime_environment    = "FLINK-1_20"
  service_execution_role = aws_iam_role.flink_role.arn

  application_configuration {
    application_code_configuration {
      code_content {
        s3_content_location {
          bucket_arn = var.scripts_bucket_arn
          file_key   = "flink_scripts/crypto_stream.zip"
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
          "pyFiles" = "lib/crypto_stream_libs.zip"
        }
      }

      property_group {

        property_group_id = "clickhouse_klines_sink"
        property_map = {
          "url"           = var.clickhouse_info.url
          "database-name" = var.clickhouse_info.database
          "table-name"    = "klines"
          "username"      = var.clickhouse_info.username
          "password"      = var.clickhouse_info.password
        }

      }

      property_group {
        property_group_id = "clickhouse_indicators_sink"
        property_map = {
          "url"           = var.clickhouse_info.url
          "database-name" = var.clickhouse_info.database
          "table-name"    = "indicators"
          "username"      = var.clickhouse_info.username
          "password"      = var.clickhouse_info.password
        }
      }

      property_group {
        property_group_id = "stream_aggtrades_source"
        property_map = {
          "stream.arn"           = var.stream_info_map["aggtrades-stream"].arn
          "aws.region"           = var.region
          "source.init.position" = "TRIM_HORIZON"
        }
      }

      property_group {
        property_group_id = "stream_indicators_sink"
        property_map = {
          "stream.arn" = var.stream_info_map["indicators-stream"].arn
          "aws.region" = var.region
        }
      }
    }
  }
  cloudwatch_logging_options {
    log_stream_arn = aws_cloudwatch_log_stream.crypto_stream_log_stream.arn
  }

}
