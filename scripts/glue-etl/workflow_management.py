#!/usr/bin/env python3
"""
AWS Glue 워크플로우 관리 스크립트
복잡한 ETL 파이프라인의 자동화 및 관리
"""

import boto3
import json
import time
from datetime import datetime, timedelta
from botocore.exceptions import ClientError

class GlueWorkflowManager:
    """Glue 워크플로우 관리 클래스"""
    
    def __init__(self, region_name='us-east-1'):
        self.glue_client = boto3.client('glue', region_name=region_name)
        self.events_client = boto3.client('events', region_name=region_name)
        self.sns_client = boto3.client('sns', region_name=region_name)
        self.region_name = region_name
    
    def create_etl_workflow(self, workflow_name, description="", default_properties=None):
        """ETL 워크플로우 생성"""
        if default_properties is None:
            default_properties = {
                'S3_BUCKET': 'your-workshop-bucket',
                'DATABASE_NAME': 'workshop_database',
                'REGION': self.region_name
            }
        
        try:
            response = self.glue_client.create_workflow(
                Name=workflow_name,
                Description=description,
                DefaultRunProperties=default_properties,
                Tags={
                    'Project': 'AWS-Data-Analysis-Workshop',
                    'Environment': 'Development',
                    'CreatedBy': 'WorkflowManager'
                }
            )
            print(f"✓ 워크플로우 '{workflow_name}' 생성 완료")
            return response
        except ClientError as e:
            if e.response['Error']['Code'] == 'AlreadyExistsException':
                print(f"⚠ 워크플로우 '{workflow_name}'가 이미 존재합니다")
                return None
            else:
                print(f"❌ 워크플로우 생성 실패: {str(e)}")
                raise
    
    def create_glue_job(self, job_name, script_location, role_arn, 
                       job_type="glueetl", glue_version="4.0"):
        """Glue 작업 생성"""
        job_config = {
            'Name': job_name,
            'Role': role_arn,
            'Command': {
                'Name': job_type,
                'ScriptLocation': script_location,
                'PythonVersion': '3'
            },
            'DefaultArguments': {
                '--TempDir': f's3://your-workshop-bucket/temp/',
                '--job-bookmark-option': 'job-bookmark-enable',
                '--enable-metrics': 'true',
                '--enable-spark-ui': 'true',
                '--spark-event-logs-path': f's3://your-workshop-bucket/spark-logs/'
            },
            'MaxRetries': 2,
            'Timeout': 2880,  # 48시간
            'GlueVersion': glue_version,
            'MaxCapacity': 2.0,
            'Tags': {
                'Project': 'AWS-Data-Analysis-Workshop',
                'Environment': 'Development'
            }
        }
        
        try:
            response = self.glue_client.create_job(**job_config)
            print(f"✓ Glue 작업 '{job_name}' 생성 완료")
            return response
        except ClientError as e:
            if e.response['Error']['Code'] == 'AlreadyExistsException':
                print(f"⚠ 작업 '{job_name}'이 이미 존재합니다")
                return None
            else:
                print(f"❌ 작업 생성 실패: {str(e)}")
                raise
    
    def create_job_trigger(self, trigger_name, workflow_name, job_names, 
                          trigger_type="ON_DEMAND", schedule=None, description=""):
        """작업 트리거 생성"""
        trigger_config = {
            'Name': trigger_name,
            'WorkflowName': workflow_name,
            'Type': trigger_type,
            'Description': description,
            'Actions': [{'JobName': job_name} for job_name in job_names],
            'Tags': {
                'Project': 'AWS-Data-Analysis-Workshop',
                'WorkflowName': workflow_name
            }
        }
        
        if trigger_type == "SCHEDULED" and schedule:
            trigger_config['Schedule'] = schedule
        
        try:
            response = self.glue_client.create_trigger(**trigger_config)
            print(f"✓ 트리거 '{trigger_name}' 생성 완료")
            return response
        except ClientError as e:
            if e.response['Error']['Code'] == 'AlreadyExistsException':
                print(f"⚠ 트리거 '{trigger_name}'이 이미 존재합니다")
                return None
            else:
                print(f"❌ 트리거 생성 실패: {str(e)}")
                raise
    
    def create_conditional_trigger(self, trigger_name, workflow_name, 
                                 predecessor_jobs, successor_jobs, 
                                 logical_operator="AND"):
        """조건부 트리거 생성 (이전 작업 완료 후 실행)"""
        conditions = []
        for job_name in predecessor_jobs:
            conditions.append({
                'LogicalOperator': 'EQUALS',
                'JobName': job_name,
                'State': 'SUCCEEDED'
            })
        
        predicate = {
            'Logical': logical_operator,
            'Conditions': conditions
        } if len(conditions) > 1 else {
            'Conditions': conditions
        }
        
        try:
            response = self.glue_client.create_trigger(
                Name=trigger_name,
                WorkflowName=workflow_name,
                Type='CONDITIONAL',
                Predicate=predicate,
                Actions=[{'JobName': job_name} for job_name in successor_jobs],
                Description=f"Conditional trigger: {' & '.join(predecessor_jobs)} -> {' & '.join(successor_jobs)}",
                Tags={
                    'Project': 'AWS-Data-Analysis-Workshop',
                    'WorkflowName': workflow_name,
                    'TriggerType': 'Conditional'
                }
            )
            print(f"✓ 조건부 트리거 '{trigger_name}' 생성 완료")
            return response
        except ClientError as e:
            if e.response['Error']['Code'] == 'AlreadyExistsException':
                print(f"⚠ 트리거 '{trigger_name}'이 이미 존재합니다")
                return None
            else:
                print(f"❌ 조건부 트리거 생성 실패: {str(e)}")
                raise
    
    def setup_complete_workflow(self, workflow_name="student-data-analysis-workflow", 
                              role_arn=None):
        """완전한 ETL 워크플로우 설정"""
        if role_arn is None:
            print("❌ IAM 역할 ARN이 필요합니다")
            return None
        
        print(f"=== {workflow_name} 워크플로우 설정 시작 ===")
        
        # 1. 워크플로우 생성
        self.create_etl_workflow(
            workflow_name, 
            "학생 데이터 분석을 위한 완전한 ETL 파이프라인"
        )
        
        # 2. 작업 정의 및 생성
        jobs_config = [
            {
                'name': 'data-quality-check',
                'script': 's3://your-workshop-bucket/scripts/glue-etl/data_quality_validator.py',
                'description': '데이터 품질 검증 작업'
            },
            {
                'name': 'advanced-etl-processing',
                'script': 's3://your-workshop-bucket/scripts/glue-etl/advanced_multi_source_etl.py',
                'description': '고급 ETL 처리 작업'
            },
            {
                'name': 'custom-transformations',
                'script': 's3://your-workshop-bucket/scripts/glue-etl/custom_transform_job.py',
                'description': '커스텀 변환 적용 작업'
            }
        ]
        
        # 작업 생성
        for job_config in jobs_config:
            self.create_glue_job(
                job_config['name'],
                job_config['script'],
                role_arn
            )
        
        # 3. 트리거 생성
        # 시작 트리거 (수동)
        self.create_job_trigger(
            'start-quality-check',
            workflow_name,
            ['data-quality-check'],
            'ON_DEMAND',
            description="워크플로우 시작 트리거"
        )
        
        # 품질 검사 → ETL 처리
        self.create_conditional_trigger(
            'quality-to-etl',
            workflow_name,
            ['data-quality-check'],
            ['advanced-etl-processing']
        )
        
        # ETL 처리 → 커스텀 변환
        self.create_conditional_trigger(
            'etl-to-transform',
            workflow_name,
            ['advanced-etl-processing'],
            ['custom-transformations']
        )
        
        print(f"✓ 완전한 워크플로우 '{workflow_name}' 설정 완료")
        return workflow_name
    
    def schedule_workflow(self, workflow_name, schedule_expression, 
                         trigger_name=None, start_job_name=None):
        """워크플로우 스케줄링"""
        if trigger_name is None:
            trigger_name = f"{workflow_name}-scheduled-trigger"
        
        if start_job_name is None:
            # 워크플로우의 첫 번째 작업 찾기
            try:
                workflow_info = self.glue_client.get_workflow(Name=workflow_name)
                triggers = self.glue_client.get_triggers()['TriggerList']
                workflow_triggers = [t for t in triggers if t.get('WorkflowName') == workflow_name]
                
                # ON_DEMAND 트리거에서 시작 작업 찾기
                for trigger in workflow_triggers:
                    if trigger['Type'] == 'ON_DEMAND' and trigger.get('Actions'):
                        start_job_name = trigger['Actions'][0]['JobName']
                        break
                
                if not start_job_name:
                    print("❌ 시작 작업을 찾을 수 없습니다")
                    return None
                    
            except Exception as e:
                print(f"❌ 워크플로우 정보 조회 실패: {str(e)}")
                return None
        
        # 스케줄 트리거 생성
        return self.create_job_trigger(
            trigger_name,
            workflow_name,
            [start_job_name],
            'SCHEDULED',
            schedule_expression,
            f"Scheduled trigger for {workflow_name}"
        )
    
    def start_workflow_run(self, workflow_name, run_properties=None):
        """워크플로우 실행 시작"""
        try:
            if run_properties is None:
                run_properties = {}
            
            response = self.glue_client.start_workflow_run(
                Name=workflow_name,
                RunProperties=run_properties
            )
            
            run_id = response['RunId']
            print(f"✓ 워크플로우 실행 시작: {run_id}")
            return run_id
            
        except Exception as e:
            print(f"❌ 워크플로우 실행 실패: {str(e)}")
            return None
    
    def monitor_workflow_runs(self, workflow_name, max_runs=10, detailed=False):
        """워크플로우 실행 모니터링"""
        try:
            response = self.glue_client.get_workflow_runs(
                Name=workflow_name,
                MaxResults=max_runs
            )
            
            print(f"=== {workflow_name} 실행 이력 ===")
            
            if not response.get('Runs'):
                print("실행 이력이 없습니다.")
                return []
            
            for i, run in enumerate(response['Runs']):
                run_id = run['WorkflowRunId']
                status = run['Status']
                start_time = run.get('StartedOn', 'N/A')
                end_time = run.get('CompletedOn', 'N/A')
                
                print(f"\n{i+1}. Run ID: {run_id}")
                print(f"   Status: {status}")
                print(f"   Started: {start_time}")
                print(f"   Completed: {end_time}")
                
                if 'Statistics' in run:
                    stats = run['Statistics']
                    print(f"   Total Actions: {stats.get('TotalActions', 0)}")
                    print(f"   Succeeded: {stats.get('SucceededActions', 0)}")
                    print(f"   Failed: {stats.get('FailedActions', 0)}")
                    print(f"   Running: {stats.get('RunningActions', 0)}")
                
                # 상세 정보 표시
                if detailed and 'Graph' in run:
                    print("   Job Details:")
                    for node in run['Graph'].get('Nodes', []):
                        if node['Type'] == 'JOB':
                            job_name = node['Name']
                            job_status = node.get('JobDetails', {}).get('JobRuns', [{}])[0].get('JobRunState', 'UNKNOWN')
                            print(f"     - {job_name}: {job_status}")
            
            return response['Runs']
            
        except Exception as e:
            print(f"❌ 워크플로우 모니터링 실패: {str(e)}")
            return []
    
    def get_workflow_status(self, workflow_name, run_id=None):
        """워크플로우 상태 조회"""
        try:
            if run_id:
                # 특정 실행의 상태 조회
                response = self.glue_client.get_workflow_run(
                    Name=workflow_name,
                    RunId=run_id
                )
                return response['Run']['Status']
            else:
                # 최신 실행의 상태 조회
                runs = self.glue_client.get_workflow_runs(
                    Name=workflow_name,
                    MaxResults=1
                )
                if runs['Runs']:
                    return runs['Runs'][0]['Status']
                else:
                    return 'NO_RUNS'
                    
        except Exception as e:
            print(f"❌ 워크플로우 상태 조회 실패: {str(e)}")
            return 'ERROR'
    
    def stop_workflow_run(self, workflow_name, run_id):
        """워크플로우 실행 중지"""
        try:
            response = self.glue_client.stop_workflow_run(
                Name=workflow_name,
                RunId=run_id
            )
            print(f"✓ 워크플로우 실행 중지: {run_id}")
            return response
        except Exception as e:
            print(f"❌ 워크플로우 중지 실패: {str(e)}")
            return None
    
    def delete_workflow(self, workflow_name, force=False):
        """워크플로우 삭제"""
        try:
            if not force:
                # 실행 중인 작업이 있는지 확인
                status = self.get_workflow_status(workflow_name)
                if status == 'RUNNING':
                    print(f"⚠ 워크플로우가 실행 중입니다. force=True로 강제 삭제하거나 실행 완료 후 삭제하세요.")
                    return False
            
            # 트리거 먼저 삭제
            triggers = self.glue_client.get_triggers()['TriggerList']
            workflow_triggers = [t for t in triggers if t.get('WorkflowName') == workflow_name]
            
            for trigger in workflow_triggers:
                self.glue_client.delete_trigger(Name=trigger['Name'])
                print(f"✓ 트리거 삭제: {trigger['Name']}")
            
            # 워크플로우 삭제
            self.glue_client.delete_workflow(Name=workflow_name)
            print(f"✓ 워크플로우 삭제: {workflow_name}")
            return True
            
        except Exception as e:
            print(f"❌ 워크플로우 삭제 실패: {str(e)}")
            return False

