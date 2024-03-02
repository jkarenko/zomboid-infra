import pulumi
from pulumi_aws import ec2

# Create a new security group for SSH and Zomboid ports
sec_group = ec2.SecurityGroup('zomboidSecurityGroup',
    description='Allow SSH and Zomboid ports',
    ingress=[
        {'protocol': '-1', 'from_port': 22, 'to_port': 22, 'cidr_blocks': ['0.0.0.0/0']},
        {'protocol': '-1', 'from_port': 16261, 'to_port': 16262, 'cidr_blocks': ['0.0.0.0/0']}
    ],
    egress=[
        {'protocol': '-1', 'from_port': 0, 'to_port': 0, 'cidr_blocks': ['0.0.0.0/0']},
    ])

# Launch an EC2 instance using the existing key pair and the new security group
instance = ec2.Instance('zomboidServer',
    instance_type='c5.large',
    security_groups=[sec_group.name],
    ami='ami-xxxxxxxx', # Replace with a valid Project Zomboid-compatible AMI in your region
    key_name='zomboid')

pulumi.export('instance_id', instance.id)
pulumi.export('public_ip', instance.public_ip)
