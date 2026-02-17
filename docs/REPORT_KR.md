# ⚖️ D-HASH: 분산 캐시 로드 밸런싱을 위한 동적 Hot-key 대응 해싱

> "분산 캐시 시스템의 Hot-key 병목 현상을 해결하는 클라이언트 사이드 동적 라우팅 알고리즘"

<p>
  <img src="https://img.shields.io/badge/Python-3.11-3776AB?style=flat-square&logo=python&logoColor=white"/>
  <img src="https://img.shields.io/badge/Redis-7.4.2-DC382D?style=flat-square&logo=redis&logoColor=white"/>
  <img src="https://img.shields.io/badge/Docker-2496ED?style=flat-square&logo=docker&logoColor=white"/>
  <img src="https://img.shields.io/badge/License-MIT-green?style=flat-square"/>
</p>

## 📄 논문 정보
* 제목: D-HASH: Dynamic Hot-key Aware Scalable Hashing for Load Balancing in Distributed Cache Systems
* 저자: 방혁, 전상훈 (수원대학교 정보보호학과)
* 게재: KSII TIIS 2026 (SCIE 등재)
* DOI: [10.3837/tiis.2026.xx.xxx](https://doi.org/10.3837/tiis.2026.xx.xxx)

<br>

## 📋 목차
1. [프로젝트 소개](#1-프로젝트-소개)
2. [시스템 구조](#2-시스템-구조)
3. [핵심 알고리즘](#3-핵심-알고리즘)
4. [실험 환경](#4-실험-환경)
5. [실행 방법](#5-실행-방법)
6. [실험 결과](#6-실험-결과)
7. [트러블 슈팅](#7-트러블-슈팅)
8. [한계 및 향후 과제](#8-한계-및-향후-과제)

<br>

## 1. 프로젝트 소개

### 배경
대규모 캐시 시스템에서 널리 쓰이는 Consistent Hashing 방식은 데이터를 노드에 골고루 나누는 데는 효과적입니다. 하지만 특정 데이터(Hot-key) 자체에 트래픽이 몰리는 문제는 해결하지 못합니다.
실제 NASA 웹 로그를 분석해 보니, 상위 1%의 데이터가 전체 요청의 40% 이상을 차지했습니다. 이 때문에 특정 서버만 과부하가 걸려 전체 시스템이 느려지는 문제가 발생합니다.

### 목표
서버 구조를 바꾸거나 비싼 프록시 서버를 두지 않고, 클라이언트(SDK) 코드 수정만으로 Hot-key를 실시간으로 감지하고 트래픽을 분산시키는 경량 알고리즘(D-HASH)을 구현했습니다.

<br>

## 2. 시스템 구조

![System Architecture](images/dhash_architecture.png)  
*(D-HASH 전체 시스템 구조도)*

### 구성 요소
1.  기본 계층: 일반적인 Consistent Hashing 링 (가상 노드 포함)
2.  감지 계층: 클라이언트 내부에서 LRU 카운터로 데이터 요청 빈도 측정
3.  라우팅 계층: 특정 키가 Hot-key로 판단되면 동적으로 경로를 변경하는 로직

### 데이터 처리 전략
* 일반 키: 기존처럼 해시값에 맞는 메인 노드(Primary)로 보냅니다.
* Hot-key (읽기): 메인 노드와 대체 노드(Alternate)로 트래픽을 반반씩 나눕니다.
* Hot-key (쓰기): 데이터가 꼬이지 않도록 메인 노드에만 기록합니다.

<br>

## 3. 핵심 알고리즘

### 감지 및 승격
어떤 키의 조회수가 정해진 임계값($T$)을 넘으면 Hot-key로 '승격'시킵니다. 이때 바로 분산시키면 대체 노드에 데이터가 없어 에러(Cache Miss)가 날 수 있으므로, 잠시 데이터를 채워주는 예열 시간(Guard Phase)을 가집니다.

~~~python
# LRU 카운터 로직
if read_count[key] > THRESHOLD:
    promote_to_hotkey(key)  # Hot-key로 승격
    enter_guard_phase(key)  # 예열 시작 (대체 노드에도 데이터 저장)
~~~

### 윈도우 기반 라우팅
Hot-key로 승격된 데이터는 요청 횟수에 따라 메인 노드와 대체 노드로 번갈아 보냅니다.

~~~python
# 결정론적 라우팅 (랜덤 아님)
window_id = request_count // WINDOW_SIZE

if window_id % 2 == 0:
    route_to_alternate_node(key) # 짝수 윈도우: 대체 노드
else:
    route_to_primary_node(key)   # 홀수 윈도우: 메인 노드
~~~
* 임계값 ($T$): 300회 (실험을 통해 구한 최적값)
* 윈도우 크기 ($W$): 1,000회

<br>

## 4. 실험 환경

* 하드웨어: Intel Core i5-1340P, 16GB RAM
* 소프트웨어: Docker (WSL2), Redis 7.4.2
* 클라이언트: Python 3.11 (`redis-py` 라이브러리 확장)
* 데이터셋:
    1.  NASA HTTP Logs: 실제 웹 트래픽 데이터
    2.  Synthetic Zipfian: 인위적으로 쏠림 현상을 극대화한 데이터 ($\alpha=1.5$)

<br>

## 5. 실행 방법

### 사전 준비
* Docker 및 Docker Compose 설치

### 벤치마크 실행
~~~bash
# 1. 저장소 다운로드
git clone https://github.com/yourusername/dhash.git
cd dhash

# 2. 컨테이너 빌드 및 실행 (Redis 노드 + 벤치마크 툴)
docker-compose up --build

# 3. 실시간 로그 확인
docker-compose logs -f runner
~~~

### 결과 확인
실험 결과는 `./results` 폴더에 CSV 파일로 저장됩니다.
* `synthetic_zipf_results.csv`: 메인 성능 결과
* `synthetic_ablation.csv`: 파라미터 테스트 결과

<br>

## 6. 실험 결과

### NASA 데이터셋 (실제 환경)
| 알고리즘 | 처리량 (ops/s) | 부하 표준편차 (낮을수록 좋음) | 개선율 |
|:---|:---:|:---:|:---:|
| Consistent Hashing | 159,608 | 725,757 | - |
| D-HASH | 159,927 | 531,824 | 🔻 26.7% 개선 |

### Zipf 분포 데이터 (극한 환경)
| 알고리즘 | 처리량 (ops/s) | 부하 표준편차 (낮을수록 좋음) | 개선율 |
|:---|:---:|:---:|:---:|
| Consistent Hashing | 179,902 | 49,944 | - |
| D-HASH | 167,092 | 33,054 | 🔻 33.8% 개선 |

결론: 약 7% 정도의 처리 속도 저하는 있었지만, 서버 간 부하 불균형을 33.8%나 줄여서 시스템이 훨씬 안정적으로 돌아가게 만들었습니다.

<br>

## 7. 트러블 슈팅

### 1. xxHash64와 __slots__를 통한 Python 성능 최적화
[👉 포스트 보러가기](https://bh1848.github.io/hzeror/D-HASH-xxhash/)

- **Situation**: 대규모 분산 시뮬레이션 시 MD5의 높은 연산 비용으로 처리량이 급감하고, Python 객체 오버헤드로 인해 메모리 점유율이 한계에 도달.
- **Task**: 수백만 개의 키와 노드를 수용할 수 있도록 시뮬레이터의 연산 속도 및 메모리 효율 최적화.
- **Action**: 암호학적 해시인 MD5를 비암호화 고속 해시인 xxHash64로 대체하고, Python 클래스에 `__slots__`를 적용하여 동적 딕셔너리 생성을 차단.
- **Result**: 해싱 연산 속도 20배 향상 및 객체당 메모리 사용량 50% 절감을 통해 대규모 시나리오 테스트 가능 환경 확보.

### 2. Hot-key 승격 지연을 위한 Guard Phase 설계
[👉 포스트 보러가기](https://bh1848.github.io/hzeror/D-HASH-guard-phase/)

- **Situation**: 특정 키가 Hot-key로 승격되어 대체 노드(Alternate Node)로 트래픽이 전환되는 순간, 캐시가 비어있는 'Cold Start' 상태로 인해 응답 지연(Latency Spike) 발생.
- **Task**: 동적 라우팅 전환 시점의 캐시 미스를 방지하고 부하 분산의 안정성 확보.
- **Action**: 승격 직후 일정 기간 트래픽을 유지하는 Guard Phase와, 쓰기 요청을 대체 노드에도 비동기로 복제하는 Pre-warming(이중 쓰기) 전략 설계.
- **Result**: 승격 구간의 급격한 성능 저하를 차단하고, Zipfian 워크로드 환경에서 부하 표준편차를 최대 33.8% 개선.

### 3. 데이터 정합성을 위한 Write-Primary 라우팅 설계
[👉 포스트 보러가기](https://bh1848.github.io/hzeror/D-HASH-routing-strategy/)

- **Situation**: 읽기 트래픽 분산을 위한 동적 라우팅 규칙을 쓰기 요청에도 동일하게 적용할 경우, 노드 간 데이터 파편화(Fragmentation) 및 정합성 불일치 위협 확인.
- **Task**: 동적 로드 밸런싱 환경에서도 데이터의 무결성(Consistency)을 완벽하게 보장하는 아키텍처 수립.
- **Action**: 읽기 요청은 부하에 따라 경로를 분기하되, 쓰기 요청은 불변의 해시 링이 지정한 주 노드(p(k))로만 고정하는 Write-Primary 패턴 도입.
- **Result**: 복잡한 분산 락(Distributed Lock) 없이도 데이터 파편화 0%를 달성하며 시스템의 복잡도와 정합성 문제를 동시에 해결.

### 4. ThreadPoolExecutor를 이용한 비동기 벤치마크 환경 구축
[👉 포스트 보러가기](https://bh1848.github.io/hzeror/D-HASH-threadpoolexecutor/)

- **Situation**: 동기식(Blocking I/O) 부하 테스트 수행 중, 서버 자원은 충분함에도 클라이언트의 네트워크 대기 시간(RTT)으로 인해 처리량(Throughput)이 정체되는 병목 현상 발생.
- **Task**: 네트워크 지연을 배제하고 서버의 순수 최대 처리량(OPS)을 검증할 수 있는 논블로킹 테스트 환경 구축.
- **Action**: Python `ThreadPoolExecutor`를 도입하여 요청을 병렬화하고, 노드별 버킷팅(Bucketing)을 통해 락 경합을 최소화한 비동기 벤치마크 툴 개발.
- **Result**: 기존 대비 압도적인 180,000 OPS를 달성하여 실제 운영 환경 수준의 성능을 검증하고, Tail Latency(P99) 측정의 정밀도 확보.

<br>

## 8. 한계 및 향후 과제

### 현재의 한계
1.  시야 제한: 각 클라이언트가 혼자서만 카운팅을 하므로, 전체 시스템 상황을 완벽하게 실시간으로 알 수는 없습니다.
2.  강등 로직 부재: Hot-key가 식었을 때 다시 일반 키로 돌리는 기능이 아직 없습니다.
3.  네트워크 환경: 도커 내부 통신이라 실제 인터넷망의 지연 시간(Jitter)까지는 반영하지 못했습니다.

### 향후 계획
* 자동 강등: 시간이 지나면 카운트를 줄이는 알고리즘을 넣어, 안 쓰는 Hot-key를 해제하는 기능 추가.
* 정보 공유: 클라이언트끼리 Hot-key 정보를 주고받는 프로토콜(Gossip) 구현.
* 클라우드 검증: AWS 같은 실제 클라우드 환경에서 테스트 진행.