class WorkflowNotificationManager:
    """워크플로우 알림 관리 클래스"""
    
    def __init__(self, region_name='us-east-1'):
        self.sns_client = boto3.client('sns', region_name=region_name)
        self.events_client = boto3.client('events', region_name=region_name)
        self.cloudwatch_client = boto3.client('cloudwatch', region_name=region_name)
    
    def create_notification_topic(self, topic_name, email_addresses):
        """알림용 SNS 토픽 생성"""
        try:
            # 토픽 생성
            response = self.sns_client.create_topic(Name=topic_name)
            topic_arn = response['TopicArn']
            
            # 이메일 구독 추가
            for email in email_addresses:
                self.sns_client.subscribe(
                    TopicArn=topic_arn,
                    Protocol='email',
                    Endpoint=email
                )
                print(f"✓ 이메일 구독 추가: {email}")
            
            print(f"✓ 알림 토픽 생성: {topic_arn}")
            return topic_arn
            
        except Exception as e:
            print(f"❌ 알림 토픽 생성 실패: {str(e)}")
            return None
    
    def setup_workflow_alarms(self, workflow_name, topic_arn):
        """워크플로우 알람 설정"""
        alarms = [
            {
                'name': f'{workflow_name}-job-failures',
                'description': 'Glue 작업 실패 알람',
                'metric_name': 'glue.driver.aggregate.numFailedTasks',
                'threshold': 1,
                'comparison': 'GreaterThanThreshold'
            },
            {
                'name': f'{workflow_name}-long-running',
                'description': '장시간 실행 작업 알람',
                'metric_name': 'glue.driver.aggregate.elapsedTime',
                'threshold': 7200,  # 2시간
                'comparison': 'GreaterThanThreshold'
            }
        ]
        
        for alarm in alarms:
            try:
                self.cloudwatch_client.put_metric_alarm(
                    AlarmName=alarm['name'],
                    ComparisonOperator=alarm['comparison'],
                    EvaluationPeriods=1,
                    MetricName=alarm['metric_name'],
                    Namespace='AWS/Glue',
                    Period=300,
                    Statistic='Sum',
                    Threshold=alarm['threshold'],
                    ActionsEnabled=True,
                    AlarmActions=[topic_arn],
                    AlarmDescription=alarm['description'],
                    Dimensions=[
                        {
                            'Name': 'JobName',
                            'Value': workflow_name
                        }
                    ]
                )
                print(f"✓ 알람 설정: {alarm['name']}")
                
            except Exception as e:
                print(f"❌ 알람 설정 실패: {str(e)}")

