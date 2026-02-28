# 트러블슈팅 기록

이 디렉토리는 D-HASH 구현 과정에서 확인된 실행 경로와 설계 판단을 정리한 문서 모음이다.

각 문서는 “문제–해결” 요약이 아니라,  
분기 조건이 어떤 실행 경로를 만들었는지와 그 경로를 어떻게 제어했는지를 기준으로 정리했다.

---

## 문서 목록

1. [01_alternate_selection.md](./01_alternate_selection.md)  
   가상노드 링에서 Alternate가 Primary와 동일 노드로 남는 경로,  
   `cand != primary` 비교를 기준으로 좁힌 선택 구조.

2. [02_guard_phase.md](./02_guard_phase.md)  
   핫키 판정 직후 read 전환이 즉시 발생하던 경로,  
   `delta < self.W` 조건으로 전환 시점을 분리한 구조.

3. [03_routing_window.md](./03_routing_window.md)  
   요청 단위 전환이 열 수 있는 교차 경로,  
   `epoch = (delta - self.W) // self.W` 계산으로 고정한 window 기반 전환.

4. [04_weighted_percentile.md](./04_weighted_percentile.md)  
   파이프라인 환경에서 batch 단위 샘플이 percentile 기준 축을 바꾸는 경로,  
   `(value, weight)` 누적 방식으로 op 단위 기준을 유지한 계산 구조.

---

## 작성 기준

- 분기 조건과 실행 경로를 함께 적는다
- 로그에서 관찰된 내용만 적는다
- 수치를 임의로 추가하지 않는다
- 대상(노드/키)과 시점(전환 직후/임계치 이후)을 분리해 적는다