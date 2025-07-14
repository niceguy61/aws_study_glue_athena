# AWS 서비스 통합 아키텍처 다이어그램

## 1. AWS 서비스 간 상세 연결 관계

```mermaid
graph TB
    subgraph "Identity & Access Management"
        IAM[AWS IAM<br/>🔐 Identity & Access Management<br/>• User management<br/>• Role-based access<br/>• Policy enforcement<br/>• Cross-service permissions]
        
        STS[AWS STS<br/>🎫 Security Token Service<br/>• Temporary credentials<br/>• Role assumption<br/>• Cross-account access]
    end
    
    subgraph "Data Storage Services"
        S3_Raw[Amazon S3 - Raw Data<br/>📦 Object Storage<br/>• Bucket: workshop-raw-data<br/>• Versioning enabled<br/>• Lifecycle policies<br/>• Event notifications]
        
        S3_Processed[Amazon S3 - Processed Data<br/>📦 Object Storage<br/>• Bucket: workshop-processed-data<br/>• Optimized formats<br/>• Partitioned structure<br/>• Compression enabled]
        
        S3_Results[Amazon S3 - Query Results<br/>📦 Object Storage<br/>• Bucket: workshop-athena-results<br/>• Query output location<br/>• Result caching<br/>• Automatic cleanup]
    end
    
    subgraph "Data Processing Services"
        Glue_Crawler[AWS Glue Crawler<br/>🕷️ Schema Discovery<br/>• Automatic schema detection<br/>• Scheduled execution<br/>• Multiple data sources<br/>• Incremental updates]
        
        Glue_Catalog[AWS Glue Data Catalog<br/>📚 Metadata Repository<br/>• Table definitions<br/>• Schema versions<br/>• Partition information<br/>• Data lineage tracking]
        
        Glue_ETL[AWS Glue ETL Jobs<br/>⚙️ Data Transformation<br/>• PySpark execution<br/>• Serverless processing<br/>• Auto-scaling<br/>• Job bookmarking]
        
        Glue_Studio[AWS Glue Studio<br/>🎨 Visual ETL Designer<br/>• Drag-and-drop interface<br/>• Code generation<br/>• Job monitoring<br/>• Template library]
    end
    
    subgraph "Analytics Services"
        Athena[Amazon Athena<br/>🔍 Serverless SQL<br/>• Pay-per-query pricing<br/>• Standard SQL support<br/>• Result caching<br/>• Workgroup management]
    end
    
    subgraph "Monitoring & Logging"
        CloudWatch[Amazon CloudWatch<br/>📊 Monitoring & Observability<br/>• Metrics collection<br/>• Log aggregation<br/>• Alarm management<br/>• Dashboard creation]
        
        CloudTrail[AWS CloudTrail<br/>📋 API Logging<br/>• API call tracking<br/>• Compliance auditing<br/>• Event history<br/>• Security monitoring]
        
        XRay[AWS X-Ray<br/>🔬 Distributed Tracing<br/>• Request tracing<br/>• Performance analysis<br/>• Service map<br/>• Error analysis]
    end
    
    subgraph "Notification Services"
        SNS[Amazon SNS<br/>📧 Simple Notification Service<br/>• Email notifications<br/>• SMS alerts<br/>• Topic-based messaging<br/>• Multi-protocol delivery]
        
        SES[Amazon SES<br/>✉️ Simple Email Service<br/>• Bulk email sending<br/>• Email templates<br/>• Delivery tracking<br/>• Bounce handling]
    end
    
    %% IAM Connections (Security)
    IAM -.->|Permissions| S3_Raw
    IAM -.->|Permissions| S3_Processed
    IAM -.->|Permissions| S3_Results
    IAM -.->|Permissions| Glue_Crawler
    IAM -.->|Permissions| Glue_Catalog
    IAM -.->|Permissions| Glue_ETL
    IAM -.->|Permissions| Glue_Studio
    IAM -.->|Permissions| Athena
    IAM -.->|Permissions| CloudWatch
    IAM -.->|Permissions| SNS
    
    STS -.->|Temporary Credentials| Glue_ETL
    STS -.->|Temporary Credentials| Athena
    
    %% Data Flow Connections
    S3_Raw -->|Data Source| Glue_Crawler
    Glue_Crawler -->|Schema Discovery| Glue_Catalog
    Glue_Catalog -->|Metadata| Glue_ETL
    Glue_Catalog -->|Metadata| Glue_Studio
    Glue_Catalog -->|Table Definitions| Athena
    
    Glue_ETL -->|Transformed Data| S3_Processed
    Glue_Studio -->|Visual ETL Output| S3_Processed
    S3_Raw -->|Source Data| Glue_ETL
    S3_Raw -->|Source Data| Glue_Studio
    
    S3_Processed -->|Analytics Data| Athena
    Athena -->|Query Results| S3_Results
    
    %% Monitoring Connections
    S3_Raw -->|Metrics & Logs| CloudWatch
    S3_Processed -->|Metrics & Logs| CloudWatch
    S3_Results -->|Metrics & Logs| CloudWatch
    Glue_Crawler -->|Job Metrics| CloudWatch
    Glue_ETL -->|Job Metrics| CloudWatch
    Athena -->|Query Metrics| CloudWatch
    
    CloudWatch -->|Alarms| SNS
    SNS -->|Email Notifications| SES
    
    %% Audit Trail
    S3_Raw -->|API Calls| CloudTrail
    Glue_Crawler -->|API Calls| CloudTrail
    Glue_ETL -->|API Calls| CloudTrail
    Athena -->|API Calls| CloudTrail
    
    %% Tracing
    Glue_ETL -->|Execution Traces| XRay
    Athena -->|Query Traces| XRay
    
    %% Styling
    classDef security fill:#ffebee,stroke:#d32f2f
    classDef storage fill:#e3f2fd,stroke:#1976d2
    classDef processing fill:#e8f5e8,stroke:#388e3c
    classDef analytics fill:#fff8e1,stroke:#f57c00
    classDef monitoring fill:#f3e5f5,stroke:#7b1fa2
    classDef notification fill:#fff3e0,stroke:#f57c00
    
    class IAM,STS security
    class S3_Raw,S3_Processed,S3_Results storage
    class Glue_Crawler,Glue_Catalog,Glue_ETL,Glue_Studio processing
    class Athena analytics
    class CloudWatch,CloudTrail,XRay monitoring
    class SNS,SES notification
```

