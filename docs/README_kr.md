# D-HASH

Dynamic Hot-key Aware Client-side Routing for Distributed Cache Systems
TIIS (SCIE), 2026 (Accepted)

---

## 1. 개요

Zipf 분포에서는 일부 키가 전체 요청의 대부분을 차지한다.

Consistent Hashing은 키-노드 매핑을 안정적으로 유지하지만,
특정 키에 요청이 몰릴 때 발생하는 read 부하까지 직접 다루지는 않는다.

이 경우, 특정 물리 노드에 부하가 집중될 수 있다.

D-HASH는 서버 구조를 바꾸지 않고,
클라이언트에서 read 경로를 조건부로 조정하는 방식으로
이 문제를 다루도록 설계했다.

---

## 2. 설계 접근

핫키 대응에서는 두 단계를 분리했다.

1) Alternate를 준비하는 단계
2) 현재 요청에서 Alternate를 선택하는 단계

전환 가능 여부와 실제 전환을 나누면,
임계치 근처에서 경로가 자주 바뀌는 문제를 줄일 수 있다.

구성은 다음과 같다.

- `router` — 실행 흐름 제어
- `guard` — 전환 가능 구간 판단
- `alternate` — 물리 노드 기준 후보 선택
- `window` — 전환 안정화
- `stats` — 통계 계산 유틸

Primary는 항상 해싱 결과를 기준으로 한다.
라우팅 변경은 조건이 충족될 때만 적용한다.

---

## 3. 구현 스냅샷 (발췌)

### 3.1 Write는 Primary 고정

~~~python
if op == "write":
    return self._primary_safe(key)
~~~

write는 Primary로 고정한다.
read 요청에서만 경로 조정을 고려한다.

---

### 3.2 Guard 구간

~~~python
delta = max(0, cnt - threshold)
return delta < window_size
~~~

임계치 직후에는 Primary를 유지한다.
즉시 전환하지 않는다.

---

### 3.3 Window 전환

~~~python
epoch = (delta - window_size) // window_size

if epoch % 2 == 0:
    return alt_node
return primary_fn(key)
~~~

전환은 window 단위로 계산된다.
같은 epoch 안에서는 노드가 바뀌지 않는다.

요청 단위로 경로가 흔들리는 현상을 줄이기 위한 구조다.

---

### 3.4 Alternate 후보는 물리 노드 기준

~~~python
if cand != primary:
    return cand
~~~

가상노드 기반 링에서는 슬롯이 달라도
물리 노드는 같을 수 있다.

그래서 Primary와 같은 물리 노드는 후보에서 제외한다.

---

### 3.5 Weighted Percentile

~~~python
samples_sorted = sorted(samples, key=lambda x: x[0])
total_w = sum(w for _, w in samples_sorted)
target = q * total_w
~~~

파이프라인 환경에서는 하나의 latency 샘플이
여러 operation을 포함할 수 있다.

Percentile은 샘플 수가 아니라 weight 기준으로 누적 계산한다.

---

## 4. 동작 특성 요약

- write는 항상 Primary로 보낸다.
- read에서만 조건부 전환을 고려한다.
- Alternate 준비와 read 선택은 분리되어 있다.
- Guard와 Window는 역할이 다르다.
- 코어 라우팅(`dhash`)과 실험 계층(`dhash_repro`)은 분리되어 있다.

---

## 5. 문서

- 설계: `docs/design/`
- 재현: `docs/reproduction/`
- 트러블슈팅: `docs/troubleshooting/`
- 레퍼런스: `docs/reference/`

---

## 6. 트러블슈팅 기록

- [01 Alternate](docs/troubleshooting/01_alternate.md)
- [02 Guard](docs/troubleshooting/02_guard.md)
- [03 Window](docs/troubleshooting/03_window.md)
- [04 Weighted Percentile](docs/troubleshooting/04_weighted_percentile.md)
