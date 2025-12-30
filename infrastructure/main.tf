# Terraform Production Deployment Template (AWS)
# This file provides a blueprint for deploying the Kyotei AI Suite to the cloud.

provider "aws" {
  region = "ap-northeast-1" # Tokyo
}

# 1. VPC for secure networking
resource "aws_vpc" "main" {
  cidr_block = "10.0.0.0/16"
  enable_dns_hostnames = true
  tags = { Name = "Kyotei-AI-VPC" }
}

# 2. EC2 Instance for API & Worker
resource "aws_instance" "app_server" {
  ami           = "ami-0d52744d609124477" # Amazon Linux 2 (example)
  instance_type = "t3.large"
  
  vpc_security_group_ids = [aws_security_group.app_sg.id]
  key_name               = "kyotei-key"

  tags = { Name = "Kyotei-AI-App" }
}

# 3. Security Group
resource "aws_security_group" "app_sg" {
  name        = "kyotei-app-sg"
  vpc_id      = aws_vpc.main.id

  # API
  ingress {
    from_port   = 8000
    to_port     = 8001
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # SSH
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["YOUR_IP/32"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# 4. Redis (ElastiCache) for caching
resource "aws_elasticache_cluster" "redis" {
  cluster_id           = "kyotei-cache"
  engine               = "redis"
  node_type            = "cache.t3.micro"
  num_cache_nodes      = 1
  parameter_group_name = "default.redis6.x"
  port                 = 6379
}

output "app_public_ip" {
  value = aws_instance.app_server.public_ip
}
