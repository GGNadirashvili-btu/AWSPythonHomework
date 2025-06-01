# AWSPythonHomework

This repository contains Python scripts that automate AWS infrastructure tasks using the `boto3` SDK. It is designed for educational and practical use in setting up cloud resources such as VPCs, subnets, security groups, and EC2 instances via CLI.

## Contents

- `main.py` – Automates the creation of VPC components like subnets, route tables, internet gateways, etc.
- `create_ec2_instance.py` – CLI tool for launching an EC2 instance inside a specified VPC and subnet, with automatic key pair and security group creation.
- Additional helper files may be included for modular support.

## Features

### VPC & Network Setup (`main.py`)

- Creates a Virtual Private Cloud (VPC)
- Creates public and private subnets
- Attaches an Internet Gateway
- Configures route tables
- Associates route tables with subnets
- Tags resources for easier management

### EC2 Instance Provisioning (`create_ec2_instance.py`)

- Accepts VPC ID and Subnet ID via CLI arguments
- Creates a security group with:
  - HTTP access from all IPs (0.0.0.0/0)
  - SSH access restricted to the current machine’s public IP
- Generates an EC2 Key Pair and saves the `.pem` file locally
- Launches a `t2.micro` EC2 instance with:
  - AMI ID of your choice
  - 10 GB `gp2` EBS volume
  - Public IP association

## Requirements

- Python 3.7+
- AWS account with appropriate IAM permissions
- AWS credentials configured locally (`~/.aws/credentials` or environment variables)
- Packages:
  - `boto3`
  - `requests`

Install dependencies:

```bash
pip install boto3 requests
