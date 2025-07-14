# AWS 데이터 분석 워크샵 아키텍처 다이어그램

이 문서는 AWS 데이터 분석 워크샵에서 사용되는 전체 아키텍처와 데이터 플로우를 시각화한 다이어그램들을 포함합니다.

## 1. 전체 데이터 파이프라인 아키텍처

```mermaid
graph TB
    subgraph "External Data Sources"
        A[Kaggle<br/>AI Tool Usage Dataset]
        B[Hugging Face<br/>Datasets]
        C[Other Public<br/>Data Sources]
    end
    
    subgraph "AWS Data Analytics Pipeline"
        subgraph "Data Storage Layer"
            D[Amazon S3<br/>Raw Data Bucket]
            I[Amazon S3<br/>Processed Data Bucket]
        end
        
        subgraph "Data Processing Layer"
            E[AWS Glue Crawler<br/>Schema Discovery]
            F[AWS Glue Data Catalog<br/>Metadata Repository]
            G[AWS Glue ETL Jobs<br/>Data Transformation]
            H[AWS Glue Studio<br/>Visual ETL Editor]
        end
        
        subgraph "Analytics Layer"
            J[Amazon Athena<br/>SQL Query Engine]
        end
        
        subgraph "Security & Access"
            K[AWS IAM<br/>Roles & Policies]
        end
    end
    
    subgraph "Workshop Learning Materials"
        L[GitHub Repository<br/>Workshop Materials]
        M[Documentation<br/>Markdown Files]
        N[Code Examples<br/>Scripts & Queries]
        O[Configuration Files<br/>Templates & Policies]
    end
    
    subgraph "Student Learning Environment"
        P[AWS Console<br/>Web Interface]
        Q[Local Development<br/>Environment]
    end
    
    %% Data Flow Connections
    A --> D
    B --> D
    C --> D
    D --> E
    E --> F
    F --> G
    F --> H
    G --> I
    H --> I
    I --> J
    
    %% Security Connections
    K -.-> D
    K -.-> E
    K -.-> F
    K -.-> G
    K -.-> H
    K -.-> I
    K -.-> J
    
    %% Learning Materials Connections
    L --> M
    L --> N
    L --> O
    M --> P
    N --> P
    O --> P
    P --> Q
    
    %% Styling
    classDef dataSource fill:#e1f5fe
    classDef awsService fill:#fff3e0
    classDef storage fill:#f3e5f5
    classDef processing fill:#e8f5e8
    classDef analytics fill:#fff8e1
    classDef security fill:#ffebee
    classDef learning fill:#f1f8e9
    
    class A,B,C dataSource
    class D,I storage
    class E,F,G,H processing
    class J analytics
    class K security
    class L,M,N,O,P,Q learning
```

## 2. AWS 서비스 간 연결 관계 상세 다이어그램

```mermaid
graph TB
    subgraph "Data Ingestion"
        S3_Raw[Amazon S3<br/>Raw Data Storage<br/>CSV JSON Parquet files<br/>Partitioned by date<br/>Lifecycle policies]
    end
    
    subgraph "Schema Discovery"
        Crawler[AWS Glue Crawler<br/>Automatic schema detection<br/>Scheduled runs<br/>Data format recognition]
        
        Catalog[AWS Glue Data Catalog<br/>Table definitions<br/>Schema versions<br/>Partition information<br/>Data lineage]
    end
    
    subgraph "Data Transformation"
        ETL[AWS Glue ETL Jobs<br/>PySpark scripts<br/>Data cleaning<br/>Format conversion<br/>Data validation]
        
        Studio[AWS Glue Studio<br/>Visual ETL designer<br/>Drag and drop interface<br/>Code generation<br/>Job monitoring]
    end
    
    subgraph "Processed Storage"
        S3_Processed[Amazon S3<br/>Processed Data Storage<br/>Optimized formats Parquet<br/>Compressed data<br/>Analytics ready structure]
    end
    
    subgraph "Query Analytics"
        Athena[Amazon Athena<br/>Serverless SQL queries<br/>Pay per query pricing<br/>Integration with BI tools<br/>Result caching]
    end
    
    subgraph "Security Governance"
        IAM[AWS IAM<br/>Service roles<br/>User policies<br/>Resource based policies<br/>Cross service permissions]
        
        CloudTrail[AWS CloudTrail<br/>API call logging<br/>Audit trail<br/>Compliance monitoring]
    end
    
    %% Primary Data Flow
    S3_Raw --> Crawler
    Crawler --> Catalog
    Catalog --> ETL
    Catalog --> Studio
    ETL --> S3_Processed
    Studio --> S3_Processed
    S3_Processed --> Athena
    Catalog --> Athena
    
    %% Security Flow
    IAM -.-> S3_Raw
    IAM -.-> Crawler
    IAM -.-> Catalog
    IAM -.-> ETL
    IAM -.-> Studio
    IAM -.-> S3_Processed
    IAM -.-> Athena
    
    CloudTrail -.-> S3_Raw
    CloudTrail -.-> Crawler
    CloudTrail -.-> ETL
    CloudTrail -.-> Athena
    
    %% Styling
    classDef storage fill:#e3f2fd
    classDef processing fill:#e8f5e8
    classDef analytics fill:#fff8e1
    classDef security fill:#ffebee
    
    class S3_Raw,S3_Processed storage
    class Crawler,Catalog,ETL,Studio processing
    class Athena analytics
    class IAM,CloudTrail security
```

