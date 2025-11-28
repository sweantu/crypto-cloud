resource "aws_efs_file_system" "grafana_fs" {
  creation_token = "grafana-efs"
}

resource "aws_efs_mount_target" "grafana_mt" {
  file_system_id  = aws_efs_file_system.grafana_fs.id
  subnet_id       = var.public_subnet_ids[0]
  security_groups = [aws_security_group.grafana_efs_sg.id]
}

resource "aws_efs_access_point" "grafana_ap" {
  file_system_id = aws_efs_file_system.grafana_fs.id

  posix_user {
    uid = 472
    gid = 472
  }

  root_directory {
    path = "/grafana"
    creation_info {
      owner_uid   = 472
      owner_gid   = 472
      permissions = "755"
    }
  }
}
