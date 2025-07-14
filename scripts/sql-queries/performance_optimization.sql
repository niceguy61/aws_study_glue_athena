-- 성능 최적화를 위한 Athena 쿼리 예제 모음
-- 대용량 데이터 처리 및 쿼리 튜닝 기법

-- =============================================================================
-- 1. 파티션 프루닝 최적화
-- =============================================================================

-- ✅ 좋은 예: 파티션 키를 WHERE 절에 명시
SELECT 
    field_of_study,
    COUNT(*) as student_count,
    AVG(gpa) as avg_gpa,
    AVG(usage_frequency_score) as avg_usage,
    STDDEV(gpa) as gpa_stddev
FROM integrated_student_analysis
WHERE field_of_study IN ('Computer Science', 'Mathematics', 'Physics')  -- 파티션 프루닝
  AND semester = '2024-2'  -- 파티션 프루닝
  AND gpa IS NOT NULL
  AND usage_frequency_score IS NOT NULL
GROUP BY field_of_study
ORDER BY avg_gpa DESC;

-- ❌ 나쁜 예: 파티션 키에 함수 적용
-- SELECT * FROM integrated_student_analysis 
-- WHERE UPPER(field_of_study) = 'COMPUTER SCIENCE'  -- 파티션 프루닝 불가
-- WHERE YEAR(CAST(last_updated AS DATE)) = 2024     -- 파티션 프루닝 불가

-- ✅ 시간 범위 쿼리 최적화
SELECT 
    DATE_TRUNC('month', CAST(last_updated AS DATE)) as month,
    field_of_study,
    COUNT(*) as monthly_count,
    AVG(gpa) as avg_monthly_gpa,
    AVG(usage_frequency_score) as avg_monthly_usage
FROM integrated_student_analysis
WHERE last_updated >= '2024-01-01'  -- 파티션 프루닝
  AND last_updated < '2024-12-31'   -- 파티션 프루닝
  AND field_of_study IS NOT NULL
  AND gpa IS NOT NULL
GROUP BY DATE_TRUNC('month', CAST(last_updated AS DATE)), field_of_study
ORDER BY month, field_of_study;

-- =============================================================================
-- 2. 집계 최적화 기법
-- =============================================================================

-- ✅ 효율적인 집계를 위한 단계별 최적화
WITH 
-- 1단계: 필요한 컬럼만 선택하여 데이터 스캔 최소화
filtered_data AS (
    SELECT 
        field_of_study,
        gpa,
        usage_frequency_score,
        satisfaction_level,
        num_ai_tools,
        attendance_rate
    FROM integrated_student_analysis
    WHERE gpa IS NOT NULL 
      AND usage_frequency_score IS NOT NULL
      AND field_of_study IN ('Computer Science', 'Mathematics', 'Physics', 'Chemistry')  -- 조기 필터링
      AND semester IN ('2024-1', '2024-2')  -- 파티션 프루닝
),

-- 2단계: 중간 집계로 데이터 크기 축소
pre_aggregated AS (
    SELECT 
        field_of_study,
        -- 기본 통계를 위한 집계
        COUNT(*) as student_count,
        SUM(gpa) as total_gpa,
        SUM(gpa * gpa) as sum_gpa_squared,
        SUM(usage_frequency_score) as total_usage,
        SUM(satisfaction_level) as total_satisfaction,
        SUM(num_ai_tools) as total_tools,
        SUM(attendance_rate) as total_attendance,
        
        -- 분포 계산을 위한 집계
        SUM(CASE WHEN gpa >= 3.5 THEN 1 ELSE 0 END) as high_performers,
        SUM(CASE WHEN gpa < 2.5 THEN 1 ELSE 0 END) as low_performers,
        SUM(CASE WHEN usage_frequency_score >= 4 THEN 1 ELSE 0 END) as high_users,
        SUM(CASE WHEN satisfaction_level >= 4 THEN 1 ELSE 0 END) as highly_satisfied,
        
        -- 상관관계 계산을 위한 집계
        SUM(gpa * usage_frequency_score) as gpa_usage_product,
        SUM(usage_frequency_score * usage_frequency_score) as sum_usage_squared,
        SUM(usage_frequency_score * satisfaction_level) as usage_satisfaction_product,
        SUM(satisfaction_level * satisfaction_level) as sum_satisfaction_squared,
        
        -- 최솟값과 최댓값
        MIN(gpa) as min_gpa,
        MAX(gpa) as max_gpa,
        MIN(usage_frequency_score) as min_usage,
        MAX(usage_frequency_score) as max_usage
    FROM filtered_data
    GROUP BY field_of_study
),

