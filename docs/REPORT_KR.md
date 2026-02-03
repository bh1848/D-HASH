# ⚖️ D-HASH: 분산 캐시 로드 밸런싱을 위한 동적 Hot-key 대응 해싱

> **"분산 캐시 시스템의 Hot-key 병목 현상을 해결하는 클라이언트 사이드 동적 라우팅 알고리즘"**

<p>
  <img src="https://img.shields.io/badge/Python-3.11-3776AB?style=flat-square&logo=python&logoColor=white"/>
  <img src="https://img.shields.io/badge/Redis-7.4.2-DC382D?style=flat-square&logo=redis&logoColor=white"/>
  <img src="https://img.shields.io/badge/Docker-2496ED?style=flat-square&logo=docker&logoColor=white"/>
  <img src="https://img.shields.io/badge/License-MIT-green?style=flat-square"/>
</p>

## 📄 논문 정보 (Paper Info)
* **Title**: D-HASH: Dynamic Hot-key Aware Scalable Hashing for Load Balancing in Distributed Cache Systems
* **Authors**: 방혁, 전상훈 (수원대학교 정보보호학과)
* **Journal**: KSII Transactions on Internet and Information Systems (TIIS), 2026 (SCIE)
* **DOI**: [10.3837/tiis.2026.xx.xxx](https://doi.org/10.3837/tiis.2026.xx.xxx)

<br>

## 🎯 프로젝트 핵심 요약

| Category | Description |
|:---:|:---|
| **Problem** | Consistent Hashing 환경에서 특정 키(Hot-key)로 트래픽 집중 시 발생하는 **단일 노드 과부하** |
| **Solution** | 클라이언트 사이드 **윈도우 기반 동적 라우팅** (Proxy-less Architecture) |
| **Impact** | 표준 Consistent Hashing 대비 **부하 표준편차(Load Stddev) 33.8% 감소** |
| **Stack** | Python 3.11, Redis, Consistent Hashing, Window-based Routing |

<br>

## 📋 목차
1. [프로젝트 소개](#1-프로젝트-소개)
2. [시스템 아키텍처](#2-시스템-아키텍처)
3. [핵심 알고리즘](#3-핵심-알고리즘)
4. [실험 환경](#4-실험-환경)
5. [실행 방법](#5-실행-방법)
6. [실험 결과](#6-실험-결과)
7. [트러블 슈팅](#7-트러블-슈팅)
8. [한계 및 향후 과제](#8-한계-및-향후-과제)

<br>

## 1. 프로젝트 소개

### 배경 (Background)
대규모 분산 캐시 시스템에서 Consistent Hashing은 데이터 분산 저장의 표준으로 사용되지만, **Data Skewness(데이터 쏠림)** 문제를 근본적으로 해결하지 못합니다. 실제 NASA 웹 로그 분석 결과, 상위 1%의 키가 전체 요청의 40% 이상을 차지하는 현상이 관측되었습니다. 이는 특정 노드의 과부하(Overload)와 전체 시스템의 성능 저하로 이어집니다.

### 목표 (Objective)
기존 서버 인프라 변경이나 별도의 프록시 서버 도입 없이, **클라이언트(SDK) 레벨**에서 Hot-key를 실시간으로 감지하고 트래픽을 동적으로 분산 처리하는 경량 알고리즘(D-HASH)을 구현합니다.

<br>

## 2. 시스템 아키텍처

![System Architecture](images/dhash_architecture.png)
*(D-HASH 전체 시스템 구조도)*

### 구성 요소
1.  **Base Layer**: 표준 Consistent Hashing 링 (Virtual Nodes 적용).
2.  **Detection Layer**: 클라이언트 내장 LRU 카운터를 통한 실시간 빈도 측정.
3.  **Routing Layer**: 임계값 초과 시 동작하는 윈도우 기반 스위칭 로직.

### 데이터 흐름 전략
* **Normal Key**: `Primary Node`로 해싱 및 라우팅 (기존 방식 유지).
* **Hot-key (Read)**: `Primary`와 `Alternate Node`로 트래픽 1:1 분산.
* **Hot-key (Write)**: 데이터 정합성(Strong Consistency) 보장을 위해 `Primary Node`로 고정.

<br>

## 3. 핵심 알고리즘

### 3-1. 감지 및 승격 (Detection & Promotion)
요청 빈도가 임계값($T$)을 초과하면 해당 키를 Hot-key로 승격시킵니다. 승격 직후 발생할 수 있는 Cache Miss를 방지하기 위해 일정 기간(Guard Phase) 예열 과정을 거칩니다.

~~~python
# LRU Counter Logic
if read_count[key] > THRESHOLD:
    promote_to_hotkey(key)  # Hot-key 승격
    enter_guard_phase(key)  # Warm-up (Alternate Node 예열)
~~~

### 3-2. 윈도우 기반 라우팅 (Window Routing)
Hot-key에 대한 요청은 윈도우 크기($W$) 단위로 Primary Node와 Alternate Node에 교차 분배됩니다.

~~~python
# Deterministic Routing Logic
window_id = request_count // WINDOW_SIZE

if window_id % 2 == 0:
    route_to_alternate_node(key) # 짝수 윈도우: 대체 노드
else:
    route_to_primary_node(key)   # 홀수 윈도우: 메인 노드
~~~
* **Threshold ($T$)**: 300 ops (Ablation Study 최적값)
* **Window Size ($W$)**: 1,000 ops

<br>

## 4. 실험 환경

* **H/W**: Intel Core i5-1340P, 16GB RAM
* **S/W**: Docker (WSL2), Redis 7.4.2
* **Client**: Python 3.11 (`redis-py` extended)
* **Workloads**:
    1.  **NASA HTTP Logs**: 실제 웹 트래픽 기반 데이터셋.
    2.  **Synthetic Zipfian**: 파라미터 $\alpha=1.5$의 고강도 쏠림 데이터셋.

<br>

## 5. 실행 방법

### 사전 요구사항
* Docker & Docker Compose

### 벤치마크 실행
~~~bash
# 1. 저장소 클론
git clone https://github.com/yourusername/dhash.git
cd dhash

# 2. 컨테이너 빌드 및 실행 (Redis Nodes + Benchmark Client)
docker-compose up --build

# 3. 실시간 로그 확인
docker-compose logs -f runner
~~~

### 결과 확인
실험 결과는 `./results` 디렉토리에 CSV 포맷으로 저장됩니다.
* `synthetic_zipf_results.csv`: 메인 성능 지표
* `synthetic_ablation.csv`: 파라미터 민감도 분석 결과

<br>

## 6. 실험 결과

### 6-1. NASA Dataset (Real-world)
| Algorithm | Throughput (ops/s) | Load Stddev (낮을수록 좋음) | Improvement |
|:---|:---:|:---:|:---:|
| Consistent Hashing | 159,608 | 725,757 | - |
| **D-HASH** | **159,927** | **531,824** | **🔻 26.7% 개선** |

### 6-2. Synthetic Zipf ($\alpha=1.5$)
| Algorithm | Throughput (ops/s) | Load Stddev (낮을수록 좋음) | Improvement |
|:---|:---:|:---:|:---:|
| Consistent Hashing | 179,902 | 49,944 | - |
| **D-HASH** | **167,092** | **33,054** | **🔻 33.8% 개선** |

**결론**: D-HASH는 약 7%의 Throughput 오버헤드로 노드 간 부하 편차를 33.8% 감소시켜 시스템 안정성을 크게 향상시켰습니다.

<br>

## 7. 트러블 슈팅

| Issue | Cause | Solution | Tech Blog |
|:---:|:---|:---|:---:|
| **Hashing Overhead** | Python 내장 해시 함수의 속도 한계 | **xxHash64** 라이브러리 교체 및 `__slots__` 적용으로 메모리 최적화 | [🔗 Velog](#) |
| **Cold Start Spike** | Hot-key 승격 직후 Alternate Node에 데이터 부재 | **Guard Phase** 도입: 승격 초기에는 Write를 병행하여 Cache Warming 수행 | [🔗 Velog](#) |
| **Write Consistency** | 분산된 노드 간 데이터 불일치 | **Write-Primary** 정책: 쓰기 작업은 항상 Primary Node에서 수행 | [🔗 Velog](#) |
| **Test Accuracy** | 동기식(Sync) 요청에 의한 RTT 병목 | **ThreadPoolExecutor**를 활용한 비동기 부하 테스트 환경 구축 | [🔗 Velog](#) |

<br>

## 8. 한계 및 향후 과제

### 한계점 (Limitations)
1.  **Local View**: 각 클라이언트가 독립적으로 카운팅하므로, 전체 클러스터 관점의 Hot-key 감지에 시차 발생.
2.  **No Demotion**: 트래픽이 감소한 Hot-key를 일반 키로 복귀시키는 로직 미구현.
3.  **Simulation Constraints**: Docker 가상 네트워크 환경으로 실제 네트워크 지연(Jitter) 반영 미흡.

### 향후 계획 (Future Work)
* **Adaptive Demotion**: Time-decay 알고리즘을 적용한 자동 강등 로직 구현.
* **Gossip Protocol**: 클라이언트 간 Hot-key 메타데이터 비동기 공유.
* **Cloud Verification**: AWS ElastiCache 환경에서의 Multi-AZ 지연 시간 검증.
