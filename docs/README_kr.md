# D-HASH (Korean Documentation)

Dynamic Hot-key Aware Client-side Routing for Distributed Cache Systems

---

## 개요

Zipf 분포 환경에서는 일부 키가 전체 요청의 상당 부분을 차지한다.
Consistent Hashing은 키-노드 매핑의 안정성은 제공하지만, 특정 키에 집중되는 read 부하를 직접 제어하지는 않는다.

D-HASH는 서버 구조 변경 없이, 클라이언트 측에서 핫키를 판정하고 read 경로를 제어하는 방식으로 구현되었다.

설계에서는 다음 두 조건을 분리한다.

- Alternate 노드를 생성하는 조건
- read 요청이 해당 노드를 선택하는 조건

Alternate의 준비와 read 경로 전환은 독립적으로 동작한다.

---

## 설계 구조

### 1. Alternate 선택

가상노드 기반 Consistent Hashing 링에서는 슬롯 이동이 곧 물리 노드 변경을 의미하지 않는다.

Alternate는 물리 노드 기준으로 `cand != primary` 조건을 만족하는 경우에만 확정된다.
후보 판정은 슬롯 위치가 아니라 node id 기준으로 수행된다.

다음 순서를 따른다.

- 보조 해시를 이용해 stride를 계산한다.
- stride 단위로 링을 점프하며 후보를 탐색한다.
- `primary`와 다른 물리 노드를 찾으면 Alternate로 확정한다.
- 실패할 경우 선형 스캔(linear fallback)을 수행한다.

`ensure_alternate()` 함수로 분리되어 있으며, 위 조건을 만족하지 못하는 경우에만 fallback이 동작한다.

---

### 2. Guard Phase

핫키 판정 직후 read 경로를 즉시 전환하지 않는다.

핫키 판정 이후 증가한 요청 수를 `delta`라 할 때, `delta < W` 구간에서는 Primary를 유지한다.

다음 조건을 `in_guard_phase(delta, W)` 함수로 분리하였다.

```python
def in_guard_phase(delta: int, W: int) -> bool:
    return delta < W
```

Guard 구간에서는 항상 `_primary_safe(key)`가 반환된다.

---

### 3. Window 기반 전환

Guard 구간을 지난 이후 read 경로는 window 단위로 계산된다.

`pick_node_by_window()` 함수에서 다음 계산이 수행된다.

```python
epoch = (delta - W) // W

if epoch % 2 == 0:
    return alt_node
return primary_fn(key)
```

- 동일한 epoch 구간에서는 노드가 변경되지 않는다.
- epoch의 짝수 구간에서는 Alternate,
- 홀수 구간에서는 Primary가 선택된다.

이 계산은 Guard 이후 구간에서만 적용된다.

---

### 4. Percentile 계산 기준

파이프라인 환경에서는 하나의 latency 샘플이 여러 operation을 포함할 수 있다.

Percentile 계산 시 샘플 개수가 아니라 각 샘플이 포함하는 operation 수를 기준으로 누적한다.

다음 순서를 따른다.

```python
samples_sorted = sorted(samples, key=lambda x: x[0])
total_w = sum(w for _, w in samples_sorted)
target = q * total_w
```

- 샘플은 latency 기준으로 정렬된다.
- weight는 해당 batch에 포함된 operation 수다.
- 누적 weight가 `target`에 도달하는 지점에서 percentile이 결정된다.
- 목표 지점이 두 샘플 사이에 위치하는 경우 선형 보간(linear interpolation)을 적용한다.

이 방식은 batch 크기 차이에 따른 누적 비중 왜곡을 완화하기 위한 계산 방식이다.

---

## 실행 특성

- write 요청은 항상 Primary로 전달된다.
- read 요청은 Guard 이후 window 단위로 전환된다.
- Alternate의 준비 조건과 read 선택 조건은 분리되어 있다.
- Percentile은 operation 단위 누적 방식으로 계산된다.

---

## 트러블슈팅 기록

- [Alternate Selection](troubleshooting/01_alternate.md)
- [Guard Phase](troubleshooting/02_guard.md)
- [Routing Window](troubleshooting/03_window.md)
- [Weighted Percentile](troubleshooting/04_weighted_percentile.md)

---

## 논문 정보

**D-HASH: Dynamic Hot-key Aware Scalable Hashing for Load Balancing in Distributed Cache Systems**
TIIS (SCIE), 2026 (In Press)
