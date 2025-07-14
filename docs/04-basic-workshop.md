# 기본 실습 가이드

이 문서는 AWS 데이터 분석 파이프라인의 전체 과정을 단계별로 실습할 수 있는 가이드입니다. AWS 웹 콘솔을 통해 S3에서 데이터를 업로드하고, Glue로 ETL 작업을 수행한 후, Athena에서 분석하는 완전한 워크플로우를 경험하게 됩니다.

## 목차

1. [실습 환경 준비](#1-실습-환경-준비)
2. [S3 데이터 업로드 실습](#2-s3-데이터-업로드-실습)
3. [Glue 크롤러 실행 실습](#3-glue-크롤러-실행-실습)
4. [ETL 작업 생성 및 실행](#4-etl-작업-생성-및-실행)
5. [Athena 쿼리 실습](#5-athena-쿼리-실습)
6. [실습 검증 체크포인트](#6-실습-검증-체크포인트)

---

## 1. 실습 환경 준비

### 1.1 사전 준비사항

실습을 시작하기 전에 다음 사항들이 준비되어 있는지 확인하세요:

- [ ] AWS 계정 (프리 티어 계정 가능)
- [ ] 웹 브라우저 (Chrome, Firefox, Safari 등)
- [ ] 안정적인 인터넷 연결
- [ ] [AWS 설정 가이드](02-aws-setup-guide.md) 완료
- [ ] [데이터셋 가이드](03-dataset-guide.md)에 따른 데이터 다운로드 완료

### 1.2 AWS 콘솔 접속 및 확인

1. **AWS 콘솔 로그인**
   - [AWS 콘솔](https://console.aws.amazon.com)에 접속
   - IAM 사용자로 로그인 (루트 계정 사용 지양)

2. **리전 확인**
   - 콘솔 우상단에서 리전이 `아시아 태평양(서울) ap-northeast-2`로 설정되어 있는지 확인
   - 다른 리전으로 설정되어 있다면 서울 리전으로 변경

3. **필수 서비스 접근 확인**
   - S3, AWS Glue, Amazon Athena 서비스에 접근 가능한지 확인
   - 권한 오류가 발생하면 [AWS 설정 가이드](02-aws-setup-guide.md) 재확인

### 1.3 실습 데이터 확인

로컬 컴퓨터에 다운로드한 데이터 파일을 확인합니다:

- [ ] `Students.csv` 파일이 다운로드되어 있음
- [ ] 파일 크기가 적절함 (약 500KB-2MB)
- [ ] Excel이나 텍스트 에디터로 파일이 정상적으로 열림
- [ ] 데이터에 헤더 행이 있음을 확인

---

## 2. S3 데이터 업로드 실습

Amazon S3는 AWS의 객체 스토리지 서비스입니다. 클라우드의 무제한 저장공간이라고 생각하면 됩니다.

### 2.1 S3 버킷 확인 및 폴더 구조 생성

1. **S3 콘솔 접속**
   - AWS 콘솔에서 "S3" 검색 후 클릭
   - 이전에 생성한 버킷 확인 (`workshop-data-[고유번호]`)

2. **폴더 구조 생성**
   - 버킷 클릭하여 진입
   - "폴더 만들기" 버튼 클릭
   - 다음 폴더들을 순서대로 생성:
     ```
     raw-data/
     processed-data/
     athena-results/
     ```

3. **세부 폴더 생성**
   - `raw-data` 폴더 진입
   - "폴더 만들기"로 `ai-tool-usage` 폴더 생성

### 2.2 데이터 파일 업로드

1. **업로드 위치 이동**
   - `raw-data/ai-tool-usage/` 폴더로 이동

2. **파일 업로드**
   - "업로드" 버튼 클릭
   - "파일 추가" 클릭
   - 다운로드한 `Students.csv` 파일 선택
   - "업로드" 버튼 클릭

3. **업로드 확인**
   - 업로드 완료 메시지 확인
   - 파일 목록에서 업로드된 파일 확인
   - 파일 크기와 업로드 시간 확인

### 2.3 업로드 결과 검증

1. **파일 속성 확인**
   - 업로드된 파일 클릭
   - "속성" 탭에서 파일 정보 확인
   - 크기, 업로드 시간, 스토리지 클래스 등 확인

2. **파일 미리보기 (선택사항)**
   - "객체 작업" → "S3 Select로 쿼리" 클릭
   - 입력 설정: CSV, 헤더 있음
   - SQL 쿼리: `SELECT * FROM s3object LIMIT 10`
   - "SQL 쿼리 실행" 클릭하여 데이터 미리보기

---

## 3. Glue 크롤러 실행 실습

AWS Glue 크롤러는 데이터의 구조를 자동으로 파악하여 테이블 스키마를 생성하는 도구입니다.

### 3.1 Glue 데이터베이스 확인

1. **Glue 콘솔 접속**
   - AWS 콘솔에서 "Glue" 검색 후 클릭
   - 좌측 메뉴에서 "데이터베이스" 클릭

2. **데이터베이스 확인**
   - `workshop_database`가 있는지 확인
   - 없다면 "데이터베이스 추가"로 생성

### 3.2 크롤러 생성

1. **크롤러 생성 시작**
   - 좌측 메뉴에서 "크롤러" 클릭
   - "크롤러 생성" 버튼 클릭

2. **크롤러 속성 설정**
   - 이름: `ai-tool-usage-crawler`
   - 설명: `AI 도구 사용 데이터 크롤러`
   - "다음" 클릭

3. **데이터 소스 설정**
   - "데이터 소스 추가" 클릭
   - 데이터 소스: "S3" 선택
   - S3 경로: `s3://workshop-data-[고유번호]/raw-data/ai-tool-usage/`
   - "S3 데이터 소스 추가" 클릭
   - "다음" 클릭

4. **보안 설정**
   - IAM 역할: "기존 IAM 역할 선택"
   - 역할: `GlueWorkshopRole` 선택
   - "다음" 클릭

5. **출력 및 스케줄링**
   - 대상 데이터베이스: `workshop_database` 선택
   - 테이블 이름 접두사: `raw_` (선택사항)
   - 크롤러 일정: "온디맨드" 선택
   - "다음" 클릭

6. **검토 및 생성**
   - 설정 내용 검토
   - "크롤러 생성" 클릭

### 3.3 크롤러 실행

1. **크롤러 실행**
   - 생성된 크롤러 선택
   - "실행" 버튼 클릭

2. **실행 상태 모니터링**
   - 상태가 "시작 중" → "실행 중" → "중지 중" → "준비됨"으로 변경됨을 확인
   - 보통 2-5분 소요

3. **실행 결과 확인**
   - 크롤러 실행 완료 후 "테이블" 메뉴로 이동
   - `workshop_database`에 새로 생성된 테이블 확인
   - 테이블 클릭하여 스키마 정보 확인

### 3.4 생성된 테이블 검증

1. **테이블 스키마 확인**
   - 생성된 테이블 클릭 (예: `raw_students`)
   - "스키마" 탭에서 컬럼 정보 확인
   - 데이터 타입이 올바르게 인식되었는지 확인

2. **예상 스키마 예시**
   ```
   student_name         string
   college_name         string
   stream              string
   year_of_study       bigint
   ai_tools_used       string
   daily_usage_hours   double
   use_cases           string
   trust_in_ai_tools   bigint
   impact_on_grades    bigint
   preferred_ai_tool   string
   state               string
   device_used         string
   ```

---

## 4. ETL 작업 생성 및 실행

ETL(Extract, Transform, Load)은 데이터를 추출하고, 변환하고, 저장하는 과정입니다.

### 4.1 Glue Studio에서 ETL 작업 생성

1. **Glue Studio 접속**
   - Glue 콘솔에서 "ETL 작업" → "시각적 ETL" 클릭
   - "작업 생성" 버튼 클릭
   - "빈 캔버스로 시각적 ETL" 선택
   - "생성" 클릭

2. **작업 기본 설정**
   - 상단 "작업 세부 정보" 탭 클릭
   - 이름: `ai-tool-usage-etl-job`
   - IAM 역할: `GlueWorkshopRole`
   - Glue 버전: `4.0`
   - 언어: `Python 3`

### 4.2 시각적 ETL 파이프라인 구성

#### 4.2.1 Source 노드 추가

1. **데이터 소스 추가**
   - 캔버스에서 "소스" → "AWS Glue Data Catalog" 드래그
   - 노드 선택 후 우측 패널에서 설정:
     - 데이터베이스: `workshop_database`
     - 테이블: 크롤러로 생성된 테이블 선택
   - 노드 이름: `Source - AI Tool Usage`

#### 4.2.2 Transform 노드 추가

1. **데이터 정제**
   - "변환" → "Null 필드 삭제" 드래그
   - Source 노드와 연결
   - 노드 이름: `Remove Null Values`

2. **필드 선택**
   - "변환" → "필드 선택" 드래그
   - 이전 노드와 연결
   - 필요한 컬럼만 선택 (불필요한 개인정보 제외)
   - 노드 이름: `Select Fields`

3. **데이터 타입 변경**
   - "변환" → "스키마 변경" 드래그
   - 이전 노드와 연결
   - 데이터 타입 조정:
     - 숫자 필드들을 적절한 타입으로 변경
     - 문자열 필드 정리
   - 노드 이름: `Change Schema`

#### 4.2.3 Target 노드 추가

1. **저장 대상 설정**
   - "대상" → "Amazon S3" 드래그
   - 마지막 Transform 노드와 연결
   - 설정:
     - 형식: `Parquet`
     - 압축 유형: `Snappy`
     - S3 대상 위치: `s3://workshop-data-[고유번호]/processed-data/ai-tool-usage/`
     - 데이터 카탈로그 업데이트 옵션: "테이블 생성 및 스키마 업데이트"
     - 데이터베이스: `workshop_database`
     - 테이블 이름: `processed_ai_tool_usage`

### 4.3 ETL 작업 실행

1. **작업 저장**
   - 우상단 "저장" 버튼 클릭
   - 파이프라인 구성 확인

2. **작업 실행**
   - "실행" 버튼 클릭
   - 실행 확인 대화상자에서 "작업 실행" 클릭

3. **실행 모니터링**
   - "실행" 탭에서 진행 상황 확인
   - 상태: "시작 중" → "실행 중" → "성공" (보통 5-15분 소요)

### 4.4 ETL 결과 확인

1. **처리된 데이터 확인**
   - S3 콘솔에서 `processed-data/ai-tool-usage/` 폴더 확인
   - Parquet 파일들이 생성되었는지 확인

2. **새 테이블 확인**
   - Glue 콘솔의 "테이블" 메뉴에서 `processed_ai_tool_usage` 테이블 확인
   - 스키마가 올바르게 생성되었는지 확인

---

## 5. Athena 쿼리 실습

Amazon Athena는 S3의 데이터를 SQL로 직접 분석할 수 있는 서비스입니다.

### 5.1 Athena 설정 확인

1. **Athena 콘솔 접속**
   - AWS 콘솔에서 "Athena" 검색 후 클릭

2. **쿼리 결과 위치 확인**
   - "설정" 탭 클릭
   - 쿼리 결과 위치가 설정되어 있는지 확인
   - 없다면 `s3://workshop-data-[고유번호]/athena-results/` 설정

### 5.2 기본 데이터 탐색 쿼리

1. **데이터베이스 선택**
   - 쿼리 편집기에서 데이터베이스 드롭다운에서 `workshop_database` 선택

2. **기본 탐색 쿼리 실행**

   **전체 데이터 개수 확인:**
   ```sql
   SELECT COUNT(*) as total_records
   FROM processed_ai_tool_usage;
   ```

   **데이터 샘플 확인:**
   ```sql
   SELECT *
   FROM processed_ai_tool_usage
   LIMIT 10;
   ```

   **컬럼별 고유값 확인:**
   ```sql
   SELECT 
       COUNT(DISTINCT stream) as unique_streams,
       COUNT(DISTINCT year_of_study) as unique_years,
       COUNT(DISTINCT preferred_ai_tool) as unique_tools
   FROM processed_ai_tool_usage;
   ```

### 5.3 분석 쿼리 실습

#### 5.3.1 전공별 분석

```sql
-- 전공별 학생 수
SELECT 
    stream,
    COUNT(*) as student_count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2) as percentage
FROM processed_ai_tool_usage
GROUP BY stream
ORDER BY student_count DESC;
```

```sql
-- 전공별 평균 AI 도구 신뢰도
SELECT 
    stream,
    COUNT(*) as student_count,
    ROUND(AVG(trust_in_ai_tools), 2) as avg_trust,
    MIN(trust_in_ai_tools) as min_trust,
    MAX(trust_in_ai_tools) as max_trust
FROM processed_ai_tool_usage
GROUP BY stream
HAVING COUNT(*) >= 10
ORDER BY avg_trust DESC;
```

#### 5.3.2 학년별 분석

```sql
-- 학년별 AI 도구 사용 패턴
SELECT 
    year_of_study,
    COUNT(*) as total_students,
    ROUND(AVG(daily_usage_hours), 2) as avg_daily_hours,
    ROUND(AVG(trust_in_ai_tools), 2) as avg_trust,
    ROUND(AVG(impact_on_grades), 2) as avg_grade_impact
FROM processed_ai_tool_usage
GROUP BY year_of_study
ORDER BY year_of_study;
```

#### 5.3.3 AI 도구별 분석

```sql
-- 선호 AI 도구별 사용자 특성
SELECT 
    preferred_ai_tool,
    COUNT(*) as user_count,
    ROUND(AVG(daily_usage_hours), 2) as avg_daily_hours,
    ROUND(AVG(trust_in_ai_tools), 2) as avg_trust,
    ROUND(AVG(impact_on_grades), 2) as avg_grade_impact
FROM processed_ai_tool_usage
WHERE preferred_ai_tool IS NOT NULL
GROUP BY preferred_ai_tool
HAVING COUNT(*) >= 5
ORDER BY user_count DESC;
```

#### 5.3.4 고급 분석 쿼리

```sql
-- 전공별, 학년별 교차 분석
SELECT 
    stream,
    year_of_study,
    COUNT(*) as student_count,
    ROUND(AVG(trust_in_ai_tools), 2) as avg_trust,
    ROUND(AVG(daily_usage_hours), 2) as avg_hours
FROM processed_ai_tool_usage
GROUP BY stream, year_of_study
HAVING COUNT(*) >= 3
ORDER BY stream, year_of_study;
```

```sql
-- 사용 시간대별 신뢰도 분석
SELECT 
    CASE 
        WHEN daily_usage_hours < 1 THEN 'Light User (< 1h)'
        WHEN daily_usage_hours < 3 THEN 'Moderate User (1-3h)'
        WHEN daily_usage_hours < 5 THEN 'Heavy User (3-5h)'
        ELSE 'Very Heavy User (5h+)'
    END as usage_category,
    COUNT(*) as user_count,
    ROUND(AVG(trust_in_ai_tools), 2) as avg_trust,
    ROUND(AVG(impact_on_grades), 2) as avg_grade_impact
FROM processed_ai_tool_usage
WHERE daily_usage_hours IS NOT NULL
GROUP BY 
    CASE 
        WHEN daily_usage_hours < 1 THEN 'Light User (< 1h)'
        WHEN daily_usage_hours < 3 THEN 'Moderate User (1-3h)'
        WHEN daily_usage_hours < 5 THEN 'Heavy User (3-5h)'
        ELSE 'Very Heavy User (5h+)'
    END
ORDER BY avg_trust DESC;
```

### 5.4 쿼리 결과 저장

1. **결과 다운로드**
   - 쿼리 실행 후 "결과 다운로드" 버튼 클릭
   - CSV 파일로 로컬에 저장

2. **S3에서 결과 확인**
   - S3의 `athena-results` 폴더에서 쿼리 결과 파일 확인

---

## 6. 실습 검증 체크포인트

### 6.1 전체 파이프라인 검증

다음 항목들이 모두 완료되었는지 확인하세요:

#### 데이터 업로드 단계
- [ ] S3 버킷에 원본 데이터가 업로드됨
- [ ] 폴더 구조가 체계적으로 구성됨
- [ ] 파일이 정상적으로 업로드되고 접근 가능함

#### 스키마 발견 단계
- [ ] Glue 크롤러가 성공적으로 실행됨
- [ ] Data Catalog에 테이블이 생성됨
- [ ] 테이블 스키마가 올바르게 인식됨

#### 데이터 변환 단계
- [ ] ETL 작업이 성공적으로 실행됨
- [ ] 처리된 데이터가 Parquet 형식으로 저장됨
- [ ] 새로운 테이블이 Data Catalog에 생성됨

#### 데이터 분석 단계
- [ ] Athena에서 기본 쿼리가 실행됨
- [ ] 집계 분석이 의미있는 결과를 반환함
- [ ] 복잡한 분석 쿼리가 정상 작동함

### 6.2 예상 결과 확인

#### 데이터 규모
- 원본 데이터: 약 3,000개 레코드
- 처리된 데이터: 정제 후 2,500-2,800개 레코드 예상
- 쿼리 응답 시간: 대부분 10초 이내

#### 주요 인사이트 예시
- 가장 많은 전공: Engineering 계열
- 평균 일일 사용 시간: 2-4시간
- 가장 선호하는 AI 도구: ChatGPT
- 학년별 사용 패턴: 고학년일수록 사용 시간 증가 경향

### 6.3 문제 해결

일반적인 문제와 해결 방법:

**크롤러 실행 실패:**
- IAM 역할 권한 확인
- S3 경로가 정확한지 확인
- 데이터 파일 형식 확인

**ETL 작업 실패:**
- 소스 테이블이 존재하는지 확인
- 대상 S3 경로 권한 확인
- 데이터 타입 변환 오류 확인

**Athena 쿼리 오류:**
- 테이블명과 컬럼명 확인
- 데이터 타입 불일치 확인
- 쿼리 결과 저장 위치 설정 확인

### 6.4 성공 기준

다음 조건들이 모두 충족되면 워크샵이 성공적으로 완료된 것입니다:

- [ ] 전체 파이프라인이 오류 없이 실행됨
- [ ] 각 단계의 결과물이 예상대로 생성됨
- [ ] Athena에서 다양한 분석 쿼리가 실행됨
- [ ] 의미있는 데이터 인사이트를 도출함
- [ ] 전체 과정을 이해하고 설명할 수 있음

## 7. 다음 단계

워크샵을 성공적으로 완료했다면:

1. **심화 학습**: [고급 예제 가이드](05-advanced-examples.md)로 더 복잡한 분석 시도
2. **다른 데이터셋**: 새로운 데이터셋으로 동일한 파이프라인 구축
3. **시각화**: Amazon QuickSight를 사용한 대시보드 생성
4. **자동화**: 스케줄링을 통한 정기적 데이터 처리 설정

## 8. 리소스 정리

워크샵 완료 후 비용 절약을 위해 다음 리소스들을 정리하세요:

1. **S3 버킷**: 불필요한 파일 삭제
2. **Glue 작업**: 사용하지 않는 ETL 작업 삭제
3. **Athena**: 쿼리 결과 파일 정리
4. **IAM**: 임시로 생성한 역할이나 사용자 정리

---

**축하합니다! 🎉**

AWS 데이터 분석 파이프라인 워크샵을 성공적으로 완료하셨습니다. 이제 클라우드 기반 데이터 분석의 전체 과정을 이해하고 실무에 적용할 수 있는 기초를 갖추셨습니다.