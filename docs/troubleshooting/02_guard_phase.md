# 핫키 전환 직후 Alternate로 즉시 이동하던 실행 경로

## 핫키 판정 직후 Alternate에서 연속 미스가 기록된 구간

워크로드 반복 실행 중, 핫키로 판정된 직후 구간에서 응답 지연이 상승하는 패턴이 로그에 남았다.

같은 시점의 로그에는 Alternate 노드에서 캐시 미스가 연속적으로 기록되어 있었다.  
Alternate는 생성되었지만, 해당 노드는 아직 데이터가 채워지지 않은 상태였다.

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

## 조건에 따라 열리는 실행 경로

`cnt < self.T and key not in self.alt`  
→ 조건 만족 시 Primary 반환

→ 조건 불만족  
→ `_ensure_alternate(key)` 호출  
→ `delta = max(0, cnt - self.T)` 계산

→ `delta < self.W`  
→ Primary 유지

→ `delta >= self.W`  
→ `epoch = (delta - self.W) // self.W` 계산  
→ `(epoch % 2 == 0)`이면 Alternate  
→ 그렇지 않으면 Primary

---

## `key not in self.alt` 조건이 여는 경로

`_ensure_alternate()`가 한 번이라도 실행되어 `self.alt[key]`가 생성되면,

→ 이후 `cnt < self.T` 구간이라도  
→ `cnt < self.T and key not in self.alt` 조건은 성립하지 않는다  
→ early-return을 타지 않는다  
→ read는 항상 `_ensure_alternate()` 아래 경로로 내려온다

Alternate 생성 여부와 전환 시점은 다른 조건에서 결정된다.

---

## Guard가 없는 경우 열리는 경로

`delta < self.W` 조건이 없다면 실행 경로는 다음과 같다.

`cnt >= self.T`  
→ `_ensure_alternate()` 호출  
→ `delta = cnt - self.T`  
→ `epoch = delta // self.W`  
→ `(epoch % 2 == 0)`이면 Alternate 반환

핫키 판정 직후 `delta == 0`이면,

→ `epoch == 0`  
→ `(epoch % 2 == 0)` 성립  
→ 즉시 Alternate 반환

Alternate 생성 직후 read가 바로 해당 노드로 이동하는 경로가 열린다.

---

## `delta < self.W` 조건이 닫는 경로

```python
if delta < self.W:
    return self._primary_safe(key)
```

핫키 판정 직후 `delta == 0`이면,

→ `delta < self.W` 성립  
→ Primary 유지

처음 `W` 요청 동안은 Alternate가 생성되어 있어도 선택되지 않는다.  
전환은 `delta >= self.W` 이후에만 발생한다.

---

## Guard 이후 관찰된 변화

수치는 기록하지 않았다.

Guard 조건이 포함된 이후 동일 워크로드에서,  
핫키 판정 직후 Alternate 노드에 연속적으로 미스가 기록되던 구간은 보이지 않았다.

전환 직후 콜드 노드로 read가 이동하는 경로는 로그상에서 관찰되지 않았다.

---

## 설계 관점 정리

`_ensure_alternate()`는 Alternate를 생성하는 단계다.  
`delta < self.W`는 read가 해당 노드를 선택하는 시점을 제어한다.

대상 노드 확장과 전환 시점 제어는 서로 다른 조건으로 분리되어 있다.

Guard는 전환 시점을 지연시킨다.  
Primary는 `W` 요청을 추가로 처리한다는 비용이 발생한다.  
대신 핫키 판정 직후 구간의 경로는 제한된다.