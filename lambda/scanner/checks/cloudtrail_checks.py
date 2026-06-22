import boto3


def run_all_cloudtrail_checks():
    findings = []
    ct = boto3.client('cloudtrail')
    trails = ct.describe_trails(includeShadowTrails=False)['trailList']
    if not trails:
        findings.append({
            'check_id': 'CIS-3.1',
            'title': 'No CloudTrail trails found',
            'severity': 'CRITICAL',
            'resource': 'CloudTrail',
            'resource_type': 'CloudTrail::Trail',
            'description': 'No CloudTrail configured. API activity is not being logged.',
            'remediation': 'Enable CloudTrail with multi-region coverage.'
        })
        return findings
    for trail in trails:
        findings.extend(check_multi_region(ct, trail))
        findings.extend(check_log_validation(trail))
        findings.extend(check_log_encryption(trail))
    return findings


def check_multi_region(ct, trail):
    """CIS 3.1 — CloudTrail should be enabled in all regions."""
    findings = []
    if not trail.get('IsMultiRegionTrail', False):
        findings.append({
            'check_id': 'CIS-3.1',
            'title': f"Trail {trail['Name']} is not multi-region",
            'severity': 'HIGH',
            'resource': trail.get('TrailARN', trail['Name']),
            'resource_type': 'CloudTrail::Trail',
            'description': 'Trail only captures events in its home region.',
            'remediation': 'Enable multi-region trail logging.'
        })
    return findings


def check_log_validation(trail):
    """CIS 3.2 — CloudTrail log file validation must be enabled."""
    findings = []
    if not trail.get('LogFileValidationEnabled', False):
        findings.append({
            'check_id': 'CIS-3.2',
            'title': f"Trail {trail['Name']} has log file validation disabled",
            'severity': 'MEDIUM',
            'resource': trail.get('TrailARN', trail['Name']),
            'resource_type': 'CloudTrail::Trail',
            'description': 'Cannot verify log integrity — logs could be tampered.',
            'remediation': 'Enable log file validation on the trail.'
        })
    return findings


def check_log_encryption(trail):
    """CIS 3.7 — CloudTrail logs should be encrypted with KMS."""
    findings = []
    if not trail.get('KMSKeyId'):
        findings.append({
            'check_id': 'CIS-3.7',
            'title': f"Trail {trail['Name']} logs are not KMS-encrypted",
            'severity': 'MEDIUM',
            'resource': trail.get('TrailARN', trail['Name']),
            'resource_type': 'CloudTrail::Trail',
            'description': 'Trail S3 logs are not encrypted with KMS CMK.',
            'remediation': 'Configure a KMS CMK for trail log encryption.'
        })
    return findings
