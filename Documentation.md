Project Documentation


PART 1 — IAM Roles

    • Role 1 — Lambda Role

IAM → Roles → Create role
    •  Trusted entity type: AWS Service
    • Service: Lambda
    • Click Next
    •  Skip adding managed policies for now → click Next
    • Role name: lambda-pipeline-execution-role
    • Create role

Now add permissions — search for your new role and click it:

→ Permissions tab → Add permissions → Create inline policy
→ Click JSON tab → paste this:

{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "glue:StartCrawler",
        "glue:GetCrawler",
        "glue:StartJobRun",
        "glue:GetJobRun"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::e-commerce-data-kpc",
        "arn:aws:s3:::e-commerce-data-kpc/*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "*"
    }
  ]
}

→ Click Next
→ Policy name: lambda-pipeline-policy
→ Create policy


Role 2 — Glue Role

IAM → Roles → Create role
    • → Trusted entity type: AWS Service
    • → Service: Glue
    • → Click Next
    • → Search "AWSGlueServiceRole" → check it → Next
    • → Role name: glue-pipeline-service-role
      
One Role — Two Policies Inside It
glue-pipeline-service-role
    ├── AWSGlueServiceRole    ← managed policy (attached during role creation)
    └── glue-s3-access            ← inline policy (you add this after)
→ Create role

→ Permissions tab → Add permissions → Create inline policy
→ JSON tab → paste this:

{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::e-commerce-data-kpc",
        "arn:aws:s3:::e-commerce-data-kpc/*"
      ]
    }
  ]
}


    • Policy name: glue-s3-access
    • Create policy


PART 2 — S3 Folders

S3 → e-commerce-data-kpc → Create folder


Create these 4 folders one by one:

| Folder name |
------------------------
| raw |
| etl_processed_data |
| athena-results |
| glue-scripts |

Then upload `orders.json` into the `raw/` folder and upload `etl_ecommerce.py` script into `glue-scripts/` folder.


PART 3 — Glue Setup

Create Database

Glue → Databases → Add database
→ Name: ecommerce_db
→ Create

Create Crawler

Glue → Crawlers → Create crawler
→ Name: ecommerce-crawler
→ Next
→ Add data source → S3
→ S3 path: s3://e-commerce-data-kpc/raw/
→ Add → Next
→ IAM Role: glue-pipeline-service-role
→ Next
→ Target database: ecommerce_db
→ Next → Create crawler






Create ETL Job

Glue → ETL Jobs → Script editor
    • Engine: Spark
    • Start fresh
    • Job name: etl_ecommerce
    • IAM Role: glue-pipeline-service-role
    • Glue version: Glue 4.0
    • Worker type: G.1X
    • Number of workers: 2


Paste the ETL script in the editor and click Save


PART 4 — Lambda Functions

Lambda 1 — s3-crawler-trigger

Lambda → Create function
    • Function name: s3-crawler-trigger
    • Runtime: Python 3.12
    • Permissions → Use existing role → lambda-pipeline-execution-role
    • Create function



Paste code → click Deploy:

import boto3

CRAWLER_NAME = 'ecommerce-crawler'

def lambda_handler(event, context):
    glue = boto3.client('glue')
    
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = event['Records'][0]['s3']['object']['key']
    print(f"File uploaded: s3://{bucket}/{key}")
    
    response = glue.get_crawler(Name=CRAWLER_NAME)
    state = response['Crawler']['State']
    print(f"Crawler state: {state}")
    
    if state == 'RUNNING':
        print("Crawler already running — skipping")
        return {"status": "skipped"}
    
    glue.start_crawler(Name=CRAWLER_NAME)
    print(f"Crawler started!")
    
    return {"status": "success"}

Set timeout:

Configuration → General configuration → Edit
→ Timeout: 1 min 0 sec → Save


Lambda 2 — etl-job-trigger

Lambda → Create function
    • → Function name: etl-job-trigger
    • → Runtime: Python 3.12
    • → Permissions → Use existing role → lambda-pipeline-execution-role
    • → Create function

Paste code → click Deploy:

import boto3

ETL_JOB_NAME = 'etl_ecommerce'

def lambda_handler(event, context):
    glue = boto3.client('glue')
    
    print(f"Event received: {event}")
    
    state = event['detail']['state']
    crawler_name = event['detail']['crawlerName']
    print(f"Crawler: {crawler_name} | State: {state}")
    
    if state != 'Succeeded':
        print(f"Crawler state was {state} — ETL not triggered")
        return {"status": "skipped"}
    
    response = glue.start_job_run(JobName=ETL_JOB_NAME)
    print(f"ETL job started! RunId: {response['JobRunId']}")
    
    return {"status": "success", "jobRunId": response['JobRunId']}


Set timeout:

Configuration → General configuration → Edit
→ Timeout: 1 min 0 sec → Save




PART 5 — S3 Event Notification

S3 → e-commerce-data-kpc → Properties
→ Event notifications → Create event notification

| Field | Value |
---------------------------------------------------
| Event name | json-upload-trigger |
| Prefix | raw/ |
| Suffix | .json |
| Event types | All object create events |
| Destination | Lambda function |
| Lambda function | `s3-crawler-trigger` |

→ Save changes

This automatically adds the S3 permission to invoke Lambda 1 

PART 6 — EventBridge Rule

EventBridge → Rules → Create rule
→ Name: on-crawler-complete
→ Event bus: default
→ Rule type: Rule with an event pattern
→ Next


In event pattern section:

→ Event source: AWS services
→ AWS service: Glue
→ Event type: Glue Crawler State Change
→ Switch to "Edit pattern" and paste:


{
  "source": ["aws.glue"],
  "detail-type": ["Glue Crawler State Change"],
  "detail": {
    "crawlerName": ["ecommerce-crawler"],
    "state": ["Succeeded"]
  }
}

→ Next
→ Target type: AWS service
→ Select a target: Lambda function
→ Function: etl-job-trigger
→ Next → Next → Create rule

This automatically adds the EventBridge permission to invoke Lambda 2 

PART 7 — Athena Setup

Athena → Settings → Manage
→ Query result location: s3://e-commerce-data-kpc/athena-results/
→ Save


Final Checklist

IAM: lambda-pipeline-execution-role created with inline policy
IAM: glue-pipeline-service-role created with AWSGlueServiceRole + inline policy
S3: folders created (raw, etl_processed_data, athena-results, glue-scripts)
S3: ETL script uploaded to glue-scripts/
Glue: ecommerce_db database created
Glue: ecommerce-crawler created → points to raw/
Glue: etl_ecommerce job created with script
Lambda 1: s3-crawler-trigger deployed with 1 min timeout
Lambda 2: etl-job-trigger deployed with 1 min timeout
S3 Event Notification → s3-crawler-trigger (auto-adds permission)
EventBridge Rule → etl-job-trigger (auto-adds permission)
Athena: result location set