-- 3단계: 최종 계산 (복잡한 수식은 마지막에)
final_calculations AS (
    SELECT 
        field_of_study,
        student_count,
        
        -- 평균 계산
        ROUND(total_gpa / student_count, 3) as avg_gpa,
        ROUND(total_usage / student_count, 2) as avg_usage,
        ROUND(total_satisfaction / student_count, 2) as avg_satisfaction,
        ROUND(total_tools / student_count, 1) as avg_tools,
        ROUND(total_attendance / student_count, 3) as avg_attendance,
        
        -- 표준편차 계산 (베셀 보정 적용)
        ROUND(
            SQRT(
                GREATEST(0, 
                    (sum_gpa_squared - (total_gpa * total_gpa / student_count)) / 
                    GREATEST(1, student_count - 1)
                )
            ), 3
        ) as gpa_stddev,
        
        -- 비율 계산
        ROUND(100.0 * high_performers / student_count, 1) as high_performer_pct,
        ROUND(100.0 * low_performers / student_count, 1) as low_performer_pct,
        ROUND(100.0 * high_users / student_count, 1) as high_user_pct,
        ROUND(100.0 * highly_satisfied / student_count, 1) as highly_satisfied_pct,
        
        -- 피어슨 상관계수 계산
        ROUND(
            CASE 
                WHEN student_count > 1 THEN
                    (gpa_usage_product - (total_gpa * total_usage / student_count)) /
                    NULLIF(
                        SQRT(
                            (sum_gpa_squared - (total_gpa * total_gpa / student_count)) *
                            (sum_usage_squared - (total_usage * total_usage / student_count))
                        ), 0
                    )
                ELSE NULL
            END, 4
        ) as gpa_usage_correlation,
        
        -- 범위 계산
        ROUND(max_gpa - min_gpa, 3) as gpa_range,
        ROUND(max_usage - min_usage, 2) as usage_range
    FROM pre_aggregated
)

-- 최종 결과 출력
SELECT 
    field_of_study,
    student_count,
    avg_gpa,
    gpa_stddev,
    avg_usage,
    avg_satisfaction,
    avg_tools,
    avg_attendance,
    high_performer_pct,
    low_performer_pct,
    high_user_pct,
    highly_satisfied_pct,
    gpa_usage_correlation,
    gpa_range,
    usage_range,
    
    -- 종합 평가 지수
    ROUND(
        (avg_gpa * 0.3 + 
         avg_usage * 0.2 + 
         avg_satisfaction * 0.2 + 
         avg_attendance * 4 * 0.15 +
         high_performer_pct * 0.01 * 0.15), 3
    ) as composite_score
FROM final_calculations
ORDER BY composite_score DESC;

-- =============================================================================
-- 3. 대용량 데이터 처리 최적화
-- =============================================================================

-- ✅ LIMIT과 ORDER BY 최적화 - 상위 N개 결과만 필요한 경우
SELECT 
    student_id,
    field_of_study,
    gpa,
    usage_frequency_score,
    satisfaction_level,
    -- 윈도우 함수 최적화: 파티션 크기 제한
    ROW_NUMBER() OVER (
        PARTITION BY field_of_study 
        ORDER BY gpa DESC, usage_frequency_score DESC
    ) as rank_in_field
FROM integrated_student_analysis
WHERE field_of_study IN ('Computer Science', 'Mathematics')  -- 파티션 제한
  AND gpa IS NOT NULL
  AND usage_frequency_score IS NOT NULL
  AND semester = '2024-2'  -- 최신 데이터만
QUALIFY rank_in_field <= 10  -- 각 전공별 상위 10명만
ORDER BY field_of_study, rank_in_field;

