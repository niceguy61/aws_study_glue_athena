#!/usr/bin/env python3
"""
고급 다중 소스 ETL 스크립트
여러 데이터 소스를 통합하여 복잡한 분석을 수행하는 AWS Glue ETL 작업
"""

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
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """메인 ETL 처리 함수"""
    
    # Job 초기화
    args = getResolvedOptions(sys.argv, ['JOB_NAME', 'S3_BUCKET'])
    sc = SparkContext()
    glueContext = GlueContext(sc)
    spark = glueContext.spark_session
    job = Job(glueContext)
    job.init(args['JOB_NAME'], args)
    
    s3_bucket = args['S3_BUCKET']
    
    try:
        logger.info("=== 고급 다중 소스 ETL 작업 시작 ===")
        
        # 1. 데이터 소스 읽기
        logger.info("1. 데이터 소스 읽기 중...")
        ai_usage_df = read_data_source(glueContext, "workshop_database", "ai_tool_usage")
        academic_df = read_data_source(glueContext, "workshop_database", "academic_performance")
        enrollment_df = read_data_source(glueContext, "workshop_database", "course_enrollment")
        
        # 2. 데이터 품질 검증
        logger.info("2. 데이터 품질 검증 중...")
        validate_data_quality(ai_usage_df, "AI Tool Usage")
        validate_data_quality(academic_df, "Academic Performance")
        validate_data_quality(enrollment_df, "Course Enrollment")
        
        # 3. 데이터 전처리 및 정제
        logger.info("3. 데이터 전처리 중...")
        ai_usage_clean = preprocess_ai_usage_data(ai_usage_df)
        academic_clean = preprocess_academic_data(academic_df)
        enrollment_agg = aggregate_enrollment_data(enrollment_df)
        
        # 4. 복잡한 데이터 조인
        logger.info("4. 데이터 조인 수행 중...")
        integrated_df = perform_complex_joins(ai_usage_clean, academic_clean, enrollment_agg)
        
        # 5. 고급 분석 및 인사이트 생성
        logger.info("5. 인사이트 생성 중...")
        insights_df = generate_insights(integrated_df)
        outliers_df = detect_outliers(integrated_df)
        
        # 6. 결과 저장
        logger.info("6. 결과 저장 중...")
        save_results(glueContext, s3_bucket, integrated_df, insights_df, outliers_df)
        
        logger.info("=== ETL 작업 성공적으로 완료 ===")
        
    except Exception as e:
        logger.error(f"ETL 작업 실패: {str(e)}")
        raise
    finally:
        job.commit()

def read_data_source(glue_context, database, table_name):
    """안전한 데이터 소스 읽기"""
    try:
        df = glue_context.create_dynamic_frame.from_catalog(
            database=database,
            table_name=table_name
        ).toDF()
        
        row_count = df.count()
        logger.info(f"✓ {table_name}: {row_count} 행 읽기 완료")
        
        if row_count == 0:
            raise ValueError(f"테이블 {table_name}이 비어있습니다")
        
        return df
        
    except Exception as e:
        logger.error(f"테이블 {table_name} 읽기 실패: {str(e)}")
        raise

def validate_data_quality(df, table_name):
    """데이터 품질 검증"""
    total_rows = df.count()
    
    # 결측값 검사
    null_counts = {}
    for col in df.columns:
        null_count = df.filter(F.col(col).isNull()).count()
        null_percentage = (null_count / total_rows) * 100
        null_counts[col] = {'count': null_count, 'percentage': null_percentage}
        
        if null_percentage > 20:  # 20% 이상 결측값
            logger.warning(f"{table_name}.{col}: 결측값 {null_percentage:.2f}%")
    
    # 중복 검사
    duplicate_count = total_rows - df.dropDuplicates().count()
    duplicate_percentage = (duplicate_count / total_rows) * 100
    
    logger.info(f"{table_name} 품질 검사:")
    logger.info(f"  - 총 행 수: {total_rows}")
    logger.info(f"  - 중복 행: {duplicate_count} ({duplicate_percentage:.2f}%)")
    
    # 품질 임계값 검사
    if duplicate_percentage > 10:
        raise ValueError(f"{table_name}: 중복 데이터가 너무 많습니다 ({duplicate_percentage:.2f}%)")
    
    return True

