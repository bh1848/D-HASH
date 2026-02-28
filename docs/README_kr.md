# D-HASH  
Dynamic Hot-key Aware Client-side Routing for Distributed Cache Systems

> Hot-key를 노드 확장이 아니라  
> read 경로 전환 문제로 다룬 클라이언트 사이드 라우팅 구현

---

## Overview

Zipf 분포 환경에서는 일부 키에 요청이 집중된다.  
Consistent Hashing은 키-노드 매핑에는 안정적이지만, 특정 키로 몰리는 read 편중을 직접 완화하지는 않는다.

D-HASH는 서버 구조를 변경하지 않고,  
클라이언트에서 핫키를 감지하고 read 경로를 조정하는 방식을 구현했다.

핵심은 두 조건을 분리하는 것이다.

- Alternate를 언제 생성할 것인가  
- 실제 read를 언제 전환할 것인가  

---

## Core Decisions

### 1. Alternate는 슬롯이 아니라 node id 기준으로 확정

가상노드 링에서는 슬롯 이동이 물리 노드 변경을 의미하지 않는다.  
Alternate는 `cand != primary` 조건을 통과한 경우에만 확정한다.

- stride 기반 점프 탐색
- 실패 시 선형 스캔 fallback

슬롯이 아니라 node id 기준으로 후보를 좁힌다.

---

### 2. Alternate 생성과 read 전환을 분리

핫키 판정 직후 즉시 전환하지 않는다.  
Alternate를 준비하는 조건과, read가 해당 노드를 선택하는 조건을 분리했다.

```python
if delta < self.W:
    return self._primary_safe(key)

epoch = (delta - self.W) // self.W
return self.alt[key] if (epoch % 2 == 0) else self._primary_safe(key)
```

`delta < self.W` 구간에서는 Primary를 유지한다.  
전환은 Guard 이후 window 단위에서만 발생한다.

---

### 3. 요청 단위 전환을 두지 않음

임계값 근처에서 경로가 흔들리는 구간을 줄이기 위해  
전환을 window 단위로 고정했다.

```python
epoch = (delta - self.W) // self.W
```

동일 epoch 구간에서는 노드가 바뀌지 않는다.

---

### 4. Percentile 기준을 op 단위로 유지

파이프라인 환경에서는 한 번의 latency 샘플이 여러 op를 포함한다.  
percentile 계산 시 샘플 수가 아니라 op 수 합을 기준으로 사용한다.

```python
def _weighted_percentile(samples, q):
    samples_sorted = sorted(samples, key=lambda x: x[0])
    total_w = sum(w for _, w in samples_sorted)
    target = q * total_w
    ...
```

멀티 노드 환경에서는 ConnectionPool을 재사용해 연결 생성 변동을 분리했다.

---

## Execution Characteristics

- write는 Primary로 고정  
- read는 Guard 이후 window 단위 전환  
- Alternate 준비와 선택은 다른 분기에서 결정  
- percentile은 op 기준 누적 방식으로 계산  

---

## Experimental Snapshot

Zipf α=1.5 환경에서 다음 수치를 사용했다.

| 알고리즘 | 처리량 (ops/s) | 부하 표준편차 |
|-----------|----------------|----------------|
| Consistent Hashing | 179,902 | 49,944 |
| D-HASH | 167,092 | 33,054 |

실험 설정은 논문과 벤치 코드에 포함되어 있다.

---

## Engineering Notes

- docs/troubleshooting/01_alternate_selection.md  
- docs/troubleshooting/02_guard_phase.md  
- docs/troubleshooting/03_routing_window.md  
- docs/troubleshooting/04_weighted_percentile.md  

---

## Publication

**D-HASH: Dynamic Hot-key Aware Scalable Hashing for Load Balancing in Distributed Cache Systems**  
TIIS (SCIE) 2026 게재 예정

---

## Closing

핫키 read 경로는 대상 선정과 전환 시점을 분리해 다뤘다.  
측정은 pipeline 샘플을 op 단위로 해석하는 기준에 맞췄다.
