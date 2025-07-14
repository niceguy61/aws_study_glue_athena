#!/usr/bin/env python3
"""
Level 1 Assignment: Basic Data Analysis
학생 성과 데이터를 활용한 기본 데이터 분석 과제

이 스크립트는 과제 1-1의 참고 예제입니다.
실제 과제에서는 여러분이 직접 구현해야 합니다.
"""

import pandas as pd
import numpy as np
import boto3
from datetime import datetime
import json

class BasicDataAnalyzer:
    """기본 데이터 분석 클래스"""
    
    def __init__(self, s3_bucket, aws_region='us-east-1'):
        self.s3_bucket = s3_bucket
        self.aws_region = aws_region
        self.s3_client = boto3.client('s3', region_name=aws_region)
        self.athena_client = boto3.client('athena', region_name=aws_region)
    
    def generate_sample_student_performance_data(self, num_students=1000):
        """
        샘플 학생 성과 데이터 생성
        실제 과제에서는 Kaggle 데이터를 사용하세요.
        """
        np.random.seed(42)
        
        # 기본 정보
        genders = ['male', 'female']
        race_ethnicity = ['group A', 'group B', 'group C', 'group D', 'group E']
        parental_education = [
            'some high school', 'high school', 'some college', 
            'associate\'s degree', 'bachelor\'s degree', 'master\'s degree'
        ]
        lunch_types = ['standard', 'free/reduced']
        test_prep = ['none', 'completed']
        
        data = []
        for i in range(num_students):
            # 기본 정보 생성
            gender = np.random.choice(genders)
            race = np.random.choice(race_ethnicity)
            parent_edu = np.random.choice(parental_education)
            lunch = np.random.choice(lunch_types, p=[0.6, 0.4])
            prep = np.random.choice(test_prep, p=[0.7, 0.3])
            
            # 성과에 영향을 주는 요인들 반영
            base_score = 50
            
            # 부모 교육 수준 영향
            edu_bonus = {
                'some high school': 0,
                'high school': 5,
                'some college': 10,
                'associate\'s degree': 15,
                'bachelor\'s degree': 20,
                'master\'s degree': 25
            }
            base_score += edu_bonus[parent_edu]
            
            # 점심 프로그램 영향 (경제적 상황)
            if lunch == 'free/reduced':
                base_score -= 8
            
            # 시험 준비 과정 영향
            if prep == 'completed':
                base_score += 12
            
            # 성별 영향 (미미한 차이)
            if gender == 'female':
                reading_bonus = 3
                writing_bonus = 4
                math_bonus = -1
            else:
                reading_bonus = -2
                writing_bonus = -3
                math_bonus = 2
            
            # 점수 생성 (정규분포 + 요인별 조정)
            math_score = max(0, min(100, 
                np.random.normal(base_score + math_bonus, 15)))
            reading_score = max(0, min(100, 
                np.random.normal(base_score + reading_bonus, 12)))
            writing_score = max(0, min(100, 
                np.random.normal(base_score + writing_bonus, 13)))
            
            data.append({
                'student_id': f'STU_{i+1:04d}',
                'gender': gender,
                'race_ethnicity': race,
                'parental_level_of_education': parent_edu,
                'lunch': lunch,
                'test_preparation_course': prep,
                'math_score': round(math_score),
                'reading_score': round(reading_score),
                'writing_score': round(writing_score),
                'total_score': round(math_score + reading_score + writing_score),
                'average_score': round((math_score + reading_score + writing_score) / 3, 1)
            })
        
        return pd.DataFrame(data)
    
    def upload_data_to_s3(self, df, key_prefix='student-performance'):
        """데이터를 S3에 업로드"""
        try:
            # CSV 형식으로 저장
            csv_key = f"{key_prefix}/student_performance.csv"
            csv_buffer = df.to_csv(index=False)
            
            self.s3_client.put_object(
                Bucket=self.s3_bucket,
                Key=csv_key,
                Body=csv_buffer,
                ContentType='text/csv'
            )
            
            print(f"✓ 데이터 업로드 완료: s3://{self.s3_bucket}/{csv_key}")
            
            # 파티션된 Parquet 형식으로도 저장 (성능 최적화)
            parquet_key_prefix = f"{key_prefix}/parquet"
            
            # 성별로 파티션
            for gender in df['gender'].unique():
                gender_df = df[df['gender'] == gender]
                parquet_key = f"{parquet_key_prefix}/gender={gender}/data.parquet"
                
                parquet_buffer = gender_df.to_parquet(index=False)
                self.s3_client.put_object(
                    Bucket=self.s3_bucket,
                    Key=parquet_key,
                    Body=parquet_buffer,
                    ContentType='application/octet-stream'
                )
            
            print(f"✓ 파티션된 데이터 업로드 완료: s3://{self.s3_bucket}/{parquet_key_prefix}/")
            
            return True
            
        except Exception as e:
            print(f"❌ 데이터 업로드 실패: {str(e)}")
            return False
    
    def create_glue_table_ddl(self, database_name, table_name):
        """Glue 테이블 생성을 위한 DDL 반환"""
        ddl = f"""
        CREATE EXTERNAL TABLE IF NOT EXISTS {database_name}.{table_name} (
            student_id string,
            gender string,
            race_ethnicity string,
            parental_level_of_education string,
            lunch string,
            test_preparation_course string,
            math_score int,
            reading_score int,
            writing_score int,
            total_score int,
            average_score double
        )
        PARTITIONED BY (
            gender_partition string
        )
        STORED AS PARQUET
        LOCATION 's3://{self.s3_bucket}/student-performance/parquet/'
        TBLPROPERTIES (
            'projection.enabled' = 'true',
            'projection.gender_partition.type' = 'enum',
            'projection.gender_partition.values' = 'male,female',
            'storage.location.template' = 's3://{self.s3_bucket}/student-performance/parquet/gender=${{gender_partition}}/'
        );
        """
        return ddl
    
    def generate_analysis_queries(self):
        """분석용 SQL 쿼리 생성"""
        queries = {
            "basic_statistics": """
            -- 기본 통계 분석
            SELECT 
                COUNT(*) as total_students,
                ROUND(AVG(math_score), 2) as avg_math,
                ROUND(AVG(reading_score), 2) as avg_reading,
                ROUND(AVG(writing_score), 2) as avg_writing,
                ROUND(AVG(average_score), 2) as overall_avg,
                ROUND(STDDEV(average_score), 2) as score_stddev
            FROM student_performance;
            """,
            
            "gender_analysis": """
            -- 성별 성과 비교
            SELECT 
                gender,
                COUNT(*) as student_count,
                ROUND(AVG(math_score), 2) as avg_math,
                ROUND(AVG(reading_score), 2) as avg_reading,
                ROUND(AVG(writing_score), 2) as avg_writing,
                ROUND(AVG(average_score), 2) as avg_total,
                -- 성별 간 차이 계산
                ROUND(AVG(reading_score) - AVG(math_score), 2) as reading_math_diff
            FROM student_performance
            GROUP BY gender
            ORDER BY avg_total DESC;
            """,
            
            "parental_education_impact": """
            -- 부모 교육 수준이 학생 성과에 미치는 영향
            SELECT 
                parental_level_of_education,
                COUNT(*) as student_count,
                ROUND(AVG(average_score), 2) as avg_score,
                ROUND(STDDEV(average_score), 2) as score_stddev,
                -- 교육 수준별 순위
                RANK() OVER (ORDER BY AVG(average_score) DESC) as education_rank,
                -- 고득점자 비율 (80점 이상)
                ROUND(100.0 * SUM(CASE WHEN average_score >= 80 THEN 1 ELSE 0 END) / COUNT(*), 1) as high_scorer_pct
            FROM student_performance
            GROUP BY parental_level_of_education
            ORDER BY avg_score DESC;
            """,
            
            "test_prep_effectiveness": """
            -- 시험 준비 과정의 효과성 분석
            SELECT 
                test_preparation_course,
                gender,
                COUNT(*) as student_count,
                ROUND(AVG(math_score), 2) as avg_math,
                ROUND(AVG(reading_score), 2) as avg_reading,
                ROUND(AVG(writing_score), 2) as avg_writing,
                ROUND(AVG(average_score), 2) as avg_total,
                -- 준비 과정 효과 (완료 vs 미완료 차이)
                ROUND(
                    AVG(average_score) - 
                    AVG(AVG(average_score)) OVER (PARTITION BY gender), 2
                ) as prep_effect
            FROM student_performance
            GROUP BY test_preparation_course, gender
            ORDER BY gender, test_preparation_course;
            """,
            
            "lunch_program_correlation": """
            -- 점심 프로그램과 성과의 상관관계
            WITH lunch_stats AS (
                SELECT 
                    lunch,
                    race_ethnicity,
                    COUNT(*) as student_count,
                    AVG(average_score) as avg_score,
                    STDDEV(average_score) as score_stddev
                FROM student_performance
                GROUP BY lunch, race_ethnicity
            )
            SELECT 
                lunch,
                race_ethnicity,
                student_count,
                ROUND(avg_score, 2) as avg_score,
                ROUND(score_stddev, 2) as score_stddev,
                -- 전체 평균 대비 차이
                ROUND(
                    avg_score - AVG(avg_score) OVER (), 2
                ) as vs_overall_avg,
                -- 인종/민족 내에서의 점심 프로그램 효과
                ROUND(
                    avg_score - AVG(avg_score) OVER (PARTITION BY race_ethnicity), 2
                ) as within_race_effect
            FROM lunch_stats
            ORDER BY race_ethnicity, lunch;
            """,
            
            "performance_distribution": """
            -- 성과 분포 분석
            SELECT 
                CASE 
                    WHEN average_score >= 90 THEN 'A (90-100)'
                    WHEN average_score >= 80 THEN 'B (80-89)'
                    WHEN average_score >= 70 THEN 'C (70-79)'
                    WHEN average_score >= 60 THEN 'D (60-69)'
                    ELSE 'F (Below 60)'
                END as grade_range,
                COUNT(*) as student_count,
                ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) as percentage,
                ROUND(AVG(math_score), 2) as avg_math,
                ROUND(AVG(reading_score), 2) as avg_reading,
                ROUND(AVG(writing_score), 2) as avg_writing
            FROM student_performance
            GROUP BY 
                CASE 
                    WHEN average_score >= 90 THEN 'A (90-100)'
                    WHEN average_score >= 80 THEN 'B (80-89)'
                    WHEN average_score >= 70 THEN 'C (70-79)'
                    WHEN average_score >= 60 THEN 'D (60-69)'
                    ELSE 'F (Below 60)'
                END
            ORDER BY 
                CASE 
                    WHEN grade_range = 'A (90-100)' THEN 1
                    WHEN grade_range = 'B (80-89)' THEN 2
                    WHEN grade_range = 'C (70-79)' THEN 3
                    WHEN grade_range = 'D (60-69)' THEN 4
                    ELSE 5
                END;
            """,
            
            "correlation_analysis": """
            -- 과목 간 상관관계 분석
            SELECT 
                COUNT(*) as total_students,
                -- 상관계수 계산
                ROUND(CORR(math_score, reading_score), 4) as math_reading_corr,
                ROUND(CORR(math_score, writing_score), 4) as math_writing_corr,
                ROUND(CORR(reading_score, writing_score), 4) as reading_writing_corr,
                -- 각 과목별 기본 통계
                ROUND(AVG(math_score), 2) as avg_math,
                ROUND(AVG(reading_score), 2) as avg_reading,
                ROUND(AVG(writing_score), 2) as avg_writing,
                ROUND(STDDEV(math_score), 2) as stddev_math,
                ROUND(STDDEV(reading_score), 2) as stddev_reading,
                ROUND(STDDEV(writing_score), 2) as stddev_writing
            FROM student_performance;
            """
        }
        
        return queries
    
    def generate_insights_template(self):
        """인사이트 보고서 템플릿 생성"""
        template = """
# 학생 성과 데이터 분석 보고서

## 1. 분석 개요
- **데이터 기간**: [분석 기간 입력]
- **분석 대상**: [학생 수] 명의 학생 데이터
- **분석 도구**: Amazon Athena, AWS Glue

## 2. 주요 발견사항

### 2.1 전체 성과 현황
- 평균 점수: [수치] 점
- 표준편차: [수치] 점
- 최고점: [수치] 점
- 최저점: [수치] 점

### 2.2 성별 차이 분석
- **수학**: [남학생 vs 여학생 비교]
- **읽기**: [남학생 vs 여학생 비교]
- **쓰기**: [남학생 vs 여학생 비교]

### 2.3 부모 교육 수준의 영향
- 가장 높은 성과: [교육 수준] ([평균 점수])
- 가장 낮은 성과: [교육 수준] ([평균 점수])
- 교육 수준별 격차: [수치] 점

### 2.4 시험 준비 과정의 효과
- 준비 과정 완료 학생 평균: [수치] 점
- 준비 과정 미완료 학생 평균: [수치] 점
- 효과 크기: [수치] 점 향상

### 2.5 경제적 배경의 영향
- 일반 점심 학생 평균: [수치] 점
- 무료/할인 점심 학생 평균: [수치] 점
- 격차: [수치] 점

## 3. 심화 분석

### 3.1 과목 간 상관관계
- 수학-읽기 상관계수: [수치]
- 수학-쓰기 상관계수: [수치]
- 읽기-쓰기 상관계수: [수치]

### 3.2 성과 분포
- A등급 (90점 이상): [비율]%
- B등급 (80-89점): [비율]%
- C등급 (70-79점): [비율]%
- D등급 (60-69점): [비율]%
- F등급 (60점 미만): [비율]%

## 4. 결론 및 제언

### 4.1 주요 결론
1. [결론 1]
2. [결론 2]
3. [결론 3]

### 4.2 교육 정책 제언
1. [제언 1]
2. [제언 2]
3. [제언 3]

### 4.3 추가 연구 방향
1. [연구 방향 1]
2. [연구 방향 2]
3. [연구 방향 3]

---
*분석 수행일: {analysis_date}*
*분석자: [이름 입력]*
        """.format(analysis_date=datetime.now().strftime('%Y-%m-%d'))
        
        return template

