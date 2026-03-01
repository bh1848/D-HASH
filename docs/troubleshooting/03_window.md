# 핫키 구간에서 요청 단위로 교차하던 라우팅 경로

## 연속 요청인데도 노드 id가 교차된 구간

특정 핫키에 대해 연속 요청이 들어오는 구간에서
Primary와 Alternate 노드 id가 짧은 간격으로 교차 기록된 구간이 있었다.

같은 키에 대한 요청인데도 라우팅 대상이 변경되었고,
그 직후 캐시 미스가 이어지는 형태가 관찰되었다.

동일 키에 대한 캐시 적중 구간이 길게 유지되지 않는 흐름이었다.

---

## `get_node()`의 read 경로

```python
def get_node(self, key, op="read"):
    if op == "write":
        return self._primary_safe(key)

    cnt = self.reads.get(key, 0) + 1
    self.reads[key] = cnt

    if cnt < self.T and key not in self.alt:
        return self._primary_safe(key)

    self._ensure_alternate(key)

    delta = max(0, cnt - self.T)

    if delta < self.W:
        return self._primary_safe(key)

    epoch = (delta - self.W) // self.W
    return self.alt[key] if (epoch % 2 == 0) else self._primary_safe(key)
```

---

## 핫키 판정 이후 실행 경로

`cnt >= self.T`
→ `_ensure_alternate(key)` 호출
→ `delta = max(0, cnt - self.T)` 계산

`delta < self.W`
→ Primary 유지

`delta >= self.W`
→ `epoch = (delta - self.W) // self.W` 계산
→ `(epoch % 2 == 0)`이면 Alternate
→ 그렇지 않으면 Primary

전환은 `delta` 자체가 아니라
`(delta - self.W) // self.W`의 값에 의해 결정된다.

---

## 요청 단위 조건이 열 수 있는 경로

전환 조건이 요청 단위로 직접 평가된다면 다음과 같은 흐름이 가능하다.

핫키 판정
→ `delta` 증가
→ 조건 만족 시 Alternate
→ 다음 요청에서 조건 변화
→ 다시 Primary

임계값 근처에서 조건이 오가면
→ 노드 id가 요청 단위로 교차
→ 동일 키가 서로 다른 노드로 반복 이동

이 경우 동일 노드에 캐시가 누적될 구간이 짧아질 수 있다.

---

## `(delta - self.W) // self.W`가 고정하는 전환 구간

현재 구조에서는 다음 흐름이 만들어진다.

`delta` 증가
→ `(delta - self.W) // self.W` 계산
→ 동일 epoch 구간에서는 동일 노드 id 유지
→ epoch이 증가하는 시점에서만 전환 발생

전환은 매 요청마다 발생하지 않는다.
`self.W` 요청 단위로만 발생한다.

---

## 로그에서 관찰된 변화

수치는 기록하지 않았다.

동일 워크로드에서 노드 id가 요청 단위로 교차하던 구간은 보이지 않았고,
전환은 `self.W` 요청 단위로만 발생하는 형태로 기록되었다.

---

## 설계 관점 정리

Alternate 선택은 부하 분산을 위한 경로다.
전환 주기가 짧으면 동일 키의 캐시가 두 노드 사이를 오간다.

`self.W`는 전환 빈도와 동일 노드에 머무는 구간 길이를 동시에 결정한다.
값이 작으면 전환은 잦아지고,
값이 크면 동일 노드에 유지되는 구간이 길어진다.
