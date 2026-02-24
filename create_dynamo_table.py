import os

import boto3

dynamodb = boto3.client(
    "dynamodb",
    region_name=os.getenv("AWS_REGION"),
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
)

TABLE_NAME = "SystemDesignProgress"

try:
    table = dynamodb.create_table(
        TableName=TABLE_NAME,
        KeySchema=[
            {
                "AttributeName": "user_id",
                "KeyType": "HASH",
            }
        ],
        AttributeDefinitions=[
            {
                "AttributeName": "user_id",
                "AttributeType": "S",
            }
        ],
        BillingMode="PAY_PER_REQUEST",
    )

    print(f"Creating table {TABLE_NAME}...")
    dynamodb.get_waiter("table_exists").wait(TableName=TABLE_NAME)
    print(f"Table {TABLE_NAME} created successfully.")
except dynamodb.exceptions.ResourceInUseException:
    print(f"Table {TABLE_NAME} already exists.")
except Exception as e:
    print(f"Error creating table {TABLE_NAME}: {e}")