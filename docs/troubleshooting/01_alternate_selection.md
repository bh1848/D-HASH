# Alternate가 Primary와 동일 노드로 남는 실행 경로

## `_ensure_alternate()` 호출 이후에도 노드 id가 변경되지 않은 구간

핫키로 판정된 키에 대해 `_ensure_alternate()`가 호출되었지만,  
일부 키에서 `self.alt[key]`가 Primary와 동일한 노드 id로 기록된 구간이 있었다.

오프로딩 로직은 실행되었으나, read 라우팅 대상은 변경되지 않은 형태였다.  

---

## 가상노드 링에서 슬롯 이동과 물리 노드 구분은 다르다

Consistent Hashing 링은 가상노드를 사용한다.  
`sorted_keys`의 서로 다른 위치가 동일한 물리 노드 id를 가리킬 수 있다.

`ring[rk[j]]`가 반환하는 값은 물리 노드 id다.  
슬롯이 달라져도 반환되는 노드 id는 동일할 수 있다.

슬롯 이동과 노드 id 변경은 동일 조건이 아니다.

---

## `_ensure_alternate()`의 실제 실행 경로

```python
def _ensure_alternate(self, key):
    if key in self.alt:
        return

    rk = getattr(self.ch, "sorted_keys", None)
    ring = getattr(self.ch, "ring", None)

    if not rk or not ring or len(self.nodes) <= 1:
        self.alt[key] = self._primary_safe(key)
        return

    hk = self._h(key)
    i = bisect(rk, hk) % len(rk)
    primary = ring[rk[i]]

    stride_span = max(1, len(self.nodes) - 1)
    stride = 1 + (self._h(f"{key}|alt") % stride_span)

    j = i
    for _ in range(len(rk)):
        j = (j + stride) % len(rk)
        cand = ring[rk[j]]
        if cand != primary:
            self.alt[key] = cand
            return

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

## 조건에 따라 열리는 분기

`key in self.alt`  
→ 기존 Alternate가 존재하면 종료

`not rk or not ring or len(self.nodes) <= 1`  
→ `self.alt[key] = self._primary_safe(key)`  
→ 즉시 fallback

일반 경로:

1. `i = bisect(rk, hk) % len(rk)`
2. `primary = ring[rk[i]]`

이후 탐색:

- `stride = 1 + (self._h(f"{key}|alt") % stride_span)`
- stride 기반 점프 반복
- `cand != primary`를 만족하면 Alternate 확정

→ 실패 시

- 선형 스캔 반복
- `cand != primary`를 만족하면 Alternate 확정

→ 두 반복 모두 실패

- `self.alt[key] = primary`

---

## `self.alt[key]`가 Primary와 동일하게 남는 조건

다음 조건 중 하나에 해당하면 `self.alt[key]`는 Primary와 동일한 노드 id가 된다.

1. `not rk or not ring or len(self.nodes) <= 1`
2. stride 탐색과 선형 스캔에서 끝까지 `cand != primary`를 찾지 못한 경우

후자의 경우는 링 전체가 동일 물리 노드를 가리키는 구성일 때 발생할 수 있다.

로그에서는 어떤 분기가 실행되었는지를 기준으로 확인했다.

---

## 설계 관점 정리

Alternate 선정은 슬롯 이동이 아니라 `cand != primary` 비교에 의해 확정된다.  
가상노드 구조에서는 슬롯이 달라도 물리 노드가 같을 수 있다.

stride 기반 점프와 선형 스캔은 반복 연산을 추가한다.  
대신 물리 노드가 다른 경우에만 Alternate가 확정된다.

노드 수가 1인 구성에서는 Primary와 Alternate가 구분되지 않는다.  
이 경우 fallback 경로가 유지된다.
