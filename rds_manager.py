import boto3

def create_rds_instance(db_identifier, db_username, db_password, security_group_id):
    rds = boto3.client('rds')
    print("Creating RDS instance...")

    response = rds.create_db_instance(
        DBInstanceIdentifier=db_identifier,
        MasterUsername=db_username,
        MasterUserPassword=db_password,
        DBInstanceClass='db.r6i.2xlarge',  # 64 GB RAM
        AllocatedStorage=100,
        Engine='mysql',
        VpcSecurityGroupIds=[security_group_id],
        Port=3306,
        BackupRetentionPeriod=1,
        MultiAZ=False,
        PubliclyAccessible=True
    )

    print("Waiting for RDS to become available...")
    waiter = rds.get_waiter('db_instance_available')
    waiter.wait(DBInstanceIdentifier=db_identifier)

    response = rds.describe_db_instances(DBInstanceIdentifier=db_identifier)
    endpoint = response['DBInstances'][0]['Endpoint']['Address']
    print(f"Database endpoint: {endpoint}")
    return endpoint

def open_db_port_all_ips(security_group_id):
    ec2 = boto3.client('ec2')
    print("Authorizing inbound traffic to port 3306 from 0.0.0.0/0...")
    ec2.authorize_security_group_ingress(
        GroupId=security_group_id,
        IpPermissions=[
            {
                'IpProtocol': 'tcp',
                'FromPort': 3306,
                'ToPort': 3306,
                'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
            }
        ]
    )
    print("Ingress rule added.")
