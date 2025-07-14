# 데이터 파이프라인 플로우 상세 다이어그램

## 1. 단계별 데이터 변환 플로우

```mermaid
flowchart LR
    subgraph "Raw Data Sources"
        CSV[CSV Files<br/>• Student survey data<br/>• Comma-separated<br/>• Headers included]
        JSON[JSON Files<br/>• API responses<br/>• Nested structures<br/>• Semi-structured]
        Parquet[Parquet Files<br/>• Columnar format<br/>• Compressed<br/>• Schema embedded]
    end
    
    subgraph "S3 Raw Data Bucket"
        RawBucket[s3://workshop-raw-data/<br/>├── csv/<br/>│   └── ai-tool-usage.csv<br/>├── json/<br/>│   └── student-profiles.json<br/>└── parquet/<br/>    └── survey-responses.parquet]
    end
    
    subgraph "Schema Discovery Process"
        Crawler[Glue Crawler<br/>• Scan file formats<br/>• Infer data types<br/>• Detect partitions<br/>• Create table schemas]
        
        CatalogTables[Data Catalog Tables<br/>• ai_tool_usage_csv<br/>• student_profiles_json<br/>• survey_responses_parquet]
    end
    
    subgraph "ETL Transformation Logic"
        DataCleaning[Data Cleaning<br/>• Remove null values<br/>• Standardize formats<br/>• Validate data types<br/>• Handle duplicates]
        
        DataEnrichment[Data Enrichment<br/>• Calculate derived fields<br/>• Add metadata<br/>• Apply business rules<br/>• Create aggregations]
        
        FormatConversion[Format Conversion<br/>• Convert to Parquet<br/>• Apply compression<br/>• Optimize partitioning<br/>• Add indexes]
    end
    
    subgraph "S3 Processed Data Bucket"
        ProcessedBucket[s3://workshop-processed-data/<br/>├── year=2025/<br/>│   ├── month=01/<br/>│   │   └── ai-tool-analytics.parquet<br/>│   └── month=02/<br/>│       └── ai-tool-analytics.parquet<br/>└── aggregated/<br/>    └── summary-statistics.parquet]
    end
    
    subgraph "Analytics Layer"
        AthenaQueries[Athena SQL Queries<br/>• Basic aggregations<br/>• Complex joins<br/>• Window functions<br/>• Statistical analysis]
        
        QueryResults[Query Results<br/>• CSV exports<br/>• JSON responses<br/>• Cached results<br/>• Visualization data]
    end
    
    %% Data Flow
    CSV --> RawBucket
    JSON --> RawBucket
    Parquet --> RawBucket
    
    RawBucket --> Crawler
    Crawler --> CatalogTables
    
    CatalogTables --> DataCleaning
    DataCleaning --> DataEnrichment
    DataEnrichment --> FormatConversion
    
    FormatConversion --> ProcessedBucket
    ProcessedBucket --> AthenaQueries
    AthenaQueries --> QueryResults
    
    %% Styling
    classDef source fill:#e3f2fd
    classDef storage fill:#f3e5f5
    classDef processing fill:#e8f5e8
    classDef analytics fill:#fff8e1
    
    class CSV,JSON,Parquet source
    class RawBucket,ProcessedBucket storage
    class Crawler,CatalogTables,DataCleaning,DataEnrichment,FormatConversion processing
    class AthenaQueries,QueryResults analytics
```

## 2. 실시간 모니터링 플로우

