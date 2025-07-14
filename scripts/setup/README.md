# AWS 워크샵 트러블슈팅 도구

이 디렉토리에는 AWS 데이터 분석 워크샵의 문제를 자동으로 진단하고 해결하는 도구들이 포함되어 있습니다.

## 📋 포함된 도구

### 1. 종합 진단 도구 (`diagnose_issues.py`)
워크샵 환경의 전반적인 문제를 자동으로 진단합니다.

**기능:**
- 시스템 요구사항 확인 (Python, AWS CLI)
- AWS 자격 증명 검증
- 네트워크 연결 상태 확인
- 서비스 권한 검증
- 일반적인 설정 문제 탐지
- 자동 수정 스크립트 생성

**사용법:**
```bash
# 기본 진단
python3 diagnose_issues.py

# 특정 S3 버킷 포함 진단
python3 diagnose_issues.py --bucket my-workshop-bucket

# 자동 수정 스크립트 생성
python3 diagnose_issues.py --bucket my-workshop-bucket --fix

# 결과를 JSON 파일로 저장
python3 diagnose_issues.py --output diagnosis.json
```

### 2. AWS 설정 검증 도구 (`validate_aws_config.py`)
AWS 계정 설정과 권한을 상세히 검증합니다.

**기능:**
- AWS 자격 증명 유효성 확인
- 서비스별 권한 검증 (S3, Glue, Athena)
- IAM 역할 및 정책 확인
- 리전별 서비스 가용성 확인

**사용법:**
```bash
# 기본 검증
python3 validate_aws_config.py

# 특정 버킷과 IAM 역할 검증
python3 validate_aws_config.py --bucket my-bucket --glue-role MyGlueRole

# 다른 AWS 프로필 사용
python3 validate_aws_config.py --profile workshop-user

# 결과를 JSON으로 저장
python3 validate_aws_config.py --output validation.json
```

### 3. 파이프라인 상태 확인 도구 (`check_pipeline_status.py`)
데이터 파이프라인의 현재 상태를 모니터링합니다.

**기능:**
- S3 버킷 및 데이터 현황 확인
- Glue 크롤러 및 ETL 작업 상태 모니터링
- Athena 쿼리 실행 기록 분석
- 파이프라인 전체 건강도 평가

**사용법:**
```bash
# 파이프라인 상태 확인 (S3 버킷 필수)
python3 check_pipeline_status.py --bucket my-workshop-bucket

# 특정 데이터베이스 포함 확인
python3 check_pipeline_status.py --bucket my-bucket --database my-database

# 요약 결과만 출력
python3 check_pipeline_status.py --bucket my-bucket --quiet
```

### 4. 통합 실행 스크립트 (`workshop_diagnostics.sh`)
모든 진단 도구를 쉽게 실행할 수 있는 셸 스크립트입니다.

**기능:**
- 의존성 자동 확인 및 설치
- 빠른 확인 모드
- 전체 진단 실행
- 사용자 친화적인 인터페이스

**사용법:**
```bash
# Linux/macOS에서 실행 권한 부여
chmod +x workshop_diagnostics.sh

# 전체 진단 실행
./workshop_diagnostics.sh --bucket my-workshop-bucket

# 빠른 확인 모드
./workshop_diagnostics.sh --quick

# 자동 수정 스크립트 생성
./workshop_diagnostics.sh --bucket my-bucket --fix
```

**Windows에서 실행:**
```cmd
bash workshop_diagnostics.sh --bucket my-workshop-bucket
```

## 🚀 빠른 시작

### 1단계: 의존성 설치
```bash
pip3 install boto3 botocore tabulate
```

### 2단계: AWS 자격 증명 설정
```bash
aws configure
```

### 3단계: 진단 실행
```bash
# 종합 진단
python3 diagnose_issues.py --bucket your-workshop-bucket

# 또는 통합 스크립트 사용
./workshop_diagnostics.sh --bucket your-workshop-bucket
```

## 📊 출력 예시

### 성공적인 진단 결과
```
🔍 AWS 워크샵 문제 진단 보고서
============================================================
📅 진단 시간: 2025-01-15 14:30:00

✅ 문제가 발견되지 않았습니다!
```

### 문제가 발견된 경우
```
🔍 AWS 워크샵 문제 진단 보고서
============================================================
📅 진단 시간: 2025-01-15 14:30:00

📊 발견된 문제: 3개
   🔴 심각: 1개
   🟠 높음: 1개
   🟡 보통: 1개
   🟢 낮음: 0개

🔴 CRITICAL 문제:
   • AWS 자격 증명이 설정되지 않았습니다
     💡 해결방법: aws configure 명령으로 Access Key와 Secret Key를 설정하세요.

🟠 HIGH 문제:
   • S3 서비스 접근 권한이 없습니다
     💡 해결방법: IAM 정책에 S3 권한을 추가하세요.
```

## 🔧 일반적인 문제 해결

### AWS CLI 설치 문제
```bash
# macOS (Homebrew)
brew install awscli

# Ubuntu/Debian
sudo apt-get install awscli

# Windows
# AWS CLI 설치 프로그램 다운로드: https://aws.amazon.com/cli/
```

### Python 패키지 설치 문제
```bash
# pip 업그레이드
pip3 install --upgrade pip

# 필수 패키지 설치
pip3 install boto3 botocore tabulate

# 권한 문제 시
pip3 install --user boto3 botocore tabulate
```

### 자격 증명 문제
```bash
# AWS 자격 증명 설정
aws configure

# 설정 확인
aws configure list

# 자격 증명 테스트
aws sts get-caller-identity
```

## 📝 로그 및 디버깅

### 상세 로그 활성화
```bash
# AWS CLI 디버그 모드
aws --debug s3 ls

# Python 스크립트 디버그
python3 -v diagnose_issues.py --bucket my-bucket
```

### 일반적인 오류 코드
- **NoCredentialsError**: AWS 자격 증명 미설정
- **AccessDenied**: 권한 부족
- **NoSuchBucket**: 버킷이 존재하지 않음
- **InvalidUserID.NotFound**: 잘못된 자격 증명

## 🆘 추가 도움

문제가 지속되면 다음 리소스를 참조하세요:

1. **워크샵 문제 해결 가이드**: `docs/06-troubleshooting.md`
2. **AWS 공식 문서**: https://docs.aws.amazon.com/
3. **AWS re:Post 커뮤니티**: https://repost.aws/
4. **GitHub Issues**: 이 저장소의 Issues 섹션

## 🔄 업데이트

이 도구들은 지속적으로 개선되고 있습니다. 최신 버전을 사용하려면:

```bash
git pull origin main
```

---

**참고**: 이 도구들은 진단 목적으로만 사용되며, 실제 AWS 리소스를 수정하지 않습니다. 자동 생성된 수정 스크립트는 실행 전에 반드시 검토하세요.