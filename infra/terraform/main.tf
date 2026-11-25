terraform {
  required_version = ">= 1.5.0"
  required_providers {
    local = {
      source  = "hashicorp/local"
      version = "~> 2.5"
    }
    null = {
      source  = "hashicorp/null"
      version = "~> 3.2"
    }
  }
}

variable "environment" {
  type    = string
  default = "production"
}

variable "namespace" {
  type    = string
  default = "capstone-abhinav"
}

variable "app_version" {
  type    = string
  default = "1.0.0"
}

resource "local_file" "runtime_env" {
  filename = "${path.module}/generated/runtime.env"
  content  = <<-EOT
    APP_NAME=cloudledger
    ENVIRONMENT=${var.environment}
    K8S_NAMESPACE=${var.namespace}
    APP_VERSION=${var.app_version}
    PROMETHEUS_SCRAPE=true
    LOG_FORMAT=json
  EOT
}

resource "local_file" "slo_policy" {
  filename = "${path.module}/generated/slo-policy.json"
  content  = jsonencode({
    service              = "CloudLedger"
    availability_target  = 0.999
    max_error_rate       = 0.05
    p95_latency_ms       = 250
    rto_seconds_target   = 30
    rpo_records_target   = 0
  })
}

resource "null_resource" "provision_docker_network" {
  triggers = {
    net_name = "cloudledger-net"
  }
  provisioner "local-exec" {
    command = "docker network inspect cloudledger-net >/dev/null 2>&1 || docker network create cloudledger-net"
  }
}

output "runtime_env_file" {
  value = local_file.runtime_env.filename
}

output "slo_policy_file" {
  value = local_file.slo_policy.filename
}

output "docker_network" {
  value = "cloudledger-net"
}
