#!/usr/bin/env python3
"""
추가 데이터셋 생성 스크립트
고급 ETL 시나리오를 위한 학업 성과 및 수강 신청 데이터 생성
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os

def create_academic_performance_dataset():
    """학업 성과 데이터셋 생성"""
    print("학업 성과 데이터셋 생성 중...")
    
    # 시드 설정으로 재현 가능한 데이터 생성
    np.random.seed(42)
    student_ids = [f"STU_{i:04d}" for i in range(1, 501)]
    
    academic_data = {
        'student_id': student_ids,
        'semester': np.random.choice(['2024-1', '2024-2'], 500),
        'gpa': np.round(np.clip(np.random.normal(3.2, 0.8, 500), 0.0, 4.0), 2),
        'credits_completed': np.random.randint(12, 21, 500),
        'major_gpa': np.round(np.clip(np.random.normal(3.4, 0.7, 500), 0.0, 4.0), 2),
        'attendance_rate': np.round(np.clip(np.random.normal(0.85, 0.15, 500), 0.0, 1.0), 2),
        'assignment_submission_rate': np.round(np.clip(np.random.normal(0.90, 0.12, 500), 0.0, 1.0), 2),
        'last_updated': datetime.now().strftime('%Y-%m-%d')
    }
    
    academic_df = pd.DataFrame(academic_data)
    
    # 데이터 품질 개선: GPA와 major_gpa 간의 일관성 확보
    for i in range(len(academic_df)):
        if abs(academic_df.loc[i, 'gpa'] - academic_df.loc[i, 'major_gpa']) > 1.5:
            # 차이가 너무 클 경우 major_gpa를 gpa 기준으로 조정
            academic_df.loc[i, 'major_gpa'] = academic_df.loc[i, 'gpa'] + np.random.uniform(-0.3, 0.3)
            academic_df.loc[i, 'major_gpa'] = np.clip(academic_df.loc[i, 'major_gpa'], 0.0, 4.0)
            academic_df.loc[i, 'major_gpa'] = round(academic_df.loc[i, 'major_gpa'], 2)
    
    # 출력 디렉토리 생성
    os.makedirs('datasets', exist_ok=True)
    
    # CSV 파일로 저장
    academic_df.to_csv('datasets/academic_performance.csv', index=False)
    print(f"✓ 학업 성과 데이터셋 생성 완료: {len(academic_df)} 행")
    
    return academic_df

def create_course_enrollment_dataset():
    """수강 신청 데이터셋 생성"""
    print("수강 신청 데이터셋 생성 중...")
    
    # 과목 정보 정의
    courses = [
        ('CS101', 'Programming_Fundamentals', 'Computer Science'),
        ('CS201', 'Data_Structures', 'Computer Science'),
        ('CS301', 'Database_Systems', 'Computer Science'),
        ('CS401', 'Machine_Learning', 'Computer Science'),
        ('MATH201', 'Statistics', 'Mathematics'),
        ('MATH301', 'Linear_Algebra', 'Mathematics'),
        ('ENG101', 'Technical_Writing', 'English'),
        ('BUS201', 'Project_Management', 'Business'),
        ('PHYS101', 'Physics_I', 'Physics'),
        ('CHEM101', 'General_Chemistry', 'Chemistry')
    ]
    
    student_ids = [f"STU_{i:04d}" for i in range(1, 401)]  # 400명의 학생
    
    enrollment_data = []
    
    # 각 학생별로 수강 과목 생성
    for student_id in student_ids:
        # 학생별로 3-6개 과목 수강
        num_courses = np.random.randint(3, 7)
        selected_courses = np.random.choice(len(courses), num_courses, replace=False)
        
        for course_idx in selected_courses:
            course_code, course_name, department = courses[course_idx]
            
            # 성적 분포 (현실적인 분포)
            grade_weights = [0.15, 0.25, 0.25, 0.20, 0.10, 0.03, 0.015, 0.005]
            grade = np.random.choice(
                ['A+', 'A', 'B+', 'B', 'C+', 'C', 'D', 'F'], 
                p=grade_weights
            )
            
            enrollment_data.append({
                'student_id': student_id,
                'course_code': course_code,
                'course_name': course_name,
                'department': department,
                'semester': np.random.choice(['2024-1', '2024-2']),
                'grade': grade,
                'credit_hours': np.random.choice([3, 4], p=[0.7, 0.3]),
                'instructor': f"Prof_{np.random.randint(1, 21):02d}",  # 20명의 교수
                'enrollment_date': (datetime.now() - timedelta(days=np.random.randint(30, 180))).strftime('%Y-%m-%d')
            })
    
    enrollment_df = pd.DataFrame(enrollment_data)
    
    # CSV 파일로 저장
    enrollment_df.to_csv('datasets/course_enrollment.csv', index=False)
    print(f"✓ 수강 신청 데이터셋 생성 완료: {len(enrollment_df)} 행")
    
    return enrollment_df

def create_student_activity_logs():
    """학생 활동 로그 데이터셋 생성 (실시간 스트리밍 시뮬레이션용)"""
    print("학생 활동 로그 데이터셋 생성 중...")
    
    student_ids = [f"STU_{i:04d}" for i in range(1, 201)]  # 200명의 학생
    ai_tools = ['ChatGPT', 'GitHub_Copilot', 'Grammarly', 'Notion_AI', 'Claude', 'Gemini']
    activity_types = ['study_session', 'assignment_work', 'research', 'collaboration', 'quiz_practice']
    
    # 최근 7일간의 활동 로그 생성
    activity_logs = []
    base_date = datetime.now() - timedelta(days=7)
    
    for day in range(7):
        current_date = base_date + timedelta(days=day)
        
        # 하루에 100-300개의 활동 로그 생성
        daily_activities = np.random.randint(100, 301)
        
        for _ in range(daily_activities):
            # 활동 시간 (주로 낮 시간대)
            hour = np.random.choice(range(24), p=[
                0.01, 0.01, 0.01, 0.01, 0.01, 0.01,  # 0-5시
                0.02, 0.03, 0.05, 0.08, 0.12, 0.15,  # 6-11시
                0.12, 0.10, 0.08, 0.06, 0.05, 0.04,  # 12-17시
                0.06, 0.08, 0.06, 0.04, 0.02, 0.01   # 18-23시
            ])
            
            activity_time = current_date.replace(
                hour=hour,
                minute=np.random.randint(0, 60),
                second=np.random.randint(0, 60)
            )
            
            activity_logs.append({
                'student_id': np.random.choice(student_ids),
                'activity_type': np.random.choice(activity_types),
                'timestamp': activity_time.isoformat(),
                'session_duration': np.random.randint(5, 180),  # 5분-3시간
                'ai_tool_used': np.random.choice(ai_tools),
                'course_id': f"CS{np.random.choice([101, 201, 301, 401])}",
                'assignment_id': f"HW_{np.random.randint(1, 11):02d}",
                'difficulty_level': np.random.randint(1, 6),  # 1-5 난이도
                'success_rate': round(np.random.uniform(0.3, 1.0), 2),
                'metadata': f'{{"device": "{np.random.choice(["laptop", "desktop", "tablet"])}", "location": "{np.random.choice(["home", "library", "cafe", "dorm"])}"}}',
                'created_at': datetime.now().isoformat()
            })
    
    activity_df = pd.DataFrame(activity_logs)
    activity_df = activity_df.sort_values('timestamp').reset_index(drop=True)
    
    # CSV 파일로 저장
    activity_df.to_csv('datasets/student_activity_logs.csv', index=False)
    print(f"✓ 학생 활동 로그 데이터셋 생성 완료: {len(activity_df)} 행")
    
    return activity_df

def generate_data_quality_issues():
    """의도적으로 데이터 품질 이슈가 있는 데이터셋 생성 (품질 검증 테스트용)"""
    print("데이터 품질 테스트용 데이터셋 생성 중...")
    
    # 기본 데이터 생성
    student_ids = [f"STU_{i:04d}" for i in range(1, 101)]
    
    problematic_data = []
    for i, student_id in enumerate(student_ids):
        record = {
            'student_id': student_id,
            'name': f"Student_{i+1}",
            'email': f"student{i+1}@university.edu",
            'age': np.random.randint(18, 25),
            'gpa': round(np.random.uniform(2.0, 4.0), 2),
            'major': np.random.choice(['CS', 'Math', 'Physics', 'Chemistry']),
            'enrollment_date': (datetime.now() - timedelta(days=np.random.randint(365, 1460))).strftime('%Y-%m-%d')
        }
        
        # 의도적으로 품질 이슈 추가
        if i % 10 == 0:  # 10%의 데이터에 결측값
            record['email'] = None
        
        if i % 15 == 0:  # 약 7%의 데이터에 잘못된 GPA
            record['gpa'] = round(np.random.uniform(4.1, 5.0), 2)  # 4.0 초과
        
        if i % 20 == 0:  # 5%의 데이터에 잘못된 나이
            record['age'] = np.random.randint(10, 17)  # 너무 어림
        
        if i % 25 == 0:  # 4%의 데이터에 잘못된 전공
            record['major'] = 'INVALID_MAJOR'
        
        problematic_data.append(record)
    
    # 중복 데이터 추가 (5개)
    for i in range(5):
        problematic_data.append(problematic_data[i].copy())
    
    problematic_df = pd.DataFrame(problematic_data)
    problematic_df.to_csv('datasets/problematic_student_data.csv', index=False)
    print(f"✓ 품질 테스트용 데이터셋 생성 완료: {len(problematic_df)} 행 (품질 이슈 포함)")
    
    return problematic_df

def main():
    """메인 실행 함수"""
    print("=== AWS 데이터 분석 워크샵 - 추가 데이터셋 생성 ===\n")
    
    try:
        # 각 데이터셋 생성
        academic_df = create_academic_performance_dataset()
        enrollment_df = create_course_enrollment_dataset()
        activity_df = create_student_activity_logs()
        problematic_df = generate_data_quality_issues()
        
        print("\n=== 생성 완료 요약 ===")
        print(f"✓ 학업 성과 데이터: {len(academic_df)} 행")
        print(f"✓ 수강 신청 데이터: {len(enrollment_df)} 행")
        print(f"✓ 활동 로그 데이터: {len(activity_df)} 행")
        print(f"✓ 품질 테스트 데이터: {len(problematic_df)} 행")
        
        print("\n=== 다음 단계 ===")
        print("1. AWS CLI를 사용하여 S3에 데이터 업로드:")
        print("   aws s3 cp datasets/ s3://your-workshop-bucket/raw-data/ --recursive")
        print("\n2. AWS Glue 크롤러 실행하여 테이블 스키마 생성")
        print("\n3. 고급 ETL 스크립트 실행")
        
    except Exception as e:
        print(f"❌ 오류 발생: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())