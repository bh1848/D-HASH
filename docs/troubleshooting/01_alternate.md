# Alternate가 Primary와 동일 노드로 남는 실행 경로

## `self.alt[key]`가 `primary`와 같은 값으로 남아있는 로그

핫키로 판정된 키에 대해 Alternate가 준비된 이후에도,
`self.alt[key]`가 Primary와 동일한 노드 id로 남아있는 로그가 있었다.

read 경로 전환이 열렸다고 가정했을 때 기대한 변화(대상 노드 id 변경)와 달라서,
Alternate 선정 경로에서 `self.alt[key]`가 어떤 조건으로 확정되는지부터 확인했다.

수치는 기록하지 않았다.

---

## `ring[rk[j]]`가 반환하는 값이 슬롯이 아니라 물리 노드 id인 전제

가상노드 기반 Consistent Hashing 링에서는 `sorted_keys`의 서로 다른 위치가
동일한 물리 노드 id를 가리킬 수 있다.

`ring[rk[j]]`는 현재 슬롯이 아니라 해당 슬롯이 가리키는 물리 노드 id를 반환한다.
따라서 슬롯이 이동하더라도 `cand`가 `primary`와 같게 유지되는 구간이 생길 수 있다.

---

## `cand != primary` 비교가 실패하는 동안 열려 있는 경로

아래 인용은 `ensure_alternate()` 내부 로직 중, Alternate 확정과 fallback에 직접 연결되는 부분이다.

```python
    if not rk or not ring or len(self.nodes) <= 1:
        # Fallback if cluster is too small
        self.alt[key] = self._primary_safe(key)
        return

    hk = self._h(key)
    i = bisect(rk, hk) % len(rk)
    primary = ring[rk[i]]

    # Use auxiliary hash to find a different node in the ring
    stride_span = max(1, len(self.nodes) - 1)
    stride = 1 + (self._h(f"{key}|alt") % stride_span)

    # 1. Try stride-based selection
    j = i
    for _ in range(len(rk)):
        j = (j + stride) % len(rk)
        cand = ring[rk[j]]
        if cand != primary:
            self.alt[key] = cand
            return

    # 2. Linear scan fallback (rarely hit)
    j = i
    for _ in range(len(rk)):
        j = (j + 1) % len(rk)
        cand = ring[rk[j]]
        if cand != primary:
            self.alt[key] = cand
            return

    self.alt[key] = primary
```

---

## `len(self.nodes) <= 1` 분기부터 `self.alt[key] = primary`까지의 실행 경로

`key in self.alt`
→ 이미 Alternate가 저장된 경우 종료

`not rk or not ring or len(self.nodes) <= 1`
→ `self.alt[key] = self._primary_safe(key)`
→ 즉시 종료

일반 경로:

1) `i = bisect(rk, hk) % len(rk)`
2) `primary = ring[rk[i]]`
3) `stride = 1 + (self._h(f"{key}|alt") % stride_span)`

stride 탐색:

- `j = (j + stride) % len(rk)` 반복
- `cand = ring[rk[j]]` 계산
- `cand != primary`가 성립하면 `self.alt[key] = cand`로 확정 → 종료

→ stride 탐색이 끝까지 실패하면

선형 스캔 fallback:

- `j = (j + 1) % len(rk)` 반복
- `cand = ring[rk[j]]` 계산
- `cand != primary`가 성립하면 `self.alt[key] = cand`로 확정 → 종료

→ 두 반복 모두 실패하면

- `self.alt[key] = primary`

---

## `self.alt[key]`가 Primary와 동일해지는 조건

`self.alt[key]`가 Primary와 동일한 노드 id로 남는 경로는 두 가지다.

1) `not rk or not ring or len(self.nodes) <= 1` 분기
→ `self._primary_safe(key)`가 반환하는 노드 id가 저장된다.

2) stride 탐색과 선형 스캔에서 끝까지 `cand != primary`가 성립하지 않는 경우
→ 마지막 줄에서 `self.alt[key] = primary`가 저장된다.

이 경우는 슬롯은 이동했지만 `ring[rk[j]]`가 계속 같은 물리 노드 id를 반환하는 구간이 길게 이어질 때 열린다.

---

## `cand != primary` 비교가 실패하면 Primary가 저장되는 구조

`cand != primary` 비교가 성립하지 않으면 Alternate는 확정되지 않는다.
슬롯 이동이 발생해도 `ring[rk[j]]`가 동일한 물리 노드 id를 반환하면 비교는 계속 실패한다.

stride 탐색과 선형 스캔은 후보를 반복적으로 변경한다.
그러나 두 반복 모두 `cand != primary`를 만족하지 않으면 마지막 줄에서 `self.alt[key] = primary`가 실행된다.

이 구조에서는 슬롯 위치가 아니라 물리 노드 id 비교가 결정 조건으로 작동한다.
노드 수가 1인 구성에서는 `len(self.nodes) <= 1` 분기에서 Primary 경로가 유지된다.
