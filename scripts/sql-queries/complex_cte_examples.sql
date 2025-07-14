-- 복잡한 CTE (Common Table Expressions) 예제 모음
-- 다단계 분석을 위한 고급 SQL 쿼리들

-- =============================================================================
-- 1. 다단계 CTE를 활용한 학습 효과성 종합 분석
-- =============================================================================

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
        ROUND(
            COALESCE(attendance_rate, 0.8) * 0.4 + 
            COALESCE(assignment_submission_rate, 0.85) * 0.6, 3
        ) as engagement_score,
        -- AI 활용도 점수
        ROUND(
            COALESCE(usage_frequency_score, 2) * 0.5 + 
            COALESCE(satisfaction_level, 3) * 0.3 + 
            COALESCE(num_ai_tools, 1) * 0.2, 2
        ) as ai_utilization_score
    FROM integrated_student_analysis
    WHERE gpa IS NOT NULL 
      AND usage_frequency_score IS NOT NULL
      AND attendance_rate IS NOT NULL
),

-- 2단계: 전공별 벤치마크 계산
field_benchmarks AS (
    SELECT 
        field_of_study,
        COUNT(*) as field_student_count,
        ROUND(AVG(gpa), 3) as field_avg_gpa,
        ROUND(AVG(engagement_score), 3) as field_avg_engagement,
        ROUND(AVG(ai_utilization_score), 2) as field_avg_ai_utilization,
        ROUND(STDDEV(gpa), 3) as field_gpa_stddev,
        ROUND(STDDEV(engagement_score), 3) as field_engagement_stddev,
        ROUND(STDDEV(ai_utilization_score), 3) as field_ai_stddev,
        -- 분위수 계산
        APPROX_PERCENTILE(gpa, 0.25) as field_gpa_q1,
        APPROX_PERCENTILE(gpa, 0.5) as field_gpa_median,
        APPROX_PERCENTILE(gpa, 0.75) as field_gpa_q3,
        APPROX_PERCENTILE(engagement_score, 0.5) as field_engagement_median,
        APPROX_PERCENTILE(ai_utilization_score, 0.5) as field_ai_median
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
        fb.field_engagement_stddev,
        fb.field_ai_stddev,
        fb.field_gpa_median,
        fb.field_engagement_median,
        fb.field_ai_median,
        -- 전공 평균 대비 성과
        ROUND(bm.gpa - fb.field_avg_gpa, 3) as gpa_vs_field_avg,
        ROUND(bm.engagement_score - fb.field_avg_engagement, 3) as engagement_vs_field_avg,
        ROUND(bm.ai_utilization_score - fb.field_avg_ai_utilization, 3) as ai_utilization_vs_field_avg,
        -- Z-score 계산
        CASE 
            WHEN fb.field_gpa_stddev > 0 THEN 
                ROUND((bm.gpa - fb.field_avg_gpa) / fb.field_gpa_stddev, 3)
            ELSE 0
        END as gpa_z_score,
        CASE 
            WHEN fb.field_engagement_stddev > 0 THEN 
                ROUND((bm.engagement_score - fb.field_avg_engagement) / fb.field_engagement_stddev, 3)
            ELSE 0
        END as engagement_z_score,
        CASE 
            WHEN fb.field_ai_stddev > 0 THEN 
                ROUND((bm.ai_utilization_score - fb.field_avg_ai_utilization) / fb.field_ai_stddev, 3)
            ELSE 0
        END as ai_utilization_z_score
    FROM base_metrics bm
    JOIN field_benchmarks fb ON bm.field_of_study = fb.field_of_study
),

-- 4단계: 학습 효과성 분류
learning_effectiveness AS (
    SELECT 
        *,
        -- 종합 효과성 점수 (Z-score 기반)
        ROUND(
            (CASE WHEN gpa_z_score > 1 THEN 3
                  WHEN gpa_z_score > 0 THEN 2
                  WHEN gpa_z_score > -1 THEN 1
                  ELSE 0 END) * 0.4 +
            (CASE WHEN engagement_z_score > 1 THEN 3
                  WHEN engagement_z_score > 0 THEN 2
                  WHEN engagement_z_score > -1 THEN 1
                  ELSE 0 END) * 0.3 +
            (CASE WHEN ai_utilization_z_score > 1 THEN 3
                  WHEN ai_utilization_z_score > 0 THEN 2
                  WHEN ai_utilization_z_score > -1 THEN 1
                  ELSE 0 END) * 0.3, 1
        ) as effectiveness_score,
        -- 학습자 유형 분류
        CASE 
            WHEN gpa_z_score > 1 AND ai_utilization_z_score > 0.5 THEN 'High Achiever + AI Savvy'
            WHEN gpa_z_score > 1 AND ai_utilization_z_score <= 0 THEN 'High Achiever + Traditional'
            WHEN gpa_z_score <= 0 AND ai_utilization_z_score > 0.5 THEN 'Struggling + AI Dependent'
            WHEN gpa_z_score <= 0 AND engagement_z_score <= 0 THEN 'At Risk'
            WHEN engagement_z_score > 1 AND gpa_z_score > 0 THEN 'Engaged High Performer'
            WHEN engagement_z_score > 1 AND gpa_z_score <= 0 THEN 'Engaged Underperformer'
            ELSE 'Average Performer'
        END as learner_type,
        -- 개선 잠재력 평가
        CASE 
            WHEN ai_utilization_z_score >= 1 AND gpa_z_score < 0 THEN 'High Potential'
            WHEN engagement_z_score >= 1 AND gpa_z_score < 0.5 THEN 'Medium Potential'
            WHEN ai_utilization_z_score < -0.5 AND gpa_z_score > 0 THEN 'AI Enhancement Opportunity'
            ELSE 'Stable'
        END as improvement_potential
    FROM relative_performance
),

