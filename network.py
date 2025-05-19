import ipaddress
from botocore.exceptions import ClientError


def validate_cidr(value: str) -> str:
    try:
        network = ipaddress.ip_network(value)
        return str(network)
    except ValueError:
        raise ValueError(f"Invalid CIDR block: {value}")


def create_vpc(ec2_client, cidr_block: str) -> str:
    resp = ec2_client.create_vpc(CidrBlock=cidr_block)
    vpc_id = resp['Vpc']['VpcId']
    ec2_client.get_waiter('vpc_available').wait(VpcIds=[vpc_id])
    return vpc_id


def tag_resource(ec2_client, resource_id: str, tags: list) -> None:
    ec2_client.create_tags(Resources=[resource_id], Tags=tags)


def enable_dns_hostnames(ec2_client, vpc_id: str) -> None:
    ec2_client.modify_vpc_attribute(
        VpcId=vpc_id,
        EnableDnsHostnames={'Value': True}
    )


def create_igw(ec2_client) -> str:
    resp = ec2_client.create_internet_gateway()
    return resp['InternetGateway']['InternetGatewayId']


def attach_igw(ec2_client, igw_id: str, vpc_id: str) -> None:
    ec2_client.attach_internet_gateway(
        InternetGatewayId=igw_id,
        VpcId=vpc_id
    )


def create_route_table(ec2_client, vpc_id: str) -> str:
    resp = ec2_client.create_route_table(VpcId=vpc_id)
    return resp['RouteTable']['RouteTableId']


def create_route(ec2_client, route_table_id: str, destination_cidr: str, gateway_id: str) -> None:
    ec2_client.create_route(
        RouteTableId=route_table_id,
        DestinationCidrBlock=destination_cidr,
        GatewayId=gateway_id
    )


def create_subnet(ec2_client, vpc_id: str, cidr_block: str, availability_zone: str = None) -> str:
    params = {'VpcId': vpc_id, 'CidrBlock': cidr_block}
    if availability_zone:
        params['AvailabilityZone'] = availability_zone
    resp = ec2_client.create_subnet(**params)
    subnet_id = resp['Subnet']['SubnetId']
    ec2_client.get_waiter('subnet_available').wait(SubnetIds=[subnet_id])
    return subnet_id