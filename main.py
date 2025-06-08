#!/usr/bin/env python3
"""
CLI tool to create a VPC with N public and N private subnets automatically.
Limits total subnets to AWS default of 200 (so N ≤ 100).
"""
import argparse
import sys
import math
import ipaddress
import boto3
from rds_manager import create_rds_instance, open_db_port_all_ips
from tasks.network import (
    validate_cidr,
    create_vpc,
    tag_resource,
    enable_dns_hostnames,
    create_igw,
    attach_igw,
    create_route_table,
    create_route,
    create_subnet,
)

def parse_args():
    parser = argparse.ArgumentParser(
        description="Create a VPC with N public and private subnets"
    )
    parser.add_argument(
        '--region', required=True,
        help='AWS region (e.g., us-east-1)'
    )
    parser.add_argument(
        '--vpc-cidr', required=True, type=validate_cidr,
        help='CIDR block for the VPC (e.g., 10.0.0.0/16)'
    )
    parser.add_argument(
        '--vpc-name', required=True,
        help='Name tag for the VPC'
    )
    parser.add_argument(
        '-n', '--subnet-count', required=True, type=int,
        help='Number of public and private subnets each (total 2×N, max 200)'
    )
    return parser.parse_args()


def main():
    parser = argparse.ArgumentParser(description="AWS CLI Tool")
    parser.add_argument('--create-rds', action='store_true', help='Create RDS instance')
    parser.add_argument('--db-identifier', type=str)
    parser.add_argument('--db-username', type=str)
    parser.add_argument('--db-password', type=str)
    parser.add_argument('--security-group-id', type=str)

    args = parser.parse_args()

    if args.create_rds:
        if not all([args.db_identifier, args.db_username, args.db_password, args.security_group_id]):
            print("Missing required arguments.")
            return
        open_db_port_all_ips(args.security_group_id)
        endpoint = create_rds_instance(
            args.db_identifier,
            args.db_username,
            args.db_password,
            args.security_group_id
        )
        print(f"\n✅ Connect to your DB at: {endpoint}")
    
    # ------------------
    args = parse_args()
    total_subnets = args.subnet_count * 2
    if total_subnets > 200:
        print(f"Error: total subnets (2×{args.subnet_count}={total_subnets}) exceeds AWS default limit of 200", file=sys.stderr)
        sys.exit(1)

    # Calculate new prefix length to split VPC into total_subnets
    vpc_network = ipaddress.ip_network(args.vpc_cidr)
    bits_needed = math.ceil(math.log2(total_subnets))
    new_prefix = vpc_network.prefixlen + bits_needed
    if new_prefix > vpc_network.max_prefixlen:
        print("Error: cannot carve out that many subnets from given VPC CIDR", file=sys.stderr)
        sys.exit(1)

    # Generate subnets
    subnets = list(vpc_network.subnets(new_prefix=new_prefix))
    public_cidrs = [str(net) for net in subnets[:args.subnet_count]]
    private_cidrs = [str(net) for net in subnets[args.subnet_count:total_subnets]]

    ec2 = boto3.client('ec2', region_name=args.region)

    # Create VPC
    print("Creating VPC...")
    vpc_id = create_vpc(ec2, args.vpc_cidr)
    tag_resource(ec2, vpc_id, [{'Key': 'Name', 'Value': args.vpc_name}])
    enable_dns_hostnames(ec2, vpc_id)
    print(f"-> VPC created: {vpc_id}")

    # Internet Gateway
    print("Creating Internet Gateway...")
    igw_id = create_igw(ec2)
    attach_igw(ec2, igw_id, vpc_id)
    print(f"-> IGW created and attached: {igw_id}")

    # Public subnets
    print("Setting up public route table and subnets...")
    public_rt = create_route_table(ec2, vpc_id)
    create_route(ec2, public_rt, '0.0.0.0/0', igw_id)
    for cidr in public_cidrs:
        sid = create_subnet(ec2, vpc_id, cidr)
        tag_resource(ec2, sid, [{'Key': 'Name', 'Value': f"{args.vpc_name}-public-{cidr}"}])
        ec2.associate_route_table(SubnetId=sid, RouteTableId=public_rt)
        print(f"-> Public subnet created: {sid} ({cidr})")

    # Private subnets
    print("Setting up private route table and subnets...")
    private_rt = create_route_table(ec2, vpc_id)
    for cidr in private_cidrs:
        sid = create_subnet(ec2, vpc_id, cidr)
        tag_resource(ec2, sid, [{'Key': 'Name', 'Value': f"{args.vpc_name}-private-{cidr}"}])
        ec2.associate_route_table(SubnetId=sid, RouteTableId=private_rt)
        print(f"-> Private subnet created: {sid} ({cidr})")

    print("All resources created successfully.")


if __name__ == '__main__':
    main()