-- ✅ 샘플링을 활용한 대용량 데이터 분석
WITH 
-- 10% 샘플링 (해시 기반 일관된 샘플링)
sampled_data AS (
    SELECT *
    FROM integrated_student_analysis
    WHERE gpa IS NOT NULL
      AND usage_frequency_score IS NOT NULL
      AND MOD(ABS(HASH(student_id)), 100) < 10  -- 10% 샘플링
),

-- 샘플 기반 분석
sample_analysis AS (
    SELECT 
        field_of_study,
        COUNT(*) as sample_size,
        COUNT(*) * 10 as estimated_total,  -- 샘플링 비율로 전체 추정
        AVG(gpa) as sample_avg_gpa,
        STDDEV(gpa) as sample_gpa_stddev,
        AVG(usage_frequency_score) as sample_avg_usage,
        STDDEV(usage_frequency_score) as sample_usage_stddev,
        -- 분위수 추정
        APPROX_PERCENTILE(gpa, 0.25) as sample_gpa_q1,
        APPROX_PERCENTILE(gpa, 0.5) as sample_gpa_median,
        APPROX_PERCENTILE(gpa, 0.75) as sample_gpa_q3,
        -- 상관관계 추정
        CORR(gpa, usage_frequency_score) as sample_correlation
    FROM sampled_data
    GROUP BY field_of_study
    HAVING COUNT(*) >= 20  -- 최소 샘플 크기 보장
)

SELECT 
    field_of_study,
    sample_size,
    estimated_total,
    ROUND(sample_avg_gpa, 3) as estimated_avg_gpa,
    ROUND(sample_gpa_stddev, 3) as estimated_gpa_stddev,
    ROUND(sample_avg_usage, 2) as estimated_avg_usage,
    ROUND(sample_usage_stddev, 2) as estimated_usage_stddev,
    ROUND(sample_gpa_median, 3) as estimated_median_gpa,
    ROUND(sample_correlation, 4) as estimated_correlation,
    
    -- 95% 신뢰구간 계산 (정규분포 가정)
    ROUND(sample_avg_gpa - 1.96 * sample_gpa_stddev / SQRT(sample_size), 3) as gpa_ci_lower,
    ROUND(sample_avg_gpa + 1.96 * sample_gpa_stddev / SQRT(sample_size), 3) as gpa_ci_upper,
    
    -- 표본 오차 추정
    ROUND(1.96 * sample_gpa_stddev / SQRT(sample_size), 3) as margin_of_error,
    
    -- 샘플링 품질 평가
    CASE 
        WHEN sample_size >= 100 THEN 'High Quality'
        WHEN sample_size >= 50 THEN 'Good Quality'
        WHEN sample_size >= 20 THEN 'Acceptable Quality'
        ELSE 'Low Quality'
    END as sample_quality
FROM sample_analysis
ORDER BY estimated_total DESC;

-- =============================================================================
-- 4. 윈도우 함수 성능 최적화
-- =============================================================================

-- ✅ 윈도우 함수 최적화 - 파티션 크기 제한 및 정렬 최적화
WITH 
-- 사전 필터링으로 윈도우 함수 처리 데이터 축소
filtered_students AS (
    SELECT 
        student_id,
        field_of_study,
        semester,
        gpa,
        usage_frequency_score,
        satisfaction_level
    FROM integrated_student_analysis
    WHERE gpa IS NOT NULL
      AND usage_frequency_score IS NOT NULL
      AND field_of_study IN ('Computer Science', 'Mathematics', 'Physics')  -- 파티션 제한
      AND semester IN ('2024-1', '2024-2')  -- 시간 범위 제한
),

