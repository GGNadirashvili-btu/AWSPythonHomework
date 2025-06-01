import boto3
import argparse
import requests
import os

def get_my_ip():
    return requests.get('https://checkip.amazonaws.com').text.strip()

def create_security_group(ec2, vpc_id, ip_address):
    sg = ec2.create_security_group(
        GroupName='web-ssh-access',
        Description='Allow HTTP and SSH access',
        VpcId=vpc_id
    )
    sg_id = sg.id

    sg.authorize_ingress(
        IpPermissions=[
            {
                'IpProtocol': 'tcp',
                'FromPort': 80,
                'ToPort': 80,
                'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
            },
            {
                'IpProtocol': 'tcp',
                'FromPort': 22,
                'ToPort': 22,
                'IpRanges': [{'CidrIp': f'{ip_address}/32'}]
            }
        ]
    )
    print(f"Created Security Group with ID: {sg_id}")
    return sg_id

def create_key_pair(ec2_client, key_name):
    key_pair = ec2_client.create_key_pair(KeyName=key_name)
    private_key = key_pair['KeyMaterial']
    filename = f"{key_name}.pem"
    with open(filename, 'w') as f:
        f.write(private_key)
    os.chmod(filename, 0o400)
    print(f"Key pair saved as {filename}")
    return key_name

def launch_instance(ec2_resource, ami_id, instance_type, key_name, sg_id, subnet_id):
    instances = ec2_resource.create_instances(
        ImageId=ami_id,
        InstanceType=instance_type,
        KeyName=key_name,
        MaxCount=1,
        MinCount=1,
        NetworkInterfaces=[{
            'SubnetId': subnet_id,
            'DeviceIndex': 0,
            'AssociatePublicIpAddress': True,
            'Groups': [sg_id]
        }],
        BlockDeviceMappings=[{
            'DeviceName': '/dev/xvda',
            'Ebs': {
                'VolumeSize': 10,
                'VolumeType': 'gp2',
                'DeleteOnTermination': True
            }
        }]
    )
    instance = instances[0]
    print(f"Launched instance with ID: {instance.id}")
    return instance.id

def main():
    parser = argparse.ArgumentParser(description="Create EC2 instance with security group and key pair")
    parser.add_argument('--vpc-id', required=True, help='VPC ID')
    parser.add_argument('--subnet-id', required=True, help='Subnet ID')
    parser.add_argument('--ami-id', required=True, help='AMI ID (e.g. ami-1234567890abcdef0)')
    parser.add_argument('--region', default='us-east-1', help='AWS Region (default: us-east-1)')
    parser.add_argument('--key-name', default='my-key-pair', help='Name of the EC2 Key Pair to create')
    args = parser.parse_args()

    ec2 = boto3.resource('ec2', region_name=args.region)
    ec2_client = boto3.client('ec2', region_name=args.region)

    my_ip = get_my_ip()
    sg_id = create_security_group(ec2, args.vpc_id, my_ip)
    create_key_pair(ec2_client, args.key_name)
    instance_id = launch_instance(
        ec2, 
        ami_id=args.ami_id,
        instance_type='t2.micro',
        key_name=args.key_name,
        sg_id=sg_id,
        subnet_id=args.subnet_id
    )
    print(f"EC2 instance {instance_id} launched successfully.")

if __name__ == '__main__':
    main()
