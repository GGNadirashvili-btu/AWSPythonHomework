import argparse
import os
import boto3
from s3_ops import list_buckets, upload_file, download_file, delete_object


def get_s3_client():
    access_key = os.getenv('AWS_ACCESS_KEY_ID')
    secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
    session_token = os.getenv('AWS_SESSION_TOKEN')
    region = os.getenv('AWS_REGION')

    return boto3.client(
        's3',
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        aws_session_token=session_token,
        region_name=region
    )


def parse_args():
    parser = argparse.ArgumentParser(description='Simple S3 CLI Tool')
    subparsers = parser.add_subparsers(dest='command', required=True)

    subparsers.add_parser('list-buckets', help='List all S3 buckets')

    up = subparsers.add_parser('upload', help='Upload a file to S3')
    up.add_argument('--bucket', required=True, help='Name of the target bucket')
    up.add_argument('--file',   required=True, help='Local file path to upload')
    up.add_argument('--key',    required=True, help='Destination S3 key')

    down = subparsers.add_parser('download', help='Download a file from S3')
    down.add_argument('--bucket', required=True, help='Name of the source bucket')
    down.add_argument('--key',    required=True, help='Source S3 key')
    down.add_argument('--file',   required=True, help='Local file path to save to')

    rem = subparsers.add_parser('delete', help='Delete an object from S3')
    rem.add_argument('--bucket', required=True, help='Bucket name')
    rem.add_argument('--key',    required=True, help='S3 key to delete')

    return parser.parse_args()

def main():
    args = parse_args()
    s3 = get_s3_client()

    if args.command == 'list-buckets':
        for name in list_buckets(s3):
            print(name)

    elif args.command == 'upload':
        upload_file(s3, args.bucket, args.file, args.key)
        print(f"Uploaded {args.file} to s3://{args.bucket}/{args.key}")

    elif args.command == 'download':
        download_file(s3, args.bucket, args.key, args.file)
        print(f"Downloaded s3://{args.bucket}/{args.key} to {args.file}")

    elif args.command == 'delete':
        delete_object(s3, args.bucket, args.key)
        print(f"Deleted s3://{args.bucket}/{args.key}")


if __name__ == '__main__':
    main()