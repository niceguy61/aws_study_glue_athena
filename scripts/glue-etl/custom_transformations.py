#!/usr/bin/env python3
"""
커스텀 변환 함수 라이브러리
학생 데이터 분석을 위한 특화된 변환 함수들
"""

from pyspark.sql import functions as F
from pyspark.sql.types import *
from pyspark.sql.window import Window
import re
from datetime import datetime, timedelta

class StudentDataTransformations:
    """학생 데이터 전용 커스텀 변환 함수들"""
    
    @staticmethod
    def calculate_ai_proficiency_score(df):
        """
        AI 도구 숙련도 점수 계산
        - 사용 도구 수 (30%)
        - 사용 빈도 (40%) 
        - 만족도 (30%)
        """
        return df.withColumn(
            "ai_proficiency_score",
            F.round(
                (F.coalesce(F.col("num_ai_tools"), F.lit(0)) * 0.3) + 
                (F.coalesce(F.col("usage_frequency_score"), F.lit(1)) * 0.4) + 
                (F.coalesce(F.col("satisfaction_level"), F.lit(1)) * 0.3), 2
            )
        ).withColumn(
            "proficiency_level",
            F.when(F.col("ai_proficiency_score") >= 4.0, "Expert")
             .when(F.col("ai_proficiency_score") >= 3.0, "Advanced")
             .when(F.col("ai_proficiency_score") >= 2.0, "Intermediate")
             .otherwise("Beginner")
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
                F.coalesce(F.col("num_ai_tools"), F.lit(0)) >= 3, "Multi_Tool_User"
            ).when(
                F.col("usage_frequency_score") >= 4, "High_Frequency_User"
            ).otherwise("Basic_User")
        ).withColumn(
            "learning_preference",
            F.when(F.col("learning_style").isin(["Research_Intensive", "Multi_Tool_User"]), "Exploratory")
             .when(F.col("learning_style") == "Assignment_Focused", "Task_Oriented")
             .otherwise("Casual")
        )
    
    @staticmethod
    def detect_at_risk_students(df):
        """위험군 학생 탐지"""
        return df.withColumn(
            "academic_risk_score",
            # GPA (40%) + 출석률 (30%) + 과제 제출률 (30%)
            F.round(
                (F.when(F.col("gpa") < 2.0, 4)
                  .when(F.col("gpa") < 2.5, 3)
                  .when(F.col("gpa") < 3.0, 2)
                  .otherwise(1) * 0.4) +
                (F.when(F.coalesce(F.col("attendance_rate"), F.lit(1)) < 0.6, 4)
                  .when(F.col("attendance_rate") < 0.7, 3)
                  .when(F.col("attendance_rate") < 0.8, 2)
                  .otherwise(1) * 0.3) +
                (F.when(F.coalesce(F.col("assignment_submission_rate"), F.lit(1)) < 0.7, 4)
                  .when(F.col("assignment_submission_rate") < 0.8, 3)
                  .when(F.col("assignment_submission_rate") < 0.9, 2)
                  .otherwise(1) * 0.3), 2
            )
        ).withColumn(
            "at_risk_flag",
            F.col("academic_risk_score") >= 3.0
        ).withColumn(
            "risk_level",
            F.when(F.col("academic_risk_score") >= 3.5, "High")
             .when(F.col("academic_risk_score") >= 2.5, "Medium")
             .when(F.col("academic_risk_score") >= 1.5, "Low")
             .otherwise("None")
        ).withColumn(
            "intervention_needed",
            F.when(F.col("risk_level") == "High", "Immediate")
             .when(F.col("risk_level") == "Medium", "Monitor")
             .otherwise("None")
        )
    
    @staticmethod
    def normalize_course_names(df):
        """과목명 정규화"""
        def clean_course_name(name):
            if name is None:
                return None
            # 언더스코어를 공백으로 변경
            cleaned = name.replace('_', ' ')
            # 특수 문자 제거
            cleaned = re.sub(r'[^\w\s]', '', cleaned)
            # 첫 글자 대문자화
            cleaned = ' '.join([word.capitalize() for word in cleaned.split()])
            return cleaned.strip()
        
        clean_course_udf = F.udf(clean_course_name, StringType())
        
        return df.withColumn(
            "course_name_normalized",
            clean_course_udf(F.col("course_name"))
        ).withColumn(
            "course_category",
            F.when(F.col("course_code").startswith("CS"), "Computer Science")
             .when(F.col("course_code").startswith("MATH"), "Mathematics")
             .when(F.col("course_code").startswith("ENG"), "English")
             .when(F.col("course_code").startswith("BUS"), "Business")
             .when(F.col("course_code").startswith("PHYS"), "Physics")
             .when(F.col("course_code").startswith("CHEM"), "Chemistry")
             .otherwise("Other")
        )
    
    @staticmethod
    def calculate_semester_workload(df):
        """학기별 학업 부담 계산"""
        return df.withColumn(
            "workload_score",
            # 수강 과목 수 (25%) + 총 학점 (35%) + 과목 다양성 (40%)
            F.round(
                (F.coalesce(F.col("total_courses"), F.lit(0)) * 2.5) + 
                (F.coalesce(F.col("total_credits"), F.lit(0)) * 1.5) + 
                (F.coalesce(F.col("academic_diversity"), F.lit(0)) * 4.0), 2
            )
        ).withColumn(
            "workload_category",
            F.when(F.col("workload_score") >= 60, "Heavy")
             .when(F.col("workload_score") >= 40, "Moderate")
             .when(F.col("workload_score") >= 20, "Light")
             .otherwise("Minimal")
        ).withColumn(
            "workload_balance_score",
            # 학업 부담과 성과의 균형 점수
            F.when(
                (F.col("workload_category") == "Heavy") & (F.col("gpa") >= 3.5), 5
            ).when(
                (F.col("workload_category") == "Moderate") & (F.col("gpa") >= 3.0), 4
            ).when(
                (F.col("workload_category") == "Light") & (F.col("gpa") >= 2.5), 3
            ).when(
                F.col("workload_category") == "Minimal", 2
            ).otherwise(1)
        )
    
    @staticmethod
    def analyze_ai_usage_patterns(df):
        """AI 사용 패턴 분석"""
        return df.withColumn(
            "usage_consistency",
            # 사용 빈도와 만족도의 일관성
            F.when(
                (F.col("usage_frequency_score") >= 4) & (F.col("satisfaction_level") >= 4), "High_Consistent"
            ).when(
                (F.col("usage_frequency_score") >= 3) & (F.col("satisfaction_level") >= 3), "Medium_Consistent"
            ).when(
                F.abs(F.col("usage_frequency_score") - F.col("satisfaction_level")) <= 1, "Consistent"
            ).otherwise("Inconsistent")
        ).withColumn(
            "adoption_stage",
            F.when(
                (F.col("usage_frequency_score") >= 4) & (F.col("num_ai_tools") >= 3), "Advanced_Adopter"
            ).when(
                (F.col("usage_frequency_score") >= 3) & (F.col("num_ai_tools") >= 2), "Regular_User"
            ).when(
                F.col("usage_frequency_score") >= 2, "Occasional_User"
            ).otherwise("Beginner")
        )
    
    @staticmethod
    def calculate_success_indicators(df):
        """성공 지표 계산"""
        # 윈도우 함수를 위한 스펙 정의
        field_window = Window.partitionBy("field_of_study")
        
        return df.withColumn(
            "relative_performance",
            # 전공 내에서의 상대적 성과
            F.percent_rank().over(field_window.orderBy("gpa"))
        ).withColumn(
            "performance_percentile",
            F.round(F.col("relative_performance") * 100, 1)
        ).withColumn(
            "success_category",
            F.when(F.col("performance_percentile") >= 90, "Top_Performer")
             .when(F.col("performance_percentile") >= 75, "High_Performer")
             .when(F.col("performance_percentile") >= 50, "Average_Performer")
             .when(F.col("performance_percentile") >= 25, "Below_Average")
             .otherwise("Low_Performer")
        ).withColumn(
            "improvement_potential",
            F.when(
                (F.col("ai_proficiency_score") >= 3.0) & (F.col("performance_percentile") < 50), "High"
            ).when(
                (F.col("ai_proficiency_score") >= 2.0) & (F.col("performance_percentile") < 75), "Medium"
            ).otherwise("Low")
        )

