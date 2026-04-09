# Project Documentation #


## PART 1 — IAM Roles ##

    Role 1 — Lambda Role

### IAM → Roles → Create role ###
    • Trusted entity type: AWS Service
    • Service: Lambda
    • Click Next
    • Skip adding managed policies for now → click Next
    • Role name: lambda-pipeline-execution-role
    • Create role

Now add permissions — search for your new role and click it:

#### → Permissions tab → Add permissions → Create inline policy → Click JSON tab → paste this: ####

{
  "Version": "2012-10-17",<br>
  "Statement": [<br>
    {<br>
      "Effect": "Allow",<br>
      "Action": [<br>
        "glue:StartCrawler",<br>
        "glue:GetCrawler",<br>
        "glue:StartJobRun",<br>
        "glue:GetJobRun"<br>
      ],<br>
      "Resource": "*"<br>
    },<br>
    {<br>
      "Effect": "Allow",<br>
      "Action": [<br>
        "s3:GetObject",<br>
        "s3:PutObject",<br>
        "s3:ListBucket"<br>
      ],<br>
      "Resource": [<br>
        "arn:aws:s3:::e-commerce-data-kpc",<br>
        "arn:aws:s3:::e-commerce-data-kpc/*"<br>
      ]<br>
    },<br>
    {<br>
      "Effect": "Allow",<br>
      "Action": [<br>
        "logs:CreateLogGroup",<br>
        "logs:CreateLogStream",<br>
        "logs:PutLogEvents"<br>
      ],<br>
      "Resource": "*"<br>
    }<br>
  ]<br>
}<br>

→ <b>Click Next<b><br>
→ <b>Policy name: lambda-pipeline-policy<b><br>
→ <b>Create policy<b><br>


Role 2 — Glue Role

### IAM → Roles → Create role ###

    → Trusted entity type: AWS Service
    → Service: Glue
    → Click Next
    → Search "AWSGlueServiceRole" → check it → Next
    → Role name: glue-pipeline-service-role
      
One Role — Two Policies Inside It<br>
glue-pipeline-service-role<br>

    ├── AWSGlueServiceRole    ← managed policy (attached during role creation)<br>
    └── glue-s3-access            ← inline policy (you add this after)

→ Create role

→ Permissions tab → Add permissions → Create inline policy → JSON tab → paste this:

{<br>
  "Version": "2012-10-17",<br>
  "Statement": [<br>
    {<br>
      "Effect": "Allow",<br>
      "Action": [<br>
        "s3:GetObject",<br>
        "s3:PutObject",<br>
        "s3:DeleteObject",<br>
        "s3:ListBucket"<br>
      ],<br>
      "Resource": [<br>
        "arn:aws:s3:::e-commerce-data-kpc",<br>
        "arn:aws:s3:::e-commerce-data-kpc/*"<br>
      ]<br>
    }<br>
  ]<br>
}<br>


    • Policy name: glue-s3-access
    • Create policy


## PART 2 — S3 Folders ##

S3 → e-commerce-data-kpc → Create folder


Create these 4 folders one by one:

### Folder Name ###

------------------------
| raw |<br>
| etl_processed_data |<br>
| athena-results |<br>
| glue-scripts |<br>

Then upload `orders.json` into the 'raw/' folder and upload 'etl_ecommerce.py' script into 'glue-scripts/' folder.


## PART 3 — Glue Setup ##

#### Create Database ####

Glue → Databases → Add database<br>
→ Name: ecommerce_db<br>
→ Create

Create Crawler

Glue → Crawlers → Create crawler<br>
→ Name: ecommerce-crawler<br>
→ Next<br>
→ Add data source → S3<br>
→ S3 path: s3://e-commerce-data-kpc/raw/<br>
→ Add → Next<br>
→ IAM Role: glue-pipeline-service-role<br>
→ Next<br>
→ Target database: ecommerce_db<br>
→ Next → Create crawler<br>



