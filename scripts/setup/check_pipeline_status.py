#!/usr/bin/env python3
"""
데이터 파이프라인 상태 확인 스크립트
S3, Glue, Athena 리소스의 상태를 확인하고 파이프라인 진행 상황을 추적합니다.
"""

import boto3
import json
import sys
from botocore.exceptions import ClientError, NoCredentialsError
from datetime import datetime, timedelta
import argparse
from tabulate import tabulate

class PipelineStatusChecker:
    def __init__(self, profile_name=None, region='us-east-1'):
        """파이프라인 상태 확인기 초기화"""
        self.profile_name = profile_name
        self.region = region
        self.session = None
        self.status_report = {
            'timestamp': datetime.now().isoformat(),
            's3_status': {},
            'glue_status': {},
            'athena_status': {},
            'pipeline_health': 'UNKNOWN'
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
            print(f"❌ AWS 세션 생성 실패: {str(e)}")
            return False
    
    def check_s3_resources(self, bucket_name):
        """S3 리소스 상태 확인"""
        s3 = self.session.client('s3')
        s3_status = {
            'bucket_exists': False,
            'raw_data_count': 0,
            'processed_data_count': 0,
            'total_size_mb': 0,
            'folders': []
        }
        
        try:
            # 버킷 존재 확인
            s3.head_bucket(Bucket=bucket_name)
            s3_status['bucket_exists'] = True
            
            # 버킷 내 객체 목록 조회
            paginator = s3.get_paginator('list_objects_v2')
            total_size = 0
            folders = set()
            raw_count = 0
            processed_count = 0
            
            for page in paginator.paginate(Bucket=bucket_name):
                if 'Contents' in page:
                    for obj in page['Contents']:
                        key = obj['Key']
                        size = obj['Size']
                        total_size += size
                        
                        # 폴더 구조 파악
                        if '/' in key:
                            folder = key.split('/')[0]
                            folders.add(folder)
                        
                        # 원본/처리된 데이터 구분
                        if 'raw' in key.lower() or 'source' in key.lower():
                            raw_count += 1
                        elif 'processed' in key.lower() or 'output' in key.lower():
                            processed_count += 1
            
            s3_status.update({
                'raw_data_count': raw_count,
                'processed_data_count': processed_count,
                'total_size_mb': round(total_size / (1024 * 1024), 2),
                'folders': list(folders)
            })
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchBucket':
                s3_status['error'] = f'버킷 {bucket_name}이 존재하지 않습니다'
            else:
                s3_status['error'] = f'S3 접근 오류: {e.response["Error"]["Message"]}'
        
        self.status_report['s3_status'] = s3_status
        return s3_status
    
    def check_glue_resources(self, database_name=None):
        """Glue 리소스 상태 확인"""
        glue = self.session.client('glue')
        glue_status = {
            'databases': [],
            'tables': [],
            'crawlers': [],
            'jobs': [],
            'recent_runs': []
        }
        
        try:
            # 데이터베이스 목록 조회
            databases = glue.get_databases()
            for db in databases['DatabaseList']:
                db_info = {
                    'name': db['Name'],
                    'description': db.get('Description', ''),
                    'created': db.get('CreateTime', '').isoformat() if db.get('CreateTime') else ''
                }
                glue_status['databases'].append(db_info)
            
            # 특정 데이터베이스의 테이블 조회
            if database_name:
                try:
                    tables = glue.get_tables(DatabaseName=database_name)
                    for table in tables['TableList']:
                        table_info = {
                            'name': table['Name'],
                            'database': table['DatabaseName'],
                            'location': table.get('StorageDescriptor', {}).get('Location', ''),
                            'input_format': table.get('StorageDescriptor', {}).get('InputFormat', ''),
                            'columns': len(table.get('StorageDescriptor', {}).get('Columns', [])),
                            'created': table.get('CreateTime', '').isoformat() if table.get('CreateTime') else ''
                        }
                        glue_status['tables'].append(table_info)
                except ClientError:
                    pass  # 데이터베이스가 없거나 권한 없음
            
            # 크롤러 목록 조회
            crawlers = glue.get_crawlers()
            for crawler in crawlers['Crawlers']:
                crawler_info = {
                    'name': crawler['Name'],
                    'state': crawler['State'],
                    'database': crawler.get('DatabaseName', ''),
                    'last_crawl': crawler.get('LastCrawl', {}).get('StartTime', '').isoformat() if crawler.get('LastCrawl', {}).get('StartTime') else '',
                    'status': crawler.get('LastCrawl', {}).get('Status', 'NEVER_RUN')
                }
                glue_status['crawlers'].append(crawler_info)
            
            # ETL 작업 목록 조회
            jobs = glue.get_jobs()
            for job in jobs['Jobs']:
                job_info = {
                    'name': job['Name'],
                    'role': job['Role'],
                    'created': job.get('CreatedOn', '').isoformat() if job.get('CreatedOn') else '',
                    'last_modified': job.get('LastModifiedOn', '').isoformat() if job.get('LastModifiedOn') else ''
                }
                glue_status['jobs'].append(job_info)
                
                # 최근 작업 실행 기록 조회
                try:
                    runs = glue.get_job_runs(JobName=job['Name'], MaxResults=5)
                    for run in runs['JobRuns']:
                        run_info = {
                            'job_name': job['Name'],
                            'run_id': run['Id'],
                            'state': run['JobRunState'],
                            'started': run.get('StartedOn', '').isoformat() if run.get('StartedOn') else '',
                            'completed': run.get('CompletedOn', '').isoformat() if run.get('CompletedOn') else '',
                            'execution_time': run.get('ExecutionTime', 0)
                        }
                        glue_status['recent_runs'].append(run_info)
                except ClientError:
                    pass
            
        except ClientError as e:
            glue_status['error'] = f'Glue 접근 오류: {e.response["Error"]["Message"]}'
        
        self.status_report['glue_status'] = glue_status
        return glue_status
    
    def check_athena_resources(self, database_name=None):
        """Athena 리소스 상태 확인"""
        athena = self.session.client('athena')
        athena_status = {
            'workgroups': [],
            'recent_queries': [],
            'query_stats': {
                'total_queries': 0,
                'successful_queries': 0,
                'failed_queries': 0,
                'data_scanned_mb': 0
            }
        }
        
        try:
            # 워크그룹 목록 조회
            workgroups = athena.list_work_groups()
            for wg in workgroups['WorkGroups']:
                wg_info = {
                    'name': wg['Name'],
                    'state': wg['State'],
                    'description': wg.get('Description', '')
                }
                athena_status['workgroups'].append(wg_info)
            
            # 최근 쿼리 실행 기록 조회
            queries = athena.list_query_executions(MaxResults=20)
            
            total_queries = 0
            successful_queries = 0
            failed_queries = 0
            total_data_scanned = 0
            
            for query_id in queries['QueryExecutionIds']:
                try:
                    query_detail = athena.get_query_execution(QueryExecutionId=query_id)
                    execution = query_detail['QueryExecution']
                    
                    query_info = {
                        'query_id': query_id,
                        'query': execution['Query'][:100] + '...' if len(execution['Query']) > 100 else execution['Query'],
                        'state': execution['Status']['State'],
                        'database': execution.get('QueryExecutionContext', {}).get('Database', ''),
                        'submission_time': execution['Status'].get('SubmissionDateTime', '').isoformat() if execution['Status'].get('SubmissionDateTime') else '',
                        'completion_time': execution['Status'].get('CompletionDateTime', '').isoformat() if execution['Status'].get('CompletionDateTime') else '',
                        'data_scanned_mb': round(execution.get('Statistics', {}).get('DataScannedInBytes', 0) / (1024 * 1024), 2),
                        'execution_time_ms': execution.get('Statistics', {}).get('EngineExecutionTimeInMillis', 0)
                    }
                    
                    athena_status['recent_queries'].append(query_info)
                    
                    # 통계 집계
                    total_queries += 1
                    if execution['Status']['State'] == 'SUCCEEDED':
                        successful_queries += 1
                    elif execution['Status']['State'] == 'FAILED':
                        failed_queries += 1
                    
                    total_data_scanned += execution.get('Statistics', {}).get('DataScannedInBytes', 0)
                    
                except ClientError:
                    continue
            
            athena_status['query_stats'] = {
                'total_queries': total_queries,
                'successful_queries': successful_queries,
                'failed_queries': failed_queries,
                'data_scanned_mb': round(total_data_scanned / (1024 * 1024), 2)
            }
            
        except ClientError as e:
            athena_status['error'] = f'Athena 접근 오류: {e.response["Error"]["Message"]}'
        
        self.status_report['athena_status'] = athena_status
        return athena_status
    
    def assess_pipeline_health(self):
        """파이프라인 전체 상태 평가"""
        health_score = 0
        max_score = 0
        issues = []
        
        # S3 상태 평가
        s3_status = self.status_report['s3_status']
        if s3_status.get('bucket_exists'):
            health_score += 2
            if s3_status.get('raw_data_count', 0) > 0:
                health_score += 2
            if s3_status.get('processed_data_count', 0) > 0:
                health_score += 2
        else:
            issues.append("S3 버킷이 존재하지 않거나 접근할 수 없습니다")
        max_score += 6
        
        # Glue 상태 평가
        glue_status = self.status_report['glue_status']
        if len(glue_status.get('databases', [])) > 0:
            health_score += 1
        if len(glue_status.get('tables', [])) > 0:
            health_score += 2
        if len(glue_status.get('crawlers', [])) > 0:
            health_score += 1
            # 크롤러 성공 실행 확인
            successful_crawlers = [c for c in glue_status.get('crawlers', []) if c.get('status') == 'SUCCEEDED']
            if successful_crawlers:
                health_score += 1
        if len(glue_status.get('jobs', [])) > 0:
            health_score += 1
            # ETL 작업 성공 실행 확인
            successful_runs = [r for r in glue_status.get('recent_runs', []) if r.get('state') == 'SUCCEEDED']
            if successful_runs:
                health_score += 1
        max_score += 7
        
        # Athena 상태 평가
        athena_status = self.status_report['athena_status']
        query_stats = athena_status.get('query_stats', {})
        if query_stats.get('total_queries', 0) > 0:
            health_score += 1
            success_rate = query_stats.get('successful_queries', 0) / query_stats.get('total_queries', 1)
            if success_rate > 0.8:
                health_score += 2
            elif success_rate > 0.5:
                health_score += 1
        max_score += 3
        
        # 전체 상태 결정
        if max_score == 0:
            health_percentage = 0
        else:
            health_percentage = (health_score / max_score) * 100
        
        if health_percentage >= 80:
            pipeline_health = 'HEALTHY'
        elif health_percentage >= 60:
            pipeline_health = 'WARNING'
        elif health_percentage >= 40:
            pipeline_health = 'DEGRADED'
        else:
            pipeline_health = 'CRITICAL'
        
        self.status_report['pipeline_health'] = pipeline_health
        self.status_report['health_score'] = f"{health_score}/{max_score} ({health_percentage:.1f}%)"
        self.status_report['issues'] = issues
        
        return pipeline_health, health_percentage, issues
    
    def print_status_report(self):
        """상태 보고서 출력"""
        print("🔍 데이터 파이프라인 상태 보고서")
        print("=" * 60)
        print(f"📅 검사 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 전체 상태
        health, percentage, issues = self.assess_pipeline_health()
        health_icon = {
            'HEALTHY': '🟢',
            'WARNING': '🟡',
            'DEGRADED': '🟠',
            'CRITICAL': '🔴'
        }.get(health, '⚪')
        
        print(f"\n🎯 전체 상태: {health_icon} {health} ({self.status_report['health_score']})")
        
        if issues:
            print(f"\n⚠️ 발견된 문제:")
            for issue in issues:
                print(f"   • {issue}")
        
        # S3 상태
        print(f"\n📦 S3 스토리지 상태:")
        s3_status = self.status_report['s3_status']
        if s3_status.get('bucket_exists'):
            print(f"   ✅ 버킷 존재: 예")
            print(f"   📁 폴더 수: {len(s3_status.get('folders', []))}")
            print(f"   📄 원본 파일: {s3_status.get('raw_data_count', 0)}개")
            print(f"   🔄 처리된 파일: {s3_status.get('processed_data_count', 0)}개")
            print(f"   💾 총 크기: {s3_status.get('total_size_mb', 0)} MB")
            if s3_status.get('folders'):
                print(f"   📂 폴더 목록: {', '.join(s3_status['folders'])}")
        else:
            print(f"   ❌ 버킷 상태: {s3_status.get('error', '접근 불가')}")
        
        # Glue 상태
        print(f"\n🔧 Glue ETL 상태:")
        glue_status = self.status_report['glue_status']
        if not glue_status.get('error'):
            print(f"   🗄️ 데이터베이스: {len(glue_status.get('databases', []))}개")
            print(f"   📋 테이블: {len(glue_status.get('tables', []))}개")
            print(f"   🕷️ 크롤러: {len(glue_status.get('crawlers', []))}개")
            print(f"   ⚙️ ETL 작업: {len(glue_status.get('jobs', []))}개")
            
            # 크롤러 상태 상세
            if glue_status.get('crawlers'):
                print(f"\n   크롤러 상세:")
                crawler_data = []
                for crawler in glue_status['crawlers']:
                    crawler_data.append([
                        crawler['name'],
                        crawler['state'],
                        crawler.get('status', 'N/A'),
                        crawler.get('last_crawl', 'Never')[:19] if crawler.get('last_crawl') else 'Never'
                    ])
                print("   " + tabulate(crawler_data, headers=['이름', '상태', '마지막 실행', '실행 시간'], tablefmt='simple'))
            
            # 최근 ETL 실행 기록
            if glue_status.get('recent_runs'):
                print(f"\n   최근 ETL 실행 기록:")
                run_data = []
                for run in glue_status['recent_runs'][:5]:  # 최근 5개만
                    run_data.append([
                        run['job_name'],
                        run['state'],
                        run.get('started', 'N/A')[:19] if run.get('started') else 'N/A',
                        f"{run.get('execution_time', 0)}초"
                    ])
                print("   " + tabulate(run_data, headers=['작업명', '상태', '시작 시간', '실행 시간'], tablefmt='simple'))
        else:
            print(f"   ❌ Glue 상태: {glue_status['error']}")
        
        # Athena 상태
        print(f"\n🔍 Athena 쿼리 상태:")
        athena_status = self.status_report['athena_status']
        if not athena_status.get('error'):
            stats = athena_status.get('query_stats', {})
            print(f"   📊 총 쿼리 수: {stats.get('total_queries', 0)}개")
            print(f"   ✅ 성공한 쿼리: {stats.get('successful_queries', 0)}개")
            print(f"   ❌ 실패한 쿼리: {stats.get('failed_queries', 0)}개")
            print(f"   📈 스캔한 데이터: {stats.get('data_scanned_mb', 0)} MB")
            
            # 최근 쿼리 기록
            if athena_status.get('recent_queries'):
                print(f"\n   최근 쿼리 기록:")
                query_data = []
                for query in athena_status['recent_queries'][:5]:  # 최근 5개만
                    query_data.append([
                        query['query'][:50] + '...' if len(query['query']) > 50 else query['query'],
                        query['state'],
                        query.get('database', 'N/A'),
                        f"{query.get('data_scanned_mb', 0)} MB"
                    ])
                print("   " + tabulate(query_data, headers=['쿼리', '상태', '데이터베이스', '스캔 데이터'], tablefmt='simple'))
        else:
            print(f"   ❌ Athena 상태: {athena_status['error']}")
        
        print("\n" + "=" * 60)
        
        return health == 'HEALTHY'

def main():
    parser = argparse.ArgumentParser(description='데이터 파이프라인 상태 확인 도구')
    parser.add_argument('--profile', help='AWS 프로필 이름')
    parser.add_argument('--region', default='us-east-1', help='AWS 리전 (기본값: us-east-1)')
    parser.add_argument('--bucket', required=True, help='확인할 S3 버킷 이름')
    parser.add_argument('--database', help='확인할 Glue 데이터베이스 이름')
    parser.add_argument('--output', help='결과를 JSON 파일로 저장')
    parser.add_argument('--quiet', action='store_true', help='요약 결과만 출력')
    
    args = parser.parse_args()
    
    # 상태 확인기 생성 및 실행
    checker = PipelineStatusChecker(profile_name=args.profile, region=args.region)
    
    if not checker.setup_session():
        sys.exit(1)
    
    print("🔍 데이터 파이프라인 상태를 확인하는 중...\n")
    
    # 각 서비스 상태 확인
    checker.check_s3_resources(args.bucket)
    checker.check_glue_resources(args.database)
    checker.check_athena_resources(args.database)
    
    # 결과 출력
    if not args.quiet:
        is_healthy = checker.print_status_report()
    else:
        health, percentage, issues = checker.assess_pipeline_health()
        print(f"파이프라인 상태: {health} ({percentage:.1f}%)")
        if issues:
            print(f"문제: {len(issues)}개 발견")
        is_healthy = health == 'HEALTHY'
    
    # JSON 파일로 저장
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(checker.status_report, f, indent=2, ensure_ascii=False)
        print(f"\n결과가 {args.output}에 저장되었습니다.")
    
    # 종료 코드 설정
    sys.exit(0 if is_healthy else 1)

if __name__ == '__main__':
    main()