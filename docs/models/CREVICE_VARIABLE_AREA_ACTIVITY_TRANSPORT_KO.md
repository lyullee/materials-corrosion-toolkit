# 가변 단면 간극 활동도 반응수송

`transport.crevice_variable_area_activity_corrected_reactive_nernst_planck_1d`는 기존 `CreviceActivityReactiveTransportRequest`의 종·활동도·경계·반응 계약을 재사용하고, caller가 제공한 시간별 cell/face 단면적을 이용해 유한체적 몰수 보존을 적분한다. 기존 scalar-area 계산 API는 수정하지 않는다.

코드: `matintegrity.crevice_variable_area_activity_transport`

## 입력

`VariableAreaCreviceActivityReactiveTransportRequest`에는 다음이 필요하다.

- 기존 activity-corrected reactive transport 요청: 시간절점, 종/전하/확산계수, cell별 활동도, mouth 경계, face velocity, 반응·속도 상수 일정
- `cell_cross_section_area_m2_by_knot`: 시간 우선 배열 `(n_time, n_cell)`
- `face_cross_section_area_m2_by_knot`: 시간 우선 배열 `(n_time, n_cell + 1)`
- geometry/provider/revision/configuration identity, 전체 area record digest, 해당 digest에 결합된 라이선스 Evidence
- 면적과 mesh mapping, 시간보간, 이동 체적 몰수/희석, face/boundary flux 기준, volume-flow 연속성에 대한 명시적 review

면적은 모든 절점에서 유한 양수여야 한다. 하위 transport request의 `cross_section_area_m2`는 새 solver에서 계산에 쓰지 않고, 첫 knot cell-area 산술평균을 가리키는 기준값으로 보존하며 일치 여부를 검사한다.

면적 계보는 다음 mapping의 `canonical_digest()`와 같아야 한다.

```python
area_record = {
    "geometry_id": geometry_id,
    "provider_id": provider_id,
    "provider_revision": provider_revision,
    "configuration_sha256": configuration_sha256,
    "time_s": list(transport_request.output_time_s),
    "cell_cross_section_area_m2_by_knot": cell_areas,
    "face_cross_section_area_m2_by_knot": face_areas,
}
area_history_sha256 = canonical_digest(area_record)
```

이 값은 `Evidence(source_id="caller_crevice_variable_area_history", sha256=area_history_sha256, ...)`로 고정한다. 사용자 계약과 usage authorization을 채운 뒤 API는 다음과 같이 호출한다.

```python
from matintegrity.crevice_variable_area_activity_transport import (
    VariableAreaCreviceActivityReactiveTransportRequest,
    evaluate_variable_area_crevice_activity_transport,
)

request = VariableAreaCreviceActivityReactiveTransportRequest(
    # transport_request, area arrays, digest/Evidence, identity, reviews
)
calculation = evaluate_variable_area_crevice_activity_transport(request)
```

## 이산식과 계산 경계

시간 knot 사이 cell 및 face 면적은 piecewise-linear로 보간한다. cell `i`의 몰수 상태는 `nᵢ = Cᵢ Aᵢ Δx`다. 입력 속도·면적 경계에서 유량밀도 `J`를 계산한 뒤 면적을 곱해 face molar rate를 얻고, concentration 미분에는 volume change 항을 포함한다.

`d(Cᵢ Aᵢ Δx)/dt = Aᶠᵢ Jᵢ − Aᶠᵢ₊₁ Jᵢ₊₁ + Rᵢ Aᵢ Δx`

여기서 `Rᵢ`는 기존 reversible mass-action network가 계산하는 순생성률이다. 적분은 knot마다 분할하여 area-slope 불연속을 넘어 solver step이 진행되지 않도록 하고 모든 요청 knot의 상태를 반환한다. boundary 유량 및 반응 source 적분을 별도 축적으로 유지해 종별 전역 inventory 잔차를 검사한다. 각 계산은 cell 전하중성, face zero-current 잔차, 음의 농도 및 유한체적 몰수 잔차 gate를 거친다.

또한 geometry 변화로 인한 `dV/dt`와 caller가 준 `uA` face flow의 차이를 각 시간구간 안에서 검사한다. 면적과 속도가 선형이므로 cell별 `Qin − Qout`은 시간 정규좌표에서 이차식이다. 끝점과 내부 극값을 확인해 구간 최대 연속성 잔차를 보고하고 tolerance를 넘으면 계산하지 않는다.

## 제한

- Cell/face 면적은 caller-provided 고정 입력 이력이다. 이 solver는 transport 결과로 geometry를 예측하거나 외부 geometry evaluator를 반복 호출하지 않는다.
- 유체 momentum, 벽운동, 난류, mesh 이동 또는 질량전달을 풀지 않는다. `d(CV)/dt`로 체적 변화에 따른 보존/희석만 처리한다. 유량 연속성은 caller velocity/area와의 일관성을 검사한다.
- 양이온·음이온은 같은 face의 공통 면적을 공유한다고 가정한다. face 단면적을 곱하기 전 flux density에 zero-current closure를 적용한다.
- 종·활동도·확산계수·기체/액체 경계·질량작용 속도 law는 모두 caller 입력이다. 자동 speciation, activity 계산, 고체상 전이, 부식률·수명·위험도 및 자격판정은 제공하지 않는다.
- 수치 보존 잔차는 알고리즘 일관성 지표이지 물리/실험 검증 증거가 아니다.
