#!/usr/bin/env python3
"""
데이터 품질 검증 스크립트
포괄적인 데이터 품질 검사 및 리포트 생성
"""

import sys
import boto3
import json
from datetime import datetime
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from pyspark.sql import functions as F
from pyspark.sql.types import *
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataQualityValidator:
    """데이터 품질 검증 클래스"""
    
    def __init__(self, spark_session, s3_client):
        self.spark = spark_session
        self.s3 = s3_client
        
    def comprehensive_quality_check(self, df, table_name, rules_config=None):
        """포괄적인 데이터 품질 검사"""
        logger.info(f"=== {table_name} 품질 검사 시작 ===")
        
        quality_report = {
            'table_name': table_name,
            'timestamp': datetime.now().isoformat(),
            'total_rows': df.count(),
            'total_columns': len(df.columns),
            'checks': {}
        }
        
        # 1. 기본 품질 검사
        quality_report['checks']['basic'] = self._basic_quality_checks(df)
        
        # 2. 비즈니스 규칙 검사
        if rules_config and 'business_rules' in rules_config:
            quality_report['checks']['business_rules'] = self._business_rule_checks(
                df, rules_config['business_rules']
            )
        
        # 3. 데이터 일관성 검사
        quality_report['checks']['consistency'] = self._consistency_checks(df)
        
        # 4. 통계적 이상값 검사
        quality_report['checks']['statistical_outliers'] = self._statistical_outlier_checks(df)
        
        # 5. 참조 무결성 검사
        if rules_config and 'reference_integrity' in rules_config:
            quality_report['checks']['reference_integrity'] = self._reference_integrity_checks(
                df, rules_config['reference_integrity']
            )
        
        logger.info(f"✓ {table_name} 품질 검사 완료")
        return quality_report
    
    def _basic_quality_checks(self, df):
        """기본 품질 검사: 결측값, 중복, 데이터 타입"""
        checks = {}
        total_rows = df.count()
        
        # 결측값 검사
        null_counts = {}
        for col in df.columns:
            null_count = df.filter(F.col(col).isNull()).count()
            null_counts[col] = {
                'count': null_count,
                'percentage': round((null_count / total_rows) * 100, 2) if total_rows > 0 else 0
            }
        checks['null_values'] = null_counts
        
        # 중복 검사
        unique_rows = df.dropDuplicates().count()
        checks['duplicates'] = {
            'total_duplicates': total_rows - unique_rows,
            'duplicate_percentage': round(((total_rows - unique_rows) / total_rows) * 100, 2) if total_rows > 0 else 0
        }
        
        # 데이터 타입 일관성
        checks['data_types'] = {col: str(df.schema[col].dataType) for col in df.columns}
        
        # 빈 문자열 검사
        empty_string_counts = {}
        for col in df.columns:
            if df.schema[col].dataType == StringType():
                empty_count = df.filter((F.col(col) == "") | (F.col(col) == " ")).count()
                empty_string_counts[col] = {
                    'count': empty_count,
                    'percentage': round((empty_count / total_rows) * 100, 2) if total_rows > 0 else 0
                }
        checks['empty_strings'] = empty_string_counts
        
        return checks
    
    def _business_rule_checks(self, df, rules):
        """비즈니스 규칙 검사"""
        checks = {}
        total_rows = df.count()
        
        for rule_name, rule_config in rules.items():
            try:
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
                        'invalid_percentage': round((invalid_count / total_rows) * 100, 2) if total_rows > 0 else 0,
                        'rule': f"{col} should be between {min_val} and {max_val}",
                        'status': 'PASS' if invalid_count == 0 else 'FAIL'
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
                        'invalid_percentage': round((invalid_count / total_rows) * 100, 2) if total_rows > 0 else 0,
                        'rule': f"{col} should be one of {valid_values}",
                        'status': 'PASS' if invalid_count == 0 else 'FAIL'
                    }
                    
                elif rule_config['type'] == 'pattern':
                    # 정규식 패턴 검사
                    col = rule_config['column']
                    pattern = rule_config['pattern']
                    
                    invalid_count = df.filter(
                        ~F.col(col).rlike(pattern)
                    ).count()
                    
                    checks[rule_name] = {
                        'invalid_count': invalid_count,
                        'invalid_percentage': round((invalid_count / total_rows) * 100, 2) if total_rows > 0 else 0,
                        'rule': f"{col} should match pattern {pattern}",
                        'status': 'PASS' if invalid_count == 0 else 'FAIL'
                    }
                    
            except Exception as e:
                checks[rule_name] = {
                    'error': str(e),
                    'status': 'ERROR'
                }
        
        return checks
    
    def _consistency_checks(self, df):
        """데이터 일관성 검사"""
        checks = {}
        total_rows = df.count()
        
        # 날짜 일관성 검사
        date_columns = [col for col, dtype in df.dtypes if 'date' in dtype.lower() or 'timestamp' in dtype.lower()]
        if len(date_columns) >= 2:
            # 첫 번째와 두 번째 날짜 컬럼 비교 (예: start_date < end_date)
            col1, col2 = date_columns[0], date_columns[1]
            invalid_dates = df.filter(F.col(col1) > F.col(col2)).count()
            
            checks['date_consistency'] = {
                'invalid_count': invalid_dates,
                'invalid_percentage': round((invalid_dates / total_rows) * 100, 2) if total_rows > 0 else 0,
                'rule': f"{col1} should be <= {col2}"
            }
        
        # 수치 일관성 검사
        numeric_columns = [col for col, dtype in df.dtypes if dtype in ['int', 'bigint', 'float', 'double']]
        
        # GPA 관련 일관성 (예: gpa vs major_gpa)
        if 'gpa' in df.columns and 'major_gpa' in df.columns:
            inconsistent_gpa = df.filter(
                F.abs(F.col('gpa') - F.col('major_gpa')) > 1.5
            ).count()
            
            checks['gpa_consistency'] = {
                'inconsistent_count': inconsistent_gpa,
                'inconsistent_percentage': round((inconsistent_gpa / total_rows) * 100, 2) if total_rows > 0 else 0,
                'rule': 'GPA and Major GPA should not differ by more than 1.5 points'
            }
        
        # 비율 필드 일관성 (0-1 범위)
        rate_columns = [col for col in df.columns if 'rate' in col.lower()]
        for col in rate_columns:
            if col in [c for c, dtype in df.dtypes if dtype in ['float', 'double']]:
                invalid_rates = df.filter(
                    (F.col(col) < 0) | (F.col(col) > 1)
                ).count()
                
                checks[f'{col}_range_consistency'] = {
                    'invalid_count': invalid_rates,
                    'invalid_percentage': round((invalid_rates / total_rows) * 100, 2) if total_rows > 0 else 0,
                    'rule': f'{col} should be between 0 and 1'
                }
        
        return checks
    
    def _statistical_outlier_checks(self, df):
        """통계적 이상값 검사"""
        checks = {}
        
        numeric_columns = [col for col, dtype in df.dtypes if dtype in ['int', 'bigint', 'float', 'double']]
        
        for col in numeric_columns:
            try:
                # 기본 통계 계산
                stats = df.select(
                    F.mean(col).alias('mean'),
                    F.stddev(col).alias('stddev'),
                    F.expr(f'percentile_approx({col}, 0.25)').alias('q1'),
                    F.expr(f'percentile_approx({col}, 0.75)').alias('q3')
                ).collect()[0]
                
                if stats['stddev'] is not None and stats['stddev'] > 0:
                    # Z-score 기반 이상값 (|z| > 3)
                    outliers_zscore = df.filter(
                        F.abs((F.col(col) - stats['mean']) / stats['stddev']) > 3
                    ).count()
                    
                    # IQR 기반 이상값
                    if stats['q1'] is not None and stats['q3'] is not None:
                        iqr = stats['q3'] - stats['q1']
                        lower_bound = stats['q1'] - 1.5 * iqr
                        upper_bound = stats['q3'] + 1.5 * iqr
                        
                        outliers_iqr = df.filter(
                            (F.col(col) < lower_bound) | (F.col(col) > upper_bound)
                        ).count()
                    else:
                        outliers_iqr = 0
                    
                    checks[col] = {
                        'zscore_outliers': outliers_zscore,
                        'iqr_outliers': outliers_iqr,
                        'mean': round(stats['mean'], 4) if stats['mean'] else None,
                        'stddev': round(stats['stddev'], 4) if stats['stddev'] else None,
                        'q1': round(stats['q1'], 4) if stats['q1'] else None,
                        'q3': round(stats['q3'], 4) if stats['q3'] else None
                    }
                    
            except Exception as e:
                checks[col] = {'error': str(e)}
        
        return checks
    
    def _reference_integrity_checks(self, df, ref_config):
        """참조 무결성 검사"""
        checks = {}
        
        for ref_name, ref_rule in ref_config.items():
            try:
                parent_table = ref_rule['parent_table']
                parent_key = ref_rule['parent_key']
                child_key = ref_rule['child_key']
                
                # 부모 테이블에서 유효한 키 값들 가져오기
                parent_df = self.spark.table(parent_table)
                valid_keys = [row[0] for row in parent_df.select(parent_key).distinct().collect()]
                
                # 자식 테이블에서 유효하지 않은 참조 찾기
                invalid_refs = df.filter(
                    ~F.col(child_key).isin(valid_keys)
                ).count()
                
                total_refs = df.filter(F.col(child_key).isNotNull()).count()
                
                checks[ref_name] = {
                    'invalid_references': invalid_refs,
                    'total_references': total_refs,
                    'invalid_percentage': round((invalid_refs / total_refs) * 100, 2) if total_refs > 0 else 0,
                    'rule': f"{child_key} must exist in {parent_table}.{parent_key}",
                    'status': 'PASS' if invalid_refs == 0 else 'FAIL'
                }
                
            except Exception as e:
                checks[ref_name] = {
                    'error': str(e),
                    'status': 'ERROR'
                }
        
        return checks
    
    def generate_quality_report(self, quality_results, output_path):
        """품질 검사 결과 리포트 생성"""
        overall_status = 'PASS'
        critical_issues = []
        warnings = []
        
        # 전체 상태 및 이슈 분석
        for table_result in quality_results:
            table_name = table_result['table_name']
            
            # 기본 품질 검사 결과 분석
            if 'basic' in table_result['checks']:
                basic_checks = table_result['checks']['basic']
                
                # 결측값 검사
                for col, null_info in basic_checks['null_values'].items():
                    if null_info['percentage'] > 50:
                        critical_issues.append(f"{table_name}.{col}: 결측값 {null_info['percentage']}%")
                        overall_status = 'FAIL'
                    elif null_info['percentage'] > 20:
                        warnings.append(f"{table_name}.{col}: 결측값 {null_info['percentage']}%")
                
                # 중복 검사
                if basic_checks['duplicates']['duplicate_percentage'] > 20:
                    critical_issues.append(f"{table_name}: 중복 데이터 {basic_checks['duplicates']['duplicate_percentage']}%")
                    overall_status = 'FAIL'
                elif basic_checks['duplicates']['duplicate_percentage'] > 5:
                    warnings.append(f"{table_name}: 중복 데이터 {basic_checks['duplicates']['duplicate_percentage']}%")
            
            # 비즈니스 규칙 검사 결과 분석
            if 'business_rules' in table_result['checks']:
                for rule_name, rule_result in table_result['checks']['business_rules'].items():
                    if rule_result.get('status') == 'FAIL':
                        if rule_result.get('invalid_percentage', 0) > 10:
                            critical_issues.append(f"{table_name}: {rule_name} 규칙 위반 {rule_result['invalid_percentage']}%")
                            overall_status = 'FAIL'
                        else:
                            warnings.append(f"{table_name}: {rule_name} 규칙 위반 {rule_result['invalid_percentage']}%")
        
        # 최종 리포트 생성
        report = {
            'summary': {
                'total_tables_checked': len(quality_results),
                'timestamp': datetime.now().isoformat(),
                'overall_status': overall_status,
                'critical_issues_count': len(critical_issues),
                'warnings_count': len(warnings),
                'critical_issues': critical_issues,
                'warnings': warnings
            },
            'detailed_results': quality_results,
            'recommendations': self._generate_recommendations(quality_results)
        }
        
        # S3에 리포트 저장
        try:
            report_json = json.dumps(report, indent=2, ensure_ascii=False)
            bucket = output_path.split('/')[2]
            key = '/'.join(output_path.split('/')[3:]) + '/quality_report.json'
            
            self.s3.put_object(
                Bucket=bucket,
                Key=key,
                Body=report_json.encode('utf-8'),
                ContentType='application/json'
            )
            
            logger.info(f"✓ 품질 리포트 저장 완료: s3://{bucket}/{key}")
            
        except Exception as e:
            logger.error(f"품질 리포트 저장 실패: {str(e)}")
        
        return report
    
    def _generate_recommendations(self, quality_results):
        """품질 개선 권장사항 생성"""
        recommendations = []
        
        for table_result in quality_results:
            table_name = table_result['table_name']
            
            # 결측값 관련 권장사항
            if 'basic' in table_result['checks']:
                for col, null_info in table_result['checks']['basic']['null_values'].items():
                    if null_info['percentage'] > 20:
                        recommendations.append({
                            'table': table_name,
                            'column': col,
                            'issue': f"높은 결측값 비율 ({null_info['percentage']}%)",
                            'recommendation': "데이터 수집 프로세스 검토 또는 기본값 설정 고려"
                        })
                
                # 중복 데이터 관련 권장사항
                if table_result['checks']['basic']['duplicates']['duplicate_percentage'] > 5:
                    recommendations.append({
                        'table': table_name,
                        'issue': f"중복 데이터 ({table_result['checks']['basic']['duplicates']['duplicate_percentage']}%)",
                        'recommendation': "데이터 중복 제거 로직 추가 또는 유니크 제약조건 설정"
                    })
            
            # 통계적 이상값 관련 권장사항
            if 'statistical_outliers' in table_result['checks']:
                for col, outlier_info in table_result['checks']['statistical_outliers'].items():
                    if isinstance(outlier_info, dict) and outlier_info.get('zscore_outliers', 0) > 0:
                        recommendations.append({
                            'table': table_name,
                            'column': col,
                            'issue': f"통계적 이상값 감지 ({outlier_info['zscore_outliers']}개)",
                            'recommendation': "이상값 원인 분석 및 데이터 검증 프로세스 강화"
                        })
        
        return recommendations