def main():
    """메인 실행 함수"""
    print("=== Level 1 Assignment: Basic Data Analysis ===\n")
    
    # 설정 (실제 과제에서는 본인의 S3 버킷으로 변경)
    S3_BUCKET = "your-workshop-bucket"
    
    try:
        # 분석기 초기화
        analyzer = BasicDataAnalyzer(S3_BUCKET)
        
        # 1. 샘플 데이터 생성 (실제 과제에서는 Kaggle 데이터 사용)
        print("1. 샘플 데이터 생성 중...")
        df = analyzer.generate_sample_student_performance_data(1000)
        print(f"   생성된 데이터: {len(df)} 행, {len(df.columns)} 열")
        
        # 2. 데이터 S3 업로드
        print("\n2. S3에 데이터 업로드 중...")
        if analyzer.upload_data_to_s3(df):
            print("   ✓ 업로드 완료")
        else:
            print("   ❌ 업로드 실패")
            return
        
        # 3. Glue 테이블 DDL 생성
        print("\n3. Glue 테이블 DDL 생성...")
        ddl = analyzer.create_glue_table_ddl("workshop_database", "student_performance")
        print("   ✓ DDL 생성 완료")
        print("   다음 DDL을 Athena에서 실행하세요:")
        print(ddl)
        
        # 4. 분석 쿼리 생성
        print("\n4. 분석 쿼리 생성...")
        queries = analyzer.generate_analysis_queries()
        print(f"   ✓ {len(queries)}개 쿼리 생성 완료")
        
        # 쿼리를 파일로 저장
        for query_name, query_sql in queries.items():
            filename = f"query_{query_name}.sql"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(query_sql)
            print(f"   - {filename} 저장 완료")
        
        # 5. 인사이트 보고서 템플릿 생성
        print("\n5. 인사이트 보고서 템플릿 생성...")
        template = analyzer.generate_insights_template()
        with open("analysis_report_template.md", 'w', encoding='utf-8') as f:
            f.write(template)
        print("   ✓ analysis_report_template.md 생성 완료")
        
        print("\n=== 과제 준비 완료 ===")
        print("다음 단계:")
        print("1. AWS Glue 콘솔에서 크롤러 생성 및 실행")
        print("2. Athena에서 DDL 실행하여 테이블 생성")
        print("3. 생성된 쿼리들을 Athena에서 실행")
        print("4. 결과를 분석하여 인사이트 도출")
        print("5. 보고서 템플릿을 완성하여 제출")
        
    except Exception as e:
        print(f"❌ 오류 발생: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())