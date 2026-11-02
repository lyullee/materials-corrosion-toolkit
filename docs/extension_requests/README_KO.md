# 다른 프로젝트 확장 요청

이 요청서는 MatIntegrity의 중립 계약을 다른 프로젝트에서 받을 때 필요한 변경을 설명한다. 상대 저장소가 이미 변경됐다는 뜻은 아니다. 사용자 데이터와 버전이 있는 JSON을 통해 별도 프로세스로도 연결할 수 있다.

| 대상 | 요청서 | 핵심 |
|---|---|---|
| PRISM | `PRISM_KO.md` | 모델 유래 기간 확률과 문헌 빈도의 의미 분리 |
| human-reliability-toolkit | `HUMAN_RELIABILITY_TOOLKIT_KO.md` | 기회당 실패확률 의미와 HRA 증거 문맥 보존 |
| hydrogen-physical-models | `HYDROGEN_PHYSICAL_MODELS_KO.md` | 수소 수송 이력·보존량·solver 계보 교환 |
| process-monitoring-toolkit | `MONITORING_KO.md` | 손상·검사 특징의 단위·시간·출처 확장 |
| lh2dt_models, hydrogen-station-sim 및 psa-dyna | `PROCESS_HISTORY_KO.md` | 압력·온도·품질·공통 시계, 검토된 국부 정압·속도 및 다성분 transient stream state 공급 |
| SAGA-PY | `SAGA_KO.md` | 구조화된 건전성 결과의 근거 설명 |
| ammonia-supply-risk 및 QSafety | `MATERIALS_PROBABILITY_KO.md` | 점수·물리 상태·사건 확률·추정기 분리 |
| prism-dynasense | `DYNASENSE_KO.md` | 일반 평가 callback·표본 수렴·상관 입력과 추정 오차 |
| hydrogen-local-energetics | `ATOMISTIC_TRANSPORT_KO.md` | 원자 규모 근거와 검토된 수송 파라미터 교환 |
| 구조·FE·노치해석 공급자 | `FE_LOCAL_TENSOR_KO.md` | 좌표계·measure·mesh·위치·shear convention을 보존한 국부 tensor 이력 |
| Sandia HELPR | `HELPR_KO.md` | 버전·설정·자산·표본 의미를 보존한 수소 배관 수명기준 CSV 교환 |
| Pipeline Integrity Toolkit | `PIPELINE_INTEGRITY_TOOLKIT_KO.md` | 공통 배관 평가 결과를 모델·단위·문맥·source-tree identity와 함께 송신 |
| 파열압 모델·FE 공급자 | `BURST_PRESSURE_PROVIDER_KO.md` | 압력 기준·입력 digest·분할을 보존한 예측 결과 교환 |
| 기상·환경 노출 공급자 | `ATMOSPHERIC_EXPOSURE_KO.md` | 위치·기간·측정/재분석 구분과 전이 실패 상태를 보존한 대기부식 공변량 |
| FTA·동적 위험성 공급자 | `ACTION_RISK_PROVIDER_KO.md` | 동일 사건·범위·기간에서 행동별 잔여 최초고장확률과 evaluator digest 제공 |
| api581-risk-analysis | `API581_RBI_KO.md` | damage·inspection·PoF·consequence 의미와 digest를 보존한 양방향 RBI 교환 |
| process-risk-consequence-toolkit | `PROCESS_RISK_CONSEQUENCE_KO.md` | 건전성 사건확률과 외부 source/release/consequence 계보를 분리한 교환 |
| 크리비스 전기화학 소비자 및 downstream FTA/건전성 모듈 | `CREVICE_ELECTROCHEMISTRY_KO.md` | 기존 순차 이력과 current-carrying NP/Faradaic API의 BDF-stage source/mixed-potential 모드, digest/폐합 계보 및 위험 해석 경계 |
| current-carrying crevice/Faradaic 결과의 downstream FTA | `CORROSION_CURRENT_CARRYING_FTA_EXTENSION_KO.md` | computed 상태·모델/request/result digest·자산/기간을 보존하고 caller가 독립 제공한 확률만 FTA 기본사건으로 결합 |
| aqueous chemistry/speciation provider | `AQUEOUS_CANDIDATE_NETWORK_PROVIDER_KO.md` | balanced candidate→Evidence-backed manual thermodynamic binding→mass-action assembly workflow를 공개 thermodynamic provider 및 speciation consumer와 연결 |
| process consequence 및 risk/FTA 세션 | `GASKET_LEAKAGE_EXPOSURE_KO.md` | finite correlated gasket leak amount를 별도 consequence/reliability event mapping에 연결하며 amount를 probability로 오인하지 않도록 경계 |
| 크리비스 외부 solver 공급자 | `CREVICE_EXTERNAL_SOLVER_KO.md` | 공급자 solver 결과·상태 digest와 inventory history 사이의 교환 계약 |
| Crevice mixed-potential component-state BDF와 이중층 계면 상태 | `CREVICE_DOUBLE_LAYER_BDF_COUPLING_KO.md` | 계면전하/전위 state, Faradaic·ionic·capacitive stage balance, ledger 및 implicit solver 검증 요구 |
| Crevice 후속 고정 형상 구간 소비자 | `CREVICE_COMPONENT_STATE_SEGMENT_HANDOFF_KO.md` | 확정 BDF 결과 재고를 digest·ledger로 검증하고 caller 제공 새 형상 mapping으로 다음 segment 초기 상태를 구성 |
| Crevice component-state BDF와 고체상 평형 provider | `CREVICE_COMPONENT_BDF_SOLID_EQUILIBRIUM_KO.md` | 총 성분 inventory의 aqueous/solid 분배, stage active-set 상평형, NP flux 및 전체 성분 ledger 연성 |
| FEM/파괴역학 `K_I` 공급자와 SCC 성장 소비자 | `SCC_STRESS_INTENSITY_PROVIDER_KO.md` | Mode-I 응력확대계수 이력과 형상/solver 계보를 SCC `da/dt` 계약으로 전달하며 Paris 피로 및 확률 추론을 분리 |
| gasket transient/fabrication consumer | `GASKET_TRANSIENT_SCENARIO_EXPOSURE_KO.md` | 시간변화 gasket 상태 및 scenario exposure 확장 경계 |
| wet-CO₂ phase provider | `WET_CO2_ELEMENTAL_PHASE_HANDOFF_PROVIDER_EXTENSION_KO.md` | 공급자 phase history와 원소 inventory 전달 계약 |
| gasket FE 공급자 | `GASKET_EXTERNAL_FE_RECEIPT_KO.md` | 접촉 압력·변형 history와 FE 해석 계보 receipt 연결 |
| WCO₂ chemistry provider | `WCO2_CHEMISTRY_BOUNDARY_KO.md` | BDF-stage mass-action speciation, caller-evidenced Davies/SIT/B-dot 옵션 및 species/reaction/phase/provider 경계 |
| fatigue life consumer | `MULTIAXIAL_LIFE_SCENARIO_ENVELOPE_KO.md` | 상관을 보존한 finite multiaxial life scenario 결과 소비 계약 |
| structural FAD history to downstream FTA | `FAD_TIME_HISTORY_TO_FTA_KO.md` | 구현된 FAD 시간 이력과 고정 boundary를 digest 검증하고 caller의 기간 최초초과 확률만 기존 FTA event로 전달하는 어댑터 |
| tube-bundle integrity evidence consumer | `TUBE_BUNDLE_PRESSURE_STRESS_KO.md` | 독립 tube별 Lamé pressure-stress history를 tube/bundle evidence에 lineage와 함께 연결 |
| welding WPS/preheat heat-input consumer | `WELDING_WAVEFORM_ENERGY_UNCERTAINTY_KO.md` | waveform heat-input first-order standard uncertainty를 procedure envelope에 확률 의미와 분리해 전달 |