-- 5단계: 최종 분석 및 인사이트
final_insights AS (
    SELECT 
        field_of_study,
        learner_type,
        improvement_potential,
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
        APPROX_PERCENTILE(effectiveness_score, 0.5) as median_effectiveness,
        ROUND(STDDEV(effectiveness_score), 2) as effectiveness_stddev
    FROM learning_effectiveness
    GROUP BY field_of_study, learner_type, improvement_potential
    HAVING COUNT(*) >= 3
)

-- 최종 결과 출력
SELECT 
    field_of_study,
    learner_type,
    improvement_potential,
    student_count,
    avg_gpa,
    avg_effectiveness_score,
    avg_engagement,
    avg_ai_utilization,
    avg_gpa_vs_field,
    avg_engagement_vs_field,
    avg_ai_utilization_vs_field,
    median_effectiveness,
    effectiveness_stddev,
    -- 전체 대비 비율
    ROUND(100.0 * student_count / SUM(student_count) OVER (PARTITION BY field_of_study), 1) as pct_of_field,
    -- 효과성 순위
    RANK() OVER (PARTITION BY field_of_study ORDER BY avg_effectiveness_score DESC) as effectiveness_rank
FROM final_insights
ORDER BY field_of_study, avg_effectiveness_score DESC;

-- =============================================================================
-- 2. 코호트 분석 - AI 도구 사용 패턴별 성과 추적
-- =============================================================================

WITH 
-- 코호트 정의
ai_usage_cohorts AS (
    SELECT 
        student_id,
        field_of_study,
        year_of_study,
        usage_frequency_score,
        satisfaction_level,
        num_ai_tools,
        gpa,
        attendance_rate,
        assignment_submission_rate,
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
        -- 학년별 경험 수준
        CASE 
            WHEN year_of_study <= 1 THEN 'Freshman'
            WHEN year_of_study <= 2 THEN 'Sophomore'
            WHEN year_of_study <= 3 THEN 'Junior'
            ELSE 'Senior'
        END as academic_level
    FROM integrated_student_analysis
    WHERE usage_frequency_score IS NOT NULL 
      AND satisfaction_level IS NOT NULL
      AND gpa IS NOT NULL
),

-- 코호트별 기본 통계
cohort_stats AS (
    SELECT 
        usage_cohort,
        satisfaction_segment,
        academic_level,
        field_of_study,
        COUNT(*) as cohort_size,
        ROUND(AVG(gpa), 3) as avg_gpa,
        ROUND(AVG(attendance_rate), 3) as avg_attendance,
        ROUND(AVG(assignment_submission_rate), 3) as avg_submission_rate,
        ROUND(AVG(usage_frequency_score), 2) as avg_usage_frequency,
        ROUND(AVG(satisfaction_level), 2) as avg_satisfaction,
        ROUND(AVG(num_ai_tools), 1) as avg_tools_used,
        -- 성과 분포
        ROUND(STDDEV(gpa), 3) as gpa_stddev,
        MIN(gpa) as min_gpa,
        MAX(gpa) as max_gpa,
        APPROX_PERCENTILE(gpa, 0.25) as gpa_q1,
        APPROX_PERCENTILE(gpa, 0.5) as gpa_median,
        APPROX_PERCENTILE(gpa, 0.75) as gpa_q3
    FROM ai_usage_cohorts
    GROUP BY usage_cohort, satisfaction_segment, academic_level, field_of_study
    HAVING COUNT(*) >= 5
),