## 2. 데이터 라이프사이클 관리

```mermaid
stateDiagram-v2
    [*] --> RawData : Data Upload
    
    state RawData {
        [*] --> Uploaded
        Uploaded --> Validated : Schema Check
        Validated --> Cataloged : Crawler Run
        Cataloged --> [*]
    }
    
    RawData --> Processing : ETL Trigger
    
    state Processing {
        [*] --> ETLJob
        ETLJob --> DataCleaning
        DataCleaning --> DataTransformation
        DataTransformation --> DataValidation
        DataValidation --> OutputGeneration
        OutputGeneration --> [*]
    }
    
    Processing --> ProcessedData : ETL Complete
    
    state ProcessedData {
        [*] --> Optimized
        Optimized --> Partitioned
        Partitioned --> Compressed
        Compressed --> Indexed
        Indexed --> [*]
    }
    
    ProcessedData --> Analytics : Query Ready
    
    state Analytics {
        [*] --> QueryExecution
        QueryExecution --> ResultGeneration
        ResultGeneration --> ResultCaching
        ResultCaching --> [*]
    }
    
    Analytics --> Archive : Lifecycle Policy
    
    state Archive {
        [*] --> InfrequentAccess
        InfrequentAccess --> Glacier
        Glacier --> DeepArchive
        DeepArchive --> [*]
    }
    
    Archive --> [*] : Data Retention Complete
```

## 3. 보안 및 권한 관리 아키텍처