-- 최적화된 윈도우 함수 적용
windowed_analysis AS (
    SELECT 
        student_id,
        field_of_study,
        semester,
        gpa,
        usage_frequency_score,
        satisfaction_level,
        
        -- 효율적인 순위 함수 (동일 파티션/정렬 기준 재사용)
        ROW_NUMBER() OVER (
            PARTITION BY field_of_study, semester 
            ORDER BY gpa DESC
        ) as gpa_rank,
        
        DENSE_RANK() OVER (
            PARTITION BY field_of_study, semester 
            ORDER BY gpa DESC
        ) as gpa_dense_rank,
        
        -- 백분위수 계산
        PERCENT_RANK() OVER (
            PARTITION BY field_of_study, semester 
            ORDER BY gpa
        ) as gpa_percentile,
        
        -- 이동 평균 (범위 제한)
        AVG(gpa) OVER (
            PARTITION BY student_id 
            ORDER BY semester 
            ROWS BETWEEN 1 PRECEDING AND CURRENT ROW
        ) as moving_avg_gpa,
        
        -- 누적 통계
        COUNT(*) OVER (
            PARTITION BY field_of_study, semester
        ) as total_students_in_group,
        
        -- 상대적 위치
        (ROW_NUMBER() OVER (
            PARTITION BY field_of_study, semester 
            ORDER BY gpa DESC
        ) - 1.0) / NULLIF(COUNT(*) OVER (PARTITION BY field_of_study, semester) - 1, 0) as relative_position
    FROM filtered_students
)

-- 결과 필터링 (상위 성과자만)
SELECT 
    field_of_study,
    semester,
    student_id,
    gpa,
    usage_frequency_score,
    gpa_rank,
    gpa_dense_rank,
    ROUND(gpa_percentile, 3) as gpa_percentile,
    ROUND(moving_avg_gpa, 3) as moving_avg_gpa,
    total_students_in_group,
    ROUND(relative_position, 3) as relative_position,
    
    -- 성과 카테고리
    CASE 
        WHEN gpa_percentile >= 0.9 THEN 'Top 10%'
        WHEN gpa_percentile >= 0.75 THEN 'Top 25%'
        WHEN gpa_percentile >= 0.5 THEN 'Top 50%'
        ELSE 'Bottom 50%'
    END as performance_tier
FROM windowed_analysis
WHERE gpa_rank <= 20  -- 각 그룹별 상위 20명만
ORDER BY field_of_study, semester, gpa_rank;

-- =============================================================================
-- 5. 조인 성능 최적화
-- =============================================================================

-- ✅ 효율적인 조인 최적화
WITH 
-- 작은 테이블 (브로드캐스트 조인 후보)
field_stats AS (
    SELECT 
        field_of_study,
        COUNT(*) as total_students,
        AVG(gpa) as field_avg_gpa,
        STDDEV(gpa) as field_stddev_gpa
    FROM integrated_student_analysis
    WHERE gpa IS NOT NULL
      AND semester = '2024-2'  -- 최신 데이터만
    GROUP BY field_of_study
    HAVING COUNT(*) >= 10  -- 최소 학생 수 보장
),

-- 큰 테이블 사전 필터링
student_details AS (
    SELECT 
        student_id,
        field_of_study,
        gpa,
        usage_frequency_score,
        satisfaction_level,
        attendance_rate
    FROM integrated_student_analysis
    WHERE gpa IS NOT NULL
      AND usage_frequency_score IS NOT NULL
      AND semester = '2024-2'
      AND field_of_study IN (
          SELECT field_of_study 
          FROM field_stats  -- 서브쿼리로 조인 대상 제한
      )
)

-- 최적화된 조인 (작은 테이블을 브로드캐스트)
SELECT 
    sd.field_of_study,
    sd.student_id,
    sd.gpa,
    sd.usage_frequency_score,
    sd.satisfaction_level,
    sd.attendance_rate,
    
    -- 전공 통계 정보
    fs.total_students,
    fs.field_avg_gpa,
    fs.field_stddev_gpa,
    
    -- 상대적 성과 계산
    ROUND(sd.gpa - fs.field_avg_gpa, 3) as gpa_vs_field_avg,
    CASE 
        WHEN fs.field_stddev_gpa > 0 THEN 
            ROUND((sd.gpa - fs.field_avg_gpa) / fs.field_stddev_gpa, 3)
        ELSE 0
    END as gpa_z_score,
    
    -- 성과 등급
    CASE 
        WHEN sd.gpa >= fs.field_avg_gpa + fs.field_stddev_gpa THEN 'Above Average'
        WHEN sd.gpa >= fs.field_avg_gpa THEN 'Average'
        WHEN sd.gpa >= fs.field_avg_gpa - fs.field_stddev_gpa THEN 'Below Average'
        ELSE 'Well Below Average'
    END as performance_grade
