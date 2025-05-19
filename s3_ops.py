def list_buckets(s3_client):
    """Return a list of bucket names."""
    resp = s3_client.list_buckets()
    return [b['Name'] for b in resp.get('Buckets', [])]


def upload_file(s3_client, bucket, file_path, key):
    """Upload a local file to S3."""
    s3_client.upload_file(file_path, bucket, key)


def download_file(s3_client, bucket, key, file_path):
    """Download an S3 object to a local file."""
    s3_client.download_file(bucket, key, file_path)


def delete_object(s3_client, bucket, key):
    """Delete an object from S3."""
    s3_client.delete_object(Bucket=bucket, Key=key)