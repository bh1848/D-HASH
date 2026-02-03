# ⚖️ D-HASH: Dynamic Hot-key Aware Scalable Hashing

<p>
  <b>"분산 캐시 시스템의 Hot-key 병목 현상을 동적 라우팅으로 해결"</b><br>
  Consistent Hashing 기반 Redis 클러스터의 부하 불균형을 런타임에 해소하는 경량 알고리즘
</p>

<img src="https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white"/><img src="https://img.shields.io/badge/Redis-DC382D?style=flat-square&logo=redis&logoColor=white"/><img src="https://img.shields.io/badge/Docker-2496ED?style=flat-square&logo=docker&logoColor=white"/><img src="https://img.shields.io/badge/License-MIT-green?style=flat-square"/>
<br>
<a href="https://doi.org/10.3837/tiis.2026.xx.xxx"><img src="https://img.shields.io/badge/SCIE_Paper-KSII_TIIS_2026-blue?style=for-the-badge&logo=googlescholar&logoColor=white"/></a>


<br>

> **논문:** D-HASH: Dynamic Hot-key Aware Scalable Hashing for Load Balancing in Distributed Cache Systems  
> **저자:** 방혁, 전상훈 (수원대학교 정보보호학과)  
> **게재:** KSII TIIS 2026 (SCIE 등재)    
> [**[📄 Read Paper]**](https://doi.org/10.3837/tiis.2026.xx.xxx)

<br>

## 🎯 프로젝트 핵심 요약

| Category | Description |
|:---:|:---|
| **Problem** | 특정 키(Hot-key)로 트래픽 집중 시 발생하는 **단일 노드 과부하** |
| **Solution** | Client-side **윈도우 기반 동적 라우팅** (별도 프록시 서버 ❌) |
| **Impact** | 기존 대비 **부하 편차 33.8% 감소** (안정성 확보) |
| **Stack** | Python 3.11, Redis 7.4.2, Docker |

<br>

## 📋 목차
1. [프로젝트 배경](#1-프로젝트-배경)
2. [기술 아키텍처](#2-기술-아키텍처)
3. [핵심 알고리즘](#3-핵심-알고리즘)
4. [실험 환경](#4-실험-환경)
5. [실행 방법](#5-실행-방법)
6. [실험 결과](#6-실험-결과)
7. [트러블 슈팅](#7-트러블-슈팅)
8. [한계 및 향후 과제](#8-한계-및-향후-과제)

<br>

## 1. 프로젝트 배경

### 🚨 문제 상황
실시간 서비스에서 `인기 게시글`이나 `실시간 검색어` 같은 콘텐츠에 요청이 폭주하면, 해당 데이터를 담당하는 **단일 캐시 노드**에만 부하가 집중되는 **Hot-key (Data Skewness)** 문제가 발생합니다.

* **Consistent Hashing의 한계**: 키를 노드에 균등하게 나누어 담을 수는 있지만, **특정 키 자체의 트래픽이 급증**하는 것은 막을 수 없습니다.
* **Real World Case**: NASA 웹 로그 분석 결과, **상위 1%의 키가 전체 요청의 40% 이상**을 차지하는 쏠림 현상이 관측되었습니다.

### 💡 해결 목표
> **"기존 서버 인프라를 변경하지 않고, 클라이언트(SDK) 레벨에서 Hot-key 트래픽만 스마트하게 분산하자."**

<br>

## 2. 기술 아키텍처

<div align="center">
  <img src="images/dhash_architecture.png" alt="System Architecture" width="80%">
  <p><em>[그림 1] D-HASH 전체 시스템 구조도</em></p>
</div>

### 🏗 시스템 구성
1.  **Base Layer**: 표준 Consistent Hashing 링 (가상 노드 포함)
2.  **Detection Layer**: 클라이언트 사이드 카운터 (Hot-key 실시간 감지)
3.  **Routing Layer**: 윈도우 기반 동적 스위칭 로직

### 🔄 데이터 흐름 (Data Flow)
1.  **Normal Key**: `Primary Node`로 직접 라우팅 (기존 방식)
2.  **Hot-key (Read)**: `Primary` ↔ `Alternate Node` 교차 분산 (1:1 Load Balancing)
3.  **Hot-key (Write)**: `Primary Node` 고정 (Strong Consistency 보장)

<br>

## 3. 핵심 알고리즘

### 3-1. Hot-key 감지 및 승격 (Detection)
~~~python
# LRU 기반 카운터로 빈도 측정
if read_count[key] > THRESHOLD:
    promote_to_hotkey(key)  # Hot-key로 승격
    enter_guard_phase(key)  # Warm-up (예열) 시간 보장
~~~
* **Threshold ($T$)**: 300회 (Ablation Study를 통해 도출한 최적값)
* **Guard Phase**: 승격 직후 Alternate Node의 캐시 미스(Cache Miss)를 방지하기 위한 예열 구간

### 3-2. 윈도우 기반 트래픽 분산 (Window Routing)
~~~python
# 요청 횟수 기반의 결정론적(Deterministic) 라우팅
window_id = request_count // WINDOW_SIZE

if window_id % 2 == 0:
    route_to_alternate_node(key) # 짝수 윈도우: 대체 노드
else:
    route_to_primary_node(key)   # 홀수 윈도우: 메인 노드
~~~
* **Window Size ($W$)**: 1,000 requests
* **Effect**: 별도의 로드 밸런서 없이 클라이언트 코드만으로 **1:1 부하 분산** 달성

### 3-3. 알고리즘 비교
| Algorithm | Hot-key 대응 | Overhead | Feature |
|:---|:---:|:---:|:---|
| **Consistent Hashing (CH)** | ❌ | Low | 표준, 불균형 취약 |
| **Weighted CH** | 🔺 | Low | 정적 가중치 (동적 대응 불가) |
| **Rendezvous Hashing** | ❌ | High | 재해싱 비용 높음 |
| **D-HASH (This Project)** | ✅ | Medium | **실시간 동적 분산** |

<br>

## 4. 실험 환경

* **Host**: Intel Core i5-1340P, 16GB RAM
* **Container**: Docker Compose (WSL2)
* **Middleware**: Redis 7.4.2 (Cluster Mode Off - 라우팅 검증 목적)
* **Client**: Python 3.11 + `redis-py` + `ThreadPoolExecutor`
* **Workload**:
    * NASA HTTP Logs (High Skew)
    * Synthetic Zipfian Generator ($\alpha=1.5$)

<br>

## 5. 실행 방법

### 5-1. 환경 구성 및 실행
~~~bash
# 1. 저장소 클론
git clone https://github.com/yourusername/dhash.git
cd dhash

# 2. Docker 컨테이너 빌드 및 실행 (Redis + App)
docker-compose up --build
~~~

### 5-2. 실시간 로그 모니터링
~~~bash
# 벤치마크 러너 로그 확인
docker-compose logs -f runner
~~~

### 5-3. 결과 데이터 확인
~~~bash
# 실험 결과는 results 폴더에 CSV로 저장됩니다
ls -l results/

# 주요 결과 파일:
# - synthetic_zipf_results.csv  (메인 벤치마크)
# - synthetic_ablation.csv      (임계값 민감도 분석)
~~~

<br>

## 6. 실험 결과

### 📊 1. NASA Dataset (High Skew)
> 실제 웹 로그 데이터를 기반으로 한 실험 결과입니다.

| Algorithm | Throughput (ops/s) | Load Stddev | Improvement |
|:---|:---:|:---:|:---:|
| Consistent Hashing | 159,608 | 725,757 | - |
| **D-HASH** | **159,927** | **531,824** | **🔻 26.7% 개선** |

**👉 분석**: Throughput 손실 없이 노드 간 부하 편차를 **26.7%** 줄여 시스템 안정성을 확보했습니다.

### 📊 2. Synthetic Zipf ($\alpha=1.5$)
> 더 극단적인 데이터 쏠림 환경에서의 스트레스 테스트입니다.

| Algorithm | Throughput (ops/s) | Load Stddev | Improvement |
|:---|:---:|:---:|:---:|
| Consistent Hashing | 179,902 | 49,944 | - |
| **D-HASH** | **167,092** | **33,054** | **🔻 33.8% 개선** |

**👉 Insight**: 약 7%의 처리량 오버헤드가 발생했으나, 장애 위험의 척도인 부하 편차는 **33.8%** 나 대폭 감소시켰습니다.

<br>

## 7. 트러블 슈팅

> 💡 개발 과정에서 마주친 주요 기술적 이슈와 해결 과정을 기술 블로그에 상세히 기록했습니다.

| Issue | Solution | Report |
|:---|:---|:---:|
| **성능 최적화** | Python 해시 오버헤드 → **xxHash64** 및 `__slots__` 도입으로 해결 | [🔗 View](Velog링크1) |
| **Cold Start** | 승격 직후 Latency Spike → **Guard Phase(예열)** 설계 | [🔗 View](Velog링크2) |
| **데이터 정합성** | 분산 환경 동기화 문제 → **Write-Primary** 정책 수립 | [🔗 View](Velog링크3) |
| **테스트 병목** | Client RTT 한계 → **ThreadPoolExecutor** 비동기 테스트 | [🔗 View](Velog링크4) |
| **실험 신뢰성** | GC 노이즈 발생 → **Explicit GC** 및 시드 고정 | [🔗 View](Velog링크5) |

<br>

## 8. 한계 및 향후 과제

### 🚧 Current Limitations
1.  **Distributed Global View 부재**: 각 클라이언트가 독립적으로 카운팅하므로, 다수 클라이언트 환경에서 핫키 감지 시차가 발생할 수 있습니다.
2.  **Demotion 로직 미구현**: 트래픽이 식은 핫키를 다시 일반 키로 돌리는 로직이 없어, 장기적으로 캐시 효율이 저하될 수 있습니다.
3.  **네트워크 시뮬레이션 제약**: Docker 가상 네트워크 환경으로 인해 실제 물리 네트워크의 Jitter나 패킷 손실을 완벽히 반영하지 못했습니다.


### 🚀 Future Roadmap
* **Adaptive Demotion**: `Time-decay` 알고리즘을 도입하여 사용량 감소 시 자동 강등 구현.
* **Gossip Protocol**: 클라이언트 간 핫키 정보를 비동기적으로 공유하여 전역 감지 속도 개선.
* **Redis Cluster Support**: 클러스터 모드에서도 슬롯 마이그레이션 없이 동작하도록 추상화 레이어 설계.
* **Cloud Native Test**: AWS ElastiCache 환경에서 Multi-AZ 지연 시간 검증.
