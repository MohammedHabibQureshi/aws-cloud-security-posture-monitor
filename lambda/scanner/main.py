import json
import boto3
from checks.ec2_checks import run_all_ec2_checks
from checks.iam_checks import run_all_iam_checks
from checks.s3_checks import run_all_s3_checks
from checks.cloudtrail_checks import run_all_cloudtrail_checks

from alerting import send_alerts
from storage import save_findings
import boto3

cloudwatch = boto3.client('cloudwatch')


def lambda_handler(event, context):
    """Main Lambda entry point. Runs all security checks."""
    print(f'Starting security scan. Event: {json.dumps(event)}')
    all_findings = []
    check_modules = [
        ('IAM', run_all_iam_checks),
        ('S3', run_all_s3_checks),
        ('EC2', run_all_ec2_checks),
        ('CloudTrail', run_all_cloudtrail_checks),
    ]
    for name, check_fn in check_modules:
        try:
            print(f'Running {name} checks...')
            findings = check_fn()
            all_findings.extend(findings)
            print(f'{name}: {len(findings)} findings')
        except Exception as e:
            print(f'ERROR in {name} checks: {e}')
    save_findings(all_findings)
    send_alerts(all_findings)
    publish_metrics(all_findings)
    summary = {s: sum(1 for f in all_findings if f['severity'] == s)
               for s in ('CRITICAL', 'HIGH', 'MEDIUM', 'LOW')}
    print(f'Scan complete. Summary: {summary}')
    return {'statusCode': 200, 'body': json.dumps({'findings': len(all_findings), 'summary': summary})}


def publish_metrics(findings):
    """Push custom metrics to CloudWatch."""
    severity_counts = {s: 0 for s in ('CRITICAL', 'HIGH', 'MEDIUM', 'LOW')}
    for f in findings:
        severity_counts[f['severity']] = severity_counts.get(f['severity'], 0) + 1
    metric_data = []
    for severity, count in severity_counts.items():
        metric_data.append({
            'MetricName': 'FindingsBySeverity',
            'Dimensions': [{'Name': 'Severity', 'Value': severity}],
            'Value': count,
            'Unit': 'Count'
        })
    metric_data.append({'MetricName': 'TotalFindings', 'Value': len(findings), 'Unit': 'Count'})
    cloudwatch.put_metric_data(Namespace='CSPM/SecurityFindings', MetricData=metric_data)
