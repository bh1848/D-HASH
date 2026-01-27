# ⚖️ D-HASH: Dynamic Hot-key Aware Scalable Hashing

![Python](https://img.shields.io/badge/Python-3.9-3776AB?logo=python&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-7.4.2-DC382D?logo=redis&logoColor=white)

> **논문 제목:** D-HASH: Dynamic Hot-key Aware Scalable Hashing for Load Balancing in Distributed Cache Systems
> **저자:** 방혁, 전상훈 (수원대학교 정보보호학과)
> **게재:** KSII Transactions on Internet and Information Systems (TIIS), 2026 (게재 예정)

본 레포지토리는 TIIS 2026 게재 예정 논문인 **D-HASH**의 제안 알고리즘과 실험 환경을 구현한 공식 프로젝트입니다.    
Consistent Hashing(CH) 기반의 분산 캐시 환경에서 발생하는 **Hot-key** 현상을 해결하기 위해,     
런타임에 동적으로 트래픽을 분산하는 경량 라우팅 알고리즘을 제안하고 검증했습니다.


## 📋 목차
1. [개요](#1-개요)
2. [실험 설계](#2-실험-설계)
3. [실험 환경](#3-실험-환경)
4. [프로젝트 구조](#4-프로젝트-구조)
5. [실행 방법](#5-실행-방법)
6. [실험 결과](#6-실험-결과)
7. [결론](#7-결론)


## 1. 개요

### 관련 논문
이 프로젝트는 아래 논문의 제안 알고리즘을 시뮬레이션 환경에서 구현하고, 기존 기법(CH, WCH, HRW)과 성능을 비교 검증한 결과물입니다.

![논문 표지](./images/paper_header.png)
*(그림: TIIS 2026에 게재된 논문 초록 및 저자 정보)*

### 실험 아키텍처
D-HASH는 기존 Consistent Hashing 링 구조 위에 **'동적 핫키 감지'** 및 **'윈도우 기반 스위칭'** 계층을 추가한 형태입니다.

![아키텍처 다이어그램](./images/architecture_diagram.png)

> **핵심 원리:**
> 1.  **쓰기(Write):** 데이터 일관성을 위해 항상 주 노드(Primary Node)로 고정.
> 2.  **읽기(Read):** 평소에는 주 노드로 가지만, **Hot-key로 승격되면** 주 노드와 대체 노드(Alternate Node)로 트래픽을 분산.


## 2. 실험 설계

논문의 검증 논리를 코드로 구현하기 위해 다음과 같이 설계했습니다.

### 1) 핫키 승격 (Hot-key Promotion)
* 각 키의 읽기 횟수를 모니터링하여, 임계값 T를 초과하면 Hot-key로 간주합니다.
* **Guard Phase:** 승격 직후 일정 기간(가드 구간) 동안은 트래픽을 분산하지 않고 주 노드로만 보내, 대체 노드의 캐시 Warm-up 시간을 보장합니다.

### 2) 윈도우 기반 스위칭 (Window-based Switching)
* 가드 구간이 끝나면 윈도우 크기(W) 단위로 라우팅 경로를 교차합니다.
* **짝수 구간:** 대체 노드로 분산 / **홀수 구간:** 주 노드로 복귀
* 이를 통해 별도의 부하 감지 서버 없이도 두 노드 간의 트래픽을 1:1로 수렴시킵니다.

### 3) 비교 대상 (Baselines)
* **Consistent Hashing (CH):** 표준 링 기반 해싱 (가상 노드 포함)
* **Weighted CH (WCH):** 노드 성능에 따른 가중치 적용 방식
* **Rendezvous Hashing (HRW):** 최고 랜덤 가중치 해싱
* **Dynamic Hot-key Aware Scalable Hashing (D-HASH):** 제안하는 동적 라우팅 기법


## 3. 실험 환경

* **하드웨어:** Intel Core i5-1340P, 16GB RAM, Docker (WSL2)
* **소프트웨어:** Redis 7.4.2 (라우팅 로직 검증을 위해 클러스터 모드 Off)
* **데이터셋:**
    1.  **NASA HTTP Logs:** 트래픽 쏠림이 매우 심한 환경 (High Skew)
    2.  **eBay Auction Logs:** 트래픽이 비교적 고른 환경 (Low Skew)
* **파라미터 설정:**
    * Replication Factor = 2
    * Threshold (T) = 300
    * Window (W) = 배치 크기와 동일하게 설정 (Pipeline 최적화)


## 4. 프로젝트 구조

~~~bash
dhash-routing-evaluation
├── src
│   ├── dhash_experiments
│   │   ├── algorithms.py   # 알고리즘 라우팅 로직 구현
│   │   ├── bench.py        # 벤치마크 실행 및 메트릭 측정
│   │   └── workloads.py    # Zipfian 워크로드 생성기
├── Dockerfile.runner       # Redis & Python 실행 환경
├── docker-compose.yml      # 컨테이너 오케스트레이션
└── requirements.txt        # 의존성 패키지 (mmh3, numpy, redis)
~~~


## 5. 실행 방법

### 1) 벤치마크 실행
~~~bash
# 이미지 빌드 및 시뮬레이션 시작
docker-compose up --build
~~~

### 2) 결과 확인
~~~bash
# 실행 로그에서 처리량(Throughput) 및 지연시간(Latency) 확인
docker-compose logs -f runner
~~~


## 6. 실험 결과


### 1) NASA 데이터셋 (High Skew)
트래픽 쏠림이 심한 환경에서 D-HASH는 기본 CH 대비 부하 표준편차(Load Stddev)를 약 26.7% 감소시키며, 시스템 안정성을 크게 높였습니다.

| 알고리즘 | 처리량 (ops/s) | 평균 지연시간 (ms) | P99 지연시간 (ms) | 부하 표준편차 (낮을수록 좋음) |
| :--- | :--- | :--- | :--- | :--- |
| **CH** | 159,608 | 0.016 | 0.078 | **725,757** |
| **WCH** | 156,804 | 0.016 | 0.076 | 726,973 |
| **HRW** | 153,473 | 0.018 | 0.083 | 623,144 |
| **D-HASH** | **159,927** | **0.018** | **0.078** | **531,824** |

> **분석:** D-HASH는 핫키 트래픽을 효과적으로 분산하여, 특정 노드에 부하가 집중되는 현상을 막았습니다.

### 2) eBay 데이터셋 (Low Skew)
트래픽이 비교적 고르게 분포된 환경에서도 D-HASH는 오버헤드 없이 CH보다 높은 처리량을 기록했습니다.

| 알고리즘 | 처리량 (ops/s) | 평균 지연시간 (ms) | P99 지연시간 (ms) | 부하 표준편차 |
| :--- | :--- | :--- | :--- | :--- |
| **CH** | 183,629 | 0.015 | 0.061 | 258 |
| **D-HASH** | **193,020** | **0.015** | **0.062** | **258** |


## 7. 결론

본 연구를 통해 제안된 D-HASH는 다음과 같은 성과를 입증했습니다.

1. 핫키 발생 시 부하 불균형을 획기적으로 줄여 시스템 전체의 리소스 활용도를 높였습니다.
2. 트래픽 패턴(Skew)에 상관없이 안정적인 성능을 유지하며, 오버헤드가 거의 없습니다.
3. 중앙 관리 서버 없이 클라이언트 사이드 로직만으로 동작하므로, 실제 상용 분산 시스템에 즉시 적용 가능합니다.
