#!/bin/bash

# AWS 데이터 분석 워크샵 진단 도구 실행 스크립트
# 이 스크립트는 워크샵 환경의 문제를 자동으로 진단합니다.

set -e

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 함수 정의
print_header() {
    echo -e "${BLUE}================================${NC}"
    echo -e "${BLUE}🔍 AWS 워크샵 진단 도구${NC}"
    echo -e "${BLUE}================================${NC}"
    echo ""
}

print_usage() {
    echo "사용법: $0 [옵션]"
    echo ""
    echo "옵션:"
    echo "  -p, --profile PROFILE    AWS 프로필 이름"
    echo "  -r, --region REGION      AWS 리전 (기본값: us-east-1)"
    echo "  -b, --bucket BUCKET      확인할 S3 버킷 이름"
    echo "  -o, --output FILE        결과를 JSON 파일로 저장"
    echo "  -f, --fix               자동 수정 스크립트 생성"
    echo "  -q, --quiet             요약 결과만 출력"
    echo "  -h, --help              이 도움말 표시"
    echo ""
    echo "예시:"
    echo "  $0 --bucket my-workshop-bucket"
    echo "  $0 --profile workshop-user --region us-west-2"
    echo "  $0 --bucket my-bucket --fix --output diagnosis.json"
}

check_dependencies() {
    echo -e "${YELLOW}📋 의존성 확인 중...${NC}"
    
    # Python 확인
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}❌ Python 3이 설치되지 않았습니다${NC}"
        echo "Python 3.7 이상을 설치하세요: https://www.python.org/downloads/"
        exit 1
    fi
    
    # AWS CLI 확인
    if ! command -v aws &> /dev/null; then
        echo -e "${RED}❌ AWS CLI가 설치되지 않았습니다${NC}"
        echo "AWS CLI를 설치하세요: https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html"
        exit 1
    fi
    
    # boto3 확인
    if ! python3 -c "import boto3" &> /dev/null; then
        echo -e "${YELLOW}⚠️ boto3가 설치되지 않았습니다. 설치를 시도합니다...${NC}"
        pip3 install boto3 botocore
    fi
    
    # tabulate 확인 (선택사항)
    if ! python3 -c "import tabulate" &> /dev/null; then
        echo -e "${YELLOW}⚠️ tabulate가 설치되지 않았습니다. 설치를 시도합니다...${NC}"
        pip3 install tabulate
    fi
    
    echo -e "${GREEN}✅ 의존성 확인 완료${NC}"
    echo ""
}

run_full_diagnostic() {
    local profile_arg=""
    local region_arg=""
    local bucket_arg=""
    local output_arg=""
    local fix_arg=""
    local quiet_arg=""
    
    # 인수 구성
    if [ ! -z "$PROFILE" ]; then
        profile_arg="--profile $PROFILE"
    fi
    
    if [ ! -z "$REGION" ]; then
        region_arg="--region $REGION"
    fi
    
    if [ ! -z "$BUCKET" ]; then
        bucket_arg="--bucket $BUCKET"
    fi
    
    if [ ! -z "$OUTPUT" ]; then
        output_arg="--output $OUTPUT"
    fi
    
    if [ "$FIX" = true ]; then
        fix_arg="--fix"
    fi
    
    if [ "$QUIET" = true ]; then
        quiet_arg="--quiet"
    fi
    
    echo -e "${BLUE}🔍 전체 진단 실행 중...${NC}"
    echo ""
    
    # 스크립트 디렉토리 찾기
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    
    # 진단 스크립트 실행
    python3 "$SCRIPT_DIR/diagnose_issues.py" $profile_arg $region_arg $bucket_arg $output_arg $fix_arg $quiet_arg
    diagnostic_exit_code=$?
    
    echo ""
    
    if [ $diagnostic_exit_code -eq 0 ]; then
        echo -e "${GREEN}✅ 진단 완료: 심각한 문제가 발견되지 않았습니다${NC}"
    else
        echo -e "${RED}⚠️ 진단 완료: 해결이 필요한 문제가 발견되었습니다${NC}"
        echo ""
        echo -e "${YELLOW}추가 도구 실행:${NC}"
        echo "  • AWS 설정 검증: python3 $SCRIPT_DIR/validate_aws_config.py $profile_arg $region_arg $bucket_arg"
        if [ ! -z "$BUCKET" ]; then
            echo "  • 파이프라인 상태 확인: python3 $SCRIPT_DIR/check_pipeline_status.py $profile_arg $region_arg $bucket_arg"
        fi
        echo "  • 문제 해결 가이드: docs/06-troubleshooting.md"
    fi
    
    return $diagnostic_exit_code
}

