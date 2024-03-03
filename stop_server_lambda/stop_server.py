import boto3
import json
import logging
import datetime

# Initialize the boto3 client
ec2_client = boto3.client('ec2')
ssm_client = boto3.client('ssm')
cloudwatch_client = boto3.client('cloudwatch')

# Retrieve the instance ID from SSM Parameter Store
parameter = ssm_client.get_parameter(Name='zomboidServerInstanceId')
instance_id = parameter['Parameter']['Value']

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    # Check if the instance should be stopped based on active connections
    should_stop = not check_active_connections()

    if should_stop:
        stop_instance()
        return {
            'statusCode': 200,
            'body': json.dumps('Instance stopped successfully.')
        }
    else:
        return {
            'statusCode': 200,
            'body': json.dumps('Active connections found. Instance not stopped.')
        }

def check_active_connections():
    # This function is identical to the one in start_server.py
    # It checks for active connections by querying CloudWatch metrics
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
        if response['MetricDataResults'][0]['Values']:
            active_connections = response['MetricDataResults'][0]['Values'][0]
            logger.info(f"Active connections: {active_connections}")
            return active_connections > 0
        return False
    except Exception as e:
        logger.error(f"Error checking active connections: {e}")
        return False

def stop_instance():
    # Stop the EC2 instance
    try:
        ec2_client.stop_instances(InstanceIds=[instance_id])
        logger.info(f'Instance stopped: {instance_id}')
    except Exception as e:
        logger.error(f"Error stopping instance {instance_id}: {e}")
