# D-HASH (Korean Documentation)

Dynamic Hot-key Aware Client-side Routing for Distributed Cache Systems

---

## 개요

Zipf 분포 환경에서는 일부 키가 전체 요청의 상당 부분을 차지한다.  
Consistent Hashing은 키-노드 매핑의 안정성은 제공하지만, 특정 키에 집중되는 read 부하를 직접 제어하지는 않는다.

D-HASH는 서버 구조를 변경하지 않고,
클라이언트 측에서 핫키를 판정하고 read 경로를 제어하는 구조를 구현한다.

설계는 다음 두 조건을 분리한다.

- Alternate 노드를 생성하는 조건
- read 요청이 해당 노드를 선택하는 조건

---

## 설계 구조

### 1. Alternate 선택

가상노드 기반 Consistent Hashing 링에서는 슬롯 이동이 물리 노드 변경을 의미하지 않는다.

Alternate는 물리 노드 기준으로 `cand != primary` 조건을 만족하는 경우에만 확정한다.

- stride 기반 점프 탐색
- 실패 시 선형 스캔 fallback

후보 판정은 슬롯이 아닌 node id 기준으로 수행된다.

---

### 2. Guard Phase

핫키 판정 직후 즉시 read 전환을 수행하지 않는다.

```python
if delta < self.W:
    return self._primary_safe(key)
```

`delta < W` 구간에서는 Primary를 유지한다.

---

### 3. Window 기반 전환

Guard 이후 read 경로는 window 단위로 계산된다.

```python
epoch = (delta - self.W) // self.W
return self.alt[key] if (epoch % 2 == 0) else self._primary_safe(key)
```

동일 epoch 구간에서는 노드가 변경되지 않는다.

---

### 4. Percentile 계산 기준

파이프라인 환경에서는 한 번의 latency 샘플이 여러 operation을 포함할 수 있다.

Percentile 계산 시 샘플 개수가 아닌 operation 수를 기준으로 누적한다.

```python
def _weighted_percentile(samples, q):
    samples_sorted = sorted(samples, key=lambda x: x[0])
    total_w = sum(w for _, w in samples_sorted)
    target = q * total_w
```

각 샘플의 weight는 해당 batch에 포함된 operation 수다.

---

## 실행 특성

- write는 Primary로 고정
- read는 Guard 이후 window 단위 전환
- Alternate 준비와 선택 조건은 분리
- Percentile은 op 단위 누적 방식으로 계산

---

## 트러블슈팅 기록

- [Alternate Selection](troubleshooting/01_alternate_selection.md)
- [Guard Phase](troubleshooting/02_guard_phase.md)
- [Routing Window](troubleshooting/03_routing_window.md)
- [Weighted Percentile](troubleshooting/04_weighted_percentile.md)

---

## 논문 정보

**D-HASH: Dynamic Hot-key Aware Scalable Hashing for Load Balancing in Distributed Cache Systems**  
TIIS (SCIE), 2026 (In Press)
