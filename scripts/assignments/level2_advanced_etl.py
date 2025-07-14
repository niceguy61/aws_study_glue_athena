#!/usr/bin/env python3
"""
Level 2 Assignment: Advanced ETL Pipeline
다중 데이터 소스 통합 및 고급 ETL 파이프라인 구축

이 스크립트는 과제 2-1의 참고 예제입니다.
실제 과제에서는 여러분이 직접 구현해야 합니다.
"""

import sys
import boto3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from awsglue.dynamicframe import DynamicFrame
from pyspark.sql import functions as F
from pyspark.sql.types import *

class AdvancedETLPipeline:
    """고급 ETL 파이프라인 클래스"""
    
    def __init__(self, glue_context, spark_session, s3_bucket):
        self.glue_context = glue_context
        self.spark = spark_session
        self.s3_bucket = s3_bucket
        self.s3_client = boto3.client('s3')
    
    def generate_school_info_data(self, num_schools=50):
        """학교 정보 데이터 생성"""
        np.random.seed(123)
        
        school_types = ['public', 'private', 'charter']
        school_sizes = ['small', 'medium', 'large']
        regions = ['urban', 'suburban', 'rural']
        
        schools = []
        for i in range(num_schools):
            school_id = f"SCH_{i+1:03d}"
            school_type = np.random.choice(school_types, p=[0.7, 0.2, 0.1])
            size = np.random.choice(school_sizes, p=[0.3, 0.5, 0.2])
            region = np.random.choice(regions, p=[0.3, 0.4, 0.3])
            
            # 학교 규모에 따른 학생 수
            if size == 'small':
                student_count = np.random.randint(200, 500)
            elif size == 'medium':
                student_count = np.random.randint(500, 1200)
            else:
                student_count = np.random.randint(1200, 3000)
            
            # 교사 수 (학생 대 교사 비율 고려)
            teacher_ratio = np.random.uniform(12, 25)  # 학생 12-25명당 교사 1명
            teacher_count = max(10, int(student_count / teacher_ratio))
            
            # 예산 (학생 수와 학교 유형에 따라)
            base_budget = student_count * np.random.uniform(8000, 15000)
            if school_type == 'private':
                base_budget *= 1.5
            elif school_type == 'charter':
                base_budget *= 0.9
            
            schools.append({
                'school_id': school_id,
                'school_name': f"{region.title()} {school_type.title()} School {i+1}",
                'school_type': school_type,
                'school_size': size,
                'region': region,
                'student_count': student_count,
                'teacher_count': teacher_count,
                'student_teacher_ratio': round(student_count / teacher_count, 1),
                'annual_budget': int(base_budget),
                'budget_per_student': int(base_budget / student_count),
                'established_year': np.random.randint(1950, 2010),
                'has_advanced_programs': np.random.choice([True, False], p=[0.4, 0.6]),
                'technology_score': np.random.randint(1, 10),  # 1-10 기술 수준
                'facility_score': np.random.randint(1, 10)     # 1-10 시설 수준
            })
        
        return pd.DataFrame(schools)
    
    def generate_regional_economic_data(self):
        """지역별 경제 지표 데이터 생성"""
        regions = ['urban', 'suburban', 'rural']
        
        economic_data = []
        for region in regions:
            # 지역별 경제 특성 반영
            if region == 'urban':
                median_income = np.random.normal(65000, 15000)
                unemployment_rate = np.random.uniform(3, 8)
                poverty_rate = np.random.uniform(8, 20)
                college_grad_rate = np.random.uniform(35, 55)
            elif region == 'suburban':
                median_income = np.random.normal(75000, 20000)
                unemployment_rate = np.random.uniform(2, 6)
                poverty_rate = np.random.uniform(5, 15)
                college_grad_rate = np.random.uniform(40, 65)
            else:  # rural
                median_income = np.random.normal(45000, 12000)
                unemployment_rate = np.random.uniform(4, 12)
                poverty_rate = np.random.uniform(10, 25)
                college_grad_rate = np.random.uniform(20, 40)
            
            economic_data.append({
                'region': region,
                'median_household_income': max(25000, int(median_income)),
                'unemployment_rate': round(max(1, unemployment_rate), 1),
                'poverty_rate': round(max(2, poverty_rate), 1),
                'college_graduation_rate': round(max(15, college_grad_rate), 1),
                'cost_of_living_index': np.random.uniform(85, 125),
                'population_density': {
                    'urban': np.random.randint(1000, 5000),
                    'suburban': np.random.randint(100, 1000),
                    'rural': np.random.randint(10, 100)
                }[region],
                'internet_access_rate': {
                    'urban': np.random.uniform(85, 95),
                    'suburban': np.random.uniform(80, 90),
                    'rural': np.random.uniform(60, 80)
                }[region]
            })
        
        return pd.DataFrame(economic_data)
    
    def enhance_student_data_with_school_info(self, student_df, school_df):
        """학생 데이터에 학교 정보 추가"""
        # 학생들을 학교에 랜덤 배정
        np.random.seed(456)
        
        enhanced_students = []
        for _, student in student_df.iterrows():
            # 학교 랜덤 선택 (가중치 적용)
            school = school_df.sample(n=1, weights=school_df['student_count']).iloc[0]
            
            # 학교 특성이 성과에 미치는 영향 계산
            school_effect = 0
            
            # 학교 유형 효과
            if school['school_type'] == 'private':
                school_effect += 5
            elif school['school_type'] == 'charter':
                school_effect += 2
            
            # 학생-교사 비율 효과
            if school['student_teacher_ratio'] < 15:
                school_effect += 3
            elif school['student_teacher_ratio'] > 20:
                school_effect -= 2
            
            # 예산 효과
            if school['budget_per_student'] > 12000:
                school_effect += 3
            elif school['budget_per_student'] < 8000:
                school_effect -= 2
            
            # 시설 및 기술 효과
            school_effect += (school['technology_score'] - 5) * 0.5
            school_effect += (school['facility_score'] - 5) * 0.3
            
            # 성과 점수 조정
            adjusted_scores = {}
            for subject in ['math_score', 'reading_score', 'writing_score']:
                original_score = student[subject]
                adjusted_score = original_score + school_effect + np.random.normal(0, 2)
                adjusted_scores[subject] = max(0, min(100, int(adjusted_score)))
            
            # 새로운 총점 및 평균 계산
            total_score = sum(adjusted_scores.values())
            average_score = total_score / 3
            
            enhanced_student = student.to_dict()
            enhanced_student.update({
                'school_id': school['school_id'],
                'school_name': school['school_name'],
                'school_type': school['school_type'],
                'school_size': school['school_size'],
                'region': school['region'],
                'student_teacher_ratio': school['student_teacher_ratio'],
                'budget_per_student': school['budget_per_student'],
                'technology_score': school['technology_score'],
                'facility_score': school['facility_score'],
                'math_score': adjusted_scores['math_score'],
                'reading_score': adjusted_scores['reading_score'],
                'writing_score': adjusted_scores['writing_score'],
                'total_score': total_score,
                'average_score': round(average_score, 1),
                'school_effect': round(school_effect, 1)
            })
            
            enhanced_students.append(enhanced_student)
        
        return pd.DataFrame(enhanced_students)
    
    def create_data_quality_rules(self):
        """데이터 품질 검증 규칙 정의"""
        return {
            'student_performance': {
                'required_columns': [
                    'student_id', 'math_score', 'reading_score', 'writing_score'
                ],
                'score_range': {'min': 0, 'max': 100},
                'null_tolerance': {'math_score': 0, 'reading_score': 0, 'writing_score': 0},
                'duplicate_check': ['student_id']
            },
            'school_info': {
                'required_columns': [
                    'school_id', 'student_count', 'teacher_count', 'annual_budget'
                ],
                'positive_values': ['student_count', 'teacher_count', 'annual_budget'],
                'null_tolerance': {'school_id': 0, 'student_count': 0}
            },
            'economic_data': {
                'required_columns': [
                    'region', 'median_household_income', 'unemployment_rate'
                ],
                'range_checks': {
                    'unemployment_rate': {'min': 0, 'max': 30},
                    'poverty_rate': {'min': 0, 'max': 50}
                }
            }
        }
    
    def validate_data_quality(self, df, table_name, rules):
        """데이터 품질 검증"""
        print(f"=== {table_name} 데이터 품질 검증 ===")
        
        quality_report = {
            'table_name': table_name,
            'total_rows': len(df),
            'issues': []
        }
        
        table_rules = rules.get(table_name, {})
        
        # 필수 컬럼 확인
        if 'required_columns' in table_rules:
            missing_cols = set(table_rules['required_columns']) - set(df.columns)
            if missing_cols:
                quality_report['issues'].append(f"Missing columns: {missing_cols}")
        
        # 결측값 확인
        if 'null_tolerance' in table_rules:
            for col, tolerance in table_rules['null_tolerance'].items():
                if col in df.columns:
                    null_count = df[col].isnull().sum()
                    null_rate = null_count / len(df)
                    if null_rate > tolerance:
                        quality_report['issues'].append(
                            f"{col}: {null_count} null values ({null_rate:.2%})"
                        )
        
        # 범위 확인
        if 'score_range' in table_rules:
            score_cols = ['math_score', 'reading_score', 'writing_score']
            for col in score_cols:
                if col in df.columns:
                    min_val, max_val = table_rules['score_range']['min'], table_rules['score_range']['max']
                    out_of_range = df[(df[col] < min_val) | (df[col] > max_val)]
                    if len(out_of_range) > 0:
                        quality_report['issues'].append(
                            f"{col}: {len(out_of_range)} values out of range [{min_val}, {max_val}]"
                        )
        
        # 중복 확인
        if 'duplicate_check' in table_rules:
            for col in table_rules['duplicate_check']:
                if col in df.columns:
                    duplicates = df[df.duplicated(subset=[col])]
                    if len(duplicates) > 0:
                        quality_report['issues'].append(
                            f"{col}: {len(duplicates)} duplicate values"
                        )
        
        # 결과 출력
        if quality_report['issues']:
            print(f"❌ {len(quality_report['issues'])} issues found:")
            for issue in quality_report['issues']:
                print(f"   - {issue}")
        else:
            print("✓ No data quality issues found")
        
        return quality_report
    
    def create_advanced_etl_job(self):
        """고급 ETL 작업 생성"""
        etl_script = '''
import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from awsglue.dynamicframe import DynamicFrame
from pyspark.sql import functions as F
from pyspark.sql.types import *
from pyspark.sql.window import Window

# Job 초기화
args = getResolvedOptions(sys.argv, ['JOB_NAME', 'S3_BUCKET'])
sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args['JOB_NAME'], args)

s3_bucket = args['S3_BUCKET']

try:
    print("=== Advanced ETL Pipeline Started ===")
    
    # 1. 데이터 소스 읽기
    print("1. Reading data sources...")
    
    # 학생 성과 데이터
    student_df = glueContext.create_dynamic_frame.from_catalog(
        database="workshop_database",
        table_name="enhanced_student_performance"
    ).toDF()
    
    # 학교 정보 데이터
    school_df = glueContext.create_dynamic_frame.from_catalog(
        database="workshop_database", 
        table_name="school_info"
    ).toDF()
    
    # 경제 데이터
    economic_df = glueContext.create_dynamic_frame.from_catalog(
        database="workshop_database",
        table_name="regional_economic_data"
    ).toDF()
    
    print(f"   Student records: {student_df.count()}")
    print(f"   School records: {school_df.count()}")
    print(f"   Economic records: {economic_df.count()}")
    
    # 2. 데이터 정제 및 변환
    print("2. Data cleaning and transformation...")
    
    # 학생 데이터 정제
    student_clean = student_df.filter(
        (F.col("math_score").isNotNull()) &
        (F.col("reading_score").isNotNull()) &
        (F.col("writing_score").isNotNull()) &
        (F.col("math_score") >= 0) & (F.col("math_score") <= 100) &
        (F.col("reading_score") >= 0) & (F.col("reading_score") <= 100) &
        (F.col("writing_score") >= 0) & (F.col("writing_score") <= 100)
    ).withColumn(
        "performance_tier",
        F.when(F.col("average_score") >= 90, "Excellent")
         .when(F.col("average_score") >= 80, "Good")
         .when(F.col("average_score") >= 70, "Average")
         .when(F.col("average_score") >= 60, "Below Average")
         .otherwise("Poor")
    ).withColumn(
        "subject_strength",
        F.when(
            (F.col("math_score") > F.col("reading_score")) & 
            (F.col("math_score") > F.col("writing_score")), "Math"
        ).when(
            (F.col("reading_score") > F.col("math_score")) & 
            (F.col("reading_score") > F.col("writing_score")), "Reading"
        ).when(
            (F.col("writing_score") > F.col("math_score")) & 
            (F.col("writing_score") > F.col("reading_score")), "Writing"
        ).otherwise("Balanced")
    )
    
    # 3. 복잡한 조인 및 집계
    print("3. Complex joins and aggregations...")
    
    # 학교별 성과 집계
    school_performance = student_clean.groupBy("school_id").agg(
        F.count("student_id").alias("total_students"),
        F.avg("average_score").alias("avg_school_score"),
        F.stddev("average_score").alias("score_stddev"),
        F.avg("math_score").alias("avg_math"),
        F.avg("reading_score").alias("avg_reading"),
        F.avg("writing_score").alias("avg_writing"),
        F.countDistinct("performance_tier").alias("performance_diversity"),
        F.sum(F.when(F.col("performance_tier") == "Excellent", 1).otherwise(0)).alias("excellent_count"),
        F.sum(F.when(F.col("performance_tier") == "Poor", 1).otherwise(0)).alias("poor_count")
    )
    
    # 학교 정보와 조인
    school_analysis = school_performance.join(
        school_df, on="school_id", how="inner"
    ).join(
        economic_df, on="region", how="inner"
    )
    
    # 4. 고급 분석 메트릭 계산
    print("4. Advanced analytics...")
    
    # 윈도우 함수를 사용한 순위 계산
    window_spec = Window.partitionBy("region").orderBy(F.desc("avg_school_score"))
    
    final_analysis = school_analysis.withColumn(
        "regional_rank", F.row_number().over(window_spec)
    ).withColumn(
        "regional_percentile", F.percent_rank().over(window_spec)
    ).withColumn(
        "efficiency_score",
        F.round(F.col("avg_school_score") / F.col("budget_per_student") * 1000, 2)
    ).withColumn(
        "equity_score",
        F.round(100 - (F.col("score_stddev") / F.col("avg_school_score") * 100), 2)
    ).withColumn(
        "socioeconomic_impact",
        F.round(
            F.col("avg_school_score") - 
            (F.col("median_household_income") / 1000 * 0.1), 2
        )
    )
    
    # 5. 결과 저장
    print("5. Saving results...")
    
    # 상세 분석 결과
    detailed_dynamic = DynamicFrame.fromDF(final_analysis, glueContext, "detailed_analysis")
    glueContext.write_dynamic_frame.from_options(
        frame=detailed_dynamic,
        connection_type="s3",
        connection_options={
            "path": f"s3://{s3_bucket}/advanced-analysis/detailed-school-analysis/",
            "partitionKeys": ["region", "school_type"]
        },
        format="parquet"
    )
    
    # 요약 통계
    summary_stats = final_analysis.groupBy("region", "school_type").agg(
        F.count("school_id").alias("school_count"),
        F.avg("avg_school_score").alias("regional_avg_score"),
        F.avg("efficiency_score").alias("avg_efficiency"),
        F.avg("equity_score").alias("avg_equity"),
        F.corr("budget_per_student", "avg_school_score").alias("budget_performance_corr"),
        F.corr("student_teacher_ratio", "avg_school_score").alias("ratio_performance_corr")
    )
    
    summary_dynamic = DynamicFrame.fromDF(summary_stats, glueContext, "summary_stats")
    glueContext.write_dynamic_frame.from_options(
        frame=summary_dynamic,
        connection_type="s3",
        connection_options={
            "path": f"s3://{s3_bucket}/advanced-analysis/summary-statistics/"
        },
        format="parquet"
    )
    
    print("✓ Advanced ETL Pipeline completed successfully")
    
except Exception as e:
    print(f"❌ ETL Pipeline failed: {str(e)}")
    raise

finally:
    job.commit()
        '''
        
        return etl_script
    
    def generate_advanced_analysis_queries(self):
        """고급 분석 쿼리 생성"""
        queries = {
            "school_effectiveness_analysis": """
            -- 학교 효과성 종합 분석
            WITH school_metrics AS (
                SELECT 
                    school_id,
                    school_name,
                    school_type,
                    region,
                    avg_school_score,
                    efficiency_score,
                    equity_score,
                    budget_per_student,
                    student_teacher_ratio,
                    regional_rank,
                    regional_percentile,
                    -- 종합 효과성 점수 계산
                    ROUND(
                        (avg_school_score * 0.4 + 
                         efficiency_score * 0.3 + 
                         equity_score * 0.3), 2
                    ) as overall_effectiveness
                FROM detailed_school_analysis
            )
            SELECT 
                region,
                school_type,
                COUNT(*) as school_count,
                ROUND(AVG(overall_effectiveness), 2) as avg_effectiveness,
                ROUND(AVG(avg_school_score), 2) as avg_performance,
                ROUND(AVG(efficiency_score), 2) as avg_efficiency,
                ROUND(AVG(equity_score), 2) as avg_equity,
                -- 상위 25% 학교 비율
                ROUND(100.0 * SUM(CASE WHEN regional_percentile >= 0.75 THEN 1 ELSE 0 END) / COUNT(*), 1) as top_quartile_pct,
                -- 예산 대비 성과 상관관계
                ROUND(CORR(budget_per_student, avg_school_score), 4) as budget_performance_corr
            FROM school_metrics
            GROUP BY region, school_type
            ORDER BY avg_effectiveness DESC;
            """,
            
            "socioeconomic_impact_analysis": """
            -- 사회경제적 요인이 교육 성과에 미치는 영향 분석
            WITH socioeconomic_analysis AS (
                SELECT 
                    s.*,
                    e.median_household_income,
                    e.unemployment_rate,
                    e.poverty_rate,
                    e.college_graduation_rate,
                    -- 사회경제적 지수 계산
                    ROUND(
                        (e.median_household_income / 1000 * 0.4 +
                         (100 - e.unemployment_rate) * 0.2 +
                         (100 - e.poverty_rate) * 0.2 +
                         e.college_graduation_rate * 0.2), 2
                    ) as socioeconomic_index
                FROM detailed_school_analysis s
                JOIN regional_economic_data e ON s.region = e.region
            )
            SELECT 
                region,
                COUNT(*) as school_count,
                ROUND(AVG(socioeconomic_index), 2) as avg_socioeconomic_index,
                ROUND(AVG(avg_school_score), 2) as avg_school_performance,
                ROUND(AVG(median_household_income), 0) as avg_household_income,
                ROUND(AVG(unemployment_rate), 1) as avg_unemployment_rate,
                ROUND(AVG(poverty_rate), 1) as avg_poverty_rate,
                -- 상관관계 분석
                ROUND(CORR(socioeconomic_index, avg_school_score), 4) as socioeconomic_performance_corr,
                ROUND(CORR(median_household_income, avg_school_score), 4) as income_performance_corr,
                ROUND(CORR(poverty_rate, avg_school_score), 4) as poverty_performance_corr,
                -- 격차 분석
                ROUND(MAX(avg_school_score) - MIN(avg_school_score), 2) as performance_gap,
                ROUND(STDDEV(avg_school_score), 2) as performance_stddev
            FROM socioeconomic_analysis
            GROUP BY region
            ORDER BY avg_socioeconomic_index DESC;
            """,
            
            "resource_optimization_analysis": """
            -- 교육 자원 최적화 분석
            WITH resource_efficiency AS (
                SELECT 
                    school_id,
                    school_name,
                    school_type,
                    region,
                    budget_per_student,
                    student_teacher_ratio,
                    technology_score,
                    facility_score,
                    avg_school_score,
                    efficiency_score,
                    -- 자원 활용도 점수
                    ROUND(
                        (technology_score * 0.3 +
                         facility_score * 0.3 +
                         (CASE WHEN student_teacher_ratio <= 15 THEN 10
                               WHEN student_teacher_ratio <= 20 THEN 7
                               WHEN student_teacher_ratio <= 25 THEN 5
                               ELSE 3 END) * 0.4), 2
                    ) as resource_utilization_score,
                    -- 비용 효율성 등급
                    CASE 
                        WHEN efficiency_score >= 8 THEN 'Highly Efficient'
                        WHEN efficiency_score >= 6 THEN 'Efficient'
                        WHEN efficiency_score >= 4 THEN 'Moderately Efficient'
                        ELSE 'Inefficient'
                    END as efficiency_grade
                FROM detailed_school_analysis
            )
            SELECT 
                efficiency_grade,
                school_type,
                COUNT(*) as school_count,
                ROUND(AVG(budget_per_student), 0) as avg_budget_per_student,
                ROUND(AVG(student_teacher_ratio), 1) as avg_student_teacher_ratio,
                ROUND(AVG(technology_score), 1) as avg_technology_score,
                ROUND(AVG(facility_score), 1) as avg_facility_score,
                ROUND(AVG(avg_school_score), 2) as avg_performance,
                ROUND(AVG(efficiency_score), 2) as avg_efficiency_score,
                ROUND(AVG(resource_utilization_score), 2) as avg_resource_utilization,
                -- 개선 잠재력 분석
                CASE 
                    WHEN AVG(efficiency_score) < 5 AND AVG(budget_per_student) > 10000 THEN 'High Improvement Potential'
                    WHEN AVG(efficiency_score) < 6 AND AVG(resource_utilization_score) < 6 THEN 'Medium Improvement Potential'
                    ELSE 'Optimized'
                END as improvement_potential
            FROM resource_efficiency
            GROUP BY efficiency_grade, school_type
            ORDER BY avg_efficiency_score DESC;
            """,
            
            "predictive_modeling_data": """
            -- 예측 모델링을 위한 피처 엔지니어링
            WITH modeling_features AS (
                SELECT 
                    s.school_id,
                    s.avg_school_score as target_performance,
                    -- 학교 특성 피처
                    CASE s.school_type 
                        WHEN 'public' THEN 0
                        WHEN 'charter' THEN 1
                        WHEN 'private' THEN 2
                    END as school_type_encoded,
                    CASE s.region
                        WHEN 'rural' THEN 0
                        WHEN 'suburban' THEN 1
                        WHEN 'urban' THEN 2
                    END as region_encoded,
                    s.budget_per_student,
                    s.student_teacher_ratio,
                    s.technology_score,
                    s.facility_score,
                    s.total_students,
                    -- 경제적 피처
                    e.median_household_income,
                    e.unemployment_rate,
                    e.poverty_rate,
                    e.college_graduation_rate,
                    e.internet_access_rate,
                    -- 파생 피처
                    s.budget_per_student / e.median_household_income * 100 as budget_income_ratio,
                    s.technology_score * e.internet_access_rate / 100 as tech_access_score,
                    (100 - e.poverty_rate) * s.budget_per_student / 1000 as economic_resource_index,
                    -- 상호작용 피처
                    s.student_teacher_ratio * s.total_students as class_size_impact,
                    s.technology_score * s.facility_score as infrastructure_score,
                    -- 정규화된 피처 (Z-score)
                    (s.budget_per_student - AVG(s.budget_per_student) OVER ()) / 
                    STDDEV(s.budget_per_student) OVER () as budget_zscore,
                    (s.student_teacher_ratio - AVG(s.student_teacher_ratio) OVER ()) / 
                    STDDEV(s.student_teacher_ratio) OVER () as ratio_zscore,
                    (e.median_household_income - AVG(e.median_household_income) OVER ()) / 
                    STDDEV(e.median_household_income) OVER () as income_zscore
                FROM detailed_school_analysis s
                JOIN regional_economic_data e ON s.region = e.region
            )
            SELECT 
                *,
                -- 성과 등급 (분류 모델용)
                CASE 
                    WHEN target_performance >= 85 THEN 'High'
                    WHEN target_performance >= 75 THEN 'Medium'
                    ELSE 'Low'
                END as performance_category,
                -- 훈련/테스트 분할 (80/20)
                CASE WHEN MOD(ABS(HASH(school_id)), 10) < 8 THEN 'train' ELSE 'test' END as dataset_split
            FROM modeling_features
            ORDER BY school_id;
            """
        }
        
        return queries