def main():
    """메인 실행 함수"""
    args = getResolvedOptions(sys.argv, ['JOB_NAME', 'S3_BUCKET'])
    
    sc = SparkContext()
    glueContext = GlueContext(sc)
    spark = glueContext.spark_session
    job = Job(glueContext)
    job.init(args['JOB_NAME'], args)
    
    s3_client = boto3.client('s3')
    validator = DataQualityValidator(spark, s3_client)
    
    try:
        logger.info("=== 데이터 품질 검증 작업 시작 ===")
        
        # 품질 검증 규칙 정의
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
                    },
                    'student_id_pattern': {
                        'type': 'pattern',
                        'column': 'student_id',
                        'pattern': '^STU_[0-9]{4}$'
                    }
                }
            },
            'academic_performance': {
                'business_rules': {
                    'gpa_range': {
                        'type': 'range',
                        'column': 'gpa',
                        'min': 0.0,
                        'max': 4.0
                    },
                    'attendance_rate_range': {
                        'type': 'range',
                        'column': 'attendance_rate',
                        'min': 0.0,
                        'max': 1.0
                    }
                }
            }
        }
        
        # 각 테이블에 대해 품질 검증 수행
        quality_results = []
        
        tables_to_check = ['ai_tool_usage', 'academic_performance', 'course_enrollment']
        
        for table_name in tables_to_check:
            try:
                # 테이블 읽기
                df = glueContext.create_dynamic_frame.from_catalog(
                    database="workshop_database",
                    table_name=table_name
                ).toDF()
                
                # 품질 검증 수행
                table_rules = quality_rules.get(table_name, {})
                quality_result = validator.comprehensive_quality_check(df, table_name, table_rules)
                quality_results.append(quality_result)
                
            except Exception as e:
                logger.error(f"테이블 {table_name} 품질 검증 실패: {str(e)}")
                quality_results.append({
                    'table_name': table_name,
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                })
        
        # 품질 리포트 생성 및 저장
        output_path = f"s3://{args['S3_BUCKET']}/quality-reports"
        report = validator.generate_quality_report(quality_results, output_path)
        
        logger.info(f"=== 품질 검증 완료 ===")
        logger.info(f"전체 상태: {report['summary']['overall_status']}")
        logger.info(f"심각한 이슈: {report['summary']['critical_issues_count']}개")
        logger.info(f"경고: {report['summary']['warnings_count']}개")
        
    except Exception as e:
        logger.error(f"품질 검증 작업 실패: {str(e)}")
        raise
    finally:
        job.commit()

if __name__ == "__main__":
    main()