Create ETL Job

Glue → ETL Jobs → Script editor<br>
    • Engine: Spark<br>
    • Start fresh<br>
    • Job name: etl_ecommerce<br>
    • IAM Role: glue-pipeline-service-role<br>
    • Glue version: Glue 4.0<br>
    • Worker type: G.1X<br>
    • Number of workers: 2<br>


Paste the ETL script in the editor and click Save


## PART 4 — Lambda Functions ##

Lambda 1 — s3-crawler-trigger

Lambda → Create function<br>
    • Function name: s3-crawler-trigger<br>
    • Runtime: Python 3.12<br>
    • Permissions → Use existing role → lambda-pipeline-execution-role<br>
    • Create function<br>



Paste code → click Deploy:

import boto3

CRAWLER_NAME = 'ecommerce-crawler'

def lambda_handler(event, context): glue = boto3.client('glue')

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

Configuration → General configuration → Edit → Timeout: 1 min 0 sec → Save


Lambda 2 — etl-job-trigger

Lambda → Create function<br>
    → Function name: etl-job-trigger<br>
    → Runtime: Python 3.12<br>
    → Permissions → Use existing role → lambda-pipeline-execution-role<br>
    → Create function<br>

Paste code → click Deploy:

import boto3

ETL_JOB_NAME = 'etl_ecommerce'

def lambda_handler(event, context): glue = boto3.client('glue')
    
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

Configuration → General configuration → Edit<br>
→ Timeout: 1 min 0 sec → Save<br>




## PART 5 — S3 Event Notification ##

S3 → e-commerce-data-kpc → Properties
→ Event notifications → Create event notification

#### | Field | Value ####

| Event name | json-upload-trigger |<br>
| Prefix | raw/ |<br>
| Suffix | .json |
| Event types | All object create events |<br>
| Destination | Lambda function |<br>
| Lambda function | `s3-crawler-trigger` |

→ Save changes

This automatically adds the S3 permission to invoke Lambda 1 

### PART 6 — EventBridge Rule ###

EventBridge → Rules → Create rule<br>
→ Name: on-crawler-complete<br>
→ Event bus: default<br>
→ Rule type: Rule with an event pattern<br>
→ Next<br>


In event pattern section:

→ Event source: AWS services<br>
→ AWS service: Glue<br>
→ Event type: Glue Crawler State Change<br>
→ Switch to "Edit pattern" and paste:


{
  "source": ["aws.glue"],<br>
  "detail-type": ["Glue Crawler State Change"],<br>
  "detail": {<br>
    "crawlerName": ["ecommerce-crawler"],<br>
    "state": ["Succeeded"]<br>
  }<br>
}

→ Next<br>
→ Target type: AWS service<br>
→ Select a target: Lambda function<br>
→ Function: etl-job-trigger<br>
→ Next → Next → Create rule<br>

This automatically adds the EventBridge permission to invoke Lambda 2 

### PART 7 — Athena Setup ###

Athena → Settings → Manage<br>
→ Query result location: s3://e-commerce-data-kpc/athena-results/<br>
→ Save<br>


Final Checklist

IAM: lambda-pipeline-execution-role created with inline policy<br>
IAM: glue-pipeline-service-role created with AWSGlueServiceRole + inline policy<br>
S3: folders created (raw, etl_processed_data, athena-results, glue-scripts)<br>
S3: ETL script uploaded to glue-scripts/<br>
Glue: ecommerce_db database created<br>
Glue: ecommerce-crawler created → points to raw/<br>
Glue: etl_ecommerce job created with script<br>
Lambda 1: s3-crawler-trigger deployed with 1 min timeout<br>
Lambda 2: etl-job-trigger deployed with 1 min timeout<br>
S3 Event Notification → s3-crawler-trigger (auto-adds permission)<br>
EventBridge Rule → etl-job-trigger (auto-adds permission)<br>
Athena: result location set

