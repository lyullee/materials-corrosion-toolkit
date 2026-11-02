# 틈부식 잔여 구현 범위

## 2026-11-02 구현 현황 갱신 — 이동 체적 유압 이류

`integration.crevice_component_state_bdf` schema v5에 `CreviceDynamicHydraulicAdvection` 선택 입력을 연결했다. 리뷰된 pressure drop 및 전기중성 양쪽 reservoir 조성의 시간표, BDF clock·cell·species 순서, 전하수·원소 조성을 해시로 결합한다. signed inlet flow를 BDF 상태로 적분하고 각 RHS의 solid-equilibrium geometry와 cell liquid-volume rate, slit momentum, face continuity, upwind species/component flux, 경계 component·element·charge ledger를 유한 반복 고정점으로 함께 계산한다. 체적률은 성분 상태 방향의 유한차분으로 추정한다.

경계 component reservoir 교환을 최종 global component closure에 포함하고 dynamic face flux를 적분된 face-state ledger에도 기록하도록 보완했다. 코드 검토에서 dynamic 경로가 null인 fixed-geometry schedule에 도달하던 공통 RHS 분기와 phase/hydraulic physical-scope·slit-width 결속 누락도 수정했다. fixed-point가 수렴한 stage의 체적률을 후속 재평가 없이 그대로 최종 RHS에 사용한다. schema-v6 kinetic solids 연결은 별도 2-cell synthetic BDF 사례로 실행 확인했지만, moving-hydraulic branch 자체의 수치 검증은 아직 없다. Faradaic area feedback은 허용하지 않으며 압축성/난류 및 독립 물리 적용성 검토는 잔여다.

기존 구현 목록의 `degradation.crevice_chemistry` 미완성 한 항목은 다음 다섯 요구를 포함한다. 한 항목이라는 이유로 단일 함수 수정으로 완료할 수 있다고 해석하지 않는다. 아래는 완료 주장이 아니라 남은 작업의 분해다.

| 요구 | 현재 상태 | 남은 작업 |
|---|---|---|
| 형상이 변하는 유동·반응 수송 | BDF 경로 구현; fixed-volume kinetic end-to-end만 검증 | moving-hydraulic 체적 변화·정지 유량·경계 flux 및 ledger 사례를 수치 검증; 실험·적용 범위는 별도 확인 |
| 동적 전극 전위·공간 화학 | schema-v7 same-stage Cdl/Ohmic/BV RHS 코드 및 digest/Evidence 계약 연결 | v7 요청 종단간 실행, charge/전류·성분 ledger 극한 사례, 외부 실험 적용성 및 재료별 parameter 검증은 대기 |
| 적분 단계 내부 핵생성·석출 속도 | schema-v6 코드 및 2-cell synthetic end-to-end 실행 확인 | seed/depletion·경계·수렴 사례를 확대 검증; caller kinetic data의 물리 적용성은 별도 검증 |
| 열화학 반응·상 후보 선정 | caller가 증거와 함께 지정한 유한 후보 집합의 경쟁 고체 평형 API 존재; 후보 밖의 자동 상 발견은 공급자 의존 | 현재 범위에서는 새 scoring/선정 API를 추가하지 않는다. 외부 열화학 자료 공급자가 준비되기 전까지 후보 집합 밖의 자동 발견은 미지원으로 명시 |
| 벽 반응식의 독립 검증 | 데이터·검증 대기 | 보정 자료와 분리된 실험, 절차·조건·관측 근거로 적용 범위 평가 |

## 현재 저장소의 재사용 경로와 실제 접합 간극

