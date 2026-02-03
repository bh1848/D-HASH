# D-HASH: Dynamic Hot-key Aware Scalable Hashing

> **"분산 캐시 시스템의 Hot-key 병목 현상을 동적 라우팅으로 해결"**  
> Consistent Hashing 기반 Redis 클러스터에서 특정 키로 트래픽이 몰릴 때, 런타임에 자동으로 부하를 분산하는 경량 알고리즘을 설계·검증한 프로젝트입니다.

**📝 논문:** D-HASH: Dynamic Hot-key Aware Scalable Hashing for Load Balancing in Distributed Cache Systems  
**저자:** 방혁, 전상훈 (수원대학교 정보보호학과)  
**게재:** KSII TIIS 2026 (SCIE 등재) [**📄 Paper**](https://doi.org/10.3837/tiis.2026.xx.xxx)

<br/>

## 🎯 프로젝트 핵심 요약

| 항목 | 내용 |
|------|------|
| **해결한 문제** | 특정 키로 트래픽 집중 시 단일 노드 과부하 (Hot-key 문제) |
| **핵심 성과** | 부하 편차 **33.8% 감소** (처리량 유지하며 안정성 확보) |
| **기술 스택** | Python, Redis 7.4.2, Docker, xxHash, ThreadPoolExecutor |
| **알고리즘 특징** | Client-side 경량 라우팅 (별도 서버 불필요) |

<br/>

## 📋 목차
1. [프로젝트 배경](#1-프로젝트-배경)
2. [기술 아키텍처](#2-기술-아키텍처)
3. [핵심 알고리즘](#3-핵심-알고리즘)
4. [실험 환경](#4-실험-환경)
5. [실행 방법](#5-실행-방법)
6. [실험 결과](#6-실험-결과)
7. [트러블 슈팅](#7-트러블-슈팅)
8. [배운 점과 개선 방향](#8-배운-점과-개선-방향)

<br/>

## 1. 프로젝트 배경

### 문제 상황
실시간 서비스에서 인기 콘텐츠(핫한 게시글, 실시간 검색어 등)로 요청이 몰리면, 해당 데이터를 담당하는 캐시 노드 하나에만 부하가 집중됩니다.

- **기존 Consistent Hashing의 한계:** 키를 노드에 균등 분산하지만, 특정 키의 트래픽이 급증하면 그 키를 담당하는 노드만 과부하 발생
- **실제 사례:** NASA 웹 로그 분석 결과, 상위 1% 키가 전체 요청의 40% 이상 차지

### 해결 목표
"기존 시스템 구조를 건드리지 않고, 클라이언트 레벨에서 Hot-key 트래픽만 동적으로 분산"

<br/>

## 2. 기술 아키텍처

![아키텍처 다이어그램](images/dhash_architecture.png)

### 시스템 구성
- **Base Layer:** Consistent Hashing 링 (가상 노드 포함)
- **Detection Layer:** 클라이언트 사이드 카운터 (Hot-key 실시간 감지)
- **Routing Layer:** 윈도우 기반 동적 스위칭 로직

### 데이터 흐름
1. **일반 키:** Primary Node로 직접 라우팅 (기존 CH와 동일)
2. **Hot-key (읽기):** Primary ↔ Alternate Node 교차 분산
3. **Hot-key (쓰기):** 항상 Primary Node (데이터 일관성 보장)

<br/>

## 3. 핵심 알고리즘

### 3-1. Hot-key 감지 및 승격
~~~python
if read_count[key] > THRESHOLD:
    promote_to_hotkey(key)
    enter_guard_phase(key)  # Warm-up 시간 보장
~~~

- **임계값(T):** 300회 (실험적으로 최적화)
- **Guard Phase:** 승격 직후 대체 노드의 캐시 준비 시간 확보

### 3-2. 윈도우 기반 트래픽 분산
~~~python
window_id = request_count // WINDOW_SIZE
if window_id % 2 == 0:
    route_to_alternate_node(key)
else:
    route_to_primary_node(key)
~~~

- **윈도우 크기(W):** 1,000 requests
- **효과:** 별도 모니터링 서버 없이 1:1 부하 분산 달성

### 3-3. 비교 대상 알고리즘
| 알고리즘 | 설명 | 단점 |
|---------|------|------|
| **Consistent Hashing (CH)** | 표준 링 기반 해싱 | Hot-key 대응 불가 |
| **Weighted CH (WCH)** | 노드 성능 기반 가중치 | 동적 트래픽 변화 대응 느림 |
| **Rendezvous Hashing (HRW)** | 최고 랜덤 가중치 방식 | 재해싱 오버헤드 큼 |
| **D-HASH (제안)** | 동적 런타임 분산 | ✅ 실시간 적응 가능 |

<br/>

## 4. 실험 환경

### 하드웨어 및 소프트웨어
- **Host:** Intel Core i5-1340P, 16GB RAM
- **Container:** Docker Compose (WSL2 기반)
- **Cache:** Redis 7.4.2 (Cluster Mode Off - 라우팅 검증 목적)
- **Client:** Python 3.11 + redis-py + ThreadPoolExecutor

### 워크로드 생성
- **논문 실험:** NASA HTTP Logs (High Skew), eBay Auction Logs (Low Skew)
- **재현 실험:** Synthetic Zipfian Generator (α=1.5, 재현성 확보)

### 주요 파라미터
| 파라미터 | 값 | 선정 이유 |
|---------|---|----------|
| Replication Factor | 2 | 읽기 부하 분산 최소 단위 |
| Threshold (T) | 300 | Ablation Study 결과 최적값 |
| Window (W) | 1,000 | Pipeline 배치 크기와 동기화 |

<br/>

## 5. 실행 방법

### 5-1. 환경 구성
~~~bash
# 저장소 클론
git clone https://github.com/yourusername/dhash.git
cd dhash

# Docker 이미지 빌드 및 실행
docker-compose up --build
~~~

### 5-2. 실시간 로그 확인
~~~bash
# 벤치마크 진행 상황 모니터링
docker-compose logs -f runner
~~~

### 5-3. 결과 확인
~~~bash
# 결과 파일 위치: results/ 폴더
ls results/

# 주요 결과 파일
# - synthetic_zipf_results.csv       (Main 실험 결과)
# - synthetic_ablation.csv           (Threshold 민감도 분석)
# - synthetic_pipeline_sweep.csv     (배치 크기 최적화)
~~~

<br/>

## 6. 실험 결과

### 6-1. 논문 검증 결과 (NASA/eBay 실제 로그)

#### NASA Dataset (High Skew 환경)
| Algorithm | Throughput (ops/s) | Load Stddev | 개선율 |
|-----------|-------------------|-------------|--------|
| Consistent Hashing | 159,608 | 725,757 | - |
| **D-HASH** | **159,927** | **531,824** | **🔻 26.7%** |

**분석:** 처리량을 유지하면서 부하 편차를 **26.7% 감소**시켜 시스템 안정성 확보

#### eBay Dataset (Low Skew 환경)
| Algorithm | Throughput (ops/s) | 결과 |
|-----------|-------------------|------|
| Consistent Hashing | 234,109 | - |
| **D-HASH** | **233,412** | **오버헤드 0.3%** |

**분석:** Hot-key가 없는 환경에서는 로직이 비활성화되어 기존 CH와 동등한 성능 유지

### 6-2. 재현 실험 결과 (Synthetic Zipf α=1.5)

**더 극단적인 High-Skew 환경**에서의 스트레스 테스트:

| Algorithm | Throughput (ops/s) | Load Stddev | 개선율 |
|-----------|-------------------|-------------|--------|
| Consistent Hashing | 179,902 | 49,944 | - |
| **D-HASH** | **167,092** | **33,054** | **🔻 33.8%** |

### 핵심 인사이트
✅ **안정성 우선 설계:** 처리량 7% 감소는 있지만, 부하 편차를 33.8% 줄여 노드 장애 위험 제거  
✅ **일관된 성능:** NASA 실험(26.7%)과 재현 실험(33.8%) 모두에서 유사한 개선 경향 확인  
✅ **실용성 검증:** 논문 이론이 실제 구현에서도 동작함을 증명

<br/>

## 7. 트러블 슈팅

### 7-1. 라우팅 오버헤드 최적화

**문제**  
모든 요청마다 해시 연산 + 카운팅 로직 수행 → 처리량 저하 우려

**해결**  
- Python 기본 `hash()` 대신 **xxHash64** 적용 (2배 빠른 연산)
- `__slots__` 사용으로 객체 메모리 접근 속도 최적화
- 불필요한 딕셔너리 조회 최소화

**결과**  
기존 CH 대비 처리량 93% 유지 (오버헤드 7%로 억제)

### 7-2. Cold Start Latency Spike 방지

**문제**  
Hot-key 승격 직후 대체 노드로 트래픽 분산 → **Cache Miss 급증** → DB 부하 순간 증가

**해결**  
Guard Phase 도입: 승격 후 일정 기간(W × 2) 동안 Primary만 사용하여 Alternate의 Warm-up 시간 확보

**결과**  
분산 시작 시점의 Latency Spike 제거, 부드러운 전환(Soft Landing) 달성

### 7-3. 데이터 정합성 보장

**문제**  
Hot-key를 여러 노드에 분산 시, Write 동기화 비용 과다 발생

**해결**  
- **Write:** 항상 Primary Node로 고정 (Strong Consistency)
- **Read:** Hot-key만 동적 분산 (성능 최적화)

**결과**  
복잡한 합의 알고리즘 없이 일관성 확보

### 7-4. Client-side Bottleneck 제거

**문제**  
Single-thread 벤치마크 시 RTT 대기로 인한 처리량 정체

**해결**  
`ThreadPoolExecutor` 도입하여 멀티스레드 비동기 요청 생성

**결과**  
Redis 서버 처리 능력을 최대한 활용 (Throughput 2배 향상)

### 7-5. GC로 인한 Latency Noise 제거

**문제**  
반복 실험(repeats) 시 후반부로 갈수록 지연시간 급증

**해결**  
각 실험 단계 종료 시 `gc.collect()` 명시적 호출 + 난수 시드 재설정

**결과**  
재현 가능한 안정적인 실험 환경 구축

<br/>

## 8. 배운 점과 개선 방향

### 8-1. 이 프로젝트를 통해 배운 것

- **Trade-off 사고:** 처리량 vs 안정성, 복잡도 vs 효과성의 균형점 찾기
- **점진적 개선:** Guard Phase, Window Switching 등 단계별 최적화 전략
- **데이터 기반 의사결정:** Ablation Study로 파라미터(T, W) 실험적 검증

- **성능 최적화:** 프로파일링 → 병목 지점 특정 → 해시 알고리즘/메모리 구조 개선
- **재현 가능한 실험:** Docker 환경 격리 + 시드 고정 + GC 제어
- **멀티스레드 프로그래밍:** ThreadPoolExecutor로 실제 부하 시뮬레이션

### 8-2. 한계점

**1. 시뮬레이션 환경의 제약**  
Docker 기반 단일 호스트 환경으로 실제 물리 네트워크 지연/패킷 손실 미반영

**2. Demotion 로직 부재**  
Hot-key → Cold-key 전환 시 자동 해제 메커니즘 없음 (캐시 Locality 저하 가능)

**3. 클라이언트 분산 환경**  
각 클라이언트가 독립 카운터 유지 → 다수 클라이언트 환경에서 감지 지연 발생 가능

### 8-3. 향후 개선 방향

- Time-decay 알고리즘: 일정 시간 미사용 시 카운트 감소 → 자동 Demotion
- Redis Cluster Mode 지원: Gossip Protocol과 통합

- Multi-AZ 클라우드 환경 배포 (AWS ElastiCache 등)
- Memcached, ScyllaDB 등 다른 스토리지 적용 검증

- ML 기반 Hot-key 예측: 트래픽 패턴 학습으로 사전 분산
- Adaptive Threshold: 시스템 부하에 따라 T 값 동적 조정
