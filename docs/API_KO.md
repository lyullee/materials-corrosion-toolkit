# Python API와 연동 계약

## 최신 독립 계산·연동 API

재검토 계산 묶음: 직접 에너지·관 시험압력·기준에너지 환산 4개 API는 [직접 입력 안내](models/DIRECT_ENERGY_AND_TEST_PRESSURE_KO.md), 배관 허용응력·냉각 상관식·수소 추정·연결부 압력 5개 API는 [사용자 계수 상관식 안내](models/ENGINEERING_CORRELATIONS_KO.md)를 참고한다. 공통 합성 예제 `examples/engineering_correlations.py`는 공개 registry의 Python/JSON 호출을 제공한다.

- `calibration.crevice_slit_hydraulic_law_parameters`: 독립 calibration group의 계측 유량에 reduced slit 저항·관성 multiplier 두 개를 가중 적합하고 별도 holdout을 평가한다. 적용 함수는 동일 provider/grid/physical scope와 pressure·aperture·fluid·clock fit support를 벗어나는 transfer를 거부한다. fitted user-model일 뿐 qualification이나 universal transfer는 아니다. [가이드](models/CREVICE_HYDRAULIC_PARAMETER_FIT_KO.md).

- `chemistry.crevice_nucleation_kinetic_history`: Evidence/digest-bound saturation intervals와 caller molar nucleation source를 입력받아 threshold 전에는 phase appearance, 이후에는 caller growth/dissolution law를 보수 ledger에 적용한다. 한 개 closed batch scope이며, 미시적 nucleation theory·입자분포·spatial transport는 포함하지 않는다. [모델 계약](models/CREVICE_NUCLEATION_KINETIC_HISTORY_KO.md).
- `integration.crevice_cellwise_nucleation_kinetic_history`: 같은 phase/law/provider 및 exact clock을 쓰는 고정 부피 셀 각각에 위 ledger를 적용하고, 모든 셀이 성공한 뒤에만 농도·고체 재고 이력을 몰수로 합산한다. 셀간 이동과 형상 feedback이 없는 operator-split ledger다. [가이드](models/CREVICE_CELLWISE_NUCLEATION_KINETIC_HISTORY_KO.md), [확장 요청](extension_requests/CREVICE_CELLWISE_NUCLEATION_TRANSPORT_EXTENSION_KO.md).
- `integration.crevice_bdf_nucleation_operator_split`: 각 구간의 aqueous-only fixed-volume BDF 수송을 먼저 계산하고, 셀별 seed/growth ledger를 적용한 뒤 수용액 성분 몰수를 다음 구간으로 넘긴다. 성분·원소·전하 폐합 후 구간별 atomic commit하며, within-interval 반응·수송 연성은 아니다. hydraulic/Faradaic/source/current/dynamic geometry 입력은 거부한다. [가이드](models/CREVICE_BDF_NUCLEATION_OPERATOR_SPLIT_KO.md), [확장 요청](extension_requests/CREVICE_BDF_NUCLEATION_OPERATOR_SPLIT_KO.md).
- `integration.crevice_dynamic_double_layer_faradaic_history`: caller 제공 signed polarization/Cdl 곡선과 total-current history에서 독립 lumped cell의 전위, Faradaic current, 저장전하 및 `I_total = I_F + dQ/dt` 폐합을 BDF로 계산한다. 곡선 support 밖 보간·외삽은 거부하며 공간 ohmic/NP 연성이나 자격화는 포함하지 않는다. [가이드](models/CREVICE_DYNAMIC_DOUBLE_LAYER_FARADAIC_HISTORY_KO.md), [확장 요청](extension_requests/CREVICE_DYNAMIC_DOUBLE_LAYER_FARADAIC_HISTORY_KO.md).
- `integration.crevice_dynamic_double_layer_to_component_bdf_binding`: 동적 Cdl/Faradaic 이력을 재계산 검증한 뒤 branch별 반응 extent, aqueous sign capacitive current, charge-closed ionic face-current를 typed BDF 요청으로 바인딩한다. 영 외부 전류 경계가 닫히지 않으면 거부한다. operator split이며 BDF 조성이 전위 이력으로 되먹임되지는 않는다. [가이드](models/CREVICE_DYNAMIC_DOUBLE_LAYER_BDF_BINDING_KO.md), [확장 요청](extension_requests/CREVICE_DYNAMIC_DOUBLE_LAYER_BDF_BINDING_KO.md).
- `integration.crevice_moving_volume_liquid_continuity`: digest/Evidence-bound aperture와 양쪽 boundary-flow knot 이력에서 셀별 `dV/dt = Q_left - Q_right`를 사용해 내부 면의 interval-mean 유량을 재구성한다. 좌우 경계 폐합이 맞지 않으면 commit하지 않는다. fixed mesh·비압축 액체 kinematic 연속 계산이며 압력/관성 momentum, species transport 또는 석출 kinetics와 아직 단일 RHS로 연성되지 않았다. [가이드](models/CREVICE_MOVING_VOLUME_CONTINUITY_KO.md), [후속 연동 요청](extension_requests/CREVICE_MOVING_VOLUME_CONTINUITY_EXTENSION_KO.md).
- `corrosion.crevice_moving_volume_hydraulic_history`: exact-knot aperture를 interval별 선형 보간하고 cell 체적률로 면별 유량 차이를 강제한 뒤, caller pressure forcing으로 series-slit 공통 유입 유량의 lumped resistance/inertance ODE를 적분한다. 면별 유량과 분배 cell pressure-drop closure를 반환한다. fixed mesh·비압축·wide laminar slit 한정이며 species/component transport, solid kinetics, 압력장 분포 및 qualification은 포함하지 않는다. [가이드](models/CREVICE_MOVING_VOLUME_HYDRAULIC_HISTORY_KO.md), [후속 연동 요청](extension_requests/CREVICE_MOVING_VOLUME_CONTINUITY_EXTENSION_KO.md).
- `integration.crevice_component_state_bdf` 선택형 `hydraulic_component_advection`: digest-bound slit inertance 결과를 고정 geometry BDF RHS에 연결하고, stage chemistry의 upwind 성분 유량 및 좌·우 reservoir 원소/전하 교환 ledger를 함께 적분한다. 이동 aperture/volume은 지원하지 않는다. [경계·수지 설명](models/CREVICE_COMPONENT_STATE_BDF_HYDRAULIC_ADVECTION_KO.md).
- `integration.crevice_component_state_bdf` 선택형 `capacitive_current_schedule`: caller가 exact-knot별 셀 전기이중층 전류를 제공하면 aqueous source charge continuity의 `ΔI = F·q̇ + I_cap` 폐합을 확인하고 charge ledger를 적분한다. 이 경로는 prescribed forcing이며, 전위 state 또는 stage mixed-potential/BV와의 monolithic 연성은 아니다. [BDF/Cdl 경계](models/CREVICE_COMPONENT_STATE_BDF_CAPACITIVE_CURRENT_KO.md).
- `integration.crevice_double_layer_to_component_bdf_binding`: 기존 Cdl charge history와 caller capacitive-current schedule을 셀·interval별 적분 전하로 대조한 뒤, 닫힐 때만 typed BDF request를 만든다. 전위/Cdl current는 caller가 준 값이며 operator-split binding이다. [가이드](models/CREVICE_DOUBLE_LAYER_BDF_BINDING_KO.md).
- `corrosion.crevice_hydraulic_stage_rhs`: 현재 유량·압력·간극·유체 상태에서 planar-slit R/I와 signed `dQ/dt`를 계산하는 순수 stage RHS다. 시간 적분이나 reactive/moving-volume 연성 solver는 아니다. [가이드](models/CREVICE_HYDRAULIC_STAGE_RHS_KO.md).
- `integration.crevice_component_state_bdf` schema v4 선택형 `instantaneous_solid_aperture_feedback`: caller가 Evidence/digest-bound phase molar volume·gap occupancy와 cell dimensions를 주면, 각 solid-equilibrium BDF stage에서 aqueous/solid partition과 액체 부피·aperture를 bounded damped fixed point로 연성하고 수렴 면적으로 NP current/flux를 계산한다. kinetics, nucleation, mechanics는 포함하지 않고 hydraulic/Faradaic spatial mode와 동시 사용을 거부한다. [가이드](models/CREVICE_COMPONENT_STATE_BDF_DYNAMIC_GEOMETRY_KO.md).

- `degradation.scc_crack_velocity_history`: caller가 검토한 thresholded `da/dt(K_I)` 표를 유한 `K_I(t)` history knot에서 적분한다. geometry feedback, initiation, qualification과 probability는 추론하지 않는다. [API 가이드](models/CHLORIDE_SCC_CRACK_VELOCITY_KO.md).
- `adapter.scc_crack_growth_to_fault_tree_basic_event`: exact SCC request/result를 재계산·digest 대조하고 별도 caller의 기간 최초고장확률만 FTA basic event로 전달한다. [가이드와 합성 예제](models/SCC_FTA_BINDING_KO.md).
- `structural.failure_assessment_history`: exact provider receipt knot와 digest-pinned caller FAD curve로 `Kr/Lr` 및 경계 여유를 평가하고 최초 바깥 구간을 bracket한다. [API 가이드](models/FAD_ASSESSMENT_HISTORY_KO.md).
- `adapter.fad_assessment_history_to_fault_tree_basic_event`: FAD history를 재계산 검증하고 independently caller supplied conditional-first-failure probability만 연결한다. [가이드와 합성 예제](models/FAD_FTA_BINDING_KO.md).
- `chemistry.crevice_component_solid_partition`: 한 cell 총성분 재고를 aqueous Davies/mass-action과 caller의 유한 고체상 후보로 bounded partition한다. caller phase 순서의 active-set 계산이며 global Gibbs minimum/유일성, nucleation 및 BDF coupling을 주장하지 않는다. [API 범위](models/CREVICE_COMPONENT_SOLID_PARTITION_KO.md).
- `data.mendeley_ahss1300_hydrogen_permeation_workbook_audit`: CC BY 4.0 고정 데이터 파일의 크기/hash pin과 worksheet 구조만 감사하고 raw cells를 반환하지 않는다. [데이터 계약](datasets/MENDELEY_AHSS1300_HYDROGEN_PERMEATION_KO.md).
- `integration.tube_bundle_lame_stress_history`: caller가 핀한 튜브별 현재 최소 벽두께와 내부·외부 절대압 exact knots에서 내·외면 Lamé 응력을 계산한다. 허용응력·압력용량·수명 판정은 하지 않는다. [가이드](models/TUBE_BUNDLE_LAME_STRESS_HISTORY_KO.md), [합성 예제](../examples/tube_bundle_lame_stress_history.py).
- `welding.waveform_energy_uncertainty`: 기존 용접 파형 적분에 전압·전류·효율·이동거리의 caller full covariance를 전달해 아크 에너지와 순 열입력의 1차 표준불확도를 산출한다. 확률·절차 적격 판정은 하지 않는다. [가이드](models/WAVEFORM_ENERGY_UNCERTAINTY_KO.md), [합성 예제](../examples/waveform_energy_uncertainty.py).
- `integration.crevice_component_state_segment_transition`: exact digest/ledger-closed BDF 결과의 최종 component moles를 셀별 그대로 다음 caller-geometry segment BDF request에 넣는다. Geometry는 Evidence/digest-bound 입력이며, 경계 간 operator split이지 BDF 내부 이동경계 연성이 아니다. [가이드](models/CREVICE_COMPONENT_STATE_SEGMENT_TRANSITION_KO.md).
- `integration.crevice_component_state_segment_handoff`: 확정된 component-state BDF 결과의 digest·재고 ledger를 확인하고, caller 검토 형상/고체 몰부피/간극 점유 mapping을 이용해 다음 고정 형상 구간의 초기 재고·후보 aperture를 구성한다. BDF stage 내부 이동경계 feedback은 하지 않는다. [가이드](models/CREVICE_COMPONENT_STATE_SEGMENT_HANDOFF_KO.md).

`integration.wet_co2_cylindrical_scale_recession_feedback`는 기존 transient cylindrical BV/수송 solver, phase별 caller saturation/kinetics 모델, cylindrical multilayer diffusion-supply limiter를 반복 평가한다. 제한된 Picard 반복으로 metal release, scale phase line inventory와 동일 exact-knot 원통 형상을 갱신하고, wall element 잔차와 phase inventory 수렴 후 strict wall-geometry closure를 재실행한다([모델 범위와 residual](models/WET_CO2_CYLINDRICAL_SCALE_RECESSION_FEEDBACK_KO.md)). Saturation kinetics/transport와 BV aqueous transport는 별도 caller 요청/반응 스케줄이므로 scale 침전을 BV 수송 ODE의 aqueous sink로 계산했다고 해석해서는 안 된다.

`integration.wet_co2_cylindrical_aqueous_scale_sink_feedback`는 caller가 exact knot별로 제공한 signed 상 반응 flux를 원통형 확산 공급량과 고체 재고에 맞춰 제한하고, 침전·용해 항을 Butler–Volmer와 같은 interval BDF 수지식에 넣어 수용액 농도를 함께 계산한다. 상 flux는 구간 내 좌측 값으로 유지되며, 자동 상 선택·수지/활동도/기체 종합 화학·실험 qualification을 제공하지 않는다([모델 범위](models/WET_CO2_CYLINDRICAL_AQUEOUS_SCALE_SINK_FEEDBACK_KO.md)).

`integration.wet_co2_cylindrical_stage_kinetic_scale_feedback`는 caller가 제공한 활동도 계수·기준농도·log Ksp와 precipitation/dissolution kinetic 계수로 BDF의 각 수치 평가점에서 벽면 농도 기반 반응속도를 다시 계산한다. 다상 공통 반응물의 원통 확산 공급량과 live solid 재고를 제한하고, exact-knot geometry 반복과 수지 장부를 기록한다. 활동도 및 log Ksp 기록은 interval 동안 좌측 knot 값으로 유지되며 phase discovery나 qualification을 하지 않는다([모델 범위](models/WET_CO2_CYLINDRICAL_STAGE_KINETIC_SCALE_FEEDBACK_KO.md)).

`integration.wet_co2_cylindrical_stage_speciation_scale_feedback`는 caller `AqueousMassActionSystem`의 고정 반응망과 표준상태를 사용하되, 매 BDF stage wall composition에서 보존식 target을 구성해 aqueous mass action/speciation을 다시 계산한다. 기본 schema v2는 template 활동도계수를 사용한다. `davies_activity`는 v2 이상, `sit_activity`는 v3, `bdot_activity`는 v4에서 caller의 온도별 계수·상호작용·Evidence로 이온강도와 활동도를 각 stage에서 반복한다. 세 설정은 서로 배타적이고 내장 parameter system은 stage template과 digest가 정확히 일치해야 한다. 계산된 무차원 활동도를 상별 침전·용해 law에 공급하고 그 source/sink를 BV transport와 같은 stage RHS에 연결한다. 반응망, 적용 모델 계수, log K, phase law는 caller가 지정하며 자동 species/phase discovery는 하지 않는다([모델 범위와 제한](models/WET_CO2_CYLINDRICAL_STAGE_SPECIATION_SCALE_FEEDBACK_KO.md)).

`integration.wet_co2_cylindrical_finite_gas_stage_speciation_scale_feedback`는 위 stage solver에 caller가 지정한 고정 용량 기체 저장조와 Henry/2막 전달을 결합한다. 기체 fugacity와 외부 원통 액상 셀 사이 전달률이 매 BDF stage의 동일 RHS에서 업데이트되며, 그 액상 재고가 벽 질량작용 평형, BV 반응, scale 반응에 이어진다. 기체 EOS, 반응망 자동 발견, 온도 변화는 포함하지 않는다([입력 및 수지 범위](models/WET_CO2_CYLINDRICAL_FINITE_GAS_STAGE_SPECIATION_FEEDBACK_KO.md)).

`integration.wet_co2_cylindrical_finite_gas_stage_geometry_feedback`는 동일한 기체·수용액·BV·scale 상태를 유지하면서, 각 BDF stage의 누적 벽 용출과 scale inventory로부터 bore 및 steel 반경을 다시 계산한다. 종 상태는 움직이는 원통 radial cell의 molar inventory로 적분해 geometry 변화 중 수지를 추적한다. Lagrangian mesh 가정과 경계 조건 검토가 필요하며 완전한 수력학적 유동 모델은 아니다([동적 geometry 계약](models/WET_CO2_CYLINDRICAL_FINITE_GAS_STAGE_GEOMETRY_FEEDBACK_KO.md)).

`integration.crevice_local_mass_action_projection`은 digest-bound crevice transport campaign의 각 exact knot와 cell에서 transported concentration과 caller의 linear component basis로 mass-action constraint target을 만들고 고정 활동도 solver를 실행한다. 활동도계수·반응·평형상수·온도·단일 액상 범위는 cell template에서 caller가 제공한다. 셀별 독립 operator split이며 시간사이 kinetics/transport feedback이나 고체상 전이는 계산하지 않는다([설명](models/CREVICE_LOCAL_MASS_ACTION_PROJECTION_KO.md)).

`integration.crevice_local_external_activity_projection`은 같은 cellwise projection에 caller가 주입한 외부 활동도 공급자를 연결해 각 셀의 질량작용식과 gamma를 반복 수렴시킨다. 결과 ledger에는 셀별 몰농도 표준상태 gamma와 provider/configuration lineage 및 고정점 transcript digest가 보존되어 후속 포화도 계산에 연결할 수 있다. provider runtime dependency, evidence 및 고정 topology가 필요하며 실패 knot는 부분 저장하지 않는다. 이 연결은 한 액상·독립 cell의 operator split로 제한되며 상변화·transport feedback·부식률은 계산하지 않는다([설명](models/CREVICE_LOCAL_EXTERNAL_ACTIVITY_PROJECTION_KO.md), [provider 계약](AQUEOUS_EXTERNAL_ACTIVITY_PROVIDER_KO.md)).

`chemistry.crevice_spatial_activity_solid_fixed_point`는 caller가 제공한 셀별 Davies activity/speciation과 유한 경쟁고체 평형을 번갈아 풀고, 고체 전이량만큼 수용액 선형 보존 제약을 갱신해 반복한다. 셀은 독립이며 고정 단일 geometry knot만 지원한다. 셀 간 수송, 혼합전위, Faradaic source, 가변 간극은 별도 계산 경로다([계약과 제한](models/CREVICE_SPATIAL_ACTIVITY_SOLID_FIXED_POINT_KO.md)).

`transport.crevice_spatial_activity_solid_nernst_planck_1d`는 caller가 지정한 variable-area Nernst–Planck 입력으로 exact-knot interval transport를 진행하고, 각 knot에서 Davies/speciation과 유한 고체 평형을 재계산해 다음 interval의 aqueous/solid 상태로 전달한다. 활동도는 구간 내부에서 좌측 knot 값으로 고정되는 operator-split 경로다([모델 범위](models/CREVICE_SPATIAL_CHEMISTRY_TRANSPORT_KO.md)).

`integration.crevice_spatial_chemistry_aperture_fixed_point`는 위 공간 transport/chemistry solver를 각 outer trial에서 다시 호출하며, caller의 고체 부피–간극 mapping과 간극–면속도 민감도로 exact-knot aperture 및 hydraulic history를 갱신한다. 두 residual과 하위 원소수지 gate가 함께 통과할 때만 commit한다. 고체 부피–간극 관계와 hydraulic 민감도는 caller model이며, monolithic intrastep chemistry나 pressure-flow 법칙을 제공하지 않는다([모델 범위](models/CREVICE_SPATIAL_CHEMISTRY_APERTURE_FIXED_POINT_KO.md)).

`integration.crevice_faradaic_spatial_chemistry_coupling`은 caller의 branch Nernst·Butler–Volmer 설정을 기존 variable-area transport 및 knot chemistry와 순차 연결한다. 구간 transport 뒤 endpoint Faradaic extent와 reservoir 원소 장부를 적용하고 chemistry를 재계산하며, endpoint mixed-potential/상태가 수렴해야 구간을 commit한다. 재사용 transport kernel은 각 면 전류 0을 요구하므로 비영 electrolyte face current는 거부된다. 따라서 ohmic current가 Nernst–Planck migration에 결합된 단일 연립해석이 아니다([모델 범위](models/CREVICE_FARADAIC_SPATIAL_CHEMISTRY_COUPLING_KO.md)).

`integration.crevice_external_activity_local_solid_saturation`은 위 결과의 선택 절점에서 각 셀의 후보 고체 포화비를 계산한다. 출력의 `physical_scope_id`, `elapsed_time_s`, candidate 순서와 cell별 결과 및 digest를 `integration.crevice_saturation_exposure_history`에 전달해 시간별 포화비 초과 구간을 연결할 수 있다. 후속 이력은 시간 0 시작, 엄격한 시간 증가, 절점 간 동일한 candidate/cell 순서를 요구하며 고체상 선택이나 시간 사이 보간을 하지 않는다([포화 screen](models/CREVICE_EXTERNAL_ACTIVITY_SOLID_SATURATION_KO.md), [이력 API](models/CREVICE_SATURATION_EXPOSURE_HISTORY_KO.md)).

`integration.crevice_external_activity_local_solid_saturation`은 위 projection 결과 중 caller가 선택한 exact knot의 cell마다 저장된 γ와 농도로 차원 없는 활동도를 만들고 기존 aqueous saturation screen을 호출한다. 전체 knot/commit 수, projection/result/cell/provider digest와 셀별 고정점 잔차를 재확인하고 성공 cell prefix를 보존한다. 고체 후보·Ksp·Evidence·온도와 표준상태 적합성은 caller 입력이며 이 API는 phase selection·침전량·속도론을 계산하지 않는다([계약](models/CREVICE_EXTERNAL_ACTIVITY_SOLID_SATURATION_KO.md)).

`data.mendeley_x80_srb_scc_typed_rows`는 Mendeley X80/SRB SCC dataset v1의 세 XLS 파일을 고정 크기·SHA-256으로 확인하고, caller 승인 아래 workbook/sheet/row/cell 순서와 저장 형식을 local-only typed row로 보존한다. 단위·시편 그룹·환경 조건·SCC 결과는 자동 해석하지 않는다. 제3자 자료 권리는 별도 확인 대상이다. [데이터와 사용 경계](datasets/MENDELEY_X80_SRB_SCC_TYPED_ROWS_KO.md).

`data.mendeley_az31b_corrosion_fatigue_typed_rows`는 Mendeley Data v1의 AZ31B/cold-spray AA7075/e-paint dataset에서 여덟 XLSX 파일을 provider 크기·SHA-256으로 확인하고 로컬 승인 후 workbook row를 원 셀 형식·순서·Evidence와 함께 typed import한다. 파일의 figure-number labels를 해석하거나 단위·시편·조건·fatigue life·부식률을 추론하지 않는다. CC BY 4.0 dataset notice에는 제3자 자료에 대한 추가 허가 주의가 있으므로 row-level provenance는 재사용 전에 별도로 검토해야 한다([데이터와 사용 제한](datasets/MENDELEY_AZ31B_CORROSION_FATIGUE_TYPED_ROWS_KO.md)).

`data.mendeley_mg_fsp_scc_typed_rows`는 Mendeley Data v1의 ZE41/AZ91D 및 friction-stir-processed 대응 workbook 4개를 고정 크기·SHA-256으로 확인하고 승인된 로컬 세션에서 원 셀과 workbook lineage를 typed row로 보존한다. 조건·단위·SCC susceptibility나 성능 차이를 추론하지 않는다. CC BY 4.0 공지와 제3자 자료 별도 허가 가능성을 데이터 및 rights 기록에 유지한다([데이터와 사용 제한](datasets/MENDELEY_MAGNESIUM_FSP_SCC_TYPED_ROWS_KO.md)).

`data.mendeley_explosive_weld_multilayer_fatigue_typed_rows`는 Mendeley Data v1 폭발용접 다층판 피로 workbook을 provider 크기·SHA-256으로 확인한 뒤 원 셀 순서와 provenance를 local-only typed row로 보존한다. 추가 `data.mendeley_explosive_weld_multilayer_fatigue_mapped_rows`는 caller가 명시한 sheet/header/row-range/field/unit/role 매핑만 적용하고 header 값이 달라지면 거부한다. 수식을 실행하거나 단위를 바꾸지 않으며, 피로법칙·부식률·allowable·서비스 적격성을 계산하지 않는다. CC BY 4.0와 제3자 자료 허가 주의가 적용된다([데이터와 사용 제한](datasets/MENDELEY_EXPLOSIVE_WELD_MULTILAYER_FATIGUE_TYPED_ROWS_KO.md)).

`data.mendeley_aisi1018_aerobic_corrosion_file_inventory`는 Mendeley Data v1의 AISI 1018 호기성 미생물 부식 자료 22개 파일에 대해 제공자 ID·크기·SHA-256만 확인한다. 서로 다른 text/OPJ 형식의 열 의미·단위·시편 관계가 확정되지 않아 측정값을 파싱하지 않으며, 파일명 mapping은 caller가 Evidence와 함께 직접 선언해야 한다. 원자료는 local-only이고 제공자 CC BY 4.0의 제3자 자료 허가 주의가 적용된다([자료 권리와 제한](datasets/MENDELEY_AISI1018_AEROBIC_CORROSION_INVENTORY_KO.md)).

`adapter.crevice_faradaic_to_fault_tree_basic_event`는 digest가 정확히 일치하고 모든 시간구간이 committed인 Crevice/Faradaic `Calculation`만 기존 FTA `FaultTreeBasicEvent` 계약에 연결한다. 확률, 의미, 조건화, 범위, probability Evidence, rights boundary는 모두 호출자가 제공한다. asset/location/physical-scope/clock/horizon과 source/model/result digests를 보존하며 deterministic current나 reaction extent에서 확률을 유도하지 않는다([연결 가이드](CREVICE_FARADAIC_FTA_BINDING_KO.md)).

신규 연결 API: `integration.crevice_activity_transport_spatial_phase_aperture_handoff`는 digest가 고정된 activity-corrected 반응수송 결과와 셀별 유한 고체상 속도 campaign을 순차 결합해 고체 재고와 다음 구간 slit aperture를 전달한다. 운전 중 재수송·상평형·형태 예측은 포함하지 않는다([설명](models/CREVICE_ACTIVITY_TRANSPORT_PHASE_APERTURE_KO.md)). `integration.wet_co2_cylindrical_bv_wall_recession`은 계산된 cylindrical mixed-potential 반응 extent를 caller 합금 조성·밀도에 연결해 원소 용출량과 정확한 annular bore recession을 재구성한다. 생성된 형상에서 전기화학을 반복 계산하지 않는다([설명](models/WET_CO2_CYLINDRICAL_BV_WALL_RECESSION_KO.md)). `data.mendeley_mdea_co2_eis_typed_rows`는 로컬 승인 뒤 Mendeley Data v3의 experimental/simulated EIS 텍스트 행을 digest·열 순서·원 토큰과 함께 읽으며 회로 피팅이나 부식률 계산을 수행하지 않는다([데이터와 사용 범위](datasets/MENDELEY_MDEA_CO2_EIS_TYPED_ROWS_KO.md)).

Mendeley MDEA EIS의 명시적으로 매핑된 frequency/real/imaginary 열을 복소 impedance로 변환하려면 `electrochemistry.mendeley_mdea_eis_complex_channel_conversion`을 사용한다. 원자료 행 순서와 행·파일 digest를 유지하며, 상상축 부호는 caller가 결정하고 필요하면 제공자 magnitude 열과의 일치도도 제한값으로 검사한다. experimental/simulated 파일 혼합, 회로 적합 및 부식률 추론은 하지 않는다.

원통형 wet-CO₂ geometry-dependent 계산은 matintegrity package의 make_spatial_wet_co2_candidate_solver(spatial_request_template)로 spatial BV evaluator를 고정점 callback에 연결할 수 있다. Adapter는 반복 반경에서 cylindrical geometry를 재구성하고 각 trial을 다시 계산한다. 종·전하·수용액 원소 수지는 유지하고 wall release와 geometry의 최종 일치 gate만 고정점 종료까지 보류한다. 수렴에는 controller의 반경 및 원소재고 잔차 기준 통과가 필요하다. Template의 scale 재고·kinetics·경계 입력은 caller 제공값으로 고정되며 자동 실험 검증이나 qualification은 포함하지 않는다([trial 계약](models/WET_CO2_SPATIAL_GEOMETRY_TRIAL_KO.md), [controller 계약](models/WET_CO2_GEOMETRY_FIXED_POINT_KO.md)).

crevice 활동도 보정 반응수송을 caller의 phase-rate 구간 및 간극 변경과 구간별로 순차 결합하려면 `integration.crevice_activity_transport_sequential_aperture_campaign`을 사용한다. 각 segment 시작의 균일 간극에서 transport를 다시 계산한 뒤 재고를 다음 segment에 전달한다. 현재 solver는 scalar area만 지원하므로 cellwise 비균일 간극은 거부하며 구간 내부 nonlinear fixed-point를 주장하지 않는다([상세 범위](models/CREVICE_ACTIVITY_TRANSPORT_SEQUENTIAL_APERTURE_KO.md)).

Caller가 시간별 cell/face 단면적 이력을 제공할 수 있으면 `transport.crevice_variable_area_activity_corrected_reactive_nernst_planck_1d`가 variable-volume reactive transport를 계산한다. cell 몰수 수지에 face 면적 flux와 체적변화 희석항을 포함하고, 입력 면적/속도 이력의 체적 유량 연속성을 검사한다. 이는 입력된 형상 위 transport solver이며 형상을 계산하거나 반복해석하지 않는다([상세 모델](models/CREVICE_VARIABLE_AREA_ACTIVITY_TRANSPORT_KO.md)).

내부부식 DOOBN 관련 공개자료를 후속 모델 입력으로 조사할 때는 `data.mendeley_internal_corrosion_doobn_typed_rows`의 local-only workbook reader를 사용한다. 이 API는 전문가 elicitation 기반 workbook cell과 좌표만 보존하며 확률 테이블·network를 자동 추출하거나 해석하지 않는다. Dataset record가 third-party material 추가 허가 가능성을 경고하므로 원 workbook과 동봉 PDF는 배포에 넣지 않고 각 값의 재사용 권리와 의미를 별도로 확인한다([상세 가이드](datasets/MENDELEY_INTERNAL_CORROSION_DOOBN_TYPED_ROWS_KO.md)).

최근 composable API: `integration.findley_miner_ordered_block_history`는 digest-consistent Findley life 결과를 caller가 검토한 순서형 유한 cycle blocks에 연결하며, 선형 Miner rule을 명시적으로 승인해야 한다([설명](models/FINDLEY_MINER_BLOCK_HISTORY_KO.md)). `integration.crevice_transport_volume_weighted_composition`은 exact digest-bound crevice campaign의 셀별 inventory와 체적가중 요약을 제공하며 remap 전후 상태를 분리한다([설명](models/CREVICE_TRANSPORT_COMPOSITION_BRIDGE_KO.md)). `integration.wet_co2_simulation_wall_loss_envelope`는 CC BY 제공자 simulation 행을 Evidence·row digest와 묶어 caller baseline과 노출기간에 대한 균일 감육 유한 시나리오로 계산한다([설명](models/WET_CO2_SIMULATION_WALL_LOSS_ENVELOPE_KO.md)). `fatigue.ince_glinka_gsa_life_from_curve`는 유한 평면 GSA 계산을 caller 제공 재료상태 곡선의 지원 범위 안에서만 수명으로 매핑한다([설명](models/INCE_GLINKA_GSA_CURVE_LIFE_KO.md)). `integration.crevice_local_speciation_volume_ledger`는 transport 캠페인의 각 셀·절점에 별도 계산된 mass-action 결과를 digest로 결합하고 공간별 종 몰수·전하당량·가능한 원소 재고를 기록한다([설명](models/CREVICE_LOCAL_SPECIATION_LEDGER_KO.md)). `integration.gasket_leakage_rate_threshold_events`는 계산된 caller 보정 누설 이력의 선형 재구성에 대해 출처가 있는 하한·상한 초과 구간을 식별한다([설명](models/GASKET_LEAKAGE_RATE_THRESHOLD_EVENTS_KO.md)). `chemistry.layered_scale_history_series_transport`는 상별 caller scale-thickness history를 명시적 층에 연결하고 일치하는 exact knot마다 다층 정상 확산 한계를 평가한다([설명](models/LAYERED_SCALE_HISTORY_SERIES_TRANSPORT_KO.md)). 이 API들은 입력 범위 밖의 수명·현장 예측·확률·수용·자격을 추론하지 않는다.

`chemistry.scale_precipitation_inventory_budget`는 digest 확인된 caller 단일상 scale history의 gross 석출량을 exposed area와 caller 반응물별 초기·구간 공급 재고 및 명시적 stoichiometry에 대조한다. 미충족 첫 구간은 커밋하지 않고 완료 prefix와 종별 부족량을 보고한다. 용해를 반응물 재생으로 계산하지 않으며, 용액 평형·물질전달·부식률을 추론하지 않는다. [사용 계약](models/SCALE_PRECIPITATION_INVENTORY_BUDGET_KO.md).

`corrosion.scale_diffusion_metal_loss_bound`는 digest가 고정된 정상 스케일 확산 플럭스 ceiling을 caller 반응 화학양론·금속 몰질량·밀도에 연결해 uniform penetration-rate와 유한 기간 loss 상한을 계산한다. 실제 전류·부식률을 예측하지 않으며, steady bound 유지·완전 branch 집합·균일 침식 적용성을 caller가 검토해야 한다. [사용 계약](models/SCALE_DIFFUSION_METAL_LOSS_BOUND_KO.md).

`chemistry.aqueous_mass_action_scenario_envelope`는 같은 고정 종·반응·제약 topology와 공급자 revision에 대해 caller가 지정한 2–256개 mass-action 사례를 각각 계산하고, 제공된 finite cases의 비가중 활동도·농도 extrema만 반환한다. 하나라도 실패하면 전체 envelope를 억제하고 성공 prefix와 첫 실패를 보존한다. [사용 계약](models/AQUEOUS_MASS_ACTION_SCENARIO_ENVELOPE_KO.md).

`chemistry.aqueous_mass_action_topology_envelope`는 온도·용액 ID·종 재고/활동도·제약·활동도 provider state를 고정하고 caller가 명시한 2–64개 대안 반응 network를 각각 푼다. 종별 extrema는 이 유한 대안 집합만 설명하며 자동 반응망 생성이나 선택, 확률·부식률은 제공하지 않는다. [사용 계약](models/AQUEOUS_MASS_ACTION_TOPOLOGY_ENVELOPE_KO.md).

`integration.elastic_joint_load_ordered_history`는 caller의 유한 ordered load snapshots에 기존 탄성 2-spring 하중 계산을 적용하고 처음으로 caller clamp-force 기준 아래가 된 제공 시점만 반환한다. 구간 보간, gasket relaxation, leak/seal acceptance는 포함하지 않는다. [사용 계약](models/ELASTIC_JOINT_LOAD_ORDERED_HISTORY_KO.md).

`corrosion.piecewise_linear_rate_thickness_history`는 근거가 있는 시간별 부식률 절점 사이를 caller가 검토한 선형 경로로 재구성하고 trapezoid로 균일 면적평균 감육을 적분한다. required-thickness crossing은 이 재구성에 조건부인 시간 bracket으로 보고하며, 기준두께를 초과할 구간은 커밋하지 않는다. [입력·범위](models/CORROSION_RATE_PIECEWISE_HISTORY_KO.md).

Zenodo CP 행 API `data.zenodo_cathodic_protection_sample_rows`와 pressure-decay sample iterator는 caller attribution 및 local-use authorization을 요구한다. 각 행은 source/authorization digest와 `local_only` 경계를 유지한다. [CP typed rows](datasets/CATHODIC_PROTECTION_TYPED_ROWS_KO.md), [pressure-decay typed rows](datasets/PRESSURE_DECAY_TYPED_ROWS_KO.md).

`data.zenodo_galvanized_polarization_typed_rows`는 기존 parser를 재사용해 세 개의 catalogued polarization workbook을 typed row로 넘긴다. A/cm² provider current와 A/m² parser view, raw source row·asset digest, authorization을 유지하며 reference electrode를 추정하거나 Tafel/corrosion rate를 계산하지 않는다. [범위와 예시](datasets/GALVANIZED_POLARIZATION_TYPED_ROWS_KO.md).

Ti‑12Mo‑5Zr의 제공자 명시 OCP/EIS/AESEC 파일을 선택해 원행으로 읽으려면 `Ti12Mo5ZrWorkbookRequest`와 `iter_local_rows()`를 사용한다. 요청은 allowlisted member와 로컬 원본 경로 및 명시적 계산사용·로컬사용 승인을 요구하고, reader는 archive/member digest·헤더·크기를 확인한다. 셀·시간·단위는 변환하지 않으며 intensity/ICP-AES 등 나머지 자산을 해석하지 않는다. [데이터·권리·제한](datasets/ti12mo5zr_corrosion.md).

완전한 caller-owned gasket joint 시나리오 집합과 동일 행의 가중치를 사용해 차압·접촉면적·누설 응답·선택 노드 간 유한집합 공분산/상관을 보려면 `fabrication.gasket_finite_scenario_dependence`를 쓴다. 입력 시나리오 밖으로 분포를 만들거나 원인관계·신뢰구간·연속 범위를 추정하지 않는다. [변수·단위와 범위](GASKET_FINITE_SCENARIO_DEPENDENCE_KO.md)를 따른다.

기존 digest-pinned planar-slit transient hydraulic `AssessmentResult`에서 cell별 벽면전단응력 기술량이 필요하면 `corrosion.crevice_wall_shear_exposure`를 사용한다. wide-slit 완전발달 속도분포와 준정상 wall-shear review를 요구하고, signed 값과 reversal을 분할한 absolute impulse를 분리해 반환한다. 이는 수력 결과 기반 기술량이며 erosion/corrosion률·손상·수명·합격판정이 아니다. [범위와 수식](CREVICE_WALL_SHEAR_EXPOSURE_KO.md)을 따른다.

사용자가 후보 고체식과 닫힌 수용액 종 목록을 제공한 경우 `AqueousSolidPhaseCandidateEnumeration`과 `enumerate_aqueous_solid_phase_candidates()`로 원소·전하 보존 용해식만 유한 검색할 수 있다. 입력식/재고 검토와 사용·수동선택 근거가 필요하며, 이 기능은 상식을 생성·선택하거나 열역학 안정성·평형상수·부식률을 추정하지 않는다. [계약과 한계](AQUEOUS_SOLID_PHASE_CANDIDATES_KO.md)를 따른다.

Ti‑12Mo‑5Hf CC0 archive의 두 AESEC 워크북에서 원시 행을 로컬로 읽을 때는 `Ti12Mo5HfAESECRequest`와 `iter_local_aesec_rows()`를 사용한다. 호출 전 계산사용·로컬사용 동의를 명시해야 하며, reader는 archive/member digest와 정확한 헤더를 확인한 뒤 원행·단위·순서를 보존한다. 값의 단위변환, 구간 해석, alloy/time 매핑, 부식률 계산은 하지 않는다. ICP‑MS workbook은 의미가 명확해질 때까지 이 reader 대상에 포함하지 않는다. [데이터 출처와 사용 경계](datasets/ti12mo5hf_aesec_rows.md), [Zenodo 원자료](https://zenodo.org/records/19462164)를 참고한다.

여러 complete electrochemical wall-thickness `AssessmentResult`를 같은 기준선·시간 절점에서 비교할 때 `integration.electrochemical_wall_thickness_scenario_envelope`를 사용한다. 유한 시나리오 manifest의 digest와 권리·완전성·공동 의존성 review를 입력하며, 절점별 두께/margin extrema와 witness scenario만 반환한다. 확률이나 시나리오 간 보간은 수행하지 않는다. [사용 예와 범위](ELECTROCHEMICAL_WALL_THICKNESS_SCENARIO_ENVELOPE_KO.md)를 참고한다.

전기화학 반응별 gross anodic 금속손실을 측정 벽두께 기준선에 연결하려면 `integration.electrochemical_metal_loss_wall_thickness_history`를 사용한다. 공통 평가 면적·유효 밀도와 적용 review, 전체 반응 커버리지, 첫 구간 시작시각의 Evidence-linked baseline이 필요하다. 결과는 공급 기간의 thickness margin과 교차 구간 bracket만 제공한다. [입력 계약과 범위](ELECTROCHEMICAL_WALL_THICKNESS_KO.md)를 따른다.

사용자 소유의 조성 의존 활동도 라이브러리는 `ExternalAqueousActivityIteration`과 `aqueous_external_activity_self_consistent_speciation(request, activity_provider=callback)`에 연결할 수 있다. Provider 결과의 종 순서·composition digest·모든 parameter lineage를 고정하고 molality gamma를 기존 mass-action molarity 표준상태로 변환한다. [외부 활동도 provider 계약](AQUEOUS_EXTERNAL_ACTIVITY_PROVIDER_KO.md)을 참조한다.

`solve_crevice_transport_recession_feedback()`는 기본 순차 operator-split 모드 외에 선택적 구간 내부 aperture fixed-point 모드를 제공한다. 이 옵션은 reviewed linear aperture path, moving-volume transport, selected metal-wall ledger와 bounded endpoint iteration을 연결한다. 추가 review가 선언되면 `PlanarSlitEndpointVelocityPath` contract를 통해 endpoint steady-flow face velocities 사이의 local-time 선형 경로를 transport callback에 연결한다. 입력 review와 제한은 [수송 기반 틈부식 간극 되먹임](CREVICE_TRANSPORT_RECESSION_FEEDBACK_KO.md)을 따른다.

자기일관 Davies/SIT 질량작용 반복은 molality 계수 `gamma_m`을 1 mol/L 표준상태 계수 `gamma_c = gamma_m / w`로 변환한다. 여기서 `w`는 caller 공급 kg-water/L-solution이다. 결과는 molality·molarity 기준 gamma를 구분해 보고한다. 검토 gate와 적용범위는 [Davies](AQUEOUS_DAVIES_SELF_CONSISTENT_KO.md) 및 [SIT](AQUEOUS_SIT_SELF_CONSISTENT_KO.md) 문서를 따른다.

경쟁 중성 고체 평형을 SIT 상호작용까지 자기일관 결합하려면 `chemistry.competitive_solid_sit_equilibrium`을 사용한다. 기존 고체 평형 입력, 온도별 A와 Evidence-linked directional epsilon 계수, 물 질량 변환, ionic-strength ceiling 및 완전한 parameter/phase-set review가 필요하다. 현재는 1 mol/L 활동도 기준(`activity_reference_concentration_mol_m3=1000`)만 허용한다. 전체 종·상 자동탐색이나 kinetic/morphology/transport 결합은 하지 않는다. [입력 규약과 한계](COMPETITIVE_SOLID_SIT_EQUILIBRIUM_KO.md)를 참고한다.

species별 extended Debye–Hückel B-dot 계수와 이온 크기를 사용하려면 `chemistry.competitive_solid_bdot_equilibrium`을 사용한다. 상 평형 후 이온강도에서 B-dot gamma를 재계산하며 온도, 모든 종별 parameter record/Evidence, 물 질량, 전하·이온강도 및 1 mol/L 표준상태 검토가 필요하다. [B-dot 입력·수렴·적용 한계](COMPETITIVE_SOLID_BDOT_EQUILIBRIUM_KO.md)를 참고한다.

침식·부식 시험에서 순수 침식, 순수 부식, 결합 손실을 같은 범위·단위로 맞춰 비교하려면 `degradation.erosion_corrosion_synergy_decomposition`를 사용한다. 입력 rate와 provider evidence를 digest로 고정하고 signed interaction residual을 보존한다. [성분 장부 규약](EROSION_CORROSION_SYNERGY_KO.md)을 참고한다.

동일 모델은 선택적으로 digest-bound 초기 벽두께와 required minimum을 결합해 interval별 결정론적 thickness margin 및 rate-bounds 기반 margin range를 낸다. 최초 교차는 point·가능·확정 기준별 interval bracket으로 반환하며 구간 내부 시각은 보간하지 않는다. FTA 연결에는 사용할 수 있는 limit-state basis를 제공하지만 사건 확률을 생성하지 않는다.

`fatigue.critical_plane_findley_parameter`는 caller 제공 응력 cycle·면 후보·Findley 계수 및 기준 강도 한 점을 사용한다. 유한 면 표본의 이산 응력 지표일 뿐 수명 모델이나 합격기준이 아니다. [Findley 임계면 안내](FINDLEY_CRITICAL_PLANE_KO.md)를 참고한다.

전기화학 수송에서 homogeneous mass-action source는 기본적으로 caller rate constant에 맞는 농도를 사용한다. `ElectrochemicalTransport.homogeneous_reaction_activity_correction_reviewed=True`와 정확히 같은 provider ID/configuration digest를 가진 `activity_coefficients` callback을 함께 주면 반응속도 평가에서만 종별 농도를 `gamma × concentration`으로 바꾼다. rate constant와 선언 단위는 그대로 유지하고 activity callback도 수송 화학퍼텐셜 계산에 사용한다. 이 선택은 유효농도 경험 보정이지 표준상태 변환이나 자동 kinetics 추정이 아니다. 적용 가정과 callback wiring은 [activity 보정 반응속도 안내](ACTIVITY_CORRECTED_KINETICS_KO.md)를 따른다.

선형 Prony gasket 접촉 이력은 동일한 compliance history 결과와 SHA-256을 FlangeViscoelasticContactHistoryRequest에 넣어 절점별 연산자를 적용할 수 있다. Geometry time과 node order가 정확히 맞아야 하며 절점 사이 유연도와 접촉전이 시각은 추정하지 않는다.

공간 비선형 generalized-Maxwell gasket 접촉은 `fabrication.flange_nonlinear_viscoelastic_contact_history`를 사용한다. `maximum_contact_transition_step_s`와 `contact_transition_time_tolerance_s`를 함께 설정하면 관찰된 접촉 상태변화 bracket을 검토된 단일전이 가정 아래 이분 탐색으로 좁힌다. 합성 사용 계약과 budget/한계는 [비선형 점탄성 접촉 안내](FLANGE_NONLINEAR_VISCOELASTIC_CONTACT_KO.md)를 따른다.

`fabrication.flange_contact_compliance_reduction`은 caller가 보유한 선형 증분 구조 강성행렬에서 고정 지지를 반영해 선택 접촉 DOF의 유연도 연산자를 축약한다. 수치·단위 계약과 제한은 [전용 안내](FLANGE_COMPLIANCE_REDUCTION_KO.md)를 참고한다.

시간별 solver tangent 강성을 같은 contact DOF map으로 축약할 때는 `fabrication.flange_contact_compliance_reduction_history`를 사용한다. 이력의 각 time knot는 별도의 선형 축약이며 시간 사이 값을 보간하지 않는다.

시간별 외부 FE 강성행렬에 provider receipt까지 보존하려면 `integration.external_flange_compliance_history`를 사용한다. caller가 receipt마다 시각을 명시하고 그 시각 대응을 검토해야 하며, 각 응답에 개별 receipt·결과 필드·mesh·정규화 행렬 digest가 연결된다. 이 API는 공급자가 내보낸 구조 응답을 계산하거나 시간 사이를 보간하지 않는다.

반응 기준 `log10(K)`와 caller 제공 반응 엔탈피에서 온도별 수용액 평형 상태를 다시 풀려면 `integration.aqueous_mass_action_vant_hoff_history`를 사용한다. 상수 엔탈피, constant-ΔCp 또는 기준점 주변 선형 ΔCp 열화학 모델과 온도 지지 범위 review가 필요하며, 각 열용량 모델은 별도 review gate를 쓴다. caller가 온도별 Evidence-bound 활동도계수를 넣거나 reference 활동도계수 고정 가정을 승인할 수 있다. 자세한 입력과 해석 한계는 [온도별 질량작용 안내](AQUEOUS_VANT_HOFF_HISTORY_KO.md)를 참고한다.

계산된 van't Hoff history의 활동도를 각 시각에 caller-selected 고체의 temperature-supported `Ksp`와 비교하려면 `integration.aqueous_vant_hoff_saturation_history`를 사용한다. 시간별 Ksp record, Evidence, 파일/입력 digest를 연결하며 시각·온도 사이 보간을 하지 않는다. 포화도는 상 선택·침전량·부식률을 뜻하지 않는다. [온도별 포화도 연계 안내](AQUEOUS_VANT_HOFF_SATURATION_KO.md)를 참고한다.

`corrosion.planar_slit_hydraulic_flow`는 caller가 선언한 셀별 틈새 개구부와 유체 물성, 압력차에서 정상 층류 슬릿 유량과 수송 면 속도를 제공한다. 허용 범위·모델 가정·수송 연결 방식은 [전용 API 설명](CREVICE_SLIT_HYDRAULIC_FLOW_KO.md)에 있다.

`corrosion.planar_slit_hydraulic_history`는 digest 고정 개구부 이력의 각 시간 절점에서 부호 있는 압력차로 정상 슬릿 유동을 다시 풀고, 해당 절점의 signed face velocity를 반환한다. 양수는 mouth-to-tip, 음수는 역방향, 0은 정체를 뜻한다. 이는 이후 fixed-geometry transport 호출들을 잇는 operator-split interface이며 시간간 유동이나 완전 연성 계산은 아니다. [입력과 유동방향 규약](CREVICE_SLIT_HYDRAULIC_FLOW_KO.md).

계산 결과를 직접 request에 복사하는 대신 `matintegrity.bind_planar_slit_hydraulic_snapshot()`으로 computed hydraulic-history AssessmentResult와 전체 SHA-256을 확인해 선택 snapshot을 `RestrictedTransportRequest`에 묶을 수 있다. 이 함수는 속도·provider/configuration digest·upstream result digest를 설정하고 계산 자체는 실행하지 않는다.

전체 연속 이력에는 `matintegrity.bind_planar_slit_hydraulic_history_series()`를 사용한다. 인접 hydraulic knot마다 transport segment 하나를 요구하고 각 segment local clock이 해당 knot 간격과 맞는지 검사한다.

`chemistry.competitive_solid_kinetic_ledger`는 사용자가 공급한 다상 고체 반응 extent-rate 이력을 구간별로 적용한다. `CompetingSolidKineticLedger`를 `ModelRegistry.run()`에 넣거나 `evaluate_competing_solid_kinetic_ledger()`를 직접 호출할 수 있다. 용해는 현재 고체 재고량으로 제한하고, 동시 침전은 모든 반응의 양론비를 유지하는 공통 수용액 제한계수를 적용한다. 종·상 조성과 charge/element balance를 확인하고 구간별 재고량·잔차를 기록한다. 속도 법칙, 포화도, 상 선택, 핵생성 또는 scale 보호효과를 추정하지 않는다. 입력과 범위는 [전용 안내](COMPETING_SOLID_KINETIC_LEDGER_KO.md)를 참고한다.

`chemistry.competitive_solid_saturation_kinetics`는 각 경쟁 고체상에 대해 caller가 제공한 구간별 포화비와 상별 침전·용해 계수/차수를 signed extent-rate로 변환한 후 보존 ledger를 적용한다. 구간별 온도를 입력할 수 있으며, 기준온도·유효온도 범위 및 침전·용해 활성화에너지와 적용성 review를 제공하면 해당 구간 온도로 Arrhenius 보정을 한다. `CompetingSolidSaturationKinetics`는 registry 또는 직접 `evaluate_competing_solid_saturation_kinetics()`에서 사용할 수 있다. 포화비는 계산하지 않고 입력된 상수로 취급하며 phase discovery, speciation, equilibrium, nucleation은 수행하지 않는다. [모델 설명](COMPETING_SOLID_SATURATION_KINETICS_KO.md)과 공개 schema를 참고한다.

기존 `AqueousSaturationScreen` Ksp/evidence template와 cellwise activity provider를 transport endpoint 포화 callback으로 묶을 때는 `build_transport_saturation_callback_from_activity_provider()`를 사용한다. activity sample에서 dimensionless phase saturation ratio를 다시 계산해 수송 kinetics callback API와 연결한다. provider의 `activity_standard_state`가 template과 정확히 일치해야 하며 고정 온도는 template에서 전달한다. Saturation-mode `CompetingSolidKineticTransport`에도 동일한 `saturation_activity_standard_state` 및 `temperature_K`를 선언하고 solver가 callback과 정확히 대조한다. 합성 배선 예시는 `examples/transport_activity_saturation_callback.py`에 있다.

`integration.competitive_solid_kinetic_transport`는 `RestrictedTransportRequest`와 다상 고체 ledger를 구간별 operator split으로 실행한다. 기존 방식은 caller 제공 셀별 phase-rate를 사용하고, 추가 포화도 방식은 interval transport 완료 후의 농도/고체 상태를 caller saturation callback에 전달해 phase-specific power-law rate를 계산하고 해당 구간 ledger에 적용한다. reaction·경계·activity·유동 및 필요한 saturation callback은 `solve_competing_solid_kinetic_transport()`에 전달한다. [연동 계약과 한계](COMPETING_SOLID_KINETIC_TRANSPORT_KO.md)를 참고한다.

`reliability.fault_tree_minimal_cut_sets`는 caller가 정의한 최소 컷셋의 AND/OR 구조를 입력받아, 독립 기본사건 확률 가정 아래 포함-배제로 top-event 확률과 기본사건별 Birnbaum 중요도를 계산한다. 사건 확률·조건·근거 digest는 입력자가 제공하며, 독립성·공통원인 검토·컷셋 겹침 검토와 사건 범위 확인 플래그가 없으면 계산하지 않는다. 범위와 한계는 [FTA API 안내](FAULT_TREE_KO.md)에 있다.

새 공간 Crevice/Nernst–Planck/Faradaic 결과를 외부 FTA 저장소로 연결할 때의 구현 요구는 [부식 전기화학–FTA 확장 요청서](extension_requests/CORROSION_CURRENT_CARRYING_FTA_EXTENSION_KO.md)에 정리했다. 이 결과는 상태·물질량 계산이며 확률은 FTA 쪽의 별도 caller 모델이 공급해야 한다.

FTA 결과를 검사행위 기대손실 비교의 행동별 사건확률 입력으로 만들려면 `action_event_probability_from_fault_tree_result` adapter를 사용한다. top event가 `conditional_first_failure_in_period` 의미여야 하며, caller가 준 `IntegrityEventBasis`가 입력·결과 digest와 기간을 일치시켜야 한다. 각 intervention에는 action 효과를 반영한 독립 FTA 계산 결과가 필요하다.

action별 FTA 결과에서 기대손실 입력까지 한 번에 만들 때는 strict `FaultTreeActionEventInput` 레코드 배열과 `inspection_action_expected_loss_inputs_from_fault_trees`를 사용한다. 행위 전체 coverage·baseline·사건 scope 정렬은 기존 composer에서 확인하며, 결과는 검토 플래그와 비용·consequence 입력을 포함한 `inspection.action_expected_loss` 계약이다. 이를 실제 실행하고 action별 원 FTA digest 및 비교결과를 하나의 재현 레코드로 남기려면 `evaluate_fault_tree_inspection_risk_campaign`을 사용한다.

`fatigue.propose_critical_plane_interval_overlap_pairing`는 하나의 투영 rainflow 결과에 포함된 정상응력·전단변형률 cycle의 표본 인덱스 구간 겹침을 이용해 damage API에 넘길 수 있는 페어링 제안을 만든다. 이는 자동 제안 알고리즘이지 물리 검증된 cycle 법칙이 아니며, 적용 전 배분과 미할당 cycle을 caller가 검토해야 한다. [알고리즘·범위 한계](CRITICAL_PLANE_INTERVAL_PAIRING_KO.md)를 참고한다.

`fatigue.closed_tensor_work_life`는 사용자가 분리한 폐합 3D 응력–변형률 텐서 경로의 trapezoidal 일 적분을 같은 재료상태의 caller 보정 work-life 곡선 안에서 로그–로그 보간하고, 명시된 cycle count의 선형 Miner 합을 계산한다. Tensor/engineering 전단 convention과 endpoint closure를 보존하며 cycle extraction, 외삽, 보편적 비비례 손상 법칙은 제공하지 않는다. [계산식·가정·한계](MULTIAXIAL_WORK_LIFE_KO.md)를 참고한다.

`fabrication.gasket_prony_joint_history`는 caller 보정 Prony branch 상태를 시간 knot별 선형 탄성 bolt force balance와 결합한다. 구간 내 선형 strain 가정으로 branch state를 갱신하고, 각 knot의 폐합형 force balance에서 압축변형률과 힘·잔차를 반환한다. 접촉분리나 인장 gasket 상태가 필요하면 범위 밖으로 중단한다. [가정·지원범위](GASKET_PRONY_JOINT_HISTORY_KO.md)를 참고한다.

`structural.profile_capacity_corrosion_scenario`는 검토된 두께 프로파일에 호출자 지정 균일 부식률·기간을 적용하고 같은 capacity provider로 압력차 용량을 재평가한다. [입력·가정·한계](PROFILE_CORROSION_CAPACITY_SCENARIO_KO.md)를 참고한다.

`structural.profile_capacity_rate_field_scenario`는 축방향 각 측정 노드와 시간 knot에 사용자가 제공한 부식률 격자를 piecewise-linear 보간·적분해 두께 프로파일에 반영한다. 모델은 공간이나 시간 외삽을 하지 않고, 동일 capacity provider로 forecast 용량을 재평가한다.

`fatigue.neuber_notch_strain_amplitude`는 reviewed scalar notch inputs로 국부 안정화 변형률 진폭을 계산한다. `fatigue.neuber_strain_life_chain`은 수렴한 결과만 기존 strain-life 계산으로 전달하며 양 단계의 상태와 결과를 결합한다. [입력·가정·검증 계약](NEUBER_NOTCH_STRAIN_AMPLITUDE_KO.md)을 참고한다.

`geometry.rectilinear_thickness_map`은 명시적인 직교 셀 경계의 실제 면적으로 두께 가중평균·결측영역·부피손실을 요약하고 4방향 또는 8방향 임계 연결영역을 사용자가 선택한다. 보간이나 구조 판정은 수행하지 않는다. `degradation.galvanic_resistive_coupling`은 같은 전해질·온도·기준전극에서 두 검토된 비선형 분극 곡선과 유한 직렬저항의 전류·전압 평형을 곡선 지원범위 안에서 구한다. 다중/연속 평형과 부분용출 관측을 순 전극전류와 구분한다. 두 입력은 [모델 API 참조](MODEL_REFERENCE_KO.md)와 `examples/model_inputs.json`에서 확인한다. [상세 입력·해석 경계](RECTILINEAR_THICKNESS_MAP_KO.md).

`chemistry.carbonate_alkalinity_speciation`은 검토된 수용액 pH·총알칼리도와 호출자 제공 활동도 평형상수로 탄산계 종농도를 계산한다. 계약은 `activity_standard_state=molarity_1_mol_L`로 고정되고 해당 기준 검토가 필요하며, 몰랄 기준 Davies gamma를 변환 없이 직접 전달하지 않는다. 온도·상수 lineage와 알칼리도 closure를 확인하며, 비탄산 알칼리도 종·기상 평형·부식률은 계산하지 않는다. [수식과 한계](CARBONATE_ALKALINITY_KO.md)를 참고한다.

일반 반응망을 직접 공급하려면 `chemistry.aqueous_mass_action_speciation`에 caller가 정의한 aqueous species, log10 평형상수, 고정 활동도계수, 선형 분석량/전하 제약과 양의 초기 활동도를 전달한다. 정규화 damped-Newton closure, equation rank/Jacobian condition과 구체적인 종료 진단을 반환하며 equation count·phase scope·온도 및 provider lineage review가 필요하다. 수렴 상태의 동일 Jacobian으로 `log10(K)`, constraint target 및 `ln(gamma)`에 대한 종별 국소 민감도를 제공한다. parameter 순서가 명시된 공분산행렬과 별도 검토를 입력하면 선형화 1차 농도·활동도 공분산도 반환한다. 기체/고체상, gamma iteration과 침전은 포함하지 않는다. [네트워크 계약과 solver 한계](AQUEOUS_MASS_ACTION_KO.md)를 참고한다.

`chemistry.aqueous_thermodynamic_cycle_audit`는 Evidence/hash-bound caller 반응식과 `log10(K)`에서 원소·전하 균형 및 SVD reaction-cycle closure를 검사한다. 모든 source가 같은 온도와 activity standard state인지 caller가 선언한다. 이 계산은 반응/상 발견이나 speciation solve가 아니며, rank·closure tolerance와 네트워크 완전성은 caller 검토 대상이다. [Cycle audit 계약](AQUEOUS_THERMODYNAMIC_CYCLE_AUDIT_KO.md)을 참고한다.

기존 `AqueousMassActionSystem`을 재사용하려면 `integration.aqueous_mass_action_cycle_audit`에 같은 system과 반응별 Evidence binding을 넣는다. Adapter는 reaction set을 정확히 한번씩 연결하고 동일 source Evidence file hash를 대조한 뒤 cycle audit로 넘긴다. 원소식 누락, Evidence hash 불일치 또는 open-dataset license 누락은 자동 보완하지 않고 `needs_data`를 반환한다.

반응식 구성을 보조하려면 `chemistry.aqueous_reaction_candidate_enumeration`에 검토된 종별 원소식·전하, 닫힌 후보 목록과 명시적 차수/조합 예산을 전달한다. 원자수·전하 보존 정수 후보와 입력 digest를 반환한다. 화학적 반응성·상·방향·평형상수·속도상수는 산출하지 않으므로 결과는 수동 검토 후 별도 반응망에 넣는다.

선택한 균형 후보를 사용자 제공 평형자료와 mass-action 입력에 연결할 때는 `bind_aqueous_candidate_reactions()`를 사용한다. 후보 계산 결과와 `candidate_id`/SHA를 대조하고, 사용자가 명시한 방향과 `log10(K)`를 signed reaction term으로 변환한다. 평형 parameter Evidence의 source ID와 SHA-256이 맞아야 하며, 목표 온도는 반응 상수 온도와 선언 허용차 내에서 일치해야 한다. 반환 `reactions`는 `AqueousEquilibriumReaction` 계약에 맞고, 계보는 별도 배열로 반환한다. 반응 선택·상수 검토가 없으면 계산 반응을 내보내지 않는다. [바인딩 계약 상세](AQUEOUS_CANDIDATE_REACTION_BINDING_KO.md)를 참고한다.

바인딩 결과를 solver 입력으로 옮길 때는 `assemble_aqueous_mass_action_system()`을 사용한다. 이 API는 caller의 species, activity provider lineage, 선형 분석량/전하 제약과 solver 설정을 후보 binding 결과와 합쳐 `AqueousMassActionSystem` strict contract를 검증한 뒤 반환한다. 온도·표준상태 불일치, reaction/lineage 배열 오류, 원소·전하 보존 불일치 또는 비정방 equation count면 solver 입력을 만들지 않는다. 합성 배선은 `examples/aqueous_candidate_mass_action_pipeline.py`를 참고한다.

단일 pure-salt 고이온강도 평균 활동도 계산에는 `chemistry.pitzer_single_salt_activity`를 사용한다. caller 공급 Pitzer 계수와 parameter record 증거, 계수 온도 일치 및 최대 ionic-strength support를 요구하고 `γ±`, osmotic coefficient, water activity를 반환한다. 혼합염과 single-ion activity convention은 지원하지 않는다. [수식 범위와 라이선스 선택](PITZER_SINGLE_SALT_KO.md).

Zenodo Ti-6Al-4V `Fig1.csv` 자료는 `matintegrity.galvanic_data.import_ti6al4v_cathodic_polarization_csv`로 가져온다. 예상 파일 SHA-256, 매질, 검토된 조건/단위와 Evidence를 전달하면 increasing-potential `PolarizationCurve` 및 별도 Ti 용출 부분전류 배열을 반환한다. 부호·실제 면적·시험 전이 검증은 caller 책임이다. [가져오기 계약과 한계](TI6AL4V_POLARIZATION_IMPORT_KO.md).

`chemistry.aqueous_tabulated_activity_speciation`는 종별 caller activity table로 이온강도 self-consistency를 계산한다. 고정 온도 표 또는 종마다 온도별 ionic-strength slice를 전달할 수 있고, 전체 표 점 수에는 선언 budget을 적용한다. 측정·공개 dataset의 각 knot에는 source record ID를, table Evidence에는 citation과 license/reuse policy를 요구한다. 계산 결과 및 saturation composition은 Evidence와 row-ID digest를 유지한다. 온도 slice 입력은 표 온도·이온강도 양쪽에서 `ln(gamma)`를 선형 보간하고 두 축 밖 외삽을 거부한다. 이는 사용자가 제공한 표면의 bounded interpolation이며 용매/염 조성 전이와 데이터 자격화는 caller 검토 대상이다. 표 구조는 합성 `examples/temperature_dependent_activity_table.py`에도 있다. [입력과 적용범위](AQUEOUS_TABULATED_ACTIVITY_KO.md)를 따른다.

`chemistry.sit_activity_coefficients`는 caller가 온도별 Debye–Hückel A와 방향성 이온쌍별 SIT epsilon 표를 전달해 몰랄 활동도 계수를 계산한다. 미제공 pair를 0으로 해석하므로 interaction completeness/applicability review를 요구하고, 각 epsilon의 source record ID와 Evidence 원자료 SHA-256이 일치해야 한다. 파라미터를 자동 채우거나 종분화를 수행하지 않는다. 수식·경계와 합성 예제는 [SIT API 안내](SIT_ACTIVITY_KO.md)와 `examples/sit_activity_coefficients.py`에 있다.

`chemistry.aqueous_bdot_self_consistent_speciation`는 기존 caller 정의 질량작용계와 종별 extended Debye–Hückel B-dot 활동도계수를 반복 연성한다. 온도별 A/B, 물 질량 환산, 종별 이온 크기·B-dot 계수, parameter provenance/hash, 적용 이온강도 범위와 단일 액상 검토를 입력해야 한다. 중성종 B-dot 항도 명시 입력일 때만 사용한다. 같은 계약으로 `build_bdot_transport_activity_callback()`을 만들면 restricted transport의 위치별 농도에서 몰랄 gamma를 계산한다. `build_bdot_transport_saturation_callback()`은 그 활동도를 caller 제공 Ksp screen에 연결해 competing-solid transport callback을 구성한다. 종분화·고체 선택·석출 속도는 이 helper가 추론하지 않는다. [모델 방정식과 경계](AQUEOUS_BDOT_ACTIVITY_KO.md), 합성 JSON 입력은 `examples/model_inputs.json`을 참고한다.

`integration.aqueous_bdot_speciation_history`는 ordered time knots마다 완전한 B-dot/mass-action 요청을 독립 계산한다. 매 절점의 온도별 A/B와 species parameter record는 개별 digest로 고정되며, species·reaction·constraint topology는 이력 내에서 유지한다. knot 사이를 보간하지 않고 첫 실패에서 앞선 계산 prefix와 실패 절점을 보존한다.

TRI의 고정전류 전해질 안정성 자료에는 `read_otto_electrolyte_archive()`를 사용할 수 있다. JSON 배열을 source ID와 digest에 묶어 보존하는 reader이며 부식 polarization API로 변환하지 않는다. 세부 권리·unit 누락·프로토콜 경계는 [Otto dataset reader 설명](OTTO_AQUEOUS_ELECTROLYTES_KO.md)을 따른다.

같은 표를 확산/이동 transport에 재사용하려면 `build_tabulated_activity_transport_callback()`에 계약 입력, transport 종 순서, 온도를 전달한다. 반환 callback은 request에 고정된 provider/configuration digest를 노출하므로 `RestrictedTransportRequest`의 activity lineage와 직접 맞출 수 있다. 단, 이 조합은 표 기반 gamma를 계산해 Nernst–Planck chemical-potential term에 넣는 adapter이며, 활동도 모델·확산계수 보정·전체 반응-전하 연성의 자격화를 대신하지 않는다.

tabulated activity result를 `screen_mass_action_calculation()`에 전달하면 saturation screen의 upstream lineage에 표 온도, 종별 ionic-strength/temperature support 요약, 보간 정책 및 activity table provider/record digests가 유지된다. Adapter는 finite positive 온도·activities, 고유 species ID, provider ID/revision와 SHA-256, 종 key coverage, 실제 upstream ionic strength와 온도가 선언된 각 표 support 안에 있는지 확인하며 불일치나 필수 lineage 누락 시 `needs_data`를 돌려보낸다. 이 upstream 요약은 결과의 `upstream_activity_table_lineage` 아래 제공한다.

`screen_mass_action_calculation()`은 등록된 `integration.aqueous_bdot_speciation_history`도 지원한다. 반드시 `speciation_knot_index`를 골라야 하며, 전체 AssessmentResult와 exact knot의 request/result, 시각·온도, parameter-record digest를 대조한 뒤 그 knot의 활동도만 포화 선별기로 전달한다. 결과에는 선택 절점과 upstream parameter 계보가 붙는다. 단일 등록 `chemistry.aqueous_bdot_self_consistent_speciation` AssessmentResult도 지원하며, 이력 사이 보간이나 고체상 자동 선택은 하지 않는다.

입력이 registry `AssessmentResult`면 먼저 registry input digest를 model ID/version/inputs/context에서 재계산해 확인하고, 유효할 때 upstream model ID/version/source IDs/qualification/registry input digest를 saturation result에 전달한다. 직접 evaluator가 반환한 `Calculation`은 표현 유형과 전체 upstream result digest를 기록하며 registry model metadata는 `null`로 남긴다. 두 표현의 digest는 서로 다른 result payload를 그대로 식별한다.

`integration.aqueous_saturation_to_surface_scale_kinetics`는 해시가 확인된 `integration.aqueous_vant_hoff_saturation_history`의 선택 고체 포화비를 `chemistry.caller_surface_scale_kinetics`의 인접 시간 구간에 연결하고, 선택적으로 `chemistry.caller_scale_coverage_kinetics`에도 같은 포화도 이력을 전달한다. 입력 hash뿐 아니라 포함된 van't Hoff equilibrium history digest, 원 mass-action knot 결과 digest, 시간·온도, 각 saturation screen의 upstream/result 연결 및 solubility-record digest까지 대조한다. kinetic interval은 모든 aqueous history knot와 정확히 일치해야 한다. 온도가 변하면 kinetics 요청의 기준 온도가 첫 절점 온도와 같아야 하며, `temperature_knot_mapping_reviewed=true`와 Arrhenius 계수/support를 요구한다. 각 구간은 왼쪽 절점 온도를 상수로 사용하고 온도 보간은 하지 않는다. log10 포화비는 유한 수 범위 안에서 변환한다. 반응상 선택·핵생성·속도상수는 추론하지 않고, 두 kinetics는 서로 독립되어 있고 포화도 이력만 공유한다. 두께가 coverage를 바꾸거나 coverage가 확산/부식을 되먹임하지 않는다. 단일상 경험식과 계수의 입력 및 검토는 계속 caller 책임이다.

`chemistry.aqueous_saturation_screen`은 종분화 계산에서 얻은 caller-reviewed dimensionless aqueous activities와 온도에 맞는 candidate solids의 log10 solubility products를 받아 고체별 `log10_saturation_ratio`와 saturation ratio를 산출한다. activity-state와 용해도 자료 digest를 각각 보존하고 후보를 포화지수 순으로 보여준다. 종 활동도와 후보 용해도곱에 선택적 절대 log10 bound를 주면 보수적인 하한·상한과 확정 미포화/확정 과포화/포화 경계 중첩 구분을 제공한다. 비영 경계를 쓸 때는 활동도 범위와 용해도곱 범위의 출처·해석·적용성 review flag를 각각 true로 줘야 판정한다. 둘 중 필요한 검토가 빠지면 `needs_data`를 반환한다. 모든 결과에는 실제 review flag와 해당 입력에서 요구된 review 목록이 `review_flags` 및 `review_requirements`로 보존된다. 이는 deterministic input interval이며 확률 또는 신뢰구간이 아니다. 각 후보는 원 자료의 `solubility_record_id`와 top-level Evidence의 `solubility_evidence_source_id`를 지정해야 하며 결과에 citation·license·checksum이 후보별로 따라간다. Python의 `screen_mass_action_calculation`은 evaluator 내부 `Calculation` 또는 `ModelRegistry.run()`이 반환하는 `AssessmentResult`를 받는다. 후자의 경우 고정-gamma 질량작용·등록된 Davies·B-dot·활동도표 모델 ID를 확인하고, 원 assessment digest와 activity provider/record lineage를 유지한다. `activity_log10_absolute_bounds`에 종 ID별 절대 log10 경계를 추가할 수 있으며, 입력 종 ID 집합과 경계 key가 정확히 일치해야 한다. 표현 가능한 범위를 넘어서는 산술은 값을 자르지 않고 `out_of_scope`로 끝내며, 불완전한 upstream 종 행은 `needs_data`로 반환한다. 이는 후보 선별값이며 고체상 안정성/선택, 다상 질량수지, 침전량, 핵생성·성장 속도나 부식률을 풀지 않는다. 과학적 근거와 사용 예제는 `examples/aqueous_saturation_screen.py`를 따른다.

`evaluate_caller_stateful_multiaxial_damage`는 `CallerStatefulMultiaxialDamageRequest`와 caller callback을 받아 tensor cycle을 선언된 순서·정수 반복수대로 진행한다. Callback은 각 시각에 `state_derivative_per_s`와 `damage_rate_per_s` 키를 가진 mapping을 반환하며, dimensionless state와 damage를 함께 적분한다. 기본은 고정 최대시간 classical RK4이며 `adaptive_step_doubling_rk4`는 full-step과 두 half-step의 차이로 4차 국소 오차를 추정하고 caller absolute/relative state·damage tolerance에 따라 step을 줄이거나 늘린다. 적응형 설정 및 callback 반복 결정성 review, 최소/최대 step, callback 평가·거절 예산을 요구한다. Callback 시간은 ordered sequence 전체의 누적 초이며 각 sample interval 안에서 증가한다. Cycle별 결과는 sequence 경계·반복 damage·최초/최종 state를 보존한다. 이 API는 보편 피로법칙을 제공하지 않으며 state evolution, rate law, tolerance의 물리적 적절성 및 material calibration은 caller 책임이다. 상세 범위는 `STATEFUL_MULTIAXIAL_DAMAGE_KO.md`, 합성 배선은 `examples/stateful_multiaxial_damage.py`를 참고한다.

`electrochemistry.restricted_transport_campaign`은 고정 격자 이온수송·균질 질량작용망에 팁 및 셀별 Butler–Volmer 벽 반응을 결합한다. 내장 벽 반응은 셀별 용액전위와 caller 면적/체적비를 사용하며, 하나의 금속전위를 벽 전체에 적용하는 등전위 검토가 필수다. 입력 digest·교정 support와 한계는 [전기화학 수송 API](ELECTROCHEMICAL_TRANSPORT_KO.md)를 참고한다.

`fabrication.nonlinear_gasket_prony_joint_history`는 caller의 nonlinear equilibrium/Maxwell stress–strain backbone, branch별 relaxation time·초기 내부응력, 볼트 힘–신장 곡선과 외력 이력을 결합한다. 선언 knot 사이의 선형 strain 경로를 각 branch backbone 절점에서 분할해 내부응력을 정확 갱신하고, 시간 knot마다 폐합 접촉 평형을 푼다. 지원구간 외삽과 접촉 분리는 하지 않는다. [구성식·가정·제한](NONLINEAR_GASKET_VISCOELASTIC_JOINT_KO.md)을 참고한다.

`chemistry.fixed_fugacity_carbonate_scenario_ensemble`은 각 완전한 고정 퓨가시티 평형 입력을 시나리오별로 계산하고 정규화된 호출자 가중치의 기술 통계를 반환한다. 입력·범위·분위수 규칙은 [전용 설명](CO2_FIXED_FUGACITY_EQUILIBRIUM_KO.md)을 참고한다.

`chemistry.fixed_fugacity_carbonate_history`는 시간 절점마다 caller가 제공한 fugacity/Henry/알칼리도/활동도 상수 계약을 기존 고정 퓨가시티 탄산 평형 solver에 전달한다. 정확한 절점만 계산하고 보간하지 않으며 첫 실패에서 계산 prefix와 실패 절점을 보존한다. 유한 기상 재고, kinetics, scale, 부식률은 계산하지 않는다. 입력 시계와 sample 정렬 review가 필요하다.

`chemistry.davies_activity_coefficients`는 완전한 수용액 이온 몰랄 목록에서 이온세기와 전하 잔차를 계산하고, 사용자 공급 온도별 Davies A로 전하종 활동도계수를 산출한다. 농축 염수 적용, 기체 용해, 부식률은 계산하지 않는다. [상세 경계](DAVIES_ACTIVITY_KO.md)를 참고한다.

`corrosion.coupled_wall_metal_loss`는 고정 셀 수송 결과의 signed wall species 원장을 총 금속 질량·부피 변화와 영역 평균 후퇴량으로 바꾼다. 선택적으로 `cellwise_recession_interpretation_reviewed=true`를 지정하면 고정 셀별 종 원장과 wall-area density를 대조해 셀 평균 후퇴량도 반환한다. 셀 내부의 국부 공격 분포나 움직이는 표면은 계산하지 않는다. [입력 lineage와 해석 경계](WALL_METAL_LOSS_EXCHANGE_KO.md)를 따른다.

`examples/model_inputs.json`에는 407개 등록 계산기 중 400개의 standalone JSON 입력 예제가 있다. 각 예제는 프로젝트 작성
synthetic 근거와 검토된 도메인 fixture에 기반하며 실제 설비 적합성이나 과학적 검증을 뜻하지 않는다.
모델 payload와 분리된 root `run_contexts`는 계약상 payload 필드가 아닌 asset/location/time basis를 담는다.
예제 실행 harness는 이를 `RunContext`로 전달한다. [예제 커버리지와 작성 원칙](MODEL_EXAMPLE_COVERAGE_KO.md)을
참고한다.

쿠폰 질량손실 데이터에 측정 불확도를 포함하려면 `corrosion.coupon_loss_with_uncertainty`를 사용한다. 전체 입력 공분산을 받아 1차 표준불확도를 전파하며, 변수 순서·근거·검토·해석 경계는 [전용 안내](CORROSION_COUPON_UNCERTAINTY_KO.md)에 정리했다.

계산 결과를 시편별 부식률 표본 요약과 결합할 때는 `coupon_loss_input_to_rate_observation` 어댑터로 `CorrosionRateObservation`을 만든다. 표본 요약과 결정론적 분위수 시나리오는 쿠폰 표준불확도·근거 ID를 행별로 보존하되 경험 분위수나 두께예측에 섞지 않는다. 확률 계산에 이를 전파할 때는 분포와 의존구조를 별도로 검토해야 한다.

완성된 부식률 표본 그룹의 CSV/JSONL 가져오기는 `matintegrity.tabular_contract_import`를 쓴다. 한 JSONL 행에 관측 배열과 N×N 계측오차 공분산을 넣는 [예시 profile과 helper](TABULAR_CONTRACT_IMPORT_KO.md)를 제공한다. 파일·profile·schema·가져온 record digest를 보존하며 단위는 추측하거나 자동 변환하지 않는다.

FCGR worksheet는 `FcgrWorkbookImportRequest.from_file(...)`와 `import_fcgr_workbook()`으로 읽는다. caller가 sheet별 시편/환경/R, 헤더·column index, source row window, 단위와 권리/적용성을 지정하고, importer는 해당 row 순서의 데이터만 검사해 SI curve를 만든다. frequency를 확인하지 못한 자료는 `frequency_Hz=None`으로 유지할 수 있으며 ΔK 대 da/dN/cycle 조회만 허용하고 frequency가 필요한 성장수명 계산은 거절한다. [Excel FCGR import 예제와 S460 데이터 조건](FCGR_WORKBOOK_IMPORT_KO.md).

타 저장소와의 API 581 damage/PoF, consequence scenario/result 및 deterministic compatibility receipt 계약은
[`CROSS_REPOSITORY_EXCHANGE_KO.md`](CROSS_REPOSITORY_EXCHANGE_KO.md)를 따른다.

NIST CORR-DATA의 로컬 archive/schema 집계 감사는 `data.nist_corr_data_archive_audit` 및
`audit_nist_corr_data_archive(path)`로 실행한다. 이 API는 포인트별 값이나 원문 텍스트를 반환하지 않으며
관측값의 단위·출처권리·독립성·적용성을 판정하지 않는다. [상세 경계](NIST_CORR_DATA_KO.md)를 따른다.

304L chloride-SCC 자료의 비공개 구조 감사는 `audit_mendeley_scc_archive(path)` 및
`scripts/inspect_mendeley_scc_data.py`로 수행한다. workbook 시트명과 셀 값은 출력하지 않고 시트 수,
크기, 비어있지 않은 셀·수식 셀 수와 archive/workbook digest만 기록한다. 계산 수식의 캐시 결과를
검증하거나 pointwise 데이터를 해석하는 API가 아니다. provider checksum 부재, 데이터셋 차원의
라이선스 선언과 시편 계층 미확정 경계를 유지한다.

사용자 작성 SCC facts/rules 선별은 `degradation.{chloride_scc,ammonia_scc,alkaline_scc}_user_screening`
세 API로 실행한다. 규칙·역치·unknown policy는 호출자 근거에 속하며 결과는 screening-only다.
[입력 계약, 예제와 해석 한계](SCC_USER_SCREENING_KO.md)를 따른다.

## AE localization·thermal-spray·thermal calibration API

`inspection.acoustic_emission_arrival_localization`은 고정 wave speed와 reviewed arrival picks로 source
position/origin time을 적합한다. `fabrication.thermal_spray_cross_section_summary`는 calibrated field의
thickness와 caller-segmented area porosity를 요약한다.
`structural.thermal_gradient_parameter_calibration`은 외부 provider baseline temperature와 sensitivity에서
thermal-property parameter 하나를 calibration/holdout 보정한다. 공개 자료는
`read_controlled_ae_waveform`과 `audit_controlled_wire_cut_ae`로 읽으며 arrival pick을 생성하지 않는다.
세부 계약은 [집중 문서](AE_THERMAL_SPRAY_GRADIENT_KO.md)에 있다.

## 성형·pull-off·replica feature API

`fabrication.forming_geometry_history`는 하나의 선언된 strain 관례로 surface strain과 thinning을
요약한다. `fabrication.pull_off_adhesion_calibration`은 완전한 SI force/area stress와 독립 provider
stress의 calibration/holdout 비교를 수행한다. `inspection.replica_feature_density_summary`는 calibrated
field의 feature count density, segmented area fraction과 nearest-neighbor spacing을 계산한다.
`read_coating_adhesion_workbook`은 공개 wood-substrate workbook의 raw replicate를 단위 미확정 상태로
읽는다. 계약·중단조건은 [집중 문서](FORMING_COATING_REPLICA_KO.md)에 있다.

## 단조 소성·음극방식·계장화 충격 API

`materials.monotonic_hollomon_calibration`은 분할된 pre-necking 단조점을 보정하고 calibration support
안의 holdout만 진단한다. `fabrication.cathodic_protection_field_survey`는 전위 convention과 reference
calibration, IR-drop·current·environment를 보존하며 caller threshold의 signed margin만 반환한다.
`inspection.instrumented_impact_signal_summary`는 SI force/displacement/time 신호의 valid window에서
absorbed energy와 plateau-aware peak를 계산하고 독립 machine energy를 선택적으로 비교한다. 공개 자료는
`audit_cathodic_protection_dataset`과 `read_dplot_curves`로 감사하며 모호한 current-axis를 변환하지 않는다.
계약·예제·중단 조건은 [집중 문서](PLASTICITY_CP_IMPACT_KO.md)에 있다.

## 재료 인증서·진공 pressure-rise·이종용접 API

`materials.multi_record_certificate_reconciliation`은 caller requirement와 복수 certificate/test 기록을
대조한다. `inspection.known_volume_pressure_rise`는 독립 blank/test 절대압력 이력에서 signed net
throughput을 계산한다. `welding.dissimilar_weld_applicability_evidence`는 material/layer/boundary/thermal/
environment review를 identity와 digest에 결속한다. 공개 pressure-decay reader는 누락된 blank와 상태기준
때문에 계산기로 자동 연결하지 않는다. [상세 계약](CERTIFICATE_VACUUM_DISSIMILAR_WELD_KO.md)을 따른다.

## 마모·경도·인장 원자료 API

`degradation.archard_wear_coefficient_calibration`, `inspection.hardness_reference_block_calibration`,
`inspection.tensile_offset_yield_curve`는 각각 reviewed regime, 장비 configuration, 원 curve identity를
보존한다. `audit_tribology_metadata_dataset`은 CC BY 4.0 RDF metadata의 완전성만 감사한다.
[상세 계약과 중단 조건](WEAR_HARDNESS_TENSILE_KO.md)을 따른다.

## 고분자·충식부식·기준누설 API

`materials.polymer_arrhenius_shift_calibration`, `degradation.erosion_corrosion_power_law_calibration`,
`inspection.reference_leak_response_calibration`은 모두 calibration/holdout을 물리·출처·독립성
그룹으로 분리하고 지원범위 밖 holdout을 외삽하지 않는다. `escape_leak_data` reader는
CC0 ESCAPE‑1 workbook의 time·ppm·m 배열과 provider slpm을 보존하지만, 참조상태가
없는 slpm을 `mol/s`로 변환하지 않는다. [상세 계약과 자료 경계](POLYMER_EROSION_LEAK_KO.md)를
따른다.

## 수명·민감도·실가스 심화 API

`materials.strain_life_coefficient_calibration`은 분리된 탄성·소성 변형률 amplitude의 calibration failure로 strain–life 계수를 적합하고 holdout failure로만 사후 진단한다. `creep.accelerated_lognormal_rupture_fit`은 rupture와 right-censor likelihood를 결합하고 calibration stress–temperature hull 밖 holdout을 거절한다. `reliability.sobol_replicate_stability`는 동일한 distribution·design·evaluator identity의 외부 Sobol replicate만 안정성 진단한다.

`thermo.gas_pressure_decay_inputs_from_coolprop(...)`는 세 절대압·온도 상태의 `Z`·phase와 CoolProp provenance/digest를 보존한 `inspection.gas_pressure_decay` 입력 dict를 만든다. 상세 필드·중단 조건·해석 한계는 [수명·민감도·실가스 계약](LIFE_SENSITIVITY_LEAK_KO.md)을 따른다.

## Chronoamperometry 창 요약

등록 모델 `corrosion.chronoamperometry_window_summary`는 물리 시편·source group·원 trace SHA-256과
엄격히 증가하는 `time_s`, 정렬된 `current_A`, 분석창과 선택적 baseline 창을 받는다. 창 경계는
`exact_samples` 또는 `piecewise_linear`로 명시한다. 후자는 경계 두 점만 선형 보간하고 내부 원시
시료를 정렬·평활·재표본화하지 않는다. signed charge, 0 교차를 포함한 absolute signal charge,
시간가중 평균, 최소·최대값과 plateau의 첫/마지막 시각을 반환한다.

`adapters.seccm_chronoamperometry_summary_inputs`는 `read_seccm_ca_trace` 결과를 이 모델 입력으로
변환하며 archive/member hash와 canonical 선택배열 hash를 함께 보존한다. 호출자가 보고된 전류 부호의
수치적 의미를 명시하고 검토해야 한다. 계산값은 기술적 신호 요약이며 provider descriptor 재현,
전기화학 반응 극성, 금속손실, pit 치수·분류·POD·수명·고장확률이 아니다. 자세한 계약은
[chronoamperometry 설명](CHRONOAMPEROMETRY_KO.md)에 있다.

## SECCM 원시 전류 자료

`seccm_data.audit_seccm_archive(path)`는 고정 SHA-256 ZIP의 정확한 열 개 구성 파일과 각 member
해시를 확인하고 raw CA 표 전체를 검사한다. `read_seccm_ca_trace(path, map_id,
physical_specimen_id=..., source_group_id=...)`는 선택한 provider map point의 `time_s`와
`substrate_current_A` NumPy 배열, `SeccmChronoamperometryTrace` provenance를 반환한다. 입력 header의
초와 A를 그대로 사용하며 scale 변경, smoothing, descriptor, label 또는 영상 결합을 하지 않는다.
map point는 독립 시편이 아니며 제공자 표 간 정합도 자동 추정하지 않는다. 인터페이스 ID는
`data.seccm_316l_raw_chronoamperometry`이고 상세 경계는
[SECCM 자료 계약](SECCM_316L_PITTING_DATA_KO.md)에 있다.

## 계산 실행

탄소강 1년 대기부식은 `corrosion.atmospheric_first_year_fit`과
`corrosion.atmospheric_first_year_prediction`으로 분리한다. 적합 모델은 전체 행 기준과 별도로
holdout source group별 오차·지원이탈 진단을 저장하며, 어느 그룹이든 caller 기준을 넘으면 전이 gate를
닫는다. 기준 미충족 모델은 `limited_transfer_override_reviewed`가 없으면 예측을 중단하며, 이 override도
모델을 자격화하거나 손실을 고장확률로 바꾸지 않는다. Calibration/holdout partition digest는 각 평가 입력 revision을 고정하고 pointwise 관측값을 결과에 복사하지 않는다. 자료 계약과 검증은
`ATMOSPHERIC_CORROSION_KO.md`를 따른다.

`degradation.atmospheric_scenario_ensemble`은 기존 1년 예측 계약을 시나리오별로 호출해 사용자가 정한
가중 평균·범위·경험 분위수를 집계한다. 시나리오마다 모델·기후 공변량을 달리할 수 있지만 asset/location,
physical scope, material condition, exposure environment와 노출 시계는 같아야 한다. 양의 가중치 합은
1이어야 하고, 그 의미를 호출자가 검토해야 한다. 각 시나리오의 support/transfer 조건이 유지되며 실패한
시나리오 하나라도 있으면 집계하지 않는다. 결과는 1년 평균 대기부식 손실 요약이며 확률분포·장기성장·국부
침투·수명·위험도를 의미하지 않는다.

모든 기본 계산은 `ModelRegistry`를 통해 같은 방식으로 실행한다. 각 모델의 입력 필드와 타입은 `describe()`의 JSON Schema가 기준이다. 변수 이름에 SI 단위가 붙으며 단위 변환은 계산 전에 수행한다.

`python
from matintegrity import evaluate
from matintegrity.contracts import RunContext

context = RunContext(
    asset_id="pipe-01", location_id="ut-point-01",
    time_basis="elapsed seconds from the reviewed inspection",
)
result = evaluate("corrosion.uniform_forecast", {
    "current_thickness_m": 0.010,
    "required_thickness_m": 0.006,
    "rate_m_s": 3.168808781402895e-12,
    "horizon_s": 31557600.0,
}, context)
print(result.status, result.values)
`

위 수치는 API 설명용 합성 입력이다. `required_thickness_m`는 별도의 적절한 평가에서 공급해야 한다. 결과의 `computed`는 선언한 수식과 적용 조건에서 계산했다는 뜻이다. 설비 합격이나 규격 인증의 뜻은 아니다.

`out_of_scope`는 모델의 적용 범위를 벗어났다는 뜻이다. `needs_data`는 계산에 필요한 가정이나 정보가 부족하다는 뜻이다. 입력 오류는 Pydantic 검증 예외로 구분한다. 결과의 단위, 적용 가정, 근거 ID, 입력 해시, 자산·부위·시간 기준과 실행 버전을 함께 보존한다.

`registry.run()`은 Python 타입을 엄격하게 검사한다. 예를 들어 `Evidence`의 tuple 필드는 Python tuple로 제공한다. JSON 파일·네트워크 요청에서는 `registry.run_json(model_id, inputs_json, context)`를 사용한다. JSON 배열·시간 문자열·중첩 계약을 Pydantic의 엄격한 JSON 모드로 읽는다. CLI·파라미터 프로필·워크플로도 이 경로를 사용한다. 비유한 수나 알 수 없는 키를 느슨하게 강제 변환하지 않는다.

`python
import json
from matintegrity.registry import default_registry

registry = default_registry()
inputs_json = json.dumps(result.inputs, allow_nan=False)
replayed = registry.run_json(result.model_id, inputs_json, context)
assert replayed.input_digest == result.input_digest
`

## 사용자 파라미터와 재료 표

`ParameterProfile`은 재료나 환경별 상수를 선언하고 관측 입력과 조합한다. 원래 상수를 바꾸려면 `overrides`에 명시해야 하며 변경 내용도 결과에 기록한다. 관측값에 같은 이름을 넣어 상수를 조용히 덮어쓰는 방식은 허용하지 않는다.

`TabulatedProperty`는 물성 표를 받는다. 좌표·물성 단위, 출처 ID와 보간 방법을 기록한다. 기본 선형 보간 외에 SciPy PCHIP를 선택할 수 있으며 표 범위 밖 외삽은 거절한다. 강도·인성 표의 출처와 적용 조건은 사용자가 공급한다.

`providers.PropertyIdentity`, `DesignPropertyTable`, `PropertyQuery`, `TabulatedPropertyProvider`는 허용값 등 조건에 민감한 표를 공급한다. 재료·제품형태·상태·방향·물성·근거·판본을 모두 정확히 대조한다. 일치하지 않으면 `needs_data`, 온도 범위 밖이면 `out_of_scope`다. 표 스냅샷·출처·이용권한 식별자·요청 및 표 해시를 보존한다. 사용자가 표를 넣었다는 사실이 사용권이나 규격 적합성을 자동 인증하지는 않는다.

`identification.MaterialDesignation`과 `DesignationResolver`는 정확한 명칭을 사용자 검토 별칭에 연결한다. `DesignationAlias`마다 출처·이용권한·허용 용도를 공급해야 한다. 중복 별칭, 유사 문자열 검색, 전이적 대체 관계는 허용하지 않는다. 조회 결과에는 요청·정규 명칭·근거·매핑 해시가 남는다.

`ChemistryRecord`는 원소별 `FractionInterval` 또는 미측정 `None`, 물리 범위·heat·측정법·구간 해석·근거를 보존한다. `ChemistryRequirements`에 사용자가 검토한 원소별 요구 구간을 넣고 `materials.chemistry_reconciliation`으로 비교한다. 원소 필드는 질량분율이다. 성적서와 검증 측정의 `physical_scope_id`는 같아야 하며 열 번호·검증 명칭·두 측정 구간 겹침 요구는 별도 bool 정책이다. 필드 전체와 실행 가능한 중첩 JSON은 모델 레퍼런스의 해당 절을 따른다.

`python
from matintegrity.data import TabulatedProperty
table = TabulatedProperty(
    property_id="synthetic-property", x=[100.0, 200.0], y=[10.0, 20.0],
    x_unit="K", y_unit="J/kg/K", source_id="project-example",
)
assert table.at(150.0) == 15.0
`

## 습식 CO₂ 외부 근거 대조

`wet_co2_data.audit_wet_co2_literature_row(compilation_row, evidence_row, field_maps)`는 호출자가
보유한 문헌·시험·현장 행과 편집본 한 행을 비교한다. `WetCo2LiteratureEvidenceRow`에 DOI 또는
다른 서지 ID, source locator·hash, 서지/편집행 연결 수준, 출판물 라이선스, 관측 재배포 검토와
시편·재료·노출 상태를 명시한다. `WetCo2LiteratureFieldMap`은 하나의 source 값을 scale·offset으로
변환하거나 둘 이상의 source 값을 산술평균한 뒤 scale·offset으로 변환한다. 각 map은 근거 ID와
절대 허용오차를 가져야 한다.

결과 `WetCo2LiteratureCrosswalkAudit`는 source 값, 변환값, 편집값, 차이와
`match`·`mismatch`·`source_missing`·`compilation_missing`을 보존한다. 같은 편집 필드를 두 번
mapping하거나 선언되지 않은 source field를 참조하면 거절한다. 이 함수는 원행을 수정하지 않으며
모든 선언값이 일치해도 보정 가능 상태를 부여하지 않는다. 실제 문헌의 점별 표는 패키지에 넣지
않고 사용자가 적법하게 보유한 값으로 호출한다. 전체 계약과 현재 자격화 경계는
[습식 CO₂ 자료 설명](WET_CO2_DATA_KO.md)에 있다.

`wet_co2_data.read_wet_co2_simulation_grid(path)`는 CC BY 4.0 NORSOK M-506 기반 모의 workbook을 SI `WetCo2SimulationGridRow` 계약으로 읽는다. 각 행에 DOI, provider row, 파일 digest, 저작자 표시와 명시적 시뮬레이션 결과 상태를 넣으며 실험 보정자료로 바꾸지 않는다. [공개 습식 CO₂ grid 안내](WET_CO2_SIMULATION_GRID_KO.md)를 참고한다.

`summarize_wet_co2_simulation_grid(WetCo2SimulationGridSummary(...))`는 같은 workbook에서 골라 전달한 행의 기술통계만 균등행 가정으로 요약한다. 출처 파일·행 추적을 보존하고 데이터 값에 확률 의미를 부여하지 않는다.

`thermo.co2_fugacity_coolprop`은 선택 의존성 `matintegrity[thermo]`의 CoolProp `AbstractState`로 순수 CO₂ EOS fugacity를 계산한다. 입력 압력은 전체 혼합압이 아니라 절대 CO₂ 부분압이며, 순수 성분 근사와 단일상 기체/초임계 해석에 대한 caller review를 요구한다. 결과의 `values`에 `coolprop_co2_fugacity_to_carbonate_fields(...)`를 적용하면 `chemistry.fixed_fugacity_carbonate_equilibrium` 입력의 fugacity 및 provider 계보 필드가 된다. `coolprop_co2_fugacity_to_aquasoldb_fields(...)`는 AquaSolDB 독립 비교 API용 fugacity·온도·provider 필드를 만들며, 관측·Henry 기록을 독립적으로 선택/검토하는 절차는 생략하지 않는다. 이 경로는 혼합기체 상호작용, 수용액 평형, Henry 계수 또는 부식률을 계산하지 않는다. [CoolProp CO₂ fugacity 안내](CO2_FUGACITY_COOLPROP_KO.md)를 참고한다.

`thermo.co2_pure_fugacity_history`는 시점별 순수 CO₂ `CoolPropCo2FugacityRequest` tuple을 기존 evaluator에 순서대로 전달한다. Clock/state alignment review와 동일 backend를 요구하고, 첫 실패에서 계산된 prefix를 보존한다. 시간 사이 보간 및 혼합물 상호작용은 처리하지 않는다. 자세한 범위는 [CoolProp fugacity 안내](CO2_FUGACITY_COOLPROP_KO.md)를 참조한다.

`thermo.co2_mixture_fugacity_history`는 동일한 성분 목록·순서·CoolProp backend를 유지하면서 시점별 온도, 전체압력, 조성을 적용한다. 한 history에서 provider 상태 객체를 재사용하고 첫 실패 전의 prefix 및 요청 digest를 보존한다. clock/state 정렬과 매 절점의 조성·EOS·단상 검토가 필요하며 시간 보간이나 이상혼합 fallback은 하지 않는다.

혼합기체 조성이 알려졌다면 `thermo.co2_mixture_fugacity_coolprop`에 CoolProp component 이름, 합계 1인 mole fraction, 전체 절대압과 온도를 공급한다. 각 component 사이의 필요한 interaction parameter와 EOS 적용성은 caller가 검토해야 한다. provider 계산 실패 시 ideal-mixture fallback 없이 `out_of_scope`를 반환한다. 기체·초임계 계열 상태에서의 CO₂ 성분 fugacity 계보는 `coolprop_co2_mixture_fugacity_to_carbonate_fields(...)`와 `coolprop_co2_mixture_fugacity_to_aquasoldb_fields(...)`로 연결할 수 있다. 수용액, Henry 계수, 부식률은 여전히 별도 모델·자료다.

시간 이력은 `Co2MixtureFugacityHistory` (`matintegrity.co2_mixture_fugacity_history.v1`)로 전달한다. `read_co2_mixture_history_csv()`는 CSV bytes를, `load_co2_mixture_history_csv()`는 파일 경로를 받아 caller 지정 열 매핑으로 초·절대 Pa·K·성분 몰분율을 읽고 원본 bytes의 SHA-256을 보존한다. 단위 추정이나 조성 정규화는 하지 않는다. `co2_mixture_fugacity_requests_from_history()`는 sample clock, component order, 절대압, 온도, source/case/solver digest를 보존해 표본별 CoolProp request를 만든다. invalid row에서는 압력·온도·성분을 `None`으로 보존할 수 있고, 해당 행은 제거하지 않고 `needs_data`로 유지한다. 생성된 각 유효 표본 request는 별도로 registry에서 실행해야 하며 output은 여전히 gas fugacity로 한정된다. 합성 입력은 `examples/co2_mixture_history.py`를 참고한다.

PSA-Dyna의 `dynamic-psa-mean-stream/v1` report를 사용하는 경우 메모리 JSON은 `co2_mixture_fugacity_requests_from_psa_dyna_mean_stream()`, JSON 파일은 `load_co2_mixture_fugacity_requests_from_psa_dyna_mean_stream()`에 전달한다. 파일 adapter는 원본 byte SHA-256과 canonical report digest를 각각 보존하며 내부 경로의 case/result 파일을 따라가거나 다시 읽지 않는다. 호출자는 명시적인 stream ID와 review를 제공한다. adapter는 bar→Pa 변환을 수행하지만 압력의 absolute basis를 caller가 검토하지 않으면 요청을 `needs_data`로 남긴다. case/result/source archive digest, upstream payload status/release flags와 payload digest를 유지하고 결과 계약은 `PSADynaMeanStreamFugacityBatch`다. 입력이 주기 적분 평균 스트림이면 output도 cycle-mean 조건 평가일 뿐, 시간 이력·극값·노출시간이나 금속 표면 조건이 아니다. 위치-표면 매핑, 부식 경계 적합성, CoolProp 계산과 부식 평가는 별도 단계다. 합성 조합 예제는 `examples/psa_dyna_mean_stream_fugacity.py`를 참고한다.

여러 경쟁 중성 고체상을 함께 푸는 `chemistry.competitive_solid_equilibrium`은 각 상 반응과 Ksp, 공통 수용액 종목록, 고정 gamma, 완전한 candidate phase set review를 caller에게 요구한다. 고정-gamma Gibbs potential 최적화 결과는 각 상의 포화/불포화 complementarity와 농도 extent balance가 확인될 때만 `computed`다. 자동 speciation·활동도 iteration·침전속도/핵생성·표면 보호·부식률을 추정하지 않는다. 범위와 한계는 `docs/COMPETITIVE_SOLID_EQUILIBRIUM_KO.md`, 합성 입력 모양은 `examples/competitive_solid_equilibrium.py`에 있다.

`chemistry.competitive_solid_davies_equilibrium`은 같은 caller-owned 경쟁 중성 고체상 평형을 액상 몰랄 이온강도에 대한 Davies 계수 반복으로 닫는다. 후보 종·상과 반응식, Ksp, water-mass conversion, 온도별 Davies A와 모든 source lineage는 caller가 공급해야 하며, 반복 실패·전하 불균형·0.5 mol/kg 초과 시 결과를 평형으로 승격하지 않는다. 자동 종 생성, 고체상 kinetics, scale 성장·보호 또는 부식률은 포함하지 않는다. 상세 경계는 `docs/COMPETITIVE_SOLID_DAVIES_EQUILIBRIUM_KO.md`, synthetic wiring은 `examples/competitive_solid_davies_equilibrium.py`를 참고한다.

## COQTEL 국부부식·Lamb-wave 자료

`signals.coqtel_electrochemistry(path, duplicate_policy, require_pinned_hash)`는 한 HDF5 실험의
EC 행과 `State_i`를 같은 번호로 연결하고 source SHA-256, 물리 시편 ID, 반복 시각, 전류·전위,
signed/anodic 전하와 보고된 교란 상태를 반환한다. `signals.coqtel_waveform`은 한 state의 명시한
actuator–sensor 경로만 읽고 receiver 행 순서와 HDF sampling 정의를 검사한다.
`signals.inspect_coqtel_experiment`는 두 고정 파일의 전체 구조를 집계 감사한다. 어느 함수도 전하나
파형 차이를 pit 치수·부식속도·POD·수명으로 변환하지 않는다. 상세 경계는
[COQTEL 자료 설명](COQTEL_DATA_KO.md)에 있다.

행 단위 Pydantic/Evidence 계보가 필요하면 `matintegrity.coqtel_typed_rows.iter_coqtel_electrochemistry_rows`를 사용한다. 입력 `CoqtelReadAuthorization`에는 CC BY attribution과 caller의 계산·로컬사용 선언을 전달해야 하며, typed row에는 원본순서, 1-based EC/State row, 파일 SHA-256, canonical row SHA-256, Evidence, authorization digest 및 `local_only` boundary가 포함된다. 기존 parser의 고정 checksum 검사와 동일시각 행 보존을 재사용한다. `audit_coqtel_archive`는 point value와 경로를 제외한 metadata만 반환한다. 해당 계산은 pit 치수, 감육량, 부식률 또는 failure probability를 도출하지 않는다. 자세한 입력·필드 의미는 [COQTEL typed row API 설명](datasets/COQTEL_TYPED_ELECTROCHEMISTRY_ROWS_KO.md)을 참고한다.

## 사용자 계산기

## 누설자속검사 acquisition

`inspection.magnetic_flux_leakage_acquisition_summary`는 `MflExamination`을 받아 자화기·센서 array와
channel/component mapping, reference feature, 검토된 H/B vector checkpoint, encoded scan과 indication
근거를 보존한다. 전체 좌표가 있을 때 encoded span을 계산하고 H/B vector magnitude와 비구성적 B/H
ratio를 반환한다. 이 값은 permeability·포화·검출감도 또는 결함 크기가 아니다. 합성 실행은
`examples/magnetic_flux_leakage.py`, 전체 경계는 [누설자속검사 문서](MAGNETIC_FLUX_LEAKAGE_KO.md)를
따른다.

## 와전류 acquisition과 DICONDE

`inspection.eddy_current_acquisition_summary`는 `EddyCurrentExamination`을 입력받아 절차·probe·주파수,
reference standard feature, encoded raster와 indication evidence를 한 결과로 묶는다. reference standard가
실제 probe와 모든 scan frequency를 덮지 않으면 거절한다. 전체 좌표가 검토된 scan만 span을 계산하며,
명시적인 선형·균질 적용성 검토와 conductivity·상대투자율·온도·근거가 있어야 고전 skin depth를
계산한다. `examples/eddy_current.py`가 합성 입력 예다.

`read_eddy_current_diconde(path, physical_specimen_id=..., source_role=...,
component_order=(...), component_order_basis=...)`는 `EddyCurrentDicondeRecord`, 원 저장 component 배열과
padding mask를 반환한다. 호출자가 frame component 순서와 근거를 지정해야 한다. reader는 rescale,
phase rotation, filtering, detection, sizing 또는 acceptance를 적용하지 않으며 사람 관련 DICOM field를
공개 계약으로 내보내지 않는다. 전체 제한은 [와전류검사 문서](EDDY_CURRENT_KO.md)를 따른다.

`Contract`를 상속한 입력 스키마와 `Calculation`을 반환하는 함수를 작성해 `ModelSpec`으로 등록한다. 모델 ID·버전·출처·적용 가정·단위를 반드시 제공한다. Python 플러그인은 사용자가 신뢰하는 코드로 설치하며 문자열 수식을 자동 실행하지 않는다.

`python
from matintegrity.contracts import Calculation, Contract
from matintegrity.registry import ModelRegistry, ModelSpec

class Parameters(Contract):
    value: float

def custom_model(parameters):
    return Calculation(values={"scaled": 2 * parameters.value})

registry = ModelRegistry()
registry.register(ModelSpec(
    model_id="user.scaling", input_type=Parameters, evaluator=custom_model,
    units={"scaled": "1"}, assumptions=("Synthetic example.",),
    source_ids=("user-method",), qualification="user_model",
))
`

## 계산 조합과 사용자 규칙

과도 열전도는 `thermal.transient_conduction_1d`, 두께방향 탄성 열응력은 `mechanics.through_wall_thermal_stress`로 실행한다. 열전도 입력은 형상·격자·재료 ID, 온도별 열전도율/체적 열용량, 초기온도, 출력 시각, 경계조건과 선택적 발열/분포 대류·회색복사를 갖는다. 분포 복사는 방사율·복사환경 온도 이력과 적용성 검토가 필요하다. 표 범위 밖 외삽은 없고 경계 열률은 계산 영역으로 들어오는 방향이 양수다. 열응력 입력은 위치별 온도·기준온도·열팽창계수·E·포아송비·탄성 한계와 평면/제어 조건을 갖는다. 네 물성 profile별 `property_profile_evidence`로 선택적인 출처 Evidence를 연결할 수 있으며, 결과는 profile digest와 출처 상태를 보존한다. 전체 필드와 결합 예는 [열구배 설명](THERMAL_GRADIENT_KO.md)과 `examples/thermal_gradient.py`를 따른다.

열물성 표에 provider/revision/record·원본 digest·Evidence를 선택 입력할 수 있다. 계산 결과는 원본 Evidence와 별도로 실제 사용된 정규화 물성 벡터의 SHA-256을 재료별로 반환해 외부 재사용과 계보 확인에 쓸 수 있다.

열전도 결과를 응력해석으로 넘길 때 `matintegrity.bind_thermal_temperature_profile()`은 전체 source result SHA와 등록 입력 digest를 확인하고 선택 온도 행을 위치가 정확히 일치하는 `ThroughWallThermalStress` 요청에 결합한다. 선택 시각·자산·위치·time basis가 응력 결과에 남고, registry context도 원 열전도 결과와 맞아야 한다. 보간이나 좌표변환은 하지 않는다.

`thermal_data.read_thermal_rod_series(path, run_id)`는 77개 공개 rod run의 원 시계·TC1~TC6·controller setting과 파일/멤버 해시를 읽는다. `read_thermal_rod_fitted_results(path)`는 처리 workbook의 계수와 오차를 읽고 같은 관측을 적합한 값임을 표시한다. controller setting을 W로, 처리 적합 행을 독립 시험으로 변환하지 않는다. 외부 교환용 인터페이스 `data.transient_thermal_observations`는 시간·위치·단위·출처·관측/적합 관계를 보존해야 한다.

`corrosion_metrics_data.read_corrosion_alloy_metrics(path, require_pinned_hash=False)`는 부식저항
합금 편집 workbook을 긴 형식의 지표 셀로 읽는다. `source_observation_id`와 지표별
`observation_id`, endpoint, average/maximum/minimum/standard-error/reported 통계량, 원 값,
`exact`·`lower_bound`·`upper_bound`·`qualitative`·`missing` 상태, 성분·시험조건·참조번호와
workbook 해시를 보존한다. `require_pinned_hash=True`는 현재 Figshare v2 파일만 허용한다.
전위는 `V_vs_SCE`로 기준을 유지하고 온도·전류밀도·부식속도를 SI로 변환한다. 참조 DOI는
source group 정보일 뿐 물리 시편·시험 유효성·관측 재배포 권리를 채우지 않는다. 서로 다른
끝점을 하나의 내식성 순위나 설계값으로 자동 결합하지 않는다.

`WorkflowStep`과 `OutputBinding`으로 앞 단계의 명시된 결과 필드를 다음 모델 입력에 연결한다. 결과가 미확정이거나 적용 범위 밖이면 후속 계산을 중지한다. `examples/python_composition.py`는 두께 추세에서 감육 예측으로 이어지는 실행 예제다.

요구조건 충족이 후속 절차의 전제라면 `WorkflowStep(..., satisfaction_gate=SatisfactionGate(output_key="outcome"))`를 선언한다. 해당 결과가 정확히 `satisfied`일 때만 다음 단계로 간다. `not_satisfied`는 절차의 `out_of_scope`, 누락·미확정은 `needs_data`로 중지한다. `policy_gate`에는 비교 필드·관측값·중지 결과가 남고 원 모델의 `computed` 상태는 그대로 보존된다. `examples/material_verification_gate.py`는 합성 성분이 모두 확인된 경우와 탄소가 미측정인 경우를 실행한다. gate를 선언하지 않은 단계는 계산 상태만으로 진행한다.

`Rule`과 `evaluate_rules`는 사용자가 제공한 한계값과 적용 조건을 검사한다. 누락된 값이나 단위 불일치는 `unknown`으로 남는다. `MaterialRecord`, `WeldProcedureRecord`, `InspectionRecord`, `HeatTreatmentRecord`로 재료·시공·검사 근거를 교환할 수 있다. 일반 규칙 엔진이 특정 규격의 모든 요구사항을 내장했다는 뜻은 아니다.

## 확률과 불확실성

`corrosion.simulation_rate_wall_loss_scenario`는 CC-BY-4.0 wet-CO₂ 제공자 시뮬레이션 행을 명시적 가중치와 함께 고정 선형 감육 시나리오로 전달한다. 물리 시편이나 실험 관측으로 바꾸지 않으며 DOI·행 번호·원본 archive SHA-256·evidence를 결과에 보존한다. 재료상태, 조건 전이, 선형 감육 검토 ID를 모두 요구한다. 가중 임계통과량은 입력 가중치 의미만 따르며 고장확률·신뢰구간·FTA 사건확률이 아니다. 합성 API 입력은 `examples/model_inputs.json`, 세부 계약은 `MODEL_REFERENCE_KO.md`에서 확인한다.

다른 시뮬레이션 공급자나 caller-defined 시나리오를 쓰려면 `CorrosionRateProjectionRow`와 `corrosion.model_output_rate_wall_loss_scenario`를 사용한다. 각 행에 dataset/group/record ID, SI rate, archive digest와 일치하는 `Evidence`, `simulated_model_output` 또는 `caller_assumed_scenario` 역할을 전달한다. 하나의 scenario set 안에서 출처 계보와 역할은 동일해야 하며 물리 시편 행은 empirical observation/sample API로 보낸다. NORSOK adapter `wet_co2_simulation_row_to_projection_row`가 구체 예다. 이것도 검토 게이트를 거친 선형 감육 시나리오이며 관측 보정·사건확률을 만들지 않는다.

검토된 일반 rate 시나리오를 최초 통과 위험 계산에 넘기려면 `corrosion_model_output_to_first_passage_inputs(...)`가 `SampledLinearThicknessFirstPassage` 입력 객체를 만든다. 자산·위치·물리 범위·평가 시각·생존조건·사건 정의·후보시각·분포 정의와 review ID를 호출자가 공급한다. 시나리오 weight는 그 자체로 확률이 아니며 adapter도 확률을 만들지 않는다. 별도 최초 통과 계산은 survival, joint distribution, rate law, 두께 기준과 시간 후보 검토가 모두 통과해야 계산되며, source lineage와 review IDs가 결과에 보존된다. 그 계산 결과는 기존 `probability_event(...)` 경계로 외부 FTA에 전달할 수 있다.

`examples/corrosion_to_first_passage.py`는 이 adapter → first-passage model → `EventProbability` 구성을 synthetic 입력으로 보인다. 이 예제의 확률 의미는 별도 분포·생존조건·자산/시간·검토 ID 선언에 한정되며 실제 설비 신뢰도 자료로 해석하지 않는다.

`corrosion.gumbel_area_maximum`은 `block_ids`, `maximum_depth_m`, `block_area_m2`, 정수 `target_block_count`와 표본 조건을 받는다. `extreme_value_family`는 `gumbel`(기본값) 또는 `gev`를 선택한다. 인구·노출 식별자, 독립/동일 모집단/완전 미검열 여부, 면적 외삽 상한, 목표 깊이·분위수·신뢰수준, 재표집 수·seed·진단 기준을 모두 명시한다. `python examples/pitting_area.py --family gev`로 합성 GEV 경로를 실행할 수 있으며 `--family gumbel`은 기존 기본 경로다. 검출되지 않은 pit을 0 깊이로 입력하거나 실제 반복 시계열을 독립 블록으로 바꾸지 않는다.

`AssessmentResult.probability_semantics`와 `ModelSpec.probability_semantics`는 출력 필드별 확률의 의미를 선언한다. 사용자 모델에 기간 최초고장 출력이 있다면 물리·시간 근거를 검토하고 `{"field": "conditional_first_failure_in_period"}`를 등록한다. 등록한 필드의 출력 단위는 `"1"`이어야 한다. 선언이 없거나 공간 초과·POD·unscoped인 결과는 `probability_event`가 거절한다. 기존 결과 JSON의 이 필드가 빠졌을 때 기본값은 빈 dict이며 자동으로 의미를 추정하지 않는다. 새 스키마와 수신 측 계약을 함께 갱신한다.

`probability_event`에 Weibull 결과를 보낼 때 시작·종료 시각은 `current_age_s`와 `current_age_s+horizon_s`에 맞춘다. 사용자 모델은 선언한 기간·생존 조건을 사용자가 직접 보장해야 한다. `monitoring_record`는 `MonitoringAssessmentRecord`로 의미·입력·문맥·출처와 완전 평가 digest를 독립 스냅샷으로 보존한다. 값·모델·확률 의미를 바꾸고 digest를 유지한 레코드는 거절한다. 설명 입력에는 전체 평가 객체가 포함된다. 상세 경계는 [공정 모니터링 교환계약](MONITORING_EXCHANGE_KO.md)을 따른다.

`simulate_limit_state`는 표본별·시각별 한계상태 여유를 받는다. 최초 시점에 생존한 표본에 조건부로 이후 최초 기준 도달을 집계한다. 입력의 독립성을 명시해야 하며 시간 격자 사이의 기준 도달을 놓칠 수 있어 격자 수렴 확인이 필요하다. 이항 신뢰구간은 표본추출 오차만 나타낸다.

`fit_censored_sn`는 응력 범위·파단 또는 시험 종료 사이클·runout 플래그를 받아 로그정규 수명 우도를 적합한다. 반복 시험 단계는 독립 시편으로 다루지 않는다. 반환 파라미터는 선택한 재료·용접 상태·응력비·시편 범위에 조건부다.

`inspection.hit_miss_pod`는 시편 ID·결함 크기·검출 여부와 독립성 선언을 받는다. `probability_of_detection` 배열을 같은 크기 bin의 `inspection.no_indication_update`에 명시적으로 연결할 수 있다. 실행 예제는 `examples/pod_to_inspection_update.py`다. 점별 신뢰하한들을 독립적인 확률 표본으로 간주하지 않는다. 결과의 `logistic_midpoint_size_m`, `logistic_log_size_scale`은 기존 `inspection.logistic_pod`에 연결하는 곡선 파라미터이며, 내부 표준화 계수와 구분된다.

`fatigue_data.read_fabest`는 고주기 관측·변형률 수명·정적 기준·그룹 메타데이터를 분리해 반환한다. `reported_endpoint`, `cycles_to_end`, `cycles_to_reported_break`를 각각 보존하고 `endpoint_contract_status`를 `reported_break_cycle`, `reported_interruption`, `unresolved`, `conflicting_provider_fields`로 구분한다. Provider interruption을 자동으로 runout으로 바꾸지 않는다. `calibration_role`은 깨끗한 행도 `candidate_*`일 뿐이며, 문자 접미사나 주석이 있으면 `needs_specimen_protocol_review`다. `comment_review_tags`와 `reported_comment_temperature_degC`는 자유문 선별 결과이며 시험 유효성·self-heating·시편 온도 판정이 아니다. 모든 행의 `physical_specimen_independence_reviewed`는 근거가 없으면 false다. `data.read_bam_creep_fatigue`는 SI 파형과 `cycle_extrema`를 반환하고 `fatigue_data.summarize_recorded_bam_cycles`는 실제 기록 사이클의 경로 일·끝점 차이를 제공한다. 없는 사이클이나 미세 시계를 보간하지 않는다.

`fracture.variable_paris`는 `TensileLoadBlock` 목록과 범위가 있는 형상표를 받는다. 종료 이유는 인성, 지정 깊이, 성장 보정 범위 등을 구분한다. 결과의 종료 깊이를 FAD line 도달로 이름만 바꿔 사용하지 않는다. 환경별 계수와 형상계수의 자격은 사용자 공급 근거를 따른다.

`impact_data.read_charpy_compilation()`은 관측값·원 문헌 식별자·보고 행 번호·SI 형상·조건 그룹·품질 표식을 반환한다. 보고 곡선 ID만으로 그룹화하지 않는다. `materials.impact_transition`에는 사용자가 검토한 한 조건의 관측만 넣는다. 실제 문헌 관측과 점별 적합·잔차는 공개 예제에 포함하지 않는다.

`ultrasound_data.read_willow_feature_table(path, domain="simulation"|"field", series_id=...)`는 원 열과 처리 성공·개별 누락을 보존한다. 합성에서는 `synthetic_length_unit="mm"`와 확인한 `specimen_thickness_m`를 공급한다. 합성 유효 깊이·폭은 `synthetic_reference_*`이며 실제 시계열에는 이 참값 필드를 만들지 않는다. 실제 초기 pit 치수는 `initial_pit_*_m`다. 같은 실제 시편의 `observational_unit_id`는 모든 시점에서 유지된다.

`guided_wave_data.list_guided_wave_acquisitions(path)`는 고정 외부 ZIP과 내부 ZIP을 검사하고 XLS를 열지 않은 acquisition 목록을 반환한다. `read_guided_wave_acquisition(path, acquisition_id, specimen_id=...)`는 지정 workbook만 읽고 주파수별 `distance_m`, `torsional_V`, `flexural_V`, `provider_pure_dac_V` 배열과 원 sheet 순서·workbook SHA-256을 반환한다. `iter_guided_wave_acquisitions`는 전수 처리를 위한 순차 API다. 파생 archive에는 207/29 논문 구간을 자동 적용하지 않으며 여섯 가공 단계·잔여두께·시각·온도는 만들지 않는다. `data.guided_wave_pipeline_observations` 인터페이스로 추적한다.

`pitting_data.read_local_pitting_numeric_mat(path, *, expected_sha256, dataset_id,
physical_specimen_id, source_group_id, source_role, ...)`는 checksum-pinned MATLAB level-5 파일에서
최상위 실수 numeric 배열만 읽는다. 반환값의 `metadata`는 `LocalPittingMatRecord`, 각 변수는
`NumericMatVariableRecord`이며 `raw_arrays`에는 변환하지 않은 배열 복사본이 있다. 호출자가 변수별
`(unit, basis)`와 해석·좌표 검토 근거를 명시하지 않으면 단위·정합·의미는 비어 있다. struct·cell·
object·sparse·complex·v7.3/HDF5와 과대 파일을 거절한다. 동일 shape는 동일 좌표나 시간 전이의
근거가 아니다. `data.aa7050_local_pitting_mat` 인터페이스와
[자료 계약](AA7050_LOCAL_PITTING_DATA_KO.md)으로 추적한다.

`spatial_fields.RectilinearFieldMetadata`는 별도 2차원 배열을 물리 시편·source group, 원자료·배열·
Boolean 결측 mask 해시, 물리량·단위·관측시점, 검토된 metre 좌표축과 좌표계에 결속한다.
`sample_rectilinear_field`는 같은 frame 또는 검토된 `PlanarAffineCoordinateTransform`으로 직접 매핑된
점에서만 nearest/bilinear 표본화한다. 지원영역 밖과 결측 support는 요청의 명시적 정책에 따라
거절하거나 `None`과 상태로 반환한다. 배열 shape·extent·이름으로 정합을 추정하지 않으며 pit 분할,
성장률·POD·수명을 만들지 않는다. `data.reviewed_rectilinear_spatial_field` 인터페이스와
[공간장 계약](SPATIAL_FIELD_EXCHANGE_KO.md)으로 추적한다.

`adapters.guided_wave_pair_feature_inputs(baseline, observation, ...)`는 같은 archive·physical specimen의 서로 다른 두 acquisition에서 정확히 지정한 주파수와 torsional 또는 flexural 채널을 선택한다. 반환값은 등록 모델 `inspection.guided_wave_pair_features`에 바로 전달할 수 있다. 모델은 정렬·보간하지 않고 호출자 지정 폐구간의 baseline/observation/residual RMS, 정규화 residual, 전압 에너지비, Pearson 상관, 최대 절대차와 부호 평균차를 계산한다. 거리 반복은 `preserve_samples`, `mean_aligned_duplicates`, `reject` 중 하나로 명시하며 두 acquisition의 반복 위치가 다르면 거절한다. 영 baseline의 정규화값과 퇴화 상관은 `None`이다. 이 값은 기술적 파형 descriptor이며 손상 등급·잔여두께·POD·합격·수명·고장확률이 아니다.

`adapters.guided_wave_reference_ensemble_inputs(baselines, observation, ...)`는 같은 관·archive의 고유 baseline 세 개 이상과 별도 observation을 조합한다. `inspection.guided_wave_reference_ensemble`은 호출자가 고정한 baseline source group·observation source group·선택 근거, 정확한 주파수/모드, 공간창, 반복 거리 정책과 mean/median reference를 보존한다. 점별 reference에 대한 baseline spread, 각 baseline의 leave-one-out residual RMS 분포, observation residual과 이들의 비를 계산한다. 비는 선택된 반복 acquisition 집합의 상대 기술량이지 이상확률·검출 임계값·POD·독립 시편 검증이 아니다.

`read_willow_field_signals(path, series_id=..., sample_interval_s=None, reported_temperature_unit=None)`는 원 ADC 파형·장치 설정·미확정 시간대의 달력 시각을 읽고 device ToF의 ns를 s로 변환한다. 표본 간격을 확인해 공급했을 때만 배열 0번부터의 상대 표본 시계를 만든다. 온도 단위를 공급할 때만 ambient K로 변환하며 이를 시편 온도로 가정하지 않는다. 중복 JSON 키·역전 시각을 조용히 덮거나 정렬하지 않는다.

`read_ceit_uniform_corrosion_field(path, series_id=..., reported_tof_unit=None, reported_temperature_unit=None, sample_interval_s=None)`는 단일 해안 노출 강재 시편의 장치 레코드와 raw·filtered·correlation·envelope 배열을 원 순서로 읽는다. 원 JSON은 ToF·온도·파형 시계 단위를 선언하지 않으므로 검토한 호출자가 단위를 명시할 때만 초·K·표본 시계를 만든다. raw ADC rail 개수를 보존하고 음속·왕복경로·zero 보정 없이 두께나 부식속도를 만들지 않는다. 상세 경계는 [해안 노출 균일부식 자료 계약](FIELD_UNIFORM_CORROSION_KO.md)에 있다.

`PulseEchoThicknessCalibration`과 `pulse_echo_thickness_observations`는 검토된 ToF 단위가 있는
series에 caller-owned 교정을 적용한다. 교정에는 적용 가능한 시편·프로브 ID, 재료, 종파 음속,
온도, zero offset, 입사각, raw/보정 ToF 선택, 근거와 검토 flag가 포함된다. ID 또는 검토가
일치하지 않으면 중지한다. 출력은 교정 digest와 SI 두께를 보존하지만 측정 불확실성·공간위치·독립
치수 검증을 만들어내지 않으며 부식속도나 Bayesian 갱신 준비 상태로 자동 승격하지 않는다.

`inspection.pulse_echo_sound_speed_fit`은 사용자가 보유한 기준시편의 독립 치수와 왕복 ToF로
종파 음속 하나를 적합한다. `PulseEchoSoundSpeedFit`에 고정·검토된 zero offset, 입사각, 온도,
probe·재료 ID와 `PulseEchoCalibrationObservation` 목록을 넣는다. 최소 세 calibration 관측과
한 holdout 관측을 요구하며 물리 위치 또는 source group이 두 분할을 넘나들면 거절한다. 적합은
calibration 행에만 원점을 지나는 최소제곱을 적용하고 holdout은 사후 잔차에만 쓴다. 출력의
`calibration_fragment`는 sample 적용범위가 비어 있고 `calibration_reviewed=false`이므로 호출자가
범위와 적합성을 검토하기 전에는 두께 변환에 사용할 수 없다. 공개 계약은
`docs/schemas/PulseEchoSoundSpeedFit.json`과 `PulseEchoCalibrationObservation.json`이다. 각 행에
기준치수와 왕복시간의 표준불확실성을 함께 넣고 `fit_method="iterative_effective_variance"`를
선택하면 두 오차를 합성한 반복 가중치를 사용한다. 조건부 음속 불확실성·reduced chi-square와
표준화 holdout 잔차를 반환한다. shared zero·각도·온도·probe·coupling 계통오차는 포함하지 않는다.
JSON 파일 없이 Python 객체만 사용하는 실행 예는 `examples/pulse_echo_sound_speed_fit.py`다.

`iter_willow_simulations(path, source_length_unit="m", sample_interval_s=None)`는 MATLAB v7.3/HDF cell의 시뮬레이션 ID·형상·유효 기하·파형을 순차 반환한다. 비유한 실패 파형과 시간축 부재를 보존한다. `scripts/inspect_willow_data.py`는 전체 기하·시각 매핑과 누락·미보정 특징 진단을 재현한다. 이 출력은 보정된 현장 치수나 POD 공급자가 아니다.

`inspection.visual_surface_summary`는 `VisualSurfaceExamination` Python 객체 또는 같은 구조의 dict/
JSON을 받는다. 사용자 절차·개정, direct/remote 방식, 표면상태, 조명·분해능 근거, target/examined
영역과 미검사 사유, 위치별 지시와 증거를 보존한다. 면적 coverage와 보고 유형별 기술 집계만
반환하며 지시가 없으면 별도의 negative-result 검토가 필요하다. 규격 합격·결함 분류·POD를
반환하지 않는다. 상세 계약은 [육안검사 문서](VISUAL_INSPECTION_KO.md)를 따른다.

`inspection.liquid_penetrant_summary`와 `inspection.magnetic_particle_summary`는 공통 area/indication
계약 위에 각 검사법의 공정조건을 별도로 보존한다. 침투검사는 소모품 batch, 표면 전처리·건조,
온도, 침투·현상시간과 관찰조건을 요구한다. 자분검사는 강자성 검토, particle/carrier, 장비,
각 magnetization pass의 무방향 field 각도와 adequacy 근거를 요구한다. 방향 coverage의 최소각은
사용자가 근거와 함께 공급한다. 상세 필드와 한계는 [표면검사 문서](SURFACE_EXAMINATION_KO.md)에 있다.

`inspection.radiographic_geometry_summary`는 X-ray/gamma source, 노출, 검출기, 원 영상 hash와
크기, IQI 기록, 영상-space 지시 및 선택적인 물리 위치 mapping을 보존한다. 공급된 SOD·ODD·초점
크기·pixel pitch에서 pinhole magnification, geometric unsharpness와 object-plane pixel pitch만
계산한다. 거리나 review가 없으면 추정하지 않고 `needs_data`를 반환하며 규격 한계, 총 영상분해능,
결함 크기·합격·POD를 생성하지 않는다. [RT 계약 문서](RADIOGRAPHY_KO.md)에 전체 경계가 있다.

`inspection.phased_array_acquisition_summary`는 probe/wedge, specimen velocity, focal law, encoder,
원 frame hash와 indication mapping을 보존한다. pulse-echo와 transmit/receive, conventional law와 FMC를
구분하고 aperture·nominal wavelength·pitch ratio·delay span·encoder spacing만 계산한다. 파형 처리,
focal-law 재생성, TFM, 결함 검출·크기·POD·합격은 수행하지 않는다. 상세 계약은
[PAUT 문서](PHASED_ARRAY_KO.md)에 있다.

`ml_ndt_data.list_ml_ndt_batches`와 `read_ml_ndt_batch`는 사용자가 별도로 보유한 ML-NDT 고정 commit
clone에서 provider partition·batch UUID·원 파일명/크기/SHA-256·UInt16 형상·label/JSON 정합성을
읽는다. `read_ml_ndt_image`는 명시한 byte order로 한 영상만 읽고 감사 당시 binary digest를 재검사한다.
이 API는 자료를 다운로드·복제하거나 augmented 영상을 독립 물리 시편, 원 FMC, 결함 truth 또는 POD로
변환하지 않는다.

`inspection.tofd_acquisition_summary`는 별도 송수신 probe/wedge, probe index separation, 종파 속도,
벽두께, encoder frame과 lateral/backwall/upper/lower arrival pick을 받는다. 같은 frame lateral wave에
대한 지연과 호출자가 검토한 대칭 직선경로에서만 tip depth와 paired-tip separation을 계산한다. 원 frame
hash와 pick evidence는 유지하며 파형 처리·자동 picking·dead-zone·합격·POD는 수행하지 않는다.
[TOFD 문서](TOFD_KO.md)에 전체 계약이 있다.

제작·용접·방식 모델 ID는 `fabrication.thickness_budget`, `welding.joint_profile`, `welding.hardness_traverse`, `welding.dilution`, `protection.cathodic_budget`다. 각 입력의 공급자 조건·단위·순서와 수학적 범위는 `METHODS_KO.md`, 전체 필드·실행 예제는 `MODEL_REFERENCE_KO.md`를 기준으로 한다. 사용자 한계값은 `RunContext.evidence`에 출처를 붙여 보존한다.

## 국부 감육과 파열 자료

`structural.failure_assessment_points`는 `FailureAssessmentCurve`와 하나 이상의 `FailureAssessmentPoint`를 받는다. 각 점은 material/location/load-case와 K geometry solution, reference-stress solution, toughness source ID를 갖고 `Kr=K/Kmat`, `Lr=sigma_ref/sigma_norm`을 계산한다. 곡선은 이용권한 근거가 있는 사용자 공급자이고 `Lr=0`부터 마지막 절점까지만 선형 보간한다. 출력의 `declared_boundary_outcome`은 사용자 경계 비교이지 계산 상태·규격 합격·확률이 아니다. 전체 계약은 [파괴평가 설명](FRACTURE_ASSESSMENT_KO.md)에 있다.

`fracture_data.list_crack_arrest_runs(path)`와 `read_crack_arrest_series(path, specimen_id)`는 고정 C1/C2 ZIP의 시험 ID·family·파일명 온도와 원 signed time/displacement/force/cycle 채널을 읽는다. 기계 zeroing·필터·event picking과 toughness reduction은 수행하지 않는다. 이 데이터 인터페이스는 `data.crack_arrest_observations`로 추적하며 FAD 곡선·파괴저항 공급자와 자동 연결하지 않는다.

`fracture_toughness_data.read_fracture_toughness_temperature(path, *, temperature_unit_override=None, dimension_unit_override=None, apply_article_dimension_review=True, condition_group_relative_tolerance=0.03, condition_group_absolute_tolerance_m=1e-4)`는 고정 ZIP 안 workbook의 provider training/test 분할과 source sheet/row, 보고 KJc·항복강도·탄소·형상·W/B/a·재료명을 읽는다. Workbook의 `K` 온도 표기와 음수 값 충돌은 연계 논문의 °C 선언을 별도 근거로 보존하고 기본 `temperature_K`를 만든다. 파생 workbook을 읽는 호출자는 온도에 `degC` 또는 `K`를 명시할 수 있으며 비양의 절대온도는 거절한다. W·B·a의 원 단위 표기는 `None`으로 보존하지만 논문이 치수와 T 크기를 mm로 정의하고 workbook의 전 두께 척도가 일치하므로 기본 `dimension_unit_basis="article_mm"`와 SI 치수를 만든다. 파생 자료에서 이 검토가 적용되지 않으면 `apply_article_dimension_review=False`로 SI 치수를 비우거나 `dimension_unit_override="mm"`/`"m"`로 검토값을 기록한다. `condition_group_id`는 재료명·시편형식·검토된 W/B를 상대 3%·절대 0.1 mm 허용오차로 묶은 source-specific 누설 방지 층이다. 두 허용오차는 호출자가 바꿀 수 있고, 치수 단위가 미해결이면 그룹을 만들지 않는다. 그룹은 `physical_specimen_id`가 아니며 `condition_group_physical_independence_reviewed=False`를 유지한다. `article_source_group_id`, `article_source_group_status`, `article_source_material_label`은 연계 논문 표의 재료/참고문헌 그룹만 나타낸다. 상태는 `article_table_exact`, `probable_name_variant`, `material_condition_mismatch`, `unresolved`를 구분한다. `article_reference_bibliographic_id`와 `article_reference_identity_status`는 확인된 DOI 또는 서지만 나타내며, `article_reference_publication_license_id`와 `article_reference_observation_rights_status`를 분리한다. 이 필드들은 `underlying_literature_id`나 `physical_specimen_id`를 대신하지 않는다. 이 인터페이스는 `data.fracture_toughness_observations`로 추적한다. Reported KJc를 유효 파괴저항·서비스 하한·FAD 검증값으로 자동 승격하지 않는다.

이 모델의 압력은 내압−외압의 차압이다. 기준 값과 출력 필드 이름에 `pressure_difference`를 붙이고 `values.pressure_basis="internal_minus_external"`를 반환한다. 절대 내압 이력과의 여유를 구하려면 외부 절대압을 검토해 차압으로 변환해야 한다. 편집 시험 자료의 압력 기준은 주 표에서 확인되지 않으므로 미확정으로 남긴다.

`structural.profile_capacity`의 사용자 공급자는 `models.local_capacity.ReferenceCapacity`와 `BulgingFactorTable`이다. 기준 압력·그 의미·형상/재료 상태 ID·출처 및 이용근거와, 길이별 M≥1의 비감소 표·적용 범위를 제공한다. 프로파일 자체의 ID와 정확히 일치해야 하며 스냅샷 해시를 반환한다. 두 공급자는 독립 JSON Schema로도 내보낸다. 실제 허용표·flow-stress 규칙·규격 보정계수는 패키지에 포함하지 않는다.

입력은 축 위치·잔존 두께·기준 벽 두께·최대 지원 깊이비와 적용성 선언이다. 출력의 `declared_model_pressure_difference_capacity_Pa`는 `reference_pressure_difference_Pa`와 공급자 기반의 정적 계산 용량이다. `critical_window`에는 시작/끝 인덱스·위치·길이·손실 면적·감소비·M이 남고, `scanned_nodal_windows`는 검사한 절점 구간 수다. 시작/끝 인덱스는 0부터 센다. 실제 반복 압력 이력·성장·불확실성과 연결하는 한계상태는 별도 구축한다. 합성 실행 예제는 `examples/profile_capacity.py`다.

`burst_data.read_burst_compilation(path)`는 원 ZIP 또는 workbook을 읽고 주 표만 반환한다. mm·MPa를 SI로 바꾸며 EXP/FEM, 컴파일러 보완 물성·추정 폭, 문헌 연결·원 행·인위적 case ID와 품질 표식을 보존한다. EXP의 공급자 보고 시험 파열압과 FEM의 공급자 보고 해석 실패압은 `pressure_result_role`로 분리한다. `reference_mapping_status`는 편집본 범례에 직접 연결된 문헌과 미해결 편집 표식을 구분하며, 원 관측의 권리와 물리 시편 ID는 별도 미검토 상태로 유지한다. `field_provenance`는 필드별 기원을 나타내며 미표시 셀도 `source_reported_unverified`다. `numeric_geometry_material_valid`는 수치·기본 조건 검사이며 실험 자격이 아니다. `reported_diameter_m`의 내경/외경이나 압력 기준을 추정하지 않는다. `reported_input_digest`와 반복 표식은 동일 관측 여부를 조사하기 위한 값이며 자동 시편 병합·독립성 판정에 쓰지 않는다. 원 수식 셀은 실행하지 않고 보존한다.

`structural.burst_pressure_comparison`은 `BurstPressureComparison`을 받아 사용자 공급 예측과
검토된 시험 파열압의 비를 계산한다. 행은 관측·물리 시편·source group·partition·재료·형상·
하중·압력 기준·원본 해시·예측 입력 digest를 보존한다. 이용 권한과 시험 끝점·형상·압력
기준을 검토하지 않았거나 예측을 평가 전에 고정하지 않은 경우 `needs_data`다. 중복 시편과
calibration에서 평가 분할로 넘어가는 source group은 거절한다. 공개 스키마는
`docs/schemas/BurstPressureComparison.json`과 `BurstPressureComparisonRow.json`, 예제는
`examples/burst_prediction_comparison.py`, 전체 경계는 `BURST_VALIDATION_KO.md`에 있다.

## 크리프 수명

`temperature_basis`는 `nominal_specified`(지정 온도)와 `measured_representative`(검토된 대표 측정 온도)를 구분한다. 적합·모델·예측의 기준이 정확히 같아야 한다. 실제 자료의 지정 온도와 센서 시계열을 자동 치환하지 않는다. 측정 온도 대표값·정상 상태 구간·허용 변동에 대한 검토는 공급자가 담당한다.

크리프의 보정·예측은 `creep.lognormal_life_fit`, `creep.conditional_life`다. `models.creep.CreepLifeModel`은 별도 JSON Schema로 내보내며 원 관측 대신 계수·조건 지원 범위·자료 해시·근거를 보존한다. `stress_only`에서는 활성화에너지가 `None`, `arrhenius_stress`에서는 양의 J/mol 값이다. `initial_stress_Pa`의 의미는 `stress_basis`에 따라 정하중의 초기 명목 응력 또는 일정 진응력이며 두 관례를 섞지 않는다.

Python의 엄격한 계약과 JSON 배열은 다음처럼 연결한다. 전체 실행 예제는 `examples/creep_life.py`다.

`python
import json
from matintegrity.models.creep import CreepLifeModel
model = CreepLifeModel.model_validate_json(json.dumps(fitted.values["model"]))
# evaluate("creep.conditional_life", {"model": model, ...}, context)
`

적합에는 고유한 실제 시편 ID, 응력·K·초·우측 검열 여부, 공통 기구·재료 상태와 독립성 선언, 근거를 공급한다. 원 모델의 `current_age_s`·`horizon_s`와 같은 시계의 조건부 확률만 `probability_event`로 바꾼다. 이 확률의 산포는 모집단 로그 수명 산포이며 모수 불확실성을 포함하지 않는다. `maximum_time_extrapolation_factor`는 관측된 최장 파단 시각의 명시적 배수 한도다. 중앙 수명이 한도를 넘으면 `median_life_s=None`과 표식을 반환하며, 기간 자체가 한도를 넘으면 `out_of_scope`다.

`creep_data.read_cmsx6_creep(workbook)`은 종료 메타데이터에서 파단·시간 한도·미확정을 구분한다. `read_cmsx6_trace(path, duplicate_policy="preserve")`는 중복 시각을 보존하고 표식과 개수를 기록한다. 기본 정책은 중복 거절이며 시간 미분용 가상 시각을 만들지 않는다. 시계열 표본을 독립 수명 시편으로 세지 않는다.

## 수소 분배와 관측

모델과 각 트랩의 `material_condition_id`, `reference_lattice_id`는 정확히 같아야 한다. 격자간 site density는 금속 원자의 몰밀도와 다를 수 있으므로 site 정의·다중성을 근거에 기록한다. 로그 확산계수는 ln[D/(1 m²/s)]의 관례다.

수소의 국소 분배는 `transport.hydrogen_trap_equilibrium`으로 실행한다. `HydrogenTrapPopulation`은 트랩 ID·site density(mol/m³)·격자 대비 양의 결합에너지(J/mol)·허용 점유율·근거를 갖고 독립 Schema로 내보낸다. 전체 수소 농도는 **수소 원자의 mol/m³**이며 H₂ 분자의 mol/m³와 다르다. 격자 site density, 격자 확산계수, 온도, 격자 허용 점유율과 여러 트랩을 공급한다. 빠른 국소 평형·독립 단일 점유·고정 트랩/균일 온도 선언이 없으면 자료 부족이다.

출력은 격자·트랩별 농도와 점유율, 질량 잔차, 국소 미분 저장계수와 확산계수다. `local_differential_diffusivity_m2_s`는 해당 농도에서의 값이며 전체 시험을 대표하는 일정 D가 아니다. 분율이 수치 끝점으로 반올림되면 `site_fraction_resolution_limited`를 표시한다. 미분 확산계수의 표현 범위를 벗어나면 `None`·로그값과 범위 밖 상태를 보존한다. 기체 압력→격자 농도, 포획 속도, 파괴 한계·고장확률은 별도 공급자가 필요하다. `examples/hydrogen_partition.py`는 외부 관측을 포함하지 않는 합성 예제다.

`hydrogen_data.read_he_austenite(directory)`는 고정 CSV·성분표·명시적 연결표를 읽는다. `reported_composition_mass_fraction`과 `linked_composition_mass_fraction`을 각각 보존하고 `composition_link_consistent`로 대조한다. 미보고 성분을 0으로 채우거나 계산된 성분 지표를 측정으로 승격하지 않는다. 소성 파단변형률의 미확정 단위는 `property_unit="unresolved"`와 누락 SI 값으로 남긴다. 보고 압력은 total/partial·absolute/gauge 기준이 미확정이므로 직접 CoolProp 상태로 넘기지 않는다. `compiler_verified`는 편집자가 선언한 검토 상태이며 이 패키지가 원 문헌을 재추출했다는 뜻이 아니다.

`hydrogen_exports`의 `read_permeation_export`, `read_permeation_summary`, `read_tds_export`, `read_tds_exposure_summary`는 `TabularExportProvenance`와 내보낸 CSV를 받는다. 이 계약은 원 archive/member·도구·workbook/worksheet·CSV 해시·검토 상태를 보존한다. 로더는 파일 해시를 대조하고 미선언 단위를 자동 변환하지 않는다. 두 TDS 로더의 `ppm_basis` 기본값은 `unresolved`이며, 출처별 검토가 끝난 파일에만 `hydrogen_mass_per_sample_mass`를 명시한다. 원 채널·음수·순서·미확정 의미와 attrs를 보존하며 원 적분·요약을 독립 관측으로 승격하지 않는다. 사용 예제와 수치 검토 경계는 [수소 수치 내보내기](HYDROGEN_EXPORTS_KO.md)를 따른다.

`permeation_flux_observations`는 `HydrogenPermeationSignalCalibration`에 고정된 CSV 해시,
원/처리 전류 채널, 계측/이동 시계, 원점, 막 면적, 부호, 전자 화학양론과 전류효율이 모두
검토된 경우에만 전기화학 등가 수소 원자 플럭스로 변환한다. 음수 플럭스를 자르지 않고 부호
있는 사다리꼴 누적량을 반환한다. 이 변환은 표면 격자농도나 수송계수를 추정하지 않는다.

`tds_molar_observations`는 `HydrogenTdsSignalCalibration`의 정확한 series ID/label, 수소 질량
ppm 기준과 검출기 검토가 있을 때 한 TDS series를 수소 원자 mol/(kg-sample·s)와
source-derived mol/kg-sample로 변환한다. 검토된 시편 질량을 추가하면 전체 mol/s와 mol도 함께
생성한다. 시편 질량이 보고되지 않았으면 질량 정규화 결과까지만 반환하며 임의 질량을 만들지 않는다.
원 온도 순서와 음수율을 유지하고 원 적분을 독립 관측으로 만들지 않는다.
CSV에 시계가 없으므로 온도나 명목 가열률에서 elapsed time을 생성하지 않는다. 두 공개 계약은
각각 `docs/schemas/HydrogenPermeationSignalCalibration.json`과
`docs/schemas/HydrogenTdsSignalCalibration.json`이다.

유한 평판과 속도식 트랩은 `transport.hydrogen_slab_kinetic`이다. `HydrogenSlab`에 초기 셀 평균·공통 경과시간 knot·균일 온도/D·트랩 속도 이력·두 표면 경계를 넣는다. 유한 원통은 `transport.hydrogen_finite_cylinder_kinetic`이며 `HydrogenFiniteCylinder`가 반경–축 셀 평균과 곡면·두 끝단 경계를 따로 받는다. `LatticeBoundary`는 고정 농도·무유량, 외부 근거의 평형농도와 전달계수를 받는 선형 전달, 또는 흡수·방출 한계 flux 이력을 받는 축약 해리 표면반응을 지원하며 모두 반 셀 확산저항을 보존한다. `HydrogenKineticTrap.rate_model`은 결합에너지 기반 방출/포획 비 또는 독립 capture/release 이력을 선택하며, 후자는 정렬된 `release_frequency_per_s`와 명시적 검토를 요구한다. 결과에는 모드와 이력 digest가 남는다. 표면 flux 또는 flow는 각각 안쪽으로 양수이며 재고와 누적 교환의 질량 잔차를 반환한다. 비축대칭 형상·응력·트랩 생성·다중 표면상태와 파괴는 추가 공급자/모델이 필요하다. 지원 선언과 오차 의미, 독립 재현 절차는 [수소 수송 설명](HYDROGEN_TRANSPORT_KO.md)에 있다.

`transport.hydrogen_trap_thermal_rates`는 `HydrogenTrapThermalRates` 입력의 공통 시간·온도 이력에 대해 capture/release 각각의 Arrhenius 또는 전이상태 빈도를 계산한다. 반환된 `independent_rate_contract_fields`에 matching `HydrogenTrapPopulation`과 셀별 `initial_occupancy`를 더하면 기존 `HydrogenKineticTrap` JSON으로 바로 합성할 수 있다. 적용 온도·에너지 기준·파라미터 근거와 검토가 필수이며, 결과의 rate-ratio energy는 결합에너지 측정값이 아니다.

`transport.hydrogen_dissociative_surface_rates`는 `HydrogenDissociativeSurfaceRates`의 검토된 H₂ fugacity 또는 명시적으로 검토한 ideal-gas partial-pressure 근사, 온도 이력과 두 `ThermallyActivatedSurfaceFlux`를 빈/단위 격자점유 한계 flux 이력으로 바꾼다. `boundary_contract_fields`에 surface ID를 붙이면 `LatticeBoundary`로 합성할 수 있다. 재료·격자·표면·기체종·gas-state provider·시계·reference fugacity·두 rate ID와 지원 범위를 유지한다. zero-net occupancy는 축약 경계의 진단일 뿐 bulk 용해도나 흡착 피복률이 아니다.

`transport.hydrogen_thermal_rate_fit`은 별도로 검토된 양의 속도–온도 관측에서 하나의 Arrhenius 또는 고정 transmission coefficient 전이상태 속도식을 적합한다. `HydrogenThermalRateFit`은 관측·source group·trap/material/lattice/energy-reference ID, calibration/holdout 분할과 선택적인 log-frequency 표준불확실성을 보존한다. 적합에는 calibration 행만 사용하고 holdout은 calibration 온도 범위 안에서만 예측한다. 결과는 `ThermallyActivatedFrequency` JSON, 모수 공분산·표준불확실성, 로그잔차와 분할별 RMSE를 제공한다. 공분산은 선택한 단일 경로식과 입력 불확실성/잔차에 조건부이며 TDS/투과 역문제, model-form 또는 source-group 불확실성을 포함하지 않는다.

`transport.hydrogen_detector_observation`은 검토된 표면의 signed outward 수소 원자 mol/s를 이상적인 전기화학 전류 또는 시편 질량 기준 TDS ppm/s로 정방향 변환한다. `adapters.hydrogen_observation_inputs_from_transport_result`는 평판의 inward flux에 검토된 실제 면적을 곱하거나 유한 원통의 이미 적분된 surface flow 부호를 바꿔 이 계약을 만든다. 결과·표면·시계·재료·시편·보정 ID와 원 결과 digest를 유지한다. 음수를 자르거나 신호에서 경계조건을 역산하지 않으며 detector lag, 배관/진공계 체적, pumping, 재결합, 흡착, 잡음과 모수 불확실성은 포함하지 않는다.

`transport.hydrogen_slab_flow_multiplier_fit`은 `HydrogenSlabFlowMultiplierFit` 계약으로 검토된 평판 표면의 signed outward 수소 원자 mol/s에 대해 한 개의 양수 이력 배수만 적합한다. 대상은 격자 확산계수, 한 트랩의 capture/release 빈도 또는 한 표면의 선형 전달·흡수·방출 capacity 이력 중 하나다. 관측·series·시편·검출기 보정·표면·경계·source group·partition·정확한 elapsed-time ID와 실제 면적을 보존한다. calibration 행만 `scipy.optimize.least_squares` 목적함수에 들어가고 holdout은 적합 뒤에만 평가한다. 결과는 적합 배수, 국소 log-multiplier Jacobian과 조건부 불확실성, calibration/holdout 잔차, 경계 활성 상태, 재사용 가능한 fitted `HydrogenSlab` 계약과 digest를 반환한다. 이는 한 모수 profile이며 다중 모수 식별성, 고정 입력·모델형식·검출기·시계·source-group 불확실성 또는 원 TDS/투과 신호 역산을 제공하지 않는다.

### HyMatBase 4130X 수소 피로 자료

`hydrogen_fatigue_data.read_hymatbase_hydrogen_fatigue`는 caller-pinned SHA-256,
source group, 물리 material-condition ID와 별도 record의 압력·온도를 요구한다. 네
`HydrogenFatigueSeries`와 SI 단위의 `HydrogenFatigueGrowthPoint`를 반환하며 원 workbook 행과 열,
R, 주파수, method·orientation token 및 미확정 시편 identity를 보존한다. record 4.5 MPa와 workbook
45 MPa가 다르므로 명시적 `acknowledge_pressure_conflict` 없이는 중지한다. 수식은 실행하지 않고
data 열의 수식과 한쪽만 누락된 쌍을 거절한다.

`audit_hymatbase_hydrogen_fatigue`는 점별 표 대신 curve 수·점 수·범위·수식 수·충돌 상태를
`HydrogenFatigueWorkbookAudit`으로 반환한다. 공개 schema 세 개와 적용 제한은
[4130X 수소 피로 자료 문서](HYDROGEN_FATIGUE_DATA_KO.md)를 따른다. 이 인터페이스는 서비스용
균열성장곡선, 수명 또는 확률 계산기가 아니다.

전역 민감도는 `sensitivity.run_sobol` 또는 `create_sobol_design` → `evaluate_sobol_design` → `analyze_sobol_evaluations`로 실행한다. `SobolRequest`·`SobolDesign`·`SobolInputBatch`·`SobolEvaluations`·`SobolReport`가 독립 입력·단위·모델 버전·점 ID·계산 실패와 수치 품질을 보존한다. `registry_sensitivity_evaluator`는 선언한 스칼라 입력/출력을 기존 계산기에 연결한다. `computed`와 `precision_status`를 각각 확인하며 분산 지수를 기간 PoF로 변환하지 않는다. [수치 기준·외부 작업 계약·재현 절차](SENSITIVITY_KO.md)를 따른다.

분극 곡선은 `models.electrochemistry.PolarizationCurve`와 `PolarizedElectrode`로 교환하고 `corrosion.mixed_potential`을 등록 API로 실행한다. 곡선의 부호·기준 전극·전해질·온도·점 ID·근거와 실제 면적을 보존한다. 다중 평형점·평탄 구간·누락/미검토 조건은 대표 전위를 비우며 모든 후보와 상태를 남긴다. [분극 API·실제 자료 검토·수학 검증](ELECTROCHEMISTRY_KO.md)을 확인한다. 순전류를 전체 금속 용출·기간 PoF로 변환하지 않는다.

## CoolProp 상태

`python
from matintegrity.thermo import ThermoRequest, fluid_state
state = fluid_state(ThermoRequest(
    fluid="Hydrogen", pressure_Pa=1e6, temperature_K=300.0,
))
`

압력은 절대압, 온도는 K다. 포화 상태는 온도 대신 `vapor_quality`를 지정한다. CoolProp 버전과 리비전을 결과에 남긴다. 유체 밀도·엔탈피·엔트로피와 고체 재료의 강도·부식 저항은 서로 다른 공급자다.

`cavitation_inputs_from_coolprop`은 온도에서 포화액의 증기압과 밀도를 구해
`degradation.cavitation_margin` 입력을 만든다. backend·유체·온도·CoolProp 판본과 계산 물성의
digest를 보존하며 국부 절대 정압과 특성속도 정의는 호출자가 제공한다. 자세한 계산식과 범위는
[캐비테이션 문서](CAVITATION_KO.md)를 따른다.

`cavitation_history_inputs_from_coolprop`은 정렬된 온도·국부 절대압·특성속도 표본마다 포화액
상태를 만들고 표본별/전체 digest를 보존한다. 반환값은 `degradation.cavitation_history`에
직접 넣을 수 있다. 계산기는 선형 교차, 비양수 여유 지속시간과 clipped pressure-deficit
적분을 반환하며 무효 표본을 자동 제거하지 않는다.

`adapters.cavitation_history_inputs_from_operating_history`는 검토된 `OperatingHistory`를 같은
계산 입력으로 바꾼다. 자산·부위·시계·기원·원본 digest를 보존하며, 압력 채널이 해당 위치의
절대 정압이라는 명시적 검토와 같은 길이의 양의 특성속도 이력을 요구한다. 공개 출력 계약은
`docs/schemas/CavitationHistory.json`이다.

## 외부 모듈

`adapters.LocalTensorHistory`는 구조·FE·노치해석 공급자의 한 국부점 응력·변형률 이력을
`matintegrity.local_tensor_history.v1`로 교환한다. 자산·재료상태·하중 case, solver/provider와
revision, mesh·field location·공간 평균, 오른손 직교 좌표계, stress/strain measure, shear
convention, 표본 시계·유효성 및 두 content digest를 보존한다. 공개 JSON Schema는
`docs/schemas/LocalTensorHistory.json`이다.

`critical_plane_inputs_from_local_tensor_history`는 caller-qualified Cauchy stress와 infinitesimal
strain만 임계면 입력으로 바꾼다. engineering shear가 명시되면 비대각 strain만 절반으로
변환한다. context identity 불일치, 미검토장, 결측 표본과 지원하지 않는 measure는 거절한다.
변환 record digest와 load/analysis/mesh/location/frame ID는 계산 입력에 남는다. 합성 실행 예는
`examples/local_tensor_history.py`, 외부 저장소 구현 요구는
`extension_requests/FE_LOCAL_TENSOR_KO.md`를 따른다. 이 계약은 FE 해의 품질·mesh 수렴·노치
해석 적합성 또는 실험 타당성을 인증하지 않는다.

`docs/schemas/`에는 독립 개발용 입력·결과·사건·재료·검사·물성·워크플로 등의 JSON Schema를 내보낸다. 원본은 해당 Pydantic 클래스이며 `scripts/export_schemas.py`로 다시 생성한다. schema의 버전 상수와 필수 필드를 보존하고, 변경 시 수신 측 계약 검사와 함께 갱신한다.

`workflow.pressure_fatigue`는 `OperatingHistory`를 막 응력·사이클·수명·손상으로 변환하는 첫 실행 경로다. `examples/process_history.py`로 실행한다. 모든 품질 마스크가 유효해야 하며 형상·온도·응력 범위·응력비가 명시된 보정 범위 안에 있어야 한다. 이력과 평가 자산·부위도 같아야 한다. 손상은 확률이 아니며 열응력·잔류응력·노즐·수소의 효과는 추가 모델이 필요하다.

| API | 의미 |
|---|---|
| `OperatingHistory` | 공통 시계, 절대압, 온도, 품질 마스크, 측정·예측 구분을 갖춘 이력 |
| `CavitationHistory` | 국부 정압·속도·포화물성·상태 digest를 같은 시계에 보존한 캐비테이션 선별 이력 |
| `LocalTensorHistory` | solver·mesh·부위·좌표계·measure·shear convention·표본 품질을 보존한 국부 tensor 이력 |
| `EventProbability` | 명시된 물리 범위·고장 모드·기간·생존 조건의 확률 |
| `equivalent_stationary_hazard` | 사용자가 일정 위험률 근사를 선언한 경우의 등가 위험률 |
| `explanation_payload` | 계산과 근거를 설명 서비스에 넘기는 중립 입력 |
| `monitoring_record` | 모델·출처·시간·단위를 보존한 계산 특징 |

확률을 PRISM의 기존 문헌 빈도 객체로 자동 위장하지 않는다. 등가 최초고장 위험률과 반복사건 연간 빈도는 의미가 다르다. 필요한 상대 프로젝트 확장은 `docs/extension_requests/`를 따른다. 어댑터는 외부 서비스 호출이나 설비 제어를 자동 수행하지 않는다.

`reliability.joint_event_probability`는 같은 물리 범위·기간·조건부 기준의 완전한 이진 공동
상태표를 받는다. 상태확률과 사용자 공급 상위사건 진리표로 기간 조건부 상위사건 확률,
주변확률, 쌍별 동시확률·공분산·phi 및 독립 비교값을 계산한다. 빠진 상태를 재정규화하거나
공통원인 확률을 추정하지 않는다. 공개 계약은 `docs/schemas/JointEventDistribution.json`,
상세 범위는 [공동 사건 문서](CORRELATED_EVENTS_KO.md)를 따른다.

Registry 밖의 callback API `reliability_sampling.run_subset_simulation(limit_state, request)`는
결정론적 scalar limit state `g(z) <= 0`을 seeded pCN subset simulation으로 평가한다. latent 입력,
매핑 검토, callback revision/digest, 사건 범위와 conditioning을 함께 고정한다. 조건부 체인 상관 때문에
신뢰구간이나 오차막대를 만들지 않으며, 정체된 임계값이나 단계 상한에서는 `needs_data`를 반환한다.
자세한 실행 경계는 [희귀사건 시뮬레이션 문서](RELIABILITY_SUBSET_SIMULATION_KO.md)를 따른다.

`reliability.continuous_time_markov_chain`은 검토된 유한상태 초당 생성행렬을 행렬지수로
전파한다. 원 생성행렬의 종료 상태 점유확률·기대 점유시간·기대 전이횟수와, 상위사건 상태를
흡수시킨 복사본의 기간 최초진입확률을 분리한다. `probability_event`에는 최초진입확률만 전달할
수 있다. 공개 계약은 `docs/schemas/ContinuousTimeMarkovChain.json`, 상세 범위는
[동적 신뢰성 문서](DYNAMIC_RELIABILITY_KO.md)를 따른다.

`reliability.piecewise_continuous_time_markov_chain`은 연속된 구간별 생성행렬을 입력 순서대로
전파한다. 구간 ID·경계·전이율 근거·공급자 리비전·원본 해시를 보존하고 공백·중첩·암묵 정렬을
거절한다. 경계별 상태점유와 최초진입확률, 구간별 및 누적 점유시간·전이횟수를 반환한다.
공개 계약은 `docs/schemas/PiecewiseContinuousTimeMarkovChain.json`이다. 이 모델의
`probability_given_survival`도 원 기간·상위사건·물리범위·조건·공통원인 그룹이 모두 일치할
때만 `probability_event`로 변환한다.

`reliability.bayesian_linear_thickness_update`는 한 물리 위치의 기준시점 두께와 일정 손실률
Gaussian prior를 반복 두께 관측으로 갱신한다. `update` partition만 posterior에 들어가며
`holdout`은 잔차 진단에만 사용한다. 독립 측정오차를 명시하거나 update 행 순서에 맞춘 검토된
전체 공분산을 공급한다. 공개 계약은 `docs/schemas/BayesianLinearThicknessUpdate.json`과
`docs/schemas/ThicknessObservation.json`, 상세 범위는
[Bayesian 두께 갱신 문서](BAYESIAN_GROWTH_KO.md)를 따른다. 지정 시각의 요구두께 미달은
`point_in_time_state_probability`, 양의 손실률은 `posterior_parameter_probability`이며 어느
쪽도 `EventProbability`나 기간 최초고장확률로 자동 변환하지 않는다.

`reliability.linear_thickness_state_space_update`는
`LinearThicknessStateSpaceUpdate` 계약으로 시간순 반복 두께를 순차 갱신한다. 상태는 잔여두께와
부호 있는 손실률이며, 각 구간에 검토된 2×2 과정잡음 공분산률×경과시간을 더한다. update 행은
Joseph 형식 Kalman 갱신을 수행하고 holdout 행은 one-step-ahead 잔차만 계산한다. 측정오차는 현재
독립 선언만 지원한다. 분석 종료시점 posterior는 `gaussian_thickness_posterior_sample_inputs`로
공동표본 경로에 연결할 수 있다. 공개 계약은
`docs/schemas/LinearThicknessStateSpaceUpdate.json`에 있다. 과정잡음 적합, smoother, 비선형 전이,
개입·수리와 최초도달은 이 계산에 포함되지 않는다.

`reliability.gaussian_thickness_posterior_sample_design`은
`GaussianThicknessPosteriorSampleDesign` 계약으로 기준시점 두께와 부호 있는 일정 손실률의 검토된
2변량 Gaussian posterior를 받는다. 명시적 64비트 seed와 버전 고정 SplitMix64–Box–Muller–Cholesky
추출 후, 비음수 손실률과 평가시점 임계두께 생존으로 조건화한다. 고정 후보 예산에서 요청 수를
채우지 못하면 부분 표본을 내보내지 않는다. `gaussian_thickness_posterior_sample_inputs`가 계산된
`BayesianLinearThicknessUpdate` 결과를 이 입력으로 구성하며, 결과 digest 전체를 posterior source로
보존한다. `sampled_linear_thickness_first_passage_inputs`는 완성된 표본 결과를 다음 최초도달 입력으로
구성한다. 공개 계약은 `docs/schemas/GaussianThicknessPosteriorSampleDesign.json`에 있다.

`reliability.sampled_linear_thickness_first_passage`는
`SampledLinearThicknessFirstPassage`와 `LinearThicknessFirstPassageSample` 계약을 사용한다.
평가시점 생존을 조건으로 한 동일 위치의 잔여두께-비음수 손실률 공동 표본, 가중치, 후보시각과
요구두께를 받는다. 양의 손실률 표본은 선형 임계도달 시각을 계산하고 0 손실률은 유한 도달이 없는
것으로 보존한다. 누적확률은 각 후보까지 도달한 표본 가중치의 직접 합이며 입력행을 독립 주변분포로
재조합하지 않는다. 분포·표본설계 ID, 공동 표본 hash, conditioning과 다섯 검토 gate가 필요하다.
평가시점에 이미 임계 이하인 표본은 버리지 않고 전체 결과를 `needs_data`로 둔다. 출력의
`forecast_points`는 같은 context에서 `inspection.threshold_inspection_schedule`의 점추정 입력으로
직접 사용할 수 있다. 공개 계약은 `docs/schemas/SampledLinearThicknessFirstPassage.json`과
`docs/schemas/LinearThicknessFirstPassageSample.json`에 있다.

## HELPR 결과 교환

`helpr_adapter.read_helpr_life_criteria_csv`는 Sandia HELPR 2.1.0의 고정된 다섯 열
life-criteria CSV를 HELPR 런타임 없이 읽어 `HelprLifeCriteriaRecord`로 반환한다. 호출자는
HELPR 버전·40자리 commit, 분석 ID, 자산·부위·재료 상태·하중 case, 각 행의 고유 sample ID,
설정 digest, 단위 검토, 결측 의미, `a(crit)` 해석과 실행 경고 코드를 제공하고 경고 검토를
명시해야 한다. 파일 SHA-256은 로더가 계산한다. `a(crit)`와 cycle 필드는 공급자 보고값이라는
이름으로 보존하며 물리 파괴점 또는 관측 수명으로 승격하지 않는다.

명목 출력은 정확히 한 행만 허용하고 확률 출력의 행마다 명시적인 고유 sample ID를 요구한다.
빈 값·NaN은 `None`으로 유지하며 음수·무한 값과 알 수 없는 header는 거절한다. 반환값의
`endpoint_semantics`는 `model_criterion_not_observed_failure`, `probability_semantics`는
`none`이다. 즉 cycle 기준값을 관측 파단, runout, 규격 합격, 잔여수명 보증 또는 기간
고장확률로 사용할 수 없다. 상대 프로젝트의 권장 manifest와 인수 기준은
`extension_requests/HELPR_KO.md`를 따른다.
## 희귀사건 중요도 샘플링

`reliability.gaussian_mean_shift_importance_sampling`은
`GaussianMeanShiftImportanceSampling` 계약으로 외부 계산 모듈과 연결한다. 호출자는 표준정규
잠재변수 순서, 평균이동 제안표본, 고유 sample ID와 정렬된 Boolean 사건 지시값을 제공한다.
설계·난수생성기·잠재 매핑·결정론 평가자의 ID, 리비전과 설정 SHA-256 및 동일 자산·위치·시계를
함께 제공해야 한다. 레지스트리는 `probability_given_survival`을
`conditional_first_failure_in_period`로 선언하므로 다른 의미의 사건에는 이 필드를 사용할 수 없다.

계산기는 `exp(-mu dot z + ||mu||^2/2)` 우도비를 자르지 않고 적용한다. 주 출력은 비정규화
비편향 추정량이며 자기정규화 값은 진단뿐이다. 표본 표준오차·정규근사 구간·전체/사건 ESS와
최대 정규화 가중치를 함께 검사한다. 사건 0건, 표현 불가능한 극소 확률과 1을 넘은 유한표본
추정값의 처리 및 전체 제한은 `RARE_EVENT_SAMPLING_KO.md`에 있다.

## 연속 배관 ILI 자료 인터페이스

`pipeline_ili_data.iter_pipeline_ili_features`는 처리·선별된 provider XLSX를 지연 순회해
`PipelineIliFeature`를 반환한다. 호출자는 `physical_pipeline_id`, `inspection_run_id`, 실제 설비
연령이 아닌 `expected_inspection_year_token`, `expected_sha256`을 모두 제공해야 한다. 선택적인
`start_provider_row`와 `stop_provider_row`는 대용량 파일의 명시적 구간 처리에 쓴다.

`pipeline_ili_data.audit_pipeline_ili_workbook`은 XLSX XML을 직접 순회해 `PipelineIliWorkbookAudit`을
반환한다. 고정 header, 행 수, 열별 누락·최소·최대·비수치 수와 수식·회차 불일치를 기록한다.
두 API 모두 feature matching, 성장률, MFL 신호 해석, sizing bias, POD 또는 수명을 만들지 않는다.
공개 schema는 `docs/schemas/PipelineIliFeature.json`과
`docs/schemas/PipelineIliWorkbookAudit.json`, 적용 경계는
[연속 배관 ILI 자료 문서](PIPELINE_ILI_HISTORY_KO.md)를 따른다.

## 사용자 표형 균열성장곡선

`fracture.tabulated_growth_rate`는 권한 있는 사용자가 공급한 양의 `ΔK–da/dN` 점을 지원 범위
안에서만 로그–로그 선형 보간한다. `fracture.tabulated_crack_growth`는 같은 곡선, 비감소 형상계수표와
순서 있는 인장 하중 block으로 `dN=da/(da/dN)`를 적분한다. 곡선의 재료상태·환경·응력비·주파수·
source group·내용 SHA-256, 점별 계산 이용권한과 적용성 검토가 입력 계약에 포함된다. 선택적 citation,
license ID 및 rights/applicability review ID는 import부터 calculation까지 curve payload 안에서 유지된다.

명시된 열과 단위의 UTF-8 CSV를 기존 curve 계약으로 바꾸려면
`matintegrity.fcgr_curve_import.FcgrCsvImportRequest`와 `import_fcgr_csv()`를 사용한다.
메모리 바이트는 `csv_bytes`로 직접 전달하고, 로컬 파일은
`FcgrCsvImportRequest.from_file(path, ...)`로 한 번 읽어 요청에 고정할 수 있다. 파일 입력에는
선택적으로 `expected_source_sha256`를 지정해 digest 불일치를 거부한다.
ΔK 단위(`Pa*sqrt(m)`, `MPa*sqrt(m)`, `N/mm^1.5`)와 성장률 단위(`m/cycle`,
`mm/cycle`)를 호출자가 지정한다. 원본 순서가 ΔK 오름차순이어야 하며 자동 정렬·중복 병합은
하지 않는다. 각 행은 `include` 또는 `exclude`로 명시하고 제외 사유를 기록해야 한다.
ΔK, 성장률, row ID, disposition 열은 서로 달라야 하며 exclusion reason 열 이름을 지정할 수 있다.
stage 열은 원 문자열로 보존하되 자동 필터에 사용하지 않는다. 반환값은 원 CSV SHA-256,
원본 레코드 순번, 선택 행 ID, 매핑된 원 셀, 변환된 curve, citation/license ID, rights review ID 및
applicability review ID를 함께 담는다. 계산 이용 권리와 곡선 적용성 검토는 호출자가 확인해야 하며,
공개 schema는 `FcgrCsvImportRequest.json`,
`FcgrCsvImportResult.json`, `FcgrImportedRow.json`이다. 이 importer는 Strathclyde workbook
전용 reader나 자료 권리 승인을 대신하지 않는다.

`fracture.tabulated_curve_family_growth`는 한 재료상태·환경에 속한 둘 이상의 곡선에서 block별로
하나의 곡선을 선택한다. 선택 허용차와 모든 후보의 응력비·주파수 차이, 선택 curve ID를 결과에
보존한다. 후보가 없거나 최소 정규화 거리의 동률이 있으면 임의 순서로 결정하지 않는다.

`fracture.tabulated_crack_growth_uncertainty`는 `TabulatedCrackGrowth` 또는
`TabulatedCurveFamilyGrowth`를 기준 입력으로 받고, `CrackGrowthUncertaintySample` 공동 행의
성장률·형상·응력·인성 배수를 적용한다. 분포·설계·원본 digest와 표본 ID·정규화 가중치를 보존한다.
모든 행이 계산된 경우에만 가중 평균·표준편차·이산 inverse-CDF 분위수와 선언 깊이 초과질량을
반환한다. 레지스트리의 확률 의미는 `model_implied_input_uncertainty_probability`로 고정되며
`conditional_first_failure_in_period`와 호환되는 것으로 해석하지 않는다.

`fracture.tabulated_crack_growth_uncertainty_convergence`는 같은 분포 정의와 기준 성장모델을 사용하는
`CrackGrowthUncertaintyDesignLevel` 둘 이상을 받는다. 단계별 설계·source digest·관계와 모든 결과를
보존하고, nested refinement의 기존 ID·배수행 계보를 검사한다. 평균·표준편차·요청 분위수·초과질량의
인접 단계 변화를 선언 깊이 척도로 정규화해 사용자 허용값과 비교한다. `diagnostic_criteria_met`는
계산 가능한 진단 flag이며 수렴·오차상한·표본수 충분성 또는 위험확률 자격을 뜻하지 않는다.

`fracture.tabulated_crack_growth_scenario_ensemble`은 `CrackGrowthScenario`마다 완전한
`TabulatedCrackGrowth` 또는 `TabulatedCurveFamilyGrowth`를 받는다. 따라서 전역 배수로 제한하지 않고
곡선점·곡선군·형상표·하중 block·인성·수치 제어의 행내 의존성을 그대로 보존할 수 있다. 같은 물리
범위, 고유 scenario ID, 합이 1인 가중치와 source digest를 요구하고 각 결정론 입력의 canonical
SHA-256을 결과에 기록한다. 모든 시나리오가 계산된 경우에만 집계를 반환하며 확률 의미는 기존과
같이 `model_implied_input_uncertainty_probability`다.

병렬 계산은 `crack_growth_scenario_manifest(ensemble)`로 고정 manifest를 만들고 각
`CrackGrowthScenario`를 `evaluate_crack_growth_scenario_job(...)`에 전달한다. 외부 결과는
`CrackGrowthScenarioEvaluation` JSON으로 교환하고
`fracture.tabulated_crack_growth_scenario_reduction`에서 집계한다. reducer 입력은 manifest의 ID·
가중치·source/input digest, evaluator ID·revision·configuration digest 및 result digest를 보존한다.
평가 파일 순서는 자유지만 ID 집합은 정확히 일치해야 하며, 결과 순서는 manifest 기준으로 복원된다.

하중 응력비·주파수 불일치, 곡선·형상 지원범위 밖 외삽은 `out_of_scope`로 남긴다. 성장곡선 상한,
사용자 인성에 의한 최대 K, 선언 깊이는 서로 다른 종료 사유다. 입력과 전체 예제는
[표형 균열성장 문서](TABULATED_CRACK_GROWTH_KO.md), 공개 계약은
`docs/schemas/TabulatedCrackGrowth*.json`에서 확인한다.

## 다음 검사시점 선택

`inspection.threshold_inspection_schedule`은 `ThresholdInspectionSchedule`과
`InspectionForecastPoint` 계약을 사용한다. 입력 확률은 평가시점 생존을 조건으로 한 같은 사건·
물리 범위의 누적 `conditional_first_failure_in_period`여야 한다. forecast 모델 ID·revision·입력
SHA-256, 후보 ID·시각·점추정치·선택적 상한, 사용자 승인 확률기준, 최소 notice와 최대 deferral을
보존한다.

`probability_basis="estimate"`는 점추정치, `"upper_bound"`는 모든 행에 제공된 상한으로 판정한다.
계산기는 허용 창의 제공된 후보 중 기준을 만족하는 마지막 행만 고른다. 시각 사이를 보간하거나
forecast support 밖으로 외삽하지 않는다. context의 asset/location 불일치, 비증가 시각·누적확률,
상한 누락, 검토 gate 누락은 거절하거나 `needs_data`로 남긴다. 전체 예제와 상태 의미는
[검사주기 문서](INSPECTION_SCHEDULING_KO.md), JSON Schema는
`docs/schemas/ThresholdInspectionSchedule.json`에서 확인한다.

표본 기반 두께 최초도달 출력은 `forecast_points`를 그대로 이 입력의 동명 필드에 넣을 수 있다.
asset/location/time basis, 사건 정의와 conditioning은 두 계산 사이에서 같아야 한다. 상류 계산은
신뢰상한을 만들지 않으므로 이 조합은 `probability_basis="estimate"`만 지원한다.

## 검사·정비 행동 기대손실 비교

`inspection.action_expected_loss`는 `InspectionActionExpectedLossComparison`,
`InspectionActionRiskCandidate`, `RiskCostComponent` 계약을 사용한다. 같은 사건·물리 범위·기간·
생존조건에서 정확히 하나의 baseline과 완전한 intervention 후보를 비교한다. 각 후보는 행동효과
모델 ID·revision·입력 SHA-256과 외부에서 평가한 잔여 기간 최초고장확률을 보존한다.

총 기대손실은 행동비용 합계와 `잔여확률 × 조건부 고장 결과비용 합계`의 합이다. 점추정 또는 모든
후보에 있는 상한을 선택할 수 있으며, 절대 비용 동률 허용차 안의 최소값이 둘 이상이면 선택하지
않고 `needs_data`를 반환한다. 계산기는 검사효과·확률·비용·위험허용도·합격을 만들지 않는다.
전체 계약과 FTA 연계 경계는 [행동 위험비교 문서](ACTION_RISK_COMPARISON_KO.md), JSON Schema는
`docs/schemas/InspectionActionExpectedLossComparison.json`에서 확인한다.

외부 FTA·동적 신뢰성 계산은 `ActionEventProbabilityEvaluation`으로 감싼 뒤
`inspection_action_expected_loss_inputs`로 조립한다. 어댑터는 사전 선언한 행동 ID와 평가·비용의
정확한 전체 집합을 요구하고, 모든 행동의 event/asset/scope/failure mode/horizon/conditioning을
대조한다. 누락·추가·중복·미계산 행을 삭제하지 않고 전체 조립을 거절한다. 외부 결과 digest,
위험구조와 common-cause group identity는 각 후보에 보존된다.

검사 뒤 결과별 처분을 펼칠 때는 `inspection.disposition_decision_tree`를 사용한다. 결과분기는
상호배타·완전분할이어야 하고 확률합은 선언 허용오차 안에서 1이어야 한다. 각 분기에 결과확률,
처분효과 모델 identity/digest, 결과·처분 조건부 잔여 최초고장확률과 처분비용을 공급한다. 출력의
기대 행동비용과 잔여확률은 `inspection_action_candidate_from_disposition_tree_result`로 기존
행동비교 후보가 된다. 상한, POD 기반 분기확률, 순차 정책 또는 처분 최적화는 생성하지 않는다.

다기간의 고정 정책은 `inspection.multi_period_policy_evaluation`으로 평가한다. 공개 계약은
`MultiPeriodInspectionPolicyEvaluation`, `InspectionPolicyPath`, `InspectionPolicyStage`,
`PolicyStageCostComponent`다. 호출자는 완전한 경로 manifest, 경로확률, 시간순 행동과 모델 digest,
최초고장, 비용 및 현재가치계수를 공급한다. 출력은 조건부 최초고장확률과 할인 행동·고장결과·총손실의
유한 기대값이다. 전이·할인·확률을 추정하거나 여러 정책을 탐색·최적화하지 않는다.

유한 확률표에서 경로를 만들 때는 `inspection.finite_policy_path_generation`을 사용한다. 공개 계약은
`FiniteInspectionPolicyPathGeneration`과 상태·초기분포·관측·결정규칙·행동·전이·epoch 계약이다.
모든 비영 분기를 정확히 전개하고 failure에서 멈춘다. 생성 결과는
`multi_period_policy_evaluation_inputs_from_generated_paths`로 기존 평가 입력이 된다. 경로 한도 초과는
부분 결과를 반환하지 않는다.

검토된 종단 라벨에서 확률표를 추정할 때는 `inspection.finite_policy_probability_calibration`을 사용한다.
실제상태-관측 라벨과 상태-행동-다음상태 기록을 고정 calibration/holdout 분할로 받으며 동일
`sequence_id` 또는 `source_group_id`가 두 분할에 걸치면 거절한다. 출력은 완전한 관측·전이 확률표,
holdout negative log likelihood와 multiclass Brier score다. 0확률 holdout 사건은 clipping하지 않고
ID를 보존한다. `finite_policy_epoch_from_probability_calibration`은 검토된 결정규칙·행동·failure
결과계수와 결합해 기존 경로 생성기의 epoch 계약으로 변환한다. 독립성·신뢰구간·물리 truth는 만들지 않는다.

평가가 끝난 복수 정책은 `inspection.multi_period_policy_comparison`으로 비교한다. 공개 계약은
`MultiPeriodInspectionPolicyComparison`, `MultiPeriodInspectionPolicyCandidate`,
`PolicyResourceConstraint`, `PolicyResourceUsage`다. 확률·자원 hard constraint를 먼저 적용하고
통과한 유한 후보에서만 기대손실을 비교한다. `inspection_policy_candidate_from_evaluation_result`는
평가 결과 identity와 digest를 보존한다. 전역 최적성이나 상세 자원일정은 제공하지 않는다.

## LCF 벤치마크 계산 계약

`fatigue.cyclic_response_relative_error`는 `CyclicResponseRelativeError`와
`CyclicResponseSeries`를 사용한다. 시험별 cycle과 관측/예측 평균값·진폭, 두 양수 정규화 값 및
합이 1인 가중치를 받는다. 시험 안에서 먼저 평균하고 시험들을 같은 비중으로 평균한다.

`fatigue.life_rmsle`는 `FatigueLifeRmsle`의 고유 case ID와 양의 관측/예측 cycle을 비교한다.
중도절단·runout은 수치 대체하지 않고 별도 계약으로 처리한다. `fatigue.dynamic_modulus_drop_endpoint`는
`DynamicModulusDropEndpoint`의 엄격한 cycle 순서, 압축 분지 동적탄성률, 선언 기준값·저하율·교차
정책·관측창 상태를 사용한다. 전체 예제와 경계는 [LCF 벤치마크 문서](FABEST_LCF_BENCHMARK_KO.md),
스키마는 `docs/schemas/CyclicResponseRelativeError.json`, `FatigueLifeRmsle.json`,
`DynamicModulusDropEndpoint.json`에 있다.

`fabest_lcf_data.audit_fabest_lcf_archive`는 원 ZIP의 MD5/SHA-256, member 경로·CRC·크기·암호화,
experiment/case/control mode와 네 table 역할을 반환한다. `iter_fabest_lcf_numeric_rows`는 감사에서
얻은 정확한 member와 header를 받아 provider row 번호와 유한 수치 tuple을 순서대로 yield한다.
`preserve_empty_fields=True`일 때 tuple의 공란은 `None`으로 유지하며 값 대체·보간은 하지 않는다.
전체 25,213,349행을 메모리에 올리지 않으며 자동 단위 추정·header alias 병합·시편 ID 생성은 하지
않는다. 공개 스키마는 `FabestLcfArchiveAudit`, `FabestLcfExperimentAudit`,
`FabestLcfTableAudit`, `FabestLcfMemberAudit`이다.

## 압력–온도 운전경계

`structural.pressure_temperature_envelope`는 `PressureTemperatureEnvelope`,
`PressureTemperatureEnvelopeKnot`, `PressureTemperatureOperatingPoint` 계약을 사용한다. 사용자가
적용성을 검토하고 SHA-256으로 고정한 양의 허용압력–절대온도 knot 사이에서만 선형 보간한다.
각 운전점의 허용압력·압력여유·이용률과 공급 경계 내부 여부를 반환하며, 범위 밖 온도는 외삽하지
않는다. 설계규격 표·하중조합·안전계수·수용판정은 포함하지 않는다. 상세 경계와 연동 방법은
[압력–온도 운전경계 문서](PRESSURE_TEMPERATURE_ENVELOPE_KO.md)를 따른다.
## 외부 수소 수송 결과

`matintegrity.hydrogen_exchange.HydrogenTransportHistory`는 외부 1차원 수소 수송 결과를 공급자 리비전과 complete-payload digest에 결속한다. 생성자는 `hydrogen_transport_history(**payload)`이며 공개 JSON Schema는 `docs/schemas/HydrogenTransportHistory.json`이다. 배열 구조와 해석 경계는 `HYDROGEN_TRANSPORT_EXCHANGE_KO.md`를 따른다.

## 외부 인적신뢰도 추정값

`matintegrity.human_reliability_exchange.HumanReliabilityEstimateRecord`는 외부 HRA의 event와 estimate 전체를 작업·절차·문맥 및 공급자 revision에 결속한다. `human_reliability_estimate_record(...)`로 만들며 공개 Schema는 `docs/schemas/HumanReliabilityEstimateRecord.json`이다. 확률은 정의된 한 작업 기회당 실패확률이며 `EventProbability`로 직접 변환되지 않는다. 자세한 의미는 `HUMAN_RELIABILITY_EXCHANGE_KO.md`를 따른다.

## 외부 배관 평가 결과

`matintegrity.pipeline_exchange.PipelineAssessmentRecord`는 외부 `pipeline_integrity.result.v1` 전체를 공급자 source-tree SHA-256, package version, 모델·단위·asset/scenario/clock/origin 및 qualification에 결속한다. `pipeline_assessment_record(...)`로 만들며 공개 Schema는 `docs/schemas/PipelineAssessmentRecord.json`이다. 계산 성공을 설계 또는 현장 승인으로 바꾸지 않는다. 자세한 경계는 `PIPELINE_EXCHANGE_KO.md`를 따른다.

## 용접 수소 bakeout

`welding.hydrogen_bakeout_slab`은 `HydrogenBakeoutSlab`의 time/temperature/effective-diffusivity 이력과 양면 방출 두께를 받는다. `∫Ddt/thickness²`에 대한 유한 평판 급수로 잔류·방출 분율, 평균 atom-molar 농도와 면적당 누적 방출량을 반환한다. 급수 tail 상한과 항 수를 함께 반환하며 미검토 경계·이력은 `needs_data`로 보류한다. 공개 Schema는 `docs/schemas/HydrogenBakeoutSlab.json`, 상세 범위는 `HYDROGEN_BAKEOUT_KO.md`를 따른다.

## 겨울철 열수지와 제작 증거

`fabrication.winterization_inventory`는 구간별 상수 `Tamb`, `UA`, heat tracing 전력과 유효 `cp`를 받는다. CoolProp 조합이 필요하면 `thermo.winterization_inputs_from_coolprop(...)`로 입력 dict를 만들고 일반 registry API에 전달한다. 이 조합은 property state와 공급자 판본을 digest에 고정한다.

`fabrication.surface_cleanliness_assessment`, `fabrication.chemical_cleaning_envelope`, `fabrication.storage_preservation_history`, `fabrication.coating_qualification_assessment`, `fabrication.transport_erection_history`, `inspection.test_water_quality_summary`, `welding.consumable_compatibility`는 관측과 caller-owned 한계를 분리한 제작 workflow다. 중첩 입력 계약은 `MODEL_REFERENCE_KO.md`, 의미와 제한은 `FABRICATION_EVIDENCE_WORKFLOWS_KO.md` 및 `WINTERIZATION_KO.md`를 따른다.

## 재료 compatibility와 제조품질

`fatigue.morrow_strain_life`는 caller 계수와 검토된 인장 양(+) 평균응력으로 탄성 Basquin 항을 조정한다. `fatigue.swt_strain_life`는 caller가 제공한 양의 최대응력과 변형률 진폭의 SWT 매개변수로 cycle 수를 푼다. 둘 다 완전역전 기본 모델 `fatigue.strain_life`와 분리되며 상세 조건은 [MORROW_STRAIN_LIFE_KO.md](MORROW_STRAIN_LIFE_KO.md)에 있다.

`materials.polymer_compatibility_envelope_match`, `materials.composite_compatibility_assessment`, `materials.casting_forging_quality_record`, `degradation.under_insulation_exposure_history`는 재료·제조·노출 identity와 caller-owned envelope를 보존한다. 입력 필드와 실행 예는 `MODEL_REFERENCE_KO.md`, 경계와 후속 연동은 `MATERIAL_COMPATIBILITY_WORKFLOWS_KO.md`를 따른다.

`materials.phase_microstructure_assessment`, `degradation.sour_environment_applicability`, `degradation.chloride_scc_applicability`, `degradation.microbial_campaign_summary`는 환경·시험 evidence의 identity, units, detection limit와 qualification support를 보존한다. 계산 경계는 `ENVIRONMENTAL_DEGRADATION_EVIDENCE_KO.md`를 따른다.

`phase_map_data.summarize_phase_label_map(labels, roi_mask, missing_mask, metadata)`는 digest가 고정된 2D 정수 phase map에서 caller-reviewed ROI의 상별 pixel count·실제 면적·분율을 집계한다. Missing과 미분류 pixel은 따로 보존한다. 선택적 `phase_label_map_to_observations(...)` 연결은 사용자가 모든 상의 expanded uncertainty와 basis를 공급하고 scale/ROI/label mapping review가 완료된 경우에만 기존 `PhaseFractionObservation`을 만든다. Pixel count에서 uncertainty를 추정하지 않는다. 상세 계약과 경계는 `PHASE_LABEL_MAP_KO.md`를 따른다.

Oxford `.cpr/.crc` 원자료는 선택 의존성 설치 후 `oxford_ebsd.read_oxford_ebsd_phase_labels(archive_path, member_basename, expected_archive_sha256=...)`로 digest-pinned raw phase labels와 `OxfordEbsdPhaseLabelReadRecord`를 읽는다. 이 ingest는 label 의미·ROI·pixel scale 단위를 유추하지 않고, 결과 ndarray는 read-only다. 실제 자료 적용 예와 제한은 `PHASE_LABEL_MAP_KO.md`를 따른다.

`phase_map_topology.summarize_phase_map_topology(labels, roi_mask, missing_mask, metadata, connectivity=4)`는 reviewed 범주 raster의 연결 component와 4-neighbor 공유 격자 edge 기반 sampled interface 길이를 요약한다. SciPy가 필요한 선택 `[science]` 기능이며 결정립 분할이나 물성/위험도 평가가 아니다. 반환 계약과 기하학적 제한은 `PHASE_MAP_TOPOLOGY_KO.md`에 설명한다.


Bonded-layer, ammonia/alkaline SCC와 preheat 계산기도 동일한 registry API로 실행한다. 정확한 입력 ID는 각각 `materials.bonded_layer_integrity_assessment`, `degradation.ammonia_scc_applicability`, `degradation.alkaline_scc_applicability`, `welding.preheat_procedure_envelope`다.

고온 열화 applicability 모델 ID는 `degradation.sulfidation_exposure_applicability`, `degradation.carburization_applicability`, `degradation.nitriding_applicability`, `degradation.metallurgical_aging_exposure`다. Chemical driving-force basis와 단위를 그대로 보존하며 자동 변환하지 않는다. 황화물 envelope에 연결한 각 qualification record는 재료·조성 상태·황종·quantity 정의와 단위/basis, 온도·절대압력·유동·침적·노출시간이 실제 envelope 정의에 포함되는지 별도 진단한다. 출력은 record별 source group, canonical SHA-256, 원 Evidence, 보고 관측을 검사값과 함께 유지한다. record가 지원영역 밖이면 해당 envelope를 선택하지 않는다. 이는 사용자가 제공한 시험계획의 내부 일관성 확인이며 일반화된 부식률이나 표준 적합성 계산은 아니다.

외부 보정 rate 적분 모델은 `degradation.acid_dissolution_history`, `degradation.erosion_corrosion_loss`, `degradation.under_deposit_calibrated_loss`다. Selective-leaching evidence는 `degradation.selective_leaching_applicability`를 사용한다. Rate provider identity·support·digest가 맞지 않으면 손실을 계산하지 않는다.

## 방화 보호와 용접 qualification 기록

`fabrication.fire_protection_boundary_history`는 검토된 incident-flux/transfer-fraction 이력을 적분하고 `values["thermal_boundary_contract"]`에 `thermal.transient_conduction_1d`의 `ThermalBoundary` 입력 조각을 내보낸다. 반환된 `elapsed_time_s`를 열해석 시계와 동일하게 사용하고 경계 방향 검토 플래그를 임의로 바꾸지 않는다.

`welding.local_heat_treatment`, `welding.residual_stress_evidence`, `welding.wps_qualification_envelope`는 각각 공간 온도이력, 좌표계가 명시된 응력과 불확도, production variable와 qualification specimen 증거를 caller-owned support에 비교한다. 국부 열처리 유지시간은 센서 샘플 사이 선형 온도 보간 추정이며, 미기록 peak나 절차 합격을 보증하지 않는다. 잔류응력은 중심값과 expanded-uncertainty 전체 구간이 provider stress support에 드는지 확인하며, 범위 밖 및 partition별 record ID를 최상위 결과에 제공한다. 비교행은 원 Evidence·source group·provider revision/state·record/dataset digest를 보존한다. 별도 record/support lineage arrays는 unmatched·ambiguous 행과 모든 calibration/holdout/application 행의 계보를 유지한다. Application 입력 수와 비교 완료 수는 별도 집계하며 unmatched/ambiguous 행은 coverage 실패와 unsafe ID 목록에 반영한다. 매칭된 좌표축 이름·순서, 차원, frame definition digest와 공간 support를 검사하고 mismatch 사유를 비교행에 명시한다. provider/frame 후보가 있어도 stress component 정의가 다르면 `record_match_issue_reasons`에 mismatch를 남긴다. 복수 support에 매칭되는 행은 임의 선택하지 않고 ambiguous 이유와 ID로 반환한다. 세 partition은 source group을 공유할 수 없고 holdout metric과 허용상한의 unit token이 다르면 provider qualification 계약을 거부한다. 세부 필드는 `MODEL_REFERENCE_KO.md`, 적용 경계는 `FABRICATION_EVIDENCE_WORKFLOWS_KO.md`를 따른다.

`fabrication.thermal_spray_condition`, `welding.duplex_phase_balance`, `welding.production_weld_test_evidence`, `welding.repair_welding_history`는 각각 thermal-spray qualification/production 관측, region별 phase fraction, production specimen/NDE 시험, repair stage 순서를 엄격한 identity·unit·digest로 받는다. 모두 일반 `ModelRegistry.run`/`run_json`으로 실행하며 예제 입력은 `examples/model_inputs.json`, 중첩 계약은 `MODEL_REFERENCE_KO.md`에서 확인한다.

## 고급 검사 증거

`inspection.acoustic_emission_campaign`, `inspection.replica_metallography_evidence`, `inspection.fracture_toughness_test_evidence`, `inspection.cryogenic_leak_test_evidence`는 모두 일반 registry API로 실행한다. Feature/metric·unit·partition·uncertainty·detection limit·provider digest를 자동 변환하지 않고 보존한다. 검사자료를 위험성 사건으로 바꾸기 전에 [검사 증거 워크플로](INSPECTION_EVIDENCE_WORKFLOWS_KO.md)의 연동 조건을 확인한다.

## 취성·환경 열화 applicability

`materials.brittle_applicability_evidence`, `degradation.high_temperature_hydrogen_applicability`, `degradation.liquid_metal_embrittlement_applicability`, `degradation.crevice_species_inventory_history`는 일반 registry API와 strict JSON 경로를 사용한다. 시험·qualification support와 provider digest를 입력에 포함하고 결과의 `computed`, `needs_data`, `out_of_scope`를 그대로 보존한다. Crevice interval rate는 기존 상수 입력 또는 명시적으로 검토한 시작/끝 표본의 선형 변화로 줄 수 있고, 온도·gap의 시작/끝 조건도 별도 선형 경로 검토와 함께 지정할 수 있다. 공유 knot에서 불연속 조건은 명시적으로 검토하고, 결과는 knot의 좌/우 상태를 둘 다 보존한다. 구간 온도·gap 평균은 endpoint 산술평균으로 제공되며 provider rate law를 계산하는 데 쓰이지 않는다. 입력 condition history와 provider record identity는 계산 lineage digest에 포함되어 결과에 반환된다. 각 attempted rate row는 대응 condition row digest, provider state/record identity 및 rate interval input digest를 교차 참조하며 rate diagnostics 목록도 별도 digest로 고정한다. 계산 완료 결과는 cumulative species source, 재고 수지 잔차, 경계 상태 digest ledger도 반환한다. interval 처리 실패 시에는 마지막 공통 완료 knot까지의 inventory prefix, 완료 구간 수와 실패 interval ID를 반환한다. 정확한 중첩 필드는 `MODEL_REFERENCE_KO.md`, 해석 한계와 위험성 연동 전제는 [환경 열화 증거 워크플로](ENVIRONMENTAL_DEGRADATION_EVIDENCE_KO.md)를 따른다.

## 압력시험과 용접 균열 applicability

`inspection.pressure_test_eligibility`는 caller-owned method·medium·pressure/temperature/stored-energy support와 요구사항 기록을 비교한다. `welding.solidification_cracking_applicability`, `welding.reheat_cracking_applicability`, `welding.lamellar_tearing_applicability`는 용접·소재 조건과 partitioned test evidence를 caller qualification envelope에 비교한다. 공통 입력 예제는 `examples/model_inputs.json`, 중첩 schema는 `MODEL_REFERENCE_KO.md`, 해석 경계는 [용접 균열 applicability](WELDING_CRACKING_APPLICABILITY_KO.md)를 따른다.

`fabrication.joint_efficiency_declaration`은 사용자 라이선스 규칙을 revision/content digest와 computational-use authorization에 결속한다. `welding.temper_bead_qualification`, `welding.hot_tap_applicability`, `welding.brazing_bonding_qualification`도 같은 registry API를 사용한다. 상세 경계는 [제작 증거 워크플로](FABRICATION_EVIDENCE_WORKFLOWS_KO.md)와 [용접 균열 applicability](WELDING_CRACKING_APPLICABILITY_KO.md)를 따른다.

`fabrication.forming_qualification`, `fabrication.tube_bundle_integrity_evidence`, `fabrication.cryogenic_valve_evidence`, `welding.peening_treatment_evidence`는 동일한 strict JSON registry API를 사용한다. Nested interval·observation·qualification 필드는 `MODEL_REFERENCE_KO.md`, 해석 경계는 제작 및 용접 워크플로 문서를 따른다.

`fabrication.heat_exchanger_geometry_evidence`, `structural.external_pressure_provider_evidence`, `structural.nozzle_local_stress_provider_evidence`, `structural.finite_element_result_exchange`는 외부 형상·solver 결과를 digest-bound metadata로 교환한다. 배열·메시·좌표 payload는 별도 저장하고 계약에는 shape/order/content digest를 전달한다. 상세 경계는 [구조 provider 교환](STRUCTURAL_PROVIDER_EXCHANGE_KO.md)을 따른다.

## 최신 provider evidence API

다음 모델은 `default_registry()` 또는 공통 `evaluate` 경로에서 strict JSON/Pydantic 계약으로 실행한다.

- `fabrication.gasket_joint_evidence`: 직접 preload 통계와 seating·relaxation evidence 교환
- `degradation.hydrogen_fatigue_provider_evidence`: absolute partial pressure/fugacity basis가 고정된 외부 피로 결과 교환
- `degradation.hydrogen_cracking_provider_evidence`: K/J/CTOD endpoint를 보존하는 toughness·driving result 교환
- `structural.pitting_ffs_provider_evidence`: 공식 형상·검사·하중 identity와 외부 FFS 결과 교환
- `structural.creep_fatigue_interaction_provider_evidence`: 분리된 creep/fatigue quantity와 exact interaction basis 교환

각 입력 예제는 `examples/model_inputs.json`에 있고, 공개 계약은 `MODEL_REFERENCE_KO.md`와 `docs/schemas/`에서 확인한다. 이 경로들은 규격식, 합격, 성장, 수명 또는 FTA 확률을 생성하지 않는다.

## 최신 심화 계산 API

`degradation.atmospheric_multi_year_loss_history`, `degradation.nonisothermal_parabolic_oxidation`, `reliability.binary_event_pair_calibration`, `fabrication.insulation_condensation_exposure`는 일반 registry API로 실행한다. 각각 자격화된 다년 손실 전이, 비등온 `k(T)` 적분, 이진 사건쌍 calibration/holdout, 단열 외표면 결로 가능시간을 계산한다. Strict 입력 예제는 `examples/model_inputs.json`에 있다.

습공기 이슬점 입력은 `thermo.insulation_condensation_inputs_from_coolprop(...)`로 만들 수 있다. Dry-bulb 온도 K, 상대습도 fraction, 절대압 Pa와 interval surface temperature를 넘기며 adapter는 CoolProp 판본·리비전과 상태 digest를 보존한다. 반환 dict는 `InsulationCondensationExposure` 또는 registry JSON 경로로 검증한다.

`materials.cyclic_ramberg_osgood_fit`, `inspection.signal_response_pod_calibration`, `reliability.ctmc_generator_calibration`도 일반 registry API를 사용한다. 각 모델은 calibration/holdout partition을 내부에서 강제하고 holdout을 계수 적합에 사용하지 않는다. 자세한 통계·단위·지원범위 경계는 [보정 심화 문서](CALIBRATION_DEEPENING_KO.md)를 따른다.

결로 결과를 CUI 노출로 연결할 때는 `adapters.under_insulation_inputs_from_condensation_result`에 완전한 `AssessmentResult`, interval별 insulation-condition mapping과 `DeclaredUnderInsulationExposure`를 전달한다. Adapter는 열역학적 결로 가능성을 실제 습윤으로 승격하지 않는다.



`corrosion.material_rate_contrast`는 호출자가 공급한 두 양의 부식속도의 차이와 비율을 계산하며 재료·조건·출처 식별자와 조건 서명 digest를 결과에 보존한다. 비교 입력은 SI `m/s`이며, 부식률 예측이나 조건 일치 검토를 대신하지 않는다. 출처 데이터 사용 예제와 한계는 [재료별 부식속도 비교](MATERIAL_CORROSION_RATE_CONTRAST_KO.md)를 참고한다.

`corrosion.rate_joint_scenario`는 시편 수준 `CorrosionRateSampleSummary`와 caller-owned 완전 시나리오 속도·가중치를 분리해 연결한다. 선형 벽 손실에서 시나리오별 잔여두께·요구두께 도달시간·초과 질량을 계산하며 가중치 의미를 보존하고 이를 자동으로 사건확률화하지 않는다. 입력 예제와 사용 범위는 [부식률 공동 시나리오 평가](CORROSION_RATE_JOINT_SCENARIO_KO.md)를 따른다.
다른 모듈에서는 `integration.corrosion_rate_joint_scenario` 인터페이스 메타데이터로 입력 계약을 확인하고 `default_registry().input_type("corrosion.rate_joint_scenario")`에서 직접 대상 타입을 얻을 수 있다. helper는 `corrosion_rate_joint_scenario`이며 registry 실행은 명시적 `RunContext`를 받는다.


`matintegrity.ct110_data.read_ct110_weld_corrosion_dataset()`는 설치된 CC BY CT110 용접부 부식속도 fixture를 출처 메타데이터와 함께 검증해 읽는다. 반환된 `dataset.contrast_input(comparison_id)`는 레지스트리 모델 `corrosion.material_rate_contrast`에 바로 전달 가능한 typed input이다. 일반 API 계약은 호출자가 가진 다른 재료·시험 자료에도 적용할 수 있다.

`matintegrity.aquasoldb_data.iter_aquasoldb_co2_solubility(path)`는 정확히 고정된 AquaSolDB v2.1 ZIP에서 CO₂ 수용성 행을 typed record로 스트리밍한다. 파일 digest와 CSV 계약을 검사하지만 값에서 Henry 상수·fugacity·부식률을 유도하지 않는다. 컴파일러 attribution과 원 논문 별도 인용·권리 검토 상태를 반환 record에 보존한다. 원 ZIP은 공개 패키지에 포함하지 않는다. [자료 범위와 aggregate audit](WET_CO2_DATA_KO.md)를 참고한다.

같은 모듈의 `select_aquasoldb_co2_records(records, AquaSolDBCo2SolubilityQuery(...))`는 온도·압력 범위, 압력 기준, 염 매질, source ID, 상태와 표식 기준을 명시해 행을 고른다. 기본은 측정값·무표식·온도압력 보유 행이며, 제한 수를 넘으면 자르지 않고 오류를 낸다. `compare_aquasoldb_to_fixed_fugacity_model(AquaSolDBFixedFugacityComparisonInput(...))`는 선택된 단일 측정값과 독립적으로 제공한 Henry record 및 fugacity의 농도를 비교한다. CO₂ partial-pressure 기준, 온도·용매 조성 일치, Henry convention, 원 문헌 권리·인용과 입력 품질을 사용자가 검토해야 한다. 용해도 mol/kg-water를 mol/L-solution로 바꾸는 물 질량농도와 합성 expanded uncertainty도 사용자가 제공한다. 이 함수는 Henry 계수 적합·보정이나 부식률 계산을 하지 않는다.


## 사용자 크리프–피로 상호작용 곡선

`creep_fatigue_interaction.evaluate_creep_fatigue_interaction(point, envelope)`는 재료 상태·손상 정의·온도 범위가 같은 사용자 곡선에서 fatigue limit을 선형 보간한다. 반환값의 margin과 utilization은 선언 곡선에 대한 수치 비교다. 곡선과 point의 canonical digest를 보존한다. 입력 곡선 밖은 `out_of_scope`, 검토 누락은 `needs_data`다. Zero fatigue limit에서는 utilization을 `None`으로 두고 margin과 범위 내 여부를 반환한다.


`strain_life_campaign.evaluate_strain_life_campaign(request)`는 fully reversed/Morrow/SWT 블록별 수명과 cycle-count/life 비율을 계산한다. 호출자가 선형 누적을 승인해야 총합을 만들며, 양의 cycle 블록 하나라도 적용범위 밖이면 총합을 보류한다. 순서효과·크리프 상호작용·고장확률은 별도 모델 입력이 필요하다.


`creep_history.integrate_creep_history(request)`는 연속된 구간별 Norton 이차 크리프 변형률을 적분한다. 각 구간은 고정 응력·온도와 parameter support/digest를 제공한다. 별도 검토와 모든 구간의 rupture time/provider digest가 있을 때만 선형 시간분율을 추가한다. 두 산출량은 크리프–피로 상호작용으로 자동 합산하지 않는다.


`creep_fatigue_campaign.evaluate_creep_fatigue_campaign(request)`는 크리프 이력·변형률 수명 블록·사용자 상호작용 곡선을 연결한다. 재료 상태와 손상 정의가 같아야 하며 크리프 변형률을 damage fraction으로 대체하지 않는다. rupture-time fraction 또는 fatigue cycle fraction이 없으면 상호작용을 보류하고 구성 모델 결과를 반환한다.


`thermal_expansion.integrate_tangent_expansion(table, start_K, end_K)`는 명시적으로 d(log L)/dT로 정의된 접선 계수의 선형 표를 적분한다. `expm1`로 공학적 길이 변화를 계산하고 table support 밖은 보류한다. `differential_thermal_expansion`은 두 결과와 자유 열변형 차이를 반환한다. 구속응력 계산에는 별도 강성·형상 모델이 필요하다.


`subset_replicates.run_subset_replicates(callback, request)`는 distinct seed의 subset 계산을 반복하고 모두 완료된 경우에만 평균·반복 간 표준편차·평균의 표준오차를 반환한다. 실패한 run을 제외한 선택적 평균은 만들지 않는다. 신뢰구간이나 편향·수렴 보증은 제공하지 않는다.


`fad_envelope.evaluate_fad_envelope`는 provider FAD 좌표와 caller curve의 여유를 비교한다. `assembly_calculations`는 regular tube layout ligament/void 및 bore area, identified tube wall-loss/plugging inventory, 두 spring의 joint load partition과 thermal preload를 계산한다. Contact loss에서는 선형 계산을 적용범위 밖으로 반환한다.


`insulation_surface.solve_insulation_surface`는 단일 원통 보온층 전도와 외부 대류·복사의 표면 에너지수지를 풀어 표면온도·부호 있는 열유량·잔차를 반환한다. 일정 물성과 caller 대류계수, 절대온도 및 steady applicability를 요구한다.


`calibrated_damage_history.integrate_calibrated_damage`는 microbial/cavitation의 보정된 local rate와 지원조건 검토로 구간 손실을 적분한다. `critical_plane_life.evaluate_critical_plane_swt_life`는 지정한 면의 최대 법선응력·법선 변형률 진폭을 caller-calibrated SWT life solver에 연결한다. 원 plane result digest를 유지한다.


`restricted_transport.solve_restricted_transport(request, reaction)`는 species×cell 농도장의 finite-volume Fick diffusion과 사용자 volumetric reaction callback을 BDF로 적분한다. 입구 고정농도·끝단 no-flux를 명시하고 음수 결과는 보류한다. 이 diffusion-only component는 migration·전하 closure·부식 kinetics를 대신하지 않는다.


`fire_thermal_response.evaluate_fire_thermal_response`는 caller net absorbed fire flux history를 multilayer transient heat solver에 연결한다. Left-face net prescribed flux와 clock alignment를 명시하고 반대 face 및 내부 재료는 전달된 thermal model에서 유지한다. 외부 냉각·재복사는 caller net boundary에 포함돼야 한다.


Restricted transport의 optional migration은 species charge, mouth+cell prescribed potential과 온도를 함께 요구한다. Scharfetter–Gummel flux로 diffusion/migration을 결합하고 potential closure는 별도 공급자로 유지한다. 이 선택은 electroneutrality 또는 Poisson equation을 자동 해결하지 않는다.


Restricted transport는 optional Poisson closure를 지원한다. Permittivity, species charges, temperature와 명시적 mouth potential을 받아 매 RHS에서 농도 전하와 fixed charge의 전위를 풀고 SG flux에 반영한다. 입구 Dirichlet·끝단 zero electric gradient 경계를 사용한다. 이는 electroneutrality approximation과 다르며 electrode double-layer/표면전하·activities 모델은 별도 입력이 필요하다.


`electrode_kinetics.electrode_reaction_flux`는 caller-calibrated Butler–Volmer 반응의 signed current와 species stoichiometric flux를 계산한다. Restricted transport의 `tip_surface_flux(time, concentrations, solution_potential)` callback은 용액으로 들어가는 flux를 반환하고 surface provider/digest/review를 요구한다. 반응계수·equilibrium potential·CO2 chemistry는 사용자가 제공해야 한다.


`reaction_network.mass_action_callback(network)`는 explicit forward/reverse rate constants와 integer stoichiometry를 species×cell source callback으로 만든다. Homogeneous charge conservation과 concentration-based constant unit token을 확인한다. Activities·element balance·속도상수 보정은 별도 입력이 필요하다. Callback은 음수·비유한 농도와 유효하지 않은 시각을 거부한다. `provider_id`, `provider_revision`, `network_id`, species order 및 configuration digest를 속성으로 노출해 조합기·계산 결과가 callback 출처를 보존할 수 있다. Callback configuration digest를 transport reaction configuration에 연결해야 한다.


`electrochemical_transport.solve_electrochemical_transport`는 reaction-network와 surface-reaction digest 및 species/charge 순서를 확인한 후 수송–전위–반응을 함께 적분한다. 명시적 metal potential 또는 reviewed zero-current boundary를 사용한다. 선택적 `CompetitiveSolidEquilibriumTransport` 인수는 각 transport output knot마다 caller-declared 경쟁 중성 고체상 Davies 또는 SIT 평형을 순차 적용한다. 결과의 `phase_transport_lineage`는 phase/transport request와 activity 설정 digest 및 phase scope를 downstream caller가 추적하도록 요약한다. 이는 phase/transport/electrode 동시 연성이나 침전 속도 법칙이 아니다. 사용법과 제한은 [전기화학 수송](ELECTROCHEMICAL_TRANSPORT_KO.md) 및 [경쟁 고체상 수송](COMPETITIVE_SOLID_EQUILIBRIUM_TRANSPORT_KO.md)을 따른다.


`electrode_kinetics.solve_electrode_mixed_potential`는 공통 calibrated potential support 안에서 sum signed current=0을 푼다. 모든 전류가 0이면 potential을 식별하지 않는다. Electrochemical transport의 free-corrosion review 선택은 이 zero-current boundary를 사용한다. Exchange currents/equilibrium potentials가 농도에 따라 변하는 모델은 아직 별도 kinetics provider가 필요하다.


Electrochemical transport의 `concentration_laws`는 explicit calibration support 안에서 exchange-current power law와 equilibrium-potential log-ratio shift를 적용한다. 계수는 caller가 제공하며 Nernst/activity law를 추정하지 않는다. 농도 support 밖은 보류하며 concentration-law 구성도 surface digest에 포함한다.


`sequence_crack_growth.evaluate_sequence_crack_growth`는 whole-cycle ordered loads, caller opening-K ratio와 calibrated plastic-zone memory retardation을 적용한다. Increment budget·growth calibration support를 벗어나면 보류하고 block별 zone tip을 기록한다. Terminal crossing은 partial-cycle life를 추정하지 않고 따로 표시한다.


`metal_dissolution.integrate_partial_metal_dissolution`는 식별된 partial anodic current history만 적분해 charge·용출 mol·mass·uniform recession을 반환한다. Net electrode current는 이 입력으로 대체할 수 없다. Electron count·efficiency·molar mass·density와 surface reaction identity를 요구한다.


Transport 결과는 output clock의 solution-potential field를 반환한다. Electrochemical composition은 동일 시각/농도/전위에서 surface reaction별 signed partial current와 net current를 재평가해 `surface_history`로 제공한다. 금속 용출 반응을 명시적으로 선택한 후에만 Faraday mapping에 사용할 수 있다.


`dissolution_adapter.coupled_result_metal_loss(result, selection)`는 완료된 연성 결과에서 dissolution-only로 검토된 하나의 반응을 골라 Faraday history와 loss를 반환한다. 음의 current/누락 row는 거절하며 net current를 사용하지 않는다. 출력 clock 적분해상도와 uniform recession을 별도로 검토해야 한다.


Mass-action network의 optional `elemental_composition`은 전 종의 원소 개수를 명시해 각 반응의 원소 보존도 검사한다. Transport는 callback이 제공하는 configuration digest를 요청값과 대조하고, coupled surface/transport 온도를 일치시킨다.


`critical_plane_life.evaluate_critical_plane_fs_life`는 FS factor를 caller-calibrated engineering shear strain-life 관계의 두 항에 맞춰 수명을 푼다. Shear modulus, shear fatigue strength/ductility coefficients와 음의 지수·cycle support를 요구하며 tensor shear와 engineering shear를 자동 변환하지 않는다.


Restricted transport는 concentration state와 함께 mouth/tip inward molar flux 및 homogeneous reaction source를 적분한다. 결과의 species inventory balance residual은 초기 inventory와 누적 source를 대조한 수치 잔차다. 이는 output sample trapezoid가 아니라 동일 BDF state의 누적량이며 물리 검증을 의미하지 않는다.


`carbonate_reaction_network.build_carbonate_reaction_network`는 CO2 hydration/탄산 dissociation/중탄산 dissociation/물 dissociation 네 반응을 explicit-water species network로 만든다. Forward/reverse concentration constants를 모두 caller가 제공한다. Water activity=1의 pseudo-first-order 상수를 explicit-water bimolecular 상수로 그대로 넣으면 안 된다. 함수는 상수 변환이나 solvent concentration을 추정하지 않는다.


`carbonate_transport_adapter.carbonate_transport_boundary`는 completed fixed-fugacity carbonate 결과의 mol/L를 mol/m3로 변환하고 caller hydration fraction으로 CO2*를 CO2(aq)/H2CO3로 나눈다. 물 농도·partition digest를 요구한다. 누락된 counterion이나 전체 용액 electroneutrality를 자동 생성하지 않는다.


`electrolyte_extension.extend_electrolyte_network`는 explicit metal-ion/supporting-electrolyte species와 reaction을 base carbonate network에 추가한다. 기존 species 순서를 보존하고 charge/element conservation을 재검토하며 boundary net charge를 보고한다. Counterion이나 neutralizing concentration은 자동 생성하지 않는다.


`co2_corrosion_campaign.evaluate_co2_corrosion_campaign`는 carbonate boundary·electrochemical transport·selected dissolution mapping을 하나로 실행한다. Mouth carbonate species/농도·온도와 dissolution reaction/electron count/생성 species를 대조한다. Fixed geometry와 caller-calibrated chemistry에 대한 계산이며 precipitation·moving surface는 포함하지 않는다.

`chemistry.caller_scale_coverage_kinetics`는 caller 정의 scale attachment/detachment law의 area-average coverage를 계산한다. 선택적으로 두 속도상수 각각의 활성화에너지를 주면 Arrhenius temperature scaling을 target/reference와 모든 선언된 구간 온도가 caller-declared support 안일 때 적용한다. 각 interval에 상수 온도를 지정하고 profile review를 통과하면 구간마다 rate를 재평가하며 interval 사이 온도 보간은 하지 않는다. 파라미터·온도·법칙 적용성 review와 finite-range gate가 필요하다. [속도·가정과 경계](SCALE_COVERAGE_KINETICS_KO.md)를 참고한다.

`chemistry.caller_surface_scale_kinetics`는 caller가 제공한 포화비 끝점의 선형 구간 경로도 지원한다. `linearly_varying_saturation_reviewed=True`가 필요하며 `max(Ω−1,0)^n`와 `max(1−Ω,0)^n` 노출을 임계점 기준 해석 적분한다. 침전·용해 계수는 각각 기준온도에서 선택적으로 Arrhenius scaling할 수 있고, 두 활성화에너지와 온도 support 및 적용성 검토가 필요하다. 결과에는 유효 계수와 포화비 끝점이 기록된다. 포화화학·보호효과는 계산하지 않는다. [두께 이력의 가정과 범위](CALLER_SURFACE_SCALE_KINETICS_KO.md)를 참고한다.


Butler–Volmer 결과와 coupled surface history는 gross anodic/cathodic current를 reaction net current와 구분해 반환한다. Dissolution selection의 `current_component`는 dissolution-only net 또는 gross anodic을 명시한다. Gross removal은 redeposition을 빼지 않으므로 net dimensional recession과 같다고 해석하지 않는다.


Faraday mapping은 `metal_moles_per_reaction_extent`를 명시하고 reaction electron count와 함께 금속 용출 mol을 계산한다. CO2 campaign은 surface metal production coefficient와 이 값의 일치를 확인한다. Coupled surface 반응의 ionic-charge production은 anodic electron count와 같아야 한다.


Subset replicate 결과는 log-domain 평균/표준오차와 상대 표준오차를 추가해 underflow된 probability의 분산 진단을 보존한다. Caller relative-error target 만족 여부는 diagnostic이며 estimator bias·수렴 보증이 아니다. 동일 반복값으로 관측 분산이 0이어도 정확성을 증명하지 않는다.


`electrochemical_transport.assemble_electrochemical_transport`는 선택한 network/surface 구성에서 species·charge order와 configuration digest를 생성해 transport request에 결속한다. Caller가 같은 필드를 상충되게 주면 거절하며 geometry·농도·diffusivity·potential/review flag는 추정하지 않는다. 결과는 network/surface digest, potential reference와 current/concentration unit basis를 보존한다.

`welding.rosenthal_3d_point_source_temperature`는 caller가 검토한 일정 물성 반무한체 가정 아래 이동 점열원의 3D 준정상 온도장을 계산한다. 선택한 `time_s` 및 `threshold_temperatures_K`를 지정하면 caller 제공 이동좌표 표본 사이의 온도 통과 시각도 반환한다. 이 선형 보간 결과는 자격 냉각시간이나 t8/5가 아니다. 가정과 한계는 `docs/ROSENTHAL_WELDING_FIELD_KO.md`에 기록했다.

`welding.rosenthal_cooling_interval`은 앞 모델의 time-resolved fixed-point 요청과 기존 `welding.cooling_interval`을 연결한다. 일정 transverse/depth 좌표, `source_relative_x_m(t)=x_0-v(t-t_0)` 관계, caller의 냉각 branch index와 두 threshold를 요구한다. Rosenthal 요청, cooling-interval 입력, 샘플 온도이력, 선택 branch digest와 threshold crossing 결과를 따로 반환한다. 계산 기반이 이상화된 정상 이동 열원장이므로 이 API는 t8/5 자격화를 수행하지 않는다. Registry 실행 예시는 `examples/rosenthal_cooling_interval.py`를 참고한다.

`welding.cooling_interval`은 원본 온도 이력 중 `cooling_branch_start_index`와 `cooling_branch_end_index`(양 끝 포함)로 caller가 명시한 비증가 구간만 사용한다. 여러 열사이클이 섞인 이력도 원본 배열을 그대로 보존하며 선택 branch 안에서만 두 임계온도의 선형 보간 crossing을 찾는다. 결과에는 branch 범위, 각 crossing의 표본 bracket, 선택 구간 최대 표본 간격, 전체 온도 기록과 선택 branch 각각의 SHA-256 digest를 포함한다. 두 crossing 중 하나가 빠지면 `needs_data`와 누락 상태를 반환한다. 임계온도 및 절차 적합성은 caller가 정한다.

`welding.cooling_interval_batch`는 하나의 원본 온도 기록에 대해 여러 `branch_id`, branch index 범위, upper/lower threshold를 받아 모두 독립 평가한다. 중복 ID와 단조성 위반은 입력 단계에서 거절하며, incomplete crossing은 branch별 `needs_data`로 남긴다. 전체 status는 모든 branch 완료 때만 `computed`이며 전체 history와 branch별 입력 digest를 반환한다. 각 branch result에 `units`가 포함되며 같은 mapping은 top-level `branch_result_units`에도 제공된다. 선택적으로 record/sensor/location ID, `provider_file_sha256`, `Evidence` citation/license를 결속한다. 결과의 `sample_arrays_sha256`는 canonical time/temperature arrays digest이며 provider 파일 digest와 별개다. 입력 file digest는 caller assertion으로 보존할 뿐 실제 파일과 대조하지 않는다. 입력 생성 예시는 `examples/cooling_interval_batch.py`에 있다.

`welding.cooling_interval_sensor_batch`는 공통 `time_s` 배열과 센서별 `temperature_K` trace를 받아 branch마다 대상 `sensor_id`, 위치 ID, 임계온도와 포함 인덱스 범위를 지정한다. 모든 trace 길이는 공통 시간축과 정확히 맞아야 하며 서로 다른 센서 사이의 온도 보간은 하지 않는다. branch 결과에 센서·위치, trace digest, branch digest와 단위가 함께 남는다. 센서 선택이나 branch 정의는 caller 책임이며 예제는 합성 입력이다.

`scale_transport_adapter.ScaleLimitedElectrochemicalHistory`는 caller가 만든 각 인접 scale-history 시간 구간과 그 시작점의 digest-pinned `ScaleLimitedSurfaceFlux`가 적용된 `ElectrochemicalTransport` 요청을 순차 실행한다. segment 출력 시계는 0부터 해당 구간 길이까지여야 하고, scale 결과 context에는 정확한 절대 시작 시간과 원본 history digest가 있어야 한다. 선택적 Python solver callback은 구간마다 별도 mapping으로 전달한다. 첫 미계산 구간에서 중단하며 계산된 접두 구간만 반환한다. scale 상태는 구간 안에서 고정되며 electrochemical output이 scale kinetics로 되먹임되지 않는다. 예: `evaluate_scale_limited_electrochemical_history(campaign, segment_callbacks=({"activity_coefficients": callback0}, {"activity_coefficients": callback1}))`. 콜백을 쓰지 않으면 `segment_callbacks`를 생략한다.


`dissolution_adapter.coupled_net_metal_boundary_change`는 solver-integrated tip metal flux를 순 metal mol/mass/recession history로 변환한다. Metal atom-per-species와 모든 tip flux의 용출/재석출 의미·고정 면적을 명시적으로 검토한다. Signed negative는 deposition이며 clip/abs 처리하지 않는다.


Sequence growth는 predicted cycle endpoint에서 terminal depth와 fracture toughness를 함께 확인하고 더 이른 depth limit을 기록한다. 한계통과 주기는 완료주기로 계산하지 않으며 `unresolved_crossing_cycle_interval`, limiting depth와 explicit predicted endpoint를 구분한다. Partial-cycle life는 추정하지 않는다.


Transport solver의 relative/농도 absolute/누적량 absolute tolerance와 maximum step을 caller가 지정할 수 있다. `callbacks_cell_locality_reviewed`와 fixed/no potential 조건에서만 cell-local sparse Jacobian pattern을 사용한다. Poisson coupling은 nonlocal이므로 dense path의 state budget을 적용하며 통계·물리 수렴을 자동 주장하지 않는다. Solver work counts를 결과에 기록한다.


추가 계산은 registry ID `fabrication.regular_tube_layout`, `fabrication.elastic_joint_load`, `thermal.insulation_surface_balance`로도 JSON/Python 실행할 수 있다. 직접 함수 API와 동일 입력 계약·적용범위를 사용한다. Synthetic JSON 예제는 model_inputs.json에 있다.


Registry ID `structural.caller_fad_envelope`와 `fabrication.tube_bundle_inventory`는 nested FAD point/curve와 tube records를 각각 같은 공개 계약으로 받아 JSON/Python 실행을 제공한다. Synthetic input은 model_inputs.json에 있다.


Transport의 optional mouth concentration history는 output clock×species 배열이며 초기 row와 고정 initial mouth 농도가 같아야 한다. Caller interpolation review 뒤 solver time에서 구간선형 보간한다. CO2 campaign은 초기 평형 record만으로 전체 이력을 자격화하지 않고 별도 time-varying-boundary review를 요구한다.


Registry IDs `creep.secondary_history`와 `fatigue.strain_life_campaign`은 direct typed history API와 동일 계약을 JSON/Python 실행에 연결한다. 반환 status/notes와 부분 결과·총합 보류 의미를 보존한다. Synthetic JSON inputs는 model_inputs.json에 있다.


Sequence crack growth는 `final_state`를 반환하며 후속 요청의 `initial_state`로 전달할 수 있다. Depth·plastic-zone tip·누적 cycle과 law/geometry configuration digest를 보존한다. 새로운 growth.initial_depth는 state와 같아야 하며 나머지 물리/수치 설정의 상충을 거절한다. 후속 blocks는 caller가 명시적으로 선택하며 자동 재전송/반복하지 않는다.


Registry ID `fracture.sequence_zone_memory`와 `fatigue.critical_plane_fs_life`는 direct sequence/FS-life API를 JSON/Python 실행에 연결한다. Sequence checkpoint, 한계통과 구간, calibration/support status가 같은 result values로 보존된다.


Creep-fatigue campaign은 creep request의 explicit exposure_history_sha256도 common history와 같아야 한다. 누락이면 needs_data, 상충이면 거절한다. 각 creep interval 온도가 interaction curve support 안에 있는지 확인하며 representative interaction temperature 하나로 전체 history를 대신하지 않는다.


Registry ID `structural.creep_fatigue_campaign`는 같은 exposure-history digest를 갖는 creep/fatigue 및 caller interaction curve의 중첩 입력을 처리한다. 모든 constituent status와 curve comparison을 보존한다. Synthetic JSON 입력은 model_inputs.json에 있다.


## 추가 계산 연결 (2026-10-29, 실행 검증 대기)

- `integration.layered_scale_history_transport_binding`: `ScaleHistoryTransportLink`에서 선택한 exact scale-history knot의 두께를 지정 layer에 결속한다. 결과 안 calculation-input digest와 model/version/input/context로 재구성한 AssessmentResult digest가 모두 일치해야 하며, 물리 scope·substrate/solution condition 식별자와 digest도 맞아야 한다. `coverage_characteristic_thickness_m`, `coverage_shape_exponent`, `thickness_to_coverage_relation_reviewed`를 모두 지정하면 caller-reviewed `1-exp(-(thickness/characteristic_thickness)^exponent)` 식으로 피복률도 갱신한다. 이 관계는 caller 소유 모델이며 형태·접착·보호율을 추론하지 않는다.
- `integration.layered_scale_history_transport_series_binding`: `ScaleHistoryTransportSeriesLink`로 scale 이력의 모든 strictly increasing 기록 knot를 같은 transport request와 layer mapping에 결속한다. `bind_scale_history_series_to_transport`는 knot별 입력 tuple을 반환하고, `evaluate_scale_history_transport_series`는 각 knot에서 정상상태 층상 확산 상한을 독립 계산해 `AssessmentResult`와 digest를 반환한다. 각 결과는 `ScaleLimitedSurfaceFlux.scale_transport_result` 입력으로 직접 연결할 수 있다. 전체 요청·원 scale 결과·provider/source/condition lineage·각 knot 요청과 scale-state digest를 보존한다. 시간보간이나 transient solver는 수행하지 않으며, 미완료 knot가 있으면 전체 계산 series를 완료로 표시하지 않는다.

- `corrosion.explicit_co2_campaign`: carbonate/electrode/transport 및 선택 tip dissolution 입력. `examples/build_co2_campaign_input.py`는 입력만 만들며 solver를 호출하지 않는다. `build_request(include_wall_loss=True)`는 합성 wall 반응, 벽면 기하와 `WallMetalLossSelection`까지 구성한다. 임의 합성 계수는 보정 물성이 아니다.
- `corrosion.planar_slit_geometry`: 일정 aperture/단면의 planar slit에서 cell volume, broad-face reaction area, wall area density. 수송 mol/m2 원장은 axial area 기준이며 wall area 기준과 다르다.
- `corrosion.planar_slit_aperture_history`: 셀별 signed 평균 recession 배열 또는 digest 고정 `corrosion.coupled_wall_metal_loss` 결과에서 provider aperture 범위 안의 후속 cell/face 단면적, 부피와 벽면/부피 비를 만든다. 반환된 `restricted_transport_geometry`를 기존 `RestrictedTransportRequest`에 전달하고 variable-area review를 설정해 순차 재계산할 수 있다. 양면 반응과 셀 중심→면 보간은 검토가 필요하며, 연성 유동·화학 solver는 아니다. 상세 조건은 `CREVICE_APERTURE_EVOLUTION_KO.md`를 참조한다.
- `solve_crevice_geometry_transport_campaign()`은 caller가 고정한 aperture history를 `solve_restricted_transport()`의 구간별 계산에 적용한다. 각 구간은 시작 geometry를 고정하고, 경계에서 다음 geometry에 맞춰 cell volume 보존 농도 재매핑을 수행한다. recession은 입력된 독립 history이며 transport에서 되먹임하지 않는다. 시간경계는 양쪽 clock에서 정확히 일치해야 한다. 자세한 한계는 `CREVICE_GEOMETRY_TRANSPORT_CAMPAIGN_KO.md`를 참고한다.
- `fabrication.nonlinear_gasket_contact`: monotone reversible caller compression-force curve와 elastic bolt의 piecewise-linear equilibrium. 초기 압축에서 preload를 구성하고 외력 및 bolt free-length change를 반영한다. 곡선 외삽과 hysteresis 추정은 하지 않는다.
- `fatigue.multiaxial_life_campaign`: 검토된 closed tensor cycle에서 directional/chord/circle FS/SWT factor와 같은 재료의 수명계수를 연결한다. 정확히 같은 sampled maximum의 모든 plane ID를 보존한다.

이 campaign은 `criterion="shear_normal_strain_curve"`도 지원한다. caller가 선언한 `shear_strain_amplitude + normal_strain_weight * normal_strain_amplitude`를 유한 sampled plane마다 계산하고, 동일 재료상태의 caller 수명곡선에 log-log 보간한다. `build_shear_normal_strain_life_calibration()`은 곡선 계약점, Evidence, 재료상태와 review flag를 받아 검증된 보정 객체와 digest를 만든다. 곡선 밖 외삽, 미검토 계수/보간, 미검토 데이터 권리, 재료상태 불일치는 계산을 막는다. 이 일반 사용자 정의 결합 파라미터는 특정 출판 기준식의 재현이라고 주장하지 않으며, 유한 평면 최대값과 수명곡선은 별도 검증이 필요하다. 자세한 제약은 [다축 사용자 곡선 수명 API](MULTIAXIAL_CURVE_LIFE_KO.md)를 참고한다.

같은 campaign에서 별도 `KandilBrownMillerLifeCalibration`을 사용하면 maximum-pairwise-chord로 최대 전단변형률 범위를 찾고, 해당 최대 전단면의 전단 진폭과 caller 계수 × 법선변형률 범위로 KBM 매개변수를 계산한다. `build_kandil_brown_miller_life_calibration()`은 동일한 digest·Evidence·재료조건·검토 경계를 적용한다. 결과는 제공된 유한 후보 평면과 표본에 한정되며 곡선 밖 외삽·cycle counting·재료 자격판정은 하지 않는다.

`RestrictedTransportRequest.cell_widths_m`은 선택적 비균일 셀 폭이며 합계가 length_m와 일치해야 한다. 폭을 생략하면 균일 격자다. `solve_restricted_transport`의 선택 `wall_surface_flux(t, C, potential)`는 species×cell 형상의 **용액 안쪽을 양수로 하는 mol/m2/s**를 반환한다. `wall_area_per_volume_m2_m3`와 곱한 항을 체적 source로 쓰고 별도 wall 원장에 적분한다. `activity_coefficients(t, C)`는 mouth+cell 열 순서의 양수 gamma를 반환한다. drift는 전위 변화와 log(gamma) 변화를 합산한다. 활동도와 tracer diffusivity의 해석, 국부 callback sparsity, 공급자 identity/config digest는 명시적으로 검토해야 한다. Poisson closure를 쓸 때 nonlocal dense 구조를 유지한다.

`RestrictedTransportRequest`는 선택적으로 `cell_cross_section_history_m2`와 `face_cross_section_history_m2`를 요청 시각에 맞춰 받아 piecewise-linear geometry를 transport ODE와 함께 평가한다. `moving_geometry_interpolation_reviewed`와 `moving_geometry_inventory_dilution_reviewed`가 필요하고, provider/configuration/time-basis lineage를 고정해야 한다. 가변 cell volume에 따른 `-C·(dV/dt)/V` 항을 포함해 chemistry·벽 flux가 없어도 `C×V` inventory가 보존되도록 하며, BDF를 각 제공 geometry knot에서 재시작한다. 벽면 flux를 함께 계산하면 `wall_area_per_volume_history_m2_m3`도 같은 clock으로 제공해야 한다. 이 기능은 caller가 준 geometry를 transport에 적용하는 API이며, geometry를 화학이나 벽 flux에서 예측·되먹임하지 않는다. 압력·운동량 연성, moving mesh, phase mechanics, qualified corrosion law는 다루지 않는다. 상세 수식과 데이터 계약은 [caller-prescribed moving geometry transport](RESTRICTED_TRANSPORT_MOVING_GEOMETRY_KO.md)를 참고한다.

`EquilibriumReactiveTransport`도 이 digest-pinned 활동도 callback을 받을 수 있다. 분할 solver는 transport 구간과 각 초기/후속 phase projection 시점에서 같은 callback 및 config digest를 사용하고, `SingleSolidEquilibrium`의 각 셀 기록에 있는 초기 gamma가 첫 callback 결과와 일치하는지 확인한다. 이 확장은 fixed gamma 단일 고체의 셀별 operator split만 지원한다. activity model이 종분화/고체 경쟁/속도론을 자동 생성하지 않으며, 완전 연성 다상 평형을 뜻하지 않는다.

CO2/electrochemical Python API는 두 callback을 keyword로 전달한다. 공급자 함수는 JSON에 직렬화하지 않는다. CO2 campaign의 selected-tip metal loss는 측벽 총손실이 아니며 `metal_loss_scope`가 이를 명시한다. Gamma transport를 선택해도 concentration-based homogeneous reaction law의 보정 의미가 자동 변경되지 않는다.


`degradation.calibrated_damage_history`와 `thermal.fire_flux_response`도 registry에서 제공한다. 완전 합성 요청은 `examples/model_inputs.json`의 `models` 아래에 있으며, 최근 추가 요청의 계산/회귀 실행은 보류했다. 상세 조합과 callback의 단위/면적 기준은 `NEW_CALCULATION_WORKFLOWS_KO.md`에 기록했다.


추가 registry: `degradation.calibrated_condition_loss_rate`, `degradation.calibrated_condition_loss_history`, `chemistry.single_solid_precipitation_equilibrium`. Python `EquilibriumReactiveTransport`/`solve_equilibrium_reactive_transport`는 reaction/tip/wall callbacks, digest-pinned 활동도 callback, 단일 고체 operator-split 연결을 제공한다. `Co2CorrosionCampaign.phase_transport`도 선택 가능하며 base transport의 정확한 일치와 원소 조성/온도/표준상태를 유지한다. 비균일 단면의 모든 transport ledger는 explicit reference axial area 기준이다. 자세한 수식·제약·합성 입력 위치는 NEW_CALCULATION_WORKFLOWS_KO.md에 기록했다. Subset 병렬 task API는 RELIABILITY_SUBSET_SIMULATION_KO.md를 따른다. 최근 추가 경로는 실행·검증하지 않았다.


`fabrication.gasket_relaxation_curve`는 한 시험조건에서 얻은 caller-authorized preload-retention 곡선을 지정 시간 범위 안에서 선형 보간한다. 재료 법칙을 적합하지 않고 곡선 밖 시간은 거절한다. [입력·출처·해석 한계](GASKET_RELAXATION_KO.md)를 참고한다.

`fabrication.gasket_prony_history`는 caller가 자격화한 generalized Maxwell 계수와 초기 branch 응력으로, 구간별 선형 압축변형률 이력의 hold/unload/reload/recovery 응답을 계산한다. 계수 적합, 조건 간 전이, flange 변형, 누설 및 비선형 contact separation은 제공하지 않는다. [모델 식과 한계](GASKET_RELAXATION_KO.md)를 참고한다.

`fabrication.gasket_calibrated_leakage_history`는 caller flux map을 spatial contact-pressure history에 적용하고 contact area로 합산한다. `gasket_leakage_request_from_flange_contact_history()`로 정렬·digest 검증된 flange-contact AssessmentResult를 연결할 수 있다. 시간 적분은 piecewise-linear pressure path와 bilinear calibration table을 가정하며, crossed calibration-axis knots에서 잘라 각 quadratic-or-lower 구간을 Simpson rule로 적분한다. 표 밖 외삽, 다른 gasket로 calibration transfer, leak-tightness acceptance는 하지 않는다. [누설 이력 계산과 가정](GASKET_LEAKAGE_HISTORY_KO.md)을 참고한다.

`fabrication.gasket_calibrated_leakage_rate_envelope`는 절점별 독립 접촉압력·차압 구간에 대해 고정 bilinear flux calibration의 면적가중 순간 누설률 범위를 계산한다. 각 압력 직사각형을 표 knot에서 나누고 모든 subcell corner의 최솟값/최댓값을 결합한다. 결과는 확률구간이 아니며 calibration·면적 불확실성, 시간 적분, node 간 상관, 누설 수용판정은 포함하지 않는다. [계산법과 범위](GASKET_LEAKAGE_RATE_ENVELOPE_KO.md)를 참조한다.

`fatigue.critical_plane_continuous_bound`는 sampled closed tensor cycle의 FS/SWT factor를 icosphere plane net에서 평가하고, 텐서 Frobenius Lipschitz 상수와 구면 covering radius로 continuous-plane maximum의 보수적 상한을 반환한다. 상한은 공급된 시간표본에만 적용되며 임의 cycle counting이나 시간 사이 극값은 다루지 않는다. [유도와 경계](MULTIAXIAL_CONTINUOUS_BOUND_KO.md)를 따른다.

`fatigue.continuous_plane_fs_life_bound`는 해당 인증 FS factor 구간의 양 끝을 같은 조건의 caller 보정 strain-life 식에 넣어 연속면 수명 구간을 반환한다. monotone factor-to-life review와 두 endpoint 수명의 유효 cycle support 내 근이 필요하다. [구간 전달 가정](CONTINUOUS_PLANE_FS_LIFE_BOUND_KO.md)을 참고한다.

`fatigue.critical_plane_projected_rainflow`는 기록된 tensor 이력을 선택 plane의 법선/전단 scalar projection으로 변환해 채널별 rainflow cycle을 추출한다. 각 projection은 독립 계산이며 채널 간 cycle pairing, 다축 damage parameter나 수명은 만들지 않는다. [입력 projection과 한계](MULTIAXIAL_CYCLE_COUNTING_KO.md)를 따른다.

`fatigue.critical_plane_piecewise_linear_time_history`는 timed closed tensor cycle을 piecewise-linear로 재구성한다고 review하면 유한 plane set의 지정 FS/SWT factor를 그 연속 재구성에 대해 정확히 계산한다. 이는 측정 사이 물리 거동의 진실성, continuous-plane search, cycle pairing 또는 damage/life를 보증하지 않는다. [유도와 경계](MULTIAXIAL_PIECEWISE_LINEAR_TIME_KO.md)를 따른다.

`fatigue.explicit_critical_plane_cycle_pair_damage`는 `fatigue.critical_plane_projected_rainflow`의 한 평면에서 정상응력 cycle과 engineering shear-strain cycle을 연결한다. 사용자는 각 source cycle index와 할당 cycle 수를 명시하고, 두 투영의 해석, pairing/allocation 규칙, 재료 보정 및 FS factor 관례를 검토해야 한다. 계산은 source cycle count 초과할당을 거부하고 두 선택 채널의 모든 cycle count가 명시적으로 배정되지 않으면 총 손상을 보류한다. 각 배정쌍은 caller-calibrated FS shear strain-life 관계의 지원 구간 안에서 수명을 구하고 선형 Miner 가정으로 손상을 합산한다. 이 API는 pairing을 자동 추론하지 않으며 비비례 하중에 대한 재료모델 자격화, 대체 시간 재구성, FTA 사건확률이나 합격판정을 제공하지 않는다. [계약·예제·제한](MULTIAXIAL_CYCLE_PAIR_DAMAGE_KO.md)을 따른다.

`fabrication.nonlinear_bolt_gasket_contact`는 caller 제공 단조 곡선 두 개에서 bolt force-extension 및 gasket force-compression의 단일 자유도 준정적 접촉 평형을 푼다. 초기 clamp force는 초기 압축에서 gasket 곡선으로 정하고, 곡선 지원구간을 벗어나면 외삽 없이 중지한다. spatial flange bending, 이력 의존 hysteresis, relaxation, leakage 또는 acceptance를 계산하지 않는다. [곡선 계약과 평형식](NONLINEAR_BOLT_GASKET_CONTACT_KO.md)을 따른다.

`welding.dilution_with_uncertainty`는 caller source/digest가 있는 용융 base/filler/previous-layer 질량과 원소 질량분율을 선형 혼합한다. Missing assay는 0으로 보정하지 않는다. caller가 모든 입력 조성의 joint covariance와 변수 순서를 제공하면 질량 가중 Jacobian으로 혼합 조성 공분산을 전파한다. 용융질량 불확실성·segregation·용접성 판단은 포함하지 않는다. [수식·계약·한계](WELD_DILUTION_UNCERTAINTY_KO.md)를 따른다.


`solve_restricted_transport`, `solve_electrochemical_transport` 및 CO₂ campaign Python API에 시간 callback을 공급하면 signed 면속도의 시간변화·역류를 donor-cell upwind flux에 보존적으로 반영한다. 역류 시 끝단 유입농도와 연속성 검토가 필요하며, 이동 형상과 유동장 해석은 제공하지 않는다. [수식·가정·한계](CREVICE_TRANSPORT_ADVECTION_KO.md)를 참고한다.


`corrosion.coupled_wall_metal_loss`는 적분된 signed 벽면 금속종 flux를 물리 기준면적·반응 벽면적·caller 금속 물성으로 총량과 면적평균 recession으로 변환한다. 입력결과 hash와 종 순서를 보존한다. [전용 입력·범위 설명](WALL_METAL_LOSS_EXCHANGE_KO.md).








`integration.competitive_solid_equilibrium_transport`는 고정형상 restricted transport의 각 output interval 뒤에 cell별 경쟁 중성 고체상–Davies 평형을 적용하는 직접 호출형 callback interface다. `solve_competitive_solid_equilibrium_transport(request, reaction, ...)`에 reaction과 선택 surface/advection/activity callback을 명시 전달한다. phase source와 transport source ledger 및 aqueous inventory balance를 보존한다. 이는 operator split이며 완전 동시 연성, 침전 kinetics 또는 이동형상 solver가 아니다. 상세 내용은 `docs/COMPETITIVE_SOLID_EQUILIBRIUM_TRANSPORT_KO.md`, contract 예제는 `examples/competitive_solid_equilibrium_transport.py`를 참고한다.

`fabrication.flange_nonlinear_viscoelastic_contact_history`는 선택적으로 caller의 knotwise compliance matrix 이력을 입력받는다. 보간 검토, 대칭·양의 준정부호 제한 및 전이 재생 연동은 [비선형 점탄성 접촉 안내](FLANGE_NONLINEAR_VISCOELASTIC_CONTACT_KO.md)를 참조한다.

Crevice geometry transport campaign의 각 `segment_results` 항목에는 `callback_lineage`가 포함된다. callback role별 선언 provider/configuration provenance와 `global_time_offset_s` 및 callback identity digest를 보존한다.

시간변화 compliance 이력의 실행 입력 배선 예제는 `examples/flange_time_varying_compliance.py`다. 입력 knot와 compliance history 길이가 맞아야 하며 예제 배율은 synthetic 값이다.

Adaptive step rejection diagnostics are retained as a bounded ordered history with per-attempt sequence time, cycle/repetition/interval identity, attempted/next step sizes, applicable error ratios and reason. `maximum_rejection_history_records` controls the cap; exceeding it fails closed. See `STATEFUL_MULTIAXIAL_DAMAGE_KO.md`.

Each computed cycle result also carries its own rejection-history slice, the corresponding half-open index range in the sequence history, and a cycle-local canonical digest.

Provider/state/rejection/time/damage 또는 최종 identity 실패 응답도 적분이 시작된 뒤라면 설정·평가 수·accepted/rejected 통계와 저장된 rejection history digest를 함께 반환한다.

`degradation.crevice_nernst_potential_history`는 caller 제공 dimensionless species activity, 반응 quotient의 부호 있는 화학양론, knotwise 표준전위와 온도로 반쪽전지 Nernst 전위를 계산한다. `build_crevice_nernst_request_from_inventory()`는 computed crevice species inventory 결과에 caller gamma/기준농도를 적용해 연결한다. activity 및 E0 provider는 별도 Evidence·configuration·record lineage로 추적한다. 혼합전위나 부식률은 계산하지 않는다. [식, 입력 계약과 제한](CREVICE_NERNST_PROFILE_KO.md), [합성 예제](../examples/crevice_nernst_profile.py)를 참고한다.

`electrochemistry.nernst_driven_butler_volmer_history`는 digest 검증한 Nernst assessment의 평형전위를 동일 clock ID·시간 knot의 caller 표면 전위 이력과 비교해 한 reaction의 Butler–Volmer current density와 화학양론 flux를 계산한다. 기준전극 ID, 반응 ID·방향, 온도별 rate 적용성 review가 필요하다. 구간간 시간 적분, 혼합전위, 총 부식률은 포함하지 않는다. [Nernst-to-kinetics 연결 계약](NERNST_DRIVEN_BUTLER_VOLMER_KO.md)을 참고한다.


`electrochemistry.crevice_mixed_potential_history`는 digest로 고정된 여러 crevice Nernst 이력과 caller 보정 Butler–Volmer 반응을 동일한 시계·온도·기준전극의 knot별로 결합해 공통 영전류 전위를 계산한다. 각 반응 면적을 기준 면적에 환산하고 지지구간 내 bracket 이분법을 적용한다. 완전 반응집합, 면적분배, 준정상성 및 무시 가능한 용액 저항 검토가 필요하다. 시간 적분·동역학 안정성·총 금속손실은 계산하지 않는다. [상세 계약과 한계](CREVICE_MIXED_POTENTIAL_HISTORY_KO.md)를 참조한다.


`integration.crevice_electrochemical_inventory_transfer`는 혼합전위 결과의 반응별 종 flux를 기준 면적에 대해 knot 간 선형 재구성으로 정확 적분해 구간·누적 순/유입/유출 몰 전달량을 제공한다. upstream result/input/history digest, 일정 기준 면적, 구간 선형성 및 종 flux 부호 검토가 필요하다. 농도·금속손실·부식률은 도출하지 않는다. [계약과 한계](CREVICE_ELECTROCHEMICAL_INVENTORY_KO.md)를 참조한다.

`integration.electrochemical_partial_current_metal_loss`는 혼합전위 AssessmentResult의 반응별 양극·음극 partial current를 digest로 고정해 시간 적분한 뒤 caller 지정 금속 화학량론·재료 물성·실제 branch 면적에 연결한다. 양극 용출 방향, 금속 매핑 완전성, 면적평균 recession 및 선형 구간 재구성을 검토해야 한다. 총 부식률·국부손상·수명·합격판정은 제공하지 않는다. [계약과 제한](ELECTROCHEMICAL_METAL_LOSS_KO.md)을 참조한다.

`integration.external_crevice_solver_receipt`는 외부 solver의 SI pressure/face velocity를 exact digest-pinned geometry/time/mesh와 연결하고, 검토된 piecewise-linear·no-extrapolation face-velocity callback으로 기존 restricted transport에 전달한다. 실제 provider parser와 CFD consumer 실행은 별도 작업이다. [교환 계약](EXTERNAL_CREVICE_SOLVER_EXCHANGE_KO.md)을 참조한다.

`integration.caller_multiaxial_law_applicability_binding`은 기존 memoryless/stateful 다축 피로 callback을 caller law profile에 결속한다. material/calibration/provider identity, tensor convention, componentwise stress/strain 및 cycle/reconstruction support를 binding 때와 callback 매 표본마다 확인하고 결과에 profile digest를 보존한다. 법칙과 계수는 caller 제공이며 profile만으로 검증·자격 인정되지 않는다. [profile 계약](MULTIAXIAL_FATIGUE_LAW_PROFILE_KO.md)을 참조한다.

`integration.electrochemical_chemistry_boundary_audit`는 caller가 순서와 각 결과의 JSON field path를 명시한 chemistry/speciation/transport AssessmentResult chain의 digest와 시각·온도·재료·용매·활동도 표준상태를 대조한다. 모든 종은 다음 stage에 대한 mapping/변환/명시 제외와 Evidence로 추적해야 한다. 계산 chemistry나 반응 보존성 검증은 하지 않는다. [WCO2 경계 감사 계약](WCO2_CHEMISTRY_BOUNDARY_KO.md)을 참조한다.

`integration.stateful_multiaxial_cycle_block_binding`은 외부 tensor cycle block의 입력 순서·source digest·반복 수·재료 상태 endpoint를 확인하고 정확히 같은 cycle order의 stateful 피로 요청에 exchange receipt lineage를 붙인다. source material-state identity는 damage callback 내부 state와 구별한다. [cycle-block 교환 계약](MULTIAXIAL_CYCLE_BLOCK_EXCHANGE_KO.md)을 참조한다.



`integration.crevice_electrochemical_composition_history`는 검증된 electrochemical species-transfer ledger를 사용자 제공 초기 몰수와 정확히 정렬된 액상 체적 knot에 적용해 종별 몰수·몰농도 이력을 구성한다. 전체 종 inventory, 다른 source/sink accounting, 완전 혼합 가정을 caller가 검토해야 한다. 평형 speciation·수송·침전·금속손실은 풀지 않는다. [입력 계약과 제한](CREVICE_ELECTROCHEMICAL_COMPOSITION_KO.md)을 참조한다.


`integration.crevice_composition_to_aqueous_mass_action_history`는 exact-knot 조성 이력을 knot별 caller `AqueousMassActionSystem`에 연결한다. mol/m³를 mol/L로 바꾸고 고정 γ로 양의 초기활동도를 구성하며 `composition_derived_constraint_ids`에 caller가 선택한 제약 목표만 현재 조성에서 재계산하고 나머지 고정 목표는 보존한다. 반응망·온도별 상수·활동도 계수·표준상태·Evidence는 caller가 각 knot마다 공급한다. [연동 계약과 범위](CREVICE_COMPOSITION_MASS_ACTION_KO.md)를 참조한다.


`integration.aqueous_mass_action_to_crevice_nernst_history`는 digest-검증한 crevice mass-action history 또는 exact-knot B-dot speciation history의 무차원 활동도를 caller redox quotient·전자수·표준전위 knot와 결합해 Nernst half-cell profile을 만든다. 반응식, E0 history, 표준상태·온도 적용성·기준전극은 caller가 제공하며, B-dot 경로는 upstream parameter-record lineage를 보존한다. 이는 순차 연동이며 current–chemistry 동시 연성이나 부식률 계산은 아니다. [연동 계약과 한계](AQUEOUS_MASS_ACTION_TO_NERNST_KO.md)를 참조한다.

`electrochemistry.crevice_mixed_potential_history`는 raw inventory 기반 Nernst 결과와 mass-action/B-dot 활동도 이력 기반 Nernst 결과를 같은 방식으로 소비한다. 여러 반응이 같은 source-history lineage, asset/location/physical scope, clock, 시간·온도 knot 및 기준전극을 공유해야 한다. B-dot 경로에서는 원 inventory digest를 꾸며내지 않고 knot history와 upstream activity-result digest를 별도 lineage로 전달한다. [혼합전위 이력 계약](CREVICE_MIXED_POTENTIAL_HISTORY_KO.md)을 참조한다.

## 신규 후처리·연동 API (2026-10-30)

`integration.aqueous_candidate_network_workflow`는 사용자가 정한 수용액 종 인벤토리와 원소식/전하로 제한된 반응 후보를 생성한 뒤, 사용자가 선택하고 Evidence로 뒷받침한 반응 방향·평형상수·온도를 기존 mass-action assembly로 전달한다. 같은 종 집합과 원소식/전하, 온도, 표준상태, 각 단계의 digest가 맞지 않으면 거절한다. 출력은 계산 가능한 mass-action system 구성물이며 종·반응·상 자동선택이나 평형 계산, 부식률 예측을 뜻하지 않는다.

- `integration.crevice_aperture_history_refinement`: digest-pinned CREV geometry history에 caller가 정한 aperture relative-change/segment/bisection 한도를 적용한다. 결과를 registry로 실행할 수 있고 `resolved_geometry_states`와 `interpolated_geometry_states`를 나누어 돌려준다. 중간점은 선형 보간일 뿐 transport/electrochemistry 재계산이 아니다. 상세는 [CREV aperture refinement 안내](CREVICE_APERTURE_REFINEMENT_KO.md).
- `integration.wet_co2_elemental_phase_handoff`: caller formula/solution volume과 computed phase history를 조합해 원소별 inventory를 산출한다. RunContext asset/location/time basis 확인과 finite/nonnegative/clock/shape 검사를 적용한다. 경계 flux closure나 누락 phase를 추론하지 않는다. 상세는 [WCO₂ elemental handoff 안내](WET_CO2_ELEMENTAL_PHASE_HANDOFF_KO.md).

이 두 registry entry는 외부 provider parser 및 물리 적합성 검증을 대신하지 않는다.

- `integration.gasket_leakage_scenario_exposure`: computed finite correlated gasket leakage `AssessmentResult`를 digest로 고정하고, caller-reviewed constant-state duration을 곱해 scenario별 누설량(mol)과 extrema witness를 만든다. 유량 상태 변화는 가정하지 않는다. 자세한 경계는 [전용 안내](GASKET_SCENARIO_EXPOSURE_KO.md).

## WCO2/FAT/GASK 병렬 증분 (2026-10-30)

`integration.aqueous_candidate_network_workflow`는 caller 종 목록으로 balanced reaction 후보를 열거하고 Evidence-backed manual selection/logK binding 뒤 mass-action assembly를 수행한다. 모든 workflow stage digest, species formula/charge, temperature 및 standard state를 연결하며 자동 chemistry/phase discovery와 equilibrium solve는 제공하지 않는다. API 계약 및 미해결 범위는 [reaction candidate binding 안내](AQUEOUS_CANDIDATE_REACTION_BINDING_KO.md)를 참고한다.

Stateful multiaxial cycle block receipt를 사용할 때 provider ID/revision/run ID/result digest도 damage result에 유지된다. 기존 cycle exchange 문서를 함께 참고한다.

`integration.gasket_leakage_scenario_exposure`는 상관 finite scenario rate의 computed result에 constant-state exposure duration을 적용해 scenario별 mol과 min/max witness를 반환한다. FTA probability 또는 시간 변화 누설로 바꾸려면 추가 물리·사건 매핑 API가 필요하다. [노출량 handoff 안내](GASKET_SCENARIO_EXPOSURE_KO.md).

`integration.gasket_leakage_scenario_rate_interval`은 같은 scenario ID와 calibration realization으로 맞춘 두 시점의 leakage `AssessmentResult`를 받아, caller가 검토한 piecewise-linear rate reconstruction의 정확한 trapezoid amount를 scenario별 계산한다. Joint/scope, source/calibration, node order와 시간 context를 확인하고 확률이나 샘플하지 않은 극값은 추론하지 않는다.

`integration.aqueous_candidate_network_speciation` takes the computed candidate-network workflow `AssessmentResult` and its result digest, verifies the exact mass-action assembly/system lineage, then invokes the existing fixed-gamma single-phase aqueous speciation solver. Its RunContext must match the source asset, location and time basis. It preserves upstream stage digests and solver status. It performs no reaction/phase discovery or kinetic/corrosion inference. See [workflow-to-speciation contract](AQUEOUS_CANDIDATE_NETWORK_SPECIATION_KO.md).

`fatigue.multiaxial_life_scenario_envelope`는 computed critical-plane life campaign `AssessmentResult`의 digest-pinned finite correlated scenario set을 받아 cycle-life extrema와 witness를 보고한다. 시나리오를 완전한 결합 사례로 유지하고 calibration/material/cycle-support/context 일치를 요구한다. 이는 확률이나 신뢰구간이 아니다. [입력·계보·제한](MULTIAXIAL_LIFE_SCENARIO_ENVELOPE_KO.md).
## CFD crevice solver → restricted transport binding

`matintegrity.models.external_crevice_solver.bind_external_crevice_velocity(request, receipt)` binds an approved `ExternalCreviceSolverHistory` to a `RestrictedTransportRequest` and returns `(bound_request, velocity_provider)`. It checks ordered cell widths, total axial length, and that every requested transport output time falls inside the receipt clock. It records the provider ID, configuration digest, and source-result digest on a revalidated request copy. Use it with `solve_restricted_transport(..., axial_advection_velocity=velocity_provider)`.

`fabrication.gasket_leakage_covariance_propagation` adds a first-order delta-method path for one nominal gasket state. Its covariance vector order is node contact pressures, common differential pressure, node areas, then row-major calibration flux cells. It requires a finite symmetric positive-semidefinite covariance and explicit evidence/review gates; nominal pressures must be strictly inside calibration cells because derivatives at table knots are not unique. The result reports local Jacobian, nominal rate, propagated variance and standard uncertainty, not a confidence interval or nonlinear bound.

The request must already carry explicit `time_varying_axial_advection_reviewed=True` and `axial_advection_and_flow_continuity_reviewed=True`. The binding does not make these judgments, establish CFD accuracy, infer boundary conditions, or permit extrapolation. Reverse velocities still require the solver's reviewed reversal and distal-inflow conditions. This API is a caller-controlled coupling convenience; users remain responsible for ensuring the CFD and transport clocks share the same physical time origin.


`integration.aqueous_external_activity_speciation_history`는 `ExternalAqueousActivityHistory`의 각 정확한 시각·온도 knot에서 외부 composition-dependent gamma callback을 독립 호출해 질량작용 평형 이력을 반환한다. species/reaction/constraint topology 및 provider revision은 고정되고 parameter records는 knot별로 제공된다. 시간 사이의 보간은 하지 않는다. 상세 제한과 review는 [외부 aqueous activity provider](AQUEOUS_EXTERNAL_ACTIVITY_PROVIDER_KO.md)를 따른다.


`build_external_aqueous_transport_activity_callback(request, activity_provider)`는 mol/m³ 종×공간상태 행렬을 받아 caller provider로 각 transport 위치의 molality-standard-state 활동도계수를 생성한다. `RestrictedTransportRequest.activity_provider_id`와 `activity_configuration_sha256`는 callback 속성에 일치시킨다. 이는 transport chemical-potential correction 경계이며 local speciation solver는 아니다. 상세 데이터 형식·review gates는 [외부 aqueous activity provider](AQUEOUS_EXTERNAL_ACTIVITY_PROVIDER_KO.md)를 참조한다.


일부 provider 연동 계산기는 JSON으로 표현할 수 없는 Python callback을 요구한다. `ModelRegistry.describe(model_id)["runtime_dependencies"]`에 선언된 이름으로 `ModelRegistry.run(..., runtime_dependencies={name: callable})` 또는 `run_json(..., runtime_dependencies=...)`에 주입한다. undeclared·누락 dependency는 거절된다. 입력 JSON에는 callback 객체 대신 provider ID/revision/configuration·record digest와 Evidence를 보관한다.


`fabrication.gasket_leakage_box_envelope`는 caller가 명시한 independent rectangular uncertainty set 안에서 pressure/area/calibration-flux 구간의 bilinear 누설 극값과 witness를 계산한다. 이는 correlation-preserving finite scenario 또는 covariance delta method와 별도 API이며 확률·신뢰구간이 아니다. [Gasket 상관 시나리오 및 불확실성](GASKET_CORRELATED_SCENARIO_UNCERTAINTY_KO.md)에 exactness 조건과 증명 경계를 기록한다.

`fabrication.gasket_leakage_weighted_scenario_moments`는 동일한 joint scenario 결과에 caller가 제공하고 digest·권리 근거로 고정한 양의 가중치를 적용해 finite-set 가중 평균·모집단 분산·표준편차와 extrema를 반환한다. 가중치 합은 입력에서 1이어야 한다. 가중치 의미는 empirical frequency, quadrature 또는 user-declared 중 명시하며 자동 확률화·신뢰구간 계산은 하지 않는다.

`fabrication.gasket_contact_pressure_screen`는 digest-pinned flange contact 결과에서 Pa 단위의 node 평균 접촉압력을 caller가 제공한 최소/선택적 최대 screening window와 비교한다. 비정적 결과는 exact output knot만 받는다. 출력은 pressure margin이며 gasket seal acceptance나 성능 판정이 아니다. 상세 범위는 [caller gasket pressure screen](GASKET_CONTACT_PRESSURE_SCREEN_KO.md)을 참조한다.

`degradation.crevice_lumped_exchange_reaction_history`는 일정 체적·완전혼합·단일 성분 가정 아래 piecewise-constant bulk concentration, 교환 유량, 1차 소모 계수의 폐형식 구간해와 교환·소모·inventory ledger를 계산한다. 공간 transport와 다성분 speciation/kinetics를 대신하지 않는다.

`chemistry.layered_scale_history_stack_transport`는 각 caller scale-thickness 결과에서 하나의 동일한 exact time knot을 선택해 ordered diffusion-layer stack에 연결한다. phase-to-layer 관계는 명시적으로 제공해야 하고 시간 보간·phase discovery는 하지 않는다. 자세한 경계는 [layered scale history stack](WET_CO2_LAYERED_SCALE_HISTORY_STACK_KO.md)을 참조한다.


## 추가 연결 API (2026-10-30)

`corrosion.planar_slit_transient_hydraulic_history`는 ordered cell ID와 구간별 압력차·간극으로 wide planar slit의 signed 유량 이력을 계산한다. 일정 구간 입력에 대해 lumped inertance/resistance ODE를 정확 전파하고 누적 체적과 유량 반전 기록을 남긴다. 이는 비압축 Newtonian·층류·fully developed 가정 아래의 축약 모델이며 full unsteady Navier–Stokes, 산화막/부식 반응 또는 recession 연성은 포함하지 않는다. geometry/pressure/property Evidence, rights evidence와 적용성 검토가 필요하다. [모델 범위](PLANAR_SLIT_TRANSIENT_HYDRAULIC_KO.md)를 참조한다.

`matintegrity.bind_planar_slit_transient_hydraulic_interval()`은 단일 계산된 hydraulic interval을 같은 길이의 local-clock `RestrictedTransportRequest`에 결합해 정확한 지수형 velocity callback을 만든다. 호출자는 반환 callback을 `solve_restricted_transport(..., axial_advection_velocity=callback)`에 전달한다. face aperture 재구성, 시간가변 advection, flow continuity와 가능한 역류·말단 유입 경계를 검토해야 한다. 결합은 one-way이고 chemistry나 wall recession에서 유량을 갱신하지 않는다. 자세한 계약·예시는 [transient slit hydraulic 안내](PLANAR_SLIT_TRANSIENT_HYDRAULIC_KO.md)를 참조한다.

여러 연속 구간은 `matintegrity.bind_planar_slit_transient_hydraulic_history_series()`로 일괄 연결할 수 있다. 원 hydraulic input/result digest를 한 번 확인한 뒤 각 local-clock transport request에 interval별 callback을 만든다. 각 선택 구간의 resistance/inertance, equilibrium flow, 시작·종료 flow가 pinned 입력과 서로 맞는지도 대조한다.

`fatigue.multiaxial_weighted_life_scenario_moments`는 `fatigue.multiaxial_life_scenario_envelope`의 완전한 유한 scenario에 정렬된 양의 가중치를 적용해 평균·분산·표준편차·극값을 산출한다. 가중치는 입력에서 합이 1이어야 하고 digest 및 Evidence로 고정된다. 선택적으로 검토된 weighted inverse-ECDF 분위수, 최저 수명부터 지정 가중 질량까지의 lower-tail 평균, 수명 경계 이하 scenario 가중 몫도 제공한다. 후자는 유한 manifest의 가중 비율이며 failure probability가 아니다. 결과는 caller scenario 집합의 기술통계이며 probability, confidence, continuous bound 또는 material qualification이 아니다. [모델 범위](MULTIAXIAL_WEIGHTED_LIFE_SCENARIOS_KO.md)를 참조한다.

## 포화도 이력과 외부 자료 변환 API

`chemistry.aqueous_saturation_history_events`는 고체 후보별 caller 계산 `log10(Q/K)` 절점의 canonical digest를 확인하고, 승인된 piecewise-linear 보간으로 임계 통과 시점과 초과 지속시간을 기록한다. 결과는 입력된 용액 모델의 이벤트 기술량이며 석출량·반응속도·부식률이 아니다. [계약 및 경계](models/AQUEOUS_SATURATION_HISTORY_EVENTS_KO.md).

`integration.aqueous_vant_hoff_saturation_events`는 computed van't Hoff saturation `AssessmentResult`의 전체 digest와 Registry input/context digest를 다시 확인한 뒤 선택한 한 고체의 각 exact knot를 이벤트 API에 연결한다. 각 knot의 후보가 정확히 하나씩 존재해야 하며 RunContext는 원 결과와 같아야 한다. 출력에는 부모 digest, 선택 고체와 추출 knot가 유지된다.

`corrosion.ti12mo5zr_aesec_signed_equivalent_penetration`은 로컬 전용 Ti-12Mo-5Zr AESEC 데이터의 Ti/Mo/Zr 원소 면적질량 유속을 caller 제공 밀도로 signed 균일 등가 침투량으로 변환한다. 원자료 digest·row lineage, 시간축, 양의 용출 부호, 원소 coverage, density와 선형 적분 가정 승인이 모두 필요하다. 국부 최대손상, Faraday 환산, 수명 또는 위험도를 제공하지 않는다. [변환 계약](models/ti12mo5zr_aesec_mass_balance.md).

`corrosion.ti12mo5zr_uniform_equivalent_remaining_thickness`는 digest가 검증된 AESEC 등가침투 AssessmentResult의 exact observation knots를 caller 측정 기준두께와 연결한다. 양의 누적 침투만 차감하고 음의 signed ledger는 그대로 보존한다. 출력은 균일 면적 평균 이력이므로 국부 벽두께, 수명 또는 위험도 판정으로 해석하지 않는다. [잔여 두께 handoff](models/ti12mo5zr_remaining_thickness.md).

`corrosion.ti12mo5zr_eis_complex_impedance`는 완전한 allowlisted Ti-12Mo-5Zr EIS 워크북의 원행을 입력받아 caller가 Evidence와 함께 선택한 phase 부호에 따라 `|Z|`·phase를 실수/허수 임피던스로 변환한다. source row order·frequency·scan time을 보존하며 면적 정규화, 노출시간 추론, 등가회로 fitting, 부식저항 추정 또는 합금 순위화는 하지 않는다. [EIS 변환 안내](models/TI12MO5ZR_EIS_COMPLEX_KO.md).

`fabrication.gasket_contact_pressure_window_events`는 digest가 확인된 gasket 접촉이력에서 선택 노드의 접촉압력을 추출하고, caller가 증거와 이용조건을 제공한 압력창의 이탈 시간·구간을 검토된 선형 보간으로 보고한다. 이는 seal acceptance·누설·고장 확률 판정이 아니다. [접촉압력 이벤트 안내](GASKET_CONTACT_PRESSURE_WINDOW_EVENTS_KO.md).

`integration.cycle_block_feature_handoff`는 caller의 닫힌 tensor cycle에서 선택한 finite plane의 응력·변형률 특징을 명명된 `IntegerCycleDamageBlock.parameters`에 단위와 digest를 붙여 전달하고, 기존 adaptive block 요청에 결합한다. 피로 법칙·damage·수명은 caller callback에 남는다. [handoff 안내](MULTIAXIAL_CYCLE_BLOCK_FEATURE_HANDOFF_KO.md).
`adapter.corrosion_rate_history_to_fault_tree_basic_event`는 digest가 확인된 finite corrosion-thickness condition을 기존 FTA 기본사건 계약에 연결한다. 이벤트 확률·conditioning·공통 범위·Evidence와 권리 경계는 호출자가 따로 제공해야 하며, 결정론적 감육 계산으로 확률을 만들지 않는다([설명](models/CORROSION_RATE_HISTORY_FTA_BINDING_KO.md)).

`data.mendeley_thermal_rod_typed_rows`는 checksum-pinned Mendeley thermal-rod archive의 선택 run을 metadata-only로 감사한다. 원 행이 필요한 경우 `matintegrity.thermal_typed_rows.iter_thermal_rod_observation_rows()`를 호출해 `ThermalRodReadAuthorization`을 전달한다. 반환 행에는 CSV 순서 및 provider row 번호, 시간·6개 thermocouple excess-temperature 채널·controller count, archive/member/row SHA-256, Evidence와 attribution/authorization digest가 포함된다. Controller count를 power/heat flux로 바꾸거나 측정에서 열물성·부식량·구조 성능을 추정하지 않는다. 로컬 원자료 행은 공개 배포물에 포함하지 않는다. [typed row 계약](datasets/THERMAL_ROD_TYPED_ROWS_KO.md).

`data.mendeley_crack_arrest_typed_rows`는 pinned CC BY 4.0 Mendeley C1/C2 archive를 specimen별 metadata 감사와 authorized local typed CSV rows로 제공한다. 원본 행 순서, signed force/displacement, zero 및 단위 변환, archive/member/row digest, Evidence와 authorization 계보를 보존하며 두 specimen을 합치거나 fracture toughness/acceptance를 추론하지 않는다. [typed row 계약](datasets/CRACK_ARREST_TYPED_ROWS_KO.md).

`data.mendeley_guided_wave_typed_sample_rows`는 기존 checksum-pinned pipeline guided-wave parser 위에 선택한 acquisition/frequency의 typed sample iterator를 제공한다. 원래 순서와 반복 거리, native voltage channel 및 archive/nested/member/row Evidence·authorization digest를 보존한다. 감육, 부식률, 결함, POD 또는 qualification은 추론하지 않으며 원자료는 local-only로 유지한다. [typed row 계약](datasets/GUIDED_WAVE_TYPED_ROWS_KO.md).

`integration.fixed_fugacity_carbonate_to_scale_kinetics`는 계산된 fixed-fugacity carbonate history의 exact knot에서 caller-evidenced 활동도 계수·반응종 활동도·온도지원 Ksp를 사용해 선택 고체상의 포화도를 확인하고, 완전한 포화도 이력을 기존 scale kinetics에 전달한다. 모든 Ksp record는 knot별 온도 적용성 검토가 필요하며 미검토 항목을 식별해 계산을 차단한다. 입력이나 시간점이 빠지면 kinetics를 실행하지 않으며 자동 고체상 선택, kinetic 계수 추정, 부식량 또는 수명 계산을 하지 않는다. [모델 계약](models/FIXED_FUGACITY_CARBONATE_SCALE_KINETICS_KO.md).

`data.zenodo_ceit_uniform_corrosion_field_typed_rows`는 고정된 Zenodo CEIT JSON을 확인한 뒤 기존 field parser를 재사용해 typed observation row를 제공한다. 원 순서, 단위/clock 선택, 소스 파일과 행 digest, Evidence 및 local-only authorization을 보존한다. ToF·전압 신호만으로 두께, 부식률, POD 또는 acceptance를 추론하지 않는다. [dataset 계약](datasets/CEIT_FIELD_TYPED_ROWS_KO.md).

`data.zenodo_mg_deis_typed_matrix_rows`는 pinned CC0 AZ31/WE43 DEIS archive의 선택 matrix를 기존 bounded parser로 읽어 typed rows로 전달한다. 원 행·열 순서, native values, archive/member/row Evidence 및 authorization lineage를 유지하고 시간·주파수·단위·부식률을 추론하지 않는다. [dataset 계약](datasets/ZENODO_WE43_AZ31_DEIS_TYPED_ROWS_KO.md).

`data.figshare_corrosion_alloy_metrics_typed_rows`는 기존 alloy-metrics workbook parser를 local typed rows로 감싼다. CC BY 4.0은 compilation에 한정되며 개별 논문 관측값의 재배포 권리는 unresolved로 모든 row와 audit에 유지한다. 따라서 API는 local-only 승인·attribution과 digest 계보를 요구하고 원 행을 배포물에 포함하지 않는다. [자료·권리 범위](datasets/CORROSION_METRICS_TYPED_ROWS_KO.md).

`data.dryad_formate_packer_corrosion_rows`는 CC0 Dryad H₂S/CO₂ formate-packer workbook의 원행·셀 좌표·저장 유형을 caller 승인 및 파일 hash 확인 뒤 local-only typed rows로 읽는다. figure/table 의미, 조건, 단위 및 관측/요약 구분은 추론하지 않는다. [자료·권리·API 범위](datasets/DRYAD_FORMATE_PACKER_H2S_CO2_TYPED_ROWS_KO.md).

`integration.crevice_spatial_mass_action_workflow`는 각 transport knot/cell에 대해 caller가 완전 정의한 aqueous mass-action input을 기존 solver로 개별 풀이한 뒤, 모든 셀이 성공했을 때만 digest-bound crevice volume ledger를 조립한다. 종·활동도·반응 네트워크·제약은 자동 생성하지 않고 첫 실패에서 prefix를 보존한다. [workflow 계약](models/CREVICE_SPATIAL_MASS_ACTION_WORKFLOW_KO.md).

`fatigue.ince_glinka_gsa_miner_campaign`는 caller가 지정한 finite closed-tensor cycle groups 각각을 기존 Ince–Glinka GSA-to-life curve에 연결한 뒤, 모두 계산된 경우에만 기존 Miner rule로 damage fraction을 합산한다. Cycle counting, sequence effect, material curve calibration, probability 또는 remaining life는 생성하지 않는다. [campaign 계약](models/INCE_GLINKA_GSA_MINER_CAMPAIGN_KO.md).

`data.mendeley_fracture_toughness_temperature_typed_rows`는 고정 Mendeley workbook의 Table A2/A3 행을 typed, local-only records로 제공한다. CC BY 4.0은 compilation 수준이며 individual observation rights unresolved라는 카탈로그 상태를 계속 유지한다. A2/A3 분할, 원 순서, 단위, Evidence와 권한 digest를 보존하고 toughness curve나 ASTM 수락성을 fitting하지 않는다. [자료·권리 범위](datasets/FRACTURE_TOUGHNESS_TYPED_ROWS_KO.md).

`data.mendeley_atmospheric_corrosion_typed_rows`는 기존 checksum-pinned 대기부식 parser의 행을 caller authorization/Evidence 계보와 함께 local-only typed records로 제공한다. Compilation의 CC BY 4.0 표시와 개별 원천 관측의 unresolved 재배포 권리를 구분하며, 공개 배포에 행 데이터를 복사하지 않는다. [자료·권리 범위](datasets/ATMOSPHERIC_CORROSION_TYPED_ROWS_KO.md).

`integration.elastic_joint_to_flange_contact_history`는 전역 joint clamp-force history를 caller 검토한 선형 nodal closure transfer를 통해 exact knot별 기존 unilateral flange-contact field solver에 연결한다. Reference state, location, material, time identity와 solver result digests를 보존하고, FE compliance·transfer·seal/leakage law는 자동 추정하지 않는다. [workflow 계약](models/ELASTIC_JOINT_TO_FLANGE_CONTACT_HISTORY_KO.md).

`chemistry.crevice_steady_wall_sink`는 고정된 막힌 슬릿에서 단일 종의 정상상태 1차 벽면 소모 방정식을 해석적으로 푼다. caller가 검토한 상수 물성과 경계조건 아래 농도 프로파일과 입구·벽면 sink 질량수지를 제공하며 과도 수송, speciation, 상평형, 부식률은 추론하지 않는다. [계산 경계](models/CREVICE_STEADY_WALL_SINK_KO.md).

`fatigue.sampled_stress_invariant_history`는 검토된 닫힌 응력 tensor 표본에서 최대 정수압 응력과 finite-sample J2 편차거리 지표를 산출한다. 반경 지표는 직선형 경로에 한해 통상 진폭과 일치하며, cycle counting·수명·재료 기준은 계산하지 않는다. [계산 범위](models/SAMPLED_STRESS_INVARIANT_HISTORY_KO.md).

`chemistry.pitzer_salt_finite_scenario_envelope`는 같은 순수 염·온도 조건으로 caller가 열거한 2–200개 Pitzer 단일염 계산을 순서대로 수행하고, 전부 성공했을 때에만 그 목록의 extrema를 요약한다. 연속 경계, 확률, 혼합 전해질 활동도 모델은 제공하지 않는다. [시나리오 계약](models/PITZER_SALT_FINITE_SCENARIO_ENVELOPE_KO.md).

`fabrication.gasket_contact_transition_brackets`는 digest가 일치하는 기존 점탄성 플랜지 접촉 이력에서 인접 계산 절점 사이 상태 변화만 시간 bracket으로 보고한다. 정확한 사건 시각, 절점 사이 숨은 전이, 접촉 FE 응답 또는 실링 적합성을 추론하지 않는다. [전이 구간 계약](models/GASKET_CONTACT_TRANSITION_BRACKETS_KO.md).

`chemistry.pitzer_salt_saturation_index`는 단일 순수 염 Pitzer mean-ion activity와 caller가 검토하고 Evidence/hash를 제공한 온도 일치 Ksp를 결합해 `log10(Q/Ksp)`를 계산한다. 포화지수만 반환하며 석출량, kinetics, 혼합 전해질 거동 또는 부식을 추론하지 않는다. [포화 스크리닝](models/PITZER_SALT_SATURATION_INDEX_KO.md).

`chemistry.crevice_transient_wall_sink`는 고정된 막힌 슬릿의 단일종 확산–1차 벽면 소모 방정식을 finite eigenfunction 합으로 계산한다. caller가 요청한 시간·위치·항 수만 반환하며 절단 오차나 수렴을 보증하지 않는다. [과도 응답 API](models/CREVICE_TRANSIENT_WALL_SINK_KO.md).

`fatigue.sampled_tensor_stress_strain_work_cycle`는 caller가 검토한 닫힌 응력–변형률 텐서 경로의 signed `∮σ:dε`를 유한 선분 적분으로 산출한다. signed 경로 work만 제공하며 비가역 소산, 피로 손상 또는 수명으로 해석하지 않는다. [계산 계약](models/MULTIAXIAL_TENSOR_WORK_CYCLE_KO.md).

`fabrication.gasket_contact_transition_refinement`는 caller 외부 접촉 solver callback을 이용해 단일 전이 가정 아래 기존 전이 구간을 좁힌다. provider/evidence/digest 계약을 검증하고 끝까지 bracket만 반환하며 exact event time이나 FE solver 자체는 제공하지 않는다. [callback 계약](models/GASKET_CONTACT_TRANSITION_REFINEMENT_KO.md).

`data.zenodo_zr_nb_sn_electrochemical_typed_rows`는 CC BY 4.0 Zenodo v2 자료의 8개 XLSX 파일만 정확한 파일명·크기·SHA-256 pin을 통과해 local-only iterator로 전달한다. `matintegrity.zenodo_zr_alloy_electrochemistry.iter_zr_alloy_workbook_rows()`는 caller attribution/local-use declaration을 요구하며 workbook, worksheet, 원 행 번호, 원 셀 순서·종류, 수식 문자열, 파일·행 digest와 Evidence를 보존한다. 빈 행은 생략하지만 물리 행 번호를 유지한다. 셀 의미, 시편 독립성, 부식률·감육·수명·acceptance·확률은 추론하지 않고 수식은 평가하지 않는다. 원본 파일은 배포물에서 제외한다. [dataset 경계 및 사용](datasets/ZR_NB_SN_ELECTROCHEMICAL_NOISE_DATA_KO.md).

`fatigue.multiaxial_invariant_limit_screen`은 기존 finite-sample 응력 invariant 경로와 caller가 제공한 동일 재료조건의 보정 계수·한계값을 digest/Evidence로 연결한다. 검토된 계수로 정수압 및 편차응력 descriptor의 선형 screen parameter를 계산하고 한계와 비교한다. 표본 사이 경로, 피로 수명, 파손확률, code acceptance 또는 재료 qualification은 추론하지 않는다. [계산 경계와 근거](models/MULTIAXIAL_INVARIANT_LIMIT_SCREEN_KO.md).

`fabrication.gasket_leakage_fit_diagnostics`는 digest가 맞는 기존 비음수 누설 맵 계산 결과를 재적합하지 않고, 원 관측 ID·시편 label·source-group 기준으로 calibration/holdout 잔차 통계를 계산한다. 독립 실험·확률·합격 또는 실링 qualification 주장은 하지 않는다. [진단 범위](models/GASKET_LEAKAGE_FIT_DIAGNOSTICS_KO.md).

`fabrication.gasket_contact_state_grid_sweep`는 source contact-history와 context가 맞는 외부 contact-state provider를 caller가 지정한 증가 시간격자에서 호출한다. 격자 이웃 사이에서 관측된 접촉 변화 bracket을 전부 보존하지만 숨은 전이나 정확한 사건시각·FE 응답·실링 acceptance는 추론하지 않는다. [provider 계약](models/GASKET_CONTACT_STATE_GRID_SWEEP_KO.md).

`degradation.wet_co2_two_film_transfer`는 caller가 제공한 CO₂ fugacity·Henry convention·기상막 및 액상막 계수로 정상상태 기–액 계면값과 부호 있는 CO₂* 플럭스를 계산한다. carbonate 종분화·반응·감육·부식률은 계산하지 않는다. [경계 모델 설명](models/WET_CO2_TWO_FILM_TRANSFER_KO.md).

`degradation.crevice_wall_sink_rate_history`는 caller가 선언한 exact temperature knot에서 기존 Arrhenius 계산기를 재사용해 1차 벽면 전달계수 이력을 계산한다. 지원 온도와 원 시계열 순서를 보존하며 농도·수송·반응 또는 감육은 계산하지 않는다. [이력 계약](models/CREVICE_WALL_SINK_RATE_HISTORY_KO.md).

`degradation.wet_co2_two_film_transfer_history`는 시간순 exact knot마다 기존 정상상태 2막 점 모델을 독립 평가해 전달량 상태를 묶는다. 첫 비계산 knot에서 중지하고 성공 prefix와 source/result digest를 보존하며, knot 사이 동역학·보간·반응은 제공하지 않는다. [이력 계약](models/WET_CO2_TWO_FILM_TRANSFER_HISTORY_KO.md).

`fatigue.multiaxial_sines_mean_limit_screen`은 caller 제공 닫힌 응력 경로의 유한 표본 J2 편차거리 지표와 시각 가중 정수압 평균을 명시 계수로 결합해 caller 한계와 비교한다. 이는 연속 경로 기준이나 수명, 확률, acceptance 또는 qualification을 뜻하지 않는다. [계산 경계와 시간 가중](models/MULTIAXIAL_SINES_MEAN_LIMIT_SCREEN_KO.md).

`fatigue.papadopoulos_p2_finite_sample_limit_screen`은 caller가 직접 정의한 유한 표본 재료면과 면내 전단 방향 quadrature에서 전단 진폭 지표를 계산하고 최대 정수압 응력 항과 caller 한계를 결합한다. 유한 방향 집합의 계산값이며 연속 최적화·재료계수 추정·수명·확률·qualification은 제공하지 않는다. [계산식과 문헌 경계](models/PAPADOPOULOS_P2_FINITE_SAMPLE_SCREEN_KO.md).

`degradation.crevice_aperture_displacement_flow`는 고정된 caller aperture geometry 이력에서 각 셀 체적 증감률의 누적으로 1차원 비압축성 blind-slit displacement-flow ledger를 만든다. 압력·운동량 방정식, 수송, 반응 또는 부식은 풀지 않는다. [연속성 계산 경계](models/CREVICE_APERTURE_DISPLACEMENT_FLOW_KO.md).

`fatigue.dang_van_finite_sample_limit_screen`은 caller가 선언한 유한 면·전단 방향·시간 표본에서 평균 전단 응력 이탈과 순간 정수압 응력을 caller 계수로 결합해 caller 한계와 비교한다. 평면과 시간 범위의 연속 극값, 피로 수명, 확률, acceptance 또는 qualification을 추론하지 않는다. [모델 경계와 공개 근거](models/DANG_VAN_FINITE_SAMPLE_SCREEN_KO.md).

`integration.crevice_solid_volume_inventory`는 caller가 제공한 digest-bound 셀·상별 고체 molar inventory per area와 Evidence-bound molar volume으로 체적 장부를 계산한다. precipitation, deposit morphology, porosity, wall attachment, aperture reduction이나 corrosion은 추론하지 않는다. [재료수지 경계](models/CREVICE_SOLID_VOLUME_INVENTORY_KO.md).

`integration.crevice_deposition_aperture_history`는 위 체적 장부의 exact-knot 결과를 명시된 reference area, 셀 형상, 침전 면 수, coverage와 시간 정렬해 면적 평균 간극 및 covered-patch 간극 history로 매핑한다. 양면 분배와 coverage 내부 균일도는 caller가 검토한 가정이며, morphology·porosity·부착·수송 피드백은 계산하지 않는다. [기하 변환 계약](models/CREVICE_DEPOSITION_APERTURE_HISTORY_KO.md).

`fatigue.multiaxial_sampled_shear_path_area`는 선택한 평면의 두 전단 변형률 좌표로 caller가 제공한 닫힌 유한표본 경로의 signed polygon area를 계산한다. 이는 경로 기술량이며 특정 피로 criterion, damage, life, acceptance 또는 qualification을 산출하지 않는다. [입력과 제한](models/multiaxial_sampled_shear_path_area.md).

`integration.crevice_local_solid_saturation`는 하나의 exact transport knot에서 각 셀의 digest-bound mass-action 결과를 기존 고체 포화도 검사로 연결한다. 셀별 결과를 보존하고 상 선택·침전량·속도·간극 변화는 추론하지 않는다. [공간 포화도 연결](models/CREVICE_LOCAL_SOLID_SATURATION_KO.md).

`fatigue.multiaxial_principal_stress_axis_rotation`은 닫힌 유한표본 대칭응력 이력에서 최대 대수 주응력축의 인접 표본 간 회전량을 계산한다. 최대·차상위 주응력이 근접해 축이 불안정한 표본은 caller 기준으로 거부하며, 피로 손상과 수명은 계산하지 않는다. [응력축 경로 기술량](models/principal_stress_axis_rotation.md).

`integration.crevice_saturation_exposure_history`는 같은 셀·고체 후보의 시간 knot에서 caller가 선언한 선형 `log10(Q/K)` 경로에 대해 양의 초과분의 시간 적분과 초과 지속시간을 계산한다. 포화도는 침전량이나 반응속도가 아니며, 상 선택·석출·간극 변화는 계산하지 않는다. [과포화 노출 진단](models/CREVICE_SATURATION_EXPOSURE_HISTORY_KO.md).

`integration.crevice_deposition_transport_geometry`는 침전 체적에서 유도한 exact-knot 간극 이력을 기존 crevice transport geometry-history 계약으로 변환한다. 생성 geometry를 순차 operator-split 수송에 연결할 수 있지만 동시 화학·유동·형상 해석은 하지 않는다. [기하-수송 연결](models/CREVICE_DEPOSITION_TRANSPORT_GEOMETRY_KO.md).

`fabrication.gasket_contact_root_localization`은 caller가 검토한 단일 단조 근 bracket 안에서 외부 FE/contact callback을 이용해 응답 부호변화 구간을 좁힌다. Provider query와 응답 digest를 보존하며, 물리 이벤트 시각·누설률·seal acceptance는 주장하지 않는다. [외부 응답 root API](models/GASKET_CONTACT_ROOT_LOCALIZATION_KO.md).

`degradation.wet_co2_liquid_side_mass_transfer`는 외부 유동 해석에서 받은 액상 평균 속도·벽 전단과 caller 물성/확산계수로 액상측 물질전달계수를 추정해 기존 two-film 전달 API의 입력으로 제공한다. 적용 Reynolds/Schmidt 범위와 유동 공급자 digest를 요구한다. 유동장, 젖음 면적, gas-film 저항, 수용액 반응 또는 부식률은 계산하지 않는다. [독립 구현 근거](models/WET_CO2_LIQUID_SIDE_MASS_TRANSFER_KO.md).

`degradation.crevice_wall_sink_arrhenius_calibration`은 측정된 유효 벽면 전달속도에서 기준 온도 주변의 Arrhenius 관계를 적합하고 별도 source group holdout을 평가한다. holdout은 적합에 사용되지 않으며, 이 계수는 금속 손실률이나 보편적 부식 kinetics가 아니다. [보정·적용 경계](models/CREVICE_WALL_SINK_ARRHENIUS_CALIBRATION_KO.md).

`fatigue.j2_prager_strain_history`는 caller가 지정한 소변형률 텐서 이력에 선형 등방경화·Prager 이동경화 J2 구성 업데이트를 적용한다. 변형률 증분마다 한 번 backward-Euler radial return을 수행하며, 재료별 적용성·초기상태 검토가 필요하다. 피로 손상·수명·재료 적격성은 산출하지 않는다. [구성 모델 범위](models/j2_prager_strain_history.md).

`integration.crevice_calibrated_wall_sink_rate_history`는 digest로 고정된 Arrhenius 보정 요청·결과를 재계산해 일치 여부를 확인하고, 보정 온도 지원구간 안의 정확한 온도 knot에 기존 wall-sink rate-history 계산을 적용한다. 유효 전달속도 이력만 연결하며 부식률이나 금속 손실은 산출하지 않는다. [보정 적용 API](models/CREVICE_CALIBRATED_WALL_SINK_HISTORY_KO.md).

`integration.crevice_calibrated_wall_flux_callback`은 검증된 유효 wall-sink 전달속도와 caller 표면농도 이력을 bounded 선형 보간해 기존 restricted-transport solver가 받을 callable flux 경계로 만든다. inward-positive 부호와 geometry/time/species 일치를 검토하며, 면적 가중은 수송 solver가 수행한다. [벽면 flux 연결](models/CREVICE_CALIBRATED_WALL_FLUX_CALLBACK_KO.md).

`integration.crevice_multispecies_wall_flux_callback`은 각 용존종의 digest-bound 전달속도·표면농도 이력을 공통 시간·셀 geometry와 수송 종 순서에 맞춰 independent wall-flux 행렬로 만든다. 종간 반응·site competition은 모델링하지 않는다. `validation.crevice_wall_sink_source_group_stability`는 calibration source group 하나씩 제외한 재적합과 out-of-fold 오차로 계수 안정성을 요약한다. 이는 외부 검증이나 qualification이 아니다. [다성분 경계](models/CREVICE_MULTISPECIES_WALL_FLUX_CALLBACK_KO.md), [그룹 안정성 진단](models/CREVICE_WALL_SINK_GROUP_CV_KO.md).

`integration.crevice_kinetic_solid_volume_history`는 고정 geometry 아래 다상 수송 계산의 exact solid concentration history를 셀별 몰/면적 inventory로 변환하고 기존 고체 체적 장부에 연결한다. upstream aqueous closure를 요구하며 morphology·coverage·aperture feedback은 추론하지 않는다. [kinetic inventory 연결](models/CREVICE_KINETIC_SOLID_VOLUME_HISTORY_KO.md).

`integration.crevice_saturation_interval_average_rates`는 caller가 제공한 셀별 포화도 비율의 선형 경로를 따라 기존 침전·용해 power law를 포화도 1에서 분할 적분하고 구간 평균 속도를 반환한다. 유한 quadrature 결과이며 구간 중 화학·기하와 동시 결합하지 않는다. `integration.crevice_solid_inventory_geometry_boundary_remap`은 이동 geometry 경계에서 고체 몰수를 면적 기준으로 보존해 목표 셀 체적 기준 농도로 변환한다. [구간 평균속도](models/CREVICE_SATURATION_INTERVAL_RATES_KO.md), [기하 경계 재매핑](models/CREVICE_SOLID_INVENTORY_GEOMETRY_REMAP_KO.md).

`integration.wet_co2_finite_liquid_transfer_history`는 고정 기상 저장조와 caller가 제공한 구간별 기·액막 전달계수 아래 고정 부피·완전혼합 액체의 중성 용존 CO₂* 재고를 해석식으로 전개한다. 기상 고갈, 탄산 종분화, 반응, 부식률 또는 위험도는 계산하지 않는다. [유한 액상 재고 경계](models/WET_CO2_FINITE_LIQUID_TRANSFER_HISTORY_KO.md).

`fatigue.papadopoulos_p1_finite_integral_screen`은 caller 유한 방향 quadrature로 Papadopoulos P1 고주기 피로 한계형을 근사한다. 응력 이력 표본의 닫힌 주기 전단 반범위와 caller 보정계수를 사용하며 연속 방향 적분 오차·피로수명·손상·적격성은 주장하지 않는다. [근사와 입력 경계](models/papadopoulos_p1_finite_integral_screen.md).

`fatigue.papadopoulos_p1_calibration`은 동일 재료조건의 완전반전 축·비틀림 내구한도로 P1 정수압 계수를 산출한다. `fatigue.papadopoulos_p1_calibrated_life`는 유한 적분 parameter와 caller P1 곡선을 support 내부에서만 log-log 보간하며, `fatigue.papadopoulos_p1_miner_blocks`는 caller cycle block에 대해 명시적으로 검토된 선형 Miner 누적을 적용한다. 곡선의 권리·적용성, cycle 분해, 하중 순서 효과와 qualification은 외부 검토 대상이다. [계수 보정](models/papadopoulos_p1_calibration.md), [수명 매핑](models/papadopoulos_p1_calibrated_life.md), [블록 누적](models/papadopoulos_p1_miner_blocks.md).

`fatigue.carpinteri_spagnoli_finite_limit_screen`은 caller 유한 평면 후보에서 최대 법선응력과 전단 벡터 진폭을 quadratic parameter로 결합해 HCF 한계와 비교한다. `fatigue.carpinteri_spagnoli_life_dependent_curve`는 caller 축·비틀림 S–N 곡선의 공통 수명구간에서만 생존수명을 푼다. 연속 임계면 선택·가변진폭 누적·qualification은 포함하지 않는다. [유한 screen](models/carpinteri_spagnoli_finite_screen.md), [수명 의존 곡선](models/carpinteri_spagnoli_life.md).

`fatigue.periodic_tensor_fourier_reconstruction`, `fatigue.periodic_tensor_fourier_rates`, `fatigue.periodic_fourier_tensor_work`, `fatigue.periodic_fourier_tensor_work_life`는 닫힌 균일표본 tensor 이력을 Fourier 보간·도함수·signed work·caller life curve 및 선형 Miner 누적으로 이어준다. 모든 결과는 선택한 유한표본 주기 보간 기준이며, aliasing·물리 경로 오차·소성 소산·재료 적격성을 보증하지 않는다. [재구성](models/multiaxial_periodic_fourier_reconstruction.md), [도함수](models/multiaxial_periodic_fourier_rates.md), [work 적분](models/multiaxial_fourier_tensor_work.md), [work–life](models/multiaxial_fourier_work_life.md).

`integration.wet_co2_carbonate_alkalinity_speciation`은 caller 고정 CO₂* 농도, 총 알칼리도 및 conditional K1/K2/Kw로 이상 농도기준 carbonate-only 종분화를 푼다. 기타 완충종, 비이상도, 반응속도, 부식률 또는 위험도는 포함하지 않는다. [적용 범위](models/WET_CO2_CARBONATE_ALKALINITY_SPECIATION_KO.md).

`integration.wet_co2_finite_gas_liquid_exchange_history`는 caller가 제공한 기상 inventory capacity와 Henry·2막 계수 아래 유한 기상 및 완전혼합 액상의 CO₂* 재고를 함께 갱신하고 signed 보존 장부를 반환한다. 상태식·용량 변화, carbonate chemistry, 반응, 부식률은 범위 밖이다. [유한 두 저장조 경계](models/WET_CO2_FINITE_GAS_LIQUID_EXCHANGE_HISTORY_KO.md).

`degradation.wet_co2_gas_side_mass_transfer`는 caller의 기체 유동·물성 입력에서 Chilton–Colburn 유사로 기상막 전달계수 `k_g`를 추정해 2막 전달 API에 공급한다. 전체 2상 유동이나 벽면 젖음, 부식률은 계산하지 않는다. `integration.wet_co2_parallel_zone_transfer`는 서로 분리된 계면 구역의 국부 기·액 상태와 면적별 signed 전달률을 합산한다. 구역 간 혼합·저장조 고갈·시간 변화는 다루지 않는다. [기상막 추정](models/WET_CO2_GAS_SIDE_MASS_TRANSFER_KO.md), [병렬 구역 장부](models/WET_CO2_PARALLEL_ZONE_TRANSFER_KO.md).

`integration.wet_co2_reactive_film_transfer`는 caller apparent 1차 비가역 sink를 갖는 정상 정체 액막과 기상막 저항을 결합하고 기상 흡수·액막 반응·bulk CO₂* flux를 분리한다. `integration.wet_co2_condensate_state`는 caller fugacity/Henry 물성값과 결정론적 bounds로 벽면 응축 가능성과 최초 생성 액상의 CO₂* 평형 범위를 스크리닝한다. 응축량·액상 pH·부식률은 추론하지 않는다. [반응 액막](models/WET_CO2_REACTIVE_FILM_TRANSFER_KO.md), [응축 상태 연결](models/WET_CO2_CONDENSATE_STATE_KO.md).

`integration.crevice_multispecies_wall_flux_callback`는 용존종별 digest-bound 전달속도·표면농도 이력을 공통 시간·셀 geometry와 수송 종 순서에 맞춘 독립 wall-flux 행렬로 변환한다. 종간 반응·site competition은 포함하지 않는다. `validation.crevice_wall_sink_source_group_stability`는 calibration 그룹별 교차 적합 잔차와 계수 분산을 요약하지만 외부 검증·qualification은 아니다. [다성분 flux 경계](models/CREVICE_MULTISPECIES_WALL_FLUX_CALLBACK_KO.md), [group-CV 진단](models/CREVICE_WALL_SINK_GROUP_CV_KO.md).

`fatigue.wang_brown_temporal_normal_excursion`은 caller가 계산한 shear rainflow cycle에 같은 clock의 normal-strain 샘플을 source index로 연결해 각 구간의 min/max/range를 반환한다. finite sample excursion만 제공하며 cycles를 재계수하거나 Wang–Brown damage/life criterion으로 확장하지 않는다. [시간 pairing 계약](models/wang_brown_temporal_normal_excursion.md).

`integration.wet_co2_reactive_film_transfer`는 caller apparent 1차 비가역 sink를 갖는 정상 정체 액막과 기상막 저항을 결합하고 기상 흡수·액막 반응·bulk CO₂* flux를 분리한다. `integration.wet_co2_condensate_state`는 caller fugacity/Henry 물성값과 결정론적 bounds로 벽면 응축 가능성과 최초 생성 액상의 CO₂* 평형 범위를 스크리닝한다. 응축량·액상 pH·부식률은 추론하지 않는다. [반응 액막](models/WET_CO2_REACTIVE_FILM_TRANSFER_KO.md), [응축 상태 연결](models/WET_CO2_CONDENSATE_STATE_KO.md).

`integration.crevice_multispecies_wall_flux_callback`은 용존종별 digest-bound 전달속도·표면농도 이력을 공통 시간·셀 geometry와 수송 종 순서에 맞춘 독립 wall-flux 행렬로 변환한다. 종간 반응·site competition은 포함하지 않는다. `validation.crevice_wall_sink_source_group_stability`는 calibration 그룹별 교차 적합 잔차와 계수 분산을 요약하지만 외부 검증·qualification은 아니다. `integration.crevice_wall_flux_inventory_history`는 이 경계 flux를 종별 signed 구간 수송량으로 적분한다. [다성분 flux 경계](models/CREVICE_MULTISPECIES_WALL_FLUX_CALLBACK_KO.md), [group-CV 진단](models/CREVICE_WALL_SINK_GROUP_CV_KO.md), [flux 재고 장부](models/CREVICE_WALL_FLUX_INVENTORY_HISTORY_KO.md).
## Wet-CO₂ 순수 물 포화 증기 물성 provider

`thermo.coolprop_pure_water_saturated_vapor_fugacity`는 optional `matintegrity[thermo]`의 CoolProp backend로 caller가 준 벽면 온도에서 순수 물 포화증기의 압력과 fugacity coefficient를 평가한다. 반환값은 기존 `integration.wet_co2_condensate_state`의 wall-equilibrium fugacity/provider 계보 필드에 전달할 수 있다. 사용 전 순수 물 표준상태가 해당 응축상에 적용되는지 검토해야 한다. 혼합가스 수증기 fugacity, 염수/MEG 활동도, 응축량 또는 부식률은 계산하지 않는다. 세부 한계와 호출 예시는 [CoolProp 습식 CO₂ 물 포화 provider](models/COOLPROP_WET_CO2_WATER_SATURATION_PROVIDER_KO.md)를 따른다.

`thermo.coolprop_pure_water_single_phase_state`는 같은 optional dependency에서 caller 지정 절대압력·온도의 순수 물 단일상 상태를 구해 밀도, 엔탈피, 정압비열, 점도, 열전도도, 음속 및 압축성계수를 반환한다. 기대 액상/기상/초임계 상태가 CoolProp 상태와 일치해야 하며 2상은 거절한다. backend·버전/revision·입력·결과 digest와 Evidence를 보존한다. 이 결과는 염수·글리콜·혼합가스 물성, 상변화, 질량전달 또는 부식률이 아니다. 상세 조건은 같은 [CoolProp 습식 CO₂ 물 provider 안내](models/COOLPROP_WET_CO2_WATER_SATURATION_PROVIDER_KO.md)를 따른다.

`integration.wet_co2_condensate_film_history`는 고정 벽 patch에서 caller가 제공하는 net retained-water flux를 구간별로 적산해 물의 면적 재고, 등가 균일막 두께, wet duration 및 dryout을 기록한다. Flux는 이미 condensation·retention·drainage·evaporation을 합친 값이어야 한다. 액상 밀도와 flux provider Evidence/digest를 요구하며 patch 간 이동·액적 형상·CO₂ 화학·부식률은 계산하지 않는다. [수막 재고 이력 안내](models/WET_CO2_CONDENSATE_FILM_HISTORY_KO.md).

`integration.crevice_geometry_aware_aqueous_chemistry_provider`는 `solve_crevice_transport_recession_feedback(..., geometry_aware_chemistry_provider=...)`에서 매 fixed-point 반복의 추정 aperture와 농도 상태를 caller reaction provider에 전달한다. 명시 species 순서·configuration digest·지원범위 및 stoichiometric 원소/전하 보존을 요구한다. 범위는 수용액 반응이며 고체 침전·용해, phase selection, activity feedback과 완전 동시 momentum 해석은 포함하지 않는다. [geometry-aware 크리비스 화학 provider](models/CREVICE_GEOMETRY_AWARE_AQUEOUS_CHEMISTRY_KO.md).

`integration.wet_co2_variable_condensate_transfer_history`는 구간별 기·액막 CO₂* 전달, caller condensate 부피/조성 유입, 완전혼합 액상 유출을 고정 wall patch의 액체 부피와 CO₂* 몰 재고에 함께 적산한다. 순수 물 응축 상태·water-only film inventory와 다른 제한 체적 API다. 완전혼합, 구간상수 입력, 비선택적 액상 유출을 가정하며 선택적 증발, 반응·speciation·기상 저장조 고갈, 공간 구배나 부식률은 계산하지 않는다. [변하는 응축액/CO₂* 재고](models/WET_CO2_VARIABLE_CONDENSATE_TRANSFER_HISTORY_KO.md).

`integration.wet_co2_finite_gas_variable_liquid_history`는 caller가 제공한 유한 기상 inventory-capacity, 기·액막 계수, Henry 계수와 구간별 액상 체적 flux를 사용해 기상 fugacity·액상 부피·CO₂* 농도를 함께 적분한다. SciPy DOP853, 허용오차, solver/result digest와 면적기준 기·액상 재고수지를 기록한다. EOS, 응축 생성, pH·반응·공간 구배와 부식률은 계산하지 않는다. [유한 기상/가변 액상 이력](models/WET_CO2_FINITE_GAS_VARIABLE_LIQUID_HISTORY_KO.md).

`integration.crevice_geometry_aware_solid_deposition_provider`는 `solve_crevice_transport_recession_feedback(..., geometry_aware_solid_deposition_provider=...)`에 caller가 계산한 endpoint solid reaction extents, aqueous/solid stoichiometry, initial phase inventory와 Evidence-pinned molar volumes를 제공한다. 반응 extent와 phase volume을 trial aperture 갱신에 반영하고 수용액/고체 재고 closure를 확인한다. 구간 끝에서 반응을 적용하는 operator-split 모델로, Ksp·kinetics·상 선택·형상·고체역학이나 연속적인 침전-수송 동시해석은 추정하지 않는다. [크리비스 고체 deposition provider](models/CREVICE_GEOMETRY_AWARE_SOLID_DEPOSITION_KO.md).

`fabrication.chemical_cleaning_bath_component_inventory`는 caller가 선언한 세정조 액량 및 성분 질량을 순서가 고정된 투입·완전혼합 배출·성분 소비 사건으로 추적한다. 실패 시 해당 사건에서 중단하며 반응, 세정효율, 호환성 또는 폐액 판정은 계산하지 않는다. [세정액 재고 계약](models/CHEMICAL_CLEANING_BATH_COMPONENT_INVENTORY_KO.md).

`mechanics.gasket_nominal_contact_pressure`는 같은 하중 범위로 검토된 gasket 압축 반력과 유효 접촉면적(또는 원환 지름)으로 평균 압력 F/A를 계산한다. 국부 접촉압력, 누설률, 실링 성능 또는 설계 적합성을 추정하지 않는다. [gasket 평균 접촉압력 계약](models/GASKET_NOMINAL_CONTACT_PRESSURE_KO.md).
# 2026-10-31 병렬 구현 후속 API

- `data.bam_cmsx6_creep_lis_typed_rows`: 명시적 로컬 파일 권한과 digest pin을 받은 CMSX-6 LIS를 행·열·원문 숫자 토큰 순서대로 읽습니다. creep 수명 피팅은 하지 않습니다. 입력은 `CMSX6LISReadRequest`, 출력은 `CMSX6LISTypedRow`입니다. [reader 계약](data/BAM_CMSX6_CREEP_LIS_READER_KO.md).
- `chemistry.aqueous_extended_debye_huckel_activity`: 온도·용매·이온강도 적용 범위 안에서 사용자가 Evidence와 함께 제공한 A/B 및 이온 크기 파라미터로 단일 이온 활동도 계수를 계산합니다. 계수 표를 내장하지 않으며 완전한 speciation이나 부식률을 계산하지 않습니다. [모델 범위](models/EXTENDED_DEBYE_HUCKEL_ACTIVITY_KO.md).
- `fatigue.wang_brown_reviewed_excursion_parameter`: 사용자가 고른 유한 방향 평면과 검토된 reversal arc의 shear half-range 및 보정된 normal-strain excursion을 결합한 매개변수입니다. cycle counting, 수명 환산, 재료 qualification은 포함하지 않습니다. [모델 범위](models/wang_brown_excursion_parameter.md).
- `integration.lh2dt_dynamic_network_node_state_history`: revision·구성·결과 digest가 고정된 LH2DT 동적 네트워크 결과에서 지정 node의 유체 열역학 상태만 건전성 도구로 전달합니다. 벽 상태, 재료 응답, 수소 손상은 추론하지 않습니다. [어댑터 계약](models/LH2DT_DYNAMIC_NETWORK_NODE_STATE_ADAPTER_KO.md).
# Extended Debye–Hückel 자기일관 speciation

`chemistry.aqueous_extended_debye_huckel_self_consistent_speciation`는 caller가 선언한 수용액 mass-action 종·반응·제약을 고정 activity 계수로 풀고, 조성에서 계산한 이온강도로 extended Debye–Hückel 계수를 다시 계산하는 감쇠 고정점 반복이다. 종/반응 자동 생성, 상 선택, 침전, 부식률은 수행하지 않는다. A/B, 용매·온도 범위, 이온 크기, 물 질량 환산과 모든 반응 자료는 Evidence-bound caller 입력이다. [계산 범위와 제한](models/EXTENDED_DEBYE_HUCKEL_SELF_CONSISTENT_KO.md).

`build_extended_debye_huckel_transport_activity_callback()`은 같은 caller request에서 restricted transport 용 `gamma_m` callback을 만든다. 각 위치의 완전한 caller composition, molal ionic strength와 charge closure를 확인하고, support를 벗어난 local state는 거절한다. 이 함수는 transport flux를 풀거나 local species/reactions를 추론하지 않는다.
# 2026-10-31 병렬 구현 API 증분

- `chemistry.aqueous_extended_debye_huckel_self_consistent_speciation`: caller 질량작용계에 조성 의존 extended Debye–Hückel 활동도 반복을 연결한다. A/B·이온 크기·수온·용매·전하/재고 범위와 standard-state mapping은 검토된 caller 입력만 사용한다. [범위](models/EXTENDED_DEBYE_HUCKEL_SELF_CONSISTENT_KO.md).
- `chemistry.co2_henry_vant_hoff_temperature_correction`: caller가 제공한 CO₂* Henry 계수를 용해 엔탈피와 선택 열용량 변화로 온도 보정한다. 용해도 계수 외의 fugacity/speciation/부식은 계산하지 않는다. [범위](models/CO2_HENRY_VANT_HOFF_KO.md).
- `integration.co2_henry_temperature_to_fixed_fugacity_carbonate`: digest 일치, 온도·용매·단위·coefficient convention 검토가 끝난 Henry 보정 결과만 기존 탄산염 부분계 fixed-fugacity 평형으로 넘긴다. 전체 수용액 speciation이나 부식률은 아니다. [범위](models/CO2_HENRY_CARBONATE_ADAPTER_KO.md).
- `integration.co2_henry_temperature_to_fixed_fugacity_carbonate_history`: exact ordered time knot마다 검증된 Henry 보정 결과를 탄산염 부분계 평형으로 전달하고 첫 실패에서 prefix를 보존한다. inter-knot 보간·외삽은 하지 않는다. [범위](models/CO2_HENRY_CARBONATE_HISTORY_ADAPTER_KO.md).
- `fatigue.itoh_nonproportional_strain_parameter`: 검토된 한 주기의 유한 변형률 표본과 caller 재료 보정계수로 비비례 경로 변형률 파라미터를 계산한다. cycle count·수명·손상누적은 하지 않는다. [범위](models/ITOH_NONPROPORTIONAL_STRAIN_PARAMETER_KO.md).
- `fatigue.itoh_nonproportional_strain_life`: digest-bound Itoh 변형률 파라미터를 동일 재료·변형률 기준의 caller strain-life curve에 연결하고 support 내부에서만 log-log 보간한다. cycle counting이나 Miner 누적은 하지 않는다. [범위](models/ITOH_NONPROPORTIONAL_STRAIN_LIFE_KO.md).
- `fatigue.itoh_nonproportional_miner_blocks`: caller cycle block마다 Itoh 수명을 재계산하고 모든 블록이 같은 재료·strain definition·계수·licensed curve를 공유할 때만 기존 Miner rule로 누적한다. [범위](models/ITOH_NONPROPORTIONAL_MINER_BLOCKS_KO.md).
- `fabrication.gasket_multi_bolt_sector_equilibrium`: 다중 인장 볼트와 압축 가스켓 구역의 caller 힘-압축 입력을 사용해 각 지정 load knot에서 공통 축방향 개구 평형을 푼다. 플랜지 굽힘·누설·수용성 판정은 추론하지 않는다. [범위](models/GASKET_MULTI_BOLT_SECTOR_EQUILIBRIUM_KO.md).
- `fabrication.gasket_evidence_bound_prony_history`: 기존 generalized-Maxwell 가스켓 이력 계산에 parameter/source/material-condition Evidence, license ID와 검토된 온도 support를 더한다. 계산식 자체를 재적합하지 않는다. [범위](models/GASKET_EVIDENCE_BOUND_PRONY_HISTORY_KO.md).
- `fatigue.dang_van_finite_parameter_life`: 유한표본 Dang Van-style screen 결과를 같은 재료 조건의 caller 실험 수명 곡선에 log-log 보간하며 support 바깥은 거절한다. 보편 수명 법칙이나 Miner 누적은 아니다. [범위](models/DANG_VAN_FINITE_PARAMETER_LIFE_KO.md).
- `integration.wet_co2_carbonate_transport_boundary_history`: 검증된 탄산염 이력의 exact knot마다 caller가 Evidence로 고정한 탄산염 분배 가정으로 수송 경계 조성을 만든다. 연속 보간·전체 용액 speciation·전하 균형 추론은 하지 않는다. [범위](models/WET_CO2_CARBONATE_TRANSPORT_HISTORY_KO.md).
- `integration.multi_bolt_joint_to_flange_contact_request`: digest 고정 다중 볼트 힘과 caller의 볼트-접촉 절점 영향행렬로 기존 플랜지 접촉 solver용 typed request를 만든다. 영향행렬/선형중첩은 사용자가 제공하고 근거로 고정한다. [범위](models/MULTI_BOLT_FLANGE_CONTACT_INFLUENCE_KO.md).
- `integration.gasket_joint_spatial_resultant_balance`: 같은 시각의 다중 볼트 및 플랜지 접촉 결과를 연결해 축력·모멘트 평형 잔차, 접촉력 중심, 이산 접촉면 지표를 계산한다. 국부 응력이나 누설 판정은 하지 않는다. [범위](models/GASKET_JOINT_SPATIAL_RESULTANTS_KO.md).
- `integration.wet_co2_finite_gas_wall_reaction_inventory_history`: 유한 기상·액상 CO₂* 재고를 caller 반응량론 및 digest 고정 전기화학 금속손실 이력과 operator-split 결합해 이력 적분한다. 동시 반응 kinetics나 외부 유동을 추론하지 않는다. [범위](models/WET_CO2_WALL_REACTION_COUPLED_HISTORY_KO.md).
- `fatigue.wang_brown_parameter_life_fit`: 유한 경로 parameter와 동일 재료조건의 caller 정진폭 수명자료를 log-log power law로 적합하고, 관측 parameter 구간 안에서만 수명을 계산한다. 가변진폭 손상이나 재료 전이는 추론하지 않는다. [범위](models/WANG_BROWN_PARAMETER_LIFE_FIT_KO.md).
- `fabrication.gasket_bolt_cyclic_damage`: caller가 선언한 gasket-joint 반복 이력의 볼트별 명목 인장응력에 rainflow, 동일조건 Basquin/Goodman 자료와 Miner 합산을 적용한다. 국부 응력·부식효과·누설·수명 qualification은 제공하지 않는다. [범위](models/GASKET_BOLT_CYCLIC_DAMAGE_KO.md).
- `transport.crevice_component_diffusion_1d`: caller가 정의한 단일 용존 성분의 1차원 고정 형상 간극 확산을 backward-Euler 유한체적으로 풀고 경계·생성·재고 질량수지를 보고한다. 전기이동·speciation·반응·간극 변화는 포함하지 않는다. [계산 경계](CREVICE_COMPONENT_DIFFUSION_KO.md).
- `fabrication.gasket_circumferential_contact_continuity`: 사용자 압력 기준과 ring geometry에 따라 절점 주위의 원주 방향 threshold coverage 및 연속 open-arc 길이를 이산적으로 계산한다. 누설 또는 seal acceptance를 판정하지 않는다. [범위](models/GASKET_CIRCUMFERENTIAL_CONTACT_CONTINUITY_KO.md).
- `integration.wet_co2_film_transport_limited_mixed_potential`: carbonate 경계의 caller 검토 농도와 Butler–Volmer 반응에 steady Fick 막 공급 상한을 걸고 제한 혼합전위를 푼다. 전체 speciation이나 시간변화 부식 kinetics는 포함하지 않는다. [범위](models/WET_CO2_TRANSPORT_LIMITED_MIXED_POTENTIAL_KO.md).
- `integration.wet_co2_finite_gas_multispecies_wall_flux_history`: 유한 CO₂ 기상재고와 CO₂* 용액재고를 Henry·2막 전달식으로 연결하고, 다른 용액종과 caller 벽면 flux를 독립 재고로 적분한다. 종분포·전하 균형·반응 kinetics는 추론하지 않는다. [범위](models/WET_CO2_MULTISPECIES_FINITE_INVENTORY_HISTORY_KO.md).
- `fatigue.multiaxial_crossland_proportional_limit_screen`: finite 응력 텐서 경로가 caller tolerance 안에서 비례하중인지 먼저 검사하고, caller Crossland 계수로 J2 편차진폭과 최대 정수압을 결합해 한도 screen을 수행한다. 비례가 아니거나 caller 보정 support가 맞지 않으면 계산하지 않는다. [범위](models/CROSSLAND_PROPORTIONAL_LIMIT_SCREEN_KO.md).
- `fatigue.multiaxial_deviatoric_stress_path_variation`: 닫힌 유한 텐서 경로에서 인접 표본의 `sqrt(J2)` 편차응력 거리합과 정수압 변동량을 계산한다. 경로 기술량이며 손상·수명으로 변환하지 않는다. [범위](models/MULTIAXIAL_DEVIATORIC_PATH_VARIATION_KO.md).
- `integration.wet_co2_scale_corrosion_moving_geometry_history`: 각 exact interval에서 현재 scale thickness로 막수송 제한 혼합전위를 재계산하고 caller 금속손실·scale yield/flux를 순차 적산한다. 구간 내부 동시 feedback, scale morphology/보호효과는 추론하지 않는다. [범위](models/WET_CO2_SCALE_CORROSION_COUPLED_HISTORY_KO.md).
- `fabrication.gasket_contact_distribution_statistics`: digest-pinned 접촉 이력의 유한 node areas로 압력의 면적가중 moments·quantiles·caller threshold 미달 면적률을 계산한다. 누설·seal acceptance는 판정하지 않는다. [범위](models/GASKET_CONTACT_DISTRIBUTION_STATISTICS_KO.md).
- `fatigue.crossland_proportional_miner_campaign`: caller가 선언한 비례하중 블록 횟수와 동일 조건의 Crossland parameter–수명 곡선을 연결해 블록별 수명·Miner 손상과 반복 단위를 산출한다. 사이클 계수, 곡선 외삽, 순서효과 및 자격 수명은 제공하지 않는다. [범위](models/CROSSLAND_PROPORTIONAL_MINER_CAMPAIGN_KO.md).
- `integration.wet_co2_transient_gas_carbonate_alkalinity_equilibrium`: 유한 기상 재고·변화 액상 부피·DIC·총알칼리도를 적분하면서 caller 조건부 탄산 평형을 갱신한다. 비이상 활동도, 완전 전해질 종분포와 부식 kinetics는 포함하지 않는다. [범위](models/WET_CO2_TRANSIENT_CARBONATE_GAS_EQUILIBRIUM_KO.md).
- `fabrication.gasket_contact_subthreshold_exposure`: digest-pinned 접촉 압력 이력과 caller 기준압을 비교해 절점 면적의 기준 미달 시간 적분과 압력 부족량을 계산한다. 누설률이나 씰 합격은 판정하지 않는다. [범위](models/GASKET_CONTACT_SUBTHRESHOLD_EXPOSURE_KO.md).
- `integration.wet_co2_gas_film_condensation_transfer_history`: caller fugacity와 기체막 전달계수로 벽 응축·증발량을 고정 면적 재고로 적산하고 증발량은 가용 액막 재고로 제한한다. 잠열·염수 활동도·기체 고갈과 부식은 계산하지 않는다. [범위](models/WET_CO2_GAS_FILM_CONDENSATION_TRANSFER_HISTORY_KO.md).
- `transport.crevice_electroneutral_multispecies_diffusion_1d`: 고정 형상 1차원 간극에서 caller 다종 이온 경계와 수송계수를 사용해 Nernst–Planck 유한체적 수송을 계산하고 국부 영전류 전위 기울기를 닫는다. 대류·반응·비이상 활동도는 포함하지 않는다. [범위](models/CREVICE_ELECTRONEUTRAL_DIFFUSION_KO.md).
- `integration.crevice_activity_gradient_nernst_planck_flux_1d`: caller가 제공한 단일 이온 활동도계수의 로그 기울기를 포함해 간극 한 면의 대류-확산 플럭스를 계산하고 국부 영전류 전위 기울기를 닫는다. 활동도계수 생성, speciation, 공간 적분은 포함하지 않는다. [범위](models/CREVICE_ACTIVITY_GRADIENT_FLUX_KO.md).
- `transport.crevice_activity_corrected_nernst_planck_1d`: caller 시간·셀별 활동도계수 장을 사용해 고정 격자 간극 이온 재고를 유한체적 적분한다. 입구 경계, blind-tip 무플럭스, 국부 영전류 및 inventory/charge 진단을 보존한다. [범위](models/CREVICE_ACTIVITY_CORRECTED_TRANSPORT_KO.md).
- `chemistry.crevice_activity_based_reaction_rates`: caller가 제공한 단일 이온활동도 상태와 균형 반응 parameter로 전·역 mass-action 속도 및 종별 source term을 계산하고 `kf/kr=K`를 검사한다. [범위](models/CREVICE_ACTIVITY_REACTION_RATES_KO.md).
- `transport.crevice_activity_corrected_reactive_nernst_planck_1d`: 비이상 활동도 보정 전기이동과 caller 가역 반응의 국소 mass-action kinetics를 고정 격자 finite-volume BDF 상태로 함께 적분한다. phase equilibrium, 자동 speciation, 벽반응은 포함하지 않는다. [범위](models/CREVICE_ACTIVITY_CORRECTED_REACTIVE_TRANSPORT_KO.md).
- `validation.crevice_repassivation_margin_history`: 정확히 일치하는 재료·환경·온도·기준전극의 관측 전위와 재부동태 threshold 사이 signed margin과 불확도대 분류를 계산한다. 위험확률/부식예측은 아니다. [범위](models/CREVICE_REPASSIVATION_MARGIN_KO.md).
- `validation.crevice_repassivation_excursion_duration_history`: 정확 매칭 margin 절점 사이에서 불확도 band를 기준으로 확정/가능/미해결 초과 지속시간을 요약한다. 구간 내부 crossing 시각·연속 상태·확률은 추정하지 않는다. [범위](models/CREVICE_REPASSIVATION_MARGIN_KO.md).
- `chemistry.crevice_competing_solid_equilibrium`: 하나의 고정 액상 상태와 caller가 열거한 중성 순수 고체 후보들의 평형 조성을 제한된 순차 active-set 반복으로 구한다. 각 상의 element/charge balance와 존재/부재 포화도 보완조건을 확인하며, 자동 speciation·상 발견·kinetics·전역 안정성은 포함하지 않는다. [입력·계산 경계](models/CREVICE_COMPETING_SOLID_EQUILIBRIUM_KO.md).
- `integration.wet_co2_cylindrical_steady_hydraulics`: caller 단상 유량·물성 및 원통 bore 이력으로 Darcy 마찰, 벽 전단과 구간 압력손실을 계산한다. 천이 Reynolds 구간에서는 계산을 중단한다. [범위](models/WET_CO2_CYLINDRICAL_STEADY_HYDRAULICS_KO.md).
- `integration.wet_co2_cylindrical_hydraulics_to_scale_removal`: 원통형 hydraulics 결과의 벽 전단 크기를 기존 caller 보정 scale 제거 요청에 연결하고 부호와 digest 계보를 보존한다. [범위](models/WET_CO2_CYLINDRICAL_HYDRAULICS_TO_SCALE_REMOVAL_KO.md).
- `integration.wet_co2_cylindrical_liquid_transfer_capacity_history`: 원통형 hydraulics와 caller 확산계수 이력을 기존 액상 물질전달 상관식에 연결해 축방향 구간의 벽-벌크 전달용량 노출량을 계산한다. [범위](models/WET_CO2_CYLINDRICAL_LIQUID_TRANSFER_CAPACITY_KO.md).
- `integration.wet_co2_cylindrical_finite_liquid_transfer_inventory`: 전달용량과 caller 농도/액량 history를 두 유한 액상 구획의 이송 및 외부재고 변화로 연결하고 재고·질량수지 폐쇄를 확인한다. [범위](models/WET_CO2_CYLINDRICAL_FINITE_LIQUID_TRANSFER_INVENTORY_KO.md).
- `integration.wet_co2_finite_inventory_saturation_scale_geometry`: 유한 액상 재고의 벽 활동도·포화도와 caller scale kinetics를 단일 선택 상의 aqueous/solid 재고수지 및 원통 geometry 갱신에 연결한다. [범위](models/WET_CO2_FINITE_INVENTORY_SATURATION_SCALE_GEOMETRY_KO.md).
- `integration.wet_co2_finite_inventory_electrode_mixed_potential`: 두 유한 액상 구획의 species 재고를 caller Butler–Volmer 분기와 혼합전위 폐쇄에 연결하고, 벽 재고 한계·외부 교환·부피 이력을 추적한다. lumped 모델이며 공간 PDE는 아니다. [범위](models/WET_CO2_FINITE_INVENTORY_ELECTRODE_MIXED_POTENTIAL_KO.md).
- `integration.wet_co2_cylindrical_spatial_mixed_potential`: 원통 액막의 방사 유한체적 농도장과 caller BV 가지의 공통 영전류 전위를 함께 적분한다. 고정 절점 형상에 대한 과도 계산이며 내부 geometry feedback은 아니다. [범위](models/WET_CO2_CYLINDRICAL_SPATIAL_MIXED_POTENTIAL_KO.md).
- `chemistry.wet_co2_neutral_solid_formula_proposals`: caller 선언 양이온·음이온의 전하와 원소식을 사용해 중성 이성분 조성 후보를 유한 열거한다. 상 존재·Ksp·안정도·침전은 판단하지 않는다. [범위](models/WET_CO2_NEUTRAL_SOLID_FORMULA_PROPOSALS_KO.md).
- `integration.wet_co2_cylindrical_shear_limited_scale_removal`: 원통형 확산 제한 scale 성장 장부에 caller가 보정한 벽 전단 임계 제거법칙을 operator-split 후처리로 적용하고 유한 상 재고로 제거량을 제한한다. [범위](models/WET_CO2_CYLINDRICAL_SHEAR_LIMITED_SCALE_REMOVAL_KO.md).
- `fatigue.multiaxial_sines_parameter_life`: 기존 Sines형 유한표본 screen을 동일 재료조건의 caller 수명곡선에 연결해 지지구간 안에서만 수명을 보간한다. 사이클 계수, 가변진폭 누적 및 재료 qualification은 하지 않는다. [범위](models/MULTIAXIAL_SINES_PARAMETER_LIFE_KO.md).
- `integration.crevice_neutral_reactive_transport_1d`: 고정 형상 1차원 blind-tip 간극에서 중성종의 유한체적 확산과 caller 가역 mass-action 반응을 BDF 시간적분으로 결합한다. 이온·대류·벽면반응·부식률은 포함하지 않는다. [범위](models/CREVICE_NEUTRAL_REACTIVE_TRANSPORT_1D_KO.md).
- `fatigue.multiaxial_sines_life_fit`: caller 검토 완료된 동일조건 Sines 시험 자료에서 로그-로그 수명식을 적합한다. 독립 검증, runout 처리, 외삽과 파손확률은 제공하지 않는다. [범위](models/MULTIAXIAL_SINES_LIFE_FIT_KO.md).
- `integration.wet_co2_finite_gas_water_condensation_history`: 유한 기상 수증기 재고와 벽 액막 교환을 구간상수 조건에서 지수해로 적분하고 dryout 및 기체·액막 재고수지를 계산한다. 염수 활동도·열수지·부식률은 포함하지 않는다. [범위](models/WET_CO2_FINITE_GAS_WATER_CONDENSATION_KO.md).
- `fatigue.j2_armstrong_frederick_strain_history`: caller 계수로 단일 Armstrong–Frederick backstress를 적용한 J2 소변형률 소성 응답을 각 공급 변형률 구간에 대해 계산한다. 다중 backstress, 자동 시간 세분화와 피로수명은 포함하지 않는다. [범위](models/J2_ARMSTRONG_FREDERICK_HISTORY_KO.md).
- `integration.wet_co2_lumped_wall_thermal_condensation_history`: 벽 온도와 유한 기상 수증기·액막 재고를 포화 fugacity 및 외부/현열/잠열과 함께 DOP853으로 적분한다. 포화 자료 지지구간 밖은 거부하며 염수 활동도와 부식은 모델링하지 않는다. [범위](models/WET_CO2_LUMPED_WALL_THERMAL_CONDENSATION_KO.md).
- `integration.crevice_spatial_ohmic_mixed_potential`: 고정된 간극 절점에서 caller Butler–Volmer 반응 분포와 전해질 ohmic 저항을 결합해 전위·전류 분포를 푼다. 종 수송, 용액 speciation, 전극 충전과 금속 저항은 포함하지 않는다. [범위](models/CREVICE_SPATIAL_OHMIC_MIXED_POTENTIAL_KO.md).
- `integration.wet_co2_scale_corrosion_simultaneous_history`: 각 구간 적분 중 scale 두께에 따라 film 전달한계와 혼합전위를 다시 풀고 금속손실·scale 재고·벽 후퇴를 동시 갱신한다. 주어진 반응/전달 입력을 사용하며 PDE, 유체 검증, 독립 부식 qualification은 제공하지 않는다. [범위](models/WET_CO2_SCALE_CORROSION_SIMULTANEOUS_KO.md).
- `fabrication.gasket_prony_temperature_shift_history`: caller Arrhenius 또는 WLF 이동법칙으로 기존 Prony 시간축을 reduced time으로 변환해 generalized-Maxwell 응답을 계산한다. modulus 이동·열수지·접촉·누설 판정은 포함하지 않는다. [범위](models/GASKET_PRONY_TEMPERATURE_SHIFT_HISTORY_KO.md).
- `integration.crevice_spatial_ohmic_partial_current_metal_loss`: 계산된 공간 혼합전위의 digest-pinned branch 전류 이력 중 용해 branch 양극 전류만 구간 적분해 Faraday 등가 금속손실과 고정 셀 균일 후퇴량으로 변환한다. 재석출·공식 부식률 qualification·국부 피팅형상은 포함하지 않는다. [범위](models/CREVICE_SPATIAL_OHMIC_METAL_LOSS_KO.md).
- `integration.crevice_current_carrying_np_faradaic`: 가변 단면적 활동도 보정 Nernst–Planck 수송의 이온 면전류를 공간 혼합전위와 연결하고, 별도 Faradaic 벽 종원 및 정확 절점 수용액·고체 화학을 반복해 수렴 구간만 커밋한다. 기본 `endpoint_trapezoid`는 구간 후단 source 적용을 유지한다. 검토 gate가 있는 `bdf_stage_linear_current`는 절점 혼합전위 가지전류를 선형 보간해 BDF stage 안에서 종 source·extent를 적분한다. `bdf_stage_spatial_mixed_potential`은 각 BDF RHS에서 시험 농도와 caller 공급 형상·전도도·Nernst 입력으로 공간 ohmic/Butler–Volmer 혼합전위를 다시 풀고 그 Faradaic source를 적분한다. 추가 선택 `bdf_stage_bdot_activity_by_interval`은 구간마다 Evidence-bound B-dot parameter 요청을 받고 같은 stage 계수를 Nernst–Planck, 활동도 기반 반응 속도, Nernst/BV 계산에 공유한다. 이 B-dot 옵션은 기존 공간 BDF mode와 review gate가 필요하며 별도 평가 budget과 요청 digest를 기록하지만, 질량작용 종분화나 고체상 평형을 풀지 않는다. 후자도 이중층 전하 저장을 모델링하지 않으며, 평형 화학·상 검색은 절점 경로에 남는다. 전류·전하·원소 장부가 닫히지 않으면 실패한다. [범위](models/CREVICE_CURRENT_CARRYING_NP_FARADAIC_KO.md).
- `integration.crevice_aqueous_component_ledger`: caller 입력의 시작/종료 종 몰수, face 전달량과 cell source를 명시적으로 역할 지정된 conserved-component basis로 선형 투영하고 셀·경계·전역 수지 잔차를 계산한다. 모든 mass-action 제약은 `conserved_component`/`fixed_target`/`charge_neutrality` 중 하나로 분류되어야 하며, charge row와 component reaction balance를 정확히 검토한다. 이 API는 ledger projection 선행 경로이며 기존 BDF state, 평형 chemistry 또는 transport를 풀지 않는다. [모델 범위](models/CREVICE_AQUEOUS_COMPONENT_LEDGER_KO.md).
- `chemistry.crevice_closed_batch_aqueous_equilibrium`: 초기 종별 몰수와 고정 액상 부피에서 보존 성분 제약 목표를 구성해 기존 Davies 자기일관 질량작용 solver를 호출하고, 최종 성분 재고 폐합을 확인한다. 용액상 닫힌 batch에 한정되며 고체/기체상·수송·Crevice BDF 연성은 계산하지 않는다. [모델 범위](models/CREVICE_CLOSED_BATCH_AQUEOUS_EQUILIBRIUM_KO.md).
- `integration.crevice_component_state_bdf`: 셀별 보존 성분 몰수를 BDF 상태로 적분하고 매 trial stage의 caller Davies 평형에서 종 농도·활동도를 재구성한다. 내부면 Nernst–Planck 확산 flux는 caller diffusivity/geometry 및 기본 대수적 0 이온전류 조건을 사용해 성분 inventory flux로 투영한다. 선택형 signed reaction-extent source schedule은 정확 절점별·셀별 caller history를 선형 시간 보간하고, 보존 성분 상태 및 외부 reservoir 원소/성분 ledger에 투영한다. 비영 순전하 source에는 같은 knot 시간과 face 배열을 가진 검토된 caller ionic-current schedule이 필요하며, 모든 셀에서 `I_right - I_left = F Σ(z_i ν_i r_i)`를 검사한다. 전류는 경계에서 0이고 caller 제공값이다. solver는 NP migration gradient를 지정 interior current에 맞추며 잔차를 A로 확인한다. 이 API는 혼합전위/BV에서 전류를 유도하지 않는다. 고정 부피·닫힌 경계 child solver이며 고체상·유동은 범위 밖이다. [모델 범위](models/CREVICE_COMPONENT_STATE_BDF_KO.md).
- `integration.crevice_component_state_faradaic_schedule_binding`: digest가 맞고 모든 interval이 commit된 `integration.crevice_current_carrying_np_faradaic` 결과에서 exact-knot ionic face current와 branch current density를 추출해 component-state BDF용 source-rate/current schedule을 만든다. producer/component cell 순서, species 순서·전하, exact times와 초기 conserved-component inventories를 대조한다. per-cell branch extent rate는 producer의 declared reactive area와 electron number로 계산하며, source element/component/charge reservoir ledger를 만든다. endpoint current reconstruction과 cell/physical mapping은 명시적 caller review가 필요하다. within-stage mixed-potential 결과를 endpoint history로 축약하지 않도록 해당 producer mode는 거절한다. 이 어댑터는 순차 연결이며 component BDF 내부 화학에서 BV current를 다시 풀지 않는다. [모델 범위](models/CREVICE_COMPONENT_STATE_FARADAIC_BINDING_KO.md).

입력 구조만 확인하려면 [합성 닫힌 batch 초안](../examples/crevice_closed_batch_aqueous_equilibrium.py)을 참고한다. 이 파일은 증거·검토·계산 승인 필드를 모두 `false`로 둔 미승인 JSON 초안을 출력하며 Pydantic 계약 검증이나 계산기를 호출하지 않는다.
- `integration.crevice_current_carrying_aperture_feedback`: caller가 제공한 고체 부피-개구 및 개구-면속도 민감도를 적용해 전체 current-carrying 수송·Faradaic·절점 화학 경로를 반복 재계산하고, geometry와 hydraulic 잔차가 모두 수렴할 때만 시간 이력을 커밋한다. 구간 내부는 knot geometry 선형 보간이며 BDF stage마다 형상을 연속 갱신하지 않는다. [범위](models/CREVICE_CURRENT_CARRYING_APERTURE_FEEDBACK_KO.md).
- `integration.crevice_current_carrying_extent_to_metal_loss`: 완료·digest 고정된 current-carrying CREVICE의 이미 적분된 반응 extent를 caller 금속 화학량론·몰질량·밀도·셀 반응면적으로 금속 몰수/질량/부피/균일 감육으로 변환한다. 전류를 재적분하지 않으며, 결과의 셀별 부피 장부는 기존 `integration.electrochemical_metal_loss_to_crevice_geometry`에 직접 전달할 수 있다. branch 처분·물성·분배는 caller 검토가 필요하다. [범위](models/CREVICE_CURRENT_CARRYING_EXTENT_METAL_LOSS_KO.md).
- `fabrication.gasket_prony_relaxation_spectrum_fit`: caller step-strain relaxation 자료에 유한 generalized-Maxwell 스펙트럼을 가중 비선형 적합하고, caller modulus/time bounds와 자료 계보를 보존한다. 유일한 재료상수·독립 검증·온도전이·누설 qualification은 주장하지 않는다. [범위](models/GASKET_PRONY_RELAXATION_SPECTRUM_FIT_KO.md).
- `integration.crevice_transport_to_local_mass_action`: 계산된 수송장 각 셀·절점의 caller 지정 농도를 명시적 mol/L constraint에 연결해 기존 aqueous mass-action solver를 독립 적용하고 cell inventory를 기록한다. 반응망 생성·수송 feedback·phase 선택은 추론하지 않는다. [범위](models/CREVICE_TRANSPORT_LOCAL_MASS_ACTION_KO.md).
- `integration.crevice_ionic_reactive_transport_1d`: caller 면 속도 이력, 희석 Nernst–Planck 영전류 수송과 전하·원소 보존 가역 질량작용 반응을 고정 격자에서 공동 적분한다. 유동장 생성, 활동도·상평형, 벽 반응 및 금속 손실은 범위 밖이다. [범위](models/CREVICE_IONIC_REACTIVE_TRANSPORT_KO.md).
- `fabrication.gasket_bolt_nominal_strength_screen`: upstream 다중 볼트 평형 결과의 명목 축응력을 caller가 제공한 온도별 proof-strength 선형 보간값과 비교한다. 설계 코드 허용성, 국부 응력 및 qualification은 추론하지 않는다. [범위](models/GASKET_BOLT_NOMINAL_STRENGTH_SCREEN_KO.md).
- `integration.gasket_leakage_pressure_inventory_decay`: caller가 보정한 gasket 누설 이력과 고정 체적 이상기체 재고 수지를 연결해 압력 이력을 계산한다. 접촉/누설의 압력 피드백과 등온·고정체적 가정 검증은 범위 밖이다. [범위](models/GASKET_PRESSURE_INVENTORY_DECAY_KO.md).
- `integration.wet_co2_scale_diffusion_electrode_mixed_potential`: 고정 scale 층의 1D 정상 확산·1차 소모를 공통 mixed-potential 전극 반응과 결합한다. 매개변수와 반응 가지는 caller 입력이며 동적 scale 성장·검증된 부식률은 제공하지 않는다. [범위](models/WET_CO2_SCALE_DIFFUSION_ELECTRODE_KO.md).
- `fatigue.multiaxial_mcdiarmid_finite_plane_limit_screen`: 유한한 caller 응력 표본과 후보면에서 McDiarmid 지수를 산출하는 제한 스크린이다. 표본 간 최대화, 연속 평면 수렴 또는 피로수명은 추론하지 않는다. [범위](models/MULTIAXIAL_MCDIARMID_LIMIT_SCREEN_KO.md).
- `fatigue.mcdiarmid_calibrated_miner_campaign`: 해당 스크린 지수를 caller 보정 지수–수명 곡선에 연결하고 순서가 있는 하중 블록의 Miner 누적을 계산한다. 블록 상호작용과 수명 qualification은 범위 밖이다. [범위](models/MCDIARMID_MINER_CAMPAIGN_KO.md).
- `fabrication.gasket_radial_open_path_screen`: annular 접촉압력 격자의 caller 임계압력 이하 셀에서 각도 주기 경계를 포함한 4-이웃 연결과 반경 방향 병목 경로를 평가한다. 누설량이나 밀봉 적합성은 계산하지 않는다. [범위](models/GASKET_RADIAL_OPEN_PATH_KO.md).
- `fabrication.gasket_compression_hysteresis_energy`: caller가 측정한 힘–변위 loop를 사다리꼴 경로 적분으로 요약해 루프 일과 에너지 손실 지표를 제공한다. 재료 구성식, 손상 법칙, 밀봉 적합성은 추론하지 않는다. [범위](models/GASKET_COMPRESSION_HYSTERESIS_ENERGY_KO.md).
- `fabrication.gasket_temperature_compression_curve_transfer`: 동일 시편 조건·변형률 격자의 두 온도 압축 곡선 사이를 보간해 caller 목표온도 loading branch를 만든다. 측정 온도 구간 밖 외삽이나 언로딩/점탄성 응답은 계산하지 않는다. [범위](models/GASKET_TEMPERATURE_COMPRESSION_CURVE_KO.md).
- `integration.gasket_temperature_compression_joint_history`: 보간된 가스켓 온도별 압축곡선을 caller 볼트 preload·강성 및 자유 열변형 이력과 함께 사용해 순차적인 축방향 조인트 평형을 계산한다. 접촉비선형의 공간해석과 압력 의존 누설 연동은 범위 밖이다. [범위](models/GASKET_TEMPERATURE_COMPRESSION_JOINT_HISTORY_KO.md).
- `integration.gasket_thermoelastic_expansion_joint_history`: caller 부품별 CTE(T) 표를 기준온도부터 적분해 볼트 자유길이·가스켓 자유두께 열변형을 만들고 기존 온도 조인트 solver에 전달한다. CTE 외삽, 열전달과 비선형 온도장 해석은 범위 밖이다. [범위](models/GASKET_THERMOELASTIC_EXPANSION_JOINT_HISTORY_KO.md).
- `integration.gasket_joint_equilibrium_local_covariance`: multi-bolt 조인트 평형 API의 선택한 하중·자유팽창 좌표를 central finite difference로 선형화해 caller 공분산을 출력 공분산으로 전파한다. 전역 불확실도, 접촉상태 전이와 파손확률은 계산하지 않는다.
- `fatigue.multiaxial_calibration_transfer_audit`: 동일 caller 피로매개변수 수준에서 기준·대상 재료의 짝지은 수명비를 가중 로그공간 통계로 요약한다. 곡선 이전·외삽과 수명 예측은 하지 않는다. [범위](models/MULTIAXIAL_CALIBRATION_TRANSFER_AUDIT_KO.md).
- `fatigue.multiaxial_power_law_life_transfer`: 짝지은 finite audit 결과에서 caller 참조 수명 곡선의 exact shared parameter knots에 한해 가중 log-linear transfer를 적용한다. knot 밖 외삽이나 재료 법칙 qualification은 하지 않는다. [범위](models/MULTIAXIAL_POWER_LAW_LIFE_TRANSFER_KO.md).
- `fabrication.gasket_bolt_preload_sequence_redistribution`: caller 교정 볼트 상호작용 행렬과 조임 순서를 선형 중첩해 볼트별 최종 preload 분포를 계산한다. 비선형 플랜지, 마찰 slip 및 gasket 접촉응답은 모델링하지 않는다. [범위](models/GASKET_BOLT_PRELOAD_SEQUENCE_REDISTRIBUTION_KO.md).
- `degradation.wet_co2_cylindrical_scale_geometry_history`: caller 금속 벽 후퇴와 상별 scale 선형 몰 재고를 원통 annulus 체적식으로 환산해 내경·벽·scale·bore 면적 이력을 계산한다. 축방향 비균일, 균열 및 수송 해석은 수행하지 않는다. [범위](models/WET_CO2_CYLINDRICAL_SCALE_GEOMETRY_KO.md).
- `integration.wet_co2_cylindrical_transport_mixed_potential`: 원통 scale 내부의 정상 방사 확산 수송과 caller Butler–Volmer 반응을 공통 혼합전위로 닫는다. 이 모듈만으로 transient inventory, phase chemistry나 검증된 부식률을 판단하지 않는다. [범위](models/WET_CO2_CYLINDRICAL_TRANSPORT_MIXED_POTENTIAL_KO.md).
- `integration.wet_co2_cylindrical_transient_transport`: 시간 의존 원통 반경 유한체적 수송을 보수적인 annular 재격자 및 종·원소·전하·합금 수지와 함께 적분한다. 화학 평형/상 자동 선택은 외부 입력이다. [범위](models/WET_CO2_CYLINDRICAL_TRANSIENT_TRANSPORT_KO.md).
- `integration.wet_co2_cylindrical_wall_saturation_scale_kinetics`: transient 원통 벽 인접 농도를 caller 활동도·Ksp 정의에 연결해 기존 단일상 scale law를 호출한다. 종 분화, 고체상 탐색과 수송 feedback은 하지 않는다. [범위](models/WET_CO2_CYLINDRICAL_WALL_SATURATION_SCALE_KINETICS_KO.md).
- `integration.wet_co2_cylindrical_scale_kinetics_to_geometry`: 기존 caller scale-thickness 이력과 상별 molar volume을 원통 기하 evaluator의 길이당 상 재고 입력으로 전달한다. 신규 물성이나 scale kinetics는 추정하지 않는다. [범위](models/WET_CO2_CYLINDRICAL_SCALE_KINETICS_GEOMETRY_KO.md).
- `integration.wet_co2_cylindrical_multilayer_transport_resistance`: 원통 내벽부터 bore까지 scale 층과 용액막의 caller 확산계수로부터 다층 로그 반경 확산저항을 합산한다. 반응·부식률·물성은 추정하지 않는다. [범위](models/WET_CO2_CYLINDRICAL_MULTILAYER_TRANSPORT_KO.md).
- `integration.wet_co2_cylindrical_diffusion_limited_scale_growth`: geometry, 다층 수송저항, caller 포화도와 균형 화학양론을 digest·knot 일치 조건으로 연결해 확산 공급 한계 내 scale 증가·용해 재고를 계산한다. 자동 화학종·고체상 선정은 하지 않는다. [범위](models/WET_CO2_CYLINDRICAL_DIFFUSION_LIMITED_SCALE_GROWTH_KO.md).
- `integration.wet_co2_cylindrical_coupled_scale_geometry_replay`: caller-초기 geometry seed에서 transport·포화도·scale 결과를 bounded Picard 반복으로 재생하고 knot별 inventory 잔차 허용 시에만 수렴 상태를 반환한다. monolithic solve나 qualification은 아니다. [범위](models/WET_CO2_CYLINDRICAL_COUPLED_SCALE_GEOMETRY_REPLAY_KO.md).
- `integration.wet_co2_cylindrical_geometry_coupled_history`: 공간 BV·방사 transient transport를 exact-knot 원통 벽 감육 geometry trial에 반복 연결하고, 반경 고정점과 원소별 벽 재고 수지가 수렴한 뒤 strict solver를 다시 통과해야 결과를 반환한다. scale 몰재고는 caller가 고정 제공하며 독립 validation·동시 scale chemistry는 별도 범위다. [계산·경계](models/WET_CO2_CYLINDRICAL_GEOMETRY_COUPLED_HISTORY_KO.md).
- `fabrication.gasket_compression_curve_monotone_fit`: caller 시험 곡선에 가중 isotonic regression을 적용해 단조 압축 loading curve를 산출한다. 외삽, 재료 law transfer, 이력/수명 적합은 수행하지 않는다. [범위](models/GASKET_COMPRESSION_CURVE_MONOTONE_FIT_KO.md).
- `integration.external_gasket_fe_field_import`: caller 승인된 solver receipt·digest·위치 매핑을 통해 선택한 gasket FE 결과장과 시간 이력을 명시적으로 가져온다. FE 해석, 보간, 응력복구 및 acceptance는 제공하지 않는다. [범위](models/EXTERNAL_GASKET_FE_FIELD_IMPORT_KO.md).
- `integration.gasket_fe_von_mises_caller_limit_screen`: 가져온 6성분 FE 응력텐서를 J2 von Mises 값으로 변환해 caller 한계와 비교한다. 법규 합격 판단이나 안전 qualification은 하지 않는다. [범위](models/GASKET_FE_VON_MISES_CALLER_LIMIT_SCREEN_KO.md).
- `export_ccps_release_history_request`: caller가 입력한 dense-gas 방출 시나리오를 외부 CCPS release-history 요청 계약으로 변환한다. 독립 위험도·피해 해석이나 외부 패키지 결과의 qualification은 이 adapter 범위가 아니다.
- `data.zenodo_316l_polarization_typed_rows`: caller attribution/로컬 이용 허가 아래 Zenodo CC BY 4.0 원시 분극 archive의 time·전위·전류 3열을 공급자 순서로 typed import한다. 전류밀도·부식률이나 피팅 descriptor는 추정하지 않는다. [자료와 경계](datasets/ZENODO_316L_POLARIZATION_TYPED_ROWS_KO.md).
# 추가 계산과 문서 연결

용접 생산 시험의 집계 구간·독립성 처리 1.0.1 변경과 기존 API 확인 범위는 [용접 증거 검증 기록](VALIDATION_WELDING_EVIDENCE_KO.md)을 따른다.

흡수 에너지·전단 파면 비율·횡팽창량의 관측 교차점은 `inspection.impact_metric_crossings`([안내](models/IMPACT_METRIC_CROSSINGS_KO.md))로 계산한다. 충격 캠페인의 반복 시험편 검사는 동일 안내의 1.0.1 변경을 따른다.

조성의 가중 합·곱은 `materials.composition_index_recipe`([안내](models/COMPOSITION_INDEX_RECIPE_KO.md))로 계산한다. 등가 노출 이력의 관측 공백 처리는 [이력 범위 안내](models/AGING_HISTORY_COVERAGE_KO.md)를 따른다.

기존 구조·재료·열 API 12개의 합성 호출 예제는 `examples/reviewed_core_calculations.py`에 있다. 열처리 유지 구간 계산의 1.0.1 수정과 검증 범위는 [묶음 검증 기록](VALIDATION_CORE_MECHANICS_THERMAL_KO.md)을 참조한다.

배관 클래스 정의와 부품 목록은 `design.piping_class_assessment`([안내](models/PIPING_CLASS_KO.md))로 비교한다. 성적서 상위 연결의 1.1.0 변경은 [제품·추적번호 연결 안내](models/CERTIFICATE_CAMPAIGN_IDENTITY_KO.md)를 따른다.

기화량 열유입은 `inspection.boil_off_calorimetry`([안내](models/BOIL_OFF_CALORIMETRY_KO.md)), 사용자 압력 한계 비교는 `design.relief_pressure_envelope`([안내](models/RELIEF_PRESSURE_ENVELOPE_KO.md))로 호출한다. 실행 예제는 `examples/pressure_and_boil_off.py`에 있다.

`testing.rockwell_depth`, `testing.knoop`의 입력 단위·적용 조건은 [깊이·Knoop 경도 안내](models/DEPTH_AND_KNOOP_HARDNESS_KO.md)를 참조한다. 두 API는 공통 registry의 `run`과 `run_json`으로 호출한다.

