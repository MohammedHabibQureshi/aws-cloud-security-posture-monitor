import boto3


def run_all_s3_checks():
    findings = []
    s3 = boto3.client('s3')
    buckets = s3.list_buckets()['Buckets']
    for bucket in buckets:
        name = bucket['Name']
        findings.extend(check_public_access(s3, name))
        findings.extend(check_encryption(s3, name))
        findings.extend(check_versioning(s3, name))
        findings.extend(check_logging(s3, name))
    return findings


def check_public_access(s3, bucket_name):
    """CIS 2.1.5 — S3 buckets should block public access."""
    findings = []
    try:
        config = s3.get_public_access_block(Bucket=bucket_name)['PublicAccessBlockConfiguration']
        if not all([config.get('BlockPublicAcls'), config.get('BlockPublicPolicy'),
                    config.get('IgnorePublicAcls'), config.get('RestrictPublicBuckets')]):
            findings.append({
                'check_id': 'CIS-2.1.5',
                'title': f'S3 bucket {bucket_name} does not fully block public access',
                'severity': 'CRITICAL',
                'resource': f'arn:aws:s3:::{bucket_name}',
                'resource_type': 'S3::Bucket',
                'description': 'Public access block is not fully enabled.',
                'remediation': 'Enable all four public access block settings.'
            })
    except s3.exceptions.NoSuchPublicAccessBlockConfiguration:
        findings.append({
            'check_id': 'CIS-2.1.5',
            'title': f'S3 bucket {bucket_name} has no public access block',
            'severity': 'CRITICAL',
            'resource': f'arn:aws:s3:::{bucket_name}',
            'resource_type': 'S3::Bucket',
            'description': 'No public access block configuration found.',
            'remediation': 'Enable S3 Block Public Access on the bucket.'
        })
    return findings


def check_encryption(s3, bucket_name):
    """CIS 2.1.1 — S3 buckets should have default encryption enabled."""
    findings = []
    try:
        s3.get_bucket_encryption(Bucket=bucket_name)
    except Exception:
        findings.append({
            'check_id': 'CIS-2.1.1',
            'title': f'S3 bucket {bucket_name} has no default encryption',
            'severity': 'HIGH',
            'resource': f'arn:aws:s3:::{bucket_name}',
            'resource_type': 'S3::Bucket',
            'description': 'Server-side encryption is not enabled by default.',
            'remediation': 'Enable SSE-S3 or SSE-KMS as the default encryption.'
        })
    return findings


def check_versioning(s3, bucket_name):
    """CIS 2.1.3 — S3 buckets should have versioning enabled."""
    findings = []
    resp = s3.get_bucket_versioning(Bucket=bucket_name)
    if resp.get('Status') != 'Enabled':
        findings.append({
            'check_id': 'CIS-2.1.3',
            'title': f'S3 bucket {bucket_name} has versioning disabled',
            'severity': 'MEDIUM',
            'resource': f'arn:aws:s3:::{bucket_name}',
            'resource_type': 'S3::Bucket',
            'description': 'Versioning is disabled. Data cannot be recovered if overwritten.',
            'remediation': 'Enable versioning on the bucket.'
        })
    return findings


def check_logging(s3, bucket_name):
    """CIS 2.1.2 — S3 buckets should have access logging enabled."""
    findings = []
    resp = s3.get_bucket_logging(Bucket=bucket_name)
    if 'LoggingEnabled' not in resp:
        findings.append({
            'check_id': 'CIS-2.1.2',
            'title': f'S3 bucket {bucket_name} has no access logging',
            'severity': 'LOW',
            'resource': f'arn:aws:s3:::{bucket_name}',
            'resource_type': 'S3::Bucket',
            'description': 'Access logging is disabled. No audit trail for bucket access.',
            'remediation': 'Enable server access logging and point to a log bucket.'
        })
    return findings
