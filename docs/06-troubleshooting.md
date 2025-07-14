# 문제 해결 가이드

AWS 데이터 분석 워크샵을 진행하면서 발생할 수 있는 일반적인 문제들과 해결 방법을 정리했습니다. 문제가 발생했을 때 이 가이드를 참고하여 단계별로 해결해보세요.

## 목차
- [AWS 계정 및 권한 관련 문제](#aws-계정-및-권한-관련-문제)
- [S3 관련 문제](#s3-관련-문제)
- [Glue 관련 문제](#glue-관련-문제)
- [Athena 관련 문제](#athena-관련-문제)
- [네트워크 및 연결 문제](#네트워크-및-연결-문제)
- [데이터 관련 문제](#데이터-관련-문제)
- [권한 문제 해결 체크리스트](#권한-문제-해결-체크리스트)

---

## AWS 계정 및 권한 관련 문제

### 문제: "Access Denied" 오류가 발생합니다

**증상:**
```
AccessDenied: User: arn:aws:iam::123456789012:user/username is not authorized to perform: s3:GetObject
```

**해결 방법:**
1. **IAM 정책 확인**
   ```bash
   # 현재 사용자 정보 확인
   aws sts get-caller-identity
   
   # 사용자에게 연결된 정책 확인
   aws iam list-attached-user-policies --user-name YOUR_USERNAME
   ```

2. **필요한 권한 추가**
   - S3 작업을 위한 최소 권한:
     ```json
     {
         "Version": "2012-10-17",
         "Statement": [
             {
                 "Effect": "Allow",
                 "Action": [
                     "s3:GetObject",
                     "s3:PutObject",
                     "s3:DeleteObject",
                     "s3:ListBucket"
                 ],
                 "Resource": [
                     "arn:aws:s3:::your-workshop-bucket",
                     "arn:aws:s3:::your-workshop-bucket/*"
                 ]
             }
         ]
     }
     ```

3. **정책 적용 확인**
   - IAM 콘솔에서 정책이 올바르게 적용되었는지 확인
   - 정책 변경 후 5-10분 정도 기다린 후 재시도

### 문제: AWS CLI 인증이 되지 않습니다

**증상:**
```
Unable to locate credentials. You can configure credentials by running "aws configure".
```

**해결 방법:**
1. **AWS CLI 설정 확인**
   ```bash
   aws configure list
   ```

2. **자격 증명 재설정**
   ```bash
   aws configure
   # Access Key ID, Secret Access Key, Region, Output format 입력
   ```

3. **환경 변수 확인**
   ```bash
   echo $AWS_ACCESS_KEY_ID
   echo $AWS_SECRET_ACCESS_KEY
   echo $AWS_DEFAULT_REGION
   ```

---

## S3 관련 문제

### 문제: S3 버킷에 파일 업로드가 실패합니다

**증상:**
- 업로드 중 연결이 끊어짐
- "NoSuchBucket" 오류
- 파일 크기 제한 오류

**해결 방법:**

1. **버킷 존재 확인**
   ```bash
   aws s3 ls s3://your-workshop-bucket/
   ```

2. **대용량 파일 업로드**
   ```bash
   # 멀티파트 업로드 사용
   aws s3 cp large-file.csv s3://your-workshop-bucket/ --storage-class STANDARD_IA
   ```

3. **네트워크 문제 해결**
   ```bash
   # 재시도 설정으로 업로드
   aws configure set max_attempts 10
   aws configure set retry_mode adaptive
   ```

### 문제: S3 버킷 정책 설정 오류

**증상:**
```
MalformedPolicy: Policy has invalid resource
```

**해결 방법:**
1. **버킷 정책 JSON 검증**
   - AWS Policy Generator 사용: https://awspolicygen.s3.amazonaws.com/policygen.html
   - JSON 문법 검사기로 확인

2. **올바른 버킷 정책 예시**
   ```json
   {
       "Version": "2012-10-17",
       "Statement": [
           {
               "Sid": "AllowWorkshopAccess",
               "Effect": "Allow",
               "Principal": {
                   "AWS": "arn:aws:iam::YOUR-ACCOUNT-ID:user/YOUR-USERNAME"
               },
               "Action": [
                   "s3:GetObject",
                   "s3:PutObject"
               ],
               "Resource": "arn:aws:s3:::your-workshop-bucket/*"
           }
       ]
   }
   ```

---

## Glue 관련 문제

### 문제: Glue 크롤러가 실행되지 않습니다

**증상:**
- 크롤러 상태가 "READY"에서 변하지 않음
- "FAILED" 상태로 변경됨

**해결 방법:**

1. **크롤러 상태 확인**
   ```bash
   aws glue get-crawler --name your-crawler-name
   ```

2. **IAM 역할 확인**
   - Glue 서비스 역할에 다음 정책이 연결되어 있는지 확인:
     - `AWSGlueServiceRole`
     - S3 버킷 접근 권한

3. **크롤러 설정 재확인**
   - 데이터 저장소 경로가 올바른지 확인
   - 출력 데이터베이스가 존재하는지 확인

### 문제: Glue ETL 작업이 실패합니다

**증상:**
```
Job run failed with error: java.lang.OutOfMemoryError
```

**해결 방법:**

1. **DPU(Data Processing Unit) 증가**
   ```python
   # Glue 작업 설정에서 DPU 수 증가
   job_config = {
       'AllocatedCapacity': 10,  # 기본값 2에서 증가
       'MaxCapacity': 10
   }
   ```

2. **메모리 최적화**
   ```python
   # 파티션 수 조정
   df.coalesce(1).write.mode("overwrite").parquet("s3://bucket/path/")
   ```

3. **로그 확인**
   ```bash
   # CloudWatch 로그에서 상세 오류 확인
   aws logs describe-log-groups --log-group-name-prefix "/aws-glue"
   ```

### 문제: Glue Studio에서 시각적 편집기가 로드되지 않습니다

**해결 방법:**
1. **브라우저 캐시 삭제**
   - Ctrl+Shift+Delete (Windows/Linux)
   - Cmd+Shift+Delete (Mac)

2. **브라우저 호환성 확인**
   - Chrome, Firefox, Safari 최신 버전 사용 권장
   - 팝업 차단 해제

3. **네트워크 설정 확인**
   - 회사 방화벽이나 프록시 설정 확인
   - AWS 콘솔 접근 허용 확인

---

## Athena 관련 문제

### 문제: Athena 쿼리가 실행되지 않습니다

**증상:**
```
FAILED: SemanticException table not found
```

**해결 방법:**

1. **테이블 존재 확인**
   ```sql
   SHOW TABLES IN your_database;
   DESCRIBE your_table_name;
   ```

2. **데이터베이스 선택 확인**
   ```sql
   USE your_database;
   SELECT * FROM your_table LIMIT 10;
   ```

3. **쿼리 결과 위치 설정**
   - Athena 설정에서 쿼리 결과 위치가 올바르게 설정되어 있는지 확인
   - `s3://your-athena-results-bucket/` 형태로 설정

### 문제: Athena 쿼리 성능이 느립니다

**해결 방법:**

1. **파티셔닝 활용**
   ```sql
   -- 파티션된 테이블 쿼리 시 파티션 조건 추가
   SELECT * FROM your_table 
   WHERE year = '2025' AND month = '01';
   ```

2. **데이터 형식 최적화**
   - CSV 대신 Parquet 형식 사용
   - 압축 옵션 활용 (GZIP, Snappy)

3. **쿼리 최적화**
   ```sql
   -- 필요한 컬럼만 선택
   SELECT column1, column2 FROM table
   WHERE condition
   LIMIT 1000;
   ```

---

## 네트워크 및 연결 문제

### 문제: AWS 서비스 연결이 자주 끊어집니다

**해결 방법:**

1. **네트워크 연결 상태 확인**
   ```bash
   # AWS 서비스 연결 테스트
   ping s3.amazonaws.com
   nslookup glue.us-east-1.amazonaws.com
   ```

2. **프록시 설정 확인**
   ```bash
   # 프록시 환경에서 AWS CLI 설정
   aws configure set proxy_url http://proxy.company.com:8080
   ```

3. **타임아웃 설정 조정**
   ```bash
   aws configure set cli_read_timeout 0
   aws configure set cli_connect_timeout 60
   ```

### 문제: 특정 지역(Region)에서 서비스 접근이 안됩니다

**해결 방법:**
1. **지역 가용성 확인**
   - AWS 서비스별 지역 가용성 페이지 확인
   - 일부 서비스는 특정 지역에서만 제공

2. **지역 설정 변경**
   ```bash
   aws configure set region us-east-1
   ```

---

## 데이터 관련 문제

### 문제: 데이터 형식 오류로 처리가 실패합니다

**증상:**
- 날짜 형식 불일치
- 인코딩 문제 (한글 깨짐)
- CSV 파싱 오류

**해결 방법:**

1. **데이터 형식 표준화**
   ```python
   # 날짜 형식 통일
   df['date_column'] = pd.to_datetime(df['date_column'], format='%Y-%m-%d')
   
   # 인코딩 확인 및 변경
   df = pd.read_csv('file.csv', encoding='utf-8')
   ```

2. **CSV 파싱 옵션 조정**
   ```python
   # 구분자 및 인용 문자 설정
   df = pd.read_csv('file.csv', sep=',', quotechar='"', escapechar='\\')
   ```

### 문제: 대용량 데이터 처리 시 메모리 부족

**해결 방법:**
1. **청크 단위 처리**
   ```python
   # 대용량 파일을 청크로 나누어 처리
   chunk_size = 10000
   for chunk in pd.read_csv('large_file.csv', chunksize=chunk_size):
       process_chunk(chunk)
   ```

2. **데이터 샘플링**
   ```python
   # 전체 데이터의 일부만 사용
   sample_df = df.sample(frac=0.1)  # 10% 샘플링
   ```

---

## 권한 문제 해결 체크리스트

문제가 발생했을 때 다음 체크리스트를 순서대로 확인해보세요:

### ✅ 기본 설정 확인
- [ ] AWS CLI가 올바르게 설치되어 있는가?
- [ ] `aws configure`로 자격 증명이 설정되어 있는가?
- [ ] 올바른 AWS 리전이 설정되어 있는가?
- [ ] 인터넷 연결이 안정적인가?

### ✅ IAM 권한 확인
- [ ] 사용자 계정이 활성화되어 있는가?
- [ ] 필요한 IAM 정책이 연결되어 있는가?
- [ ] MFA(다중 인증)가 필요한 경우 설정되어 있는가?
- [ ] 임시 자격 증명이 만료되지 않았는가?

### ✅ 서비스별 권한 확인

**S3 권한:**
- [ ] `s3:ListBucket` 권한이 있는가?
- [ ] `s3:GetObject`, `s3:PutObject` 권한이 있는가?
- [ ] 버킷 정책이 올바르게 설정되어 있는가?

**Glue 권한:**
- [ ] `glue:*` 권한 또는 필요한 Glue 작업 권한이 있는가?
- [ ] Glue 서비스 역할이 생성되어 있는가?
- [ ] Glue 역할에 S3 접근 권한이 있는가?

**Athena 권한:**
- [ ] `athena:*` 권한이 있는가?
- [ ] 쿼리 결과 저장을 위한 S3 권한이 있는가?
- [ ] Glue Data Catalog 접근 권한이 있는가?

### ✅ 리소스 확인
- [ ] S3 버킷이 존재하고 올바른 이름인가?
- [ ] Glue 데이터베이스와 테이블이 생성되어 있는가?
- [ ] 데이터 파일이 올바른 위치에 있는가?
- [ ] 파일 형식과 스키마가 올바른가?

### ✅ 네트워크 및 보안
- [ ] 회사 방화벽이나 프록시가 AWS 접근을 차단하지 않는가?
- [ ] VPC 설정이 올바른가? (해당하는 경우)
- [ ] 보안 그룹 규칙이 적절한가? (해당하는 경우)

---

## 추가 도움이 필요한 경우

### AWS 공식 문서
- [AWS Glue 문제 해결](https://docs.aws.amazon.com/glue/latest/dg/troubleshooting.html)
- [Amazon S3 문제 해결](https://docs.aws.amazon.com/AmazonS3/latest/userguide/troubleshooting.html)
- [Amazon Athena 문제 해결](https://docs.aws.amazon.com/athena/latest/ug/troubleshooting-athena.html)

### 커뮤니티 지원
- [AWS re:Post](https://repost.aws/) - AWS 공식 커뮤니티
- [Stack Overflow AWS 태그](https://stackoverflow.com/questions/tagged/amazon-web-services)

### 로그 및 모니터링
- **CloudWatch 로그**: 상세한 오류 로그 확인
- **CloudTrail**: API 호출 기록 확인
- **AWS Personal Health Dashboard**: 서비스 상태 확인

문제가 지속되면 위의 체크리스트를 모두 확인한 후, 구체적인 오류 메시지와 함께 도움을 요청하세요.
---


## 자주 묻는 질문 (FAQ)

### 💰 비용 관련 질문

#### Q: 이 워크샵을 진행하는데 얼마나 비용이 들까요?
**A:** 일반적으로 워크샵 전체를 완료하는데 **$3-5** 정도의 비용이 발생합니다.

**비용 구성:**
- **S3 스토리지**: $0.50-1.00 (1GB 데이터 기준)
- **Glue 크롤러**: $0.44/시간 (보통 5-10분 소요)
- **Glue ETL 작업**: $0.44/DPU/시간 (2 DPU × 10분 = 약 $0.15)
- **Athena 쿼리**: $5/TB 스캔 (100MB 스캔 시 약 $0.0005)

**비용 절약 팁:**
- 실습 완료 후 즉시 리소스 삭제
- S3 버킷의 모든 객체 삭제
- Glue 크롤러와 ETL 작업 삭제

#### Q: 실습 후 비용이 계속 발생하지 않으려면 어떻게 해야 하나요?
**A:** 다음 리소스들을 반드시 삭제하세요:

```bash
# S3 버킷 내용 삭제
aws s3 rm s3://your-workshop-bucket --recursive

# S3 버킷 삭제
aws s3 rb s3://your-workshop-bucket

# Glue 크롤러 삭제
aws glue delete-crawler --name your-crawler-name

# Glue ETL 작업 삭제
aws glue delete-job --job-name your-job-name

# Glue 데이터베이스 삭제 (선택사항)
aws glue delete-database --name your-database-name
```

#### Q: AWS 프리 티어로 이 워크샵을 진행할 수 있나요?
**A:** 부분적으로 가능합니다:
- **S3**: 프리 티어에서 5GB까지 무료
- **Glue**: 프리 티어 없음 (유료 서비스)
- **Athena**: 프리 티어 없음, 하지만 소량 데이터로 비용 최소화 가능

**권장사항:** 프리 티어 계정이라도 $5-10 정도의 예산을 준비하세요.

### 🎓 학습 관련 질문

#### Q: 이 워크샵을 완료하는데 얼마나 시간이 걸리나요?
**A:** 경험 수준에 따라 다릅니다:
- **초보자**: 4-6시간 (설정 포함)
- **중급자**: 2-3시간
- **고급자**: 1-2시간

**시간 배분:**
- AWS 계정 설정: 30분
- 기본 실습: 2-3시간
- 심화 예제: 1-2시간
- 문제 해결: 30분-1시간

#### Q: 사전에 알아야 할 지식이 있나요?
**A:** 다음 지식이 있으면 도움이 됩니다:
- **필수**: 기본적인 컴퓨터 사용법
- **권장**: SQL 기초 지식
- **선택**: Python 기초 (심화 예제용)
- **선택**: 클라우드 컴퓨팅 개념

#### Q: 프로그래밍 경험이 없어도 따라할 수 있나요?
**A:** 네, 가능합니다! 
- 대부분의 작업은 AWS 웹 콘솔에서 클릭으로 진행
- 코드 복사-붙여넣기로 충분
- 단계별 스크린샷 제공
- 하지만 SQL 기초는 미리 학습하는 것을 권장

#### Q: 어떤 운영체제에서 실습할 수 있나요?
**A:** 모든 주요 운영체제에서 가능합니다:
- **Windows 10/11**: AWS CLI 설치 필요
- **macOS**: 터미널에서 AWS CLI 설치
- **Linux**: 패키지 매니저로 AWS CLI 설치
- **웹 브라우저만으로도 대부분 실습 가능**

### 🔧 기술적 질문

#### Q: AWS CLI 없이도 실습할 수 있나요?
**A:** 네, 대부분 가능합니다:
- **AWS 웹 콘솔**로 모든 기본 작업 수행 가능
- **Glue Studio**의 시각적 인터페이스 활용
- **Athena 웹 인터페이스**에서 쿼리 실행
- CLI는 자동화와 고급 작업에만 필요

#### Q: 회사 네트워크에서 실습할 때 주의사항이 있나요?
**A:** 다음 사항을 확인하세요:
- **방화벽 설정**: AWS 도메인 접근 허용 필요
- **프록시 설정**: AWS CLI에 프록시 설정 필요할 수 있음
- **포트 제한**: HTTPS(443) 포트 접근 필요
- **IT 부서 승인**: 회사 정책에 따라 사전 승인 필요할 수 있음

#### Q: 실습 중 데이터가 손실될 위험이 있나요?
**A:** 실습용 데이터이므로 안전합니다:
- **공개 데이터셋** 사용으로 개인정보 없음
- **별도 S3 버킷** 생성으로 기존 데이터와 분리
- **실습 전용 IAM 권한**으로 다른 리소스 접근 제한
- 만약을 위해 **중요한 AWS 계정과 분리** 권장

#### Q: 다른 AWS 리전에서도 실습할 수 있나요?
**A:** 네, 가능합니다:
- **권장 리전**: us-east-1 (버지니아 북부)
- **대안 리전**: us-west-2, eu-west-1, ap-northeast-2
- **주의사항**: 일부 서비스는 특정 리전에서만 제공
- **비용 차이**: 리전별로 약간의 가격 차이 있음

### 📚 추가 학습 질문

#### Q: 이 워크샵 후에 어떤 것을 더 학습하면 좋을까요?
**A:** 다음 주제들을 추천합니다:

**데이터 엔지니어링 심화:**
- Apache Spark와 EMR
- AWS Lambda를 활용한 서버리스 ETL
- Apache Airflow로 워크플로우 관리
- dbt(data build tool)로 데이터 변환

**데이터 분석 도구:**
- Amazon QuickSight로 시각화
- Jupyter Notebook과 SageMaker
- Tableau, Power BI 연동
- Python pandas, numpy 라이브러리

**클라우드 아키텍처:**
- AWS Well-Architected Framework
- 데이터 레이크 아키텍처 설계
- 실시간 스트리밍 (Kinesis)
- 데이터 거버넌스와 보안

#### Q: 실무에서 이 기술들을 어떻게 활용할 수 있나요?
**A:** 다양한 분야에서 활용 가능합니다:

**비즈니스 분석:**
- 고객 행동 분석
- 매출 트렌드 분석
- 마케팅 캠페인 효과 측정

**운영 최적화:**
- 재고 관리 최적화
- 공급망 분석
- 품질 관리 데이터 분석

**연구 및 개발:**
- 실험 데이터 분석
- A/B 테스트 결과 분석
- 제품 사용 패턴 분석

#### Q: 관련 자격증이 있나요?
**A:** AWS 데이터 관련 자격증들:
- **AWS Certified Cloud Practitioner** (입문)
- **AWS Certified Data Analytics - Specialty** (전문)
- **AWS Certified Solutions Architect** (아키텍처)
- **AWS Certified Machine Learning - Specialty** (ML)

### 🤝 지원 및 커뮤니티

#### Q: 실습 중 막히면 어디서 도움을 받을 수 있나요?
**A:** 여러 지원 채널이 있습니다:

**무료 지원:**
- [AWS re:Post](https://repost.aws/) - AWS 공식 커뮤니티
- [Stack Overflow](https://stackoverflow.com/questions/tagged/amazon-web-services)
- [AWS 문서](https://docs.aws.amazon.com/)
- GitHub Issues (이 워크샵 저장소)

**유료 지원:**
- AWS Support Plans (Developer, Business, Enterprise)
- AWS Professional Services

**학습 커뮤니티:**
- AWS User Groups (지역별)
- LinkedIn AWS 그룹
- Reddit r/aws 커뮤니티

#### Q: 이 워크샵 자료를 수업이나 교육에 사용해도 되나요?
**A:** 네, 자유롭게 사용하세요:
- **오픈소스 라이선스**로 제공
- **교육 목적 사용 권장**
- **상업적 사용도 허용**
- **출처 표기 권장** (필수 아님)
- **개선사항 기여 환영**

#### Q: 워크샵 자료에 오류를 발견했을 때는 어떻게 하나요?
**A:** 다음 방법으로 신고해주세요:
- **GitHub Issues** 생성 (권장)
- **Pull Request** 제출
- **이메일 문의**
- **구체적인 오류 내용과 재현 방법** 포함

---

## 추가 학습 리소스

### 📖 공식 문서
- [AWS Glue Developer Guide](https://docs.aws.amazon.com/glue/latest/dg/)
- [Amazon S3 User Guide](https://docs.aws.amazon.com/AmazonS3/latest/userguide/)
- [Amazon Athena User Guide](https://docs.aws.amazon.com/athena/latest/ug/)
- [AWS CLI User Guide](https://docs.aws.amazon.com/cli/latest/userguide/)

### 🎥 동영상 강의
- [AWS Training and Certification](https://aws.amazon.com/training/)
- [AWS YouTube Channel](https://www.youtube.com/user/AmazonWebServices)
- [AWS re:Invent 세션](https://reinvent.awsevents.com/)

### 📚 추천 도서
- "Learning AWS" by Aurobindo Sarkar
- "AWS Certified Data Analytics Study Guide" by Kareem Sherif
- "Data Engineering with AWS" by Gareth Eagar

### 🛠️ 실습 플랫폼
- [AWS Hands-on Tutorials](https://aws.amazon.com/getting-started/hands-on/)
- [AWS Workshops](https://workshops.aws/)
- [Qwiklabs AWS Quests](https://www.qwiklabs.com/catalog?keywords=aws)

### 💼 커리어 정보
- [AWS Jobs Portal](https://aws.amazon.com/careers/)
- [Data Engineer 로드맵](https://roadmap.sh/data-engineer)
- [AWS 자격증 가이드](https://aws.amazon.com/certification/)

---

*이 FAQ는 지속적으로 업데이트됩니다. 추가 질문이나 개선사항이 있으면 언제든 제안해주세요!*