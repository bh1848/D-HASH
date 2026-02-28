# D-HASH: 분산 캐시 로드 밸런싱을 위한 동적 Hot-key 대응 해싱

> **"상위 1% 데이터가 전체 트래픽의 40%를 차지하는 '핫키(Hot-key)' 병목 현상을 해결하기 위한 클라이언트 사이드 라우팅 레이어 연구"**

<p align="left">
  <img src="https://img.shields.io/badge/Python-3.11-3776AB?style=flat-square&logo=python&logoColor=white"/>
  <img src="https://img.shields.io/badge/Redis-7.4.2-DC382D?style=flat-square&logo=redis&logoColor=white"/>
  <img src="https://img.shields.io/badge/TIIS_(SCIE)-In_Press-0066CC?style=flat-square&logo=googlescholar&logoColor=white"/>
</p>

## 논문 정보
* **제목**: D-HASH: Dynamic Hot-key Aware Scalable Hashing for Load Balancing in Distributed Cache Systems
* **학술지**: TIIS 2026 게재 예정 (SCIE)
* **저자**: 방혁, 전상훈

<br/>

## 1. 프로젝트 요약
실제 NASA 웹 로그 분석 결과, **상위 1%의 데이터가 전체 요청의 40% 이상을 차지하는 핫키 문제**를 확인했습니다. 기존 Consistent Hashing으로는 해결하기 어려운 이 쏠림 현상을 풀기 위해, 서버 구조 변경 없이 클라이언트 SDK 수정만으로 트래픽을 분산시키는 **D-HASH** 알고리즘을 설계하고 구현했습니다.

<br/>


## 2. 시스템 구조
![System Architecture](../docs/images/dhash_architecture.png)

* **감지 및 라우팅**: 클라이언트 내부의 LRU 카운터로 요청 빈도를 재고, 임계값을 넘으면 실시간으로 경로를 바꿉니다.
* **데이터 정합성**: 읽기 요청은 나누되, 쓰기 요청은 데이터가 꼬이지 않도록 항상 메인 노드(Primary)에만 기록하는 **Write-Primary** 전략을 씁니다.

<br/>

## 3. 핵심 로직: Guard Phase (예열 구간)
핫키로 판단되어 노드가 바뀌는 순간, 새로운 노드에 데이터가 없어 응답이 늦어지는 문제(Cold Start)를 막기 위해 **Guard Phase**를 도입했습니다.

~~~python
# src/dhash_experiments/algorithms.py

# Guard Phase: 노드 전환 직후 첫 번째 구간(W) 동안은 메인 노드로 보내면서 새로운 노드 예열 유도
if delta < self.W:
    return self._primary_safe(key)
    
# 이후 구간 단위로 메인 노드와 대체 노드를 번갈아 호출하며 부하 분산
epoch = (delta - self.W) // self.W
return self.alt[key] if (epoch % 2 == 0) else self._primary_safe(key)
~~~

<br/>

## 4. 실험 결과 (Zipf alpha=1.5 기준)
* **부하 분산**: 기존 방식보다 노드 간 부하 편차를 **33.8% 줄였습니다**.
* **성능 오버헤드**: 추가 로직으로 인한 처리량 저하는 **7% 내외**로 막았습니다.

| 알고리즘 | 처리량 (ops/s) | 부하 표준편차 (🔻) | 개선율 |
|:---|:---:|:---:|:---:|
| Consistent Hashing | 179,902 | 49,944 | - |
| **D-HASH (제안)** | **167,092** | **33,054** | **33.8% 개선** |


<br/>

## 5. 트러블슈팅

### 1. Alternate가 Primary와 같은 물리 노드로 선택되던 문제

**문제**  
Hot-key 오프로딩에서 Alternate를 다음 슬롯으로 고르던 로직이 있었는데, virtual node 링 특성상 Primary와 같은 physical node가 다시 선택될 수 있었음. 이 경우 오프로딩이 사실상 실패함.

**해결**  
`_ensure_alternate()`에서 candidate를 고를 때마다 `candidate != ring[primary_idx].physical_node` 조건을 확인하도록 수정함.  
또한 `stride = 1 + hash(key|alt) % (N-1)`로 링을 점프하면서 다른 물리 노드를 탐색하고, 실패 시 linear scan fallback을 추가함.

**결과**  
현재 코드에서는 alt == primary 케이스가 발생하지 않도록 막혀 있음. Alternate는 항상 Primary와 다른 물리 노드로 선택됨.

**Blog**  
[D-HASH에서 Alternate가 Primary와 같은 노드로 잡히던 문제 수정](https://velog.io/@bh1848/D-HASH%EC%97%90%EC%84%9C-Alternate%EA%B0%80-Primary%EC%99%80-%EA%B0%99%EC%9D%80-%EB%AC%BC%EB%A6%AC-%EB%85%B8%EB%93%9C%EB%A1%9C-%EC%84%A0%ED%83%9D%EB%90%98%EB%8D%98-%EB%AC%B8%EC%A0%9C-%EC%88%98%EC%A0%95)

### 2. Hot-key 전환 직후 캐시 미스로 tail latency 증가

**문제**  
핫키 판정 직후 전환 구간에서 Alternate가 콜드 상태라 연속 캐시 미스가 발생했고, 전환 직후 tail latency가 튀는 현상을 로그로 확인함.

**원인**  
핫키 감지 직후 Alternate 쪽 캐시 예열 없이 read가 분산되면서 미스가 연속으로 발생함. cold node로 read가 몰리면 지연이 증가할 수 있음.

**해결**  
`get_node()`에 Guard Phase(W 요청) 도입.  
임계치 T 초과 직후 W번 요청은 Primary를 유지하고, Guard 이후에는 window 단위로 Primary/Alternate를 번갈아 라우팅하도록 정리함.  
또한 실험 시 초기 캐시 상태를 맞추기 위해 `warmup_cluster()`에서 Alternate에도 일부 키를 미리 적재하도록 보완함.

**결과**  
Guard 적용 이후 전환 직후에 발생하던 연속 캐시 미스 구간이 완화되는 것을 로그 기준으로 확인함. 즉시 전환이 아니라, 준비 구간 후 분산하는 흐름으로 바뀜.

**Blog**  
[D-HASH에서 핫키 전환 직후 캐시 미스로 tail latency가 튀던 문제 해](https://velog.io/@bh1848/D-HASH%EC%97%90%EC%84%9C-%ED%95%AB%ED%82%A4-%EC%A0%84%ED%99%98-%EC%A7%81%ED%9B%84-%EC%BA%90%EC%8B%9C-%EB%AF%B8%EC%8A%A4%EB%A1%9C-tail-latency%EA%B0%80-%EC%95%85%ED%99%94%EB%90%98%EB%8D%98-%EB%AC%B8%EC%A0%9C)

<br/>

## 6. 회고록
Redis의 노드 과부하 문제를 해결하고 싶어 시작한 고민이 1년 6개월의 연구와 논문 게재로 이어졌습니다.  
처리량과 부하 분산 사이의 트레이드 오프를 찾는 과정이 쉽지 않았지만, 기존 시스템에 부담을 주지 않는 클라이언트 사이드 로직으로 유의미한 수치를 뽑아낼 수 있었습니다.  
알고리즘 설계부터 실험, 영어 논문 작성까지 직접 해보며 분산 시스템에 대한 이해를 크게 넓힐 수 있었던 경험이었습니다.  