def main():
    """메인 실행 함수 - 워크플로우 설정 예제"""
    print("=== AWS Glue 워크플로우 관리 도구 ===\n")
    
    # 워크플로우 매니저 초기화
    manager = GlueWorkflowManager()
    
    # IAM 역할 ARN (실제 값으로 변경 필요)
    role_arn = "arn:aws:iam::123456789012:role/GlueServiceRole"
    
    try:
        # 1. 완전한 워크플로우 설정
        workflow_name = manager.setup_complete_workflow(
            "student-data-analysis-workflow", 
            role_arn
        )
        
        if workflow_name:
            # 2. 일일 스케줄 설정 (새벽 2시)
            schedule_expression = "cron(0 2 * * ? *)"
            manager.schedule_workflow(workflow_name, schedule_expression)
            
            # 3. 워크플로우 실행 (테스트)
            print("\n워크플로우 테스트 실행을 시작하시겠습니까? (y/n): ", end="")
            if input().lower() == 'y':
                run_id = manager.start_workflow_run(workflow_name)
                
                if run_id:
                    print("워크플로우 실행 상태를 모니터링합니다...")
                    time.sleep(10)  # 10초 대기
                    manager.monitor_workflow_runs(workflow_name, max_runs=1, detailed=True)
            
            # 4. 알림 설정 (선택사항)
            print("\n알림 설정을 하시겠습니까? (y/n): ", end="")
            if input().lower() == 'y':
                notification_manager = WorkflowNotificationManager()
                
                print("알림 받을 이메일 주소를 입력하세요: ", end="")
                email = input().strip()
                
                if email:
                    topic_arn = notification_manager.create_notification_topic(
                        f"{workflow_name}-notifications",
                        [email]
                    )
                    
                    if topic_arn:
                        notification_manager.setup_workflow_alarms(workflow_name, topic_arn)
        
        print("\n=== 워크플로우 설정 완료 ===")
        print("AWS Glue 콘솔에서 워크플로우를 확인할 수 있습니다.")
        
    except Exception as e:
        print(f"❌ 워크플로우 설정 중 오류 발생: {str(e)}")

if __name__ == "__main__":
    main()