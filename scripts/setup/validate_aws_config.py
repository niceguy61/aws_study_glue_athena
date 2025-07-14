#!/usr/bin/env python3
"""
AWS 워크샵 설정 검증 스크립트
AWS 계정 설정, 권한, 리소스 상태를 자동으로 확인합니다.
"""

import boto3
import json
import sys
from botocore.exceptions import ClientError, NoCredentialsError, ProfileNotFound
from datetime import datetime
import argparse

class AWSConfigValidator:
    def __init__(self, profile_name=None, region='us-east-1'):
        """AWS 설정 검증기 초기화"""
        self.profile_name = profile_name
        self.region = region
        self.session = None
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'checks': [],
            'summary': {'passed': 0, 'failed': 0, 'warnings': 0}
        }
        
    def setup_session(self):
        """AWS 세션 설정"""
        try:
            if self.profile_name:
                self.session = boto3.Session(profile_name=self.profile_name, region_name=self.region)
            else:
                self.session = boto3.Session(region_name=self.region)
            return True
        except ProfileNotFound:
            self.add_result('AWS Profile', 'FAILED', f'Profile "{self.profile_name}" not found')
            return False
        except Exception as e:
            self.add_result('AWS Session', 'FAILED', f'Failed to create session: {str(e)}')
            return False
    
    def add_result(self, check_name, status, message, details=None):
        """검증 결과 추가"""
        result = {
            'check': check_name,
            'status': status,
            'message': message,
            'timestamp': datetime.now().isoformat()
        }
        if details:
            result['details'] = details
            
        self.results['checks'].append(result)
        
        if status == 'PASSED':
            self.results['summary']['passed'] += 1
        elif status == 'FAILED':
            self.results['summary']['failed'] += 1
        else:
            self.results['summary']['warnings'] += 1
    
    def check_credentials(self):
        """AWS 자격 증명 확인"""
        try:
            sts = self.session.client('sts')
            identity = sts.get_caller_identity()
            
            self.add_result(
                'AWS Credentials', 
                'PASSED', 
                'AWS credentials are valid',
                {
                    'account_id': identity.get('Account'),
                    'user_arn': identity.get('Arn'),
                    'user_id': identity.get('UserId')
                }
            )
            return True
            
        except NoCredentialsError:
            self.add_result('AWS Credentials', 'FAILED', 'No AWS credentials found. Run "aws configure" to set up credentials.')
            return False
        except ClientError as e:
            self.add_result('AWS Credentials', 'FAILED', f'Invalid credentials: {e.response["Error"]["Message"]}')
            return False
    
    def check_s3_permissions(self, bucket_name=None):
        """S3 권한 확인"""
        s3 = self.session.client('s3')
        
        try:
            # S3 버킷 목록 조회 권한 확인
            s3.list_buckets()
            self.add_result('S3 List Buckets', 'PASSED', 'Can list S3 buckets')
            
            # 특정 버킷이 지정된 경우 해당 버킷 권한 확인
            if bucket_name:
                try:
                    s3.head_bucket(Bucket=bucket_name)
                    self.add_result(f'S3 Bucket Access ({bucket_name})', 'PASSED', f'Can access bucket {bucket_name}')
                    
                    # 버킷 내 객체 목록 조회 권한 확인
                    try:
                        s3.list_objects_v2(Bucket=bucket_name, MaxKeys=1)
                        self.add_result(f'S3 List Objects ({bucket_name})', 'PASSED', f'Can list objects in {bucket_name}')
                    except ClientError as e:
                        if e.response['Error']['Code'] == 'AccessDenied':
                            self.add_result(f'S3 List Objects ({bucket_name})', 'FAILED', 'No permission to list objects')
                        else:
                            self.add_result(f'S3 List Objects ({bucket_name})', 'WARNING', f'Error: {e.response["Error"]["Message"]}')
                            
                except ClientError as e:
                    if e.response['Error']['Code'] == 'NoSuchBucket':
                        self.add_result(f'S3 Bucket ({bucket_name})', 'WARNING', f'Bucket {bucket_name} does not exist')
                    else:
                        self.add_result(f'S3 Bucket ({bucket_name})', 'FAILED', f'Cannot access bucket: {e.response["Error"]["Message"]}')
                        
        except ClientError as e:
            self.add_result('S3 Permissions', 'FAILED', f'No S3 permissions: {e.response["Error"]["Message"]}')
    
    def check_glue_permissions(self):
        """Glue 권한 확인"""
        glue = self.session.client('glue')
        
        try:
            # Glue 데이터베이스 목록 조회
            glue.get_databases()
            self.add_result('Glue Permissions', 'PASSED', 'Can access Glue service')
            
            # Glue 크롤러 목록 조회
            try:
                glue.get_crawlers()
                self.add_result('Glue Crawlers', 'PASSED', 'Can list Glue crawlers')
            except ClientError as e:
                self.add_result('Glue Crawlers', 'WARNING', f'Limited crawler access: {e.response["Error"]["Message"]}')
                
            # Glue 작업 목록 조회
            try:
                glue.get_jobs()
                self.add_result('Glue Jobs', 'PASSED', 'Can list Glue jobs')
            except ClientError as e:
                self.add_result('Glue Jobs', 'WARNING', f'Limited job access: {e.response["Error"]["Message"]}')
                
        except ClientError as e:
            self.add_result('Glue Permissions', 'FAILED', f'No Glue permissions: {e.response["Error"]["Message"]}')
    
    def check_athena_permissions(self):
        """Athena 권한 확인"""
        athena = self.session.client('athena')
        
        try:
            # Athena 쿼리 실행 기록 조회
            athena.list_query_executions(MaxResults=1)
            self.add_result('Athena Permissions', 'PASSED', 'Can access Athena service')
            
            # 워크그룹 목록 조회
            try:
                athena.list_work_groups()
                self.add_result('Athena WorkGroups', 'PASSED', 'Can list Athena work groups')
            except ClientError as e:
                self.add_result('Athena WorkGroups', 'WARNING', f'Limited work group access: {e.response["Error"]["Message"]}')
                
        except ClientError as e:
            self.add_result('Athena Permissions', 'FAILED', f'No Athena permissions: {e.response["Error"]["Message"]}')
    
    def check_iam_role(self, role_name):
        """특정 IAM 역할 확인"""
        iam = self.session.client('iam')
        
        try:
            role = iam.get_role(RoleName=role_name)
            self.add_result(f'IAM Role ({role_name})', 'PASSED', f'Role {role_name} exists')
            
            # 역할에 연결된 정책 확인
            try:
                attached_policies = iam.list_attached_role_policies(RoleName=role_name)
                policy_names = [p['PolicyName'] for p in attached_policies['AttachedPolicies']]
                
                self.add_result(
                    f'IAM Role Policies ({role_name})', 
                    'PASSED', 
                    f'Role has {len(policy_names)} attached policies',
                    {'policies': policy_names}
                )
            except ClientError as e:
                self.add_result(f'IAM Role Policies ({role_name})', 'WARNING', f'Cannot list policies: {e.response["Error"]["Message"]}')
                
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchEntity':
                self.add_result(f'IAM Role ({role_name})', 'WARNING', f'Role {role_name} does not exist')
            else:
                self.add_result(f'IAM Role ({role_name})', 'FAILED', f'Cannot access role: {e.response["Error"]["Message"]}')
    
    def check_region_services(self):
        """현재 리전에서 서비스 가용성 확인"""
        # 각 서비스 클라이언트 생성 시도
        services = ['s3', 'glue', 'athena']
        
        for service in services:
            try:
                client = self.session.client(service)
                # 간단한 API 호출로 서비스 가용성 확인
                if service == 's3':
                    client.list_buckets()
                elif service == 'glue':
                    client.get_databases()
                elif service == 'athena':
                    client.list_work_groups()
                    
                self.add_result(f'{service.upper()} Service', 'PASSED', f'{service.upper()} is available in {self.region}')
                
            except ClientError as e:
                if 'not available' in str(e) or 'not supported' in str(e):
                    self.add_result(f'{service.upper()} Service', 'FAILED', f'{service.upper()} not available in {self.region}')
                else:
                    self.add_result(f'{service.upper()} Service', 'PASSED', f'{service.upper()} is available (permission check failed)')
    
    def run_all_checks(self, bucket_name=None, glue_role_name=None):
        """모든 검증 실행"""
        print("🔍 AWS 워크샵 설정 검증을 시작합니다...\n")
        
        # AWS 세션 설정
        if not self.setup_session():
            return self.results
        
        # 기본 검증
        print("1️⃣ AWS 자격 증명 확인...")
        if not self.check_credentials():
            return self.results
        
        print("2️⃣ 리전별 서비스 가용성 확인...")
        self.check_region_services()
        
        print("3️⃣ S3 권한 확인...")
        self.check_s3_permissions(bucket_name)
        
        print("4️⃣ Glue 권한 확인...")
        self.check_glue_permissions()
        
        print("5️⃣ Athena 권한 확인...")
        self.check_athena_permissions()
        
        # IAM 역할 확인 (선택사항)
        if glue_role_name:
            print(f"6️⃣ IAM 역할 확인 ({glue_role_name})...")
            self.check_iam_role(glue_role_name)
        
        return self.results
    
    def print_results(self):
        """검증 결과 출력"""
        print("\n" + "="*60)
        print("🎯 AWS 설정 검증 결과")
        print("="*60)
        
        # 요약 정보
        summary = self.results['summary']
        total = summary['passed'] + summary['failed'] + summary['warnings']
        
        print(f"\n📊 요약:")
        print(f"   ✅ 통과: {summary['passed']}/{total}")
        print(f"   ❌ 실패: {summary['failed']}/{total}")
        print(f"   ⚠️  경고: {summary['warnings']}/{total}")
        
        # 상세 결과
        print(f"\n📋 상세 결과:")
        for check in self.results['checks']:
            status_icon = "✅" if check['status'] == 'PASSED' else "❌" if check['status'] == 'FAILED' else "⚠️"
            print(f"   {status_icon} {check['check']}: {check['message']}")
            
            if check.get('details'):
                for key, value in check['details'].items():
                    if isinstance(value, list):
                        print(f"      - {key}: {', '.join(value)}")
                    else:
                        print(f"      - {key}: {value}")
        
        # 권장사항
        if summary['failed'] > 0:
            print(f"\n🔧 권장사항:")
            print("   - AWS CLI 설정 확인: aws configure list")
            print("   - IAM 권한 확인: AWS 콘솔에서 사용자 권한 검토")
            print("   - 문제 해결 가이드 참조: docs/06-troubleshooting.md")
        
        print("\n" + "="*60)
        
        return summary['failed'] == 0

def main():
    parser = argparse.ArgumentParser(description='AWS 워크샵 설정 검증 도구')
    parser.add_argument('--profile', help='AWS 프로필 이름')
    parser.add_argument('--region', default='us-east-1', help='AWS 리전 (기본값: us-east-1)')
    parser.add_argument('--bucket', help='확인할 S3 버킷 이름')
    parser.add_argument('--glue-role', help='확인할 Glue IAM 역할 이름')
    parser.add_argument('--output', help='결과를 JSON 파일로 저장')
    parser.add_argument('--quiet', action='store_true', help='요약 결과만 출력')
    
    args = parser.parse_args()
    
    # 검증기 생성 및 실행
    validator = AWSConfigValidator(profile_name=args.profile, region=args.region)
    results = validator.run_all_checks(bucket_name=args.bucket, glue_role_name=args.glue_role)
    
    # 결과 출력
    if not args.quiet:
        success = validator.print_results()
    else:
        summary = results['summary']
        print(f"검증 완료: {summary['passed']}개 통과, {summary['failed']}개 실패, {summary['warnings']}개 경고")
        success = summary['failed'] == 0
    
    # JSON 파일로 저장
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"\n결과가 {args.output}에 저장되었습니다.")
    
    # 종료 코드 설정
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()