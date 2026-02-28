# 파이프라인 환경에서 percentile 기준 축이 batch 단위로 해석되던 경로

## P99이 batch 경계에 따라 함께 움직이던 로그

파이프라인을 활성화한 벤치 구간에서 P99 값이 batch 크기 변화에 따라 같이 움직이는 패턴이 기록되었다.

동일 워크로드인데도 batch 크기를 조정한 구간에서 tail 값의 위치가 달라졌다.  
수치는 기록하지 않았다.

---

## `execute()` 단위 샘플이 여는 해석 경로

파이프라인에서는 여러 op가 한 번의 `execute()`로 묶인다.

N개의 op 적재  
→ 한 번의 `execute()` 호출  
→ batch 전체에 대한 latency 1개 측정

이때 latency 샘플을 batch 단위로 수집하고,  
percentile 계산에서 각 샘플을 동일 weight로 취급하면 다음과 같은 해석이 가능하다.

batch A (op 1개)  
batch B (op 100개)  
→ 샘플은 2개  
→ percentile은 샘플 개수 기준으로 정렬  
→ op 개수 기준 분포와 분리

percentile의 기준 축이 op 수가 아니라 batch 수로 해석될 수 있다.

---

## `_weighted_percentile()`의 실제 구현

latency 샘플은 `(avg_latency_per_op, batch_size)` 형태로 유지된다.  
percentile 계산은 `_weighted_percentile(samples, q)`에서 수행된다.

```python
def _weighted_percentile(samples: List[Tuple[float, int]], q: float) -> float:
    if not samples:
        return 0.0

    samples_sorted = sorted(samples, key=lambda x: x[0])
    total_w = sum(w for _, w in samples_sorted)

    if total_w <= 0:
        return 0.0

    target = q * total_w
    cum = 0.0
    prev_v = samples_sorted[0][0]

    for v, w in samples_sorted:
        next_cum = cum + w
        if next_cum >= target:
            if w == 0:
                return v
            frac = (target - cum) / w
            return prev_v + (v - prev_v) * frac
        prev_v = v
        cum = next_cum

    return samples_sorted[-1][0]
```

---

## 실행 경로

`not samples`  
→ `0.0` 반환

`total_w <= 0`  
→ `0.0` 반환

일반 경로:

`sorted(samples, key=lambda x: x[0])`  
→ `total_w = sum(w ...)`  
→ `target = q * total_w`

→ `for v, w in samples_sorted:`  
→ `next_cum = cum + w`

`next_cum >= target`이면 반환 지점 확정

- `w == 0`이면 `v` 반환  
- 그렇지 않으면  
  `frac = (target - cum) / w`  
  `prev_v + (v - prev_v) * frac` 반환

여기서 `w`는 `batch_size`다.

누적 기준은 샘플 개수가 아니라 op 개수 합이다.

---

## batch 단위와 op 단위 percentile의 분리

`target = q * total_w`는 전체 op 수 기준 위치다.

batch가 클수록 누적 weight에 더 크게 반영되고,  
작은 batch는 작은 구간만 차지한다.

샘플 개수 기준 정렬과 달리,  
누적 weight 기준 탐색은 op 단위 분포에 맞춘 위치를 반환한다.

---

## 로그에서 관찰된 변화

수치는 기록하지 않았다.

동일 워크로드에서 batch 크기를 변경해도  
P99이 샘플 개수 변화에 직접적으로 따라 움직이는 형태는 보이지 않았다.

percentile 기준 축은 op 단위로 유지되었다.

---

## `_connection_pools`를 통한 연결 생성 변동 분리

멀티 노드·멀티 스레드 환경에서는 클라이언트 생성이 반복되면  
연결 수 변동이 latency에 섞일 수 있다.

다음 구조는 host별 `ConnectionPool`을 캐시한다.

```python
_connection_pools: Dict[str, ConnectionPool] = {}

def _redis_client(host: str) -> StrictRedis:
    if host not in _connection_pools:
        _connection_pools[host] = ConnectionPool(host=host, port=6379, db=0)
    return StrictRedis(connection_pool=_connection_pools[host])
```

실행 경로:

`host not in _connection_pools`  
→ `ConnectionPool(...)` 생성  
→ `_connection_pools[host]`에 저장

`host in _connection_pools`  
→ 기존 풀 재사용  
→ `StrictRedis(connection_pool=...)` 반환

연결 생성 비용이 percentile 계산에 직접 개입하는 경로를 줄이기 위한 구조다.

---

## 설계 관점 정리

파이프라인 환경에서는 샘플과 op가 동일 단위가 아니다.  
`(value, weight)` 구조는 percentile 기준을 op 단위로 고정한다.

정렬과 누적 계산은 추가 연산을 발생시킨다.  
대신 batch 크기 변화와 percentile 위치의 관계가 분리된다.

측정 단위 정의는 분산 알고리즘 비교와 함께 다뤄야 하는 조건이다.