```mermaid
sequenceDiagram
    participant Student as 👨‍🎓 Student
    participant CloudWatch as 📊 CloudWatch
    participant S3 as 📦 S3
    participant Glue as ⚙️ Glue
    participant Athena as 🔍 Athena
    participant SNS as 📧 SNS
    
    Note over Student, SNS: 실습 진행 모니터링
    
    Student->>S3: Upload data file
    S3->>CloudWatch: Log upload metrics
    CloudWatch->>CloudWatch: Check file size & format
    
    alt File size > 100MB
        CloudWatch->>SNS: Send size warning
        SNS->>Student: Email notification
    end
    
    Student->>Glue: Start crawler
    Glue->>CloudWatch: Log crawler start
    
    loop Crawler Progress
        Glue->>CloudWatch: Update progress metrics
        CloudWatch->>Student: Display progress (Console)
    end
    
    Glue->>CloudWatch: Log crawler completion
    
    alt Crawler failed
        CloudWatch->>SNS: Send failure alert
        SNS->>Student: Error notification
    else Crawler succeeded
        CloudWatch->>Student: Success notification
    end
    
    Student->>Glue: Start ETL job
    Glue->>CloudWatch: Log ETL start
    
    loop ETL Progress
        Glue->>CloudWatch: Update job metrics
        Note over CloudWatch: • DPU usage<br/>• Processing time<br/>• Data volume
    end
    
    Glue->>CloudWatch: Log ETL completion
    Student->>Athena: Execute query
    Athena->>CloudWatch: Log query metrics
    
    Note over CloudWatch: • Query duration<br/>• Data scanned<br/>• Cost estimation
    
    Athena->>Student: Return results
    CloudWatch->>Student: Display cost summary
```

## 3. 오류 처리 및 복구 플로우

```mermaid
flowchart TD
    Start([실습 단계 시작]) --> Execute[작업 실행]
    Execute --> Check{작업 성공?}
    
    Check -->|성공| Success[다음 단계 진행]
    Check -->|실패| ErrorType{오류 유형 분석}
    
    ErrorType -->|권한 오류| PermissionFix[IAM 권한 확인<br/>• 정책 검토<br/>• 역할 설정 확인<br/>• 리소스 접근 권한]
    ErrorType -->|데이터 오류| DataFix[데이터 검증<br/>• 파일 형식 확인<br/>• 스키마 검증<br/>• 데이터 품질 체크]
    ErrorType -->|설정 오류| ConfigFix[설정 검토<br/>• 서비스 구성 확인<br/>• 파라미터 검증<br/>• 연결 설정 점검]
    ErrorType -->|리소스 오류| ResourceFix[리소스 상태 확인<br/>• 서비스 한도 점검<br/>• 가용성 확인<br/>• 네트워크 연결]
    
    PermissionFix --> Retry[작업 재시도]
    DataFix --> Retry
    ConfigFix --> Retry
    ResourceFix --> Retry
    
    Retry --> ReCheck{재시도 성공?}
    ReCheck -->|성공| Success
    ReCheck -->|실패| Support[지원 요청<br/>• FAQ 참조<br/>• 트러블슈팅 가이드<br/>• 강사 문의]
    
    Support --> ManualFix[수동 해결]
    ManualFix --> Success
    
    Success --> End([단계 완료])
    
    %% 스타일링
    classDef startEnd fill:#4caf50,color:#fff
    classDef process fill:#2196f3,color:#fff
    classDef decision fill:#ff9800,color:#fff
    classDef error fill:#f44336,color:#fff
    classDef fix fill:#9c27b0,color:#fff
    
    class Start,End startEnd
    class Execute,Success,ManualFix process
    class Check,ErrorType,ReCheck decision
    class PermissionFix,DataFix,ConfigFix,ResourceFix,Retry,Support fix
```

## 4. 성능 최적화 플로우