## 3. 데이터 플로우 시퀀스 다이어그램

```mermaid
sequenceDiagram
    participant Student as 👨‍🎓 Student
    participant Console as 🖥️ AWS Console
    participant S3_Raw as 📦 S3 Raw Data
    participant Crawler as 🕷️ Glue Crawler
    participant Catalog as 📚 Data Catalog
    participant ETL as ⚙️ Glue ETL/Studio
    participant S3_Proc as 📦 S3 Processed
    participant Athena as 🔍 Athena
    participant Results as 📊 Query Results
    
    Note over Student, Results: Phase 1: Data Preparation
    Student->>Console: 1. Login to AWS Console
    Student->>S3_Raw: 2. Upload raw dataset (CSV/JSON)
    S3_Raw-->>Student: 3. Confirm upload success
    
    Note over Student, Results: Phase 2: Schema Discovery
    Student->>Crawler: 4. Configure and run Glue Crawler
    Crawler->>S3_Raw: 5. Scan data files and infer schema
    S3_Raw-->>Crawler: 6. Return file structure and sample data
    Crawler->>Catalog: 7. Create table definitions and metadata
    Catalog-->>Student: 8. Schema discovery complete
    
    Note over Student, Results: Phase 3: Data Transformation
    Student->>ETL: 9. Create ETL job (Code or Visual)
    ETL->>Catalog: 10. Read table schema and metadata
    Catalog-->>ETL: 11. Return table definitions
    ETL->>S3_Raw: 12. Read raw data based on schema
    S3_Raw-->>ETL: 13. Return raw data for processing
    
    Note over ETL: Data Transformation Process
    Note over ETL: • Clean and validate data<br/>• Apply business rules<br/>• Convert formats<br/>• Optimize for analytics
    
    ETL->>S3_Proc: 14. Write transformed data (Parquet format)
    S3_Proc-->>Student: 15. ETL job completion notification
    
    Note over Student, Results: Phase 4: Data Analysis
    Student->>Athena: 16. Execute SQL queries
    Athena->>Catalog: 17. Get table metadata for query planning
    Catalog-->>Athena: 18. Return table schema and location
    Athena->>S3_Proc: 19. Execute optimized query on processed data
    S3_Proc-->>Athena: 20. Return query results
    Athena->>Results: 21. Format and store query results
    Results-->>Student: 22. Display analysis results
    
    Note over Student, Results: Phase 5: Iterative Analysis
    loop Additional Analysis
        Student->>Athena: Execute more complex queries
        Athena->>S3_Proc: Query processed data
        S3_Proc-->>Athena: Return results
        Athena-->>Student: Display insights
    end
```

## 4. 워크샵 학습 플로우 다이어그램

