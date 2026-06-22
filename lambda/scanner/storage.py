import boto3
import os
import uuid
from datetime import datetime

dynamodb = boto3.resource('dynamodb')
TABLE_NAME = os.environ.get('DYNAMODB_TABLE', 'cspm-findings')


def save_findings(findings):
    """Write all findings to DynamoDB."""
    if not findings:
        return
    table = dynamodb.Table(TABLE_NAME)
    timestamp = datetime.utcnow().isoformat() + 'Z'
    scan_id = str(uuid.uuid4())
    with table.batch_writer() as batch:
        for finding in findings:
            batch.put_item(Item={
                'finding_id': str(uuid.uuid4()),
                'scan_id': scan_id,
                'timestamp': timestamp,
                'check_id': finding['check_id'],
                'title': finding['title'],
                'severity': finding['severity'],
                'resource': finding['resource'],
                'resource_type': finding['resource_type'],
                'description': finding['description'],
                'remediation': finding['remediation'],
                'ttl': int(datetime.utcnow().timestamp()) + (90 * 86400)  # 90-day TTL
            })
    print(f'Saved {len(findings)} findings to DynamoDB (scan_id={scan_id})')
