import boto3
from datetime import datetime, timezone


def run_all_iam_checks():
    """Run all CIS IAM checks and return list of findings."""
    findings = []
    findings.extend(check_root_mfa())
    findings.extend(check_unused_credentials())
    findings.extend(check_access_key_rotation())
    findings.extend(check_password_policy())
    findings.extend(check_inline_policies())
    return findings


def check_root_mfa():
    """CIS 1.5 — Root account should have MFA enabled."""
    iam = boto3.client('iam')
    findings = []
    summary = iam.get_account_summary()['SummaryMap']
    if summary.get('AccountMFAEnabled', 0) == 0:
        findings.append({
            'check_id': 'CIS-1.5',
            'title': 'Root account MFA not enabled',
            'severity': 'CRITICAL',
            'resource': 'root',
            'resource_type': 'IAM::RootAccount',
            'description': 'Root account has no MFA. Immediate risk of account takeover.',
            'remediation': 'Enable MFA on root account via IAM console.'
        })
    return findings


def check_unused_credentials():
    """CIS 1.12 — Credentials unused for 90+ days should be disabled."""
    iam = boto3.client('iam')
    findings = []
    paginator = iam.get_paginator('get_credential_report')
    try:
        report = iam.generate_credential_report()
        report_data = iam.get_credential_report()['Content'].decode('utf-8')
        lines = report_data.strip().split('\n')
        headers = lines[0].split(',')
        for line in lines[1:]:
            row = dict(zip(headers, line.split(',')))
            user = row.get('user', '')
            if user == '<root_account>':
                continue
            for key_num in ['1', '2']:
                active = row.get(f'access_key_{key_num}_active', 'false')
                last_used = row.get(f'access_key_{key_num}_last_used_date', 'N/A')
                if active == 'true' and last_used not in ('N/A', 'no_information'):
                    last_used_dt = datetime.fromisoformat(last_used.replace('Z', '+00:00'))
                    days_unused = (datetime.now(timezone.utc) - last_used_dt).days
                    if days_unused > 90:
                        findings.append({
                            'check_id': 'CIS-1.12',
                            'title': f'Access key unused for {days_unused} days',
                            'severity': 'HIGH',
                            'resource': f'{user}/key-{key_num}',
                            'resource_type': 'IAM::AccessKey',
                            'description': f'User {user} has an active key unused for {days_unused} days.',
                            'remediation': 'Disable or delete the unused access key.'
                        })
    except Exception as e:
        print(f'Credential report error: {e}')
    return findings


def check_access_key_rotation():
    """CIS 1.14 — Access keys should be rotated every 90 days."""
    iam = boto3.client('iam')
    findings = []
    users = iam.list_users()['Users']
    for user in users:
        keys = iam.list_access_keys(UserName=user['UserName'])['AccessKeyMetadata']
        for key in keys:
            if key['Status'] == 'Active':
                age_days = (datetime.now(timezone.utc) - key['CreateDate']).days
                if age_days > 90:
                    findings.append({
                        'check_id': 'CIS-1.14',
                        'title': f'Access key not rotated in {age_days} days',
                        'severity': 'MEDIUM',
                        'resource': f"{user['UserName']}/{key['AccessKeyId']}",
                        'resource_type': 'IAM::AccessKey',
                        'description': f"Key {key['AccessKeyId']} is {age_days} days old.",
                        'remediation': 'Rotate access keys every 90 days.'
                    })
    return findings


def check_password_policy():
    """CIS 1.8–1.11 — Password policy should enforce complexity."""
    iam = boto3.client('iam')
    findings = []
    try:
        policy = iam.get_account_password_policy()['PasswordPolicy']
        checks = [
            ('MinimumPasswordLength', 14, 'CIS-1.8', 'Password minimum length < 14'),
            ('RequireUppercaseCharacters', True, 'CIS-1.9', 'Password policy missing uppercase requirement'),
            ('RequireLowercaseCharacters', True, 'CIS-1.9', 'Password policy missing lowercase requirement'),
            ('RequireNumbers', True, 'CIS-1.10', 'Password policy missing number requirement'),
            ('RequireSymbols', True, 'CIS-1.11', 'Password policy missing symbol requirement'),
        ]
        for field, expected, check_id, title in checks:
            actual = policy.get(field, 0 if isinstance(expected, int) else False)
            if isinstance(expected, int) and actual < expected:
                findings.append({'check_id': check_id, 'title': title, 'severity': 'MEDIUM',
                    'resource': 'PasswordPolicy', 'resource_type': 'IAM::PasswordPolicy',
                    'description': f'{field} is {actual}, should be >= {expected}.',
                    'remediation': 'Update account password policy in IAM console.'})
            elif isinstance(expected, bool) and actual != expected:
                findings.append({'check_id': check_id, 'title': title, 'severity': 'MEDIUM',
                    'resource': 'PasswordPolicy', 'resource_type': 'IAM::PasswordPolicy',
                    'description': f'{field} is {actual}, should be {expected}.',
                    'remediation': 'Update account password policy in IAM console.'})
    except iam.exceptions.NoSuchEntityException:
        findings.append({'check_id': 'CIS-1.8', 'title': 'No password policy set',
            'severity': 'HIGH', 'resource': 'PasswordPolicy', 'resource_type': 'IAM::PasswordPolicy',
            'description': 'No account password policy exists.',
            'remediation': 'Set a strong password policy in IAM.'})
    return findings


def check_inline_policies():
    """CIS 1.16 — IAM policies should not be attached directly to users."""
    iam = boto3.client('iam')
    findings = []
    users = iam.list_users()['Users']
    for user in users:
        policies = iam.list_user_policies(UserName=user['UserName'])['PolicyNames']
        if policies:
            findings.append({
                'check_id': 'CIS-1.16',
                'title': f"User has {len(policies)} inline policy/policies",
                'severity': 'LOW',
                'resource': user['UserName'],
                'resource_type': 'IAM::User',
                'description': f"User {user['UserName']} has inline policies: {policies}.",
                'remediation': 'Use IAM groups or roles instead of inline user policies.'
            })
    return findings