```mermaid
graph LR
    subgraph "사용자 및 역할"
        Student[👨‍🎓 Student User<br/>• Workshop participant<br/>• Limited permissions<br/>• Temporary access]
        
        Instructor[👨‍🏫 Instructor Role<br/>• Workshop administrator<br/>• Full access<br/>• Resource management]
        
        ServiceRole[🤖 Service Roles<br/>• Glue service role<br/>• Athena service role<br/>• Cross-service access]
    end
    
    subgraph "권한 정책"
        StudentPolicy[Student Policy<br/>📋 Restricted Access<br/>• S3 read/write specific buckets<br/>• Glue job execution<br/>• Athena query execution<br/>• CloudWatch read access]
        
        InstructorPolicy[Instructor Policy<br/>📋 Administrative Access<br/>• Full S3 access<br/>• Glue administration<br/>• IAM management<br/>• Cost monitoring]
        
        ServicePolicy[Service Policy<br/>📋 Cross-Service Access<br/>• S3 data access<br/>• Glue catalog access<br/>• CloudWatch logging<br/>• SNS notifications]
    end
    
    subgraph "리소스 기반 정책"
        BucketPolicy[S3 Bucket Policies<br/>🔒 Resource-Level Security<br/>• Cross-account access<br/>• IP-based restrictions<br/>• Time-based access<br/>• MFA requirements]
        
        KMSPolicy[KMS Key Policies<br/>🔐 Encryption Management<br/>• Key usage permissions<br/>• Encryption context<br/>• Key rotation<br/>• Audit logging]
    end
    
    %% User to Policy Connections
    Student -->|Attached| StudentPolicy
    Instructor -->|Attached| InstructorPolicy
    ServiceRole -->|Attached| ServicePolicy
    
    %% Policy to Resource Connections
    StudentPolicy -.->|Allows| BucketPolicy
    InstructorPolicy -.->|Allows| BucketPolicy
    ServicePolicy -.->|Allows| BucketPolicy
    
    StudentPolicy -.->|Uses| KMSPolicy
    InstructorPolicy -.->|Uses| KMSPolicy
    ServicePolicy -.->|Uses| KMSPolicy
    
    %% Styling
    classDef user fill:#e3f2fd
    classDef policy fill:#fff3e0
    classDef resource fill:#ffebee
    
    class Student,Instructor,ServiceRole user
    class StudentPolicy,InstructorPolicy,ServicePolicy policy
    class BucketPolicy,KMSPolicy resource
```

## 4. 비용 최적화 및 모니터링

```mermaid
graph TB
    subgraph "비용 모니터링"
        CostExplorer[AWS Cost Explorer<br/>💰 Cost Analysis<br/>• Service-wise costs<br/>• Usage patterns<br/>• Cost forecasting<br/>• Budget alerts]
        
        Budgets[AWS Budgets<br/>📊 Budget Management<br/>• Monthly budget limits<br/>• Cost threshold alerts<br/>• Usage-based budgets<br/>• Custom notifications]
        
        BillingAlerts[Billing Alerts<br/>🚨 Cost Notifications<br/>• CloudWatch alarms<br/>• SNS notifications<br/>• Email alerts<br/>• Slack integration]
    end
    
    subgraph "리소스 최적화"
        S3Analytics[S3 Storage Analytics<br/>📈 Storage Optimization<br/>• Access pattern analysis<br/>• Lifecycle recommendations<br/>• Storage class optimization<br/>• Cost reduction insights]
        
        GlueMetrics[Glue Job Metrics<br/>⚙️ Processing Optimization<br/>• DPU utilization<br/>• Job duration analysis<br/>• Memory usage patterns<br/>• Scaling recommendations]
        
        AthenaMetrics[Athena Query Metrics<br/>🔍 Query Optimization<br/>• Data scanned analysis<br/>• Query performance<br/>• Cost per query<br/>• Optimization suggestions]
    end
    
    subgraph "자동화된 최적화"
        LifecyclePolicies[S3 Lifecycle Policies<br/>🔄 Automated Transitions<br/>• Standard to IA<br/>• IA to Glacier<br/>• Glacier to Deep Archive<br/>• Automatic deletion]
        
        AutoScaling[Auto Scaling<br/>📏 Dynamic Resource Allocation<br/>• Glue DPU scaling<br/>• Concurrent query limits<br/>• Resource scheduling<br/>• Load balancing]
    end
    
    CostExplorer --> Budgets
    Budgets --> BillingAlerts
    
    S3Analytics --> LifecyclePolicies
    GlueMetrics --> AutoScaling
    AthenaMetrics --> AutoScaling
    
    BillingAlerts -.-> S3Analytics
    BillingAlerts -.-> GlueMetrics
    BillingAlerts -.-> AthenaMetrics
    
    classDef monitoring fill:#fff3e0
    classDef optimization fill:#e8f5e8
    classDef automation fill:#f3e5f5
    
    class CostExplorer,Budgets,BillingAlerts monitoring
    class S3Analytics,GlueMetrics,AthenaMetrics optimization
    class LifecyclePolicies,AutoScaling automation
```