def preprocess_ai_usage_data(df):
    """AI 도구 사용 데이터 전처리"""
    return df.select(
        F.col("student_id"),
        F.col("field_of_study"),
        F.col("year_of_study"),
        # AI 도구 개수 계산
        F.when(F.col("ai_tools_used").isNull(), 0)
         .otherwise(F.size(F.split(F.col("ai_tools_used"), ","))).alias("num_ai_tools"),
        # 사용 빈도 점수화
        F.when(F.col("frequency_of_use") == "Daily", 5)
         .when(F.col("frequency_of_use") == "Weekly", 4)
         .when(F.col("frequency_of_use") == "Monthly", 3)
         .when(F.col("frequency_of_use") == "Rarely", 2)
         .otherwise(1).alias("usage_frequency_score"),
        F.col("satisfaction_level"),
        F.col("primary_use_case"),
        # 사용 강도 카테고리
        F.when(F.col("frequency_of_use").isin(["Daily", "Weekly"]), "High")
         .when(F.col("frequency_of_use") == "Monthly", "Medium")
         .otherwise("Low").alias("usage_intensity")
    ).filter(F.col("student_id").isNotNull())

def preprocess_academic_data(df):
    """학업 성과 데이터 전처리"""
    return df.select(
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
         .otherwise("Low").alias("performance_category"),
        # 학업 참여도 점수
        ((F.col("attendance_rate") * 0.4) + 
         (F.col("assignment_submission_rate") * 0.6)).alias("engagement_score")
    ).filter(
        (F.col("student_id").isNotNull()) &
        (F.col("gpa") >= 0.0) & (F.col("gpa") <= 4.0) &
        (F.col("attendance_rate") >= 0.0) & (F.col("attendance_rate") <= 1.0)
    )

def aggregate_enrollment_data(df):
    """수강 신청 데이터 집계"""
    # 성적을 GPA 점수로 변환
    grade_to_gpa = F.when(F.col("grade") == "A+", 4.3)\
                    .when(F.col("grade") == "A", 4.0)\
                    .when(F.col("grade") == "B+", 3.3)\
                    .when(F.col("grade") == "B", 3.0)\
                    .when(F.col("grade") == "C+", 2.3)\
                    .when(F.col("grade") == "C", 2.0)\
                    .when(F.col("grade") == "D", 1.0)\
                    .otherwise(0.0)
    
    return df.withColumn("grade_points", grade_to_gpa)\
             .groupBy("student_id", "semester").agg(
                 F.count("course_code").alias("total_courses"),
                 F.sum("credit_hours").alias("total_credits"),
                 F.avg("grade_points").alias("calculated_gpa"),
                 F.collect_list("course_name").alias("courses_taken"),
                 F.collect_list("department").alias("departments"),
                 # 다양성 지수 (서로 다른 학과 수)
                 F.countDistinct("department").alias("academic_diversity")
             )

def perform_complex_joins(ai_usage_df, academic_df, enrollment_df):
    """복잡한 다중 테이블 조인"""
    # 1차 조인: AI 사용 데이터 + 학업 성과
    ai_academic_joined = ai_usage_df.join(
        academic_df,
        on="student_id",
        how="inner"
    )
    
    # 2차 조인: 수강 신청 데이터 추가
    final_integrated = ai_academic_joined.join(
        enrollment_df,
        on=["student_id", "semester"],
        how="left"
    )
    
    # 조인 결과 검증
    original_count = ai_usage_df.count()
    final_count = final_integrated.count()
    
    logger.info(f"조인 결과: {original_count} → {final_count} 행")
    
    return final_integrated