| 결합 대상 | 이미 존재하는 실행 경로 | 아직 없는 same-stage 연결 |
|---|---|---|
| moving geometry와 성분 반응 수송 | `restricted_transport.py`는 digest 추적 geometry knot에서 셀/면 단면적을 보간하고 `dV/dt` 희석항, 반응 callback, Nernst–Planck/이동 flux, 벽·경계 적분 장부를 계산한다. 별도 schema-v6 component-state BDF는 kinetic solid occupancy를 trial geometry에 사용한다. | restricted-transport operator와 component-state BDF의 공통 monolithic solver는 없다. BDF kinetic/dynamic-geometry 분기는 end-to-end volume-change 사례 검증이 남아 있다. |
| pressure-driven moving-volume hydraulics | 위 독립 solid-volume stage API와 함께 `crevice_component_state_bdf.py` schema v5의 `CreviceDynamicHydraulicAdvection` 경로가 있다. BDF 상태에 signed inlet flow를 넣고 같은 RHS에서 trial solid geometry, directional volume-rate estimate, slit momentum, face continuity, upwind component flux와 reservoir ledger를 damped fixed point로 잇는다. | 계산 경로는 추가했으나 아직 실행 검증·경계 사례 확인 전이다. 유한차분 체적률 오차, fixed-point 수렴률, 유량 역전, 매우 작은 체적 변화, 장부 허용오차와 실제 자료 적용성을 일괄 검증해야 한다. 이 경로는 Faradaic 면적 피드백을 지원하지 않는다. |
| 적분 단계 핵생성·석출 | `crevice_bdf_kinetic_phase_set.py`가 셀별 상, 초기 고체량, 핵생성·성장 법칙을 digest로 고정한다. schema v6 BDF는 용존 activity/saturation/rate와 seed/depletion event를 동일 요청·적분 경로에 연결한다. | 2-cell synthetic event·solid inventory·component closure 사례는 통과했다. kinetic parameters의 현장 적용성, 더 넓은 depletion/reappearance 및 dynamic hydraulic 연계는 추가 검증 대상이다. |
| 동적 전위·공간 화학 | schema-v7 `dynamic_double_layer`는 BDF trial마다 trial 화학·공간 Ohmic 전류·Butler–Volmer branch·계면 전하율을 같은 RHS에서 계산한다. | 절연 양단/고정 형상 범위에서의 추가 수치 극한 검증 및 caller 자료의 물리 적용성 검토가 남는다. 외부 회로 구동, 이동 형상·유압 혼합은 현재 계약의 범위 밖이다. |

따라서 새 BDF 경로의 코드 추가만으로 동적 반응 유동 결합을 검증 완료 처리하지 않는다. 요청 시 체적률은 trial 상태 방향의 유한차분으로 추정되고, 고정점 수렴에 실패하면 해당 RHS에서 계산을 중단한다. 우선 이 구현의 보존·수렴·경계 극한을 수치적으로 확인하고, 이후 same-stage Faradaic/전극 면적 피드백은 별도 API 요구로 추적한다.

`integration.crevice_component_state_bdf`는 기본적으로 고정 체적의 성분량을 적분한다. 선택형 instantaneous solid geometry는 동적 유압 schedule과 함께 쓸 수 있으나 stage Faradaic coupling 및 fixed-geometry hydraulic history와는 함께 쓸 수 없다. 새 동적 유압 모드는 비압축 뉴턴 유체의 층류 슬릿 축소 모델이고, 움직이는 고체의 역학·공극·압축성·난류를 계산하는 일반 이동 경계 CFD가 아니다.

`integration.crevice_bdf_nucleation_operator_split`는 수송 구간을 완료한 뒤 핵생성·석출 계산을 적용한다. 계산이 존재하더라도 적분 단계 내부의 결합 계산과 구분해야 한다. 동적 이중층 결과를 일정에 연결하는 기능 역시 화학 상태가 전위 계산에 되먹임되는 동시 적분을 의미하지 않는다.

2026-11-02 갱신: same-stage kinetics schema-v6 경로는 두 셀 synthetic seed 사례로 종단간 실행했으며 관련 suite를 재실행해 30/30 통과(122.76초)했다. standalone RC 사례도 해석해와 대조했다. 동적 Cdl/Faradaic potential과 공간 화학의 same-stage 피드백은 schema-v7 실행 코드와 schema/catalog 연결을 추가했다. 현재 확인한 테스트는 Cdl 역산·입력 digest 계약과 기존 v6 회귀 범위이며, v7 전체 계산 요청의 종단간 수치 검증은 별도 검증 묶음에 남긴다. caller가 지정한 후보군의 경쟁 고체 평형은 기존 API 범위에 포함하며 후보 밖 자동 상 발견은 공급자 의존으로 둔다. moving-hydraulic kinetic branch도 end-to-end 검증이 남아 있다. 검증된 벽 반응 법칙과 독립 실험 qualification은 데이터·공급자·검증 과업으로 분리한다.

