import boto3
import json
import os
import urllib.request
from datetime import datetime

sns = boto3.client('sns')
SNS_TOPIC_ARN = os.environ.get('SNS_TOPIC_ARN', '')
SLACK_WEBHOOK_URL = os.environ.get('SLACK_WEBHOOK_URL', '')

SEVERITY_EMOJI = {
    'CRITICAL': ':red_circle:',
    'HIGH': ':orange_circle:',
    'MEDIUM': ':yellow_circle:',
    'LOW': ':white_circle:'
}


def send_alerts(findings):
    """Send alerts for all findings."""
    if not findings:
        print('No findings to alert on.')
        return
    critical = [f for f in findings if f['severity'] == 'CRITICAL']
    high = [f for f in findings if f['severity'] == 'HIGH']
    if critical or high:
        send_to_sns(findings)
        send_to_slack(findings)


def send_to_sns(findings):
    """Send summary to SNS topic (email subscribers)."""
    if not SNS_TOPIC_ARN:
        return
    critical = sum(1 for f in findings if f['severity'] == 'CRITICAL')
    high = sum(1 for f in findings if f['severity'] == 'HIGH')
    medium = sum(1 for f in findings if f['severity'] == 'MEDIUM')
    low = sum(1 for f in findings if f['severity'] == 'LOW')
    subject = f'AWS Security Scan: {critical} CRITICAL, {high} HIGH findings'
    body_lines = [
        f'AWS Security Posture Monitor — Scan Report',
        f'Timestamp: {datetime.utcnow().isoformat()}Z',
        f'',
        f'Summary:',
        f'  CRITICAL: {critical}',
        f'  HIGH:     {high}',
        f'  MEDIUM:   {medium}',
        f'  LOW:      {low}',
        f'',
        f'Top Findings:',
    ]
    for f in findings[:10]:
        body_lines.append(f"  [{f['severity']}] {f['check_id']}: {f['title']} — {f['resource']}")
    sns.publish(TopicArn=SNS_TOPIC_ARN, Subject=subject, Message='\n'.join(body_lines))


def send_to_slack(findings):
    """Send formatted message to Slack webhook."""
    if not SLACK_WEBHOOK_URL:
        return
    critical = sum(1 for f in findings if f['severity'] == 'CRITICAL')
    high = sum(1 for f in findings if f['severity'] == 'HIGH')
    blocks = [
        {'type': 'header', 'text': {'type': 'plain_text', 'text': ':shield: AWS Security Scan Alert'}},
        {'type': 'section', 'fields': [
            {'type': 'mrkdwn', 'text': f'*:red_circle: CRITICAL*\n{critical}'},
            {'type': 'mrkdwn', 'text': f'*:orange_circle: HIGH*\n{high}'},
        ]},
        {'type': 'divider'},
    ]
    for f in [x for x in findings if x['severity'] in ('CRITICAL', 'HIGH')][:5]:
        emoji = SEVERITY_EMOJI.get(f['severity'], ':white_circle:')
        blocks.append({'type': 'section', 'text': {'type': 'mrkdwn',
            'text': f"{emoji} *{f['check_id']}* — {f['title']}\n`{f['resource']}`\n_{f['remediation']}_"}})
    payload = json.dumps({'blocks': blocks}).encode('utf-8')
    req = urllib.request.Request(SLACK_WEBHOOK_URL, data=payload,
        headers={'Content-Type': 'application/json'})
    urllib.request.urlopen(req)