```mermaid
flowchart TD
    Start([워크샵 시작]) --> Intro[데이터 분석 개요 학습]
    Intro --> Setup[AWS 환경 설정]
    Setup --> Dataset[데이터셋 준비]
    Dataset --> Basic[기본 실습 시작]
    
    subgraph "기본 실습 단계"
        Basic --> Upload[S3에 데이터 업로드]
        Upload --> Crawl[Glue 크롤러 실행]
        Crawl --> Transform[ETL 작업 생성]
        Transform --> Query[Athena 쿼리 실행]
    end
    
    Query --> Check{실습 완료 확인}
    Check -->|성공| Advanced[심화 예제 진행]
    Check -->|실패| Troubleshoot[문제 해결]
    Troubleshoot --> Basic
    
    subgraph "심화 학습"
        Advanced --> Complex[복잡한 ETL 시나리오]
        Complex --> Optimize[성능 최적화]
        Optimize --> Assignment[독립 과제 수행]
    end
    
    Assignment --> Complete([워크샵 완료])
    
    %% 지원 리소스
    GitHub[GitHub 자료] -.-> Intro
    GitHub -.-> Setup
    GitHub -.-> Dataset
    GitHub -.-> Basic
    GitHub -.-> Advanced
    
    FAQ[FAQ & 트러블슈팅] -.-> Troubleshoot
    FAQ -.-> Setup
    FAQ -.-> Basic
    
    %% 스타일링
    classDef startEnd fill:#4caf50,color:#fff
    classDef process fill:#2196f3,color:#fff
    classDef decision fill:#ff9800,color:#fff
    classDef support fill:#9c27b0,color:#fff
    
    class Start,Complete startEnd
    class Intro,Setup,Dataset,Upload,Crawl,Transform,Query,Advanced,Complex,Optimize,Assignment process
    class Check decision
    class GitHub,FAQ support
```

## 5. 비용 최적화 아키텍처 가이드

```mermaid
graph TB
    subgraph "비용 효율적인 데이터 파이프라인 설계"
        subgraph "Storage Optimization"
            A[S3 Intelligent Tiering<br/>자동 계층 이동<br/>비용 최적화<br/>액세스 패턴 기반]
            B[Data Compression<br/>Parquet 형식 사용<br/>GZIP Snappy 압축<br/>스토리지 비용 절감]
            C[Partitioning Strategy<br/>날짜별 파티셔닝<br/>쿼리 성능 향상<br/>스캔 데이터 최소화]
        end
        
        subgraph "Processing Optimization"
            D[Glue Job Sizing<br/>적절한 DPU 설정<br/>작업 크기에 맞는 리소스<br/>실행 시간 최적화]
            E[Crawler Scheduling<br/>필요시에만 실행<br/>스케줄링 최적화<br/>불필요한 실행 방지]
        end
        
        subgraph "Query Optimization"
            F[Athena Query Optimization<br/>파티션 프루닝<br/>컬럼 선택 최적화<br/>결과 캐싱 활용]
            G[Result Location<br/>쿼리 결과 S3 위치<br/>생명주기 정책 적용<br/>자동 정리 설정]
        end
    end
    
    subgraph "모니터링 및 알림"
        H[CloudWatch Metrics<br/>비용 모니터링<br/>사용량 추적<br/>임계값 알림]
        I[Cost Explorer<br/>비용 분석<br/>예산 설정<br/>비용 예측]
    end
    
    A --> B
    B --> C
    D --> E
    F --> G
    H --> I
    
    classDef optimization fill:#e8f5e8
    classDef monitoring fill:#fff3e0
    
    class A,B,C,D,E,F,G optimization
    class H,I monitoring
```

## 다이어그램 사용 가이드

### 1. 전체 아키텍처 다이어그램 활용
- 워크샵 시작 시 전체 구조 설명에 사용
- 각 컴포넌트의 역할과 관계 이해
- 학습 목표와 실습 범위 명확화

### 2. 서비스 연결 관계 다이어그램 활용
- AWS 서비스 설정 단계에서 참조
- 각 서비스의 구체적인 기능 설명
- 권한 설정 및 보안 고려사항 이해

### 3. 데이터 플로우 다이어그램 활용
- 실습 진행 순서 가이드
- 각 단계별 입출력 데이터 확인
- 문제 발생 시 디버깅 참조

### 4. 학습 플로우 다이어그램 활용
- 워크샵 진행 계획 수립
- 학습자 진도 관리
- 추가 학습 경로 안내

### 5. 비용 최적화 다이어그램 활용
- 실습 비용 관리 방법 설명
- 프로덕션 환경 적용 시 고려사항
- 지속 가능한 데이터 파이프라인 설계 가이드