-- 코호트 간 비교 분석
cohort_comparison AS (
    SELECT 
        cs.*,
        -- 전체 평균 대비 성과
        cs.avg_gpa - AVG(cs.avg_gpa) OVER (PARTITION BY cs.field_of_study) as gpa_vs_field_avg,
        -- 코호트 순위
        RANK() OVER (PARTITION BY cs.field_of_study ORDER BY cs.avg_gpa DESC) as performance_rank,
        -- 효과성 지수 계산
        CASE 
            WHEN cs.avg_usage_frequency > 0 THEN 
                ROUND((cs.avg_gpa / cs.avg_usage_frequency) * 100, 1)
            ELSE NULL
        END as efficiency_index,
        -- 균형 점수 (성과와 만족도의 조화)
        ROUND((cs.avg_gpa * 0.7 + cs.avg_satisfaction * 0.3), 3) as balance_score
    FROM cohort_stats cs
),

-- 코호트 성공 패턴 분석
success_patterns AS (
    SELECT 
        usage_cohort,
        satisfaction_segment,
        COUNT(DISTINCT field_of_study) as fields_represented,
        COUNT(*) as total_cohorts,
        ROUND(AVG(avg_gpa), 3) as overall_avg_gpa,
        ROUND(AVG(balance_score), 3) as overall_balance_score,
        -- 성공 코호트 비율 (상위 25% 성과)
        ROUND(
            100.0 * SUM(CASE WHEN performance_rank <= CEIL(COUNT(*) OVER (PARTITION BY field_of_study) * 0.25) THEN 1 ELSE 0 END) / 
            COUNT(*), 1
        ) as success_rate,
        -- 일관성 지표 (표준편차가 낮을수록 일관된 성과)
        ROUND(STDDEV(avg_gpa), 3) as performance_consistency
    FROM cohort_comparison
    GROUP BY usage_cohort, satisfaction_segment
)

-- 최종 코호트 분석 결과
SELECT 
    usage_cohort,
    satisfaction_segment,
    fields_represented,
    total_cohorts,
    overall_avg_gpa,
    overall_balance_score,
    success_rate,
    performance_consistency,
    -- 코호트 추천도
    CASE 
        WHEN success_rate >= 75 AND performance_consistency <= 0.3 THEN 'Highly Recommended'
        WHEN success_rate >= 50 AND performance_consistency <= 0.5 THEN 'Recommended'
        WHEN success_rate >= 25 THEN 'Conditionally Recommended'
        ELSE 'Not Recommended'
    END as recommendation_level,
    -- 개선 제안
    CASE 
        WHEN usage_cohort = 'Light Users' AND satisfaction_segment IN ('Satisfied', 'Highly Satisfied') THEN 'Increase Usage Frequency'
        WHEN usage_cohort IN ('Power Users', 'Regular Users') AND satisfaction_segment = 'Dissatisfied' THEN 'Improve Tool Selection'
        WHEN success_rate < 25 THEN 'Comprehensive Support Needed'
        ELSE 'Maintain Current Approach'
    END as improvement_suggestion
FROM success_patterns
ORDER BY overall_balance_score DESC;

-- =============================================================================
-- 3. 시계열 트렌드 분석 - 학기별 성과 변화
-- =============================================================================

WITH 
-- 학기별 개별 성과
semester_individual AS (
    SELECT 
        student_id,
        field_of_study,
        semester,
        gpa,
        usage_frequency_score,
        satisfaction_level,
        attendance_rate,
        -- 학기 순서 정의
        ROW_NUMBER() OVER (PARTITION BY student_id ORDER BY semester) as semester_order,
        -- 이전 학기 데이터
        LAG(gpa, 1) OVER (PARTITION BY student_id ORDER BY semester) as prev_gpa,
        LAG(usage_frequency_score, 1) OVER (PARTITION BY student_id ORDER BY semester) as prev_usage,
        LAG(satisfaction_level, 1) OVER (PARTITION BY student_id ORDER BY semester) as prev_satisfaction,
        -- 다음 학기 데이터
        LEAD(gpa, 1) OVER (PARTITION BY student_id ORDER BY semester) as next_gpa,
        LEAD(usage_frequency_score, 1) OVER (PARTITION BY student_id ORDER BY semester) as next_usage
    FROM integrated_student_analysis
    WHERE semester IS NOT NULL 
      AND gpa IS NOT NULL
      AND usage_frequency_score IS NOT NULL
),

