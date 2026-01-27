# ⚖️ D-HASH: Dynamic Hot-key Aware Scalable Hashing

> **관련 논문:** [D-HASH: Dynamic Hot-key Aware Scalable Hashing for Load Balancing in Distributed Cache Systems (TIIS Submitted)]
> **저자:** 방혁, 전상훈

대규모 분산 캐시 시스템(Redis Cluster)에서 **Hot-Key(인기 키)**로 인해 발생하는 부하 불균형 문제를 해결하기 위해 고안한 새로운 라우팅 알고리즘 프로젝트입니다.
기존 Consistent Hashing(CH)의 한계를 넘어, **런타임 트래픽 분석을 통해 동적으로 부하를 분산**시켰을 때 클러스터 안정성이 얼마나 개선되는지 수치로 검증했습니다.

## 📋 목차
1. [개요](#1-개요)
2. [실험 설계](#2-실험-설계)
3. [실험 환경](#3-실험-환경)
4. [프로젝트 구조](#4-프로젝트-구조)
5. [실행 방법](#5-실행-방법)
6. [실험 결과](#6-실험-결과)
7. [결론](#7-결론)



## 1. 개요

분산 시스템에서 "특정 키에 트래픽이 쏠리는 문제(Hot-Key)"는 단순한 서버 증설(Scale-out)만으로는 해결되지 않습니다.
이번 연구에서는 무거운 중앙 관리 서버 없이, 클라이언트 사이드 라우팅만으로 **Hot-Key 부하를 자동으로 감지하고 분산**하는 D-HASH 기법을 구현하고, 기존 알고리즘 대비 성능 이점을 증명하고자 했습니다.

### 기존 방식(CH) vs 제안 방식(D-HASH)

| Consistent Hashing (CH) | D-HASH (Proposed) |
| :---: | :---: |
| ![CH Ring](./images/ch_ring.png) | ![D-HASH Routing](./images/dhash_routing.png) |
| **정적 라우팅**<br>Key는 항상 정해진 1개의 노드로만 감 | **동적 라우팅**<br>Hot-Key는 Primary와 Alternate 노드가 나누어 처리 |

### 실험 아키텍처 (Architecture Overview)
변수 통제를 위해 동일한 Python 클라이언트 내에서 알고리즘만 교체하며 테스트했습니다.

> * **알고리즘 비교:** `CH`, `WCH(Weighted)`, `HRW(Rendezvous)`, `D-HASH` 4가지 기법 비교
> * **워크로드 재현:** NASA HTTP 로그 및 eBay 경매 데이터를 사용하여 실제 트래픽 패턴(Zipfian Skew)을 시뮬레이션



## 2. 핵심 설계

단순한 알고리즘 구현을 넘어, **실제 상용 환경에서의 적용 가능성**과 **실험의 신뢰성**을 높이기 위한 엔지니어링 설계를 적용했습니다.

### 1) Deterministic Routing (상태 없는 라우팅)
* **목적:** 별도의 메타데이터 서버(Lookup Table) 없이 라우팅 경로를 결정하여 조회 속도 저하 방지
* **구현:** `algorithms.py`의 `get_node` 메서드에서 **Read Count**와 **보조 해시 함수**만으로 Alternate 노드를 수학적으로 계산해내도록 구현했습니다.

~~~python
# algorithms.py (핵심 로직 발췌)
def get_node(self, key, op="read"):
    # ... (생략)
    # Hot-Key 감지 시 윈도우 단위로 Primary/Alternate 교차 라우팅
    delta = max(0, cnt - self.T)
    epoch = (delta - self.W) // self.W
    return self.alt[key] if (epoch % 2 == 0) else self._primary_safe(key)
~~~

### 2) Experiment Pipeline (실험 자동화)
* **목적:** 다양한 파라미터($\alpha$ 값, 윈도우 크기 등) 변화에 따른 성능 추이를 일관되게 측정
* **구현:** `cli.py`를 통해 [파이프라인 최적화] → [마이크로 벤치마크] → [메인 성능 평가]로 이어지는 **단계별 실험 파이프라인**을 구축하여 재현성(Reproducibility)을 확보했습니다.



## 3. 실험 환경

* **Language:** Python 3.8+
* **Cache Engine:** Redis 7.4.2 (Docker Cluster)
* **Dataset:** NASA HTTP Access Logs, eBay Auction Data
* **Variables:** Zipfian Skew Parameter ($\alpha \in \{1.1, 1.3, 1.5\}$)
* **Metrics:** Throughput(ops/s), Tail Latency(P99), Load Standard Deviation



## 4. 프로젝트 구조

~~~bash
dhash_experiments/
├── algorithms.py    # 핵심 알고리즘 (CH, D-HASH 구현체)
├── bench.py         # 벤치마킹 로직 (Redis 연동 및 측정)
├── cli.py           # 실험 실행 엔트리포인트 (Main)
├── config.py        # 환경 설정 (Docker 노드 정보 등)
├── stages.py        # 실험 시나리오 (Pipeline, Ablation, Zipf)
└── workloads.py     # 데이터셋 파싱 및 워크로드 생성기
~~~



## 5. 실행 방법

**1. Redis 클러스터 구동 (Docker)**
~~~bash
# docker-compose.yml 기반 5개 노드 실행
docker-compose up -d
~~~

**2. 메인 성능 평가 (Main Benchmark)**
~~~bash
# Zipf 분포 기반 부하 테스트 수행
python -m dhash_experiments.cli --mode zipf --dataset ALL --repeats 10
~~~

**3. 오버헤드 검증 (Microbenchmark)**
~~~bash
# 알고리즘 자체 연산 비용 측정
python -m dhash_experiments.cli --mode microbench --repeats 10
~~~



## 6. 실험 결과

NASA 데이터셋($\alpha=1.5$) 기준 성능 비교 결과입니다.

### 성능 비교 그래프
> ![Result Graph](./images/result_graph.png)

### 상세 지표 요약

| Algorithm | Throughput (ops/s) | P99 Latency (ms) | Load Stddev (부하 표준편차) |
| :---: | :---: | :---: | :---: |
| **CH (Standard)** | 159,608 | 0.078 | 725,757 |
| **D-HASH (Proposed)** | **159,927** | **0.078** | **531,824 (▼ 27%)** |

### 결과 분석
* **부하 균형 개선:** D-HASH는 기존 CH 대비 노드 간 부하 편차(Standard Deviation)를 **약 27% 감소**시켜 특정 노드의 과부하를 효과적으로 해소했습니다.
* **Zero Overhead:** 복잡한 로직이 추가되었음에도 불구하고, 처리량(Throughput)과 지연 시간(Latency)에서 손해를 보지 않음을 입증했습니다.


## 7. 결론

### 연구의 한계
* **Network Latency:** Docker 컨테이너 간 통신 환경으로, 실제 IDC 간의 네트워크 지연(RTT) 변수는 완벽히 반영되지 않았습니다.
* **Client-Side Bottleneck:** 단일 클라이언트에서 부하를 생성했기에, 클라이언트 자체의 리소스 한계가 전체 처리량에 영향을 줄 수 있습니다.

### Insights
이번 프로젝트를 통해 도출한 결론은 다음과 같습니다.

1. **소프트웨어 라우팅의 효율성 입증:**
   하드웨어를 무작정 늘리지 않아도, **알고리즘 개선만으로 클러스터의 전체적인 부하 균형을 30% 가까이 개선**할 수 있음을 확인했습니다. 비용 효율적인 아키텍처 설계의 중요성을 체감했습니다.

2. **Tail Latency와 사용자 경험:**
   평균 응답 속도만큼이나 **P99(상위 1%) 지연 시간의 안정성**이 서비스 품질에 중요하다는 것을 배웠습니다. D-HASH는 튀는 부하를 억제하여 이 지표를 안정적으로 유지했습니다.

3. **실험 파이프라인의 중요성:**
   `stages.py`를 통해 실험 과정을 모듈화함으로써, 다양한 시나리오에서도 **일관된 데이터를 수집**할 수 있었습니다. 좋은 엔지니어링은 코드 품질뿐만 아니라 **검증 과정의 설계**에도 있음을 배웠습니다.
