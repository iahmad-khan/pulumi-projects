#!/usr/bin/env python3

import pulumi
import pulumi_aws as aws
import json
import subprocess

# Get service secrets from aws based on service prefix


def get_aws_secrets(prefix):
    service_secrets = []
    cmd = f"aws secretsmanager list-secrets --filter Key=name,Values={prefix}"
    secrets = json.loads(subprocess.getoutput(cmd))
    for secret in secrets.values():
        for s in secret:
            sname = s.get('Name')
            pair = {}
            pair['name'] = sname.split("/")[-1]
            pair['value'] = aws.secretsmanager.get_secret_version(
                sname).secret_string
            service_secrets.append(pair)
    return service_secrets
