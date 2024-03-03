import boto3
import json
import logging
import datetime

# Initialize the boto3 client
ec2_client = boto3.client('ec2')
ssm_client = boto3.client('ssm')
cloudwatch_client = boto3.client('cloudwatch')

parameter = ssm_client.get_parameter(Name='zomboidServerInstanceId')
instance_id = parameter['Parameter']['Value']

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def handler(event, context):
    # Check if the instance should be started based on active connections
    should_start = check_active_connections()

    if should_start:
        start_instance()
        return {
            'statusCode': 200,
            'body': json.dumps('Instance started successfully.')
        }
    else:
        return {
            'statusCode': 200,
            'body': json.dumps('No active connections. Instance not started.')
        }

def check_active_connections():
    # Check for active connections by querying CloudWatch metrics
    try:
        response = cloudwatch_client.get_metric_data(
            MetricDataQueries=[
                {
                    'Id': 'activeConnections',
                    'MetricStat': {
                        'Metric': {
                            'Namespace': 'AWS/EC2',
                            'MetricName': 'ActiveConnections',
                            'Dimensions': [
                                {
                                    'Name': 'InstanceId',
                                    'Value': instance_id
                                },
                            ]
                        },
                        'Period': 300,
                        'Stat': 'Average',
                    },
                    'ReturnData': True,
                },
            ],
            StartTime=datetime.datetime.now() - datetime.timedelta(seconds=600),
            EndTime=datetime.datetime.now(),
        )
        # Assuming a threshold of 0 means no active connections
        if response['MetricDataResults'][0]['Values']:
            active_connections = response['MetricDataResults'][0]['Values'][0]
            logger.info(f"Active connections: {active_connections}")
            return active_connections > 0
        return False
    except Exception as e:
        logger.error(f"Error checking active connections: {e}")
        return False

def start_instance():
    # Start the EC2 instance
    try:
        ec2_client.start_instances(InstanceIds=[instance_id])
        logger.info(f'Instance started: {instance_id}')
    except Exception as e:
        logger.error(f"Error starting instance {instance_id}: {e}")
