import boto3       # AWS library for Python
import json        # for working with JSON data
import random      # for generating random sample data
import uuid        # for creating unique IDs
from datetime import datetime, timezone, timedelta   # for timestamps


BUCKET_NAME = "e-commerce-data-kpc"   # replace with your S3 bucket name
AWS_REGION  = "us-east-1"          # replace with your AWS region
SOURCE_TYPE = "s3"

def generate_sample_data(num_records=10):

    # Creates a list of fake user records.Each record is a Python dictionary (which becomes JSON)

    first_names = ["Alice", "Bob", "Charlie", "Diana", "Eve","Frank", "Grace", "Henry", "Iris", "Jack"]
    last_names  = ["Smith", "Johnson", "Williams", "Brown", "Jones","Garcia", "Miller", "Davis", "Wilson", "Moore"]
    cities      = ["New York", "Los Angeles", "Chicago", "Houston","Phoenix", "Philadelphia", "San Antonio", "San Diego"]
    state       = ["NY","IL","WA","TX","CA","MA","CO","FL"]
    hobbies     = ["reading", "gaming", "cooking", "hiking","painting", "cycling", "photography", "music"]
    status      = ["delivered","shipped","pending","cancelled"]


    records = []

    for i in range(num_records):
        record = {
            "order_id":    str(uuid.uuid4()), 
            "first_name": random.choice(first_names),
            "last_name":  random.choice(last_names),
            "age":        random.randint(18, 65),
            "city":       random.choice(cities),
            "state":      random.choice(state),
            "hobby":      random.choice(hobbies),
            "status":     random.choice(status),
            "is_active":  random.choice([True, False]),
            "amount":     random.randint(100,1000),
            "quantity":   random.randint(1,5),
            "score":      round(random.uniform(1.0, 100.0), 2),
            "date":      datetime.now(timezone.utc),
            "created_at": datetime.now(timezone.utc) 
            }
        records.append(record)
        print(f" Generated record {i + 1}: {record['first_name']} {record['last_name']}")

    return records

def convert_to_ndjson(data):
    lines = [json.dumps(record) for record in data]
    return "\n".join(lines)

def upload_to_s3(data, bucket_name, region):
    # Converts the data to JSON and uploads it to S3.The file will be saved inside a folder called 'raw/'with today's date in the filename.

    # Connect to S3
    s3 = boto3.client(SOURCE_TYPE, region_name=region)

    ndjson_data = convert_to_ndjson(data)

    # Convert Python list → JSON string
    # json_data = json.dumps(data, indent=2)

    # Create a filename using today's date and time
    today     = datetime.utcnow().strftime("%Y-%m-%d_%H-%M-%S")
    file_name = f"raw/users_{today}.json"

    print(f"\n Uploading to s3://{bucket_name}/{file_name} ...")

    # Upload to S3
    s3.put_object(
        Bucket      = bucket_name,
        Key         = file_name,       # this is the "path" inside the bucket
        Body        = ndjson_data,       # the actual content
        ContentType = "application/json"
    )

    print(f" Upload successful!")
    print(f" Location: s3://{bucket_name}/{file_name}")

    return file_name

if __name__ == "__main__":

    try:
        print("S3 Data Uploader — Sample JSON Generator")

        # --- Generate the data ---
        print("\n Generating sample user records...\n")

        sample_data = generate_sample_data(num_records=10)

        # --- Upload to S3 ---
        print("\n Uploading to S3...\n")
        uploaded_file = upload_to_s3(sample_data, BUCKET_NAME, AWS_REGION)

        # --- Done! ---
        print(f" Done! {len(sample_data)} records uploaded.")
        print(f" File: {uploaded_file}")

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()