# Wang–Brown 계열 전단 주기와 법선 변형률 excursion 연결

## 목적

`fatigue.wang_brown_temporal_normal_excursion`은 이미 계산된 단일 평면 전단 변형률 rainflow 주기의 시작·끝 표본 인덱스를 이용해, 그 구간에 놓인 법선 변형률 표본의 최솟값·최댓값과 차이를 반환한다. 기존의 독립 법선/전단 rainflow 결과를 겹침 최적화로 서로 배정하는 방식과 달리, 전단 주기를 기준으로 법선 채널의 시간 구간을 직접 읽는다.

## 공개 기술 근거와 구현 경계

Wang과 Brown의 1993년 논문은 최대 전단 변형률 역전 주기에 걸친 법선 변형률 excursion을 다축 피로 매개변수의 구성 요소로 논의한다. 본 API는 그 공개된 물리적 동기와 시간 결합 아이디어에 근거한 독립적인 유한표본 descriptor다. 논문의 식·표·설명 문장을 복제하지 않으며, 원 논문의 완전한 손상식이나 주기 계수 알고리즘이라고 주장하지 않는다.

- Wang, C. H. & Brown, M. W. (1993), “A path-independent parameter for fatigue under proportional and non-proportional loading,” *Fatigue & Fracture of Engineering Materials & Structures*, 16, 1285–1297. [DOI: 10.1111/j.1460-2695.1993.tb00739.x](https://doi.org/10.1111/j.1460-2695.1993.tb00739.x)
- 출처 식별자: `wang_brown_1993_normal_strain_excursion_on_maximum_shear_reversal`

## 입력 및 계약

- `projected_rainflow_result`와 그 canonical SHA-256: `fatigue.critical_plane_projected_rainflow`가 반환한 `computed` 결과.
- `plane_id`, `shear_projection`: 결과에 있는 단일 평면 및 지원되는 engineering shear projection.
- `normal_strain_values`, `normal_strain_sample_ids`: 전단 rainflow 결과와 동일한 순서·길이의 법선 변형률 표본 및 고유 ID.
- `normal_strain_source_id`, `normal_strain_source_sha256`, `normal_strain_evidence`: 법선 데이터 provenance.
- `same_ordered_sample_clock_reviewed`: 두 채널의 샘플 순서/시간 기준 동일성을 검토했음을 caller가 명시.

응답 cycle별 excursion은 `max(normal_strain[start:end+1]) - min(...)`으로 정의된다. 경계 인덱스는 양 끝을 포함한다. 출력에는 extrema sample ID와 원래 cycle count weight를 보존한다. half-cycle과 full-cycle의 가중치는 입력 rainflow 결과에 기록된 값을 그대로 사용한다.

## 한계와 사용

이 계산은 rainflow counting을 수행하지 않고, caller가 제공한 cycle list를 재배열하거나 재계수하지 않는다. 시간축은 cycle start/end 표본 인덱스로만 표현하므로 불균일 시간 간격을 보간에 반영하지 않는다. cycle 사이의 중첩/중첩 주기 손상 상호작용이나 표본 사이 연속 경로 극값은 복원하지 않는다. 반환값은 kinematic cycle feature이며, 그 자체로 Wang–Brown 손상식, Miner 누적, 수명, 파괴확률 또는 설계 판정에 투입할 수 없다. 별도 검증과 재료별 보정 전까지 계산 결과는 연구용 feature로 취급한다.

## API

```python
from matintegrity.wang_brown_temporal_excursion import (
    WangBrownTemporalExcursion,
    evaluate_wang_brown_temporal_excursion,
    specifications,
)

spec = specifications()[0]  # 명시적 registry 등록을 위한 ModelSpec 제공
request = WangBrownTemporalExcursion(...)
result = evaluate_wang_brown_temporal_excursion(request)
```

이 모듈은 standalone으로 제공된다. 프로젝트 중앙 registry, catalog, schema에는 자동 등록하지 않는다.
