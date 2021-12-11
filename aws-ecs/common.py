import pulumi
from pulumi import export, ResourceOptions
import pulumi_aws as aws
import json
from pulumi_aws.ec2 import internet_gateway, subnet
from config import common_config as config


# Read back the  VPC and subnets, which we will use.
vpc = aws.ec2.get_vpc(id=config['vpc_id'])
vpc_subnets = aws.ec2.get_subnet_ids(vpc_id=vpc.id)

# Create an ECS cluster to run a container-based service.
cluster = aws.ecs.Cluster('cluster', name=config['ecs_cluster'])

# Create an IAM role that can be used by our service's task.
ecs_task_role = aws.iam.Role("EcsTaskRole", assume_role_policy="""{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": ["ecs-tasks.amazonaws.com"]
      },
      "Action": "sts:AssumeRole"
    }
  ]
  }
""")

ecs_task_role_attachment = aws.iam.RolePolicyAttachment("ecsTaskRoleAttachment",
                                                        role=ecs_task_role.name,
                                                        policy_arn="arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy")

additional_perm_policy = aws.iam.RolePolicy("additionalPermPolicy",
                                            role=ecs_task_role.id,
                                            policy="""{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "ecr:GetAuthorizationToken",
                "ecr:BatchCheckLayerAvailability",
                "ecr:GetDownloadUrlForLayer",
                "ecr:BatchGetImage",
                "logs:CreateLogGroup",
                "logs:CreateLogStream",
                "logs:DescribeLogGroups",
                "logs:DescribeLogStreams",
                "logs:PutLogEvents"
            ],
            "Resource": "*"
        }
    ]
}
""")

policy_secretsmanager = aws.iam.RolePolicy("policySecretsmanager",
                                           role=ecs_task_role.id,
                                           policy=f"""{{
  "Version": "2012-10-17",
  "Statement": [
    {{
      "Action": [
        "secretsmanager:GetSecretValue"
      ],
      "Effect": "Allow",
      "Resource": "*"
    }}
  ]
}}
""")

policy_ecs_exec = aws.iam.RolePolicy("policyEcsExec",
                                     role=ecs_task_role.id,
                                     policy="""{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": [
        "ssmmessages:CreateControlChannel",
        "ssmmessages:CreateDataChannel",
        "ssmmessages:OpenControlChannel",
        "ssmmessages:OpenDataChannel"
      ],
      "Effect": "Allow",
      "Resource": "*"
    }
  ]
}
""")


# Service disovery namespace
private_dns_namespace = aws.servicediscovery.PrivateDnsNamespace("dns-space",
                                                                 name = config['dns_namespace'],
                                                                 description="pvt dns namespace",
                                                                 vpc=vpc.id)
