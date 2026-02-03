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

## 🎯 프로젝트 요약

| 구분 | 내용 |
|:---:|:---|
| 문제점 | 특정 키(Hot-key)에 요청이 몰릴 때 발생하는 단일 노드 과부하 현상 |
| 해결책 | 별도 서버 없이 클라이언트에서 처리하는 윈도우 기반 동적 라우팅 |
| 성과 | 기존 방식 대비 부하 편차(표준편차) 33.8% 감소 |
| 스택 | Python 3.11, Redis, Consistent Hashing |

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

### 3-1. 감지 및 승격
어떤 키의 조회수가 정해진 임계값($T$)을 넘으면 Hot-key로 '승격'시킵니다. 이때 바로 분산시키면 대체 노드에 데이터가 없어 에러(Cache Miss)가 날 수 있으므로, 잠시 데이터를 채워주는 예열 시간(Guard Phase)을 가집니다.

~~~python
# LRU 카운터 로직
if read_count[key] > THRESHOLD:
    promote_to_hotkey(key)  # Hot-key로 승격
    enter_guard_phase(key)  # 예열 시작 (대체 노드에도 데이터 저장)
~~~

### 3-2. 윈도우 기반 라우팅
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

### 6-1. NASA 데이터셋 (실제 환경)
| 알고리즘 | 처리량 (ops/s) | 부하 표준편차 (낮을수록 좋음) | 개선율 |
|:---|:---:|:---:|:---:|
| Consistent Hashing | 159,608 | 725,757 | - |
| D-HASH | 159,927 | 531,824 | 🔻 26.7% 개선 |

### 6-2. Zipf 분포 데이터 (극한 환경)
| 알고리즘 | 처리량 (ops/s) | 부하 표준편차 (낮을수록 좋음) | 개선율 |
|:---|:---:|:---:|:---:|
| Consistent Hashing | 179,902 | 49,944 | - |
| D-HASH | 167,092 | 33,054 | 🔻 33.8% 개선 |

결론: 약 7% 정도의 처리 속도 저하는 있었지만, 서버 간 부하 불균형을 33.8%나 줄여서 시스템이 훨씬 안정적으로 돌아가게 만들었습니다.

<br>

## 7. 트러블 슈팅

| 문제 상황 | 원인 | 해결 방법 | 기술 블로그 |
|:---:|:---|:---|:---:|
| 해시 속도 저하 | Python 내장 함수의 성능 한계 | xxHash64 교체 및 `__slots__`로 메모리 최적화 | [🔗 Velog](https://velog.io/@bh1848/D-HASH-%ED%95%B4%EC%8B%9C-%EC%84%B1%EB%8A%A5-4%EB%B0%B0-%ED%96%A5%EC%83%81%EC%8B%9C%ED%82%A4%EA%B8%B0-xxHash%EC%99%80-slots) |
| 초기 캐시 미스 | 승격 직후 대체 노드에 데이터 없음 | Guard Phase 도입: 승격 초반엔 쓰기 작업을 병행 | [🔗 Velog](#) |
| 데이터 불일치 | 여러 노드에 데이터가 흩어짐 | Write-Primary 정책: 쓰기는 무조건 메인 노드에서만 수행 | [🔗 Velog](#) |
| 테스트 병목 | 동기 방식 요청의 대기 시간 | ThreadPoolExecutor를 써서 비동기 방식으로 부하 테스트 | [🔗 Velog](#) |

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