run_quick_check() {
    echo -e "${BLUE}⚡ 빠른 확인 실행 중...${NC}"
    echo ""
    
    # AWS 자격 증명 확인
    echo -e "${YELLOW}🔑 AWS 자격 증명 확인...${NC}"
    if aws sts get-caller-identity > /dev/null 2>&1; then
        echo -e "${GREEN}✅ AWS 자격 증명 유효${NC}"
        aws sts get-caller-identity --query 'Account' --output text | sed 's/^/   계정 ID: /'
    else
        echo -e "${RED}❌ AWS 자격 증명 문제${NC}"
        echo "   해결방법: aws configure 명령으로 자격 증명을 설정하세요"
        return 1
    fi
    
    # S3 접근 확인
    echo -e "${YELLOW}📦 S3 접근 확인...${NC}"
    if aws s3 ls > /dev/null 2>&1; then
        echo -e "${GREEN}✅ S3 접근 가능${NC}"
        bucket_count=$(aws s3 ls | wc -l)
        echo "   버킷 수: $bucket_count"
    else
        echo -e "${RED}❌ S3 접근 문제${NC}"
        echo "   해결방법: IAM 정책에 S3 권한을 추가하세요"
    fi
    
    # 특정 버킷 확인
    if [ ! -z "$BUCKET" ]; then
        echo -e "${YELLOW}🎯 버킷 '$BUCKET' 확인...${NC}"
        if aws s3 ls "s3://$BUCKET" > /dev/null 2>&1; then
            echo -e "${GREEN}✅ 버킷 접근 가능${NC}"
            object_count=$(aws s3 ls "s3://$BUCKET" --recursive | wc -l)
            echo "   객체 수: $object_count"
        else
            echo -e "${RED}❌ 버킷 접근 불가${NC}"
            echo "   해결방법: 버킷이 존재하는지 확인하고 권한을 검토하세요"
        fi
    fi
    
    echo ""
    echo -e "${GREEN}⚡ 빠른 확인 완료${NC}"
}

# 기본값 설정
PROFILE=""
REGION="us-east-1"
BUCKET=""
OUTPUT=""
FIX=false
QUIET=false
QUICK=false

# 인수 파싱
while [[ $# -gt 0 ]]; do
    case $1 in
        -p|--profile)
            PROFILE="$2"
            shift 2
            ;;
        -r|--region)
            REGION="$2"
            shift 2
            ;;
        -b|--bucket)
            BUCKET="$2"
            shift 2
            ;;
        -o|--output)
            OUTPUT="$2"
            shift 2
            ;;
        -f|--fix)
            FIX=true
            shift
            ;;
        -q|--quiet)
            QUIET=true
            shift
            ;;
        --quick)
            QUICK=true
            shift
            ;;
        -h|--help)
            print_usage
            exit 0
            ;;
        *)
            echo -e "${RED}알 수 없는 옵션: $1${NC}"
            print_usage
            exit 1
            ;;
    esac
done

# 메인 실행
print_header

if [ "$QUICK" = true ]; then
    run_quick_check
    exit_code=$?
else
    check_dependencies
    run_full_diagnostic
    exit_code=$?
fi

echo ""
echo -e "${BLUE}================================${NC}"

exit $exit_code