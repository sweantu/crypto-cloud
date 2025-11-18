variable "region" {
  type    = string
  default = "ap-southeast-1"
}

variable "profile" {
  type    = string
  default = "default"
}

variable "project" {
  type    = string
  default = "crypto-cloud"
}

variable "environment" {
  type    = string
  default = "dev"
}

variable "vpc_cidr" {
  type    = string
  default = "10.0.0.0/16"
}

variable "az_count" {
  type    = number
  default = 2
}