def main():
    """메인 실행 함수 - Glue Job에서 실행되는 경우"""
    try:
        # Glue Job 환경에서 실행되는 경우
        args = getResolvedOptions(sys.argv, ['JOB_NAME', 'S3_BUCKET'])
        sc = SparkContext()
        glueContext = GlueContext(sc)
        spark = glueContext.spark_session
        job = Job(glueContext)
        job.init(args['JOB_NAME'], args)
        
        s3_bucket = args['S3_BUCKET']
        
        # ETL 파이프라인 실행
        pipeline = AdvancedETLPipeline(glueContext, spark, s3_bucket)
        
        print("=== Advanced ETL Pipeline Execution ===")
        print("This would execute the full ETL pipeline...")
        print("For assignment purposes, please implement the pipeline step by step.")
        
        job.commit()
        
    except Exception as e:
        # 로컬 환경에서 실행되는 경우 (개발/테스트)
        print("=== Level 2 Assignment: Advanced ETL Pipeline ===")
        print("This script provides templates and examples for the advanced ETL assignment.")
        print("\nTo complete this assignment, you need to:")
        print("1. Generate multiple data sources")
        print("2. Implement data quality validation")
        print("3. Create complex ETL transformations")
        print("4. Build advanced analytics queries")
        print("5. Document insights and recommendations")
        
        # 예제 코드 실행
        pipeline = AdvancedETLPipeline(None, None, "your-workshop-bucket")
        
        # 샘플 데이터 생성 예제
        print("\n=== Sample Data Generation ===")
        school_data = pipeline.generate_school_info_data(20)
        print(f"Generated {len(school_data)} school records")
        
        economic_data = pipeline.generate_regional_economic_data()
        print(f"Generated {len(economic_data)} economic records")
        
        # 데이터 품질 규칙 예제
        print("\n=== Data Quality Rules ===")
        quality_rules = pipeline.create_data_quality_rules()
        print("Quality rules defined for:", list(quality_rules.keys()))
        
        # 고급 쿼리 예제
        print("\n=== Advanced Analysis Queries ===")
        queries = pipeline.generate_advanced_analysis_queries()
        print(f"Generated {len(queries)} advanced analysis queries")
        
        # 쿼리를 파일로 저장
        for query_name, query_sql in queries.items():
            filename = f"advanced_{query_name}.sql"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(query_sql)
            print(f"   - {filename} saved")
        
        print("\n=== Assignment Guidelines ===")
        print("1. Implement the full ETL pipeline using AWS Glue")
        print("2. Create comprehensive data quality checks")
        print("3. Build multi-source data integration")
        print("4. Develop advanced analytics and insights")
        print("5. Document your methodology and findings")

if __name__ == "__main__":
    main()