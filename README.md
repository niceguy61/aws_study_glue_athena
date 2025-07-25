# AWS 데이터 분석 워크샵

대학생을 위한 AWS 기반 데이터 분석 파이프라인 실습 워크샵입니다. 이 워크샵을 통해 현대적인 클라우드 환경에서 데이터를 수집, 변환, 분석하는 전체 과정을 학습할 수 있습니다.

## 🎯 워크샵 개요

이 워크샵은 AWS의 핵심 데이터 분석 서비스들을 활용하여 실제 데이터셋으로 완전한 ETL(Extract, Transform, Load) 파이프라인을 구축하는 실습 중심의 교육 프로그램입니다.

### 학습 목표
- AWS 기반 데이터 분석 파이프라인의 전체적인 이해
- S3 → Glue/Glue Studio → Athena로 이어지는 ETL 프로세스 실습
- 실제 공개 데이터셋을 활용한 데이터 분석 경험
- 현업에서 사용되는 데이터 분석 도구와 방법론 학습

### 사용 AWS 서비스
- **Amazon S3**: 데이터 저장소
- **AWS Glue**: ETL 서비스 및 데이터 카탈로그
- **AWS Glue Studio**: 시각적 ETL 파이프라인 구성 도구
- **Amazon Athena**: 서버리스 쿼리 서비스

## 📚 목차

### 1. [데이터 분석 개요](docs/01-introduction.md)
- 데이터 분석의 실무 활용 분야
- 현업 데이터 분석가의 페인 포인트
- ETL의 필요성과 중요성
- AWS 데이터 분석 솔루션의 장점

### 2. [AWS 서비스 설정 가이드](docs/02-aws-setup-guide.md)
- AWS 계정 설정 및 기본 보안 설정
- IAM 역할 및 정책 생성
- S3 버킷 생성 및 구성
- Glue 서비스 설정
- Athena 설정

### 3. [데이터셋 가이드](docs/03-dataset-guide.md)
- 공개 데이터 저장소 소개 (Kaggle, Hugging Face)
- 추천 데이터셋 목록
- 데이터 다운로드 및 전처리 방법

### 4. [기본 실습 워크샵](docs/04-basic-workshop.md)
- 전체 파이프라인 실습
- S3 데이터 업로드
- Glue 크롤러 실행
- ETL 작업 생성 및 실행
- Athena 쿼리 실습

### 5. [심화 예제](docs/05-advanced-examples.md)
- 고급 ETL 시나리오
- 복잡한 데이터 변환 작업
- 성능 최적화 기법
- 독립 수행 과제

### 6. [문제 해결 가이드](docs/06-troubleshooting.md)
- 일반적인 오류 해결 방법
- FAQ
- 추가 학습 리소스

## 🔧 사전 요구사항

### 필수 요구사항
- **AWS 계정**: 프리 티어 계정으로도 실습 가능
- **기본 SQL 지식**: SELECT, WHERE, GROUP BY 등 기본 쿼리 작성 능력
- **웹 브라우저**: Chrome, Firefox, Safari 등 최신 브라우저

### 권장 요구사항
- **Python 기초 지식**: Glue ETL 스크립트 이해를 위해 권장
- **데이터베이스 기본 개념**: 테이블, 스키마 등의 개념 이해
- **클라우드 컴퓨팅 기초**: AWS 기본 개념에 대한 이해

### 예상 비용
- **프리 티어 사용자**: 대부분의 실습이 무료 한도 내에서 가능
- **일반 사용자**: 전체 워크샵 완료 시 약 $3-5 예상
- **비용 절약 팁**: 실습 완료 후 리소스 정리 방법 안내

## 🚀 시작하기

1. **AWS 계정 준비**: [AWS 계정 생성](https://aws.amazon.com/ko/free/)
2. **설정 가이드 따라하기**: [AWS 서비스 설정 가이드](docs/02-aws-setup-guide.md)
3. **기본 실습 시작**: [기본 실습 워크샵](docs/04-basic-workshop.md)

## 📊 메인 데이터셋

이 워크샵에서는 **"AI Tool Usage by Indian College Students 2025"** 데이터셋을 주로 사용합니다. 이 데이터셋은 대학생들의 AI 도구 사용 패턴을 분석할 수 있는 흥미로운 인사이트를 제공합니다.

- **데이터 크기**: 약 5,000개 레코드
- **주요 컬럼**: 학생 정보, 사용 AI 도구, 사용 빈도, 만족도 등
- **분석 가능한 인사이트**: 전공별 AI 도구 선호도, 사용 패턴 분석 등

## 🤝 기여하기

이 워크샵 자료의 개선에 기여하고 싶으시다면:

1. 이슈 등록을 통한 문제점 신고
2. Pull Request를 통한 개선사항 제안
3. 새로운 데이터셋이나 예제 추가 제안

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다. 자세한 내용은 [LICENSE](LICENSE) 파일을 참조하세요.

## 📞 문의사항

워크샵 관련 문의사항이나 도움이 필요하시면 GitHub Issues를 통해 연락해 주세요.

---

**Happy Learning! 🎓**