#!/usr/bin/env python3
"""
AWS 워크샵 문제 자동 진단 도구
일반적인 문제들을 자동으로 감지하고 해결 방법을 제시합니다.
"""

import boto3
import json
import sys
import subprocess
import os
from botocore.exceptions import ClientError, NoCredentialsError
from datetime import datetime, timedelta
import argparse
import re

class IssueDiagnostic:
    def __init__(self, profile_name=None, region='us-east-1'):
        """문제 진단기 초기화"""
        self.profile_name = profile_name
        self.region = region
        self.session = None
        self.diagnostic_results = {
            'timestamp': datetime.now().isoformat(),
            'issues_found': [],
            'recommendations': [],
            'system_info': {},
            'aws_config': {}
        }
        
    def setup_session(self):
        """AWS 세션 설정"""
        try:
            if self.profile_name:
                self.session = boto3.Session(profile_name=self.profile_name, region_name=self.region)
            else:
                self.session = boto3.Session(region_name=self.region)
            return True
        except Exception as e:
            self.add_issue('AWS_SESSION', 'CRITICAL', f'AWS 세션 생성 실패: {str(e)}', 
                          'AWS CLI 설정을 확인하고 "aws configure" 명령을 실행하세요.')
            return False
    
    def add_issue(self, category, severity, description, recommendation):
        """문제 추가"""
        issue = {
            'category': category,
            'severity': severity,
            'description': description,
            'recommendation': recommendation,
            'timestamp': datetime.now().isoformat()
        }
        self.diagnostic_results['issues_found'].append(issue)
        
        if recommendation not in self.diagnostic_results['recommendations']:
            self.diagnostic_results['recommendations'].append(recommendation)
    
    def check_system_requirements(self):
        """시스템 요구사항 확인"""
        print("🔍 시스템 요구사항 확인 중...")
        
        # Python 버전 확인
        python_version = sys.version_info
        if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 7):
            self.add_issue('PYTHON_VERSION', 'HIGH', 
                          f'Python 버전이 너무 낮습니다: {python_version.major}.{python_version.minor}',
                          'Python 3.7 이상으로 업그레이드하세요.')
        
        # AWS CLI 설치 확인
        try:
            result = subprocess.run(['aws', '--version'], capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                aws_version = result.stdout.strip()
                self.diagnostic_results['system_info']['aws_cli_version'] = aws_version
                
                # AWS CLI v2 권장
                if 'aws-cli/1.' in aws_version:
                    self.add_issue('AWS_CLI_VERSION', 'MEDIUM',
                                  'AWS CLI v1을 사용 중입니다',
                                  'AWS CLI v2로 업그레이드하는 것을 권장합니다.')
            else:
                self.add_issue('AWS_CLI_MISSING', 'HIGH',
                              'AWS CLI가 설치되지 않았습니다',
                              'AWS CLI를 설치하세요: https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html')
        except (subprocess.TimeoutExpired, FileNotFoundError):
            self.add_issue('AWS_CLI_MISSING', 'HIGH',
                          'AWS CLI가 설치되지 않았거나 PATH에 없습니다',
                          'AWS CLI를 설치하고 PATH에 추가하세요.')
        
        # 필수 Python 패키지 확인
        required_packages = ['boto3', 'botocore']
        for package in required_packages:
            try:
                __import__(package)
            except ImportError:
                self.add_issue('PYTHON_PACKAGE', 'HIGH',
                              f'필수 Python 패키지가 없습니다: {package}',
                              f'pip install {package} 명령으로 설치하세요.')
    
    def check_aws_credentials(self):
        """AWS 자격 증명 확인"""
        print("🔑 AWS 자격 증명 확인 중...")
        
        try:
            # AWS CLI 설정 확인
            result = subprocess.run(['aws', 'configure', 'list'], capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                config_output = result.stdout
                self.diagnostic_results['aws_config']['cli_config'] = config_output
                
                # 자격 증명 누락 확인
                if 'not set' in config_output.lower():
                    self.add_issue('AWS_CREDENTIALS', 'CRITICAL',
                                  'AWS 자격 증명이 설정되지 않았습니다',
                                  'aws configure 명령으로 Access Key와 Secret Key를 설정하세요.')
                
                # 리전 설정 확인
                if 'region' in config_output and 'not set' in config_output:
                    self.add_issue('AWS_REGION', 'MEDIUM',
                                  'AWS 리전이 설정되지 않았습니다',
                                  'aws configure set region us-east-1 명령으로 리전을 설정하세요.')
            
            # STS를 통한 자격 증명 검증
            if self.session:
                sts = self.session.client('sts')
                identity = sts.get_caller_identity()
                self.diagnostic_results['aws_config']['identity'] = {
                    'account_id': identity.get('Account'),
                    'user_arn': identity.get('Arn'),
                    'user_id': identity.get('UserId')
                }
                
                # 임시 자격 증명 확인
                if 'assumed-role' in identity.get('Arn', ''):
                    self.add_issue('TEMP_CREDENTIALS', 'LOW',
                                  '임시 자격 증명을 사용 중입니다',
                                  '장시간 작업 시 자격 증명 만료에 주의하세요.')
                
        except subprocess.TimeoutExpired:
            self.add_issue('AWS_CLI_TIMEOUT', 'MEDIUM',
                          'AWS CLI 명령이 시간 초과되었습니다',
                          '네트워크 연결을 확인하고 프록시 설정을 검토하세요.')
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'InvalidUserID.NotFound':
                self.add_issue('AWS_CREDENTIALS', 'CRITICAL',
                              '유효하지 않은 AWS 자격 증명입니다',
                              'Access Key와 Secret Key를 다시 확인하세요.')
            elif error_code == 'TokenRefreshRequired':
                self.add_issue('AWS_TOKEN', 'HIGH',
                              'AWS 토큰을 새로 고쳐야 합니다',
                              'aws configure 명령으로 자격 증명을 다시 설정하세요.')
            else:
                self.add_issue('AWS_AUTH', 'HIGH',
                              f'AWS 인증 오류: {e.response["Error"]["Message"]}',
                              'AWS 자격 증명과 권한을 확인하세요.')
        except NoCredentialsError:
            self.add_issue('AWS_CREDENTIALS', 'CRITICAL',
                          'AWS 자격 증명을 찾을 수 없습니다',
                          'aws configure 명령으로 자격 증명을 설정하세요.')
    
    def check_network_connectivity(self):
        """네트워크 연결 확인"""
        print("🌐 네트워크 연결 확인 중...")
        
        # AWS 엔드포인트 연결 테스트
        aws_endpoints = [
            's3.amazonaws.com',
            f'glue.{self.region}.amazonaws.com',
            f'athena.{self.region}.amazonaws.com'
        ]
        
        for endpoint in aws_endpoints:
            try:
                # ping 대신 nslookup 사용 (더 안정적)
                result = subprocess.run(['nslookup', endpoint], 
                                      capture_output=True, text=True, timeout=10)
                if result.returncode != 0:
                    self.add_issue('NETWORK_DNS', 'MEDIUM',
                                  f'DNS 해석 실패: {endpoint}',
                                  'DNS 설정을 확인하고 인터넷 연결을 검토하세요.')
            except (subprocess.TimeoutExpired, FileNotFoundError):
                self.add_issue('NETWORK_TOOLS', 'LOW',
                              '네트워크 진단 도구를 사용할 수 없습니다',
                              '수동으로 인터넷 연결을 확인하세요.')
        
        # 프록시 설정 확인
        proxy_vars = ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy']
        proxy_detected = False
        for var in proxy_vars:
            if os.environ.get(var):
                proxy_detected = True
                self.diagnostic_results['system_info'][f'proxy_{var.lower()}'] = os.environ[var]
        
        if proxy_detected:
            self.add_issue('PROXY_CONFIG', 'LOW',
                          '프록시 설정이 감지되었습니다',
                          'AWS CLI에 프록시 설정이 필요할 수 있습니다: aws configure set proxy_url http://proxy:port')
    
    def check_service_permissions(self, bucket_name=None):
        """서비스 권한 확인"""
        print("🔐 서비스 권한 확인 중...")
        
        if not self.session:
            return
        
        # S3 권한 확인
        try:
            s3 = self.session.client('s3')
            s3.list_buckets()
            
            if bucket_name:
                try:
                    s3.head_bucket(Bucket=bucket_name)
                except ClientError as e:
                    if e.response['Error']['Code'] == 'NoSuchBucket':
                        self.add_issue('S3_BUCKET', 'HIGH',
                                      f'S3 버킷이 존재하지 않습니다: {bucket_name}',
                                      f'S3 콘솔에서 {bucket_name} 버킷을 생성하세요.')
                    elif e.response['Error']['Code'] == 'AccessDenied':
                        self.add_issue('S3_PERMISSIONS', 'HIGH',
                                      f'S3 버킷 접근 권한이 없습니다: {bucket_name}',
                                      'IAM 정책에 S3 버킷 접근 권한을 추가하세요.')
        except ClientError as e:
            if e.response['Error']['Code'] == 'AccessDenied':
                self.add_issue('S3_PERMISSIONS', 'HIGH',
                              'S3 서비스 접근 권한이 없습니다',
                              'IAM 정책에 S3 권한을 추가하세요.')
        
        # Glue 권한 확인
        try:
            glue = self.session.client('glue')
            glue.get_databases()
        except ClientError as e:
            if e.response['Error']['Code'] == 'AccessDenied':
                self.add_issue('GLUE_PERMISSIONS', 'HIGH',
                              'Glue 서비스 접근 권한이 없습니다',
                              'IAM 정책에 Glue 권한을 추가하세요.')
        
        # Athena 권한 확인
        try:
            athena = self.session.client('athena')
            athena.list_work_groups()
        except ClientError as e:
            if e.response['Error']['Code'] == 'AccessDenied':
                self.add_issue('ATHENA_PERMISSIONS', 'HIGH',
                              'Athena 서비스 접근 권한이 없습니다',
                              'IAM 정책에 Athena 권한을 추가하세요.')
    
    def check_common_issues(self, bucket_name=None):
        """일반적인 문제 확인"""
        print("🔧 일반적인 문제 확인 중...")
        
        if not self.session:
            return
        
        # Glue 크롤러 실패 확인
        try:
            glue = self.session.client('glue')
            crawlers = glue.get_crawlers()
            
            for crawler in crawlers['Crawlers']:
                if crawler.get('LastCrawl', {}).get('Status') == 'FAILED':
                    error_message = crawler.get('LastCrawl', {}).get('ErrorMessage', '')
                    self.add_issue('GLUE_CRAWLER_FAILED', 'MEDIUM',
                                  f'Glue 크롤러 실패: {crawler["Name"]}',
                                  f'크롤러 로그를 확인하고 데이터 경로와 IAM 역할을 검토하세요. 오류: {error_message}')
        except ClientError:
            pass
        
        # Athena 쿼리 결과 위치 확인
        try:
            athena = self.session.client('athena')
            workgroups = athena.list_work_groups()
            
            for wg in workgroups['WorkGroups']:
                if wg['Name'] == 'primary':
                    try:
                        wg_detail = athena.get_work_group(WorkGroup='primary')
                        config = wg_detail['WorkGroup'].get('Configuration', {})
                        result_config = config.get('ResultConfiguration', {})
                        
                        if not result_config.get('OutputLocation'):
                            self.add_issue('ATHENA_OUTPUT', 'MEDIUM',
                                          'Athena 쿼리 결과 저장 위치가 설정되지 않았습니다',
                                          'Athena 설정에서 쿼리 결과 저장을 위한 S3 위치를 설정하세요.')
                    except ClientError:
                        pass
        except ClientError:
            pass
        
        # 리전별 서비스 가용성 확인
        if self.region not in ['us-east-1', 'us-west-2', 'eu-west-1']:
            self.add_issue('REGION_AVAILABILITY', 'LOW',
                          f'일부 AWS 서비스가 {self.region} 리전에서 제한될 수 있습니다',
                          '주요 리전(us-east-1, us-west-2, eu-west-1) 사용을 고려하세요.')
    
    def generate_fix_script(self):
        """자동 수정 스크립트 생성"""
        fix_commands = []
        
        for issue in self.diagnostic_results['issues_found']:
            category = issue['category']
            severity = issue['severity']
            
            if category == 'AWS_CREDENTIALS' and severity == 'CRITICAL':
                fix_commands.append('echo "AWS 자격 증명 설정:"')
                fix_commands.append('aws configure')
            elif category == 'AWS_REGION' and severity == 'MEDIUM':
                fix_commands.append(f'aws configure set region {self.region}')
            elif category == 'ATHENA_OUTPUT':
                fix_commands.append('echo "Athena 쿼리 결과 위치 설정 (S3 버킷 이름을 실제 버킷으로 변경):"')
                fix_commands.append('aws athena update-work-group --work-group primary --configuration-updates "ResultConfigurationUpdates={OutputLocation=s3://your-athena-results-bucket/}"')
        
        if fix_commands:
            script_content = '#!/bin/bash\n'
            script_content += '# AWS 워크샵 문제 자동 수정 스크립트\n'
            script_content += '# 이 스크립트를 실행하기 전에 내용을 검토하세요\n\n'
            script_content += '\n'.join(fix_commands)
            
            with open('fix_aws_issues.sh', 'w') as f:
                f.write(script_content)
            
            os.chmod('fix_aws_issues.sh', 0o755)
            self.diagnostic_results['fix_script'] = 'fix_aws_issues.sh'
    
    def print_diagnostic_report(self):
        """진단 보고서 출력"""
        print("\n" + "="*60)
        print("🔍 AWS 워크샵 문제 진단 보고서")
        print("="*60)
        print(f"📅 진단 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        issues = self.diagnostic_results['issues_found']
        if not issues:
            print("\n✅ 문제가 발견되지 않았습니다!")
            return True
        
        # 심각도별 분류
        critical_issues = [i for i in issues if i['severity'] == 'CRITICAL']
        high_issues = [i for i in issues if i['severity'] == 'HIGH']
        medium_issues = [i for i in issues if i['severity'] == 'MEDIUM']
        low_issues = [i for i in issues if i['severity'] == 'LOW']
        
        print(f"\n📊 발견된 문제: {len(issues)}개")
        print(f"   🔴 심각: {len(critical_issues)}개")
        print(f"   🟠 높음: {len(high_issues)}개")
        print(f"   🟡 보통: {len(medium_issues)}개")
        print(f"   🟢 낮음: {len(low_issues)}개")
        
        # 문제 상세 출력
        for severity, severity_issues, icon in [
            ('CRITICAL', critical_issues, '🔴'),
            ('HIGH', high_issues, '🟠'),
            ('MEDIUM', medium_issues, '🟡'),
            ('LOW', low_issues, '🟢')
        ]:
            if severity_issues:
                print(f"\n{icon} {severity} 문제:")
                for issue in severity_issues:
                    print(f"   • {issue['description']}")
                    print(f"     💡 해결방법: {issue['recommendation']}")
        
        # 권장사항 요약
        if self.diagnostic_results['recommendations']:
            print(f"\n🔧 주요 권장사항:")
            for i, rec in enumerate(self.diagnostic_results['recommendations'][:5], 1):
                print(f"   {i}. {rec}")
        
        # 자동 수정 스크립트
        if self.diagnostic_results.get('fix_script'):
            print(f"\n🤖 자동 수정 스크립트가 생성되었습니다: {self.diagnostic_results['fix_script']}")
            print("   스크립트를 검토한 후 실행하세요: bash fix_aws_issues.sh")
        
        print("\n" + "="*60)
        
        return len(critical_issues) == 0 and len(high_issues) == 0

def main():
    parser = argparse.ArgumentParser(description='AWS 워크샵 문제 자동 진단 도구')
    parser.add_argument('--profile', help='AWS 프로필 이름')
    parser.add_argument('--region', default='us-east-1', help='AWS 리전 (기본값: us-east-1)')
    parser.add_argument('--bucket', help='확인할 S3 버킷 이름')
    parser.add_argument('--output', help='결과를 JSON 파일로 저장')
    parser.add_argument('--fix', action='store_true', help='자동 수정 스크립트 생성')
    parser.add_argument('--quiet', action='store_true', help='요약 결과만 출력')
    
    args = parser.parse_args()
    
    # 진단기 생성 및 실행
    diagnostic = IssueDiagnostic(profile_name=args.profile, region=args.region)
    
    print("🔍 AWS 워크샵 환경을 진단하는 중...\n")
    
    # 각 항목 진단
    diagnostic.check_system_requirements()
    diagnostic.setup_session()
    diagnostic.check_aws_credentials()
    diagnostic.check_network_connectivity()
    diagnostic.check_service_permissions(args.bucket)
    diagnostic.check_common_issues(args.bucket)
    
    # 자동 수정 스크립트 생성
    if args.fix:
        diagnostic.generate_fix_script()
    
    # 결과 출력
    if not args.quiet:
        is_healthy = diagnostic.print_diagnostic_report()
    else:
        issues = diagnostic.diagnostic_results['issues_found']
        critical_count = len([i for i in issues if i['severity'] == 'CRITICAL'])
        high_count = len([i for i in issues if i['severity'] == 'HIGH'])
        print(f"진단 완료: {len(issues)}개 문제 발견 (심각: {critical_count}, 높음: {high_count})")
        is_healthy = critical_count == 0 and high_count == 0
    
    # JSON 파일로 저장
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(diagnostic.diagnostic_results, f, indent=2, ensure_ascii=False)
        print(f"\n결과가 {args.output}에 저장되었습니다.")
    
    # 종료 코드 설정
    sys.exit(0 if is_healthy else 1)

if __name__ == '__main__':
    main()