class DataQualityTransformations:
    """데이터 품질 개선을 위한 변환 함수들"""
    
    @staticmethod
    def handle_missing_values(df, strategy="default"):
        """결측값 처리"""
        if strategy == "default":
            # 기본 전략: 수치형은 평균, 범주형은 최빈값
            return df.fillna({
                "gpa": 2.5,
                "satisfaction_level": 3,
                "usage_frequency_score": 2,
                "attendance_rate": 0.8,
                "assignment_submission_rate": 0.85,
                "num_ai_tools": 1
            })
        elif strategy == "median":
            # 중앙값으로 대체
            numeric_cols = ["gpa", "satisfaction_level", "usage_frequency_score"]
            for col in numeric_cols:
                median_val = df.approxQuantile(col, [0.5], 0.25)[0]
                df = df.fillna({col: median_val})
            return df
        else:
            return df
    
    @staticmethod
    def remove_outliers(df, method="iqr"):
        """이상값 제거"""
        if method == "iqr":
            # IQR 방법으로 이상값 제거
            numeric_cols = ["gpa", "satisfaction_level", "usage_frequency_score"]
            
            for col in numeric_cols:
                # 사분위수 계산
                quantiles = df.approxQuantile(col, [0.25, 0.75], 0.25)
                if len(quantiles) == 2:
                    q1, q3 = quantiles
                    iqr = q3 - q1
                    lower_bound = q1 - 1.5 * iqr
                    upper_bound = q3 + 1.5 * iqr
                    
                    # 이상값 필터링
                    df = df.filter(
                        (F.col(col) >= lower_bound) & (F.col(col) <= upper_bound)
                    )
            
            return df
        else:
            return df
    
    @staticmethod
    def standardize_categorical_values(df):
        """범주형 값 표준화"""
        return df.withColumn(
            "field_of_study_clean",
            F.when(F.col("field_of_study").isin(["CS", "Computer Science", "CompSci"]), "Computer Science")
             .when(F.col("field_of_study").isin(["Math", "Mathematics", "MATH"]), "Mathematics")
             .when(F.col("field_of_study").isin(["Eng", "English", "ENG"]), "English")
             .otherwise(F.col("field_of_study"))
        ).withColumn(
            "frequency_of_use_clean",
            F.when(F.col("frequency_of_use").isin(["daily", "Daily", "DAILY"]), "Daily")
             .when(F.col("frequency_of_use").isin(["weekly", "Weekly", "WEEKLY"]), "Weekly")
             .when(F.col("frequency_of_use").isin(["monthly", "Monthly", "MONTHLY"]), "Monthly")
             .when(F.col("frequency_of_use").isin(["rarely", "Rarely", "RARELY"]), "Rarely")
             .otherwise(F.col("frequency_of_use"))
        )

