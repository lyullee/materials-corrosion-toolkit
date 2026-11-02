# 원통형 wet-CO₂ 부식 감육과 scale 재고 피드백

`integration.wet_co2_cylindrical_scale_recession_feedback`는 caller의 공간 BV/finite-volume aqueous model, 단상 wall saturation/scale kinetics, 원통 다층 확산저항, 상별 반응물 stoichiometry 및 bulk concentration histories를 연결해 제한된 exact-knot feedback 반복을 수행한다. 새 모듈은 각 반복에서 모든 nested evaluator를 다시 실행한다. 계산결과를 포장하는 것만으로 형상과 scale 재고가 변한 것으로 간주하지 않는다.

## 입력 준비

1. 기준 `WetCo2CylindricalSpatialMixedPotential` request를 만든다. `geometry`는 time zero에서 wall recession이 0인 exact-knot history여야 하며, caller가 선택한 모든 scale phase와 molar volume을 포함한다.
2. geometry의 각 phase에 하나씩 `WetCo2CylindricalWallSaturationScaleKinetics`를 준비한다. 그 request의 `candidate_solid_id`, dissolution product formula, kinetic phase ID와 molar volume이 geometry phase와 같아야 한다.
3. 같은 phase마다 `WetCo2CylindricalPhaseGrowthCampaign`를 준비한다. precipitation reactant coefficients는 saturation request의 phase dissolution product coefficients와 일치해야 하고 bulk knots는 geometry time grid와 정확히 맞아야 한다. stoichiometry record digest와 Evidence는 원 ordered coefficient 행을 고정한다.
4. `WetCo2CylindricalMultilayerTransportResistance`는 모든 선언된 scale layer 및 dissolved reactant의 knot별 solid/solution diffusivity를 Evidence와 함께 제공한다.
5. 계산상 phase, activity/Ksp, kinetics, 반응 물질전달 면적 기준, 축대칭 및 공간 BV의 전극/조성 mapping을 독립 검토해 각 review gate를 명시한다.

예를 들어 각 phase campaign의 요청은 이 모듈의 `phase_saturation_kinetics_requests`, `phase_growth_campaigns` dictionary에서 같은 phase ID를 key로 쓴다. 임의 parameter 숫자를 기본값처럼 복사하지 말고 실제 근거를 붙인다. 공개 배포 예제는 raw observation을 포함하지 않는다.

## 계산 순서

각 outer iteration은 아래 순서를 따른다.

1. 현재 steel inner-radius path와 phase별 mol/m inventory path를 새 Evidence-bound geometry history로 만든다. Derived history는 내부 model-prediction source ID를 쓰며 caller provider의 새 측정으로 표시하지 않는다.
2. spatial mixed-potential evaluator를 explicit trial mode로 다시 푼다. Trial 동안 aqueous species, charge, non-alloy element closures, BV calibration support, release 방향과 feasible cylinder 조건은 계속 검사한다. metal element geometry 잔차는 최종 closure까지 보존한다.
3. 각 상의 wall saturation/kinetics evaluator를 같은 trial geometry에서 다시 수행한다. activity coefficients, standard state, Ksp 및 caller surface law는 exact-knot input으로 전달된다.
4. 다층 원통 확산저항을 같은 geometry에서 다시 계산한다. phase별 diffusion-limited scale-growth evaluator는 각 limiting aqueous reactant supply와 caller precipitation/dissolution flux를 비교하고 left-held flux×left-knot inner circumference×interval duration으로 mol/m 재고를 갱신한다.
5. spatial BV의 원소 release에서 target steel surface radius를 구하고, 갱신된 phase inventory 및 molar volume으로 보어 반경을 계산한다. metal-surface, phase inventory, wall element residual 모두 tolerance에 들어온 경우에만 수렴 후보가 된다.
6. 수렴 후보 geometry에서 trial exemption을 끈 strict spatial evaluator를 한 번 더 실행한다. metal wall geometry/release closure가 이 검사에서 실패하면 전체 결과를 computed로 승격하지 않는다.

각 trial digest는 caller request, geometry digest, knot별 steel-radius/phase-inventory 상태와 iteration 번호를 묶는다. 계산 결과에는 nested request/result digests, interval별 phase transfer, 수렴 residual 및 완료 iteration prefix가 남는다. 실패나 반복 한도 초과에서는 마지막 상태를 완성 geometry라고 부르지 않는다.

## 잔차, 보존 및 경계

- **금속 원소 잔차**: 기존 spatial BV model의 초기 벽 원소 재고에서 현재 trial geometry 벽 재고와 BV 방출 누계를 뺀 값이다. element/knot별 절대·상대 tolerance를 확인한다.
- **상 재고 잔차**: caller kinetics의 precipitate/dissolve law와 caller diffusion-supply-limited flux를 적용한 target mol/m에서 trial geometry의 현재 mol/m을 뺀 값이다. 이 phase line inventory는 cylindrical geometry의 annular solid volume에 즉시 반영한다.
- **원통 volume closure**: `pi * (steel_inner_radius**2 - bore_radius**2)`가 모든 caller phase의 `inventory_mol_m * molar_volume` 합과 일치해야 한다.
- **용존상 반응식**: 각 phase의 solid formula와 neutral dissolution product stoichiometry는 기존 saturation API에서 charge/element 균형을 검사한다. 성장 캠페인은 같은 계수와 일치해야 하며 모든 rate, molar volume, Ksp, gamma, diffusivity는 caller 제공이다.
- **수용액 sink residual은 별도**: 기존 spatial BV solver와 wall-saturation/kinetics의 transient transport는 별도 request와 반응 schedule이다. scale precipitation flux를 spatial BV ODE의 dissolved species sink로 삽입하지 않는다. 따라서 이 모델을 완전한 단일 aqueous element-conservative precipitation/electrochemistry PDE로 설명해서는 안 된다. 교차 수용액 source-term solver 및 total liquid+solid conservation closure는 후속 구현이다.
- Flux는 left-held knot approximation이다. 구간 내부의 saturation, 수송계수, 표면적, 반경, kinetics 변경을 적분하지 않으며, adaptive precipitation/scale solver가 아니다.
- 반복 contraction/unique solution/error bound는 증명하지 않는다. 비수렴 및 실패 prefix는 진단만 제공한다.
- 독립 검증, 검증된 재료/유체 kinetics, parameter identifiability, mesh/time-step sensitivity, 장기 field transfer 및 설계 수명 qualification은 수행되지 않았다.

이 API는 기존 spatial BV/수송, wall saturation kinetics, multilayer resistance, diffusion-limited growth evaluator를 같은 exact geometry 반복에 실제로 연결한다. 그러나 separate aqueous precipitation sink 때문에 완전 동시 reactive-transport/electrochemistry 계산은 아직 아니다.
