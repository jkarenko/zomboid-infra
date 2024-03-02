import pulumi
from pulumi_aws import ec2

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

# Launch an EC2 instance using the existing key pair and the new security group
instance = ec2.Instance('zomboidServer',
    instance_type='c5.large',
    vpc_security_group_ids=[sec_group.id],
    ami='ami-00381a880aa48c6c6', # Replace with a valid Project Zomboid-compatible AMI in your region
    key_name='zomboid',
    user_data="""#!/bin/bash
                echo 'Downloading steamcmd...'
                mkdir -p /opt/steam
                cd /opt/steam
                curl -sqL 'https://steamcdn-a.akamaihd.net/client/installer/steamcmd_linux.tar.gz' | tar zxvf -
                """)

eip = ec2.Eip.get('zomboid server', 'eipalloc-03bc9778dab836abe')
eip_association = ec2.EipAssociation('eipAssoc', instance_id=instance.id, public_ip=eip.public_ip)

pulumi.export('instance_id', instance.id)
pulumi.export('public_ip', instance.public_ip)
