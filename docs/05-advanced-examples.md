# 심화 예제

기본 워크샵을 완료한 후, 더 복잡하고 실무에 가까운 데이터 분석 시나리오를 경험해보세요. 이 섹션에서는 여러 데이터 소스를 통합하고, 복잡한 변환 로직을 구현하며, 고급 분석 기법을 활용하는 방법을 다룹니다.

## 목차
1. [고급 ETL 시나리오](#고급-etl-시나리오)
2. [Glue 고급 기능 활용](#glue-고급-기능-활용)
3. [고급 Athena 분석](#고급-athena-분석)
4. [독립 수행 과제](#독립-수행-과제)

---

## 고급 ETL 시나리오

### 시나리오 1: 다중 데이터 소스 통합 분석

실제 업무에서는 여러 시스템의 데이터를 통합하여 분석하는 경우가 많습니다. 이 예제에서는 학생 AI 도구 사용 데이터와 학업 성과 데이터를 결합하여 종합적인 인사이트를 도출해보겠습니다.

#### 데이터 소스 구성

**주요 데이터셋:**
- `ai_tool_usage`: 학생들의 AI 도구 사용 패턴 (기본 워크샵에서 사용)
- `academic_performance`: 학생들의 학업 성과 데이터 (새로 추가)
- `course_enrollment`: 수강 신청 및 과목 정보 (새로 추가)

#### 1.1 추가 데이터셋 준비

먼저 실습용 추가 데이터셋을 생성해보겠습니다.

**academic_performance.csv 생성:**
```python
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# 학업 성과 데이터 생성
np.random.seed(42)
student_ids = [f"STU_{i:04d}" for i in range(1, 501)]

academic_data = {
    'student_id': student_ids,
    'semester': np.random.choice(['2024-1', '2024-2'], 500),
    'gpa': np.round(np.random.normal(3.2, 0.8, 500), 2),
    'credits_completed': np.random.randint(12, 21, 500),
    'major_gpa': np.round(np.random.normal(3.4, 0.7, 500), 2),
    'attendance_rate': np.round(np.random.normal(0.85, 0.15, 500), 2),
    'assignment_submission_rate': np.round(np.random.normal(0.90, 0.12, 500), 2),
    'last_updated': datetime.now().strftime('%Y-%m-%d')
}

academic_df = pd.DataFrame(academic_data)
academic_df.to_csv('datasets/academic_performance.csv', index=False)
print("Academic performance dataset created!")
```

**course_enrollment.csv 생성:**
```python
# 수강 신청 데이터 생성
courses = [
    'CS101_Programming_Fundamentals', 'CS201_Data_Structures', 
    'CS301_Database_Systems', 'CS401_Machine_Learning',
    'MATH201_Statistics', 'MATH301_Linear_Algebra',
    'ENG101_Technical_Writing', 'BUS201_Project_Management'
]

enrollment_data = []
for student_id in student_ids[:300]:  # 300명의 학생만 선택
    num_courses = np.random.randint(3, 6)
    selected_courses = np.random.choice(courses, num_courses, replace=False)
    
    for course in selected_courses:
        enrollment_data.append({
            'student_id': student_id,
            'course_code': course.split('_')[0],
            'course_name': '_'.join(course.split('_')[1:]),
            'semester': np.random.choice(['2024-1', '2024-2']),
            'grade': np.random.choice(['A+', 'A', 'B+', 'B', 'C+', 'C', 'D', 'F'], 
                                   p=[0.1, 0.2, 0.25, 0.2, 0.15, 0.05, 0.03, 0.02]),
            'credit_hours': np.random.choice([3, 4], p=[0.7, 0.3])
        })

enrollment_df = pd.DataFrame(enrollment_data)
enrollment_df.to_csv('datasets/course_enrollment.csv', index=False)
print("Course enrollment dataset created!")
```

#### 1.2 복잡한 데이터 조인 ETL 작업

이제 Glue Studio에서 복잡한 조인 로직을 구현해보겠습니다.

**Glue ETL 스크립트 (Python):**
```python
import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from pyspark.sql import functions as F
from pyspark.sql.types import *

# Job 초기화
args = getResolvedOptions(sys.argv, ['JOB_NAME'])
sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args['JOB_NAME'], args)

# 데이터 소스 읽기
ai_usage_df = glueContext.create_dynamic_frame.from_catalog(
    database="workshop_database",
    table_name="ai_tool_usage"
).toDF()

academic_df = glueContext.create_dynamic_frame.from_catalog(
    database="workshop_database", 
    table_name="academic_performance"
).toDF()

enrollment_df = glueContext.create_dynamic_frame.from_catalog(
    database="workshop_database",
    table_name="course_enrollment"
).toDF()

# 데이터 품질 검증 함수
def validate_data_quality(df, table_name):
    """데이터 품질 검증 및 리포트 생성"""
    total_rows = df.count()
    
    # 결측값 검사
    null_counts = {}
    for col in df.columns:
        null_count = df.filter(F.col(col).isNull()).count()
        null_counts[col] = null_count
    
    # 중복 검사
    duplicate_count = df.count() - df.dropDuplicates().count()
    
    print(f"=== {table_name} 데이터 품질 리포트 ===")
    print(f"총 행 수: {total_rows}")
    print(f"중복 행 수: {duplicate_count}")
    print("결측값 현황:")
    for col, null_count in null_counts.items():
        if null_count > 0:
            print(f"  {col}: {null_count} ({null_count/total_rows*100:.2f}%)")
    
    # 품질 임계값 검사
    max_null_rate = max([count/total_rows for count in null_counts.values()])
    if max_null_rate > 0.1:  # 10% 이상 결측값
        raise Exception(f"{table_name}: 결측값이 너무 많습니다 ({max_null_rate*100:.2f}%)")
    
    if duplicate_count > total_rows * 0.05:  # 5% 이상 중복
        raise Exception(f"{table_name}: 중복 데이터가 너무 많습니다 ({duplicate_count}개)")
    
    return True

# 각 데이터셋 품질 검증
validate_data_quality(ai_usage_df, "AI Tool Usage")
validate_data_quality(academic_df, "Academic Performance") 
validate_data_quality(enrollment_df, "Course Enrollment")

# 복잡한 데이터 변환 및 조인
# 1. AI 도구 사용 데이터 전처리
ai_usage_clean = ai_usage_df.select(
    F.col("student_id"),
    F.col("field_of_study"),
    F.col("year_of_study"),
    F.size(F.split(F.col("ai_tools_used"), ",")).alias("num_ai_tools"),
    F.when(F.col("frequency_of_use") == "Daily", 5)
     .when(F.col("frequency_of_use") == "Weekly", 4)
     .when(F.col("frequency_of_use") == "Monthly", 3)
     .when(F.col("frequency_of_use") == "Rarely", 2)
     .otherwise(1).alias("usage_frequency_score"),
    F.col("satisfaction_level"),
    F.col("primary_use_case")
)

# 2. 학업 성과 데이터 전처리
academic_clean = academic_df.select(
    F.col("student_id"),
    F.col("semester"),
    F.col("gpa"),
    F.col("major_gpa"),
    F.col("credits_completed"),
    F.col("attendance_rate"),
    F.col("assignment_submission_rate"),
    # 성과 카테고리 생성
    F.when(F.col("gpa") >= 3.5, "High")
     .when(F.col("gpa") >= 2.5, "Medium")
     .otherwise("Low").alias("performance_category")
)

# 3. 수강 신청 데이터 집계
enrollment_agg = enrollment_df.groupBy("student_id", "semester").agg(
    F.count("course_code").alias("total_courses"),
    F.sum("credit_hours").alias("total_credits"),
    F.avg(
        F.when(F.col("grade") == "A+", 4.3)
         .when(F.col("grade") == "A", 4.0)
         .when(F.col("grade") == "B+", 3.3)
         .when(F.col("grade") == "B", 3.0)
         .when(F.col("grade") == "C+", 2.3)
         .when(F.col("grade") == "C", 2.0)
         .when(F.col("grade") == "D", 1.0)
         .otherwise(0.0)
    ).alias("calculated_gpa"),
    F.collect_list("course_name").alias("courses_taken")
)

# 4. 복잡한 다중 조인 수행
# AI 사용 데이터와 학업 성과 조인
ai_academic_joined = ai_usage_clean.join(
    academic_clean, 
    on="student_id", 
    how="inner"
)

# 수강 신청 데이터 추가 조인
final_integrated = ai_academic_joined.join(
    enrollment_agg,
    on=["student_id", "semester"],
    how="left"
)

# 5. 고급 집계 및 인사이트 생성
insights_df = final_integrated.groupBy(
    "field_of_study", 
    "performance_category",
    "primary_use_case"
).agg(
    F.count("student_id").alias("student_count"),
    F.avg("num_ai_tools").alias("avg_ai_tools_used"),
    F.avg("usage_frequency_score").alias("avg_usage_frequency"),
    F.avg("satisfaction_level").alias("avg_satisfaction"),
    F.avg("gpa").alias("avg_gpa"),
    F.avg("major_gpa").alias("avg_major_gpa"),
    F.avg("attendance_rate").alias("avg_attendance"),
    F.avg("assignment_submission_rate").alias("avg_submission_rate"),
    F.corr("usage_frequency_score", "gpa").alias("usage_gpa_correlation")
).filter(F.col("student_count") >= 5)  # 최소 5명 이상인 그룹만

# 6. 이상값 탐지 및 플래깅
from pyspark.sql.window import Window

# 각 전공별 GPA 분포 계산
window_spec = Window.partitionBy("field_of_study")
outlier_detection = final_integrated.withColumn(
    "field_avg_gpa", F.avg("gpa").over(window_spec)
).withColumn(
    "field_stddev_gpa", F.stddev("gpa").over(window_spec)
).withColumn(
    "gpa_z_score", 
    (F.col("gpa") - F.col("field_avg_gpa")) / F.col("field_stddev_gpa")
).withColumn(
    "is_outlier",
    F.when(F.abs(F.col("gpa_z_score")) > 2.5, True).otherwise(False)
)

# 결과 저장
# 통합 데이터셋 저장
final_integrated_dynamic = DynamicFrame.fromDF(
    final_integrated, glueContext, "final_integrated"
)

glueContext.write_dynamic_frame.from_options(
    frame=final_integrated_dynamic,
    connection_type="s3",
    connection_options={
        "path": "s3://your-workshop-bucket/processed-data/integrated-student-analysis/",
        "partitionKeys": ["field_of_study", "semester"]
    },
    format="parquet"
)

# 인사이트 데이터 저장
insights_dynamic = DynamicFrame.fromDF(insights_df, glueContext, "insights")
glueContext.write_dynamic_frame.from_options(
    frame=insights_dynamic,
    connection_type="s3", 
    connection_options={
        "path": "s3://your-workshop-bucket/processed-data/student-insights/"
    },
    format="parquet"
)

# 이상값 데이터 저장
outliers_dynamic = DynamicFrame.fromDF(
    outlier_detection.filter(F.col("is_outlier") == True),
    glueContext, 
    "outliers"
)

glueContext.write_dynamic_frame.from_options(
    frame=outliers_dynamic,
    connection_type="s3",
    connection_options={
        "path": "s3://your-workshop-bucket/processed-data/outlier-analysis/"
    },
    format="parquet"
)

job.commit()
```

#### 1.3 데이터 품질 검증 및 오류 처리

**고급 데이터 품질 검증 스크립트:**
```python
# data_quality_validator.py
import boto3
from pyspark.sql import functions as F
from pyspark.sql.types import *
import json
from datetime import datetime

class DataQualityValidator:
    def __init__(self, spark_session, s3_client):
        self.spark = spark_session
        self.s3 = s3_client
        
    def comprehensive_quality_check(self, df, table_name, rules_config):
        """포괄적인 데이터 품질 검사"""
        quality_report = {
            'table_name': table_name,
            'timestamp': datetime.now().isoformat(),
            'total_rows': df.count(),
            'checks': {}
        }
        
        # 1. 기본 품질 검사
        quality_report['checks']['basic'] = self._basic_quality_checks(df)
        
        # 2. 비즈니스 규칙 검사
        if 'business_rules' in rules_config:
            quality_report['checks']['business_rules'] = self._business_rule_checks(
                df, rules_config['business_rules']
            )
        
        # 3. 데이터 일관성 검사
        quality_report['checks']['consistency'] = self._consistency_checks(df)
        
        # 4. 참조 무결성 검사
        if 'reference_integrity' in rules_config:
            quality_report['checks']['reference_integrity'] = self._reference_integrity_checks(
                df, rules_config['reference_integrity']
            )
        
        return quality_report
    
    def _basic_quality_checks(self, df):
        """기본 품질 검사: 결측값, 중복, 데이터 타입"""
        checks = {}
        
        # 결측값 검사
        null_counts = {}
        for col in df.columns:
            null_count = df.filter(F.col(col).isNull()).count()
            null_counts[col] = {
                'count': null_count,
                'percentage': null_count / df.count() * 100
            }
        checks['null_values'] = null_counts
        
        # 중복 검사
        total_rows = df.count()
        unique_rows = df.dropDuplicates().count()
        checks['duplicates'] = {
            'total_duplicates': total_rows - unique_rows,
            'duplicate_percentage': (total_rows - unique_rows) / total_rows * 100
        }
        
        # 데이터 타입 일관성
        checks['data_types'] = {col: str(df.schema[col].dataType) for col in df.columns}
        
        return checks
    
    def _business_rule_checks(self, df, rules):
        """비즈니스 규칙 검사"""
        checks = {}
        
        for rule_name, rule_config in rules.items():
            if rule_config['type'] == 'range':
                # 범위 검사
                col = rule_config['column']
                min_val = rule_config['min']
                max_val = rule_config['max']
                
                invalid_count = df.filter(
                    (F.col(col) < min_val) | (F.col(col) > max_val)
                ).count()
                
                checks[rule_name] = {
                    'invalid_count': invalid_count,
                    'invalid_percentage': invalid_count / df.count() * 100,
                    'rule': f"{col} should be between {min_val} and {max_val}"
                }
                
            elif rule_config['type'] == 'categorical':
                # 카테고리 값 검사
                col = rule_config['column']
                valid_values = rule_config['valid_values']
                
                invalid_count = df.filter(
                    ~F.col(col).isin(valid_values)
                ).count()
                
                checks[rule_name] = {
                    'invalid_count': invalid_count,
                    'invalid_percentage': invalid_count / df.count() * 100,
                    'rule': f"{col} should be one of {valid_values}"
                }
        
        return checks
    
    def _consistency_checks(self, df):
        """데이터 일관성 검사"""
        checks = {}
        
        # 날짜 일관성 검사 (예: 시작일 < 종료일)
        if 'start_date' in df.columns and 'end_date' in df.columns:
            invalid_dates = df.filter(
                F.col('start_date') > F.col('end_date')
            ).count()
            
            checks['date_consistency'] = {
                'invalid_count': invalid_dates,
                'invalid_percentage': invalid_dates / df.count() * 100
            }
        
        # 수치 일관성 검사 (예: GPA vs Major GPA)
        if 'gpa' in df.columns and 'major_gpa' in df.columns:
            # Major GPA가 전체 GPA보다 현저히 다른 경우
            inconsistent_gpa = df.filter(
                F.abs(F.col('gpa') - F.col('major_gpa')) > 1.0
            ).count()
            
            checks['gpa_consistency'] = {
                'inconsistent_count': inconsistent_gpa,
                'inconsistent_percentage': inconsistent_gpa / df.count() * 100
            }
        
        return checks
    
    def _reference_integrity_checks(self, df, ref_config):
        """참조 무결성 검사"""
        checks = {}
        
        for ref_name, ref_rule in ref_config.items():
            parent_table = ref_rule['parent_table']
            parent_key = ref_rule['parent_key']
            child_key = ref_rule['child_key']
            
            # 부모 테이블에서 유효한 키 값들 가져오기
            parent_df = self.spark.table(parent_table)
            valid_keys = parent_df.select(parent_key).distinct().rdd.flatMap(lambda x: x).collect()
            
            # 자식 테이블에서 유효하지 않은 참조 찾기
            invalid_refs = df.filter(
                ~F.col(child_key).isin(valid_keys)
            ).count()
            
            checks[ref_name] = {
                'invalid_references': invalid_refs,
                'invalid_percentage': invalid_refs / df.count() * 100,
                'rule': f"{child_key} must exist in {parent_table}.{parent_key}"
            }
        
        return checks
    
    def generate_quality_report(self, quality_results, output_path):
        """품질 검사 결과 리포트 생성"""
        report = {
            'summary': {
                'total_tables_checked': len(quality_results),
                'timestamp': datetime.now().isoformat(),
                'overall_status': 'PASS'
            },
            'detailed_results': quality_results
        }
        
        # 전체 상태 결정
        for table_result in quality_results:
            for check_type, checks in table_result['checks'].items():
                if check_type == 'basic':
                    # 결측값이 20% 이상이면 FAIL
                    for col, null_info in checks['null_values'].items():
                        if null_info['percentage'] > 20:
                            report['summary']['overall_status'] = 'FAIL'
                    
                    # 중복이 10% 이상이면 FAIL  
                    if checks['duplicates']['duplicate_percentage'] > 10:
                        report['summary']['overall_status'] = 'FAIL'
        
        # S3에 리포트 저장
        report_json = json.dumps(report, indent=2)
        self.s3.put_object(
            Bucket=output_path.split('/')[2],
            Key='/'.join(output_path.split('/')[3:]) + '/quality_report.json',
            Body=report_json,
            ContentType='application/json'
        )
        
        return report

# 사용 예제
quality_rules = {
    'ai_tool_usage': {
        'business_rules': {
            'satisfaction_range': {
                'type': 'range',
                'column': 'satisfaction_level',
                'min': 1,
                'max': 5
            },
            'valid_frequency': {
                'type': 'categorical', 
                'column': 'frequency_of_use',
                'valid_values': ['Daily', 'Weekly', 'Monthly', 'Rarely', 'Never']
            }
        },
        'reference_integrity': {
            'student_exists': {
                'parent_table': 'student_master',
                'parent_key': 'student_id',
                'child_key': 'student_id'
            }
        }
    }
}
```

#### 1.4 오류 처리 및 복구 로직

**견고한 ETL 파이프라인을 위한 오류 처리:**
```python
# error_handling_etl.py
import logging
from functools import wraps
import boto3
from botocore.exceptions import ClientError
import time

class ETLErrorHandler:
    def __init__(self, job_name, s3_bucket):
        self.job_name = job_name
        self.s3_bucket = s3_bucket
        self.logger = self._setup_logging()
        self.s3_client = boto3.client('s3')
        
    def _setup_logging(self):
        """로깅 설정"""
        logger = logging.getLogger(self.job_name)
        logger.setLevel(logging.INFO)
        
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        return logger
    
    def retry_on_failure(self, max_retries=3, delay=60):
        """실패 시 재시도 데코레이터"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                for attempt in range(max_retries):
                    try:
                        return func(*args, **kwargs)
                    except Exception as e:
                        self.logger.warning(
                            f"Attempt {attempt + 1} failed for {func.__name__}: {str(e)}"
                        )
                        if attempt == max_retries - 1:
                            self.logger.error(f"All {max_retries} attempts failed for {func.__name__}")
                            raise
                        time.sleep(delay)
                return None
            return wrapper
        return decorator
    
    def safe_data_read(self, glue_context, database, table_name):
        """안전한 데이터 읽기"""
        try:
            df = glue_context.create_dynamic_frame.from_catalog(
                database=database,
                table_name=table_name
            ).toDF()
            
            # 기본 검증
            row_count = df.count()
            if row_count == 0:
                raise ValueError(f"Table {table_name} is empty")
            
            self.logger.info(f"Successfully read {row_count} rows from {table_name}")
            return df
            
        except Exception as e:
            self.logger.error(f"Failed to read table {table_name}: {str(e)}")
            # 백업 데이터 소스 시도
            return self._try_backup_source(glue_context, table_name)
    
    def _try_backup_source(self, glue_context, table_name):
        """백업 데이터 소스에서 읽기 시도"""
        backup_path = f"s3://{self.s3_bucket}/backup-data/{table_name}/"
        
        try:
            df = glue_context.create_dynamic_frame.from_options(
                connection_type="s3",
                connection_options={"paths": [backup_path]},
                format="parquet"
            ).toDF()
            
            self.logger.info(f"Successfully read from backup source: {backup_path}")
            return df
            
        except Exception as e:
            self.logger.error(f"Backup source also failed: {str(e)}")
            raise
    
    def safe_data_write(self, glue_context, dynamic_frame, output_path, format="parquet"):
        """안전한 데이터 쓰기"""
        try:
            # 임시 경로에 먼저 쓰기
            temp_path = output_path.replace('/processed-data/', '/temp-data/')
            
            glue_context.write_dynamic_frame.from_options(
                frame=dynamic_frame,
                connection_type="s3",
                connection_options={"path": temp_path},
                format=format
            )
            
            # 검증 후 최종 경로로 이동
            if self._validate_output(temp_path):
                self._move_to_final_location(temp_path, output_path)
                self.logger.info(f"Successfully wrote data to {output_path}")
            else:
                raise ValueError("Output validation failed")
                
        except Exception as e:
            self.logger.error(f"Failed to write data to {output_path}: {str(e)}")
            # 오류 데이터를 별도 위치에 저장
            self._save_error_data(dynamic_frame, output_path)
            raise
    
    def _validate_output(self, path):
        """출력 데이터 검증"""
        try:
            # S3에서 파일 존재 확인
            bucket = path.split('/')[2]
            prefix = '/'.join(path.split('/')[3:])
            
            response = self.s3_client.list_objects_v2(
                Bucket=bucket,
                Prefix=prefix
            )
            
            if 'Contents' not in response:
                return False
            
            # 파일 크기 확인 (최소 1KB)
            total_size = sum([obj['Size'] for obj in response['Contents']])
            return total_size > 1024
            
        except Exception as e:
            self.logger.error(f"Output validation failed: {str(e)}")
            return False
    
    def create_checkpoint(self, glue_context, step_name, data_frame):
        """체크포인트 생성"""
        checkpoint_path = f"s3://{self.s3_bucket}/checkpoints/{self.job_name}/{step_name}/"
        
        try:
            from awsglue.dynamicframe import DynamicFrame
            dynamic_frame = DynamicFrame.fromDF(data_frame, glue_context, step_name)
            glue_context.write_dynamic_frame.from_options(
                frame=dynamic_frame,
                connection_type="s3",
                connection_options={"path": checkpoint_path},
                format="parquet"
            )
            
            self.logger.info(f"Checkpoint created: {checkpoint_path}")
            return checkpoint_path
            
        except Exception as e:
            self.logger.error(f"Failed to create checkpoint: {str(e)}")
            return None
    
    def recover_from_checkpoint(self, glue_context, step_name):
        """체크포인트에서 복구"""
        checkpoint_path = f"s3://{self.s3_bucket}/checkpoints/{self.job_name}/{step_name}/"
        
        try:
            df = glue_context.create_dynamic_frame.from_options(
                connection_type="s3",
                connection_options={"paths": [checkpoint_path]},
                format="parquet"
            ).toDF()
            
            self.logger.info(f"Recovered from checkpoint: {checkpoint_path}")
            return df
            
        except Exception as e:
            self.logger.error(f"Failed to recover from checkpoint: {str(e)}")
            return None

# 사용 예제
error_handler = ETLErrorHandler("advanced_etl_job", "your-workshop-bucket")

@error_handler.retry_on_failure(max_retries=3)
def process_student_data(glue_context):
    # 안전한 데이터 읽기
    ai_usage_df = error_handler.safe_data_read(
        glue_context, "workshop_database", "ai_tool_usage"
    )
    
    # 체크포인트 생성
    error_handler.create_checkpoint(glue_context, "raw_data_loaded", ai_usage_df)
    
    # 데이터 변환 로직
    from pyspark.sql import functions as F
    processed_df = ai_usage_df.groupBy("field_of_study").agg(
        F.count("student_id").alias("student_count"),
        F.avg("satisfaction_level").alias("avg_satisfaction")
    )
    
    # 안전한 데이터 쓰기
    from awsglue.dynamicframe import DynamicFrame
    processed_dynamic = DynamicFrame.fromDF(processed_df, glue_context, "processed")
    error_handler.safe_data_write(
        glue_context,
        processed_dynamic,
        "s3://your-workshop-bucket/processed-data/student-summary/"
    )
```

### 시나리오 2: 실시간 데이터 스트리밍 처리

실시간으로 들어오는 학생 활동 로그를 처리하는 시나리오입니다.

#### 2.1 Kinesis Data Streams 연동

```python
# kinesis_streaming_etl.py
import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from pyspark.sql import functions as F
from pyspark.sql.types import *

# 스트리밍 ETL 작업
def process_streaming_data():
    args = getResolvedOptions(sys.argv, ['JOB_NAME'])
    sc = SparkContext()
    glueContext = GlueContext(sc)
    spark = glueContext.spark_session
    job = Job(glueContext)
    job.init(args['JOB_NAME'], args)
    
    # Kinesis 스트림에서 데이터 읽기
    kinesis_options = {
        "streamName": "student-activity-stream",
        "startingPosition": "TRIM_HORIZON",
        "inferSchema": "true",
        "classification": "json"
    }
    
    streaming_df = glueContext.create_dynamic_frame.from_options(
        connection_type="kinesis",
        connection_options=kinesis_options
    )
    
    # 스트리밍 데이터 변환
    transformed_df = streaming_df.toDF().select(
        F.col("student_id"),
        F.col("activity_type"),
        F.col("timestamp"),
        F.col("session_duration"),
        F.col("ai_tool_used"),
        F.from_json(F.col("metadata"), 
                   StructType([
                       StructField("course_id", StringType()),
                       StructField("assignment_id", StringType()),
                       StructField("difficulty_level", IntegerType())
                   ])).alias("parsed_metadata")
    ).select(
        "*",
        F.col("parsed_metadata.course_id").alias("course_id"),
        F.col("parsed_metadata.assignment_id").alias("assignment_id"),
        F.col("parsed_metadata.difficulty_level").alias("difficulty_level")
    ).drop("parsed_metadata")
    
    # 실시간 집계 (윈도우 함수 사용)
    windowed_aggregation = transformed_df.groupBy(
        F.window(F.col("timestamp"), "10 minutes"),
        F.col("ai_tool_used")
    ).agg(
        F.count("student_id").alias("usage_count"),
        F.avg("session_duration").alias("avg_session_duration"),
        F.countDistinct("student_id").alias("unique_users")
    )
    
    # 결과를 S3에 저장 (파티션별로)
    output_df = DynamicFrame.fromDF(windowed_aggregation, glueContext, "windowed_agg")
    
    glueContext.write_dynamic_frame.from_options(
        frame=output_df,
        connection_type="s3",
        connection_options={
            "path": "s3://your-workshop-bucket/streaming-data/real-time-usage/",
            "partitionKeys": ["window"]
        },
        format="parquet"
    )
    
    job.commit()
```

---

## 실습 단계

### 단계 1: 추가 데이터셋 생성 및 업로드

1. **Python 환경에서 추가 데이터셋 생성:**
   ```bash
   # 가상환경 활성화
   python -m venv advanced_workshop
   source advanced_workshop/bin/activate  # Linux/Mac
   # 또는
   advanced_workshop\Scripts\activate  # Windows
   
   # 필요한 라이브러리 설치
   pip install pandas numpy boto3
   
   # 데이터 생성 스크립트 실행
   python generate_additional_datasets.py
   ```

2. **S3에 새 데이터셋 업로드:**
   ```bash
   aws s3 cp datasets/academic_performance.csv s3://your-workshop-bucket/raw-data/academic_performance/
   aws s3 cp datasets/course_enrollment.csv s3://your-workshop-bucket/raw-data/course_enrollment/
   ```

3. **Glue 크롤러로 새 테이블 생성:**
   - AWS Glue 콘솔에서 새 크롤러 생성
   - 새 데이터 경로 지정
   - 크롤러 실행하여 테이블 스키마 생성

### 단계 2: 복잡한 ETL 작업 실행

1. **Glue Studio에서 새 ETL 작업 생성:**
   - 시각적 편집기 사용
   - 여러 데이터 소스 연결
   - 조인 및 변환 노드 구성

2. **Python 스크립트 모드로 전환:**
   - 위의 복잡한 ETL 스크립트 복사
   - 버킷 이름을 실제 버킷으로 수정
   - 작업 실행

3. **데이터 품질 검증:**
   - 품질 검증 스크립트 실행
   - 결과 리포트 확인
   - 필요시 데이터 정제 재실행

### 단계 3: 결과 검증

1. **Athena에서 결과 확인:**
   ```sql
   -- 통합 데이터 확인
   SELECT field_of_study, performance_category, 
          COUNT(*) as student_count,
          AVG(usage_frequency_score) as avg_usage_frequency,
          AVG(gpa) as avg_gpa
   FROM integrated_student_analysis
   GROUP BY field_of_study, performance_category
   ORDER BY field_of_study, performance_category;
   
   -- 인사이트 데이터 확인
   SELECT * FROM student_insights
   WHERE usage_gpa_correlation IS NOT NULL
   ORDER BY usage_gpa_correlation DESC;
   
   -- 이상값 확인
   SELECT student_id, field_of_study, gpa, gpa_z_score
   FROM outlier_analysis
   ORDER BY ABS(gpa_z_score) DESC
   LIMIT 10;
   ```

2. **데이터 품질 리포트 확인:**
   - S3에서 quality_report.json 다운로드
   - 품질 지표 검토
   - 필요시 추가 정제 작업 수행

---

## 학습 포인트

이 고급 ETL 시나리오를 통해 다음을 학습할 수 있습니다:

1. **복잡한 데이터 조인**: 여러 테이블을 효율적으로 조인하는 방법
2. **데이터 품질 관리**: 체계적인 품질 검증 및 오류 처리
3. **성능 최적화**: 파티셔닝과 적절한 데이터 타입 사용
4. **오류 복구**: 체크포인트와 재시도 로직 구현
5. **실시간 처리**: 스트리밍 데이터 처리 기초

다음 섹션에서는 Glue의 고급 기능들을 더 자세히 살펴보겠습니다.
---

#
# Glue 고급 기능 활용

AWS Glue의 고급 기능들을 활용하여 더 효율적이고 확장 가능한 ETL 파이프라인을 구축해보겠습니다.

### 2.1 커스텀 변환 함수 작성

Glue에서 제공하는 기본 변환 외에도 복잡한 비즈니스 로직을 위한 커스텀 함수를 작성할 수 있습니다.

#### 커스텀 변환 함수 예제

```python
# custom_transformations.py
from pyspark.sql import functions as F
from pyspark.sql.types import *
import re
from datetime import datetime, timedelta

class StudentDataTransformations:
    """학생 데이터 전용 커스텀 변환 함수들"""
    
    @staticmethod
    def calculate_ai_proficiency_score(df):
        """AI 도구 숙련도 점수 계산"""
        return df.withColumn(
            "ai_proficiency_score",
            # 사용 도구 수 (30%) + 사용 빈도 (40%) + 만족도 (30%)
            (F.col("num_ai_tools") * 0.3) + 
            (F.col("usage_frequency_score") * 0.4) + 
            (F.col("satisfaction_level") * 0.3)
        )
    
    @staticmethod
    def categorize_learning_style(df):
        """학습 스타일 분류"""
        return df.withColumn(
            "learning_style",
            F.when(
                (F.col("primary_use_case") == "Research") & 
                (F.col("usage_frequency_score") >= 4), "Research_Intensive"
            ).when(
                (F.col("primary_use_case") == "Assignment_Help") & 
                (F.col("satisfaction_level") >= 4), "Assignment_Focused"
            ).when(
                F.col("num_ai_tools") >= 3, "Multi_Tool_User"
            ).otherwise("Basic_User")
        )
    
    @staticmethod
    def detect_at_risk_students(df):
        """위험군 학생 탐지"""
        return df.withColumn(
            "at_risk_flag",
            F.when(
                (F.col("gpa") < 2.5) & 
                (F.col("attendance_rate") < 0.7) & 
                (F.col("assignment_submission_rate") < 0.8), True
            ).otherwise(False)
        ).withColumn(
            "risk_level",
            F.when(F.col("at_risk_flag"), 
                F.when(F.col("gpa") < 2.0, "High")
                 .when(F.col("gpa") < 2.5, "Medium")
                 .otherwise("Low")
            ).otherwise("None")
        )
    
    @staticmethod
    def normalize_course_names(df):
        """과목명 정규화"""
        # UDF 정의
        def clean_course_name(name):
            if name is None:
                return None
            # 언더스코어를 공백으로 변경
            cleaned = name.replace('_', ' ')
            # 첫 글자 대문자화
            cleaned = ' '.join([word.capitalize() for word in cleaned.split()])
            return cleaned
        
        clean_course_udf = F.udf(clean_course_name, StringType())
        
        return df.withColumn(
            "course_name_normalized",
            clean_course_udf(F.col("course_name"))
        )
    
    @staticmethod
    def calculate_semester_workload(df):
        """학기별 학업 부담 계산"""
        return df.withColumn(
            "workload_score",
            # 수강 과목 수 + 총 학점 + 과목 다양성
            (F.col("total_courses") * 2) + 
            (F.col("total_credits") * 1.5) + 
            (F.col("academic_diversity") * 3)
        ).withColumn(
            "workload_category",
            F.when(F.col("workload_score") >= 50, "Heavy")
             .when(F.col("workload_score") >= 35, "Moderate")
             .otherwise("Light")
        )

# Glue ETL 작업에서 커스텀 변환 사용
def apply_custom_transformations(df):
    """커스텀 변환 함수들을 순차적으로 적용"""
    transformer = StudentDataTransformations()
    
    # 변환 파이프라인
    df = transformer.calculate_ai_proficiency_score(df)
    df = transformer.categorize_learning_style(df)
    df = transformer.detect_at_risk_students(df)
    df = transformer.normalize_course_names(df)
    df = transformer.calculate_semester_workload(df)
    
    return df
```

#### Glue Studio에서 커스텀 변환 사용

```python
# glue_custom_transform_job.py
import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from awsglue.dynamicframe import DynamicFrame

# 커스텀 변환 함수 import (위의 코드를 별도 파일로 저장 후)
from custom_transformations import StudentDataTransformations, apply_custom_transformations

def main():
    args = getResolvedOptions(sys.argv, ['JOB_NAME'])
    sc = SparkContext()
    glueContext = GlueContext(sc)
    spark = glueContext.spark_session
    job = Job(glueContext)
    job.init(args['JOB_NAME'], args)
    
    # 데이터 읽기
    integrated_df = glueContext.create_dynamic_frame.from_catalog(
        database="workshop_database",
        table_name="integrated_student_analysis"
    ).toDF()
    
    # 커스텀 변환 적용
    transformed_df = apply_custom_transformations(integrated_df)
    
    # 결과 저장
    result_dynamic = DynamicFrame.fromDF(transformed_df, glueContext, "transformed")
    glueContext.write_dynamic_frame.from_options(
        frame=result_dynamic,
        connection_type="s3",
        connection_options={
            "path": "s3://your-workshop-bucket/processed-data/custom-transformed/"
        },
        format="parquet"
    )
    
    job.commit()

if __name__ == "__main__":
    main()
```

### 2.2 파티셔닝 및 성능 최적화

대용량 데이터 처리를 위한 파티셔닝 전략과 성능 최적화 기법을 살펴보겠습니다.

#### 효율적인 파티셔닝 전략

```python
# partitioning_optimization.py
from pyspark.sql import functions as F
from awsglue.dynamicframe import DynamicFrame

class PartitioningOptimizer:
    """파티셔닝 최적화 클래스"""
    
    def __init__(self, glue_context):
        self.glue_context = glue_context
    
    def optimize_partitioning_by_date(self, df, date_column, s3_path):
        """날짜 기반 파티셔닝"""
        # 날짜 컬럼에서 년/월 추출
        partitioned_df = df.withColumn(
            "year", F.year(F.col(date_column))
        ).withColumn(
            "month", F.month(F.col(date_column))
        )
        
        # 파티션별 데이터 분포 확인
        partition_stats = partitioned_df.groupBy("year", "month").count().collect()
        print("파티션별 데이터 분포:")
        for stat in partition_stats:
            print(f"  {stat['year']}-{stat['month']:02d}: {stat['count']} 행")
        
        # 파티셔닝하여 저장
        dynamic_frame = DynamicFrame.fromDF(partitioned_df, self.glue_context, "partitioned")
        self.glue_context.write_dynamic_frame.from_options(
            frame=dynamic_frame,
            connection_type="s3",
            connection_options={
                "path": s3_path,
                "partitionKeys": ["year", "month"]
            },
            format="parquet"
        )
        
        return partitioned_df
    
    def optimize_partitioning_by_category(self, df, category_column, s3_path, max_partitions=50):
        """카테고리 기반 파티셔닝 (파티션 수 제한)"""
        # 카테고리별 데이터 분포 확인
        category_counts = df.groupBy(category_column).count().orderBy(F.desc("count"))
        total_categories = category_counts.count()
        
        print(f"총 {total_categories}개 카테고리 발견")
        
        if total_categories > max_partitions:
            # 상위 카테고리만 개별 파티션으로, 나머지는 'others'로 그룹화
            top_categories = [row[category_column] for row in 
                            category_counts.limit(max_partitions - 1).collect()]
            
            partitioned_df = df.withColumn(
                f"{category_column}_partition",
                F.when(F.col(category_column).isin(top_categories), F.col(category_column))
                 .otherwise("others")
            )
        else:
            partitioned_df = df.withColumn(
                f"{category_column}_partition", F.col(category_column)
            )
        
        # 파티셔닝하여 저장
        dynamic_frame = DynamicFrame.fromDF(partitioned_df, self.glue_context, "partitioned")
        self.glue_context.write_dynamic_frame.from_options(
            frame=dynamic_frame,
            connection_type="s3",
            connection_options={
                "path": s3_path,
                "partitionKeys": [f"{category_column}_partition"]
            },
            format="parquet"
        )
        
        return partitioned_df
    
    def optimize_file_size(self, df, target_file_size_mb=128):
        """파일 크기 최적화"""
        # 데이터 크기 추정
        sample_size = min(1000, df.count())
        sample_df = df.sample(fraction=sample_size/df.count())
        
        # 샘플 데이터를 JSON으로 변환하여 크기 추정
        sample_json = sample_df.toJSON().collect()
        avg_row_size = sum(len(row) for row in sample_json) / len(sample_json)
        
        total_rows = df.count()
        estimated_total_size_mb = (total_rows * avg_row_size) / (1024 * 1024)
        
        # 최적 파티션 수 계산
        optimal_partitions = max(1, int(estimated_total_size_mb / target_file_size_mb))
        
        print(f"데이터 크기 추정: {estimated_total_size_mb:.2f} MB")
        print(f"최적 파티션 수: {optimal_partitions}")
        
        # 파티션 수 조정
        return df.repartition(optimal_partitions)

# 사용 예제
def optimize_student_data_partitioning(glue_context, df):
    """학생 데이터 파티셔닝 최적화"""
    optimizer = PartitioningOptimizer(glue_context)
    
    # 1. 전공별 파티셔닝 (카테고리 기반)
    field_partitioned = optimizer.optimize_partitioning_by_category(
        df, "field_of_study", 
        "s3://your-workshop-bucket/optimized-data/by-field/"
    )
    
    # 2. 학기별 파티셔닝 (날짜 기반)
    if "enrollment_date" in df.columns:
        date_partitioned = optimizer.optimize_partitioning_by_date(
            df, "enrollment_date",
            "s3://your-workshop-bucket/optimized-data/by-date/"
        )
    
    # 3. 파일 크기 최적화
    size_optimized = optimizer.optimize_file_size(df, target_file_size_mb=256)
    
    return size_optimized
```

#### 성능 최적화 기법

```python
# performance_optimization.py
from pyspark.sql import functions as F
from pyspark.sql.types import *
from pyspark import StorageLevel

class PerformanceOptimizer:
    """성능 최적화 클래스"""
    
    @staticmethod
    def optimize_joins(df1, df2, join_keys, join_type="inner"):
        """조인 성능 최적화"""
        # 1. 조인 키 기준으로 데이터 사전 정렬
        df1_sorted = df1.sortWithinPartitions(*join_keys)
        df2_sorted = df2.sortWithinPartitions(*join_keys)
        
        # 2. 브로드캐스트 조인 힌트 (작은 테이블의 경우)
        df2_count = df2.count()
        if df2_count < 10000:  # 10K 행 미만이면 브로드캐스트
            df2_broadcast = F.broadcast(df2_sorted)
            result = df1_sorted.join(df2_broadcast, join_keys, join_type)
        else:
            result = df1_sorted.join(df2_sorted, join_keys, join_type)
        
        return result
    
    @staticmethod
    def optimize_aggregations(df, group_cols, agg_cols):
        """집계 성능 최적화"""
        # 1. 사전 필터링으로 불필요한 데이터 제거
        filtered_df = df.filter(F.col(group_cols[0]).isNotNull())
        
        # 2. 컬럼 선택으로 메모리 사용량 감소
        selected_cols = group_cols + agg_cols
        selected_df = filtered_df.select(*selected_cols)
        
        # 3. 캐싱 (반복 사용되는 경우)
        cached_df = selected_df.cache()
        
        return cached_df
    
    @staticmethod
    def optimize_memory_usage(df, cache_level=StorageLevel.MEMORY_AND_DISK):
        """메모리 사용량 최적화"""
        # 1. 불필요한 컬럼 제거
        important_cols = [col for col in df.columns if not col.endswith('_temp')]
        optimized_df = df.select(*important_cols)
        
        # 2. 데이터 타입 최적화
        for col_name, col_type in optimized_df.dtypes:
            if col_type == 'string':
                # 문자열 길이 확인 후 최적화
                max_length = optimized_df.agg(F.max(F.length(col_name))).collect()[0][0]
                if max_length and max_length < 50:
                    # 짧은 문자열은 카테고리화 고려
                    distinct_count = optimized_df.select(col_name).distinct().count()
                    if distinct_count < 100:
                        print(f"컬럼 {col_name}: 카테고리화 권장 (고유값 {distinct_count}개)")
        
        # 3. 적절한 캐싱 레벨 설정
        return optimized_df.persist(cache_level)
    
    @staticmethod
    def optimize_window_functions(df, partition_cols, order_cols):
        """윈도우 함수 성능 최적화"""
        from pyspark.sql.window import Window
        
        # 1. 파티션 키 기준으로 사전 정렬
        sorted_df = df.sortWithinPartitions(*(partition_cols + order_cols))
        
        # 2. 윈도우 스펙 최적화
        window_spec = Window.partitionBy(*partition_cols).orderBy(*order_cols)
        
        # 3. 여러 윈도우 함수를 한 번에 적용
        result_df = sorted_df.withColumn(
            "row_number", F.row_number().over(window_spec)
        ).withColumn(
            "rank", F.rank().over(window_spec)
        ).withColumn(
            "running_total", F.sum("gpa").over(window_spec)
        )
        
        return result_df

# 성능 모니터링 함수
def monitor_job_performance(spark_context):
    """작업 성능 모니터링"""
    # Spark UI 정보 수집
    app_id = spark_context.applicationId
    app_name = spark_context.appName
    
    print(f"=== 성능 모니터링 ===")
    print(f"Application ID: {app_id}")
    print(f"Application Name: {app_name}")
    
    # 메모리 사용량 확인
    executor_infos = spark_context.statusTracker().getExecutorInfos()
    for executor in executor_infos:
        print(f"Executor {executor.executorId}:")
        print(f"  Max Memory: {executor.maxMemory / (1024**3):.2f} GB")
        print(f"  Memory Used: {executor.memoryUsed / (1024**3):.2f} GB")
    
    return {
        'app_id': app_id,
        'app_name': app_name,
        'executor_count': len(executor_infos)
    }
```

### 2.3 스케줄링 및 워크플로우 관리

복잡한 ETL 파이프라인을 자동화하고 관리하는 방법을 살펴보겠습니다.

#### AWS Glue Workflows 설정

```python
# workflow_management.py
import boto3
import json
from datetime import datetime, timedelta

class GlueWorkflowManager:
    """Glue 워크플로우 관리 클래스"""
    
    def __init__(self, region_name='us-east-1'):
        self.glue_client = boto3.client('glue', region_name=region_name)
        self.events_client = boto3.client('events', region_name=region_name)
    
    def create_etl_workflow(self, workflow_name, description=""):
        """ETL 워크플로우 생성"""
        try:
            response = self.glue_client.create_workflow(
                Name=workflow_name,
                Description=description,
                DefaultRunProperties={
                    'S3_BUCKET': 'your-workshop-bucket',
                    'DATABASE_NAME': 'workshop_database'
                }
            )
            print(f"✓ 워크플로우 '{workflow_name}' 생성 완료")
            return response
        except Exception as e:
            print(f"워크플로우 생성 실패: {str(e)}")
            return None
    
    def add_crawler_to_workflow(self, workflow_name, crawler_name):
        """워크플로우에 크롤러 추가"""
        try:
            self.glue_client.put_workflow_run_properties(
                Name=workflow_name,
                RunProperties={
                    'crawler_name': crawler_name
                }
            )
            print(f"✓ 크롤러 '{crawler_name}'를 워크플로우에 추가")
        except Exception as e:
            print(f"크롤러 추가 실패: {str(e)}")
    
    def create_job_trigger(self, trigger_name, workflow_name, job_names, 
                          trigger_type="ON_DEMAND", schedule=None):
        """작업 트리거 생성"""
        trigger_config = {
            'Name': trigger_name,
            'WorkflowName': workflow_name,
            'Type': trigger_type,
            'Actions': [{'JobName': job_name} for job_name in job_names]
        }
        
        if trigger_type == "SCHEDULED" and schedule:
            trigger_config['Schedule'] = schedule
        
        try:
            response = self.glue_client.create_trigger(**trigger_config)
            print(f"✓ 트리거 '{trigger_name}' 생성 완료")
            return response
        except Exception as e:
            print(f"트리거 생성 실패: {str(e)}")
            return None
    
    def create_conditional_trigger(self, trigger_name, workflow_name, 
                                 predecessor_jobs, successor_jobs):
        """조건부 트리거 생성 (이전 작업 완료 후 실행)"""
        try:
            response = self.glue_client.create_trigger(
                Name=trigger_name,
                WorkflowName=workflow_name,
                Type='CONDITIONAL',
                Predicate={
                    'Conditions': [
                        {
                            'LogicalOperator': 'EQUALS',
                            'JobName': job_name,
                            'State': 'SUCCEEDED'
                        } for job_name in predecessor_jobs
                    ]
                },
                Actions=[{'JobName': job_name} for job_name in successor_jobs]
            )
            print(f"✓ 조건부 트리거 '{trigger_name}' 생성 완료")
            return response
        except Exception as e:
            print(f"조건부 트리거 생성 실패: {str(e)}")
            return None
    
    def setup_complete_workflow(self):
        """완전한 ETL 워크플로우 설정"""
        workflow_name = "student-data-analysis-workflow"
        
        # 1. 워크플로우 생성
        self.create_etl_workflow(
            workflow_name, 
            "학생 데이터 분석을 위한 완전한 ETL 파이프라인"
        )
        
        # 2. 작업 순서 정의
        jobs_sequence = [
            {
                'name': 'data-quality-check',
                'description': '데이터 품질 검증',
                'script': 'data_quality_validator.py'
            },
            {
                'name': 'advanced-etl-processing',
                'description': '고급 ETL 처리',
                'script': 'advanced_multi_source_etl.py'
            },
            {
                'name': 'custom-transformations',
                'description': '커스텀 변환 적용',
                'script': 'custom_transform_job.py'
            }
        ]
        
        # 3. 트리거 생성
        # 첫 번째 작업 (수동 시작)
        self.create_job_trigger(
            'start-quality-check',
            workflow_name,
            ['data-quality-check'],
            'ON_DEMAND'
        )
        
        # 두 번째 작업 (품질 검사 완료 후)
        self.create_conditional_trigger(
            'quality-to-etl',
            workflow_name,
            ['data-quality-check'],
            ['advanced-etl-processing']
        )
        
        # 세 번째 작업 (ETL 완료 후)
        self.create_conditional_trigger(
            'etl-to-transform',
            workflow_name,
            ['advanced-etl-processing'],
            ['custom-transformations']
        )
        
        print(f"✓ 완전한 워크플로우 '{workflow_name}' 설정 완료")
    
    def schedule_daily_workflow(self, workflow_name, hour=2, minute=0):
        """일일 워크플로우 스케줄링"""
        schedule_expression = f"cron({minute} {hour} * * ? *)"
        
        # EventBridge 규칙 생성
        rule_name = f"{workflow_name}-daily-schedule"
        
        try:
            self.events_client.put_rule(
                Name=rule_name,
                ScheduleExpression=schedule_expression,
                Description=f"Daily schedule for {workflow_name}",
                State='ENABLED'
            )
            
            # Glue 워크플로우를 타겟으로 설정
            self.events_client.put_targets(
                Rule=rule_name,
                Targets=[
                    {
                        'Id': '1',
                        'Arn': f'arn:aws:glue:us-east-1:123456789012:workflow/{workflow_name}',
                        'RoleArn': 'arn:aws:iam::123456789012:role/GlueWorkflowRole'
                    }
                ]
            )
            
            print(f"✓ 일일 스케줄 설정 완료: 매일 {hour:02d}:{minute:02d}")
            
        except Exception as e:
            print(f"스케줄 설정 실패: {str(e)}")
    
    def monitor_workflow_runs(self, workflow_name, max_runs=10):
        """워크플로우 실행 모니터링"""
        try:
            response = self.glue_client.get_workflow_runs(
                Name=workflow_name,
                MaxResults=max_runs
            )
            
            print(f"=== {workflow_name} 실행 이력 ===")
            for run in response['Runs']:
                run_id = run['WorkflowRunId']
                status = run['Status']
                start_time = run.get('StartedOn', 'N/A')
                
                print(f"Run ID: {run_id}")
                print(f"  Status: {status}")
                print(f"  Started: {start_time}")
                
                if 'Statistics' in run:
                    stats = run['Statistics']
                    print(f"  Total Actions: {stats.get('TotalActions', 0)}")
                    print(f"  Succeeded: {stats.get('SucceededActions', 0)}")
                    print(f"  Failed: {stats.get('FailedActions', 0)}")
                print()
            
        except Exception as e:
            print(f"워크플로우 모니터링 실패: {str(e)}")

# 사용 예제
def setup_student_analysis_workflow():
    """학생 분석 워크플로우 설정"""
    manager = GlueWorkflowManager()
    
    # 완전한 워크플로우 설정
    manager.setup_complete_workflow()
    
    # 일일 스케줄 설정 (새벽 2시)
    manager.schedule_daily_workflow("student-data-analysis-workflow", hour=2)
    
    # 워크플로우 모니터링
    manager.monitor_workflow_runs("student-data-analysis-workflow")

if __name__ == "__main__":
    setup_student_analysis_workflow()
```

#### 오류 처리 및 알림 시스템

```python
# error_handling_workflow.py
import boto3
import json
from datetime import datetime

class WorkflowErrorHandler:
    """워크플로우 오류 처리 클래스"""
    
    def __init__(self):
        self.sns_client = boto3.client('sns')
        self.cloudwatch_client = boto3.client('cloudwatch')
        self.glue_client = boto3.client('glue')
    
    def create_error_notification_topic(self, topic_name):
        """오류 알림용 SNS 토픽 생성"""
        try:
            response = self.sns_client.create_topic(Name=topic_name)
            topic_arn = response['TopicArn']
            
            # 이메일 구독 추가 (실제 이메일로 변경 필요)
            self.sns_client.subscribe(
                TopicArn=topic_arn,
                Protocol='email',
                Endpoint='admin@university.edu'
            )
            
            print(f"✓ 알림 토픽 생성: {topic_arn}")
            return topic_arn
            
        except Exception as e:
            print(f"알림 토픽 생성 실패: {str(e)}")
            return None
    
    def setup_cloudwatch_alarms(self, workflow_name, topic_arn):
        """CloudWatch 알람 설정"""
        alarm_configs = [
            {
                'name': f'{workflow_name}-job-failures',
                'description': 'Glue 작업 실패 알람',
                'metric_name': 'glue.driver.aggregate.numFailedTasks',
                'threshold': 1
            },
            {
                'name': f'{workflow_name}-long-running-jobs',
                'description': '장시간 실행 작업 알람',
                'metric_name': 'glue.driver.aggregate.elapsedTime',
                'threshold': 3600  # 1시간
            }
        ]
        
        for config in alarm_configs:
            try:
                self.cloudwatch_client.put_metric_alarm(
                    AlarmName=config['name'],
                    ComparisonOperator='GreaterThanThreshold',
                    EvaluationPeriods=1,
                    MetricName=config['metric_name'],
                    Namespace='AWS/Glue',
                    Period=300,
                    Statistic='Sum',
                    Threshold=config['threshold'],
                    ActionsEnabled=True,
                    AlarmActions=[topic_arn],
                    AlarmDescription=config['description'],
                    Dimensions=[
                        {
                            'Name': 'JobName',
                            'Value': workflow_name
                        }
                    ]
                )
                print(f"✓ 알람 설정: {config['name']}")
                
            except Exception as e:
                print(f"알람 설정 실패: {str(e)}")
    
    def create_retry_logic(self, job_name, max_retries=3):
        """작업 재시도 로직 생성"""
        retry_config = {
            'JobName': job_name,
            'MaxRetries': max_retries,
            'Timeout': 2880,  # 48시간
            'MaxConcurrentRuns': 1,
            'NotificationProperty': {
                'NotifyDelayAfter': 60  # 60분 후 알림
            }
        }
        
        try:
            self.glue_client.update_job(**retry_config)
            print(f"✓ 재시도 로직 설정: {job_name} (최대 {max_retries}회)")
            
        except Exception as e:
            print(f"재시도 로직 설정 실패: {str(e)}")

# 실습 단계별 가이드
def setup_advanced_glue_features():
    """고급 Glue 기능 설정 가이드"""
    print("=== AWS Glue 고급 기능 설정 가이드 ===\n")
    
    print("1. 커스텀 변환 함수 작성")
    print("   - custom_transformations.py 파일 생성")
    print("   - 비즈니스 로직에 맞는 변환 함수 구현")
    print("   - Glue 작업에서 import하여 사용\n")
    
    print("2. 파티셔닝 ��적화")
    print("   - 데이터 크기와 쿼리 패턴 분석")
    print("   - 적절한 파티션 키 선택")
    print("   - 파일 크기 최적화 (128MB-1GB 권장)\n")
    
    print("3. 워크플로우 설정")
    print("   - AWS Glue 콘솔에서 워크플로우 생성")
    print("   - 작업 간 의존성 설정")
    print("   - 스케줄링 및 트리거 구성\n")
    
    print("4. 모니터링 및 알림")
    print("   - CloudWatch 메트릭 확인")
    print("   - SNS 알림 설정")
    print("   - 오류 처리 로직 구현")

if __name__ == "__main__":
    setup_advanced_glue_features()
```

---

## 실습 가이드: Glue 고급 기능

### 단계 1: 커스텀 변환 함수 구현

1. **커스텀 변환 스크립트 생성:**
   ```bash
   # scripts/glue-etl/ 디렉토리에 파일 생성
   touch scripts/glue-etl/custom_transformations.py
   ```

2. **Glue 작업에서 커스텀 함수 사용:**
   - AWS Glue Studio에서 새 작업 생성
   - Python 스크립트 모드 선택
   - 커스텀 변환 함수 import 및 사용

3. **결과 검증:**
   ```sql
   -- Athena에서 변환 결과 확인
   SELECT learning_style, COUNT(*) as student_count,
          AVG(ai_proficiency_score) as avg_proficiency
   FROM custom_transformed_data
   GROUP BY learning_style
   ORDER BY avg_proficiency DESC;
   ```

### 단계 2: 파티셔닝 최적화

1. **현재 데이터 분포 분석:**
   ```sql
   -- 전공별 데이터 분포 확인
   SELECT field_of_study, COUNT(*) as count
   FROM integrated_student_analysis
   GROUP BY field_of_study
   ORDER BY count DESC;
   ```

2. **파티셔닝 전략 적용:**
   - 전공별 파티셔닝 (카테고리 기반)
   - 학기별 파티셔닝 (시간 기반)
   - 파일 크기 최적화

3. **성능 비교:**
   - 파티셔닝 전후 쿼리 성능 측정
   - 스캔되는 데이터 양 비교

### 단계 3: 워크플로우 설정

1. **AWS Glue 콘솔에서 워크플로우 생성:**
   - 워크플로우 이름: `student-analysis-pipeline`
   - 설명: 학생 데이터 분석 파이프라인

2. **작업 순서 구성:**
   - 데이터 품질 검증 → ETL 처리 → 커스텀 변환
   - 각 단계별 트리거 설정

3. **스케줄링 설정:**
   - 일일 실행 (새벽 2시)
   - EventBridge 규칙 생성

### 단계 4: 모니터링 설정

1. **CloudWatch 대시보드 생성:**
   - Glue 작업 메트릭 모니터링
   - 실행 시간, 성공/실패율 추적

2. **알림 설정:**
   - SNS 토픽 생성
   - 이메일 알림 구독
   - 실패 시 자동 알림

---

## 학습 포인트

이 섹션을 통해 다음을 학습할 수 있습니다:

1. **커스텀 변환**: 비즈니스 로직에 맞는 데이터 변환 구현
2. **성능 최적화**: 파티셔닝과 메모리 관리를 통한 성능 향상
3. **워크플로우 관리**: 복잡한 ETL 파이프라인의 자동화
4. **모니터링**: 실시간 모니터링과 오류 처리 시스템 구축
5. **확장성**: 대용량 데이터 처리를 위한 아키텍처 설계

다음 섹션에서는 Athena의 고급 분석 기능을 살펴보겠습니다.--
-

## 고급 Athena 분석

Amazon Athena의 고급 SQL 기능을 활용하여 복잡한 데이터 분석을 수행해보겠습니다. 윈도우 함수, CTE(Common Table Expressions), 고급 집계 함수 등을 사용한 실무 수준의 분석 예제를 다룹니다.

### 3.1 윈도우 함수를 활용한 고급 분석

윈도우 함수는 행 그룹에 대해 계산을 수행하면서도 개별 행을 유지할 수 있는 강력한 기능입니다.

#### 학생 성과 순위 분석

```sql
-- 전공별 GPA 순위 및 백분위수 계산
WITH student_rankings AS (
    SELECT 
        student_id,
        field_of_study,
        gpa,
        usage_frequency_score,
        satisfaction_level,
        -- 전공 내 GPA 순위
        ROW_NUMBER() OVER (
            PARTITION BY field_of_study 
            ORDER BY gpa DESC
        ) as gpa_rank,
        -- 전공 내 GPA 백분위수
        PERCENT_RANK() OVER (
            PARTITION BY field_of_study 
            ORDER BY gpa
        ) as gpa_percentile,
        -- 전공별 총 학생 수
        COUNT(*) OVER (PARTITION BY field_of_study) as total_students_in_field,
        -- 전공 내 상위 10% 여부
        CASE 
            WHEN PERCENT_RANK() OVER (
                PARTITION BY field_of_study 
                ORDER BY gpa
            ) >= 0.9 THEN 'Top 10%'
            WHEN PERCENT_RANK() OVER (
                PARTITION BY field_of_study 
                ORDER BY gpa
            ) >= 0.75 THEN 'Top 25%'
            WHEN PERCENT_RANK() OVER (
                PARTITION BY field_of_study 
                ORDER BY gpa
            ) >= 0.5 THEN 'Top 50%'
            ELSE 'Bottom 50%'
        END as performance_tier
    FROM integrated_student_analysis
    WHERE gpa IS NOT NULL
)
SELECT 
    field_of_study,
    performance_tier,
    COUNT(*) as student_count,
    ROUND(AVG(gpa), 3) as avg_gpa,
    ROUND(AVG(usage_frequency_score), 2) as avg_ai_usage,
    ROUND(AVG(satisfaction_level), 2) as avg_satisfaction,
    -- 성과 계층별 AI 사용 패턴 분석
    ROUND(
        AVG(usage_frequency_score * satisfaction_level), 2
    ) as ai_engagement_score
FROM student_rankings
GROUP BY field_of_study, performance_tier
ORDER BY field_of_study, 
         CASE performance_tier 
             WHEN 'Top 10%' THEN 1
             WHEN 'Top 25%' THEN 2  
             WHEN 'Top 50%' THEN 3
             ELSE 4
         END;
```

#### 시계열 분석 - 학기별 성과 추이

```sql
-- 학기별 성과 변화 추이 분석
WITH semester_performance AS (
    SELECT 
        student_id,
        semester,
        gpa,
        attendance_rate,
        assignment_submission_rate,
        -- 이전 학기 GPA
        LAG(gpa, 1) OVER (
            PARTITION BY student_id 
            ORDER BY semester
        ) as previous_gpa,
        -- 다음 학기 GPA  
        LEAD(gpa, 1) OVER (
            PARTITION BY student_id 
            ORDER BY semester
        ) as next_gpa,
        -- 학생별 평균 GPA (전체 기간)
        AVG(gpa) OVER (
            PARTITION BY student_id
        ) as student_avg_gpa,
        -- 누적 평균 GPA
        AVG(gpa) OVER (
            PARTITION BY student_id 
            ORDER BY semester 
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        ) as cumulative_gpa
    FROM integrated_student_analysis
    WHERE semester IS NOT NULL AND gpa IS NOT NULL
),
performance_trends AS (
    SELECT 
        *,
        -- GPA 변화량
        CASE 
            WHEN previous_gpa IS NOT NULL THEN 
                ROUND(gpa - previous_gpa, 3)
            ELSE NULL
        END as gpa_change,
        -- 성과 트렌드 분류
        CASE 
            WHEN previous_gpa IS NOT NULL THEN
                CASE 
                    WHEN gpa - previous_gpa > 0.3 THEN 'Significant Improvement'
                    WHEN gpa - previous_gpa > 0.1 THEN 'Moderate Improvement'
                    WHEN gpa - previous_gpa > -0.1 THEN 'Stable'
                    WHEN gpa - previous_gpa > -0.3 THEN 'Moderate Decline'
                    ELSE 'Significant Decline'
                END
            ELSE 'First Semester'
        END as performance_trend
    FROM semester_performance
)
SELECT 
    semester,
    performance_trend,
    COUNT(*) as student_count,
    ROUND(AVG(gpa), 3) as avg_current_gpa,
    ROUND(AVG(previous_gpa), 3) as avg_previous_gpa,
    ROUND(AVG(gpa_change), 3) as avg_gpa_change,
    ROUND(AVG(attendance_rate), 3) as avg_attendance,
    ROUND(AVG(assignment_submission_rate), 3) as avg_submission_rate
FROM performance_trends
WHERE performance_trend != 'First Semester'
GROUP BY semester, performance_trend
ORDER BY semester, 
         CASE performance_trend
             WHEN 'Significant Improvement' THEN 1
             WHEN 'Moderate Improvement' THEN 2
             WHEN 'Stable' THEN 3
             WHEN 'Moderate Decline' THEN 4
             WHEN 'Significant Decline' THEN 5
         END;
```

#### 코호트 분석 - AI 도구 사용 패턴

```sql
-- AI 도구 사용 코호트 분석
WITH ai_usage_cohorts AS (
    SELECT 
        student_id,
        field_of_study,
        usage_frequency_score,
        satisfaction_level,
        num_ai_tools,
        -- AI 사용 강도별 코호트 분류
        CASE 
            WHEN usage_frequency_score >= 4 AND num_ai_tools >= 3 THEN 'Power Users'
            WHEN usage_frequency_score >= 3 AND num_ai_tools >= 2 THEN 'Regular Users'
            WHEN usage_frequency_score >= 2 THEN 'Occasional Users'
            ELSE 'Light Users'
        END as usage_cohort,
        -- 만족도 기반 세그먼트
        CASE 
            WHEN satisfaction_level >= 4 THEN 'Highly Satisfied'
            WHEN satisfaction_level >= 3 THEN 'Satisfied'
            WHEN satisfaction_level >= 2 THEN 'Neutral'
            ELSE 'Dissatisfied'
        END as satisfaction_segment,
        gpa,
        attendance_rate
    FROM integrated_student_analysis
    WHERE usage_frequency_score IS NOT NULL 
      AND satisfaction_level IS NOT NULL
),
cohort_analysis AS (
    SELECT 
        usage_cohort,
        satisfaction_segment,
        field_of_study,
        COUNT(*) as cohort_size,
        ROUND(AVG(gpa), 3) as avg_gpa,
        ROUND(AVG(attendance_rate), 3) as avg_attendance,
        ROUND(AVG(usage_frequency_score), 2) as avg_usage_frequency,
        ROUND(AVG(satisfaction_level), 2) as avg_satisfaction,
        ROUND(AVG(num_ai_tools), 1) as avg_tools_used,
        -- 코호트 내 성과 분포
        ROUND(STDDEV(gpa), 3) as gpa_stddev,
        MIN(gpa) as min_gpa,
        MAX(gpa) as max_gpa,
        -- 백분위수 계산
        APPROX_PERCENTILE(gpa, 0.25) as gpa_q1,
        APPROX_PERCENTILE(gpa, 0.5) as gpa_median,
        APPROX_PERCENTILE(gpa, 0.75) as gpa_q3
    FROM ai_usage_cohorts
    GROUP BY usage_cohort, satisfaction_segment, field_of_study
    HAVING COUNT(*) >= 5  -- 최소 5명 이상인 코호트만
)
SELECT 
    field_of_study,
    usage_cohort,
    satisfaction_segment,
    cohort_size,
    avg_gpa,
    gpa_median,
    avg_attendance,
    avg_usage_frequency,
    avg_satisfaction,
    avg_tools_used,
    -- 성과 지수 계산 (GPA와 출석률의 가중 평균)
    ROUND((avg_gpa * 0.7 + avg_attendance * 4 * 0.3), 3) as performance_index,
    -- 코호트 순위 (전공 내에서)
    RANK() OVER (
        PARTITION BY field_of_study 
        ORDER BY avg_gpa DESC
    ) as performance_rank_in_field
FROM cohort_analysis
ORDER BY field_of_study, performance_index DESC;
```

### 3.2 복잡한 서브쿼리와 CTE 사용법

Common Table Expressions(CTE)를 사용하여 복잡한 분석을 단계별로 구성해보겠습니다.

#### 다단계 분석 - 학습 효과성 평가

```sql
-- 다단계 CTE를 활용한 학습 효과성 종합 분석
WITH 
-- 1단계: 기본 메트릭 계산
base_metrics AS (
    SELECT 
        student_id,
        field_of_study,
        year_of_study,
        gpa,
        usage_frequency_score,
        satisfaction_level,
        num_ai_tools,
        attendance_rate,
        assignment_submission_rate,
        -- 학습 참여도 점수
        (attendance_rate * 0.4 + assignment_submission_rate * 0.6) as engagement_score,
        -- AI 활용도 점수
        (usage_frequency_score * 0.5 + satisfaction_level * 0.3 + num_ai_tools * 0.2) as ai_utilization_score
    FROM integrated_student_analysis
    WHERE gpa IS NOT NULL 
      AND usage_frequency_score IS NOT NULL
      AND attendance_rate IS NOT NULL
),

-- 2단계: 전공별 벤치마크 계산
field_benchmarks AS (
    SELECT 
        field_of_study,
        AVG(gpa) as field_avg_gpa,
        AVG(engagement_score) as field_avg_engagement,
        AVG(ai_utilization_score) as field_avg_ai_utilization,
        STDDEV(gpa) as field_gpa_stddev,
        COUNT(*) as field_student_count
    FROM base_metrics
    GROUP BY field_of_study
),

-- 3단계: 개별 학생의 상대적 성과 계산
relative_performance AS (
    SELECT 
        bm.*,
        fb.field_avg_gpa,
        fb.field_avg_engagement,
        fb.field_avg_ai_utilization,
        fb.field_gpa_stddev,
        -- 전공 평균 대비 성과
        ROUND((bm.gpa - fb.field_avg_gpa), 3) as gpa_vs_field_avg,
        ROUND((bm.engagement_score - fb.field_avg_engagement), 3) as engagement_vs_field_avg,
        ROUND((bm.ai_utilization_score - fb.field_avg_ai_utilization), 3) as ai_utilization_vs_field_avg,
        -- Z-score 계산
        CASE 
            WHEN fb.field_gpa_stddev > 0 THEN 
                ROUND((bm.gpa - fb.field_avg_gpa) / fb.field_gpa_stddev, 3)
            ELSE 0
        END as gpa_z_score
    FROM base_metrics bm
    JOIN field_benchmarks fb ON bm.field_of_study = fb.field_of_study
),

-- 4단계: 학습 효과성 분류
learning_effectiveness AS (
    SELECT 
        *,
        -- 종합 효과성 점수
        ROUND(
            (CASE WHEN gpa_z_score > 1 THEN 3
                  WHEN gpa_z_score > 0 THEN 2
                  WHEN gpa_z_score > -1 THEN 1
                  ELSE 0 END) * 0.4 +
            (CASE WHEN engagement_vs_field_avg > 0.1 THEN 3
                  WHEN engagement_vs_field_avg > 0 THEN 2
                  WHEN engagement_vs_field_avg > -0.1 THEN 1
                  ELSE 0 END) * 0.3 +
            (CASE WHEN ai_utilization_vs_field_avg > 0.5 THEN 3
                  WHEN ai_utilization_vs_field_avg > 0 THEN 2
                  WHEN ai_utilization_vs_field_avg > -0.5 THEN 1
                  ELSE 0 END) * 0.3, 1
        ) as effectiveness_score,
        -- 학습자 유형 분류
        CASE 
            WHEN gpa_z_score > 1 AND ai_utilization_vs_field_avg > 0.5 THEN 'High Achiever + AI Savvy'
            WHEN gpa_z_score > 1 AND ai_utilization_vs_field_avg <= 0 THEN 'High Achiever + Traditional'
            WHEN gpa_z_score <= 0 AND ai_utilization_vs_field_avg > 0.5 THEN 'Struggling + AI Dependent'
            WHEN gpa_z_score <= 0 AND engagement_vs_field_avg <= 0 THEN 'At Risk'
            ELSE 'Average Performer'
        END as learner_type
    FROM relative_performance
)

-- 5단계: 최종 분석 결과
SELECT 
    field_of_study,
    learner_type,
    COUNT(*) as student_count,
    ROUND(AVG(gpa), 3) as avg_gpa,
    ROUND(AVG(effectiveness_score), 2) as avg_effectiveness_score,
    ROUND(AVG(engagement_score), 3) as avg_engagement,
    ROUND(AVG(ai_utilization_score), 2) as avg_ai_utilization,
    -- 성과 지표
    ROUND(AVG(gpa_vs_field_avg), 3) as avg_gpa_vs_field,
    ROUND(AVG(engagement_vs_field_avg), 3) as avg_engagement_vs_field,
    ROUND(AVG(ai_utilization_vs_field_avg), 2) as avg_ai_utilization_vs_field,
    -- 분포 정보
    MIN(effectiveness_score) as min_effectiveness,
    MAX(effectiveness_score) as max_effectiveness,
    APPROX_PERCENTILE(effectiveness_score, 0.5) as median_effectiveness
FROM learning_effectiveness
GROUP BY field_of_study, learner_type
HAVING COUNT(*) >= 3
ORDER BY field_of_study, avg_effectiveness_score DESC;
```

#### 복잡한 조건부 집계

```sql
-- 조건부 집계를 활용한 세그먼트별 상세 분석
WITH segment_analysis AS (
    SELECT 
        field_of_study,
        -- 다양한 조건부 집계
        COUNT(*) as total_students,
        
        -- GPA 구간별 분포
        COUNT(CASE WHEN gpa >= 3.5 THEN 1 END) as high_gpa_count,
        COUNT(CASE WHEN gpa BETWEEN 2.5 AND 3.49 THEN 1 END) as medium_gpa_count,
        COUNT(CASE WHEN gpa < 2.5 THEN 1 END) as low_gpa_count,
        
        -- AI 사용 패턴별 분포
        COUNT(CASE WHEN usage_frequency_score >= 4 THEN 1 END) as high_usage_count,
        COUNT(CASE WHEN usage_frequency_score BETWEEN 2 AND 3.99 THEN 1 END) as medium_usage_count,
        COUNT(CASE WHEN usage_frequency_score < 2 THEN 1 END) as low_usage_count,
        
        -- 교차 분석: 고성과 + 고사용
        COUNT(CASE WHEN gpa >= 3.5 AND usage_frequency_score >= 4 THEN 1 END) as high_gpa_high_usage,
        COUNT(CASE WHEN gpa >= 3.5 AND usage_frequency_score < 2 THEN 1 END) as high_gpa_low_usage,
        COUNT(CASE WHEN gpa < 2.5 AND usage_frequency_score >= 4 THEN 1 END) as low_gpa_high_usage,
        COUNT(CASE WHEN gpa < 2.5 AND usage_frequency_score < 2 THEN 1 END) as low_gpa_low_usage,
        
        -- 조건부 평균 계산
        AVG(CASE WHEN usage_frequency_score >= 4 THEN gpa END) as avg_gpa_high_users,
        AVG(CASE WHEN usage_frequency_score < 2 THEN gpa END) as avg_gpa_low_users,
        
        -- 조건부 표준편차
        STDDEV(CASE WHEN usage_frequency_score >= 4 THEN gpa END) as stddev_gpa_high_users,
        STDDEV(CASE WHEN usage_frequency_score < 2 THEN gpa END) as stddev_gpa_low_users,
        
        -- 위험군 식별
        COUNT(CASE WHEN gpa < 2.5 AND attendance_rate < 0.7 THEN 1 END) as at_risk_students,
        COUNT(CASE WHEN gpa >= 3.5 AND usage_frequency_score >= 4 AND satisfaction_level >= 4 THEN 1 END) as star_performers
        
    FROM integrated_student_analysis
    WHERE gpa IS NOT NULL AND usage_frequency_score IS NOT NULL
    GROUP BY field_of_study
)
SELECT 
    field_of_study,
    total_students,
    
    -- 비율 계산
    ROUND(100.0 * high_gpa_count / total_students, 1) as high_gpa_pct,
    ROUND(100.0 * medium_gpa_count / total_students, 1) as medium_gpa_pct,
    ROUND(100.0 * low_gpa_count / total_students, 1) as low_gpa_pct,
    
    ROUND(100.0 * high_usage_count / total_students, 1) as high_usage_pct,
    ROUND(100.0 * medium_usage_count / total_students, 1) as medium_usage_pct,
    ROUND(100.0 * low_usage_count / total_students, 1) as low_usage_pct,
    
    -- 교차 분석 비율
    ROUND(100.0 * high_gpa_high_usage / total_students, 1) as high_gpa_high_usage_pct,
    ROUND(100.0 * low_gpa_high_usage / total_students, 1) as low_gpa_high_usage_pct,
    
    -- 성과 차이 분석
    ROUND(avg_gpa_high_users - avg_gpa_low_users, 3) as gpa_difference_by_usage,
    
    -- 위험도 지표
    ROUND(100.0 * at_risk_students / total_students, 1) as at_risk_pct,
    ROUND(100.0 * star_performers / total_students, 1) as star_performer_pct,
    
    -- 효과성 지수 (고사용자의 성과 향상 정도)
    CASE 
        WHEN avg_gpa_low_users > 0 THEN 
            ROUND((avg_gpa_high_users / avg_gpa_low_users - 1) * 100, 1)
        ELSE NULL
    END as ai_effectiveness_index
    
FROM segment_analysis
ORDER BY ai_effectiveness_index DESC NULLS LAST;
```

### 3.3 성능 최적화를 위한 쿼리 튜닝

Athena에서 대용량 데이터를 효율적으로 처리하기 위한 최적화 기법을 살펴보겠습니다.

#### 파티션 프루닝 최적화

```sql
-- 파티션을 활용한 효율적인 쿼리
-- 좋은 예: 파티션 키를 WHERE 절에 명시
SELECT 
    field_of_study,
    COUNT(*) as student_count,
    AVG(gpa) as avg_gpa,
    AVG(usage_frequency_score) as avg_usage
FROM integrated_student_analysis
WHERE field_of_study IN ('Computer Science', 'Mathematics')  -- 파티션 프루닝
  AND semester = '2024-2'  -- 파티션 프루닝
  AND gpa IS NOT NULL
GROUP BY field_of_study;

-- 나쁜 예: 파티션 키에 함수 적용
-- SELECT * FROM table WHERE UPPER(field_of_study) = 'COMPUTER SCIENCE'

-- 시간 범위 쿼리 최적화
SELECT 
    DATE_TRUNC('month', CAST(last_updated AS DATE)) as month,
    field_of_study,
    COUNT(*) as monthly_count,
    AVG(gpa) as avg_monthly_gpa
FROM integrated_student_analysis
WHERE last_updated >= '2024-01-01'  -- 파티션 프루닝
  AND last_updated < '2024-12-31'   -- 파티션 프루닝
  AND field_of_study IS NOT NULL
GROUP BY DATE_TRUNC('month', CAST(last_updated AS DATE)), field_of_study
ORDER BY month, field_of_study;
```

#### 집계 최적화 기법

```sql
-- 효율적인 집계를 위한 쿼리 구조
WITH optimized_aggregation AS (
    -- 1. 필요한 컬럼만 선택하여 데이터 스캔 최소화
    SELECT 
        field_of_study,
        gpa,
        usage_frequency_score,
        satisfaction_level,
        num_ai_tools
    FROM integrated_student_analysis
    WHERE gpa IS NOT NULL 
      AND usage_frequency_score IS NOT NULL
      AND field_of_study IN ('Computer Science', 'Mathematics', 'Physics')  -- 조기 필터링
),
pre_aggregated AS (
    -- 2. 중간 집계로 데이터 크기 축소
    SELECT 
        field_of_study,
        -- 기본 통계
        COUNT(*) as student_count,
        SUM(gpa) as total_gpa,
        SUM(gpa * gpa) as sum_gpa_squared,
        SUM(usage_frequency_score) as total_usage,
        SUM(satisfaction_level) as total_satisfaction,
        SUM(num_ai_tools) as total_tools,
        -- 분포 계산을 위한 집계
        SUM(CASE WHEN gpa >= 3.5 THEN 1 ELSE 0 END) as high_performers,
        SUM(CASE WHEN usage_frequency_score >= 4 THEN 1 ELSE 0 END) as high_users,
        -- 상관관계 계산을 위한 집계
        SUM(gpa * usage_frequency_score) as gpa_usage_product,
        SUM(usage_frequency_score * satisfaction_level) as usage_satisfaction_product
    FROM optimized_aggregation
    GROUP BY field_of_study
)
-- 3. 최종 계산
SELECT 
    field_of_study,
    student_count,
    -- 평균 계산
    ROUND(total_gpa / student_count, 3) as avg_gpa,
    ROUND(total_usage / student_count, 2) as avg_usage,
    ROUND(total_satisfaction / student_count, 2) as avg_satisfaction,
    ROUND(total_tools / student_count, 1) as avg_tools,
    -- 표준편차 계산 (베셀 보정 적용)
    ROUND(
        SQRT(
            (sum_gpa_squared - (total_gpa * total_gpa / student_count)) / 
            (student_count - 1)
        ), 3
    ) as gpa_stddev,
    -- 비율 계산
    ROUND(100.0 * high_performers / student_count, 1) as high_performer_pct,
    ROUND(100.0 * high_users / student_count, 1) as high_user_pct,
    -- 상관관계 계산 (피어슨 상관계수 근사)
    ROUND(
        (gpa_usage_product - (total_gpa * total_usage / student_count)) /
        SQRT(
            (sum_gpa_squared - (total_gpa * total_gpa / student_count)) *
            (SUM(usage_frequency_score * usage_frequency_score) - (total_usage * total_usage / student_count))
        ), 3
    ) as gpa_usage_correlation
FROM pre_aggregated
ORDER BY student_count DESC;
```

#### 대용량 데이터 처리 최적화

```sql
-- 대용량 데이터 처리를 위한 최적화된 쿼리
-- LIMIT과 ORDER BY 최적화
SELECT 
    student_id,
    field_of_study,
    gpa,
    usage_frequency_score,
    -- 윈도우 함수 최적화: 파티션 크기 제한
    ROW_NUMBER() OVER (
        PARTITION BY field_of_study 
        ORDER BY gpa DESC
    ) as rank_in_field
FROM integrated_student_analysis
WHERE field_of_study IN ('Computer Science', 'Mathematics')  -- 파티션 제한
  AND gpa IS NOT NULL
QUALIFY rank_in_field <= 10  -- 각 전공별 상위 10명만
ORDER BY field_of_study, rank_in_field;

-- 샘플링을 활용한 대용량 데이터 분석
WITH sampled_data AS (
    SELECT *
    FROM integrated_student_analysis
    WHERE gpa IS NOT NULL
      AND MOD(ABS(HASH(student_id)), 100) < 10  -- 10% 샘플링
),
sample_analysis AS (
    SELECT 
        field_of_study,
        COUNT(*) * 10 as estimated_total,  -- 샘플링 비율로 전체 추정
        AVG(gpa) as sample_avg_gpa,
        STDDEV(gpa) as sample_gpa_stddev,
        AVG(usage_frequency_score) as sample_avg_usage
    FROM sampled_data
    GROUP BY field_of_study
)
SELECT 
    field_of_study,
    estimated_total,
    ROUND(sample_avg_gpa, 3) as estimated_avg_gpa,
    ROUND(sample_gpa_stddev, 3) as estimated_gpa_stddev,
    ROUND(sample_avg_usage, 2) as estimated_avg_usage,
    -- 신뢰구간 계산 (95% 신뢰도)
    ROUND(sample_avg_gpa - 1.96 * sample_gpa_stddev / SQRT(estimated_total), 3) as gpa_ci_lower,
    ROUND(sample_avg_gpa + 1.96 * sample_gpa_stddev / SQRT(estimated_total), 3) as gpa_ci_upper
FROM sample_analysis
ORDER BY estimated_total DESC;
```

#### 쿼리 성능 모니터링

```sql
-- 쿼리 실행 계획 분석을 위한 EXPLAIN 사용
EXPLAIN (TYPE DISTRIBUTED)
SELECT 
    field_of_study,
    COUNT(*) as student_count,
    AVG(gpa) as avg_gpa
FROM integrated_student_analysis
WHERE field_of_study = 'Computer Science'
  AND semester = '2024-2'
GROUP BY field_of_study;

-- 데이터 스캔량 최소화 확인
SELECT 
    '$path' as file_path,
    '$file_size' as file_size,
    COUNT(*) as record_count
FROM integrated_student_analysis
WHERE field_of_study = 'Computer Science'
  AND semester = '2024-2'
GROUP BY '$path', '$file_size'
ORDER BY CAST('$file_size' AS BIGINT) DESC;
```

---

## 실습 가이드: 고급 Athena 분석

### 단계 1: 윈도우 함수 실습

1. **기본 순위 함수 실습:**
   ```sql
   -- 전공별 상위 5명 학생 조회
   SELECT *
   FROM (
       SELECT 
           student_id, field_of_study, gpa,
           ROW_NUMBER() OVER (PARTITION BY field_of_study ORDER BY gpa DESC) as rank
       FROM integrated_student_analysis
       WHERE gpa IS NOT NULL
   )
   WHERE rank <= 5;
   ```

2. **이동 평균 계산:**
   ```sql
   -- 학생별 3학기 이동 평균 GPA
   SELECT 
       student_id, semester, gpa,
       AVG(gpa) OVER (
           PARTITION BY student_id 
           ORDER BY semester 
           ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
       ) as moving_avg_gpa
   FROM integrated_student_analysis
   WHERE gpa IS NOT NULL
   ORDER BY student_id, semester;
   ```

### 단계 2: CTE 복합 분석 실습

1. **다단계 CTE 구성:**
   - 기본 메트릭 계산
   - 벤치마크 설정
   - 상대적 성과 분석
   - 최종 분류

2. **결과 검증:**
   ```sql
   -- CTE 결과 검증
   SELECT 
       learner_type,
       COUNT(*) as count,
       AVG(effectiveness_score) as avg_score
   FROM (위의 CTE 쿼리)
   GROUP BY learner_type
   ORDER BY avg_score DESC;
   ```

### 단계 3: 성능 최적화 실습

1. **쿼리 실행 계획 분석:**
   ```sql
   EXPLAIN (TYPE DISTRIBUTED, FORMAT JSON)
   SELECT field_of_study, COUNT(*)
   FROM integrated_student_analysis
   GROUP BY field_of_study;
   ```

2. **파티션 프루닝 효과 측정:**
   - 파티션 필터 있는 쿼리 vs 없는 쿼리
   - 실행 시간 및 스캔 데이터량 비교

3. **집계 최적화 적용:**
   - 중간 집계 활용
   - 불필요한 컬럼 제거
   - 조기 필터링 적용

### 단계 4: 실무 분석 시나리오

1. **학습 효과성 대시보드 쿼리:**
   - 전공별 성과 지표
   - AI 사용 패턴 분석
   - 위험군 학생 식별

2. **트렌드 분석:**
   - 시계열 성과 변화
   - 코호트 분석
   - 예측 모델링 기초 데이터

---

## 학습 포인트

이 고급 Athena 분석 섹션을 통해 다음을 학습할 수 있습니다:

1. **윈도우 함수 마스터**: 순위, 백분위수, 이동 평균 등 고급 분석 기법
2. **CTE 활용**: 복잡한 분석을 단계별로 구성하는 방법
3. **성능 최적화**: 대용량 데이터 처리를 위한 쿼리 튜닝 기법
4. **실무 분석**: 비즈니스 인사이트 도출을 위한 실전 쿼리 작성
5. **모니터링**: 쿼리 성능 분석 및 최적화 방법

다음 섹션에서는 독립 수행 과제를 통해 학습한 내용을 종합적으로 활용해보겠습니다.--
-

## 독립 수행 과제

기본 워크샵과 심화 예제를 완료한 후, 학습한 내용을 종합적으로 활용할 수 있는 독립 수행 과제입니다. 다양한 난이도의 문제를 통해 실무 역량을 기를 수 있습니다.

### 4.1 초급 과제 (Level 1)

#### 과제 1-1: 기본 데이터 탐색 및 시각화

**목표**: 새로운 데이터셋을 활용하여 기본적인 데이터 분석 파이프라인을 구축합니다.

**과제 설명**:
1. Kaggle에서 "Student Performance in Exams" 데이터셋을 다운로드
2. S3에 업로드하고 Glue 크롤러로 테이블 생성
3. Athena를 사용하여 기본 통계 분석 수행

**구체적 요구사항**:
```sql
-- 다음 분석을 수행하세요:
-- 1. 성별, 인종/민족별 평균 점수 비교
-- 2. 부모 교육 수준이 학생 성과에 미치는 영향
-- 3. 시험 준비 과정 완료 여부와 성과의 관계
-- 4. 점심 프로그램 참여와 성과의 상관관계
```

**제출물**:
- S3 버킷 구조 스크린샷
- Glue 데이터 카탈로그 테이블 정보
- 분석 SQL 쿼리 5개 이상
- 주요 인사이트 요약 (500자 이내)

**평가 기준**:
- 데이터 업로드 및 카탈로그 생성 완료 (30%)
- SQL 쿼리 정확성 및 효율성 (40%)
- 인사이트 도출 및 해석 (30%)

---

#### 과제 1-2: 간단한 ETL 파이프라인 구축

**목표**: Glue Studio를 사용하여 시각적 ETL 파이프라인을 구성합니다.

**과제 설명**:
학생 성과 데이터를 정제하고 분석용 데이터마트를 생성하는 ETL 작업을 구현합니다.

**구체적 요구사항**:
1. **데이터 소스**: 원본 학생 성과 데이터
2. **변환 작업**:
   - 결측값 처리 (평균값 또는 최빈값으로 대체)
   - 점수 구간별 등급 생성 (A, B, C, D, F)
   - 종합 점수 계산 (수학, 읽기, 쓰기 평균)
3. **출력**: 정제된 데이터를 새로운 S3 경로에 Parquet 형식으로 저장

**제출물**:
- Glue Studio 워크플로우 스크린샷
- ETL 작업 실행 로그
- 변환 전후 데이터 비교 쿼리
- 데이터 품질 검증 결과

**평가 기준**:
- ETL 파이프라인 구성 완료 (40%)
- 데이터 변환 로직 정확성 (35%)
- 데이터 품질 검증 (25%)

---

### 4.2 중급 과제 (Level 2)

#### 과제 2-1: 다중 데이터 소스 통합 분석

**목표**: 여러 데이터 소스를 통합하여 복합적인 인사이트를 도출합니다.

**과제 설명**:
학생 성과 데이터와 추가 데이터셋(학교 정보, 지역 경제 데이터 등)을 결합하여 종합 분석을 수행합니다.

**데이터 소스**:
1. 기본 학생 성과 데이터
2. 학교별 정보 데이터 (예: 학교 규모, 예산, 교사 비율)
3. 지역별 경제 지표 데이터

**분석 요구사항**:
```sql
-- 다음 분석을 포함해야 합니다:
-- 1. 학교 규모별 학생 성과 차이 분석
-- 2. 지역 경제 수준과 교육 성과의 상관관계
-- 3. 교사 대 학생 비율이 성과에 미치는 영향
-- 4. 다중 요인을 고려한 성과 예측 모델 기초 데이터
```

**고급 요구사항**:
- 윈도우 함수를 활용한 순위 분석
- CTE를 사용한 복잡한 다단계 분석
- 통계적 유의성 검정 기초 계산

**제출물**:
- 데이터 통합 ERD 다이어그램
- 복합 분석 SQL 쿼리 (10개 이상)
- 인사이트 보고서 (1000자 이내)
- 개선 제안사항

**평가 기준**:
- 데이터 통합 설계 (25%)
- 분석 쿼리 복잡성 및 정확성 (40%)
- 인사이트 품질 (25%)
- 개선 제안 실용성 (10%)

---

#### 과제 2-2: 실시간 데이터 처리 시뮬레이션

**목표**: 배치 처리와 유사실시간 분석을 결합한 하이브리드 아키텍처를 구현합니다.

**과제 설명**:
학생 활동 로그 데이터를 시뮬레이션하여 실시간 모니터링 대시보드용 데이터를 생성합니다.

**구현 요구사항**:
1. **데이터 생성**: Python 스크립트로 시간별 학생 활동 로그 생성
2. **배치 처리**: 일일 집계 데이터 생성 (Glue ETL)
3. **증분 처리**: 신규 데이터만 처리하는 로직 구현
4. **모니터링**: CloudWatch 메트릭 설정

**기술 스택**:
- AWS Glue (ETL)
- Amazon Athena (분석)
- Amazon S3 (저장)
- AWS CloudWatch (모니터링)

**제출물**:
- 데이터 생성 Python 스크립트
- 증분 처리 ETL 코드
- 실시간 분석 쿼리 예제
- 모니터링 대시보드 설정

**평가 기준**:
- 아키텍처 설계 (30%)
- 코드 품질 및 효율성 (35%)
- 모니터링 구현 (20%)
- 문서화 품질 (15%)

---

### 4.3 고급 과제 (Level 3)

#### 과제 3-1: 머신러닝 파이프라인 구축

**목표**: AWS 서비스를 활용하여 완전한 ML 파이프라인을 구축합니다.

**과제 설명**:
학생 성과 예측 모델을 개발하고 배포하는 end-to-end ML 파이프라인을 구현합니다.

**파이프라인 구성**:
1. **데이터 준비**: Glue ETL로 피처 엔지니어링
2. **모델 훈련**: SageMaker 또는 Glue ML Transform 사용
3. **모델 평가**: 교차 검증 및 성능 메트릭 계산
4. **배포**: 배치 예측 또는 실시간 추론 엔드포인트
5. **모니터링**: 모델 성능 추적

**고급 요구사항**:
```python
# 다음 기능을 포함해야 합니다:
# 1. 자동화된 피처 선택
# 2. 하이퍼파라미터 튜닝
# 3. 모델 버전 관리
# 4. A/B 테스트 기능
# 5. 드리프트 감지
```

**제출물**:
- 전체 아키텍처 다이어그램
- ETL 및 ML 코드 (Python/PySpark)
- 모델 성능 평가 보고서
- 배포 및 모니터링 가이드

**평가 기준**:
- 아키텍처 완성도 (25%)
- 코드 품질 및 모듈화 (30%)
- 모델 성능 (25%)
- 운영 고려사항 (20%)

---

#### 과제 3-2: 대용량 데이터 최적화 프로젝트

**목표**: 대용량 데이터 처리 최적화 기법을 실제로 적용합니다.

**과제 설명**:
10GB 이상의 대용량 교육 데이터를 효율적으로 처리하는 최적화된 솔루션을 구현합니다.

**최적화 영역**:
1. **스토리지 최적화**: 파티셔닝, 압축, 파일 형식
2. **쿼리 최적화**: 인덱싱, 쿼리 튜닝, 캐싱
3. **비용 최적화**: 스토리지 클래스, 라이프사이클 정책
4. **성능 최적화**: 병렬 처리, 메모리 관리

**성능 목표**:
- 쿼리 응답 시간 50% 단축
- 스토리지 비용 30% 절감
- 처리 처리량 2배 향상

**제출물**:
- 최적화 전후 성능 비교 보고서
- 최적화 기법 구현 코드
- 비용 분석 및 ROI 계산
- 모범 사례 가이드

**평가 기준**:
- 성능 개선 달성도 (40%)
- 최적화 기법 다양성 (30%)
- 비용 효율성 (20%)
- 문서화 및 재사용성 (10%)

---

### 4.4 팀 프로젝트 과제

#### 과제 4-1: 교육 데이터 분석 플랫폼 구축

**목표**: 팀 단위로 완전한 데이터 분석 플랫폼을 구축합니다.

**팀 구성**: 3-4명 (역할 분담 필수)
- 데이터 엔지니어: ETL 파이프라인 구축
- 데이터 분석가: 분석 로직 및 인사이트 도출
- 시스템 아키텍트: 전체 아키텍처 설계
- 프로젝트 매니저: 일정 관리 및 품질 보증

**프로젝트 범위**:
1. **데이터 수집**: 다양한 교육 관련 데이터 소스 통합
2. **데이터 처리**: 실시간 및 배치 처리 파이프라인
3. **분석 엔진**: 대화형 분석 및 자동화된 리포트
4. **시각화**: 대시보드 및 리포트 생성
5. **운영**: 모니터링, 알림, 백업

**기술 요구사항**:
- AWS 서비스 5개 이상 활용
- Infrastructure as Code (CloudFormation/CDK)
- CI/CD 파이프라인 구축
- 보안 및 거버넌스 구현

**제출물**:
- 프로젝트 계획서 및 아키텍처 문서
- 전체 소스 코드 (GitHub 저장소)
- 데모 비디오 (10분 이내)
- 최종 발표 자료

**평가 기준**:
- 기술적 완성도 (30%)
- 혁신성 및 창의성 (25%)
- 팀워크 및 협업 (20%)
- 발표 및 커뮤니케이션 (15%)
- 문서화 품질 (10%)

---

## 과제 제출 가이드

### 제출 방법

1. **GitHub 저장소 생성**:
   ```
   repository-name: aws-data-analysis-assignment-[학번]
   구조:
   ├── README.md
   ├── code/
   │   ├── etl/
   │   ├── sql/
   │   └── scripts/
   ├── docs/
   │   ├── analysis-report.md
   │   └── screenshots/
   └── data/
       └── sample-outputs/
   ```

2. **문서 작성 요구사항**:
   - README.md: 프로젝트 개요 및 실행 방법
   - 분석 보고서: 마크다운 형식
   - 코드 주석: 한글 또는 영어
   - 스크린샷: PNG 형식, 해상도 1920x1080 이상

3. **코드 품질 기준**:
   - PEP 8 스타일 가이드 준수 (Python)
   - SQL 포맷팅 일관성 유지
   - 에러 처리 로직 포함
   - 테스트 케이스 작성 (선택사항)

### 평가 루브릭

#### 기술적 역량 (60%)
- **우수 (90-100점)**: 모든 요구사항 완벽 구현, 추가 기능 포함
- **양호 (80-89점)**: 주요 요구사항 구현, 일부 고급 기능 포함
- **보통 (70-79점)**: 기본 요구사항 구현, 동작 확인
- **미흡 (60-69점)**: 일부 요구사항 미구현, 기본 동작
- **불량 (0-59점)**: 대부분 요구사항 미구현

#### 분석 품질 (25%)
- **우수**: 깊이 있는 인사이트, 실무 적용 가능
- **양호**: 의미 있는 분석 결과, 논리적 해석
- **보통**: 기본적인 분석, 표면적 해석
- **미흡**: 단순 집계, 해석 부족
- **불량**: 분석 결과 부정확 또는 부재

#### 문서화 (15%)
- **우수**: 완벽한 문서화, 재현 가능
- **양호**: 충분한 설명, 대부분 재현 가능
- **보통**: 기본 설명, 일부 재현 가능
- **미흡**: 불충분한 설명, 재현 어려움
- **불량**: 문서화 부재 또는 부정확

### 도움말 및 리소스

#### 참고 자료
- [AWS Glue 개발자 가이드](https://docs.aws.amazon.com/glue/)
- [Amazon Athena 사용자 가이드](https://docs.aws.amazon.com/athena/)
- [SQL 성능 튜닝 가이드](https://aws.amazon.com/blogs/big-data/)
- [데이터 분석 모범 사례](https://aws.amazon.com/big-data/datalakes-and-analytics/)

#### 질문 및 지원
- **Office Hours**: 매주 화요일 14:00-16:00
- **온라인 Q&A**: GitHub Discussions 활용
- **긴급 문의**: 이메일 support@university.edu

#### 추가 데이터셋
- [Kaggle Education Datasets](https://www.kaggle.com/datasets?search=education)
- [UCI Machine Learning Repository](https://archive.ics.uci.edu/ml/datasets.php)
- [AWS Open Data](https://aws.amazon.com/opendata/)

---

## 학습 성과 평가

### 자가 진단 체크리스트

완료한 과제에 대해 다음 항목을 체크해보세요:

#### 기술적 역량
- [ ] AWS 서비스 3개 이상을 효과적으로 활용했는가?
- [ ] ETL 파이프라인을 성공적으로 구축했는가?
- [ ] 복잡한 SQL 쿼리를 작성할 수 있는가?
- [ ] 데이터 품질 검증을 수행했는가?
- [ ] 성능 최적화를 고려했는가?

#### 분석 역량
- [ ] 비즈니스 문제를 데이터 문제로 변환할 수 있는가?
- [ ] 적절한 분석 방법을 선택했는가?
- [ ] 결과를 올바르게 해석했는가?
- [ ] 실행 가능한 인사이트를 도출했는가?
- [ ] 한계점을 인식하고 있는가?

#### 프로젝트 관리
- [ ] 명확한 목표를 설정했는가?
- [ ] 일정을 계획하고 준수했는가?
- [ ] 품질 관리를 수행했는가?
- [ ] 문서화를 충실히 했는가?
- [ ] 지속적인 개선을 고려했는가?

### 다음 단계 학습 가이드

과제 완료 후 다음 영역으로 학습을 확장해보세요:

#### 고급 AWS 서비스
- Amazon SageMaker (머신러닝)
- Amazon QuickSight (비즈니스 인텔리전스)
- AWS Lambda (서버리스 컴퓨팅)
- Amazon Kinesis (실시간 데이터 스트리밍)

#### 데이터 엔지니어링
- Apache Spark 고급 기능
- 데이터 레이크 아키텍처
- 스트리밍 데이터 처리
- 데이터 거버넌스

#### 데이터 사이언스
- 통계 분석 및 가설 검정
- 머신러닝 알고리즘
- 딥러닝 기초
- A/B 테스트

#### 비즈니스 분석
- 데이터 스토리텔링
- 시각화 디자인
- 비즈니스 메트릭 설계
- ROI 분석

---

이제 여러분은 AWS 기반 데이터 분석의 전 과정을 경험했습니다. 독립 수행 과제를 통해 실무 역량을 기르고, 지속적인 학습을 통해 데이터 전문가로 성장하시기 바랍니다!