종단간 synthetic 검증 갱신(2026-11-02): schema-v6 BDF 요청을 두 셀로 구성해 실제 계산했다. 같은 trial의 Davies 평형·kinetics와 핵생성 이벤트 후 고체 inventory 및 성분 폐합을 확인했고 focused suite 재실행은 30/30 통과(122.76초)했다. 이 결과는 실행 코드 경로를 검증하지만 caller-provided kinetic constants의 물리 타당성을 검증하지 않는다. 남은 코드 공백은 dynamic Cdl/Faradaic potential과 spatial electrolyte chemistry의 same-stage feedback이다. 기존 competing-solid equilibrium은 caller가 지정한 유한 후보군을 다루며, 후보 밖 열역학 상 자동 발견은 외부 공급자 의존이다. 검증된 procedure wall law와 실험 qualification은 데이터·공급자 의존으로 남는다.

이 잔여 목록만으로 전체 기술 범위의 미완성 목록이 확정되는 것은 아니다. 미검토 요구와의 대응 확인도 계속 필요하다.

내부 구현은 `crevice_stage_kinetic_rates.py`의 단계별 속도·과포화도·성분 투영, `crevice_coupled_phase_state.py`의 공동 상태, `crevice_coupled_phase_rhs.py`의 같은 단계 연결, `crevice_coupled_phase_chemistry.py`의 기존 Davies 평형 어댑터까지 진행했다. 단순 종자 보유 폐쇄계의 내부 RHS는 BDF 결과를 해석해와 비교했고, 화학 어댑터는 실제 평형 계산에서 용존량 변화에 따른 농도·활동도 변화를 확인했다. 이것은 이벤트 적분기, 생산용 요청 근거, 공간 수송의 전체 연결과 독립 물리 검증이 완료됐다는 뜻은 아니다. 공개 완료 모델로 등록하지 않는다.

내부 `crevice_coupled_seed_bdf.py`는 종자 임계 이벤트에서 적분을 재시작한다. 같은 경계의 상승 방향 종자 표면은 64 binary64 ULP 범위에서 묶고, ODE 허용오차로 근접한 사건을 합치지 않는다. 두 셀 동시 전환·별도 근접 전환·그룹 예산 부족을 포함한 관련 14개 사례가 통과했다. 이 수치 정책은 물리적 사건 시각의 불확도나 모든 다중 사건의 정확성을 보증하지 않는다. 소진·재출현 및 전체 공간 수송의 생산용 계약은 계속 미완료다.
# Moving-volume hydraulic transport implementation note — 2026-11-02

`crevice_component_state_bdf` now has an opt-in moving-volume hydraulic transport path through `CreviceDynamicHydraulicAdvection`. It binds a reviewed pressure-drop and electroneutral reservoir-composition schedule to the exact BDF clock, cell order, species order, charge map, elemental formulas and declared fluid/slit support. The BDF state includes signed inlet flow; each RHS trial evaluates current solid-equilibrium aperture and volume, liquid-volume-rate continuity, slit momentum, upwind species/component fluxes and left/right component, element and charge reservoir ledgers.

The liquid-volume-rate/chemistry coupling is a bounded damped fixed-point calculation. Directional finite differences estimate how liquid volume changes along the component-state derivative. Schema-v6 same-stage kinetic solids can feed this geometry path through explicit kinetic phase inputs; the two-cell synthetic BDF check does not exercise the moving-hydraulic branch. Faradaic area feedback remains rejected. Mechanical deposition response, compressibility, turbulence, experimental flow-reversal validation and qualification are not claimed. Keep this path in the user-model/data-validation group pending its own numerical and physical review.

