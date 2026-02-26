# 📊 D-HASH: 분산 캐시 로드 밸런싱을 위한 동적 Hot-key 대응 해싱

> "분산 캐시 시스템의 Hot-key 병목 현상을 해결하는 클라이언트 사이드 동적 라우팅 알고리즘"

<p align="left">
  <img src="https://img.shields.io/badge/Python-3.11-3776AB?style=flat-square&logo=python&logoColor=white"/>
  <img src="https://img.shields.io/badge/Redis-7.4.2-DC382D?style=flat-square&logo=redis&logoColor=white"/>
  <img src="https://img.shields.io/badge/Docker-Ready-2496ED?style=flat-square&logo=docker&logoColor=white"/>
  <img src="https://img.shields.io/badge/TIIS_(SCIE)-In_Press-0066CC?style=flat-square&logo=googlescholar&logoColor=white"/>
  <img src="https://img.shields.io/badge/License-MIT-green?style=flat-square"/>
</p>

## 📄 논문 정보
* 제목: D-HASH: Dynamic Hot-key Aware Scalable Hashing for Load Balancing in Distributed Cache Systems
* 저자: 방혁, 전상훈 (수원대학교 정보보호학과)
* 게재: KSII TIIS 2026 (SCIE 등재)
* DOI: [10.3837/tiis.2026.xx.xxx](https://doi.org/10.3837/tiis.2026.xx.xxx)

<br/>

## 1. 프로젝트 소개

### 배경
대규모 캐시 시스템에서 널리 쓰이는 Consistent Hashing 방식은 데이터를 노드에 골고루 나누는 데는 효과적입니다. 하지만 특정 데이터(Hot-key) 자체에 트래픽이 몰리는 문제는 해결하지 못합니다.
실제 NASA 웹 로그를 분석해 보니, 상위 1%의 데이터가 전체 요청의 40% 이상을 차지했습니다. 이 때문에 특정 서버만 과부하가 걸려 전체 시스템이 느려지는 문제가 발생합니다.

### 목표
서버 구조를 바꾸거나 비싼 프록시 서버를 두지 않고, 클라이언트(SDK) 코드 수정만으로 Hot-key를 실시간으로 감지하고 트래픽을 분산시키는 경량 알고리즘(D-HASH)을 구현했습니다.

<br/>

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

<br/>

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

<br/>

## 4. 실험 환경

* 하드웨어: Intel Core i5-1340P, 16GB RAM
* 소프트웨어: Docker (WSL2), Redis 7.4.2
* 클라이언트: Python 3.11 (`redis-py` 라이브러리 확장)
* 데이터셋:
    1.  NASA HTTP Logs: 실제 웹 트래픽 데이터
    2.  Synthetic Zipfian: 인위적으로 쏠림 현상을 극대화한 데이터 ($\alpha=1.5$)

<br/>

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

<br/>

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

<br/>

## 7. 트러블 슈팅

### 1. xxHash64와 `__slots__`를 활용한 성능 최적화
- **문제**: 대규모 시뮬레이션 시 MD5 해싱 연산의 높은 비용으로 처리량이 급감하고, Python 객체 오버헤드로 인해 메모리 부족 발생
- **해결**: 암호학적 해시인 MD5를 고속 비암호화 해시인 `xxHash64`로 교체하고, 클래스에 `__slots__`를 적용해 객체당 메모리 사용량 최적화
- **결과**: **해싱 속도 20배 향상 및 메모리 50% 절감**을 통해 대규모 시나리오 테스트가 가능한 환경 구축  
- [👉 포스트 보러가기](https://hzeror.netlify.app/D-HASH-xxhash/)

### 2. Hot-key 승격 시 Latency Spike 방어 (Guard Phase)
- **문제**: 특정 키가 Hot-key로 판단되어 노드가 전환되는 순간, 대상 노드에 데이터가 없는 'Cold Start' 상태로 인해 응답 지연 발생
- **해결**: 노드 전환 전 일정 시간 요청을 유지하며 데이터를 채워주는 **Guard Phase**와 비동기 이중 쓰기(Pre-warming) 전략 도입
- **결과**: 전환 구간의 성능 저하를 방지하고, Zipfian 분포 기반 테스트 환경에서 **부하 불균형 33.8% 개선**
- [👉 포스트 보러가기](https://hzeror.netlify.app/D-HASH-guard-phase/)

### 3. 데이터 정합성 보장을 위한 Write-Primary 구조 설계
- **문제**: 읽기 트래픽 분산 로직을 쓰기 요청에 동일하게 적용할 경우, 여러 노드에 데이터가 흩어져 정합성이 깨지는 이슈 확인
- **해결**: 읽기는 분산하되 쓰기는 해시 링이 지정한 주 노드(Primary)에만 고정하는 **Write-Primary** 패턴 적용
- **결과**: 복잡한 분산 락(Distributed Lock) 없이 **데이터 파편화 0%** 달성 및 시스템 복잡도 해결
- [👉 포스트 보러가기](https://hzeror.netlify.app/D-HASH-routing-strategy/)

### 4. ThreadPoolExecutor를 이용한 비동기 벤치마크 툴 개발
- **문제**: 동기 방식(Blocking I/O) 테스트 시 클라이언트의 네트워크 대기 시간 때문에 서버의 최대 처리량(Throughput) 측정 불가
- **해결**: `ThreadPoolExecutor`를 활용해 요청을 병렬화하고, 노드별 버킷팅으로 락 경합을 최소화한 비동기 테스트 환경 구축
- **결과**: **180,000 OPS급 고부하 환경**을 구현하여 실제 운영 수준의 성능 검증 및 P99 지연 시간 측정의 정밀도 확보
- [👉 포스트 보러가기](https://hzeror.netlify.app/D-HASH-threadpoolexecutor/)

<br/>

## 8. 프로젝트를 마치며
MySQL과 Redis의 성능을 비교하며 Redis의 노드 과부하 문제에 관심이 생겼고, 이를 해결하기 위해 1년 6개월이라는 시간이 걸렸습니다.  
처음에는 처리량 향상과 부하 분산을 동시에 잡으려 했으나 현실적으로 어렵다는 것을 깨달았습니다. 이후 방향을 틀어 Consistent Hashing 기반의 처리량은 최대한 유지하면서, 핫키로 인한 불균형만 확실히 해결하는 것에 집중했습니다.  
시스템에 부하를 주지 않기 위해 무거운 프록시 대신 LRU 카운터와 Guard Phase를 활용한 클라이언트 사이드 로직으로 접근했습니다. 중간중간 어려움이 많았지만, 결과적으로 처리량 저하를 최소화하면서 불균형 문제를 눈에 띄게 개선할 수 있었습니다.  
스스로 한계점을 인지하고 있어 완벽히 만족하지는 않습니다. 하지만 알고리즘 설계, 데이터 수집, 실험, 영어 논문 작성까지 전 과정을 혼자 진행하며 분산 시스템을 이해하고 성장할 수 있었던 경험이었던 것 같습니다.  



