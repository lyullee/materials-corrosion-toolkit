# 활동도 간극 수송에서 공간 고체상·간극 이력으로의 단계형 연결

## 목적

`integration.crevice_activity_transport_spatial_phase_aperture_handoff`는 고정·균일한 간극 geometry에서 계산된 활동도 보정 반응–Nernst–Planck history와 caller가 명시한 셀별 고체 반응속도/초기 고체 재고를 exact time/cell/species identity로 맞춘다. 구간별 고체 반응 extent를 액상 유한체적 상태에 적용하고, 고체 몰수와 caller 몰부피·coverage·침전 면 수를 이용해 다음 계산 구간에 전달할 셀별 간극 이력을 만든다.

이 계산은 한 구간의 수송 계산을 마친 뒤 반응/형상을 갱신하는 operator-split handoff다. 현재 입력된 수송 history를 다시 풀거나 같은 구간 안에서 geometry feedback을 반복하지 않는다.

## 구성식과 원장

각 phase `s`의 caller rate `r[s,i,k]`는 고체 진행량의 부호 규약(침전 양수, 용해 음수)으로 입력되며 인접한 두 knot의 interval 동안 상수로 해석된다.

\[
\Delta\xi_{s,i,k}=r_{s,i,k}(t_{k+1}-t_k),\qquad
n_{s,i,k+1}=n_{s,i,k}+\Delta\xi_{s,i,k}.
\]

고체 반응의 균형 stoichiometry를 통해 액상 농도는 수송 계산값에서 순누적 침전 extent를 빼고 용해 extent를 더한 값으로 갱신한다. 모든 종의 최종 농도와 각 상의 잔여 재고가 음수가 되면 그 시점은 commit하지 않는다. 고체 부피는 `phase concentration × fixed initial liquid cell volume × molar volume`로 산정한다. 셀 planform 면적 `width × cell length`에 대한 등가 평균 gap 변화와, caller가 선언한 면 수·coverage로 균등 배분한 covered-patch gap 변화를 함께 반환한다.

## Lineage 및 적용 조건

- activity transport는 `transport.crevice_activity_corrected_reactive_nernst_planck_1d`에서 `computed` 상태인 typed request/result여야 한다. 전체 result SHA, upstream input SHA, 물리 범위·asset·clock ID, exact time knots, cell 수, 종 순서와 charge/element mapping을 확인한다.
- kinetics는 `CompetingSolidKineticTransport` direct-interval-rate mode를 쓴다. 모델의 rate-law callback은 이 adapter가 실행하지 않는다. 모든 phase/interval/cell에 extent rate가 있어야 하고, kinetic campaign의 시간·균일 셀·초기 농도·단면적은 activity transport와 정확히 일치해야 한다.
- campaign의 neutral-solid 반응식은 이미 정의된 species의 charge·원소 균형을 따라야 한다. caller가 각 상의 몰부피를 입력하고 mapping digest를 Evidence에 고정한다.
- activity transport가 고정 cross-section 하나를 쓰므로 초기 aperture와 cell length는 균일해야 하며 초기 `aperture × transverse width`가 transport 단면적과 일치해야 한다. 침전 후 aperture는 셀마다 달라질 수 있다.
- finite-volume 수송 잔차, knot별 local charge diagnostics, 보정 후 액상 농도, 고체 재고와 nonnegative aperture를 확인한다. 실패 시 완료된 knot prefix와 최초 실패 위치를 기록한다.

## 출력 해석과 제한

반환된 `aperture_history`는 다음 segment를 구성하기 위한 caller geometry handoff다. 결과에 연결된 `phase_inventory_history`는 초기 액상 셀 부피 기준 solid inventory 농도와 셀별 총 고체 부피를 보존한다. 액상 종 농도는 수송 history에 고체 반응 extent를 적용한 구간 끝 상태다.

- 이 API는 수송–반응–형상 수식을 하나의 동시 연성 solver로 풀지 않는다. 고체 extent는 각 activity transport 구간 후 적용하고 새 aperture는 다음 segment에서만 쓸 수 있다.
- 동시 계산된 본 구간에서 침전이 농도·활동도·전류를 바꾸는 feedback은 계산하지 않는다. activity transport result를 phase rate에 사용한지 여부는 caller가 별도 kinetic provenance로 확인한다.
- 상 선택·자동 speciation·활동도 생성·Ksp 계산·phase discovery·벽면 kinetics를 수행하지 않는다. 수송 결과와 solid-rate campaign의 숫자가 정확히 대응하더라도 물리적 독립검증이나 qualification은 아니다.
- coverage 내부 균일 침전과 면별 균등 분할을 가정한다. 국부 형상, 공극률, 부착, 재배치, pit morphology, 균열 및 acceptance/risk를 추론하지 않는다.
- 활동도 보정 수송 API의 단면적이 고정이므로 초기 비균일 geometry를 지원하지 않는다. 이 출력은 후속 variable-area/geometry-aware solver에 연결해야 한다.

## Python API

```python
from matintegrity.crevice_activity_transport_phase_aperture import (
    CreviceActivityTransportPhaseApertureRequest,
    evaluate_crevice_activity_transport_phase_aperture,
)
```

Source IDs: `caller_activity_corrected_reactive_transport_history`, `caller_cellwise_competing_solid_kinetic_rate_campaign`, `caller_solid_molar_volume_and_deposition_coverage`, `sequential_finite_volume_phase_inventory_to_slit_aperture_handoff`.

이 API는 단계형 수치 연결만 추가하며 `degradation.crevice_chemistry` 전체를 완료 상태로 바꾸지 않는다. Registry·schema·capability/source catalog 연결은 완료했다. 자동 speciation/상 전이, 침전 속도 검증, 벽면 열화법칙 및 동시 이동경계 PDE 잔여가 유지된다.
