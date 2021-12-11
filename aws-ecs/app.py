from pulumi import export, ResourceOptions
import pulumi_aws as aws
import json
from pulumi_aws.iam import policy
from pulumi import Output
from config import app_config
from config import common_config as config

from common import cluster, vpc, vpc_subnets, private_dns_namespace
from common import ecs_task_role as role

# Create a SecurityGroup that permits ingress and unrestricted egress.
group = aws.ec2.SecurityGroup('app-secgrp',
                              vpc_id=vpc.id,
                              description='Enable app Ports',
                              ingress=[
                                  aws.ec2.SecurityGroupIngressArgs(
                                      protocol='tcp',
                                      from_port=app_config['port1'],
                                      to_port=app_config['port1'],
                                      cidr_blocks=['0.0.0.0/0'],
                                  ),
                                  aws.ec2.SecurityGroupIngressArgs(
                                      protocol='tcp',
                                      from_port=app_config['port2'],
                                      to_port=app_config['port2'],
                                      cidr_blocks=['0.0.0.0/0'],
                                  )
                              ],
                              egress=[aws.ec2.SecurityGroupEgressArgs(
                                  protocol='-1',
                                  from_port=0,
                                  to_port=0,
                                  cidr_blocks=['0.0.0.0/0'],
                              )])


# Spin up a load balanced service running our container image.
task_definition = aws.ecs.TaskDefinition('app-task',
                                         family='fargate-task-definition',
                                         cpu=app_config['cpu'],
                                         memory=app_config['memory'],
                                         network_mode=app_config['network_mode'],
                                         requires_compatibilities=['FARGATE'],
                                         execution_role_arn=role.arn,
                                         task_role_arn=role.arn,
                                         container_definitions=json.dumps([{
                                             'name': app_config['name'],
                                             'image': app_config['image'],
                                             'networkMode': app_config['network_mode'],
                                             'repositoryCredentials': {
                                                 'credentialsParameter': config['ghcr_arn'],
                                             },
                                             'readonlyRootFilesystem': False,
                                             'environment': app_config['env_secrets'],
                                             'portMappings': [
                                                 {
                                                     'containerPort': app_config['port1'],
                                                     'hostPort': app_config['port1'],
                                                     'protocol': 'tcp'
                                                 },
                                                 {
                                                     'containerPort': app_config['port2'],
                                                     'hostPort': app_config['port2'],
                                                     'protocol': 'tcp'
                                                 }
                                             ],
                                             'logConfiguration': {
                                                 'logDriver': 'awslogs',
                                                 'options': {
                                                     'awslogs-group': app_config['log_group'],
                                                     'awslogs-region': app_config['aws_region'],
                                                     'awslogs-stream-prefix': 'main'
                                                 }
                                             }
                                         }]))

# Service discovery config
app_service_discovery = aws.servicediscovery.Service("app-service-discovery",
                                                       name=app_config['name'],
                                                       dns_config=aws.servicediscovery.ServiceDnsConfigArgs(
                                                           namespace_id=private_dns_namespace.id,
                                                           dns_records=[aws.servicediscovery.ServiceDnsConfigDnsRecordArgs(
                                                               ttl=10,
                                                               type="SRV",
                                                           )],
                                                           routing_policy="MULTIVALUE",
                                                       ),
                                                       health_check_custom_config=aws.servicediscovery.ServiceHealthCheckCustomConfigArgs(
                                                           failure_threshold=1,
                                                       ),
                                                       opts=ResourceOptions(
                                                           depends_on=[task_definition])
                                                       )

# ECS service
app_ecs_service = aws.ecs.Service('app-ecs-service',
                                    cluster=cluster.arn,
                                    desired_count=app_config['container_count'],
                                    launch_type='FARGATE',
                                    task_definition=task_definition.arn,
                                    enable_execute_command=True,
                                    wait_for_steady_state=True,
                                    service_registries=aws.ecs.ServiceServiceRegistriesArgs(
                                        registry_arn=app_service_discovery.arn,
                                        port=app_config['port1'],
                                    ),
                                    network_configuration=aws.ecs.ServiceNetworkConfigurationArgs(
                                        assign_public_ip=False,
                                        subnets=vpc_subnets.ids,
                                        security_groups=[group.id],
                                    ))