```mermaid
graph TB
    subgraph "데이터 최적화 전략"
        A[파일 크기 최적화<br/>• 128MB-1GB 권장<br/>• 너무 작은 파일 병합<br/>• 큰 파일 분할]
        
        B[파티셔닝 전략<br/>• 날짜별 파티션<br/>• 카테고리별 파티션<br/>• 쿼리 패턴 고려]
        
        C[압축 최적화<br/>• Snappy 압축<br/>• GZIP 압축<br/>• 압축률 vs 성능]
    end
    
    subgraph "쿼리 최적화 전략"
        D[파티션 프루닝<br/>• WHERE 절 활용<br/>• 파티션 키 사용<br/>• 불필요한 스캔 방지]
        
        E[컬럼 선택 최적화<br/>• SELECT * 지양<br/>• 필요한 컬럼만 선택<br/>• Parquet 컬럼 스토어 활용]
        
        F[조인 최적화<br/>• 작은 테이블 먼저<br/>• 적절한 조인 키<br/>• 브로드캐스트 조인 고려]
    end
    
    subgraph "리소스 최적화 전략"
        G[Glue DPU 최적화<br/>• 데이터 크기별 DPU<br/>• 병렬 처리 고려<br/>• 비용 효율성]
        
        H[Athena 동시성<br/>• 쿼리 큐 관리<br/>• 동시 실행 제한<br/>• 리소스 경합 방지]
    end
    
    A --> B
    B --> C
    D --> E
    E --> F
    G --> H
    
    C -.-> D
    F -.-> G
    
    classDef optimization fill:#e8f5e8
    class A,B,C,D,E,F,G,H optimization
```

## 5. 보안 및 거버넌스 플로우

```mermaid
flowchart LR
    subgraph "데이터 보안 계층"
        Encryption[데이터 암호화<br/>• S3 서버 측 암호화<br/>• 전송 중 암호화<br/>• KMS 키 관리]
        
        Access[접근 제어<br/>• IAM 정책<br/>• 버킷 정책<br/>• ACL 설정]
        
        Network[네트워크 보안<br/>• VPC 엔드포인트<br/>• 보안 그룹<br/>• NACL 설정]
    end
    
    subgraph "감사 및 모니터링"
        Logging[로깅<br/>• CloudTrail 로그<br/>• S3 액세스 로그<br/>• Glue 작업 로그]
        
        Monitoring[모니터링<br/>• CloudWatch 메트릭<br/>• 알람 설정<br/>• 대시보드 구성]
        
        Compliance[컴플라이언스<br/>• 데이터 분류<br/>• 보존 정책<br/>• 규정 준수]
    end
    
    subgraph "데이터 거버넌스"
        Catalog[데이터 카탈로그<br/>• 메타데이터 관리<br/>• 스키마 진화<br/>• 데이터 계보]
        
        Quality[데이터 품질<br/>• 품질 규칙<br/>• 검증 프로세스<br/>• 이상 탐지]
        
        Lifecycle[생명주기 관리<br/>• 자동 아카이빙<br/>• 삭제 정책<br/>• 비용 최적화]
    end
    
    Encryption --> Access
    Access --> Network
    Logging --> Monitoring
    Monitoring --> Compliance
    Catalog --> Quality
    Quality --> Lifecycle
    
    Network -.-> Logging
    Compliance -.-> Catalog
    
    classDef security fill:#ffebee
    classDef monitoring fill:#fff3e0
    classDef governance fill:#f3e5f5
    
    class Encryption,Access,Network security
    class Logging,Monitoring,Compliance monitoring
    class Catalog,Quality,Lifecycle governance
```

## 다이어그램 활용 가이드

### 실습 단계별 다이어그램 매핑

1. **데이터 업로드 단계**: 단계별 데이터 변환 플로우 참조
2. **크롤러 실행 단계**: 실시간 모니터링 플로우 참조
3. **ETL 작업 단계**: 성능 최적화 플로우 참조
4. **쿼리 실행 단계**: 오류 처리 및 복구 플로우 참조
5. **보안 설정 단계**: 보안 및 거버넌스 플로우 참조

### 문제 해결 시 참조 순서

1. 오류 발생 → 오류 처리 및 복구 플로우
2. 성능 이슈 → 성능 최적화 플로우
3. 보안 문제 → 보안 및 거버넌스 플로우
4. 모니터링 필요 → 실시간 모니터링 플로우