공통 기준 스키마는 `matintegrity.contracts`, `matintegrity.adapters`, `matintegrity.records`의 JSON Schema다. 송신·수신 모두 자산·부위·출처 해시와 평가기간을 보존한다. 계약 검증, 실제 서비스 교환, 물리적 통합 검증을 각각 기록한다.

개발 중 결과 계약에는 `probability_semantics`가 추가됐다. 의미가 없는 기존 결과는 빈 dict로 읽지만 사건 변환에서는 허용하지 않는다. 각 수신 측도 최신 스키마로 갱신하고 공간 크기 초과·POD·기간 최초고장을 구분하는 인수 검사를 추가한다.


| Crevice component-state BDF와 transient hydraulic consumer | `CREVICE_HYDRAULIC_COMPONENT_ADVECTION_KO.md` | digest·clock·mesh를 보존한 signed inertance flow, upwind 성분 flux 및 경계 원소/전하 장부 전달 |

| Crevice nucleation-kinetic history consumer | `CREVICE_NUCLEATION_KINETIC_HISTORY_KO.md` | molar nucleation source와 saturation/growth law Evidence·digest, aqueous/solid 및 element/charge history 전달 |

| Crevice component-state BDF와 caller geometry segment consumer | `CREVICE_COMPONENT_STATE_SEGMENT_TRANSITION_KO.md` | committed 결과의 cellwise component moles를 새 digest-bound geometry의 다음 BDF request로 넘기는 경계 operator split |

<!-- generated-extension-request-index -->

## 추가 연동 요청

아래 목록은 실제 요청서 파일에서 생성한다. 요청서의 존재는 상대 프로젝트의 구현 완료를 뜻하지 않는다.

| 요청서 | 제목 |
|---|---|
| `CREVICE_BDF_NUCLEATION_OPERATOR_SPLIT_KO.md` | Downstream extension request: component BDF and seed-ledger split |
| `CREVICE_CELLWISE_NUCLEATION_TRANSPORT_EXTENSION_KO.md` | Downstream extension request: cellwise nucleation ledgers into transport |
| `CREVICE_DYNAMIC_DOUBLE_LAYER_BDF_BINDING_KO.md` | Downstream request: stage-resolved dynamic Cdl and Faradaic coupling |
| `CREVICE_DYNAMIC_DOUBLE_LAYER_FARADAIC_HISTORY_KO.md` | Downstream request: spatially coupled dynamic double layer |
| `CREVICE_DYNAMIC_GEOMETRY_INTEGRATION_KO.md` | Downstream extension request: dynamic crevice geometry |
| `CREVICE_HYDRAULIC_DOUBLE_LAYER_COUPLING_KO.md` | Downstream extension request: crevice hydraulics and double-layer charge |
| `CREVICE_HYDRAULIC_PARAMETER_FIT_KO.md` | Downstream extension request: calibrated slit hydraulics |
| `CREVICE_MOVING_VOLUME_CONTINUITY_EXTENSION_KO.md` | Extension request: couple moving-volume continuity to hydraulic component BDF |
| `FLUX_GAS_SLAG_METAL_THERMODYNAMICS_KO.md` | 기체–슬래그–금속 열역학 확장 요청 |
