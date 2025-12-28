variable "vpc_cidr" { type = string }
variable "azs" { type = list(string) }
variable "vpc_name" { type = string }
variable "igw_name" { type = string }
variable "public_subnet_names" { type = map(string) }
variable "public_route_table_name" { type = string }
