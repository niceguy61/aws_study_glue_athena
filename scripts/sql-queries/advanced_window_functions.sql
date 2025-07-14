-- 고급 윈도우 함수 예제 모음
-- Amazon Athena에서 실행 가능한 고급 분석 쿼리들

-- =============================================================================
-- 1. 학생 성과 순위 및 백분위수 분석
-- =============================================================================

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

-- =============================================================================
-- 2. 시계열 분석 - 학기별 성과 추이
-- =============================================================================

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

-- =============================================================================
-- 3. 이동 평균 및 누적 통계
-- =============================================================================

-- 학생별 3학기 이동 평균 GPA 계산
SELECT 
    student_id,
    field_of_study,
    semester,
    gpa,
    -- 3학기 이동 평균
    ROUND(
        AVG(gpa) OVER (
            PARTITION BY student_id 
            ORDER BY semester 
            ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
        ), 3
    ) as moving_avg_3_semesters,
    -- 누적 평균
    ROUND(
        AVG(gpa) OVER (
            PARTITION BY student_id 
            ORDER BY semester 
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        ), 3
    ) as cumulative_avg_gpa,
    -- 최고 GPA 대비 현재 성과
    ROUND(
        gpa / MAX(gpa) OVER (PARTITION BY student_id), 3
    ) as performance_vs_best,
    -- 학기별 성과 개선도
    ROUND(
        gpa - FIRST_VALUE(gpa) OVER (
            PARTITION BY student_id 
            ORDER BY semester 
            ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
        ), 3
    ) as improvement_from_first_semester
FROM integrated_student_analysis
WHERE gpa IS NOT NULL AND semester IS NOT NULL
ORDER BY student_id, semester;

-- =============================================================================
-- 4. 분위수 및 분포 분석
-- =============================================================================

-- 전공별 GPA 분포 및 분위수 분석
WITH gpa_distribution AS (
    SELECT 
        field_of_study,
        student_id,
        gpa,
        -- 분위수 계산
        NTILE(4) OVER (
            PARTITION BY field_of_study 
            ORDER BY gpa
        ) as gpa_quartile,
        NTILE(10) OVER (
            PARTITION BY field_of_study 
            ORDER BY gpa
        ) as gpa_decile,
        -- 백분위수
        PERCENT_RANK() OVER (
            PARTITION BY field_of_study 
            ORDER BY gpa
        ) as gpa_percentile_rank,
        -- 표준점수 (Z-score) 계산을 위한 평균과 표준편차
        AVG(gpa) OVER (PARTITION BY field_of_study) as field_avg_gpa,
        STDDEV(gpa) OVER (PARTITION BY field_of_study) as field_stddev_gpa
    FROM integrated_student_analysis
    WHERE gpa IS NOT NULL
)
SELECT 
    field_of_study,
    gpa_quartile,
    COUNT(*) as student_count,
    ROUND(MIN(gpa), 3) as min_gpa,
    ROUND(MAX(gpa), 3) as max_gpa,
    ROUND(AVG(gpa), 3) as avg_gpa,
    ROUND(STDDEV(gpa), 3) as stddev_gpa,
    -- 각 분위수의 범위
    ROUND(MIN(gpa_percentile_rank), 3) as min_percentile,
    ROUND(MAX(gpa_percentile_rank), 3) as max_percentile
FROM gpa_distribution
GROUP BY field_of_study, gpa_quartile
ORDER BY field_of_study, gpa_quartile;

-- =============================================================================
-- 5. 상관관계 및 회귀 분석 기초
-- =============================================================================

