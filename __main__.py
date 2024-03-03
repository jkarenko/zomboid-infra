import base64
import pulumi
from pulumi_aws import iam, lambda_, cloudwatch, ssm, ec2

sec_group = ec2.SecurityGroup('zomboidSecurityGroup',
    description='Allow SSH and game client ports',
    ingress=[
        {'protocol': 'tcp', 'from_port': 22, 'to_port': 22, 'cidr_blocks': ['0.0.0.0/0']},
        {'protocol': 'tcp', 'from_port': 8766, 'to_port': 8766, 'cidr_blocks': ['0.0.0.0/0']},
        {'protocol': 'udp', 'from_port': 16261, 'to_port': 16261, 'cidr_blocks': ['0.0.0.0/0']},
        {'protocol': 'udp', 'from_port': 16262, 'to_port': 16262, 'cidr_blocks': ['0.0.0.0/0'], 'description': 'Game client port range'},
        {'protocol': 'tcp', 'from_port': 27015, 'to_port': 27015, 'cidr_blocks': ['0.0.0.0/0']},
        {'protocol': 'tcp', 'from_port': 27016, 'to_port': 27016, 'cidr_blocks': ['0.0.0.0/0']},
        {'protocol': 'tcp', 'from_port': 8080, 'to_port': 8080, 'cidr_blocks': ['0.0.0.0/0'], 'description': 'HTTP for internal services'},
        {'protocol': 'tcp', 'from_port': 8443, 'to_port': 8443, 'cidr_blocks': ['0.0.0.0/0'], 'description': 'HTTPS for internal services'}
    ],
    egress=[
        {'protocol': '-1', 'from_port': 0, 'to_port': 0, 'cidr_blocks': ['0.0.0.0/0']},
    ])

with open('install_steamcmd.sh', 'r') as file:
    install_cmd = base64.b64encode(file.read().encode()).decode()

with open('install_zomboid.sh', 'r') as file:
    zomboid_cmd = base64.b64encode(file.read().encode()).decode()

with open('start_zomboid.sh', 'r') as file:
    start_cmd = base64.b64encode(file.read().encode()).decode()

# Launch an EC2 instance using the existing key pair and the new security group
instance = ec2.Instance('zomboid',
    instance_type='c5.large',
    vpc_security_group_ids=[sec_group.id],
    ami='ami-00381a880aa48c6c6', # Replace with a valid Project Zomboid-compatible AMI in your region
    key_name='zomboid',
    tags={
        'Name': 'zomboid-server',
    },
)

eip = ec2.Eip.get('zomboid', 'eipalloc-03bc9778dab836abe')
eip_association = ec2.EipAssociation('eipAssoc', instance_id=instance.id, public_ip=eip.public_ip)

pulumi.export('instance_id', instance.id)
pulumi.export('public_ip', instance.public_ip)


# IAM Role and Policy for Lambda to interact with EC2, CloudWatch, and SSM
lambda_role = iam.Role("lambdaRole",
    assume_role_policy="""{
        "Version": "2012-10-17",
        "Statement": [{
            "Action": "sts:AssumeRole",
            "Principal": {"Service": "lambda.amazonaws.com"},
            "Effect": "Allow",
            "Sid": ""
        }]
    }""")

policy = iam.RolePolicy("lambdaPolicy",
    role=lambda_role.id,
    policy="""{
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Action": [
                "ec2:DescribeInstances",
                "ec2:StartInstances",
                "ec2:StopInstances",
                "ssm:SendCommand",
                "ssm:GetParameter",
                "cloudwatch:PutMetricData",
                "cloudwatch:GetMetricData",
                "cloudwatch:GetMetricStatistics",
                "logs:CreateLogGroup",
                "logs:CreateLogStream",
                "logs:PutLogEvents"
            ],
            "Resource": "*"
        }]
    }""")

# Lambda function for starting the server
start_server_lambda = lambda_.Function("StartServerLambda",
    code=pulumi.AssetArchive({
        ".": pulumi.FileArchive("./start_server_lambda")
    }),
    role=lambda_role.arn,
    handler="start_server.handler",
    runtime="python3.12")

pulumi.export('start_server_lambda_arn', start_server_lambda.arn)

# Lambda function for stopping the server
stop_server_lambda = lambda_.Function("StopServerLambda",
    code=pulumi.AssetArchive({
        ".": pulumi.FileArchive("./stop_server_lambda")
    }),
    role=lambda_role.arn,
    handler="stop_server.handler",
    runtime="python3.8")

pulumi.export('stop_server_lambda_arn', start_server_lambda.arn)


# CloudWatch Event Rule to trigger the start server lambda every minute
start_event_rule = cloudwatch.EventRule("StartServerRule",
    schedule_expression="rate(1 minute)")

start_event_target = cloudwatch.EventTarget("StartServerTarget",
    arn=start_server_lambda.arn,
    rule=start_event_rule.name,  # Associate with the start event rule
    target_id="StartServerLambdaTarget")

# CloudWatch Event Rule to trigger the stop server lambda based on conditions
stop_event_rule = cloudwatch.EventRule("StopServerRule",
    schedule_expression="rate(5 minutes)")

stop_event_target = cloudwatch.EventTarget("StopServerTarget",
    arn=stop_server_lambda.arn,
    rule=stop_event_rule.name,  # Associate with the stop event rule
    target_id="StopServerLambdaTarget")

# Permission for CloudWatch to invoke StartServerLambda
start_permission = lambda_.Permission("StartLambdaPermission",
    action="lambda:InvokeFunction",
    function=start_server_lambda.name,
    principal="events.amazonaws.com",
    source_arn=start_event_rule.arn)

# Permission for CloudWatch to invoke StopServerLambda
stop_permission = lambda_.Permission("StopLambdaPermission",
    action="lambda:InvokeFunction",
    function=stop_server_lambda.name,
    principal="events.amazonaws.com",
    source_arn=stop_event_rule.arn)

# Save the instance ID to SSM Parameter Store
instance_id_parameter = ssm.Parameter("InstanceIdParameter",
    name="zomboidServerInstanceId",
    type="String",
    value=instance.id)
