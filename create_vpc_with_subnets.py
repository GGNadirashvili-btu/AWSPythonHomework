import argparse
import boto3
from network import (
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
        description="Create a VPC with public/private subnets and an Internet Gateway"
    )
    parser.add_argument(
        '--region', required=True,
        help='AWS region (e.g., us-east-1)'
    )
    parser.add_argument(
        '--vpc-cidr', required=True, type=validate_cidr,
        help='CIDR block for the new VPC (e.g., 10.0.0.0/16)'
    )
    parser.add_argument(
        '--vpc-name', required=True,
        help='Name tag value for the VPC'
    )
    parser.add_argument(
        '--public-subnets', required=True, nargs='+', type=validate_cidr,
        help='One or more CIDR blocks for public subnets'
    )
    parser.add_argument(
        '--private-subnets', required=True, nargs='+', type=validate_cidr,
        help='One or more CIDR blocks for private subnets'
    )
    return parser.parse_args()


def main():
    args = parse_args()
    ec2 = boto3.client('ec2', region_name=args.region)

    print("Creating VPC...")
    vpc_id = create_vpc(ec2, args.vpc_cidr)
    tag_resource(ec2, vpc_id, [{'Key': 'Name', 'Value': args.vpc_name}])
    enable_dns_hostnames(ec2, vpc_id)
    print(f"-> VPC created: {vpc_id}")

    print("Creating Internet Gateway...")
    igw_id = create_igw(ec2)
    attach_igw(ec2, igw_id, vpc_id)
    print(f"-> IGW created and attached: {igw_id}")

    print("Setting up public route table...")
    public_rt = create_route_table(ec2, vpc_id)
    create_route(ec2, public_rt, '0.0.0.0/0', igw_id)
    print("Creating public subnets...")
    for cidr in args.public_subnets:
        subnet_id = create_subnet(ec2, vpc_id, cidr)
        tag_resource(ec2, subnet_id, [{'Key': 'Name', 'Value': f"{args.vpc_name}-public-{cidr}"}])
        ec2.associate_route_table(SubnetId=subnet_id, RouteTableId=public_rt)
        print(f"-> Public subnet: {subnet_id} ({cidr})")

    print("Setting up private route table...")
    private_rt = create_route_table(ec2, vpc_id)
    print("Creating private subnets...")
    for cidr in args.private_subnets:
        subnet_id = create_subnet(ec2, vpc_id, cidr)
        tag_resource(ec2, subnet_id, [{'Key': 'Name', 'Value': f"{args.vpc_name}-private-{cidr}"}])
        ec2.associate_route_table(SubnetId=subnet_id, RouteTableId=private_rt)
        print(f"-> Private subnet: {subnet_id} ({cidr})")

    print("All resources created successfully.")

if __name__ == '__main__':
    main()