-- AI 사용과 학업 성과 간의 상관관계 분석
WITH correlation_analysis AS (
    SELECT 
        field_of_study,
        student_id,
        gpa,
        usage_frequency_score,
        satisfaction_level,
        num_ai_tools,
        -- 전공별 평균값들
        AVG(gpa) OVER (PARTITION BY field_of_study) as avg_gpa,
        AVG(usage_frequency_score) OVER (PARTITION BY field_of_study) as avg_usage,
        AVG(satisfaction_level) OVER (PARTITION BY field_of_study) as avg_satisfaction,
        -- 편차 계산
        gpa - AVG(gpa) OVER (PARTITION BY field_of_study) as gpa_deviation,
        usage_frequency_score - AVG(usage_frequency_score) OVER (PARTITION BY field_of_study) as usage_deviation,
        satisfaction_level - AVG(satisfaction_level) OVER (PARTITION BY field_of_study) as satisfaction_deviation
    FROM integrated_student_analysis
    WHERE gpa IS NOT NULL 
      AND usage_frequency_score IS NOT NULL 
      AND satisfaction_level IS NOT NULL
),
correlation_stats AS (
    SELECT 
        field_of_study,
        COUNT(*) as sample_size,
        -- 상관계수 계산 (피어슨)
        ROUND(
            SUM(gpa_deviation * usage_deviation) / 
            SQRT(
                SUM(gpa_deviation * gpa_deviation) * 
                SUM(usage_deviation * usage_deviation)
            ), 4
        ) as gpa_usage_correlation,
        ROUND(
            SUM(gpa_deviation * satisfaction_deviation) / 
            SQRT(
                SUM(gpa_deviation * gpa_deviation) * 
                SUM(satisfaction_deviation * satisfaction_deviation)
            ), 4
        ) as gpa_satisfaction_correlation,
        -- 회귀 계수 (기울기) 계산
        ROUND(
            SUM(gpa_deviation * usage_deviation) / 
            SUM(usage_deviation * usage_deviation), 4
        ) as gpa_usage_slope,
        -- 결정계수 (R²) 근사
        ROUND(
            POWER(
                SUM(gpa_deviation * usage_deviation) / 
                SQRT(
                    SUM(gpa_deviation * gpa_deviation) * 
                    SUM(usage_deviation * usage_deviation)
                ), 2
            ), 4
        ) as r_squared_gpa_usage
    FROM correlation_analysis
    GROUP BY field_of_study
)
SELECT 
    field_of_study,
    sample_size,
    gpa_usage_correlation,
    gpa_satisfaction_correlation,
    gpa_usage_slope,
    r_squared_gpa_usage,
    -- 상관관계 강도 해석
    CASE 
        WHEN ABS(gpa_usage_correlation) >= 0.7 THEN 'Strong'
        WHEN ABS(gpa_usage_correlation) >= 0.5 THEN 'Moderate'
        WHEN ABS(gpa_usage_correlation) >= 0.3 THEN 'Weak'
        ELSE 'Very Weak'
    END as correlation_strength,
    -- 통계적 유의성 추정 (간단한 기준)
    CASE 
        WHEN sample_size >= 30 AND ABS(gpa_usage_correlation) >= 0.3 THEN 'Likely Significant'
        WHEN sample_size >= 100 AND ABS(gpa_usage_correlation) >= 0.2 THEN 'Likely Significant'
        ELSE 'Not Significant'
    END as significance_estimate
FROM correlation_stats
ORDER BY ABS(gpa_usage_correlation) DESC;

-- =============================================================================
-- 6. 고급 순위 및 비교 분석
-- =============================================================================

-- 다중 기준 순위 분석
WITH multi_criteria_ranking AS (
    SELECT 
        student_id,
        field_of_study,
        gpa,
        usage_frequency_score,
        satisfaction_level,
        attendance_rate,
        assignment_submission_rate,
        -- 각 기준별 순위
        RANK() OVER (PARTITION BY field_of_study ORDER BY gpa DESC) as gpa_rank,
        RANK() OVER (PARTITION BY field_of_study ORDER BY usage_frequency_score DESC) as usage_rank,
        RANK() OVER (PARTITION BY field_of_study ORDER BY satisfaction_level DESC) as satisfaction_rank,
        RANK() OVER (PARTITION BY field_of_study ORDER BY attendance_rate DESC) as attendance_rank,
        -- 종합 점수 계산 (가중 평균)
        ROUND(
            (gpa * 0.4 + 
             usage_frequency_score * 0.2 + 
             satisfaction_level * 0.2 + 
             attendance_rate * 4 * 0.1 + 
             assignment_submission_rate * 4 * 0.1), 3
        ) as composite_score
    FROM integrated_student_analysis
    WHERE gpa IS NOT NULL 
      AND usage_frequency_score IS NOT NULL
      AND attendance_rate IS NOT NULL
),
final_rankings AS (
    SELECT 
        *,
        -- 종합 순위
        RANK() OVER (PARTITION BY field_of_study ORDER BY composite_score DESC) as overall_rank,
        -- 순위 변동성 계산 (표준편차)
        ROUND(
            SQRT(
                (POWER(gpa_rank - (gpa_rank + usage_rank + satisfaction_rank + attendance_rank) / 4.0, 2) +
                 POWER(usage_rank - (gpa_rank + usage_rank + satisfaction_rank + attendance_rank) / 4.0, 2) +
                 POWER(satisfaction_rank - (gpa_rank + usage_rank + satisfaction_rank + attendance_rank) / 4.0, 2) +
                 POWER(attendance_rank - (gpa_rank + usage_rank + satisfaction_rank + attendance_rank) / 4.0, 2)) / 3
            ), 2
        ) as rank_volatility
    FROM multi_criteria_ranking
)
SELECT 
    field_of_study,
    student_id,
    overall_rank,
    composite_score,
    gpa_rank,
    usage_rank,
    satisfaction_rank,
    attendance_rank,
    rank_volatility,
    -- 균형잡힌 성과자 식별
    CASE 
        WHEN rank_volatility <= 5 AND overall_rank <= 10 THEN 'Consistent Top Performer'
        WHEN rank_volatility <= 3 THEN 'Balanced Performer'
        WHEN rank_volatility > 10 THEN 'Inconsistent Performer'
        ELSE 'Average Performer'
    END as performance_type
FROM final_rankings
WHERE overall_rank <= 20  -- 상위 20명만 표시
ORDER BY field_of_study, overall_rank;