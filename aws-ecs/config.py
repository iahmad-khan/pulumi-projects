
# This file will host all the configuration keys for all the services and environments
import pulumi
import json
from secrets import get_aws_secrets

# Reference stack name in resouce naming ( dev, staging, prod )
stack = pulumi.get_stack()


# Common config across services
common_config = {
    # Common config
    'vpc_id': 'vpc-09f21cf5d1a3d2f25',
    'ecs_cluster': f"ecs-{stack}-cluster",
    'dns_namespace': f"myapp-{stack}.net",
    'ghcr_arn': 'arn:aws:secretsmanager:us-west-2:379821691363:secret:ImagePullSecret-t2t7Oz',

}
# App service config
app_config = {
    'name': "app",
    'port1': 8081,
    'port2': 8080,
    'image': 'app_image',
    'env_secrets': json.loads(json.dumps(get_aws_secrets(f"/{stack}-example-dev.net/app/"))),
    'cpu': 256,
    'memory': 512,
    'network_mode': 'awsvpc',
    'container_count': 1,
    'aws_region': 'us-west-2',
    'log_group': 'pulumi-ecs',
}