FROM student_details sd
JOIN field_stats fs ON sd.field_of_study = fs.field_of_study  -- 이미 필터링된 데이터 조인
WHERE sd.gpa IS NOT NULL
ORDER BY sd.field_of_study, sd.gpa DESC;

-- =============================================================================
-- 6. 쿼리 성능 모니터링 및 분석
-- =============================================================================

-- 쿼리 실행 계획 분석
EXPLAIN (TYPE DISTRIBUTED, FORMAT JSON)
SELECT 
    field_of_study,
    COUNT(*) as student_count,
    AVG(gpa) as avg_gpa,
    STDDEV(gpa) as gpa_stddev
FROM integrated_student_analysis
WHERE field_of_study = 'Computer Science'
  AND semester = '2024-2'
  AND gpa IS NOT NULL
GROUP BY field_of_study;

-- 데이터 스캔량 및 파일 정보 확인
SELECT 
    '$path' as file_path,
    '$file_size' as file_size_bytes,
    ROUND(CAST('$file_size' AS BIGINT) / 1024.0 / 1024.0, 2) as file_size_mb,
    COUNT(*) as record_count,
    COUNT(*) / (CAST('$file_size' AS BIGINT) / 1024.0 / 1024.0) as records_per_mb
FROM integrated_student_analysis
WHERE field_of_study = 'Computer Science'
  AND semester = '2024-2'
GROUP BY '$path', '$file_size'
ORDER BY CAST('$file_size' AS BIGINT) DESC;

-- 파티션별 데이터 분포 확인
SELECT 
    field_of_study,
    semester,
    COUNT(*) as record_count,
    MIN(gpa) as min_gpa,
    MAX(gpa) as max_gpa,
    AVG(gpa) as avg_gpa,
    -- 데이터 품질 지표
    COUNT(CASE WHEN gpa IS NULL THEN 1 END) as null_gpa_count,
    COUNT(CASE WHEN usage_frequency_score IS NULL THEN 1 END) as null_usage_count,
    ROUND(100.0 * COUNT(CASE WHEN gpa IS NULL THEN 1 END) / COUNT(*), 2) as null_gpa_pct
FROM integrated_student_analysis
GROUP BY field_of_study, semester
ORDER BY field_of_study, semester;

-- =============================================================================
-- 7. 메모리 효율적인 집계 쿼리
-- =============================================================================

-- ✅ 메모리 효율적인 대용량 집계
SELECT 
    field_of_study,
    
    -- 기본 통계 (메모리 효율적)
    COUNT(*) as total_students,
    COUNT(CASE WHEN gpa IS NOT NULL THEN 1 END) as valid_gpa_count,
    
    -- 근사 함수 사용으로 메모리 절약
    ROUND(APPROX_AVG(gpa), 3) as approx_avg_gpa,
    ROUND(APPROX_STDDEV(gpa), 3) as approx_stddev_gpa,
    
    -- 근사 분위수 (정확한 ORDER BY 없이 계산)
    APPROX_PERCENTILE(gpa, 0.25) as approx_gpa_q1,
    APPROX_PERCENTILE(gpa, 0.5) as approx_gpa_median,
    APPROX_PERCENTILE(gpa, 0.75) as approx_gpa_q3,
    
    -- 근사 고유값 개수
    APPROX_DISTINCT(student_id) as approx_unique_students,
    APPROX_DISTINCT(usage_frequency_score) as approx_unique_usage_scores,
    
    -- 효율적인 조건부 집계
    ROUND(100.0 * APPROX_AVG(CASE WHEN gpa >= 3.5 THEN 1.0 ELSE 0.0 END), 1) as high_performer_pct,
    ROUND(100.0 * APPROX_AVG(CASE WHEN usage_frequency_score >= 4 THEN 1.0 ELSE 0.0 END), 1) as high_usage_pct,
    
    -- 메모리 효율적인 상관관계 근사
    ROUND(CORR(gpa, usage_frequency_score), 4) as gpa_usage_correlation
    
FROM integrated_student_analysis
WHERE gpa IS NOT NULL
  AND usage_frequency_score IS NOT NULL
  AND semester IN ('2024-1', '2024-2')  -- 파티션 프루닝
GROUP BY field_of_study
HAVING COUNT(*) >= 20  -- 최소 샘플 크기
ORDER BY total_students DESC;