## 5. 재해 복구 및 백업 전략

```mermaid
flowchart TD
    subgraph "백업 전략"
        PrimaryRegion[Primary Region<br/>🌍 ap-northeast-2<br/>• Main workshop resources<br/>• Active data processing<br/>• Real-time monitoring]
        
        BackupRegion[Backup Region<br/>🌏 ap-southeast-1<br/>• Cross-region replication<br/>• Disaster recovery<br/>• Backup storage]
        
        S3Replication[S3 Cross-Region Replication<br/>🔄 Automated Backup<br/>• Real-time replication<br/>• Version control<br/>• Encryption in transit]
    end
    
    subgraph "복구 절차"
        HealthCheck[Health Monitoring<br/>🏥 Service Health Check<br/>• Automated monitoring<br/>• Failure detection<br/>• Alert generation]
        
        Failover[Failover Process<br/>🔄 Service Switching<br/>• DNS routing<br/>• Service redirection<br/>• Data consistency check]
        
        Recovery[Recovery Process<br/>🔧 Service Restoration<br/>• Data validation<br/>• Service restart<br/>• Performance verification]
    end
    
    subgraph "데이터 보호"
        Versioning[S3 Versioning<br/>📚 Version Control<br/>• Object versioning<br/>• Accidental deletion protection<br/>• Point-in-time recovery]
        
        MFA[MFA Delete<br/>🔐 Multi-Factor Authentication<br/>• Secure deletion<br/>• Administrative protection<br/>• Audit trail]
        
        Encryption[Data Encryption<br/>🔒 Security at Rest<br/>• KMS encryption<br/>• Client-side encryption<br/>• Key rotation]
    end
    
    PrimaryRegion -->|Replicate| S3Replication
    S3Replication -->|Store| BackupRegion
    
    HealthCheck -->|Detect Failure| Failover
    Failover -->|Switch Services| BackupRegion
    BackupRegion -->|Restore| Recovery
    Recovery -->|Validate| PrimaryRegion
    
    PrimaryRegion -.->|Enable| Versioning
    Versioning -.->|Protect| MFA
    MFA -.->|Secure| Encryption
    
    classDef primary fill:#e3f2fd
    classDef backup fill:#fff3e0
    classDef protection fill:#ffebee
    
    class PrimaryRegion,S3Replication primary
    class BackupRegion,HealthCheck,Failover,Recovery backup
    class Versioning,MFA,Encryption protection
```

## 통합 아키텍처 활용 가이드

### 1. 워크샵 설정 단계
- IAM 역할 및 정책 설정 참조
- 보안 및 권한 관리 아키텍처 활용
- 서비스 간 연결 관계 확인

### 2. 실습 진행 단계
- 데이터 라이프사이클 관리 플로우 참조
- AWS 서비스 간 상세 연결 관계 활용
- 모니터링 및 알림 설정

### 3. 비용 관리 단계
- 비용 최적화 및 모니터링 다이어그램 참조
- 리소스 사용량 추적
- 자동화된 최적화 설정

### 4. 문제 해결 단계
- 재해 복구 및 백업 전략 참조
- 서비스 상태 모니터링
- 복구 절차 실행

### 5. 워크샵 완료 후
- 리소스 정리 가이드
- 비용 최적화 검토
- 보안 설정 검증