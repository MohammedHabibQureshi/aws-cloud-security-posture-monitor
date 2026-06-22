import boto3


DANGEROUS_PORTS = {22: 'SSH', 3389: 'RDP', 3306: 'MySQL', 5432: 'PostgreSQL',
                   27017: 'MongoDB', 6379: 'Redis', 9200: 'Elasticsearch'}


def run_all_ec2_checks():
    findings = []
    ec2 = boto3.client('ec2')
    findings.extend(check_security_groups(ec2))
    findings.extend(check_ebs_encryption(ec2))
    findings.extend(check_imds_v2(ec2))
    return findings


def check_security_groups(ec2):
    """CIS 5.2/5.3 — No SG should allow unrestricted inbound on dangerous ports."""
    findings = []
    paginator = ec2.get_paginator('describe_security_groups')
    for page in paginator.paginate():
        for sg in page['SecurityGroups']:
            for rule in sg.get('IpPermissions', []):
                from_port = rule.get('FromPort', 0)
                to_port = rule.get('ToPort', 65535)
                for cidr in rule.get('IpRanges', []):
                    if cidr.get('CidrIp') == '0.0.0.0/0':
                        for port, svc in DANGEROUS_PORTS.items():
                            if from_port <= port <= to_port:
                                findings.append({
                                    'check_id': 'CIS-5.2',
                                    'title': f'SG allows unrestricted {svc} (port {port}) inbound',
                                    'severity': 'CRITICAL' if port in (22, 3389) else 'HIGH',
                                    'resource': sg['GroupId'],
                                    'resource_type': 'EC2::SecurityGroup',
                                    'description': f"Security group {sg['GroupId']} ({sg['GroupName']}) allows 0.0.0.0/0 on port {port} ({svc}).",
                                    'remediation': f'Restrict port {port} to specific IP ranges.'
                                })
    return findings


def check_ebs_encryption(ec2):
    """Check that EBS encryption by default is enabled."""
    findings = []
    resp = ec2.get_ebs_encryption_by_default()
    if not resp.get('EbsEncryptionByDefault', False):
        findings.append({
            'check_id': 'CIS-2.2.1',
            'title': 'EBS encryption by default is disabled',
            'severity': 'HIGH',
            'resource': 'EBSDefaultEncryption',
            'resource_type': 'EC2::EBSEncryption',
            'description': 'New EBS volumes will not be encrypted by default.',
            'remediation': 'Enable EBS encryption by default in EC2 settings.'
        })
    return findings


def check_imds_v2(ec2):
    """Check that instances use IMDSv2 (token-required) to prevent SSRF attacks."""
    findings = []
    paginator = ec2.get_paginator('describe_instances')
    for page in paginator.paginate(Filters=[{'Name': 'instance-state-name', 'Values': ['running']}]):
        for reservation in page['Reservations']:
            for instance in reservation['Instances']:
                metadata_options = instance.get('MetadataOptions', {})
                if metadata_options.get('HttpTokens') != 'required':
                    instance_id = instance['InstanceId']
                    findings.append({
                        'check_id': 'CSPM-EC2-001',
                        'title': f'Instance {instance_id} uses IMDSv1 (vulnerable to SSRF)',
                        'severity': 'HIGH',
                        'resource': instance_id,
                        'resource_type': 'EC2::Instance',
                        'description': 'IMDSv1 allows SSRF attacks to steal instance credentials.',
                        'remediation': 'Set HttpTokens=required to enforce IMDSv2.'
                    })
    return findings
