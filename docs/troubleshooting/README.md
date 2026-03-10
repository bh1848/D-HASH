# 트러블슈팅 기록

D-HASH 구현 과정에서의 트러블슈팅을 기록한 문서다.

---

## 문서 목록

- [01 Alternate](01_alternate.md)
   가상노드 링에서 Alternate가 Primary와 동일 노드로 남는 경로,
   `cand != primary` 비교를 기준으로 좁힌 선택 구조.

- [02 Guard](02_guard.md)
   핫키 판정 직후 read 전환이 즉시 발생하던 경로,
   `delta < self.W` 조건으로 전환 시점을 분리한 구조.

- [03 Window](03_window.md)
   요청 단위 전환이 열 수 있는 교차 경로,
   `epoch = (delta - self.W) // self.W` 계산으로 고정한 window 기반 전환.

- [04 Weighted Percentile](04_weighted_percentile.md)
   파이프라인 환경에서 batch 단위 샘플이 percentile 기준 축을 바꾸는 경로,
   `(value, weight)` 누적 방식으로 op 단위 기준을 유지한 계산 구조.
