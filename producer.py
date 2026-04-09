
import boto3
import json
import time
from datetime import datetime
import random
from config_reader import read_config

config = read_config("config/config.json")

input_aws_region = config["input"]["AWS_REGION"]
input_stream_name = config["input"]["STREAM_NAME"]
input_bucket_name = config["input"]["BUCKET_NAME" ]

# AWS Configuration
# AWS_REGION = 'us-east-1'  # Change to your preferred region
# STREAM_NAME = 'kinesis-demo'  # Your Kinesis stream name
# BUCKET_NAME = 'e-commerce-data-kpc' #BUCKET NAME

# Initialize Kinesis client
kinesis_client = boto3.client('kinesis', region_name=input_aws_region)
s3 = boto3.client('s3', region_name=input_aws_region)


def generate_sample_data():
    
    data = {
        'timestamp': datetime.utcnow().isoformat(),
        'user_id': f'user_{random.randint(1000, 9999)}',
        'event_type': random.choice(['login', 'purchase', 'view', 'logout']),
        'value': round(random.uniform(10, 1000), 2),
        'metadata': {
            'source': 'python_app',
            'version': '1.0'
        }
    }
    return data


def send_to_kinesis(data):
    
    try:
        # Convert data to JSON string
        json_data = json.dumps(data)
        
        # Use user_id as partition key for even distribution
        # Partition key determines which shard the record goes to
        partition_key = data.get('user_id', 'default')
        
        # Put record to Kinesis
        response = kinesis_client.put_record(
            StreamName=input_stream_name,
            Data=json_data,
            PartitionKey=partition_key
        )
        
        print(f"Record sent successfully!")
        print(f"Shard ID: {response['ShardId']}")
        print(f"Sequence Number: {response['SequenceNumber']}")
        print(f"Data: {json_data}")
        
        return response
        
    except Exception as e:
        print(f"Error sending record: {str(e)}")
        raise


def send_batch_to_kinesis(records):
   
    try:
        # Prepare records for batch
        kinesis_records = []
        for record in records:
            kinesis_records.append({
                'Data': json.dumps(record),
                'PartitionKey': record.get('user_id', 'default')
            })
        
        # Send batch
        response = kinesis_client.put_records(
            StreamName=input_stream_name,
            Records=kinesis_records
        )
        
        # Check for failures
        failed_count = response['FailedRecordCount']
        if failed_count > 0:
            print(f"{failed_count} records failed to send")
        else:
            print(f"All {len(records)} records sent successfully!")
        
        return response
        
    except Exception as e:
        print(f"Error sending batch: {str(e)}")
        raise


def main():
    
    print("Kinesis Data Stream Producer")
    
    # Send single records
    print("\n--- Sending Single Records ---")
    for i in range(3):
        print(f"Sending record {i+1}")
        data = generate_sample_data()
        send_to_kinesis(data)
        time.sleep(1)  
    
    # Send batch of records (more efficient)
    # print("\n--- Sending Batch of Records ---")
    # batch_records = [generate_sample_data() for _ in range(5)]
    # send_batch_to_kinesis(batch_records)
    # print("Done! Check your Lambda function and S3 bucket for results.")

# Custom data example - uncomment and modify for your use case
# def send_custom_data():
#     my_data = {
#         'timestamp': datetime.utcnow().isoformat(),
#         # Add your custom fields here
#         'custom_field_1': 'value1',
#         'custom_field_2': 123,
#         'custom_field_3': ['item1', 'item2']
#     }
    
    # send_to_kinesis(data)

if __name__ == '__main__':
    main()
    