-- 변화량 계산
semester_changes AS (
    SELECT 
        *,
        -- 성과 변화량
        CASE WHEN prev_gpa IS NOT NULL THEN ROUND(gpa - prev_gpa, 3) ELSE NULL END as gpa_change,
        CASE WHEN prev_usage IS NOT NULL THEN ROUND(usage_frequency_score - prev_usage, 2) ELSE NULL END as usage_change,
        CASE WHEN prev_satisfaction IS NOT NULL THEN ROUND(satisfaction_level - prev_satisfaction, 2) ELSE NULL END as satisfaction_change,
        -- 트렌드 방향
        CASE 
            WHEN prev_gpa IS NOT NULL THEN
                CASE 
                    WHEN gpa - prev_gpa > 0.2 THEN 'Improving'
                    WHEN gpa - prev_gpa < -0.2 THEN 'Declining'
                    ELSE 'Stable'
                END
            ELSE 'First Semester'
        END as performance_trend,
        -- 예측 성과 (다음 학기)
        CASE 
            WHEN next_gpa IS NOT NULL AND prev_gpa IS NOT NULL THEN
                CASE 
                    WHEN (gpa - prev_gpa) > 0 AND (next_gpa - gpa) > 0 THEN 'Sustained Growth'
                    WHEN (gpa - prev_gpa) > 0 AND (next_gpa - gpa) <= 0 THEN 'Peak Performance'
                    WHEN (gpa - prev_gpa) <= 0 AND (next_gpa - gpa) > 0 THEN 'Recovery'
                    WHEN (gpa - prev_gpa) <= 0 AND (next_gpa - gpa) <= 0 THEN 'Continued Decline'
                    ELSE 'Fluctuating'
                END
            ELSE NULL
        END as trajectory_pattern
    FROM semester_individual
),

-- 전공별 트렌드 집계
field_trends AS (
    SELECT 
        field_of_study,
        semester,
        performance_trend,
        COUNT(*) as student_count,
        ROUND(AVG(gpa), 3) as avg_gpa,
        ROUND(AVG(gpa_change), 3) as avg_gpa_change,
        ROUND(AVG(usage_frequency_score), 2) as avg_usage,
        ROUND(AVG(usage_change), 2) as avg_usage_change,
        ROUND(AVG(satisfaction_level), 2) as avg_satisfaction,
        -- 변화의 일관성
        ROUND(STDDEV(gpa_change), 3) as gpa_change_stddev,
        -- 극단적 변화 비율
        ROUND(100.0 * SUM(CASE WHEN ABS(gpa_change) > 0.5 THEN 1 ELSE 0 END) / COUNT(*), 1) as extreme_change_pct
    FROM semester_changes
    WHERE performance_trend != 'First Semester'
    GROUP BY field_of_study, semester, performance_trend
),

-- 궤적 패턴 분석
trajectory_analysis AS (
    SELECT 
        field_of_study,
        trajectory_pattern,
        COUNT(*) as pattern_count,
        ROUND(AVG(gpa), 3) as avg_final_gpa,
        ROUND(AVG(usage_frequency_score), 2) as avg_final_usage,
        -- 패턴별 성공률
        ROUND(100.0 * SUM(CASE WHEN gpa >= 3.5 THEN 1 ELSE 0 END) / COUNT(*), 1) as high_performance_rate,
        -- AI 사용과 성과 궤적의 관계
        ROUND(
            SUM(usage_change * gpa_change) / 
            SQRT(SUM(usage_change * usage_change) * SUM(gpa_change * gpa_change)), 3
        ) as usage_performance_correlation
    FROM semester_changes
    WHERE trajectory_pattern IS NOT NULL
      AND usage_change IS NOT NULL
      AND gpa_change IS NOT NULL
    GROUP BY field_of_study, trajectory_pattern
    HAVING COUNT(*) >= 5
)

-- 최종 트렌드 분석 결과
SELECT 
    ft.field_of_study,
    ft.semester,
    ft.performance_trend,
    ft.student_count,
    ft.avg_gpa,
    ft.avg_gpa_change,
    ft.avg_usage,
    ft.avg_usage_change,
    ft.avg_satisfaction,
    ft.gpa_change_stddev,
    ft.extreme_change_pct,
    -- 트렌드 안정성 평가
    CASE 
        WHEN ft.gpa_change_stddev <= 0.2 AND ft.extreme_change_pct <= 10 THEN 'Very Stable'
        WHEN ft.gpa_change_stddev <= 0.4 AND ft.extreme_change_pct <= 20 THEN 'Stable'
        WHEN ft.gpa_change_stddev <= 0.6 AND ft.extreme_change_pct <= 30 THEN 'Moderate Volatility'
        ELSE 'High Volatility'
    END as trend_stability,
    -- 개입 필요성
    CASE 
        WHEN ft.performance_trend = 'Declining' AND ft.extreme_change_pct > 25 THEN 'Immediate Intervention'
        WHEN ft.performance_trend = 'Declining' THEN 'Monitor Closely'
        WHEN ft.performance_trend = 'Stable' AND ft.avg_gpa < 2.5 THEN 'Support Needed'
        ELSE 'Continue Current Approach'
    END as intervention_recommendation
FROM field_trends ft
ORDER BY ft.field_of_study, ft.semester, 
         CASE ft.performance_trend 
             WHEN 'Improving' THEN 1
             WHEN 'Stable' THEN 2
             WHEN 'Declining' THEN 3
         END;