def apply_all_transformations(df, include_quality_fixes=True):
    """모든 커스텀 변환을 순차적으로 적용"""
    print("=== 커스텀 변환 적용 시작 ===")
    
    # 데이터 품질 개선 (선택적)
    if include_quality_fixes:
        print("1. 데이터 품질 개선 중...")
        quality_transformer = DataQualityTransformations()
        df = quality_transformer.handle_missing_values(df)
        df = quality_transformer.standardize_categorical_values(df)
        df = quality_transformer.remove_outliers(df)
    
    # 학생 데이터 변환
    print("2. 학생 데이터 변환 중...")
    student_transformer = StudentDataTransformations()
    
    df = student_transformer.calculate_ai_proficiency_score(df)
    df = student_transformer.categorize_learning_style(df)
    df = student_transformer.detect_at_risk_students(df)
    
    if "course_name" in df.columns:
        df = student_transformer.normalize_course_names(df)
    
    if "total_courses" in df.columns:
        df = student_transformer.calculate_semester_workload(df)
    
    df = student_transformer.analyze_ai_usage_patterns(df)
    df = student_transformer.calculate_success_indicators(df)
    
    print("✓ 모든 커스텀 변환 완료")
    return df

def validate_transformations(df):
    """변환 결과 검증"""
    print("=== 변환 결과 검증 ===")
    
    # 새로 생성된 컬럼들 확인
    new_columns = [
        "ai_proficiency_score", "proficiency_level", "learning_style",
        "at_risk_flag", "risk_level", "workload_category", "success_category"
    ]
    
    existing_new_cols = [col for col in new_columns if col in df.columns]
    print(f"생성된 새 컬럼: {existing_new_cols}")
    
    # 기본 통계 확인
    if "ai_proficiency_score" in df.columns:
        proficiency_stats = df.select(
            F.min("ai_proficiency_score").alias("min_proficiency"),
            F.max("ai_proficiency_score").alias("max_proficiency"),
            F.avg("ai_proficiency_score").alias("avg_proficiency")
        ).collect()[0]
        
        print(f"AI 숙련도 점수 범위: {proficiency_stats['min_proficiency']:.2f} ~ {proficiency_stats['max_proficiency']:.2f}")
        print(f"평균 AI 숙련도: {proficiency_stats['avg_proficiency']:.2f}")
    
    # 위험군 학생 비율 확인
    if "at_risk_flag" in df.columns:
        total_students = df.count()
        at_risk_count = df.filter(F.col("at_risk_flag") == True).count()
        at_risk_percentage = (at_risk_count / total_students) * 100
        
        print(f"위험군 학생: {at_risk_count}명 ({at_risk_percentage:.1f}%)")
    
    # 학습 스타일 분포 확인
    if "learning_style" in df.columns:
        learning_style_dist = df.groupBy("learning_style").count().orderBy(F.desc("count")).collect()
        print("학습 스타일 분포:")
        for row in learning_style_dist:
            print(f"  {row['learning_style']}: {row['count']}명")
    
    print("✓ 변환 결과 검증 완료")
    return True

if __name__ == "__main__":
    print("커스텀 변환 함수 라이브러리 로드 완료")
    print("사용 방법:")
    print("1. from custom_transformations import apply_all_transformations")
    print("2. transformed_df = apply_all_transformations(your_df)")
    print("3. validate_transformations(transformed_df)")