def generate_insights(df):
    """고급 인사이트 생성"""
    insights = df.groupBy(
        "field_of_study",
        "performance_category", 
        "usage_intensity"
    ).agg(
        F.count("student_id").alias("student_count"),
        F.avg("num_ai_tools").alias("avg_ai_tools_used"),
        F.avg("usage_frequency_score").alias("avg_usage_frequency"),
        F.avg("satisfaction_level").alias("avg_satisfaction"),
        F.avg("gpa").alias("avg_gpa"),
        F.avg("major_gpa").alias("avg_major_gpa"),
        F.avg("engagement_score").alias("avg_engagement"),
        F.avg("academic_diversity").alias("avg_academic_diversity"),
        # 상관관계 분석
        F.corr("usage_frequency_score", "gpa").alias("usage_gpa_correlation"),
        F.corr("satisfaction_level", "engagement_score").alias("satisfaction_engagement_correlation"),
        # 통계적 지표
        F.stddev("gpa").alias("gpa_stddev"),
        F.min("gpa").alias("min_gpa"),
        F.max("gpa").alias("max_gpa")
    ).filter(F.col("student_count") >= 5)  # 최소 5명 이상인 그룹만
    
    return insights

def detect_outliers(df):
    """이상값 탐지"""
    # 전공별 GPA 분포 기반 이상값 탐지
    window_spec = Window.partitionBy("field_of_study")
    
    outliers = df.withColumn(
        "field_avg_gpa", F.avg("gpa").over(window_spec)
    ).withColumn(
        "field_stddev_gpa", F.stddev("gpa").over(window_spec)
    ).withColumn(
        "gpa_z_score",
        (F.col("gpa") - F.col("field_avg_gpa")) / F.col("field_stddev_gpa")
    ).withColumn(
        "is_gpa_outlier",
        F.when(F.abs(F.col("gpa_z_score")) > 2.5, True).otherwise(False)
    )
    
    # 사용 패턴 이상값 탐지
    usage_window = Window.partitionBy("field_of_study", "year_of_study")
    
    outliers = outliers.withColumn(
        "avg_usage_frequency", F.avg("usage_frequency_score").over(usage_window)
    ).withColumn(
        "usage_z_score",
        (F.col("usage_frequency_score") - F.col("avg_usage_frequency")) / 
        F.stddev("usage_frequency_score").over(usage_window)
    ).withColumn(
        "is_usage_outlier",
        F.when(F.abs(F.col("usage_z_score")) > 2.0, True).otherwise(False)
    ).withColumn(
        "outlier_type",
        F.when(F.col("is_gpa_outlier") & F.col("is_usage_outlier"), "Both")
         .when(F.col("is_gpa_outlier"), "GPA")
         .when(F.col("is_usage_outlier"), "Usage")
         .otherwise("None")
    )
    
    return outliers.filter(F.col("outlier_type") != "None")

def save_results(glue_context, s3_bucket, integrated_df, insights_df, outliers_df):
    """결과를 S3에 저장"""
    
    # 1. 통합 데이터셋 저장 (파티션별)
    integrated_dynamic = DynamicFrame.fromDF(integrated_df, glue_context, "integrated")
    glue_context.write_dynamic_frame.from_options(
        frame=integrated_dynamic,
        connection_type="s3",
        connection_options={
            "path": f"s3://{s3_bucket}/processed-data/integrated-student-analysis/",
            "partitionKeys": ["field_of_study", "semester"]
        },
        format="parquet"
    )
    logger.info("✓ 통합 데이터셋 저장 완료")
    
    # 2. 인사이트 데이터 저장
    insights_dynamic = DynamicFrame.fromDF(insights_df, glue_context, "insights")
    glue_context.write_dynamic_frame.from_options(
        frame=insights_dynamic,
        connection_type="s3",
        connection_options={
            "path": f"s3://{s3_bucket}/processed-data/student-insights/"
        },
        format="parquet"
    )
    logger.info("✓ 인사이트 데이터 저장 완료")
    
    # 3. 이상값 데이터 저장
    outliers_dynamic = DynamicFrame.fromDF(outliers_df, glue_context, "outliers")
    glue_context.write_dynamic_frame.from_options(
        frame=outliers_dynamic,
        connection_type="s3",
        connection_options={
            "path": f"s3://{s3_bucket}/processed-data/outlier-analysis/"
        },
        format="parquet"
    )
    logger.info("✓ 이상값 분석 데이터 저장 완료")

if __name__ == "__main__":
    main()