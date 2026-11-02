## 2026-11-01 — caller nucleation kinetics and component-state segment transition

Added two independently registered calculations. `chemistry.crevice_nucleation_kinetic_history` applies digest/Evidence-bound, caller-provided saturation intervals, phase-specific molar nucleation source laws, an explicit seed-inventory threshold, and caller seeded growth/dissolution laws. Each interval advances aqueous concentrations and solid inventories through the existing conservative kinetic ledger with element/charge checks. No automatic phase discovery, particle population balance or universal nucleation law is claimed.

`integration.crevice_component_state_segment_transition` binds an exact committed component-state BDF result to a caller-evidenced next-segment geometry/template. It transfers final component moles cellwise, verifies component/species identity and aperture-derived cell-volume closure, and creates a typed next BDF request. Geometry remains caller supplied and changes only at the segment boundary; there is no intrastep moving-boundary feedback, deposit-derived aperture or changing-cell topology remap.

Both modules include ModelSpec and Korean model/extension documentation. Central registry/schema/source/capability/scope wiring is complete: 948 capabilities (665 models, 190 interfaces, 101 partial), 1,450 public schemas, and 909 implementation bases. Package catalog sync is complete. Static scope audit: 101 rows / 474 source paths / 597 components, missing/unmapped/stale-symbol count 0. Numerical tests, package build and HPC remain deferred.

## 2026-11-01 — Crevice BDF capacitive forcing and fixed-volume advection

`integration.crevice_component_state_bdf` schema v3 adds two opt-in schedules. A digest/Evidence-pinned exact-knot, per-cell capacitive-current input enters the ionic charge-continuity balance and has an integrated charge ledger; it remains prescribed-current forcing and does not solve dynamic electrode potential or monolithic BV/Cdl coupling. A digest-bound transient planar-slit inertance input drives signed upwind component advection at each BDF RHS from the reconstructed stage chemistry. Left/right inlet/outlet component, element and charge reservoir changes are integrated as BDF states and included in closure records. The advection mode requires fixed aperture and volume and electroneutral caller reservoir compositions. It does not implement moving-boundary remap or pressure-flow feedback from the evolving chemistry. Numerical verification and package build are deferred. Central catalogs currently contain 946 capabilities (663 models, 190 interfaces, 101 partial), 1,444 schemas and 906 implementation bases; package catalog sync and static scope audit completed (101 rows, 472 paths, 595 components, 0 missing paths/unmapped components).

## 2026-11-01 — 빠른 우선순위 10개 통합 완료

이번 회차에서 합의한 10개 실행 항목을 연결했다: (1) BDF 결과→다음 고정 구간 재고 인계 API 확인, (2) registry 등록, (3) 입력/결과 schema export, (4) source identity 추가, (5) capability/model index 재생성, (6) package catalog mirror 동기화, (7) 101행 scope source mapping, (8) API·사용자 매뉴얼·모델 가이드·downstream extension request 반영, (9) 공개 Mendeley 부식 데이터 후보 2건을 metadata-only로 기록, (10) dataset rights/catalog 및 공개 경계 감사와 backlog 기록 갱신.

최신 생성물: 946 capabilities(663 models, 190 interfaces, 101 partial), 1,442 schemas, 904 implementation bases. 정적 scope audit: 101 rows / 471 source paths / 595 components, missing paths 및 unmapped symbols/components 0; classification 48 provider-dependent / 52 data-validation-pending / 1 code-incomplete. 데이터 카탈로그 감사: 83 datasets / 510 assets, publisher checksum 누락 5, local checksum-verified assets 171; rights audit 0 errors / 14 warnings. release boundary: passed, 3,377 files / 59,531,609 bytes. 전체 목표 완료율은 산정하지 않으며 bounded code trace 100/101은 unchanged. 수치 테스트·패키지 빌드·HPC job 제출은 하지 않았다.

2026-11-01 병렬 확장 2개 중앙 연결: `integration.tube_bundle_lame_stress_history`가 caller 제공 geometry/absolute-pressure exact-knot records를 재사용 Lamé 원통 해석으로 내·외면 응력으로 변환한다. `welding.waveform_energy_uncertainty`는 기존 `WaveformEnergy` 적분에 V/I/효율/이동거리의 digest-bound full covariance를 1차 전파한다. 두 모델 모두 권리 Evidence, review gate, 범위/계산량 제한을 두고 acceptance, 수명, probability 또는 qualification을 추론하지 않는다. 두 개의 합성 예제, 사용자 가이드와 downstream extension request를 추가했다. 중앙 연결 완료: 945 capabilities(662 models, 190 interfaces, 101 partial), 1,440 schemas, 903 source bases. 정적 범위 감사 101행·470경로·594구성요소, 누락/AST/symbol/unmapped/drift 0. code trace 100/101 유지, 전체 연구 목표율은 미산정. 공개 경계 감사 passed (비법률 검토). 테스트·패키징·HPC 미실행.

2026-11-01 추가 BDF 고체상 연성 및 중앙 연결: `integration.crevice_component_state_bdf`에 opt-in `instantaneous_solid_equilibrium` 모드를 연결했다. 요청의 `CellSolidPhaseSet`은 cell/assessment/asset/location/physical scope/clock/exact knot/material/metallurgy/environment/temperature/phase candidates/evidence/digest를 결속한다. 각 RHS trial에서 total conserved-component state를 bounded aqueous/solid partition API로 나누고 aqueous species를 NP/Faradaic coupling에 공급한다. Output에는 exact-knot solid/liquid histories, total component ledger와 component→element/charge/reservoir/current ledger가 포함된다. nested partition의 active-set/bisection work도 BDF request aggregate budget 안에 둔다. 기존 `aqueous_only` 기본 모드는 그대로다. schema 1,435개, source bases 901개, capability catalog 943개로 재생성; static scope audit 101 rows/470 paths/594 components, missing paths/AST/symbol/unmapped/drift 0. Bounded trace는 100/101 유지하고 broad Crevice residual을 문서화했다. Public boundary audit, numerical tests, package build, HPC는 이 갱신 이후 실행하지 않았다.

## 2026-11-01 — SCC–FTA 어댑터 등록 및 후속 개발

병렬 구현을 마무리해 Crevice 총성분 기반 한-cell aqueous/solid active-set partition, provider receipt 검증이 있는 시간별 FAD history, 이 history에서 caller probability만 쓰는 FTA adapter, AHSS1300 CC BY 4.0 workbook의 파일 pin/attribution 확인 후 값 비노출 worksheet 구조감사를 추가했다. AHSS raw file은 로컬 원자료 경계 밖으로 복사하거나 수정하지 않았다. 모든 신규 모델/API를 registry/schema/source/capability/model reference/backlog에 연결했다. 재생성 수치는 943 capabilities(660 models), 1,434 schemas, 900 sources. 정적 source/AST audit 101 rows, 469 paths, 593 components에서 누락·미매핑 0; public source boundary audit passed 3,356 files/58,917,776 bytes(이는 법률 clearance가 아님). Crevice solid partition은 standalone이며 BDF coupling gap은 남아 bounded trace 100/101 그대로다. No tests, numerical model runs, package build or HPC job.

SCC 균열성장 request/result를 digest 재계산으로 확인한 뒤 caller 제공 균열진전 한계와 기간 최초고장확률을 기존 FTA basic-event contract로 전달하는 adapter를 추가했다. 스키마·registry·catalog/reference/backlog를 갱신했다. 재현 가능한 합성 연결 예제 `examples/scc_fta_binding.py`도 추가했다. 후속 독립 작업은 Crevice intrastage solid partition, 공개 AHSS1300 hydrogen-permeation reader 연결, time-resolved FAD history로 나뉘어 병렬 진행 중이다. No tests, packaging or HPC jobs.

## 2026-11-01 — CREVICE component-state current schedule and public contract integration

Extended `integration.crevice_component_state_bdf` with an optional exact-knot ionic face-current history. Nonzero aqueous charge production is permitted only when a reviewed caller schedule supplies all `ncell + 1` face currents at the same times as reaction extents, uses zero external boundary currents, and closes the knotwise relation `I_right − I_left = F Σ(zνr)`. Interior Nernst–Planck migration gradients are reconstructed to match caller current and current residuals are checked in A. The calculation records charge C, Evidence and schedule digests, and bounded current evaluations. This is a prescribed-current child contract, not a Butler–Volmer/mixed-potential current predictor. Schemas and API/source catalogs now include the current schedule. Catalog totals: 935 capabilities, 1,417 schemas, 892 implementation/source bases; the 101-row/468-path/592-component static scope audit reports no structural drift. No numerical tests, package build, or HPC calculation was run.

## 2026-11-01 — current-carrying CREVICE result to component-state schedule adapter

Added a registered cross-module binding API that constructs `CreviceComponentStateBDFRequest` schedules from a digest-matched, fully committed `integration.crevice_current_carrying_np_faradaic` result. The producer exports exact-knot ionic face currents and branch current densities with units. The adapter requires reviewed identity/order/time mapping, checks the initial conserved-component moles against producer species concentration and volume, converts branch current density to extent rate using the producer's reactive area/electron number, derives component/electronic reservoir ledgers, and reruns contract validation including charge continuity. It rejects the within-stage mixed-potential producer mode because endpoint schedules cannot reproduce it. This supports sequential integration while keeping the non-monolithic limitation explicit. Added schemas, registry/capability/source lineage, model/API docs and a CREVICE handoff note. Catalogs: 936 capabilities, 1,419 public schemas, 893 sources; source audit: 101 rows/469 paths/593 components, zero structural findings. Tests, numeric model execution, packaging and HPC were not run.

## 2026-11-01 — component-source lineage name aligned with charged-current support

Renamed the component-state BDF ModelSpec source ID from the charge-neutral-only label to `caller_evidenced_component_source_extent_schedule`, matching the current contract that supports charge-producing source extents only with a paired prescribed-current schedule and continuity closure. The old catalog derivation remains so prior result lineage can still be interpreted. Regenerated source/capability/model-reference catalogs and re-ran the scope source/AST audit (101 rows, 468 paths, 592 components, no structural findings). No calculation tests, package build or HPC were run.

## 2026-11-01 — Wet-CO2 integrated finite-gas solver evidence reconciliation

Re-read the live implementation and model guide for `integration.wet_co2_cylindrical_finite_gas_stage_geometry_feedback`. The BDF RHS reconstructs caller-defined aqueous mass action, BV/transport fluxes, finite-gas transfer and phase/wall inventories while recomputing cylindrical geometry and the radial mesh; schema v2 integrates stage shear detachment and solid export. The broad `degradation.wet_co2` parent is still partial, and automatic reaction/phase discovery and empirical qualification are not claimed. Its remaining item asked for this same integrated solver, so it was reclassified from `code_incomplete` to `data_validation_pending` with a source-symbol SHA record. The bounded trace changes 99/101 → 100/101, not the overall project completion estimate. The generated implementation backlog and source/AST audit were refreshed. No tests, numeric execution, package build or HPC were run.

## 2026-10-31 — current-carrying CREVICE extent to metal-loss and geometry handoff

Added `integration.crevice_current_carrying_extent_to_metal_loss` to bridge the new spatial current/Faradaic calculation into the existing CREVICE metal-loss and aperture path. It verifies the upstream `AssessmentResult` input/result digests against its exact request, requires a full committed contiguous interval history, preserves cell and branch order, and requires every branch to be mapped as net metal dissolution or explicitly excluded. Caller mapping Evidence pins metal stoichiometry, molar mass, density and per-cell reactive areas. The adapter consumes already integrated extents in mol and does not reintegrate current or apply Faraday's law a second time. Negative net extents for mapped dissolution branches fail closed because interval totals cannot resolve within-interval reversals.

Extended `integration.electrochemical_metal_loss_to_crevice_geometry` to accept the new AssessmentResult and use its exact digest-bound per-cell cumulative metal volumes without a second caller cell-fraction mapping. Direct geometry consumption requires the geometry cell IDs/order to match the source cell IDs and checks per-reaction volume closure against cumulative mass/density. Legacy metal-loss inputs retain their caller allocation path. The geometry remains sequential and does not feed aperture changes back into the electrochemical solve.

Wired both contracts into the default registry and standalone schemas, added source-basis records, API/model documentation and the CREVICE partial-scope path mapping, then regenerated capability/source/schema/package catalogs and model reference. Static scope audit: 101 rows/466 paths/590 components; missing paths, AST failures, stale/unmapped symbols, unmapped components and catalog drift are 0. Catalog: 931 capability rows (648 models/190 interfaces/101 partial), 1,399 schemas, 877 sources. Release-rights metadata audit: 81 datasets/877 sources, no findings; dataset archive rights audit: 81 datasets/356 assets, 0 errors/16 catalog warnings; public-source boundary audit passed. These are structural audits, not scientific or legal qualification. Numerical tests, package build and HPC were not run. Overall parent code progress remains 47/101 (46.5%).

## 2026-10-31 — AISI 1018 공개 부식자료 인벤토리 등록

공식 Mendeley v1 기록의 CC BY 4.0 선언과 제3자 콘텐츠 권리 주의사항을 반영해 `mendeley-aisi1018-aerobic-consortium-corrosion`를 데이터 및 source/capability 카탈로그에 등록하고 패키지 데이터 카탈로그와 동기화했다. 22개 원본 파일(총 444,555 bytes)은 파일 ID·크기·SHA-256을 로컬에서 대조했다. 17개 텍스트와 5개 OPJ의 스키마·단위·시편 매핑이 완전히 명시되지 않고 일부 ZView 헤더의 `1993`/`demo.z` 맥락이 다른 파일 메타데이터와 충돌하므로 데이터 행을 파싱하지 않는 metadata-only 인벤토리 API를 제공한다. raw 파일은 `data/raw`에만 두고 배포 경계에서 제외한다.

정적 결과: 카탈로그 81 datasets/356 assets, 로컬 provider checksum 일치 asset 171개 전체 중 해당 자료 22개, 누락 provider checksum 6건은 기존 자료에 한정. Dataset rights audit 0 errors/16 catalog-wide warnings이며 이 자료별 finding은 없다. Release-rights metadata audit는 81 dataset/874 source에서 findings 0; 공개 경계 감사는 3,286 files/56,290,707 bytes, manifest `9942de7cd6d1b8dabd58468d5523cce32615476202e44cbdb0de6179ccd32870`로 통과했다. 이는 법적 clearance가 아니다. parent code metric은 47/101 (46.5%) 그대로다. 계산 테스트, 패키징, HPC는 실행하지 않았다.

## 2026-10-31 — 유한 기상 stage geometry 및 current-carrying Crevice aperture 결합

`integration.wet_co2_cylindrical_finite_gas_stage_geometry_feedback`는 유한 기상, 액상 CO2*, wall chemistry와 스케일 상태를 BDF 내부 단계에서 함께 사용해 원통 반경·radial mesh·cell volume을 갱신한다. molar inventory 상태와 각 stage geometry/mass-action digest, element ledger를 보존한다. Lagrangian moving mesh 및 caller law 기반이며 동적 gas EOS, 자동 반응망 탐색, qualification은 제공하지 않는다.

`integration.crevice_current_carrying_aperture_feedback`는 current-carrying NP/Faradaic/spatial-chemistry 경로를 caller solid molar volume 및 aperture/hydraulic sensitivity로 반복 실행한다. aperture/velocity residual 모두 수렴한 마지막 trial만 결과로 반환한다. geometry는 정확한 time knots에서 업데이트하고 구간 사이는 선형이며, 연속 BDF 내부단계의 aperture state는 아니다.

추가된 두 계산 API를 포함해 통합 생성 결과는 929 capability (646 models/190 interfaces/101 partial), 1,393 schemas, 872 source records다. Partial-scope audit: 101 rows, 466 source paths, 589 components, 누락·AST·stale·unmapped 0. Dataset rights audit: 80 datasets/334 assets, errors 0/warnings 16. Release-rights metadata audit passed without findings. Public source boundary: 3,280 files/56,180,729 bytes, manifest `1c62dabda0f9271f1fbdd48fd4884c19cdb2157fd4cd2b40877436bbafa6580e`; structural check only, not legal clearance.

별도 open-data 후보 AISI 1018 aerobic-consortium corrosion archive 22개 파일(444,555 bytes)은 provider SHA-256과 size 일치를 확인해 ignored local raw 경로에 보관했지만 public data catalog/rights review에는 아직 넣지 않았다. 수치 테스트, 패키징, HPC job은 실행하지 않았다. 상위 broad-scope metric은 47/101 (46.5%) 그대로이며 신규 child model만으로 wet-CO2/Crevice parent를 complete로 승격하지 않았다.

## 2026-10-31 — BDF 단계 수용액 재계산, 전류 수송/Faradaic 결합 및 공개 피로 자료

`integration.wet_co2_cylindrical_stage_speciation_scale_feedback`는 BDF stage의 벽면 조성으로 caller 지정 질량작용 네트워크를 다시 풀고 얻은 활동도를 같은 RHS의 상별 스케일 침전·용해 속도에 공급한다. 반응망, 표준상태, 활동도 모델과 속도식은 입력자가 제공하며 자동 상/종 탐색과 적격성 판정은 하지 않는다. registry, schema, capability/source catalog, API 가이드와 `degradation.wet_co2`의 하위 경로가 연결됐다. 상위 wet-CO₂ 범위는 여전히 code-incomplete다.

`integration.crevice_current_carrying_np_faradaic`는 변수 단면 Nernst–Planck 이동전류, 혼합전위 면전류, Faradaic 벽 반응과 공간 화학 수지를 반복 연결하는 새 API다. 셀 0 전위 게이지, 절연 경계, 이중층 전하 저장 생략 및 전류·수지 closure review를 요구한다. registry/schema/capability/source 연결과 상위 Crevice 범위 감사가 끝났으며, 넓은 범위 완료로 간주하지 않는다.

Mendeley v1 폭발용접 다층판 피로 workbook에 대해 CC BY 4.0 및 제3자 권리 유의사항을 기록하고, 원 셀/provenance 보존용 typed-row reader를 registry/schema/catalog에 추가했다. raw workbook과 검토에서 제외한 ultrasonic 후보 ZIP은 local-only 경로에 남고 배포물에서 제외된다. 이 reader는 단위·적층 해석, 피로법칙 또는 성능을 추론하지 않는다. 데이터 권리 감사 결과는 80 dataset/334 asset, 오류 0, 기존 경고 16이다.

Caller-mapped import도 추가했다. 명시한 sheet/header/row span/column mapping, meaning, unit, role 및 Evidence에 따라 원값과 formula를 보존한다. 선택된 범위와 headers가 정확히 맞아야 하며, 단위 변환이나 수식 평가를 하지 않는다. caller row/cell 예산은 materialization 전에 확인하고 초과 요청은 빈 결과로 거부한다.

`adapter.crevice_faradaic_to_fault_tree_basic_event`는 계산 완료 상태, 정확한 input/result digest, 모든 committed interval의 요청 시각 일치 및 모델 Evidence를 확인한 뒤에만 FTA event를 구성한다. 확률, probability meaning, conditioning, scope, Evidence와 권리 경계는 caller 소유이며 current 또는 reaction extent에서 확률을 추론하지 않는다. 실제 다른 저장소 적용 전 필요한 별도 변경은 `docs/extension_requests/CORROSION_CURRENT_CARRYING_FTA_EXTENSION_KO.md`에 기록했다.

`integration.wet_co2_cylindrical_finite_gas_stage_speciation_scale_feedback`는 유한 기상 inventory, 원통 CO₂* 기액전달, 단계별 mass-action speciation, BV 및 scale kinetics를 BDF RHS에서 연결한다. 기체·액상 inventory cap과 원소수지 폐쇄, digest/evidence 계보를 포함한다. caller 반응망·속도·기액전달 파라미터 및 적용성 review가 필요하며 자동 종/상 탐색이나 qualification은 제공하지 않는다.

통합 metadata refresh 결과는 927 capability rows (644 models/189 interfaces/101 partial), 1,391 schemas, 869 source records다. Scope audit는 101행/464 paths/587 components이며 missing path, AST failure, stale symbol, unmapped component가 0이다. Public boundary audit는 3,274 files/55,656,439 bytes에서 통과했다. Dataset rights audit는 80 datasets/334 assets, errors 0/warnings 16이다. broad-scope code metric은 47/101 (46.5%)로 변동하지 않았으며 wet-CO₂/Crevice parent는 partial이다. 이번 변경에서는 수치 테스트, 패키징, HPC job을 실행하지 않았다.

## 2026-10-31 — stage-evaluated wet-CO2 scale kinetics, spatial crevice Faradaic path and magnesium SCC data

Added integration.wet_co2_cylindrical_stage_kinetic_scale_feedback. Caller activity coefficients, reference concentrations, log solubility products and kinetic coefficients define precipitation/dissolution fluxes. The reaction quotient and flux law are reevaluated from wall-cell concentrations at each BDF stage, with overflow-safe power caps, common cylindrical reactant supply, live solid inventory, RHS budget and species/element/charge/geometry closure ledgers. Activity and log-K records remain exact-knot-held; the API does not discover phases or qualify a corrosion law.

Added integration.crevice_faradaic_spatial_chemistry_coupling. It sequences variable-area transport, endpoint trapezoidal Faradaic extents, exact-knot aqueous/solid chemistry and a local mixed-potential iteration with branch/current/charge/element/reservoir closure. The existing transport solver requires zero ionic current on every face, so nonzero electrolyte face current is rejected; this does not claim ohmic migration coupled to Nernst-Planck transport.

Added data.mendeley_mg_fsp_scc_typed_rows for the official version-1 ZE41/AZ91D and friction-stir-processed workbook set. All four local-only raw assets match publisher sizes and SHA-256 values. The dataset rights record declares CC BY 4.0 and carries the third-party-permission caveat; reader rows retain cell/source lineage without interpreting SCC performance.

Central generation: 921 capability rows, 638 registered models, 187 interface bindings, 101 partial scope rows, 1,372 contract schemas and 858 source-basis records. Static scope audit: 101 rows, 461 source paths and 584 components; no missing paths, AST failures, stale symbols or unmapped components; two newly added wet-CO2/crevice child links were reconciled. Rights audit reports 79 datasets/333 assets, zero errors and 16 existing warnings. Parent implementation count stays 47/101 (46.5%) because both broad parent gaps remain open. Dynamic wet-CO2 aqueous chemistry, current-carrying crevice migration and another rights-reviewed dataset are now separate local tasks. No numerical tests, packaging, HPC or post-dataset public-boundary audit was run.
## 2026-10-31 — intrainterval scale sinks, crevice aperture feedback and central reconciliation

Added wet-CO2 model integration.wet_co2_cylindrical_aqueous_scale_sink_feedback. For each exact-knot interval, it constrains caller signed phase precipitation/dissolution terms by shared cylindrical reactant supply and inserts them in the same BDF inventory RHS as spatial Butler–Volmer branches. Phase inventory and cylindrical geometry are updated in a bounded outer iteration; closure and failure-prefix records are retained. Caller phase flux is held within the interval, so phase kinetics/selection and thermodynamic chemistry are not solved intrastep.

Added crevice model integration.crevice_spatial_chemistry_aperture_fixed_point. It reruns the spatial variable-area transport and endpoint chemistry operator split for each aperture/hydraulic trial. Caller solid-volume-to-gap mapping and aperture-to-face-velocity sensitivity inputs drive bounded updates; both residual classes and inherited elemental closure must pass to commit. This does not infer a pressure-flow law or move chemistry into the transport integrator stages.

Integrated the earlier AZ31B Mendeley corrosion-fatigue typed reader and its eight local-only source workbooks. Provider byte counts and SHA-256 values match; data, source and rights records disclose the dataset-level CC BY 4.0 declaration and possible third-party permissions. No measurement interpretation or corrosion/fatigue qualification is added.

Central catalog generation now reports 918 capability rows, 635 registered models, 184 interface bindings, 101 partial scope rows, 1,361 JSON contract schemas and 851 source-basis records. Static scope audit: 101 rows, 459 source paths, 582 components; no missing paths, AST failures, stale symbols or unmapped components; two new wet-CO2/crevice child links were reconciled. The 47/101 bounded-code count is unchanged because the wet-CO2 and crevice parent scopes remain incomplete. Three independent local tasks are underway: dynamic wet-CO2 kinetics, spatial crevice Faradaic coupling, and another rights-reviewed public dataset. No numerical tests, packaging, HPC jobs or post-dataset public-boundary audit were run.
## 2026-10-31 — wet-CO2 scale/recession, crevice transport/chemistry and AZ31B public data

Added integration.wet_co2_cylindrical_scale_recession_feedback, which iterates spatial BV transport, per-phase saturation/kinetics, diffusion-limited supply and cylindrical geometry on exact knots, with phase-flux accounting and a strict final geometry solve. Added 	ransport.crevice_spatial_activity_solid_nernst_planck_1d, which advances variable-area Nernst–Planck transport by interval, recalculates caller Davies/speciation/finite-solid chemistry at exact knots, carries aqueous and solid state forward, and records elemental closure and digest lineage. The crevice path is operator-split: chemistry is recomputed at knots and held within each transport interval; Faradaic and aperture feedback remain open.

Added a local-only AZ31B corrosion-fatigue typed-row reader for the official Mendeley version-1 workbook set. Eight files match provider byte counts and SHA-256 values. Catalog/source/rights records cite the dataset-level CC BY 4.0 declaration and disclose possible third-party content rights; pointwise interpretation and qualification are out of scope. Raw workbooks stay outside release artifacts.

Central generation: 916 capability rows (633 models, 183 API/interface entries, 101 partial scope rows), 1,357 schemas and 846 source records. Duplicate interface bindings now enrich an existing model row rather than emitting a repeated capability ID; future duplicate errors include both conflicting row summaries. Scope reconciliation: 101 rows, 457 source paths, 580 components, with no missing paths, AST failures, stale symbols or unmapped components. Parent implementation count remains 47/101 (46.5%); wet-CO2 and crevice remain code-incomplete because broader simultaneous chemistry/electrochemistry, geometry feedback and independent qualification are open. Next wet-CO2 sink and crevice aperture increments are underway locally in parallel. No numerical tests, packaging or HPC were run.
## 2026-10-31 — crevice exact-knot/cell mass-action projection

integration.crevice_local_mass_action_projection을 추가하고 registry, capability/source catalogs, implementation scope, 세 공개 JSON schema와 API 안내에 연결했다. 각 exact transport knot/cell에 caller mass-action template를 받아 transported concentration에서 caller-selected linear constraint target만 재구성하며 미선택 target은 보존한다. 고정 gamma와 concentration을 이용한 positive initial-activity guess, zero concentration용 명시적 numerical seed, species/stoichiometry topology 고정, transport-cell context digest, solver input/result digest를 유지한다. 한 knot의 모든 cell이 계산된 경우에만 그 knot을 커밋하고 앞선 complete prefix와 first failure를 보존한다. 활동도/상수는 caller 제공이며 시간 사이 kinetic feedback, phase transition, corrosion inference는 하지 않는다. 카탈로그: 909 capabilities(626 models), 1,344 schemas, 836 sources. 정적 scope audit 101행/452경로/575구성요소; 누락·AST·stale/unmapped 0. 수치/실험 테스트는 수행하지 않았다.

## 2026-10-31 — wet-CO2 spatial BV와 fixed-point adapter 연결

`make_spatial_wet_co2_candidate_solver(spatial_request_template)`를 추가하고 `matintegrity` package 최상위 API로 공개했다. Adapter는 각 iterate의 보어 반경과 고정 scale phase 재고에서 annular geometry를 다시 만들고, fixed-point digest와 adapter configuration digest를 trial request에 바인딩해 spatial BV 계산을 재호출한다. 종·전하·수용액 원소 수지 gate는 유지하고 wall-geometry closure 잔차는 controller로 전달한다. Controller ModelSpec은 spatial BV, kinetics, geometry source lineage를 연결한다. scale kinetics를 갱신하거나 외부 계수를 추정하지 않는다. Capability/source catalogs와 scope trace를 갱신했다. 수치 테스트는 보류한다.

## 2026-10-31 — 원통형 액상 물질전달용량 연결

integration.wet_co2_cylindrical_liquid_transfer_capacity_history를 registry/schema/capability/source/API/scope에 연결했다. caller가 digest 고정한 액상 확산계수와 단상 원통형 hydraulics 및 geometry knot를 기존 액상측 mass-transfer 상관식에 전달해 세그먼트별 전달 conductance exposure를 계산한다. 생성: 889 capabilities (607 models/181 interfaces/101 partial), 1,291 schemas, 791 sources. scope 101 rows/439 paths/558 components; missing/AST/stale/unmapped/drift 0. rights 73/302, errors 0/warnings 16. public boundary 통과: 3,104 files/50,137,199 bytes, SHA 91d0ab335b6907ba2d9406e95e5b111b0e68a68f8e7c3a48629e0d53faadbb3c. 테스트·패키징·HPC 미실행.

## 2026-10-31 — 원통형 scale 전단 제거 API 중앙 연결

integration.wet_co2_cylindrical_shear_limited_scale_removal을 registry, schema, capability/source catalogs, API 안내와 wet_CO2 scope에 연결했다. 총 884 capabilities (602 models/181 interfaces/101 partial), 1,280 schemas, 777 sources. 정적 scope 감사 101 rows/434 paths/553 components, 누락·AST·stale/unmapped·drift 0. wet_CO2와 crevice_chemistry는 code-incomplete로 유지한다. 권리 audit 73 datasets/302 assets, errors 0/warnings 16; public boundary 통과 3,083 files/49,798,235 bytes, SHA 3be129fd34164381d99a17739501456e1d100bba6a309e2063101bdeb0be8f17. 테스트·패키징·HPC 미실행.

## 2026-10-31 — 활동도 기울기 보정 간극 면 플럭스 구현

integration.crevice_activity_gradient_nernst_planck_flux_1d 계산기를 추가했다. 단일 면에서 caller 농도와 ln(gamma) 기울기, 확산계수 및 유속으로 종별 플럭스를 계산하며, 대류를 포함한 전류합이 0이 되도록 전위 기울기를 대수적으로 정한다. 활동도 생성이나 aqueous speciation을 수행하지 않고, 표준상태·단일 이온 관례와 열역학 일관성은 caller 검토 및 Evidence로 묶는다. 경계와 사용 예시는 docs/models/CREVICE_ACTIVITY_GRADIENT_FLUX_KO.md에 기록했다. 현재 감사된 baseline은 882 capabilities / 1,276 schemas / 772 sources, scope 432 paths / 551 components이며 public boundary SHA-256은 3bf8efd0fbf7c6047e448de266556360f2c291575239c40423ea85e0a4b4939다. 새 API의 재생성과 감사는 이어서 수행한다. 테스트·수치 검증·패키징·HPC는 실행하지 않았다.


## 2026-10-31 — 후속 CO₂·Itoh·gasket API 조합과 중앙 연결

추가 5개 API를 기존 계산기와 digest-pinned 결과에 연결했다. `integration.co2_henry_temperature_to_fixed_fugacity_carbonate`와 `integration.co2_henry_temperature_to_fixed_fugacity_carbonate_history`는 검토된 Henry 온도 보정 결과를 점별·시간이력 carbonate-only equilibrium에 전달하고, upstream input/result digest·단위·용매·온도·RunContext를 확인한다. carbonate 계산은 전체 aqueous chemistry가 아님을 기록했다. `fatigue.itoh_nonproportional_strain_life`는 동일 재료·strain definition 및 licensed curve 범위 안에서만 Itoh parameter를 life로 매핑하고, `fatigue.itoh_nonproportional_miner_blocks`는 caller cycle block 전부가 일관될 때 기존 Miner 계산을 쓴다. `fabrication.gasket_evidence_bound_prony_history`는 기존 generalized-Maxwell solver에 Evidence, license, 온도 범위를 더한다.

앞선 네 범위 증분과 함께 registry/schema/catalog/source/model reference/API guide/scope trace가 최신 생성됐다. 총 catalog: 822 capabilities (541 models/180 interfaces/101 partial), 1,110 public schemas, 612 sources; static scope: 101 rows/374 unique paths/491 unique components, 누락/AST/stale/unmapped 0. Audit 재실행 때 중복 component가 늘어나던 결함을 수정했다. generated `Literal` import 오류도 바로잡고 catalog 재생성에 성공했다. 공개 소스 경계 감사를 재실행해 2,784 files에서 통과했고, dataset rights audit는 69 datasets/291 assets, errors 0, warnings 16이었다. 두 감사는 구조·metadata 검사이며 legal clearance가 아니다. 전체 parent progress는 47/101(46.5%)이며 신규 하위 API는 parent 전체를 완료시키지 않는다. Tests, model execution, experimental validation, examples, package builds, HPC submissions are deferred.

## 2026-10-31 — 네 범위 계산기 병렬 증분과 중앙 연결

네 개 API를 추가해 코드 미완성 네 broad parent에 각각 연결했다. `chemistry.co2_henry_vant_hoff_temperature_correction`는 caller 열화학 parameter로 CO₂* Henry 계수를 온도 보정한다; `chemistry.aqueous_extended_debye_huckel_self_consistent_speciation`는 caller mass-action을 조성별 extended Debye–Hückel 계수와 고정점 반복으로 연결한다; `fatigue.itoh_nonproportional_strain_parameter`는 검토된 한 주기의 유한 변형률 경로와 재료 caller 계수로 비비례 parameter를 산출한다; `fabrication.gasket_multi_bolt_sector_equilibrium`는 다중 인장 볼트·압축 가스켓 sector의 공통 축방향 개구와 힘 평형을 각 caller load knot에서 푼다.

네 API의 registry, JSON contracts, capability parent mapping, source catalog, model reference, API guide와 package metadata를 생성·동기화했다. static scope traceability는 101 rows, 368 unique paths, 485 unique components; missing/AST/stale/unmapped results 0이다. audit script의 repeated-run duplicate component 누적도 바로잡았다. 최신 catalog는 817 capabilities (536 models, 180 interfaces, 101 partial), 1,102 schemas, 607 source records다. broad parent progress는 47/101 (46.5%) 그대로며 이는 parent closure만 세기 때문이다.

이전 Hangang job `1186453`은 source-order mock partition만 통과하고 `AssessmentResult.qualification="data_import"` contract 오류로 실패했다. 해당 Literal과 schema는 수정했지만 job을 재제출하지 않았다. 이번 모델들의 tests, numerical calculation, experimental validation, examples, package builds 및 HPC jobs는 수행하지 않았다.

## 2026-10-31 — CoolProp 순수 물 포화증기 provider 연결

습식 CO₂ wall 상태에서 순수 물 포화증기 fugacity만 공급하는 optional adapter를 일반 registry API에 연결했다. CoolProp은 호출 시점에만 import하며 backend·버전·revision·입력 상태·결과 digest를 기록한다. caller의 wall phase 적용성 검토와 결정론적 bound를 요구하고, 실제 혼합가스 수증기 fugacity, 염수/MEG 활동도, 응축량 및 부식률은 계산하지 않는다. capability/source/schema/model reference와 package catalog를 재생성·동기화했다. 정적 범위 감사는 101행·353경로·473구성요소, 누락/미매핑 0이다. 모델 테스트, 실제 계산, HPC 제출 및 패키지 빌드는 수행하지 않았다.

## 2026-10-30 — 가중 피로수명 lower-tail 평균

다축 피로 가중 scenario 요약에 caller 지정 lower-tail mass levels를 추가했다. 가장 짧은 수명부터 정확히 지정 가중 질량까지 누적하고, 경계 시나리오의 일부 weight만 사용해 tail 평균을 계산한다. 가중 분위수 및 threshold summary와 같은 distribution-summary review가 필요하다. finite scenario lower-tail 평균은 probability, confidence 또는 continuous-distribution CVaR가 아니다. Python API/schema/catalog와 weighted scenario 설명·scope audit를 갱신했다. 테스트·수치 검증은 보류한다.


## 2026-10-30 — coverage kinetics 구간별 Arrhenius 온도 이력

`CallerScaleCoverageKinetics`에 interval temperature와 `interval_temperature_profile_reviewed`를 추가했다. Arrhenius를 선택하면 각 구간 온도에서 attachment/detachment rate를 다시 평가하고, 모든 구간 온도가 명시적 support 안에 있어야 한다. Chemistry→scale adapter의 coverage 경로도 검토된 왼쪽 절점 온도를 각 interval에 연결한다. coverage request의 첫 온도는 aqueous history 시작 온도와 일치해야 하며, interval 사이 온도 보간은 하지 않는다. API/schema/source 및 전용 coverage 문서를 갱신한다. 테스트·수치 검증은 보류한다.


## 2026-10-30 — 가중 수명 분위수/threshold 조회 비용 절감

가중 분위수와 cycle threshold 계산을 개선했다. 수명 순 정렬 후 Kahan 누적 가중치 배열을 한 번 만들고 이진 탐색으로 각 질의를 처리한다. 최대 10,000 시나리오·1,000 threshold에서 threshold마다 전체 ID 목록을 복제하던 출력을 threshold별 개수와 가중 몫으로 줄였으며, ID는 이미 hash-pinned `scenario_lives`에서 추적 가능하다. 분위수 q=1은 weight 합 허용오차와 무관하게 최대 수명 witness를 반환하도록 정의했다. 계산 의미/API 문서/source basis를 갱신한다. 테스트는 보류한다.


## 2026-10-30 — 화학 포화도에서 스케일 coverage 이력 연결

기존 `integration.aqueous_saturation_to_surface_scale_kinetics`에 선택형 `CallerScaleCoverageKinetics` 요청을 추가했다. 단일상 두께 kinetics와 같은 digest-검증 수용액 포화도 knot를 소비하며, coverage interval의 clocks가 모든 knot와 정확히 맞고 coverage 요청의 scale phase/specimen/condition이 두께 요청과 일치해야 한다. 이 기록 작성 당시에는 coverage 모델이 단일 온도만 받았다. 이후 구간별 상수 온도 및 Arrhenius 연동을 추가했다. 두 state law는 독립 계산이며 두께→coverage, scale→확산/부식 피드백은 구현하지 않았다. 기존 커버리지 속도 solver를 재사용하고 registry/schema/API/source 및 wet-CO2 범위 설명을 갱신했다. 테스트·수치검증은 보류한다.


## 2026-10-30 — 다축 피로 시나리오 가중 분위수와 임계수명 몫

기존 finite weighted-life moments에 선택형 weighted inverse-ECDF 분위수와 caller 정의 cycle-life threshold별 가중 scenario 몫을 추가했다. 분위수는 수명 오름순·동률 scenario ID 순으로 고정하고 누적 caller weight 기준으로 계산한다. 각 기능은 별도 review flag, 입력 threshold/quantile, witness ID를 결과에 남긴다. 임계수명 몫은 finite manifest의 가중 질량이며 failure probability나 신뢰구간으로 해석하지 않는다. API/모델범위/source derivation 문서를 갱신했다. 테스트·수치 검증은 보류한다.


## 2026-10-30 — 스케일 kinetics의 온도 이력 처리

수용액 포화도 이력은 절점별 온도를 가질 수 있지만 기존 단일상 스케일 kinetics는 온도 하나만 받았다. `SurfaceScaleKineticInterval.temperature_K`와 `interval_temperature_profile_reviewed`를 추가해 caller-reviewed 구간별 상수 온도를 지원한다. 각 구간의 Arrhenius 속도상수는 그 구간 온도에서 별도로 계산하며, 입력된 절점 온도는 Arrhenius support 안에 있어야 한다. 포화도→스케일 adapter는 온도 이력이 기준 온도와 다를 때 `temperature_knot_mapping_reviewed`를 요구하고 왼쪽 절점 온도를 구간 온도로 연결한다. 온도 보간이나 연속 온도-속도 적분을 주장하지 않는다. 계산 코드, 단위 metadata, API/source derivation 문서를 갱신했다. 테스트 및 수치 검증은 보류한다.


## 2026-10-30 — 수용액 포화도→스케일 연동의 내부 절점 계보 확인 강화

앞서 추가한 `integration.aqueous_saturation_to_surface_scale_kinetics` adapter의 입력 검증을 강화했다. 최상위 saturation AssessmentResult와 nested van't Hoff mass-action history의 registry input/result digest를 각각 재계산하고, 모든 knot의 source Calculation digest, time/temperature, 포화 screen의 upstream mass-action digest와 용해도 기록 digest를 상호 확인한 후에만 caller kinetic law를 호출한다. 해시가 있어도 입력과 결과 내부의 절점 연결이 서로 다르면 `needs_data`로 종료한다. API/source derivation 기록을 갱신했다. 테스트·수치 실행은 보류한다.


## 2026-10-30 — 포화도 이력과 단일상 스케일 kinetics 연결

`integration.aqueous_saturation_to_surface_scale_kinetics`를 추가했다. 입력된 van't Hoff 수용액 포화도 AssessmentResult의 전체 digest와 registry input digest를 확인하고, caller 선택 고체의 각 계산 knot가 정상인지 확인한 뒤 인접 knot의 포화비를 caller 정의 스케일 kinetics 구간에 연결한다. 구간 경계는 원 history 시간과 정확히 같아야 하고, 포화비 변환은 log10 범위 ±300으로 제한한다. 계수, 반응상 선택, kinetics 적용성은 caller 소유로 유지하며 값의 자동 추론이나 보간은 하지 않는다. API 설명 및 범위 추적 catalog를 갱신했다. 테스트와 수치 검증은 보류한다.

## 2026-10-30 — B-dot exact-knot 포화 선별 adapter

`screen_mass_action_calculation()`은 직접 speciation `Calculation` 또는 registered `AssessmentResult`에서 species activity, temperature, standard state와 provider record를 가져온다. 기존 지원 목록에 registered B-dot speciation과 exact-knot B-dot history를 추가했다. History에는 `speciation_knot_index`가 필수이며, adapter는 전체 assessment input digest, knot-history list digest, request digest, result digest, knot clock/temperature와 `parameter_record_sha256_by_knot` 정합성을 확인한다. 사용한 upstream activity state digest는 원 B-dot AssessmentResult digest이고, 선택 knot와 parameter digest는 별도 lineage fields로 반환한다. 불완전한 history, 틀린 knot/parameter mapping, 미계산 source는 포화 계산 전에 `needs_data` 또는 upstream status로 닫는다. 포화 방정식은 기존 `aqueous_saturation_screen()`에 맡긴다. 선택한 candidate들의 saturation ratio와 caller uncertainty intervals만 계산하며 상 선택, 물질수지, 핵생성/침전량/속도는 추론하지 않는다. 합성 `aqueous_bdot_to_nernst_history.py`를 확장해 포화선별·Nernst 두 branch·mixed potential을 함께 배선했지만 실행하지 않았다. 정적 산출물 갱신 기록은 뒤따르는 continuation/status 항목을 따른다.

## 2026-10-30 — caller geometry 이력 지원 restricted transport

`RestrictedTransportRequest`에 output-clock-aligned cell/face cross-section histories와 선택적인 wall-area-density history를 추가했다. `solve_restricted_transport`는 요청 시각 사이에 area를 선형 보간하고, `d(CV)/dt` conservation form에 맞춰 concentration ODE에 `-C(dV/dt)/V`를 포함한다. geometry knot에서 BDF를 재시작해 piecewise derivative의 불연속을 건너뛰지 않으며, inventory와 Poisson potential 계산도 해당 시각 geometry를 사용한다. mouth/tip/reaction/wall ledger는 기존 고정 reference-area basis를 유지한다. geometry interpolation·inventory dilution review, provider/config/time-basis lineage와 시작 geometry 일치를 요구한다. 이력은 외생 입력이며 chemistry·wall flux와 연성되어 예측되지는 않는다. 전용 API/수식/한계 문서와 capability 설명을 갱신했다. schema·source/capability/model-reference 생성과 101-row 정적 scope audit를 갱신했다. 계산 테스트·계산 실행·패키징·HPC 제출은 하지 않았으며 전체 추적은 47/101(46.5%)로 유지한다.

## 2026-10-30 — KBM 최대 전단면 수명 곡선 경로

`KandilBrownMillerLifeCalibration`과 builder를 추가해 기존 generic shear/normal curve mapping과 구별했다. 해당 경로는 maximum-pairwise-chord에 의한 유한 샘플 최대 전단 범위 후보만 선택하고, 각 후보에서 `shear_strain_amplitude + S_KBM × normal_strain_range`를 caller 계수로 계산한 뒤 digest가 고정된 동일 재료조건 수명곡선 안에서 log-log 보간한다. 전단 범위 동률과 parameter 동률을 보존하고, 다른 range method·곡선 외부·열린 review는 계산을 차단한다. 독립적으로 저작한 수식 설명과 synthetic calibration wiring example, KBM 출처 근거 및 공개 API/구현현황 문서를 연결했다. 공개 스키마 828개, model 391개, interface 159개, capability 651개(부분범위 101개), source basis 453개를 재생성했다. 정적 범위 audit 101행·266 경로·381 구성요소에서 누락 경로/AST 실패/stale symbol/unmapped component가 0임을 확인했다. 계산 테스트·계산 실행·패키징·HPC 제출은 하지 않았다. 넓은 구현 완료 추적은 47/101(46.5%)로 유지한다.

## 2026-10-30 — erosion-corrosion 두께 한계상태 연결

`ErosionCorrosionWallThicknessBaseline`을 추가해 측정 두께와 caller required minimum을 source digest로 고정했다. 계산은 baseline 시각부터 연속하는 모든 erosion-corrosion interval에 대해서만 cumulative combined loss를 빼 deterministic margin을 반환한다. 모든 재료·형상·위치·scope identity가 맞아야 하며 누락 시계나 열린 review는 limit-state section만 `needs_data`로 만든다. 완전한 caller rate endpoints가 존재하면 하한/상한 margin과 threshold relation을 제공한다. 이는 FTA/신뢰성 모듈의 deterministic event basis일 뿐 failure probability, acceptance 또는 remaining life는 아니다. 합성 example에 synthetic wall baseline을 연결했다. Registry/schema/catalog/model reference/source audit를 재생성해 386 models·159 interfaces·101 partial entries (646 total)·821 schemas·444 source bases, audit 101 rows·265 paths·380 components, missing/AST/stale/unmapped=0을 기록했다. 계산 테스트·패키징은 실행하지 않았고 full-scope completion은 47/101(46.5%)다.

## 2026-10-30 — 침식·부식 상호작용의 결정론적 bound 전파

`ErosionCorrosionRateRecord`에 optional lower/upper thickness-loss rate endpoints와 point containment contract를 추가했다. 명시적 review가 있고 순수 침식·순수 부식·결합률의 각 구간 bounds가 모두 있을 때 interval arithmetic으로 residual synergy 및 cumulative loss bounds를 계산한다. 별도 corrosion-during-erosion 값까지 four-record endpoint가 갖춰지면 해당 구간의 두 interaction-term bounds도 출력한다. 누락/미검토 입력은 aggregate bounds를 withheld하며 확률이나 confidence level로 해석하지 않는다. 합성 fixture에 wiring 전용 endpoints를 보완하고 전용 안내에 semantics를 기록했다. Static generation은 386 models·159 interfaces·101 partial rows (646)·821 schemas·443 source bases를 반영했고 audit 101 rows·265 paths·380 components, missing/AST/stale/unmapped=0이다. 계산 테스트·패키징은 미실행이다. Strict completion flag는 47/101(46.5%)로 유지한다.

## 2026-10-30 — 침식·부식 상호작용 성분 장부

`degradation.erosion_corrosion_synergy_decomposition`를 추가했다. 동일 재료·유체·형상·물리범위·위치와 공통 `m/s` 두께손실 기준을 가진 record를 digest-linked Evidence로 고정한다. 순수 침식, 순수 부식, 결합환경의 piecewise-constant rate를 적분하고 signed residual을 계산한다. 침식 중 측정한 부식률이 추가되면 erosion/corrosion acceleration component를 분리하며, 빠진 구간의 partition은 완료로 표시하지 않는다. 음수 interaction을 보존하고 연속 구간 사이를 보간하지 않는다. 공개 학술 출처와 독립 algebraic derivation, 합성 입력, API/해석한계 문서를 연결했다. 스키마·카탈로그·model reference와 scope audit를 재생성해 386 models·159 interfaces·101 partial entries (646)·821 schemas·443 source bases, audit 101 rows·265 paths·380 components, missing/AST/stale/unmapped=0을 확인했다. 계산 및 패키징은 실행하지 않았다. 전체 completion remains 47/101(46.5%).

## 2026-10-30 — 수용액 균질 kinetics의 선택적 activity 보정

`mass_action_callback()`에 optional activity-coefficient provider를 추가했다. `ElectrochemicalTransport`는 이를 사용하려면 명시적 `homogeneous_reaction_activity_correction_reviewed` gate를 요구하고, `RestrictedTransportRequest`에 고정된 activity provider ID/configuration digest와 callback identity를 대조한다. 선택 시 종별 농도를 `gamma × concentration`으로 보정해 기존 caller forward/reverse concentration rate expression을 평가하고, 결과 lineage에 provider/revision/digest와 rate basis를 남긴다. rate constant 단위·보정 수치는 변경하지 않는다. 이는 caller가 검토한 유효농도 kinetics이며 표준상태 변환이나 일반적인 활동도 기반 반응속도 law는 아니다. API·제한 문서와 합성 callback wiring 예제를 추가했다. schemas/catalogs/model reference 및 101-row static audit를 재생성해 모델 385·인터페이스 159·partial 101·schema 821·source basis 441, source path 265·component 379, missing/AST/stale/unmapped 0을 확인했다. 계산 테스트, package build, HPC 제출은 실행하지 않았다. 전체 목표완료 수치는 47/101(46.5%) 그대로다.

## 2026-10-30 — 틈새 geometry 지원범위 이탈 prefix 보존

`planar_slit_aperture_history()`가 caller 지원 aperture 범위를 벗어나거나 geometry 수치범위가 초과될 때, 성공 이전 knot를 잃지 않고 `geometry_states`와 `computed_prefix_geometry_states`로 반환하도록 했다. 결과는 계속 `out_of_scope`이며 최초 실패 시각·구간과 범위 이탈 셀 ID를 제공한다. 이 prefix는 진단·재개용이고 완전한 transport history가 아니다. `integration.crevice_aperture_history_refinement`도 digest-pinned `out_of_scope` source의 유효 prefix를 검토/세분화할 수 있지만, 그 상태를 계속 `out_of_scope`로 보존하고 후속 완전 geometry campaign 입력으로 승격하지 않는다. `CREVICE_APERTURE_EVOLUTION_KO.md`의 signed recession 식을 코드의 positive-metal-loss convention에 맞춰 바로잡았다. registry/schema/model reference를 재생성하고, 정적 source audit 101행·265 경로·378 구성요소에서 누락/AST/stale/unmapped 0을 확인했다(821 public schema; 384 model inputs). 실행 테스트 및 package 작업은 사용자 지시대로 미실행이다. 이는 adaptive physics re-solve나 within-interval moving boundary 구현이 아니다.

## 2026-10-30 — 전체 registry 합성 입력 연결 및 연동 결함 수정

`examples/model_inputs.json`의 미수록 38개 registry 모델에 프로젝트 작성 합성 payload를 추가해 384개 전체 model ID와 입력 목록을 맞췄다. strict contract 입력과 구별하기 위해 17개 모델의 asset/location/time-basis 실행 문맥은 root `run_contexts`로 보존하고 예제 실행 harness가 이를 소비하도록 연결했다. 모델군별 fragment는 병렬 registry JSON 호출로 확인했으며, 이 기록은 전체 pytest suite, 독립 수치 benchmark 또는 물리 검증 결과를 뜻하지 않는다.

연동 호출 중 드러난 결함을 수정했다: wet-CO₂ elemental handoff의 phase/component 매핑 비교, 전기화학 금속손실→틈새 형상에서 reaction-ID dict를 key로 잘못 순회한 부분, aqueous mass-action JSON 배열을 Python strict tuple contract로 재검증하던 assembly/composition 경로, chemistry boundary scalar path의 singleton string 반환. 이 수정 후 chemistry 경로 fragment는 synthetic upstream AssessmentResult까지 구성해 실행되며, 모든 synthetic input은 qualification이나 실측값을 주장하지 않는다. 테스트 suite와 package build는 미실행이다.

Hangang CPU 공유 연결은 wrapper를 통해 `HPC_LOGIN_NODE` / `HPC_USER`로 확인했다. GPU 공유 연결은 사용할 수 없는 상태였다. Scheduler 계산은 제출하지 않았다. 전체 scope 진행률은 기존 감사 기준 47/101 (46.5%)로 유지한다. 새 예제 커버리지는 전체 목표 완료율에 더하지 않았으며, code-incomplete/data-validation/provider 분류는 이 변경만으로 재평가하지 않았다.

## 2026-10-30 — Single-salt Pitzer activity API

고농도 순수 단일 전해질을 위한 `chemistry.pitzer_single_salt_activity`를 별도 모델로 구현했다. caller는 전하/화학식, molality, 온도별 molality-scale `Aphi`, `b`, `beta0/1/2`, `Cphi`, `alpha1/2`, parameter record checksum, Evidence, 온도 일치·ionic-strength 범위 review를 공급한다. 구현은 mean ionic `gamma±`, osmotic coefficient, solvent water activity를 산출하며 개별 이온 gamma와 혼합염의 theta/psi interaction은 생성하지 않는다. 작은 alpha-sqrt(I)에서의 `Bγ` 표현은 cancellation 완화를 위해 급수 전개를 적용한다. 공개 배포의 GPL 경계를 고려해 Pytzer GPL-3.0을 의존성으로 포함하지 않았다. source/capability catalog, JSON schema, model reference, scope 문서와 합성 parameter 예제를 추가했다. Catalog/schema 생성만 실행했으며, formula/calc regression, parameter-source validation과 package build는 보류했다.

## 2026-10-30 — CC0 Ti-6Al-4V 분극 CSV importer

공개 Zenodo record 12727325의 선택 `Fig1.csv` 바이트를 고정 provider SHA-256과 비교하는 `matintegrity.galvanic_data.import_ti6al4v_cathodic_polarization_csv`를 추가했다. Evidence도 source ID·record 식별·CC0-1.0·동일 파일 SHA-256이 함께 맞아야 한다. 매질 선택, 제공자 열 이름, reviewer-supplied 온도/전위 기준/조건, 단위검토를 계약으로 받는다. μA/cm²→A/m² 환산, signed electrochemical net current 및 Ti dissolution partial current 분리, 누락 row 기록, source row identity 보존을 구현했다. 단조 감소 branch만 배열 전체를 뒤집고 비단조/반복 전위는 정렬하지 않고 보류한다. registry, source/interface catalog, JSON schema, 모델 참조, API/data 문서와 로컬 원본을 인수하는 예제를 갱신했다. 카탈로그·스키마 생성은 성공했다. 모델 계산, 실측 자료 import, tests와 package build는 실행하지 않았다.

## 2026-10-30 — Activity table 원본 row 계보 및 입력 budget

각 activity knot에 선택적 `source_record_id`를 추가하고 measured/open_dataset Evidence가 있으면 모든 knot의 source row ID를 요구한다. open_dataset Evidence에는 license/reuse policy가 필요하다. 결과에 citation/license Evidence, point count budget, slice별 source row ID 개수와 ID 목록의 SHA-256을 남긴다. 기본 표 점 budget은 250,000이며 caller는 10,000,000까지 올릴 수 있다. saturation composition은 해당 evidence/support/digest count가 정확한 종 집합과 점 budget에 맞는지 확인하고 유효 lineage만 넘긴다. 스키마·model reference·catalog를 갱신하며 수치 계산은 실행하지 않는다.

## 2026-10-30 — Registry 입력 lineage digest 재검증

Saturation composition이 registry `AssessmentResult`를 받으면 `ModelRegistry.run()`이 입력 계약에서 만든 `{model_id, model_version, inputs, context}` digest를 동일한 canonical JSON 규칙으로 다시 계산해 stored input SHA-256과 대조한다. 잘못되거나 변형된 등록 결과는 `needs_data`로 닫히고, 통과한 upstream에는 model version/source IDs/qualification 및 전체 result digest를 유지한다. 계산 tests는 실행하지 않았다.

## 2026-10-30 — Registry Assessment lineage 구분

Saturation composition 결과에 upstream representation을 명시하고 registry `AssessmentResult`일 때 model version, catalog source IDs, qualification과 registry input digest를 직접 보존한다. standalone `Calculation`은 자체 결과 digest만 upstream identity로 기록하고 registry-only metadata는 비운다. Context metadata를 복사하지 않아 사용자 정의 context를 불필요하게 확장 결과에 노출하지 않는다. 계산 검증과 tests는 미실행이다.

## 2026-10-30 — 상위 종활동 상태의 입력 경계 검증

Saturation composition adapter는 상위 결과에서 finite positive 절대온도, nonempty standard state, 고유한 비어 있지 않은 species ID 및 finite positive dimensionless activities를 확인한다. Provider revision도 record ID/digest와 함께 요구하고 record SHA-256은 lowercase 64-hex 형식인지 확인한다. 이는 직접 구성한 raw `Calculation`/`AssessmentResult` payload가 후속 Pydantic request 생성에서 예상치 않은 예외를 발생시키는 경로를 줄이며 malformed upstream은 `needs_data`로 보류한다. 계산·test는 실행하지 않았다.

## 2026-10-30 — Activity table upstream 합성 fail-closed 검증

Candidate-solid saturation adapter가 tabulated-activity 결과를 식별하면 표 온도·온도별 ionic support·보간 정책·configuration/record digest와 actual fixed-point ionic strength를 확인한다. Exact species coverage, ordered slice temperature, ionic-strength query coverage, temperature support와 SHA-256 형식을 검증하고 중복 species row도 거부한다. 불완전하거나 서로 맞지 않는 상위 lineage는 `needs_data`로 끝내며 screen 입력을 만들지 않는다. 실행 tests와 화학 계산 검증은 하지 않았다.

## 2026-10-30 — Saturation screen에서 upstream 활동도표 lineage 유지

`screen_mass_action_calculation()`이 upstream activity table result에서 tabulated-activity signature를 확인하면 temperature, 종별 ionic-strength/temperature support, interpolation policy와 configuration/record digest를 `upstream_activity_table_lineage`로 전달한다. 결과 content hash는 전체 upstream 계산을 계속 결속하며 별도 구조 요약은 소비자가 support 및 적용 조건을 직접 확인하게 한다. 계산과 tests는 실행하지 않았다.

## 2026-10-30 — 활동도표 지원격자 lineage 출력

Tabulated activity 계산결과에 종별 fixed/sliced table mode, 온도별 ionic-strength 최소·최대 및 점 개수와 계산된 온도/이온강도 평가점을 명시했다. 원 table 내용은 기존 canonical input digest와 provider/record digest에 묶이고 요약 support를 결과에서 바로 확인할 수 있다. 전체 point 배열을 복제하지 않아 result size를 입력 표 크기에 비례해 늘리지 않는다. 계산 tests는 실행하지 않았다.

## 2026-10-30 — Caller 활동도 계수의 온도 표면

기존 fixed-temperature, species-wise ionic-strength table API에 temperature-sliced table 입력을 추가했다. 각 종은 두 개 이상의 증가 온도 slice를 제공하고 각 slice는 0에서 시작해 선언한 ionic-strength 상한을 덮어야 한다. `ln(gamma)`는 먼저 각 slice에서 이온강도 방향으로 보간한 다음 온도 방향으로 선형 보간한다. 계산 온도·이온강도 양쪽의 외삽은 허용하지 않고 species별 온도 support 및 보간법을 결과에 남긴다. 이는 caller 데이터 표면 위의 보간기이며 용매 전이, 물성 자격화나 검증된 전해질 모델이 아니다. schema·model reference·catalog를 동기화했으며 계산 테스트와 온도 slice 예제 실행은 하지 않았다.

## 2026-10-30 — Caller 활동도 표 온도 적용조건 명시

`AqueousTabulatedActivityIteration`에 입력 table의 온도 `activity_table_temperature_K`를 명시하고 `AqueousMassActionSystem.temperature_K`와 정확히 맞지 않으면 contract 단계에서 거부하도록 했다. 결과에는 system 온도와 table 온도를 각각 남기며 synthetic model-input fixture를 갱신했다. 온도 외의 solvent/electrolyte composition/pressure applicability 및 외부 계수표 타당성은 여전히 caller review 사항이다. schema/reference를 갱신하되 계산 tests는 실행하지 않는다.

## 2026-10-30 — Ksp callback과 kinetic campaign 상태 일치 검사

Saturation-mode campaign에 `saturation_activity_standard_state`를 추가하고 필수화했다. 계산 진입 시 callback이 제공하는 고정 `temperature_K`와 `activity_standard_state`가 campaign 설정과 정확히 일치해야 한다. 이전에는 factory가 template 상태를 callback에 보존했어도 solver가 campaign과 비교하지 않아 서로 다른 온도·표준상태가 결합될 수 있었다. 계약 schema를 갱신하고 문서에 해당 제약을 추가한다. 수치 tests 및 예제 실행은 하지 않는다.

## 2026-10-30 — 포화 callback 활동도 표준상태 결속

기존 Ksp/evidence template에서 transport 포화 callback을 만들 때 activity provider가 보고한 `activity_standard_state`가 reviewed template과 완전히 같은지 요구하도록 했다. 표준상태 문자열을 합성 callback 설정 digest와 callback metadata에도 포함해 설정 lineage에서 빠지지 않게 했다. template이 제공하는 온도는 고정 온도로 activity provider에 전달되며 이를 설명하는 합성 배선 예제를 추가했다. 계산 검증·테스트·패키징은 수행하지 않았다.

## 2026-10-30 — 다상 transport에 포화 callback kinetics 연결

`CompetingSolidKineticTransport`에 direct-rate 및 saturation-provider 모드를 상호 배타적으로 추가했다. Saturation 모드는 각 구간 수송 종료 후 현재 cell concentration 및 solid inventory를 구간 종료 global time과 cell index와 함께 caller callback에 보내고, callback configuration digest·표준상태 review와 phase별 law를 검증한다. 반환된 saturation ratios를 phase별 signed power-law rate로 변환해 해당 transport 구간 끝에 기존 charge/element-conserving cell ledger에 적용한다. 셀별 포화비·driving distance·방향·속도를 기록하고 callback/provider 불일치나 비수치 결과는 해당 실패 시점 prefix에서 중단한다. 이는 lagged operator split이며 interval 내 동시 chemistry/transport 해가 아니다. 공개 interface schema/catalog, 합성 callback wiring 예제와 한계 문서를 갱신했다. 스키마·catalog/reference 생성 및 정적 AST 감사만 하고 계산 예제/테스트/검증/package는 실행하지 않았다.

## 2026-10-30 — 경쟁 고체상 포화도 기반 kinetics 연결

`CompetingSolidSaturationKinetics`와 `evaluate_competing_solid_saturation_kinetics`를 추가했다. caller가 모든 후보상에 대해 공급한 표준상태 기준 saturation ratio 이력을 각 상별 precipitation/dissolution 계수와 반응차수로 signed extent-rate로 변환하고 기존 다상 kinetic ledger에 전달한다. 양론·charge/element balance·고체 inventory 제한 및 동시 침전 resource limiter는 기존 conservative ledger를 재사용한다. 유한 numeric overflow는 계산 prefix를 보존하고 완료 결과를 내지 않는다. JSON 계약, registry API, synthetic composition-only example, 전용 설명서 및 공개 schema/catalog를 연결했다. 포화도 산출, speciation, phase discovery, nucleation, rate calibration/qualification은 다루지 않는다. 실행 테스트·수치 검증·패키징은 하지 않았다.

## 2026-10-30 — 틈부식 recession feedback 내부 형상 갱신 간격

기존 feedback operator split에 선택적 `maximum_geometry_update_step_s`와 `maximum_internal_segments` 정책을 연결했다. 사용자가 표본화 적합성을 검토해야만 내부 분할을 허용하며, 원래 입구 농도 이력은 원래 출력 시간점 사이에서 선형 보간한다. 각 내부 수송 구간에서 금속 제거는 양의 recession으로 간극을 넓히고 재석출은 음의 recession으로 간극을 줄인다. 농도 형상·유한성·비음수성과 inventory-remap tolerance가 모두 확인된 뒤 ledger·상태·완료 segment를 커밋하도록 순서를 바꾸고, 실패한 계산 구간은 완료 prefix와 구별해 보존한다. 결과에 내부 시간표, 최대 간격, segment 제한, 보간 정책을 기록하고 범위 문서를 동기화했다. 연속 moving-boundary 계산은 아니다. schema를 갱신했으며 수치 실행·계산 테스트·패키징은 하지 않는다.


## 2026-10-30 — 틈새 개구부에 따른 정상 슬릿 유동 및 수송 연결

`PlanarSlitHydraulicFlow`와 `evaluate_planar_slit_hydraulic_flow`를 추가했다. 셀별 길이·개구부·압력차·뉴턴 유체 물성으로 넓은 평행판의 Poiseuille 저항을 셀별 산출하고 직렬 합산해 유량, 셀 압력 손실/경계 압력, 셀 속도와 transport face 속도를 반환한다. 선택 입력한 aperture-history 전체 결과는 canonical digest와 마지막 cell aperture로 고정한다. 폭/개구부 종횡비 및 hydraulic-diameter Reynolds 수가 caller 선언범위를 넘으면 결과를 닫는다. face velocity는 `RestrictedTransportRequest.axial_advection_velocity_m_s`에 연결 가능하며 provider와 configuration digest를 함께 반환한다. 이는 정상·비압축성·뉴턴·층류 감산식으로, 과도 운동량/압축성/거칠기/입출구 손실/flow-recession 동시 결합이나 유동방향 경계 처리를 추정하지 않는다. 새 schema·registry model·source catalog·method note·합성 예제를 추가했다. 계산 테스트와 package 작업은 사용자 지시에 따라 보류했다.

2026-10-30 crevice hydraulics extension: `PlanarSlitHydraulicFlow`, aperture-history requests, and sequential recession feedback now accept finite signed pressure differences. Positive values define mouth-to-tip flow, negative values reverse the signed face-velocity field, and zero is a valid stagnant state. The Reynolds criterion uses speed magnitude; signed cell pressure drops and pressure-closure residual retain direction. This allows reviewed flow reversal to enter the existing signed transport boundary path without guessing inlet concentration. It remains steady laminar slit hydraulics at declared geometry/time points, with no transient momentum or within-segment moving boundary. Tests were not run.

Signed hydraulics integration follow-up: `RestrictedTransportRequest.axial_advection_velocity_m_s` now accepts signed static profiles as well as the existing signed callback output. A static profile containing reverse flow is refused unless reversal is reviewed and a distal inflow concentration vector is supplied, matching the callback path. The hydraulic API note records how to connect velocity, provider/configuration digests and distal boundary data. No numerical evaluation was run.

2026-10-30 hydraulic-to-transport adapter: added `matintegrity.bind_planar_slit_hydraulic_snapshot()` to verify a computed registry history, its registered input digest, the caller-pinned complete result digest, selected snapshot status and face count before creating a transport request. It copies signed velocity plus snapshot provider/configuration and upstream-result digests; reverse flow still needs the transport request's reviewed distal boundary. The synthetic hydraulic example now builds a registry AssessmentResult and demonstrates request binding without solving transport. Execution and numerical tests remain deferred.

Hydraulic time-series handoff: added `matintegrity.bind_planar_slit_hydraulic_history_series()` to require one transport request per adjacent hydraulic knot pair and exact local-clock duration alignment. It binds each interval to the start-knot steady snapshot and retains the complete upstream history digest in every resulting request. The example now demonstrates the series adapter for its single interval. This remains fixed-state operator splitting and does not solve transport or automatically update concentrations between segments.

The hydraulic binding also now writes the selected upstream global source time and registry time-basis ID into `RestrictedTransportRequest`, in addition to the local segment clock and full result digest. A later transport AssessmentResult can therefore distinguish the source snapshot time from its zero-based local integration time.

Thermal transient extension: `DistributedHeatExchange` now optionally accepts caller emissivity and radiative-environment temperature history together with an explicit gray-surface applicability review. The implicit nonlinear iteration adds a tangent/secant radiative exchange conductance per cell; the energy ledger accumulates the exact net Stefan–Boltzmann exchange. Radiation remains an area-average environment model with unit view factor and no participating-medium or shielding treatment. API/method limits were documented; no tests or numerical example were run.

Follow-up: factored the radiation tangent conductance into a finite-support helper, added a synthetic convection-plus-radiation registry example and documented its caller parameter contract. The example has not been executed.

The distributed radiation contract additionally accepts either one constant emissivity or a time-knot emissivity history aligned with the thermal clock. Time-varying emissivity is linearly interpolated only between caller knots; source/environment applicability remains caller-reviewed. The synthetic wiring example now uses the history form.

Thermal material lineage extension: `ThermalMaterialProperties` accepts an optional complete provider/revision/record/source-SHA set with matching `Evidence`. The transient conduction output records each normalized material-condition table's canonical digest and its source lineage, including an explicit unprovenanced caller-input state when no provider evidence is supplied. This does not qualify property values or infer temperature support; schema and API documentation were updated.

Thermal-to-stress handoff: added `bind_thermal_temperature_profile()` for a digest-pinned transient-conduction AssessmentResult and exact selected output index. It requires section coordinates to equal the thermal cell centers, records thermal model/version/result digest, selected global time and asset/location/time-basis identities, and validates these against the stress registry context. The thermal-gradient example now uses the typed binder rather than copying a bare temperature list. No thermal/stress calculation or test was executed.

## 2026-10-30 — 틈새 개구부·압력 이력에 따른 순차 유동 갱신

`PlanarSlitHydraulicHistory`와 `evaluate_planar_slit_hydraulic_history`를 추가했다. 계산된 aperture history 전체의 canonical digest를 요구하고, geometry knot와 길이가 같은 양의 pressure-drop 이력을 확인한다. 각 knot마다 현재 셀 개구부에 대한 기존 정상 유동 API를 개별 실행하여 압력 손실과 face velocity를 보존하고, 모든 knot가 계산범위일 때만 집계 결과를 `computed`로 한다. 이는 셀마다 하나의 고정 geometry transport를 실행하는 순차 operator-split 흐름에 맞춰 설계했으며 knot 간 압력 보간, 순간 운동량, 유동역전, 동시 chemistry/recession은 계산하지 않는다. 틈새부식 capability의 구현 구성요소 목록에도 정상 유량·history 양쪽 API를 연결했다. schema/catalog/model reference 및 합성 이력 예제를 갱신했다. 수치 테스트와 패키징은 계속 보류한다.

## 2026-10-30 — 외부 선형 구조강성에서 가스켓 접촉 연산자 축약

`FlangeComplianceReductionRequest`는 upstream solver/revision, 강성 source SHA, 일관된 translational `N/m` 증분행렬, 고정 DOF, 접촉 node→normal DOF 순서와 closure 부호를 명시한다. `reduce_flange_contact_compliance`는 고정 증분 DOF를 제거하고 자유 강성행렬의 양정치성·조건수를 확인한 뒤, 각 signed unit contact load에 대한 선형계만 풀어 상대 `m/N` compliance matrix를 만든다. 결과 행렬 대칭·PSD 조건과 node 순서를 확인해 기존 `FlangeContactFieldRequest` 계열 입력에 직접 복사 가능한 nested operator를 제공한다. FE mesh/element 조립·baseline 온도/압력/볼트 response·비선형 contact·누설/봉합 자격화는 범위 밖이다. registry/schema/capability/source catalog, 합성 예제 및 방법서를 연결했다. 계산 시험과 package는 보류했다.

## 2026-10-30 — 가스켓 접촉 유연도 행렬 시간 이력

`FlangeComplianceReductionHistoryRequest`와 `reduce_flange_contact_compliance_history`를 추가했다. 시간, 각 운영점 증분강성행렬, 그 행렬 source SHA 배열, upstream solver revision 및 접촉 DOF 배열을 정렬 검증하고 행렬×시간 계산 budget을 제한한다. 고정된 DOF/sign 매핑으로 기존 linear stiffness-to-compliance API를 각 knot마다 독립 실행하여 `m/N` 행렬과 조건수·고유값·원본 digest를 행별 반환한다. 전체 history는 모든 절점이 계산 가능할 때만 `computed`다. 기존 gasket contact solver에 각 절점별 행렬을 연결할 수 있지만 solver tangent 사이 보간이나 접촉 응답을 자동 시간 통합하지 않는다. 등록·공개 schema·source/capability catalog·방법서·합성 예제를 갱신했다. 계산 테스트·수치 검증·package는 보류한다.

## 2026-10-30 — 선형 Prony 접촉에 시간별 구조 유연도 적용

기존 FlangeViscoelasticContactHistoryRequest가 선택적으로 FlangeComplianceReductionHistoryRequest 산출물과 canonical SHA-256을 받도록 연결했다. 입력 검증 시 history의 계산 상태/digest, operator별 상태·유한성·대칭성, 동일한 time knot과 node order, 정적 compatibility field와 첫 절점 행렬의 일치를 강제한다. 접촉 이력 계산은 각 time knot의 compliance matrix를 해당 closure/Prony branch update에 적용하며 절점별 구조 source SHA와 최소 고유값을 결과에 보존한다. 이력 계산은 piecewise-linear branch strain 경로로만 진행하고 operator 시간 보간이나 knot 사이 contact transition을 계산하지 않는다. 기존 single-matrix 입력은 호환된다. source derivation, API 안내와 방법서 계약을 갱신했다. 테스트/수치 검증/package는 실행 보류다.

## 2026-10-30 — 층상 scale 상한의 전기화학 경계 연결

`ScaleLimitedSurfaceFlux`를 `ElectrochemicalTransport`와 `assemble_electrochemical_transport`에 연결했다. Digest-pinned computed `chemistry.layered_scale_diffusion_limit` 결과의 area-average molar-flux upper bound를 tip 또는 built-in wall reaction 경계에 맵핑하고, anodic 또는 cathodic 방향 중 하나로 대상 종을 생산하는 모든 boundary reaction ID가 정확히 열거되었는지 확인한다. 단일 binding을 유지하면서 추가 tip/wall 종별 binding tuple도 허용한다. 동일 boundary의 여러 종 binding은 일치하는 명시 `surface_area_basis_id`를 요구하며 scale transport 계산 결과와 digest로 연결한다. 각 평가점에서 원래 부분전류 기준으로 각 종 상한의 공통 배율을 구하고, 여러 제한 종을 함께 생성하는 공유 branch에는 그중 최소 배율을 한 번 적용한다. 따라서 binding 순서와 무관하게 모든 flux upper bound를 만족하도록 branch를 낮추며, 각 제한 뒤 net current·reaction extent·모든 종 flux를 재계산해 반응별 전자/종 화학량론을 보존한다. 종별 diagnostics에는 독립 상한 배율과 실제 적용된 공유 branch 배율을 구별해 기록한다. 자유부식 mode는 제한된 전체 전류로 다시 zero-current potential을 bracket/solve하며 지원범위 안에 bracket되지 않으면 중단한다. 물리 scope·condition·상태·종·단위·면적 basis·고정 scale 상태·전위 기준 review를 요구한다. 이는 고정 scale 상태의 상한 limiter이며 scale 생성·피복 진화, morphology, 완전 동시 다층 수송-반응, 이동 경계, 실제 보호율은 모델링하지 않는다. 공개 contract/schema, source/capability/interface catalog와 한글 method note를 추가했다. 계산 테스트 및 package 작업은 지시대로 보류했다.

## 2026-10-30 — caller 다축 경로 손상 provider 적분기

`CallerMultiaxialDamageRequest`와 `evaluate_caller_multiaxial_damage`를 추가했다. 요청은 시간 정렬 6성분 cycle, piecewise-linear 또는 cubic-Hermite 재구성, material/calibration/provider/configuration digest, 사용권 및 물리 적용성 review, 값 closure와 기울기 closure 한도 및 quadrature budget을 고정한다. cubic-Hermite cycle은 stress/strain 기울기 시작-끝 차이도 검사하고 caller 한도를 넘으면 aggregate를 차단한다. provider callback은 각 경로점에서 순간 비음수 damage rate를 반환하고, adaptive composite Gauss-Legendre 적분이 sample interval별 손상을 수렴 tolerance 안에서 누적한다. provider identity mismatch, 음수/비유한 rate, open cycle, 미수렴 적분이나 비유한 합계에서는 aggregate를 제공하지 않는다. memoryless rate만 지원하며 stateful internal variable, cycle interaction, law calibration/qualification을 만들지 않는다. 공개 contract/schema, capability/source/interface catalog, method note와 합성 API wiring 예제를 추가했다. 예제 constant rate는 물리 모델·검증 데이터가 아니다. 계산 회귀 및 패키징은 지시대로 미실행이다.

## 2026-10-30 — 수송 기반 틈부식 간극 되먹임

`solve_crevice_transport_recession_feedback`와 `CreviceTransportRecessionFeedback`를 추가했다. 연속 출력 시각을 구간으로 나눠 각 구간을 시작 시점 slit geometry에서 고정형상 restricted transport로 계산하고, 선택 금속 종의 signed cellwise wall ledger를 caller 몰질량·밀도·검토된 reactive-wall 면적으로 cell-average recession으로 변환한다. 다음 구간의 aperture/area를 갱신하고 셀 inventory를 보존하도록 concentration을 remap한다. 두 반응면 동일 recession, 금속 종/ledger 의미, aperture 적용 범위 및 operator-split review를 요구한다. campaign-wide species balance residual/limit과 구간 입력 digest를 결과에 남기며 지원 aperture 밖으로 나가면 계산을 중단한다. 후속 소스 점검에서 시간·ledger·농도 shape, 음수/비유한 값과 remap tolerance 경계를 강화했다. API 범위 문서와 공개 schema/source/capability/interface catalog를 갱신했다. Catalog generation 및 101-item source AST/path audit만 수행했고 계산 테스트·패키징은 실행하지 않았다. 감사 결과는 101 rows, 216 source paths, 318 component links, missing path 0, unmapped component 0, AST parse error 0이다.

## 2026-10-29 — 선형 점탄성 gasket–bolt 시간 이력 평형

`fabrication.gasket_prony_joint_history`를 추가해 이미 등록된 caller Prony branch 재료 계약을 선형 탄성 bolt와 하나의 시간별 압축 접촉 평형으로 연결했다. 각 구간에서 선형 strain 경로에 대한 Maxwell branch stress를 닫힌형식으로 갱신하고, endpoint 변형률에 대해 affine인 force balance를 직접 풀어 gasket/bolt force와 잔차를 낸다. geometry, 초기 internal stress, calibration·사용권, piecewise-linear update와 model applicability review를 gate로 둔다. 접촉분리·인장 gasket 응력·지원 strain 초과는 `out_of_scope`로 정지하며 flange 공간장·leakage는 포함하지 않는다. 예제, API 안내, 전용 설명, registry, source/capability catalog, public schema와 model reference를 갱신했다. Static registry/example-key reconciliation은 330개씩 일치하고, 계산 테스트·패키징은 실행하지 않았다.

## 2026-10-29 — 폐합 다축 텐서 work-life API

`fatigue.closed_tensor_work_life`는 caller가 분리한 ordered closed 3D stress/strain tensor cycle에서 trapezoidal work를 적분하고, 같은 material condition의 positive caller calibration 범위 안에서만 log-log life 보간을 한다. Tensor/engineering shear convention과 endpoint closure tolerance, source SHA-256, five review gates를 명시하고 모든 cycle이 유효할 때만 Miner 합을 낸다. Rainflow 추출, 미관측 경로 재구성, calibration extrapolation 또는 universal nonproportional law는 추론하지 않는다. 근거 설명, two public schemas, synthetic example, catalog와 model reference를 연결했다. 수치 테스트와 패키징은 실행하지 않았다.

## 2026-10-29 — 사용자 정의 수용액 질량작용 network

`chemistry.aqueous_mass_action_speciation`를 추가했다. 종별 charge, caller fixed gamma와 초기 dimensionless activity, user reaction의 stoichiometry/log10 K, 그리고 임의 선형 analytical/charge balance를 묶어 square system으로 검증한다. 로그 활동도 natural coordinates에서 caller residual scale을 적용한 damped Newton solve를 구현했다. Equation row-normalization 후 구조 rank를 확인하고, 매 iteration에서 Jacobian rank/condition number를 검토하며 singularity, condition-limit, nonfinite step, line-search failure, iteration exhaustion을 별도 종료 사유로 보존한다. 초기 활동도 범위와 maximum condition threshold를 계약화했다. 자동 charge balance·gamma/ionic-strength iteration·기상/고상·침전 대체를 하지 않는다. 여러 종·반응/제약 contracts, synthetic diprotic-acid example, schema, source/capability/model reference와 API/전용 안내를 추가했다. Registry와 JSON example key는 331개씩 정적 대조됐다. 테스트나 계산 실행·패키징은 하지 않았다.

## 2026-10-29 — provenance 기반 용접 희석 조성 및 공분산 전파

`welding.dilution_with_uncertainty`를 추가했다. Caller가 고정한 base/filler/previous-layer 용융 질량과 source ID·SHA-256이 연결된 원소 질량분율로 혼합 조성을 계산한다. Missing assay를 0으로 처리하지 않는다. 선택한 모든 constituent-element 조합의 full joint covariance를 exact variable order와 함께 받으면 mass-weight Jacobian으로 출력 조성 공분산과 caller coverage-factor expanded uncertainty를 전달한다. 무작위 상관은 full covariance 안에 caller가 선언하며 독립성을 자동 가정하지 않는다. Melt mass는 exact input이고 burnoff/segregation/weldability 판단은 범위 밖이다. Registry, example, source/capability, schema, API/전용 문서에 연결하고 계산 테스트·패키징 없이 정적 catalog/schema/AST 감사만 실행했다.

## 2026-10-29 — 고정 단일 고체 분할수송의 활동도 provider 연결

기존 `EquilibriumReactiveTransport`가 phase projection의 모든 gamma를 1로 제한하고 `activity_provider_id`를 거절하던 경계를 수정했다. 이제 수송 request에 고정된 provider ID/configuration SHA-256과 활동도·tracer diffusivity 검토가 있으면 Python callback을 transport chemical-potential drift와 초기/시간별 단일 고체 phase projection에 함께 적용한다. callback은 species × (mouth + cells) 순서의 유한 양수 gamma를 반환하고, phase projection 시각의 절대 clock과 현재 농도를 받는다. 각 셀의 초기 phase gamma는 첫 callback 값과 일치해야 한다. callback이 누락되거나 범위·형상이 틀리면 aggregate 계산을 중단한다. 전기화학 및 CO₂ campaign 경로로 callback을 전달하고, 원래 digest 및 고정 geometry/operator-split 경계를 보존한다. 일반 수용액 종분화, 경쟁 다상, 동시 평형, 침전 속도론과 moving boundary는 구현하지 않았다. API·workflow·source basis·scope audit 문구를 갱신하고 정적 카탈로그 생성을 수행했으며, 수치 테스트는 실행하지 않았다.

## 2026-10-29 — 비선형 bolt/gasket 곡선 평형 API

`fabrication.nonlinear_bolt_gasket_contact`를 추가했다. caller가 권한·재료·조건 적용성을 검토한 signed bolt force-change/extension 표와 gasket force/compression 표로 단일 자유도 준정적 접촉 평형을 푼다. 초기 bolt clamp는 초기 gasket 압축 곡선에서 정하고, 외부 분리 하중과 free-length 변화를 포함한다. 폐쇄 접촉은 곡선 지원구간 교집합 안에서 단조 잔차를 bisection으로 풀며, 분리 상태는 bolt curve가 지원할 때 gap을 별도로 계산한다. 외삽하지 않고 두 원본 곡선 ID·SHA-256을 결과에 남긴다. 이 모델은 사용자가 공급한 equivalent assembly response를 쓸 수 있지만 flange 공간 휨·경로 의존 hysteresis·leakage·acceptance는 계산하지 않는다. registry/capability/source/schema/example/API/reference/backlog에 연결했고, 정적 카탈로그·AST 경로 감사만 생성했다. 수치 테스트와 패키징은 실행하지 않았다.

## 2026-10-29 — pCN subset simulation callback API

`reliability_sampling.run_subset_simulation(limit_state, request)`를 추가했다. Seeded PCG64 independent standard-normal latent population 뒤에 pCN reversible proposal rejection chain을 사용하고, caller limit-state callback에 어떤 MatIntegrity model이든 조합할 수 있게 했다. 각 level의 threshold, conditional fraction, cumulative/log partial estimate, proposal acceptance와 evaluator digest를 저장한다. MCMC correlation을 무시한 iid confidence interval은 만들지 않으며 threshold 정체·level cap은 `needs_data`로 돌린다. Public request/level/result schema, example, scope note와 batch110 회귀 입력을 추가했다. 테스트는 실행하지 않았다.

## 2026-10-29 — 평균응력 포함 변형률-수명 계산

`fatigue.morrow_strain_life`와 `fatigue.swt_strain_life`를 추가했다. Morrow는 인장 양(+) 평균응력을 fatigue strength coefficient에서 빼고 elastic Basquin term을 조정하며 SWT는 최대응력-변형률 진폭 곱에 맞춘 fatigue life root를 구한다. logarithmic cycle coordinate에서 root를 찾아 수치 overflow를 줄이고, 입력계수·재료 적용성 검토와 유효 cycle interval 밖 외삽 금지를 계약화했다. 독립 합성 예제·회귀 입력·문서를 추가했고 batch109를 HPC 목록에 등록했다. 회귀는 실행하지 않았다.

# 2026-10-29 — 범용 부식률 시나리오 교환 경로

## 2026-10-29 — EBSD 상 지도 면적 집계와 공개자료 확보

## 2026-10-29 — 상지도 연결 topology descriptors

`phase_map_topology.summarize_phase_map_topology()`를 추가했다. 선택 4/8 연결성에서 범주별 component 수·크기·ROI/결측 경계 접촉과 이웃 label 사이 격자 edge 및 픽셀 크기 기반 길이를 반환한다. 기존 digest/review 계약을 재사용한다. grain sizing, stereology, 3D interface area, 물성, 위험 또는 acceptance로 해석하지 않는다. 합성 예제·제한 문서·typed schema·capability/source basis를 더하고 batch108 회귀를 HPC manifest에 등록했다. 로컬 pytest와 Nurion 제출은 하지 않았다.

`phase_map_data.summarize_phase_label_map()`을 추가해 사용자 정수 상 라벨 배열, ROI mask와 missing mask의 dtype/shape/content digest를 검증하고 균일 픽셀 면적의 상별 pixel/area fraction을 계산한다. 미분류 영역과 missing area를 분리 보존하며 통계적 불확도는 생성하지 않는다. `phase_label_map_to_observations()`는 사용자 불확도와 basis, scale·ROI·label mapping review를 요구해 `PhaseFractionObservation`에 명시적으로 연결한다. 예제, 문서, source/capability/schema와 batch106 회귀를 갱신했다. Zenodo API로 Aalto 자료의 CC BY 4.0·크기·제공자 MD5를 확인해 제외 원자료 cache에 고정했다. CPR metadata에서 세 map의 1245×934 shape, grid-distance 0.1 및 DefDAP가 요구하는 orientation group의 부재를 확인했다. DefDAP 1.3 optional reader는 SHA-pinned archive에서 선택 `.cpr/.crc`만 안전하게 추출하고 raw labels·digest·provider metadata를 반환한다. 누락 orientation은 temp reader input에만 identity placeholder를 쓰며 원래 member hash를 남긴다. `batch107` mock regression과 실제 세 map aggregate validation command를 manifest에 추가했다. 생성 source/capability/schema 문서는 갱신했다. local pytest와 Nurion job submission은 하지 않았다.

대기부식 fitted model과 aggregate validation report에 holdout input digest를 추가해 calibration·holdout partition revision을 별도로 추적하도록 했다. 원 관측 행은 결과에 복사하지 않는다. batch95의 digest handoff 회귀는 Nurion manifest에 추가했다.

대기부식 1년 fit의 source-separated transfer gate에 그룹별 최대 log-RMSE와 절대 log-bias 제한을 추가했다. row-weighted 평균이 작은 독립 source group의 큰 오차를 희석하지 못하도록 record count 및 지원이탈률과 함께 source group별 진단을 보존한다. group별 진단이 없는 legacy caller model은 자동 자격으로 보지 않는다. masking 합성 회귀 batch94를 manifest에 추가했고 계산 및 실제 공개자료 재검증은 Nurion 일괄실행 전이다.

황화물 qualification record 진단 결과에 원 record의 source group, canonical digest, Evidence와 관측 요약을 넣어 envelope 범위 판단의 근거를 결과에서 재추적할 수 있게 했다. record/envelope 식별·설명 필드의 공백값도 계약에서 거절하며 회귀 batch93을 등록했다.

황화물 applicability envelope가 참조하는 qualification record를 ID 연결에 그치지 않고 envelope의 material/condition, sulfur definition·unit/basis, flow/deposit descriptor와 quantity·temperature·absolute pressure·duration 범위에 직접 대조한다. record별 boolean diagnostic과 유효 record가 뒷받침하는 envelope 목록을 출력하고 지원하지 않는 envelope는 선택하지 않는다. batch92 회귀를 HPC 명세에 추가했으며 모델 curve나 규격 판단을 추가하지 않았다.

NORSOK 전용 시나리오 외부에서 재사용하도록 CorrosionRateProjectionRow와 corrosion.model_output_rate_wall_loss_scenario를 추가했다. dataset/group/record IDs, source role, SI rate, archive digest와 evidence를 보존하고 simulated output과 caller assumption을 구별한다. 물리 시편은 경험 관측 계약에 남기고, 혼합 source group/revision/role과 근거 해시 불일치는 거절한다. NORSOK typed row adapter, 합성 JSON 예제, schema/API/capability 문서, batch77 HPC 명세를 추가했다. 신규 pytest는 로컬에서 실행하지 않았고 Nurion에도 제출하지 않았다.

## 2026-10-29 — 용접 잔류응력 불확도 구간의 support 확인

응력 중심값과 expanded-uncertainty 폭을 개별 확인하던 결과에 uncertainty interval 전체의 provider stress support 포함 여부를 추가했다. 중심값 자체가 범위 안이어도 불확도 상단이 밖으로 나가는 합성 회귀를 batch80에 추가했다. 실행은 Nurion 일괄 검증 대기.

같은 평가 결과에 지원범위 외 전체 record ID와 application subset ID를 추가해 계산 완료 상태를 application coverage로 혼동하지 않게 했다. regression은 batch81에 등록했으며 기존 의미의 실험 qualification은 하지 않았다.

## 2026-10-29 — 용접 잔류응력 qualification metric 단위 계약

Holdout metric 관측치와 허용상한의 unit token을 개별 기록하고 exact match를 강제한다. 조용한 단위 혼용으로 provider qualification gate가 잘못 통과하는 일을 막으며 자동 단위 환산은 도입하지 않았다. 네 개의 잔류응력 입력 계약 schema를 공개 exporter에 추가하고 batch82에 거절 회귀를 등록했다.

## 2026-10-29 — 용접 잔류응력 source-group partition 격리

Calibration, holdout, application partition 사이 source-group 재사용을 모두 거절하고, 결과에 partition별 record ID를 반환하도록 했다. 회귀는 source-group 누수 거절 및 비-application row와 application handoff의 분리를 batch83에서 확인하도록 구성했다. 로컬 계산 테스트 및 Nurion 제출은 하지 않았다.

비교 결과에 원 record/support Evidence와 provider/source/dataset digest 및 revision 계보를 포함했다. 후속 소비자가 결과만 받아도 출처를 감사할 수 있도록 provenance 회귀를 batch84에 등록했다.

Application 행의 총 입력 수와 비교된 행 수를 분리하고, unmatched/ambiguous ID를 unsafe application 목록에 포함시켰다. 매칭 행의 공간 좌표 차원 및 범위 이탈도 구체적 사유 코드로 출력한다. 이 handoff 경계 회귀를 batch85에 등록했다.

잔류응력 좌표 record/support에 coordinate-frame definition SHA-256을 명시해 같은 frame ID 문자열이 다른 원점·회전 정의를 가리키는 경우 비교를 차단한다. 회귀는 batch88이며 frame registration 및 surveyed transformation 자체를 검증하지 않는다.

같은 provider/frame 기준 후보에서 component definition만 달라 정확 매칭되지 않는 application record에는 reason code를 반환한다. 성분 불일치가 빠진 결과 전달을 개선하며 회귀 batch89에 등록했다.

복수의 동일 identity support가 일치하는 application은 비교를 생략하고 ambiguous reason을 보존해 downstream coverage를 실패 처리하는 회귀를 batch90에 등록했다.

## 2026-10-29 — 국부 용접 열처리 band dwell-time 보간

온도 샘플 양 끝점이 모두 유지 band 안에 있는 구간만 세던 추정을, 각 인접 샘플 사이 선형온도 경로가 band와 겹치는 시간만 적분하는 방식으로 변경했다. 센서별 최소 dwell 산출은 유지하면서 비정렬·비단조 온도 이력에도 구간별 적용한다. 새 수치 회귀는 batch79에 등록했고 실제 온도장 재구성이나 금속학적 qualification은 주장하지 않는다. pytest/Nurion 대기.

## 2026-10-29 — 최초 통과 입력 provenance 검증

`SampledLinearThicknessFirstPassage`에서 nested source lineage의 finite number를 재귀 검사하고 공백 review reference를 거절한다. 경계 회귀 두 건을 batch78 파일에 추가했다. 공개 schema 재생성, Ruff, HPC manifest, 권리 메타데이터 및 배포 archive 포함 감사는 통과했다. pytest는 실행하지 않았고 Nurion 제출도 하지 않았다.

## 2026-10-29 — 공개 NORSOK grid의 계보 보존 통계 API

`WetCo2SimulationGridSummary`는 동일 pinned source digest와 provider row identity를 요구하고, caller 선택 행의 SI 변수 및 부식률을 최솟값·최댓값·산술평균·균등행 선형 경험 분위수로 요약한다. 출력은 제공 모델 행의 기술통계로만 명시하고 physical observation, failure probability, calibration readiness를 추론하지 않는다. NORSOK 공급자 결과를 실험 시편 관측으로 위장해 기존 `CorrosionRateSampleSummary`에 넣지 않도록 독립 data adapter에 유지했다.

합성 workbook 경계 회귀, 합성 데이터 사용 예제, schema·catalog·설명서를 추가했다. Ruff 정적 검사만 수행하고 회귀 테스트 및 실데이터 실행은 Nurion용으로 대기시켰다.

## 2026-10-29 — 공개 NORSOK 기반 wet-CO₂ grid reader

`WetCo2SimulationGridRow`와 `read_wet_co2_simulation_grid(path)`를 추가했다. 고정 workbook SHA-256, 최대 파일 크기, 한 시트, 열 순서, 단위표와 243개 숫자 행을 확인한 뒤 온도·압력·효율·부식률을 지정 단위에 따라 SI로 변환한다. dataset DOI, provider row, archive digest, CC BY 4.0 attribution을 각 record에 붙이고 model output·비실측·비보정 의미를 명시했다. 공개 자료 자체는 로컬 제외 `data/raw`에 유지하고 소스 배포물에 넣지 않는다.

합성 workbook 기반 단위·provenance 회귀를 추가해 batch75에 연결했다. API 안내, 실행 예제, capability·source catalog와 공개 schema를 갱신했다. Ruff·format 및 HPC manifest 정적 검사는 완료했으며 pytest와 실데이터 reader 실행은 하지 않았다.

## 2026-10-29 — 고정 퓨가시티 CO₂ 평형 입력 시나리오 앙상블

기존 고정 퓨가시티 carbonate 평형 입력 전체를 각 시나리오에 보존하는 `chemistry.fixed_fugacity_carbonate_scenario_ensemble`을 추가했다. caller-normalized weights와 분포 의미, 모든 시나리오 결과 및 input digest를 기록한다. 모든 행이 계산될 때만 가중 기술 통계와 관측행 기반 비보간 경험 분위수를 반환한다. 미해결 행 하나라도 있으면 부분 집계를 제공하지 않으며, 시나리오 가중치를 사건확률이나 부식률 분포로 바꾸지 않는다.

합성 JSON 예제, wet-CO₂ capability·source catalog, 생성 API 참조, 공개 schema와 batch74 검증 명세를 갱신했다. Ruff 검사·형식은 완료했다. pytest와 계산기 회귀는 실행하지 않았고 Nurion에도 제출하지 않았다.

## 2026-10-29 — 쿠폰 질량손실 공분산 불확도 모듈

기존 균일 질량손실 계산을 보완하는 `corrosion.coupon_loss_with_uncertainty`를 추가했다. caller-corrected 질량손실·노출면적·밀도·기간과 네 입력의 전체 공분산을 받고, 시편·조건군·출처·검토 ID와 evidence를 출력 digest에 보존한다. 대칭 양의 준정부호를 상관행렬로 정규화해 검증하고 1차 델타법으로 평균 침투량 및 속도의 표준불확도를 각각 전파한다. 기간 불확도는 속도에는 영향을 주지만 관측된 누적 침투량에는 영향을 주지 않는 수학 항등을 회귀 명세에 포함했다.

세정/blank 보정은 caller 입력에 맡기고 어떤 표준의 수치 기준도 복제하지 않는다. 출력 표준불확도는 신뢰·예측구간이 아니며 국부손상, 수명, FFS, 합격 또는 위험확률을 뜻하지 않는다. 합성 API 예제, API/개발 안내, 공개 schema와 batch67 회귀 작업을 추가했다. Ruff·형식 및 manifest·release-rights metadata·public-source-boundary 검사는 통과했지만 pytest는 실행하지 않았고 Nurion 작업도 제출하지 않았다.

다음 단계에서 검토된 쿠폰 입력을 `CorrosionRateObservation`으로 변환하는 typed adapter를 추가했다. rate sample summary는 새 optional measurement-standard-uncertainty와 per-observation evidence를 요약 분위수와 분리해 내보내고, deterministic rate-quantile forecast도 그 lineage를 보존하지만 uncertainty를 예측에 혼합하지 않는다. Interface catalog와 batch68에 교환 회귀를 더했으며 현재 통합 검사는 여전히 누리온에서 대기 중이다.

표본 요약은 N×N measurement-error covariance를 선택적으로 받아 observed rate의 산술평균 표준불확도를 계산하도록 확장했다. 행렬은 관측 입력 순서, 대각과 각 행 표준불확도의 정합, symmetry, PSD 검증을 받는다. 동일 결과에서 between-specimen sample SD는 따로 보고하며 오차가 미상/의존성 불명일 때 임의 독립 합산하지 않는다. 수치 단위 회귀·잘못된 상관행렬·누락 marginal uncertainty 확인을 batch69에 적재했고 실행은 Nurion 대기 중이다.

사용자 파일 연결을 위해 `CorrosionRateSampleSummary`용 nested JSONL group profile·helper·합성 fixture 및 `CorrosionRateObservation`용 specimen CSV profile/helper를 추가했다. strict tuple evidence field import를 위해 importer에 `json_tuple` parsing을 추가했다. JSONL/CSV source hash·profile/schema/record digest, unknown field 거절, covariance inconsistency 회귀를 batch70에 등록했고 미실행이다.

`corrosion.rate_joint_scenario`는 경험 표본 요약을 caller-created rate ensemble과 혼동하지 않게 별도의 완전 시나리오 입력 계약을 둔다. 원 시나리오 digest, 각 rate·weight·ID, weight meaning, 표본 계보와 세 가지 적용성 검토 ID를 유지한다. 고정 선형 두께 계산은 요구두께 도달시간·임계 초과질량·관통 질량을 내며 임계 초과를 `EventProbability`가 아니라 declared-weighted mass로만 보고한다. synthetic JSON registry example, 기술문서, 회귀 및 HPC batch71을 추가했다. `integration.corrosion_rate_joint_scenario`는 상위 모듈로 표본 계보와 시나리오 계산 입력 타입을 연결한다. 로컬 테스트와 Nurion 제출은 미실행이다.


## 2026-10-29 — AquaSolDB 공개 기체 용해도 자료 연결

AquaSolDB v2.1의 versioned Zenodo archive를 취득하고 제공자 MD5 및 고정 SHA-256을 확인했다. compiler CC BY 4.0은 컴파일 편집본에만 적용되고 개별 실험 측정은 원 출처별 인용·권리 검토가 필요하므로 ZIP은 `data/raw` 전용 경로에 보관한다. CO₂ 용해도 7,194행을 검토해 압력 기준, 매질, 방법, flags, 이온 조성 누락과 온도/압력 span을 aggregate audit에 남겼다. 저압 순수물·partial-CO₂·무표식 탐색 필터는 41행/8개 원 출처를 찾지만 Henry 계수나 보정 자료로 자격화하지 않는다.

고정 v2.1 digest와 schema를 확인하는 독립 typed reader를 추가했다. reader는 원 수치를 caller process로 읽으며 Henry conversion, fugacity 계산, 용해도 단위 변환 또는 corrosion fit을 수행하지 않는다. Public audit, source attribution/rights notes, schema, capability interface와 batch65 회귀 입력을 기록했다. 미실행 회귀는 누리온 묶음에 남겼고 데이터 감사 결과에는 pointwise value나 source citation text를 넣지 않았다.

다음 구현 단계에서 조건 명시형 조회 계약과 독립 Henry/fugacity 단일점 비교 adapter를 추가했다. 조회 상한 초과를 오류로 처리하고 기본 선택은 measured·무표식·온도/압력 보유 행으로 제한한다. 비교는 부분 CO₂ 압력 기준·온도·용매 digest·명시 Henry convention 및 원 논문 권리검토에 대한 사용자 확인을 요구하며, 단위 변환에 필요한 물 질량농도와 expanded uncertainty를 외부 입력으로 받는다. 행에서 Henry 계수를 맞추거나 부식률을 추론하지 않는다. 공개 schema/interface 카탈로그를 갱신하고 회귀를 batch66에 추가했으나 테스트는 로컬 실행하지 않았다.

## 2026-10-29 — 고정 fugacity wet-CO₂ 탄산계 평형 API

사용자가 공급하고 검토한 CO₂ fugacity, 용매 조성 hash에 맞는 Henry 계수, 활동도 상수 및 총알칼리도를 받아 고정 기상 저장고 조건의 수용액 탄산종과 pH를 풀이하는 모듈을 추가했다. 고압 fugacity 자체와 기체-액체 계면은 외부 공급자로 남기며, Henry/EOS 파라미터를 내장하지 않는다. 탄산계 전용 알칼리도 닫힘과 온도·출처 계보 확인을 적용한다. 합성 해석 예제, API 설명, 공개 스키마와 batch64 회귀 입력을 추가했고 예제·capability·source catalog를 갱신했다.

검증계획은 닫힌형식 합성 상태, 알칼리도 잔차 민감도, review gate, 용매 hash/온도 불일치, 범위 밖 pH 구간 및 JSON registry 경계다. Ruff 정적 점검과 manifest 검사는 통과했지만 pytest는 실행하지 않았고, 누리온 계산도 제출하지 않았다. [USGS PHREEQC 문서](https://water.usgs.gov/water-resources/software/PHREEQC/documentation/phreeqc3-html/phreeqc3-17.htm)는 기체 fugacity/용해 접근의 근거로만 연결한다. NIST 수치 표 데이터는 복제하지 않는다.

## 2026-10-29 — Corrosion quantile forecast 배포물 확인

Wheel, source distribution, source-review ZIP을 다시 만들고 archive membership를 확인했다. Wheel에는 models/corrosion.py와 설치 catalog, source archive에는 신규 pytest 파일·Python 예제·상세 문서·CorrosionRateQuantileForecast schema가 있고 review ZIP에도 코드·문서·schema가 포함됐다. 세 배포물 경로/확장자 감사에서 PDF·OPJU·XLSX·raw data 경로는 발견되지 않았다. Package audit file count는 wheel 262, sdist 1535, review ZIP 1528이다. 이는 배포물 구조 확인일 뿐 legal/scientific qualification 또는 pytest 실행이 아니다.

## 2026-10-29 — 경험 분위수에서 고정 두께 시나리오로 연결

corrosion.rate_quantile_forecast는 시편 표본 요약에서 정확히 선택한 경험 분위수를 기존 일정 균일손실 두께 계산에 전달한다. 재료상태 적합, 시험에서 설비 조건으로의 속도 전이, 선형손실 적용성을 호출자가 각각 확인하지 않으면 실행하지 않는다. 결과에 선택 분위수와 계산 속도, 시편·관측 ID, 조건/출처 group 및 조건서명 digest를 보존한다. 분위수 수준은 신뢰수준이나 사건확률이 아니며 결과는 결정론적 두께 시나리오에 한정한다.

합성 JSON/Python 예제, 경계 문서, 공개 schema, capability/API 참조, batch63 회귀 입력을 추가했다. Ruff, source boundary/rights metadata audits, 93-task manifest 및 모델-예제 ID 집합 정적검사는 통과했다. pytest와 HPC 계산은 실행하지 않았다.

## 2026-10-29 local-capacity corrosion scenario schema export

`ProfileCapacityCorrosionScenario`가 registry와 model reference에는 있었으나 independently consumable public JSON Schema 목록에는 빠져 있어 `scripts/export_schemas.py` import/contract inventory에 추가했다. exporter는 현재 545개 고유 schema를 기록하며 `docs/schemas/ProfileCapacityCorrosionScenario.json`을 생성했다. 데이터 입력이나 계산 의미는 변경하지 않았다. schema export와 exporter Ruff 정적검사만 확인하고 pytest는 실행하지 않았다.

## 2026-10-29 chronoamperometry polarity-separated charge summaries

기존 `corrosion.chronoamperometry_window_summary`에 positive/negative polarity별 gross charge를 추가했다. 각 piecewise-linear 구간의 내부 0 교차점을 analytically 분할해 적분하며 signed·absolute charge와 함께 반환한다. 출력 극성은 전류 부호만 뜻하고, 리뷰된 계측 부호 basis 없이는 anodic/cathodic 의미를 붙이지 않는다. background·capacitive·부분반응 전류를 분리하지 않으므로 금속 용출량이나 pit loss로 해석하지 않는다. 폐형식 직선신호와 표본 사이 부호반전 회귀를 batch55에 등록했다. 기존 공개 SECCM trace reader와 같은 trace provenance·창·부호 검토 계약을 사용한다. 로컬 pytest와 누리온 실행은 하지 않았다. 검증 manifest는 85개 task (`0–84`)다.

## 2026-10-29 축방향·시간별 부식률 격자 연동

`structural.profile_capacity_rate_field_scenario`를 추가했다. 사용자가 각 프로파일 절점 및 시간 knot에 제공한 부식률 격자를 시간 방향 piecewise-linear로 적분하고 각 지점의 누적 손실을 잔여두께 프로파일에 반영한 뒤 기존 용량 공급자를 다시 사용한다. 예측기간은 자료의 시간 지원 안으로 제한하고, 속도 외삽·절점간 보간 및 rate fitting을 수행하지 않는다. 일정 균일 속도와 기존 시나리오의 등가성, 부분 최종구간 해석적 적분, 격자 shape·지원 범위 검사를 batch54 HPC task로 등록했다. 예제와 사용 한계를 추가했다. 로컬 pytest와 누리온 제출은 하지 않았으며, manifest는 84 task (`0–83`)다.

## 2026-10-29 균일 부식 시나리오 기반 두께 프로파일 용량 재평가

`structural.profile_capacity_corrosion_scenario`를 추가해 caller 지정의 균일 두께손실률과 기간을 기존 axial profile capacity에 적용한다. 같은 참조 압력·벌징 provider를 재사용하고 기준/예측 압력차, 변화량, 예측 최소두께와 지배 window를 내보낸다. 0 ligament, 기준 입력 부적합과 provider 범위 이탈은 용량 수치 생성 없이 상태로 보존한다. 완전한 FFS, 수명, 파손확률, acceptance는 계산하지 않는다. 합성 예제·한계 문서·집중 회귀 입력과 batch53 HPC task를 등록했으며 manifest/PBS/Slurm은 83 task (`0–82`)로 갱신했다. 정적 검사만 진행하고 pytest와 누리온 제출은 하지 않았다.

# 개발 기록

## 2026-10-29 — 상분율 선형 대비와 교차 공분산

기존 phase-fraction 비교가 개별 관측만 다루는 점을 보완해 `materials.phase_fraction_linear_contrast`를 추가했다. 한 물리 시편·영역·측정법에 대해 사용자가 상 ID와 선형 대비 계수, 요구 범위, 확장 공분산 행렬을 공급한다. 행렬은 관측 ID 순서를 고정하고 측정별 확장불확도 제곱과 대각값이 일치해야 하며 대칭·양의 준정부호를 검사한다. 결과는 `aᵀx`와 `sqrt(aᵀCa)`의 결정론적 확장구간으로 한정하고, 누락 공분산은 독립으로 대체하지 않고 `needs_data` 처리한다. 공개 NIST TN 1297 근거와 독립 산술 정의를 source catalog에 기록했으며, capability·Registry·JSON 예제·API 참조·공개 schema·한국어 방법 문서·회귀 입력을 연결했다. batch105에는 신규 계약, 전 모델 예제 및 HPC contract 검사가 포함된다. 로컬 pytest와 Nurion 제출은 하지 않았다. 정적 lint/format/compileall, manifest/PBS 범위 확인은 완료했다.

## 2026-10-29 — 부식속도 시편 표본 계약 보강

`corrosion.rate_sample_summary`를 추가해 한 연구·조건의 시편별 단일 균일손실 속도를 정리한다. 입력 계약은 observation/physical-specimen ID, 재료, SI 속도, 조건 서명, 조건 그룹, 측정법과 출처 그룹을 함께 요구한다. 시편 중복, metadata 혼합, 공백 식별자, 빈 조건, 중복되거나 역순인 분위수 선택을 거부한다. NumPy 선형 경험 분위수와 최솟값·최댓값을 산출하고 원 행 식별자를 유지한다.

결과에 독립성·측정불확실성·대표성·전이가능성은 포함하지 않는다. 분위수는 신뢰/예측구간, 손실률 보수값, 수명 또는 고장확률로 해석할 수 없다. 공개용 합성 API 예제, 설명문서, 세 계약 스키마, capability/source/API 참조와 batch62 HPC 회귀 입력을 추가했다. Ruff 검사·포맷과 92-task PBS/Slurm manifest, 모델-예제 ID 집합 정적 검사는 통과했다. pytest 및 원격 HPC 계산은 실행하지 않았다.

## 2026-10-29 수용액 탄산계 알칼리도 종분포

`chemistry.carbonate_alkalinity_speciation`을 추가했다. 호출자 제공 pH 활동도, 총알칼리도, 온도별 activity-basis K1/K2/Kw, gamma 계수와 제공자 lineage로 탄산계·물 종분포를 계산하고 알칼리도 closure를 확인한다. 총알칼리도 expanded uncertainty는 다른 입력을 고정한 정확 선형 민감도로 종별 전달하고 확률로 해석하지 않는다. 가스-액 평형·기상 CO2 압력·추가 완충종·부식률은 평가하지 않는다. 공식 USGS 근거, 상세 한국어 문서, 합성 예제, 공개 schema와 wet-CO2 partial capability 연결을 추가했다. focused 회귀를 batch58에 추가했으며 테스트와 누리온 작업은 실행하지 않았다.


## 2026-10-29 직교 두께 지도 및 유한저항 갈바닉 모듈

`geometry.rectilinear_thickness_map`은 불균일 직교 셀 면적·결측 범위·signed 두께손실·임계 셀 연결영역을 요약한다. 연결성은 `four_neighbour`(변 공유) 또는 `eight_neighbour`(변/꼭짓점 접촉)로 선택 가능하고, 기본값은 이전 동작과 맞춘 4방향이다. 면적가중, 결측 보존, 임계 비교는 그대로 유지한다. 대각선 접촉 회귀는 batch56 작업에 포함했다.

`degradation.galvanic_resistive_coupling`은 비선형 분극곡선 두 개와 명시적 유한 직렬저항의 piecewise-linear 평형을 곡선 범위 안에서 푼다. 두 API의 적용 한계와 합성 입력을 등록하고 공개 계약·스키마·능력 추적 및 88-task HPC manifest에 연결했다. 정적 린트와 배포 아카이브 포함 검사는 통과했다. focused 테스트는 로컬에서 실행하지 않고 누리온 batch56/57 검증 묶음에 남겼다. 직교 두께 지도 상세 범위는 `RECTILINEAR_THICKNESS_MAP_KO.md`를 참고한다.

## 2026-10-29 PBS/Slurm 배열 사전검사

`scripts/validate_hpc_manifest.py`가 종전 Slurm 배열만 검사하던 범위를 PBS `#PBS -J` 선언까지 확장했다. manifest task 수와 두 scheduler의 inclusive start/end index를 각각 비교하고 결과 JSON에도 두 범위를 보존한다. PBS 범위 불일치 거부 회귀를 batch51의 기존 HPC task-contract 파일에 추가했다. 실제 PBS/Slurm 제출은 하지 않았다.

## 2026-10-29 HPC 결과 collector 무결성 계약

`hpc_collect.py`를 재구성해 매 task result의 schema/index/name/manifest digest, 예상 명령 수와 하위 command 종료상태를 교차 확인한다. JUnit 누락·손상도 문제 및 실패 인덱스로 보존한다. 정상 결과, 잘못된 task identity/command count, 상위 status와 다른 하위 실패를 다루는 합성 회귀를 `tests/test_hpc_collect.py`에 추가하고 batch52로 등록했다. manifest는 82개 작업, PBS/Slurm 범위는 0–81이다. 로컬 pytest와 누리온 실행·제출은 하지 않았다. HPC 실행절차 문서를 현재 PBS bundle·array·collector 계약으로 교체하고 이전 49/50/76 task 설명을 제거했다.

## 2026-10-29 PBS 병렬 bundle 작업 수 자동화

`hpc/pbs_bundle.sh`가 작업 인덱스 0–75를 하드코딩해 manifest의 batch50을 빠뜨리던 문제를 개선했다. 실행 전 Python validator로 manifest/Slurm 배열 계약을 확인하고 JSON task count로 범위를 계산한다. `MATINTEGRITY_PBS_WORKERS`는 1–64로 검증하며 기본값은 16이다. 회귀는 HPC bundle 계약 테스트를 batch51에 추가하고 PBS/Slurm array를 0–80으로 맞추었다. 파일 패턴/Ruff/manifest 정적 확인만 하였고 제출하지 않았다.

## 2026-10-29 Neuber-to-strain-life 연계 모델

`fatigue.neuber_strain_life_chain`을 추가했다. 노치 계산이 검토되고 수렴한 때만 국부 변형률 진폭을 기존 strain-life 식에 연결한다. 노치 단계 미검토/미수렴이면 life 연산을 스킵하고, 수명 근이 보정 주기 범위를 벗어나면 국부 응답은 보존하되 수명값을 생성하지 않는다. 반복 검증은 batch50에 연결했고 로컬 pytest와 누리온 실행은 하지 않았다. 모델/예제 276개, capability 479개로 생성 카탈로그를 갱신했다.

## 2026-10-29 Neuber 노치 변형률 진폭 계산기

`fatigue.neuber_notch_strain_amplitude`를 추가했다. 호출자가 검토한 단축 명목 응력 진폭, 탄성 Kt, 탄성계수, 반복 강도계수와 경화지수로 Neuber/Ramberg–Osgood 교점을 이분법으로 계산한다. 국부 변형률 진폭·탄성/소성 분리·Neuber 잔차를 제공하며 기존 strain-life API에 호출자가 연결할 수 있다. 수명, 다축 효과, 평균·잔류응력, notch gradient 및 승인 판정은 범위 밖이다. 예제 key를 registry와 맞추고 회귀 테스트를 batch50에 등록했다. 로컬 pytest와 누리온 실행은 하지 않았다. Registry 275개, 실행 예제 275개, 능력 항목 478개, 독립 구현 근거 307개, HPC manifest task 80개로 갱신했다. 공개 계약 schema export는 543개로 유지된다.

## 2026-10-29 공개 배포물 재생성 및 경계 감사

Neuber 계산기 반영 이후 source review ZIP, wheel과 sdist를 다시 생성하고 실제 archive member를 검사했다. wheel 256개, sdist 1,490개, source review 1,483개 파일에서 차단 suffix와 경로를 검사해 통과했다. 신규 `fatigue.py`는 wheel에, Neuber 집중 회귀 파일은 sdist에 포함된 것을 확인했다. `validation/package_audit.json`과 `dist/checksums.json`을 갱신했다. 이 검사는 archive 포함 경계만 확인하며 법률 검토 또는 물리 qualification이 아니다.

## 2026-10-29 누리온 기존 회귀 결과 분석 및 보완

기존 누리온 PBS 작업 `24229540.pbs`가 71개 task 이후 exit status 123으로 종료했다. 회귀는 2,333건 중 25건 실패했다. 8 pytest shard 모두 같은 `test_model_examples` 입력의 asset/location/time context와 synthetic `RunContext` 불일치를 여러 건 포함했고, 예제 coverage 누락 35개도 확인했다. 테스트는 예제 입력에 선언된 context를 전달하도록 수정했고 마지막 24개 domain fixture example을 채워 274개 모델의 exact coverage 회귀를 복원했다. FABEST full numeric scan에서는 실제 workbook의 빈 CSV 필드를 비수치 오류로 처리해 중단했다. iterator에 선택적인 `preserve_empty_fields` 정책을 추가해 공란을 `None`으로 보존하고 비공란 비수치/비유한 값과 ragged row는 계속 거절하며, full scan 결과에서 공란 수를 집계한다. 기존 스냅샷 Ruff format 실패도 로컬에서 정리했다. 이 수정은 새 batch49에 추가했으나 pytest는 아직 로컬/누리온 어느 쪽에서도 재검증하지 않았고 새 누리온 작업을 제출하지 않았다.

registry 274개와 `examples/model_inputs.json`을 대조해 남아 있던 예제 누락 24개를 각 도메인 회귀 fixture로 채웠다. 마지막 추가는 세 제작/운송 campaign, 9개 NDE campaign family, 6개 material/시험 campaign, bonded-layer/casting-forging, brazing/production-weld/hardness/repair-weld contract를 포함한다. 총 274개 example key와 registry ID가 일치하도록 coverage regression을 exact set equality로 복구했다. 각 예제는 동작 계약 및 synthetic evidence 예시이지 현장 qualification이 아니며, batch49에서 context-aligned execution을 누리온 회귀 대상으로 둔다. 이번 입력은 로컬에서 모델 실행하지 않았다.

## 2026-10-29 Mendeley 304L chloride-SCC 자료의 비공개 구조 감사

Mendeley Data version 1의 dataset-level CC BY 4.0 선언을 확인하고, 원자료는 ignored local cache에만 취득했다. 외부 ZIP(81,799 bytes), 내부 ZIP(327,326 bytes), workbook(327,096 bytes)의 관측 SHA-256을 고정했다. dataset version과 local digest는 재현성을 위한 프로젝트 pin이며 provider checksum 검증이 아니다. 집계 감사는 workbook 5 sheet와 550 formula cell을 확인했으며 sheet name hash, reported dimensions, nonempty cell/formula counts만 JSON에 기록한다. 한 sheet가 16,384 columns로 표시되어 수작업/서식 영역의 유효 범위 정리가 필요하다. 수식 계산값, 단위·시험조건 연결, replicate/specimen 계층, third-party rights를 확인하지 않았으므로 데이터 행 reader·SCC 성장 적합·검증 calibration은 만들지 않았다. 합성 workbook audit 테스트를 batch48에 등록했고 local pytest는 사용자 지시에 따라 실행하지 않았다. HPC task manifest는 현재 80개 작업이다.

## 2026-10-29 NIST CORR-DATA 공개 데이터 감사와 schema export 식별성

Data.gov가 공개 NIST CORR-DATA ZIP과 NIST open-data 조건을 제공하지만, NIST의 자체 권리 설명은 SRD·NIST 창작물·외부 기여 자료를 구분하며 편집물의 250여 원 문헌별 권리는 일괄 해소하지 않는다. 고정된 354,591바이트 ZIP을 로컬 제외 캐시에 취득하고 제공자 SHA-256, ZIP member CRC/구성, CSV 24,721행·15열, 239 reference key, 필드 결측과 rate token 유형을 집계했다. 수치 scalar는 두 rate 열에 각각 5,896/5,823건, 범위 표기는 16/15건이며 나머지는 혼합 text/qualitative notation과 blank다. 원 행·인용문·점별 파생값을 내보내지 않는 audit API와 합성 parser fixture, rights-boundary 문서를 추가했다. 권리·단위·조건·독립성 검토 전 모델 적합과 공개 재배포는 보류한다.

JSON Schema 내보내기 계약 클래스 543개를 대조해 클래스명 중복 4쌍으로 실제 파일 539개만 남던 충돌을 찾았다. 중복 이름은 출처 모듈을 포함한 고유 파일명으로 내보내고 이전 충돌 alias 네 개는 제거하도록 했다. 합성 filename 회귀 테스트를 HPC batch47에 추가했다. 이번 변경 세 묶음은 로컬 단위 테스트로 실행하지 않았으며, NIST archive의 독립 구조 audit와 Ruff 정적 검사는 수행했다. HPC manifest는 76개 작업으로 확장했고 새 계산은 제출하지 않았다.

## 2026-10-29 atmospheric scenario ensemble 후속 배치

`degradation.atmospheric_scenario_ensemble`은 기존의 1년 대기 부식 예측 API를 각 사용자 시나리오에 그대로 적용한 뒤, 검토된 가중치 기반 산술평균·범위·가중 경험 분위수를 집계한다. 모델의 calibration support와 transfer gate를 그대로 유지하며, 실패하거나 지원범위를 벗어난 scenario가 있으면 요약을 중단한다. 가중치가 확률이라는 의미를 자동 부여하지 않으며 장기 성장·국부 침투·수명·위험도를 생성하지 않는다. 신규 입력 계약과 synthetic fixture 테스트 및 HPC batch44 항목을 추가했다.

## 2026-10-29 allowable properties·galvanic coupling·external pressure 병렬 배치

`materials.allowable_property_provider`는 기존 표형 물성 provider를 조합해 exact material/product/condition/orientation/property/basis/edition, caller entitlement, provider revision, applicability, 단위, 온도 support와 query/result digest를 감사한다. `degradation.galvanic_coupling`은 기존 mixed-potential 계산을 재사용하면서 electrode/metal/area/environment/reference/connection/resistance와 polarization support를 보존하고 signed net current와 partial dissolution observation을 분리한다. `structural.external_pressure`는 기존 외부압 provider 평가 위에 geometry/material/imperfection/boundary/load/pressure basis, solver/config/result digest, convergence와 calibration/holdout evidence를 묶는다. 외삽·규격표·부식률·수명·buckling solve·안전계수·자동 합격은 만들지 않는다.

직접 focused test 12건이 통과했다. 현재 273개 계산기, 100개 인터페이스, 474개 능력 항목(101 partial·0 planned), 301개 구현 근거, 539개 공개 schema와 72개 병렬 검증 작업이며 관리용 진행률은 76%다. 배치 42까지의 고정 71-task checkpoint는 오프라인 Python 3.12 wheelhouse를 사용해 누리온 작업 `24229540.pbs`로 제출했으며, 한 노드 64코어에서 최대 16개 task를 동시에 실행하고 마지막에 자동 집계한다.

## 2026-10-29 specification alias·certificate·CUI 병렬 배치

`materials.specification_aliases`는 기존 exact resolver를 조합해 caller-owned profile 집합, query coverage, ambiguity·unknown과 material family/condition binding을 감사한다. `materials.certificate_reconciliation`은 기존 multi-record 수치 대조 위에 document/product/heat/traceability identity와 chemistry·mechanical·heat-treatment·NDE·traceability coverage를 결합한다. `degradation.under_insulation`은 insulation/jacketing/coating/material/service/environment scope, ordered access·inspection·repair·reinstatement event, 명시적 접근 coverage와 moisture·visual·thickness·NDE observation을 보존한다. Fuzzy 등가성, 내장 규격값, 자동 재료승인, hidden-area 외삽, 부식률·수명·POD·위험도는 만들지 않는다.

직접 focused test 11건과 실제 HPC runner 70번 작업이 통과했다. 모델 레퍼런스 생성기는 검토된 합성 예제가 없는 신규 모델도 상태를 명시하고 중단 없이 문서화하도록 보강했다. 현재 270개 계산기, 100개 인터페이스, 474개 능력 항목(104 partial·0 planned), 298개 구현 근거, 526개 공개 schema와 71개 누리온 작업이며 관리용 진행률은 75%다.

## 2026-10-28 storage preservation·repair welding·test-water와 입력 pinning 병렬 배치

Storage-preservation campaign은 보존 구역·환경·격리 상태, ordered inspection/maintenance event와 포장·건조제·방청제·계측 evidence를 보존한다. Repair-welding campaign은 결함·제거·joint preparation, WPS/용접재료/heat, ordered weld·열처리·검사·보수 event를 기록한다. Test-water-quality campaign은 수원·처리·회수·배출, sampling context와 caller가 보고한 화학·미생물·부식 coupon·육안 evidence를 다룬다. 세 모델 모두 caller가 제공한 판정 기준만 적용하며 부식률·잔여수명·균열성장·규격 주기·WPS 자격·화학종 변환·MIC 판정을 자동 생성하지 않는다.

표형 입력 profile에 선택적 원본 SHA-256과 대상 계약 schema digest를 추가했다. 따라서 원자료 또는 설치된 입력 계약이 고정 기준과 달라지면 import 단계에서 명시적으로 중단된다. 신규 집중 테스트 18건과 실제 HPC runner 69번 작업이 통과했다. 현재 267개 계산기, 100개 인터페이스, 474개 능력 항목(107 partial·0 planned), 295개 구현 근거, 513개 공개 schema와 70개 누리온 작업이며 관리용 진행률은 74%다.

## 2026-10-28 replica·chemical cleaning·weld hardness와 tabular CLI 병렬 배치

Replica-metallography campaign은 component/location/material/service history, surface preparation, replica medium, magnification, calibration과 정량·정성 microstructure observation을 보존한다. Chemical-cleaning production campaign은 chemical batch, ordered fill/circulate/soak/rinse/neutralize/dry event, process conditions, coupon/solution/surface/residue/chemistry/NDE와 waste disposition을 다룬다. Weld-hardness mapping은 weld/WPS/heat/consumable/material, cross-section coordinate frame, traverse와 caller-assigned base/HAZ/fusion/weld region point를 보존한다. 이미지 자동분석·반응속도·부식률·scale 변환·강도추론·HAZ 자동분류·규격 acceptance는 하지 않는다.

`matintegrity import-tabular` CLI를 추가했다. 모델 ID로 레지스트리에 등록된 입력 계약만 선택하고 임의 module/class import를 허용하지 않는다. Profile·source와 출력 record를 JSON으로 감사할 수 있지만 모델 실행과 `RunContext`는 별도 단계다. 신규 집중 테스트 16건과 실제 HPC runner 68번 작업이 통과했다. 현재 264개 계산기, 100개 인터페이스, 474개 능력 항목(110 partial·0 planned), 292개 구현 근거, 491개 공개 schema와 69개 누리온 작업이며 진행률은 73%다.

## 2026-10-28 인장시험·표면청정도·접합층과 실제 tabular 예제 병렬 배치

Tensile campaign은 specimen/product/heat/orientation/geometry, machine/load-cell/extensometer calibration, temperature/strain rate, offset definition과 reported modulus/yield/UTS/elongation/reduction-area를 보존한다. Surface-cleanliness production campaign은 substrate/area/previous coating, ordered preparation events, ambient/surface/dewpoint와 salt/dust/profile/oil/visual/roughness 측정을 다룬다. Bonded-layer campaign은 substrate/layer/interface/process geometry, ordered preparation/application/cure history와 thickness/adhesion/shear/peel/porosity/disbond/continuity/NDE evidence를 보존한다. Caller 기준만 사용하며 곡선 재계산·이미지 판독·failure mechanism 자동판정·규격 acceptance·qualification은 하지 않는다.

CSV parser는 quoted field 내부 줄바꿈을 보존하고 profile의 scalar target과 nested target prefix 충돌을 실행 전에 거절한다. `examples/tabular_contract_import.py`는 합성 JSONL 두 행을 실제 공개 `MaterialDesignation` 계약으로 가져와 source/profile/record digest를 출력한다. 신규 집중 테스트 16건과 실제 HPC runner 67번 작업이 통과했다. 현재 261개 계산기, 100개 인터페이스, 472개 능력 항목(111 partial·0 planned), 289개 구현 근거, 467개 공개 schema와 68개 누리온 작업이며 진행률은 72%다.

## 2026-10-28 hardness·production weld·casting/forging과 선언형 데이터 연결 병렬 배치

Hardness campaign은 subject/location/material/heat, method/scale/load/dwell/indenter, instrument/reference block, surface/spacing/thickness와 reading uncertainty를 보존한다. Production weld test campaign은 weld/joint/WPS/welder/consumable/base heat, coupon extraction과 bend/tensile/impact/hardness/macro/NDE/chemistry evidence를 다룬다. Casting/forging quality campaign은 route, forging-ratio 정의 또는 casting process, heat treatment, sampling orientation과 dimensional/surface/internal/macro/micro/chemistry/mechanical observation을 보존한다. 모두 caller 기준만 사용하고 공식 변환·규격 validity·허용결함·WPS 또는 재료 qualification을 주장하지 않는다.

`tabular_contract_import`는 사용자 CSV/JSONL을 공개 Pydantic 계약에 연결한다. Profile이 source/target 경로, string/integer/number/boolean/json 파싱, 필수성과 unmapped-field 정책을 명시하며 `eval`, 단위 추정·변환, 보간과 누락값 보충을 하지 않는다. Source SHA-256, profile digest와 imported-record digest를 남기고 거절 finding에는 원 셀 값을 복제하지 않는다. 신규 집중 테스트 14건과 실제 HPC runner 66번 작업이 통과했다. 현재 258개 계산기, 100개 인터페이스, 470개 능력 항목(112 partial·0 planned), 286개 구현 근거, 444개 공개 schema와 67개 누리온 작업이며 진행률은 71%다.

## 2026-10-28 충격시험·brazing/bonding·운송설치와 공개 source 경계 병렬 배치

충격시험 campaign은 specimen/product/heat/orientation/notch/dimension, 시험온도, 장비·striker·교정, reported energy·lateral expansion·shear fracture와 독립성·불확도를 보존한다. Brazing/bonding production campaign은 base/filler/adhesive lot, surface prep, fit-up, atmosphere/flux, ordered thermal-pressure-cure cycle과 destructive/NDE/leak/strength/continuity evidence를 다룬다. Transport/erection campaign은 lift·transport·storage·support identity, ordered handling event, acceleration/load/orientation/temperature/humidity/impact, temporary support와 alignment/geometry/damage-survey/NDE를 보존한다. 모두 caller profile만 적용하며 공식 validity·구조해석·자동 손상·규격 허용값·qualification은 제공하지 않는다.

공개 source 선택을 archive 생성 전에 감사하는 경로를 추가했다. Allowlist 밖의 raw/derived/evidence/artifacts/tmp, PDF·OPJU·workbook 등 제한 binary, 로컬 절대경로와 원 프로젝트 문서 제목·저자 표식이 있으면 실패한다. 자체 audit 출력을 집계에서 제외해 반복 실행 결과가 안정적이며, 현재 1,292개 선택 파일의 경계 검사가 통과했다. 47개 dataset·283개 source 권리 metadata 감사도 finding 0건이다. 이는 구조적 누락 검사이지 법적 clearance가 아니다. 신규 집중 테스트 13건과 실제 HPC runner 65번 작업이 통과했다. 현재 255개 계산기, 99개 인터페이스, 467개 능력 항목(113 partial·0 planned), 283개 구현 근거, 418개 공개 schema와 66개 누리온 작업이며 진행률은 70%다.

## 2026-10-28 wall tolerance·overlay/cladding·파괴인성과 HPC 실행계약 병렬 배치

제품·형상·구역별 nominal wall과 반복 측정·비대칭 caller 허용차를 비교하는 profile을 추가했다. Forming allowance와 corrosion allowance는 제조 허용차 판정에 숨게 혼합하지 않고 별도 record-only 필드로 보존한다. Overlay/cladding은 substrate·filler lot·layer/pass·heat history와 dilution·composition·thickness·ferrite·bond·continuity/NDE evidence를 caller 기준으로 평가한다. 파괴인성 campaign은 시험편 형상·방향·온도·loading·fatigue precrack·reported K/J/CTOD/arrest 값과 validity flags를 보존한다. 규격표, 공식 validity 규칙, 설계 허용값, 재계산과 qualification은 내장하지 않는다.

누리온 실행기를 점검해 focused `pytest` 작업이 manifest의 `paths`를 처리하지 못하던 결함을 수정했다. 이제 해당 작업도 JUnit을 생성하고 집계기가 이를 포함하며, result에는 Python executable과 핵심 runtime version이 기록된다. 새 사전검사는 manifest schema, 8개 shard의 정확한 순서·완전성, 고유 작업명과 Slurm `0-64` 범위를 확인한다. 신규 집중 테스트 16건과 실제 HPC runner의 64번 작업이 통과했다. 현재 252개 계산기, 99개 인터페이스, 465개 능력 항목(114 partial·0 planned), 280개 구현 근거, 395개 공개 schema와 65개 누리온 작업이며 진행률은 69%다.

## 2026-10-28 고온·도장·파동검사와 API 581 수치 provider 병렬 배치

산화·황화·침탄·질화·금속학적 시효에 공통인 ordered 고온 노출·측정 이력, 도장 campaign/lot의 표면처리·batch·경화·두께·접착·기공·holiday evidence, AE/GW의 array·baseline·reference·channel/coverage 품질 평가를 추가했다. 모든 판정 한계는 caller profile에서만 오며 자동 손상 검출·크기 산정·POD·규격 적격성은 주장하지 않는다.

고정 API 581 저장소의 실제 `frequency/adjusted` 및 `reliability/poisson-probability` 계산을 호출하는 독립 provider를 추가했다. 합성 GFF `1e-4/year`, management factor `0.5`, caller-reviewed damage factor `2.0`에서 연간빈도 `0.0001/year`, 1년 확률 `9.99950001666625e-05`를 얻고 독립식과 일치시켰다. 실제 설비 PoF나 공학 qualification이 아니다. 신규 집중 테스트 18건과 catalog 감사 테스트가 통과했다. 현재 251개 계산기, 97개 인터페이스, 463개 능력 항목(115 partial·0 planned), 279개 구현 근거, 374개 공개 schema와 64개 누리온 작업이며 진행률은 68%다.

## 2026-10-28 국부환경·다중환경 재료·전자기검사와 native consequence 병렬 배치

Galvanic couple, crevice와 under-deposit에 공통인 ordered local-environment history API를 추가했다. 전극 기준이 명시된 potential, current, species, pH와 불확도·결측을 보존하며 galvanic series나 부식률을 내장하지 않는다. Polymer, seal, composite에는 material state와 복수 exposure, media concentration, property retention/swelling/mass/strength evidence를 연결했다. Caller가 명시한 경우에만 시간축 내부 선형 보간을 하고 외삽하지 않는다. Eddy-current와 MFL에는 probe/sensor/magnetizer, excitation/lift-off/speed, reference feature, scan/channel coverage, staged sensitivity/noise/resolution/drift campaign 검사를 추가했다.

고정 consequence toolkit의 native passive-plume primitive를 MatIntegrity provider 요청에서 실제 실행했다. Caller가 제공한 합성 source, wind와 sigma로 농도 `0.002546479089470325 kg/m³`를 얻고 실제 ProviderResult binding을 통과했다. 자동 모델 선택, 기상 추정, dense-gas 대체, 현장 검증 또는 qualification은 없다. 신규 집중 테스트 18건이 통과했다. 현재 249개 계산기, 94개 인터페이스, 458개 능력 항목(115 partial·0 planned), 278개 구현 근거, 350개 공개 schema와 63개 누리온 작업이다. 외부 native 물리 계산 milestone을 반영해 진행률은 67%다.

## 2026-10-28 구조 공급자·볼트 체결부·영상검사와 실제 consumer 실행 병렬 배치

External-pressure, nozzle local-stress와 일반 FE 공급자 receipt에 mesh/frame/load case/result field, equilibrium/convergence/uncertainty/verification diagnostics와 caller acceptance profile을 연결했다. Bolted joint API는 직접 preload와 불확도, flange alignment, gasket compression/recovery, ordered thermal-pressure history와 leakage evidence를 보존한다. RT/PAUT campaign 모델은 reference feature와 pre/in-process/post verification, coverage, sensitivity/resolution을 caller criterion으로 평가한다. Solver, 토크 변환, 자동 flaw acceptance, POD 또는 내장 규격값은 제공하지 않는다.

API 581과 consequence 저장소를 catalog의 고정 commit으로 제외 checkout했다. MatIntegrity method-selection payload는 실제 API 581 input model과 계산을 통과했고, consequence payload는 실제 ProviderRequest와 evaluate_provider binding을 통과했다. External consequence engine과 numeric PoF provider는 실행하지 않았다. 신규 모듈 및 integration catalog 집중 테스트 16건이 통과했다. 현재 247개 계산기, 91개 인터페이스, 453개 능력 항목(115 partial·0 planned), 277개 구현 근거, 321개 공개 schema와 62개 누리온 작업이다. Consumer 실행 milestone을 반영해 관리 진행률은 66%다.

## 2026-10-28 remaining-strength·용접 compatibility·누설 campaign·권리감사 병렬 배치

Caller가 제공한 1~5차원 capacity surface에 대해 exact identity/unit/domain을 확인하고 다중선형 보간만 수행하는 remaining-strength API를 추가했다. 불확도 표본 중 최소 응답을 governing 값으로 유지하고 외삽과 clipping은 거절한다. 이종재 용접·오버레이/클래딩·소모재에는 chemistry/property/dilution/service facts, layer sequence와 caller envelope를 적용하는 compatibility API를 추가했다. Leak-rate·vacuum·cryogenic 시험에는 reference leak, blank/background, 상태 identity, repeatability, drift와 uncertainty/detection evidence를 caller criterion으로 감사하는 세 모델을 추가했다. 어느 경로에도 코드식·규격표·내장 합격기준이 없다.

공개 배포 권리 metadata 감사는 47개 데이터셋의 license URL, rights evidence, acquisition policy, limitation, asset URL/checksum 상태와 276개 구현 근거의 reference/derivation/reuse 필드를 검사한다. 감사 과정에서 Hannover weld와 UCI 2개 자료의 공급자 체크섬 미제공 상태를 명시적으로 기록했다. 구조 감사는 통과했지만 법률 검토 완료를 뜻하지 않는다. 집중 테스트 19건이 통과했다. 현재 245개 계산기, 88개 인터페이스, 448개 능력 항목(115 partial·0 planned), 294개 공개 schema와 61개 누리온 작업이며 진행률은 65%다.

## 2026-10-28 caller-profile 재료·표면검사·SCC·POD 병렬 배치

규격 alias는 namespace·designation·edition·product form·condition의 exact caller mapping만 해석하고 fuzzy 추론을 하지 않는다. 재료 인증서 대조는 caller-owned chemistry/mechanical 범위, 명시적 Pint 단위 규칙, heat/lot/profile, 측정 불확도 구간과 missing/unknown/mismatch를 행 단위로 보존한다. Visual·PT·MT 공통 표면 indication API는 caller procedure와 acceptance profile만 적용하고 accept/reject/review/insufficient-evidence를 분리한다. 세 SCC 스크리닝 모델은 환경·재료·응력 facts와 사용자 rule을 사용하며 unknown을 screen-out하지 않는다. POD 캠페인 감사는 표본, hit/miss, flaw-size bin, operator/material/geometry/access, blind와 specimen 독립성 coverage를 모델 적합 전에 검사한다. 어느 경로도 내장 규격값, qualification, 물리 검증 또는 failure probability를 주장하지 않는다.

집중 테스트 21건이 통과했다. 현재 242개 계산기, 85개 인터페이스, 442개 능력 항목(115 partial·0 planned), 275개 구현 근거, 270개 공개 schema와 59개 누리온 작업이다. 전체 회귀와 배포물 재생성은 `0-58` 배열로 이관했고, 독립 물리 검증이 늘지 않아 진행률은 65%다.

## 2026-10-28 pinned raw-schema validation 병렬 배치

API 581 PoF-method request와 consequence provider request를 실제 고정 raw schema bytes에 검증하는 경로,
schema audit/finding을 deterministic compatibility receipt로 연결하는 경로를 추가했다. Schema hash,
required, closed properties, enum/pattern/format와 request digest 불일치를 거절한다. 해시가 맞는 원문만
`artifacts/external-schemas` 제외 캐시에 atomic write하는 취득 스크립트와 synthetic fetch 검사를 추가했다.

현재 239개 계산기, 81개 인터페이스, 435개 능력 항목(115 partial·0 planned), 274개 구현 근거,
239개 공개 schema와 58개 누리온 작업이다. Schema 검증은 성공했지만 consumer 실행과 독립 물리검증은
아직 없어 진행률은 65%다.

## 2026-10-28 pinned external-schema adapter 병렬 배치

API 581 고정 공개 schema의 PoF-method-selection closed input과 consequence toolkit의 provider-request
required/closed shape를 raw bytes SHA-256으로 대조했다. 전자는 외부 numeric PoF 필드가 없어 방법 선택만
보내고 숫자 비전송 승인을 요구한다. 후자는 pressure/composition/time/event 의미를 허용된 settings
extension에 원 handoff digest와 함께 보존하고 source term을 caller/provider 입력으로만 받는다. 외부
schema 원문을 저장하지 않는 구조 audit record도 추가했다.

현재 239개 계산기, 77개 인터페이스, 431개 능력 항목(115 partial·0 planned), 274개 구현 근거,
234개 공개 schema와 57개 누리온 작업이다. 상대 저장소를 import·실행·수정하지 않았고 end-to-end 및
독립 물리검증은 아직 없어 진행률은 65%다.

## 2026-10-28 타 저장소 교환 계약 병렬 배치

API 581 damage/inspection/PoF record, integrity event에서 외부 source/release/consequence로 넘기는 handoff와
단계별 result record, producer/consumer schema·revision·canonical payload digest·field decision을 고정하는
compatibility receipt를 추가했다. Damage factor/POD/spatial probability를 PoF로, wall loss를 opening으로,
consequence를 failure probability로 자동 변환하지 않는다. 세 계약군 집중 테스트 15건을 작성했다.

`api581-risk-analysis`와 `process-risk-consequence-toolkit`의 reviewed commit·license evidence·관찰한 공개
계약과 요청서를 `data/catalogs/github_integrations.json`에 기록하고 offline audit를 추가했다. 현재
239개 계산기, 74개 인터페이스, 428개 능력 항목(115 partial·0 planned), 274개 구현 근거, 228개 공개
schema와 56개 누리온 작업이다. 상대 저장소 end-to-end 실행과 독립 물리검증은 미완료이므로 관리
진행률은 65%를 유지한다.

## 2026-10-28 AE 파속·용사 기공률·열해석 수렴 병렬 심화 배치

Known-source geometry와 arrival pick으로 homogeneous AE wave speed/clock offset을 보정하는 경로,
caller-segmented pore area의 field/replicate porosity와 불확도/holdout 비교, 외부 thermal solver의 ordered
space-time refinement level을 동일 query에서 비교하는 진단을 추가했다. 세 경로는 source/specimen/
partition/support와 provider·input·result digest를 보존한다. Pick·segmentation·PDE를 생성하지 않고
anisotropy, pore class, 수렴 증명, 판정, 수명 또는 확률을 추론하지 않는다. 집중 테스트 13건과 strict
JSON 예제 3개가 통과했다.

GitHub 공개 API로 `api581-risk-analysis`와 `process-risk-consequence-toolkit`의 고정 commit·공개 계약
구조를 다시 확인하고, 상대 저장소를 수정하지 않은 상태에서 두 개의 구체적 확장 요청서를 추가했다.
현재 239개 계산기, 71개 인터페이스, 425개 능력 항목(115 partial·0 planned), 274개 구현 근거,
212개 공개 schema와 54개 누리온 작업이다. 독립 물리·현장 검증이 늘지 않아 진행률은 65%다.

## 2026-10-28 AE pick·용사 두께 불확도·열이력 비교 병렬 심화 배치

검토된 원 waveform의 threshold/AIC 원표본 arrival pick, 반복 thermal-spray thickness의 calibration·
measurement·repeatability 불확도 결합, 외부 solver와 측정 transient temperature의 정렬된 residual·
weighted bias/RMSE/MAE 비교를 추가했다. 세 경로 모두 digest, sensor/instrument/provider identity,
support와 calibration/holdout partition을 보존하며 event 분류, image segmentation, 자체 PDE, 판정,
수명 또는 확률을 생성하지 않는다. 집중 테스트 13건과 strict JSON 예제 3개가 통과했다.

현재 236개 계산기, 71개 인터페이스, 422개 능력 항목(115 partial·0 planned), 271개 구현 근거,
212개 공개 schema와 53개 누리온 작업이다. 전체 회귀·release 재생성은 누리온에 남겼고 독립 물리·
현장 검증이 늘지 않아 관리 진행률은 65%를 유지한다.

## 2026-10-28 AE·thermal-spray·열물성 보정 병렬 심화 배치

고정 wave speed와 다중 sensor arrival pick의 weighted nonlinear source localization, calibrated thermal-
spray cross-section의 thickness/area porosity, 외부 provider baseline/sensitivity 기반 transient thermal
parameter calibration을 추가했다. 세 경로 모두 partition/support와 immutable identity를 보존하고 event
분류·pore 분류·자체 PDE solver·판정·수명·확률을 만들지 않는다.

BAM CC BY 4.0 controlled-source AE text 자료 13개 파일·2,355,730바이트를 provider MD5로 고정했다.
11 waveform·180,224표본, 4 sensor coordinates, 2 source coordinates와 event table 87행을 감사했다.
Source 좌표 불일치와 C_A2 channel 10 누락으로 자동 위치추정 연결은 보류했다. 집중 테스트 18건,
strict JSON 예제 3개와 변경 lint가 통과했다. 현재 233개 계산기, 71개 인터페이스, 419개 능력 항목
(115 partial·0 planned), 268개 구현 근거, 212개 공개 schema와 52개 누리온 작업이다. 독립 물리검증이
늘지 않아 진행률은 65%다.

## 2026-10-28 성형·코팅·replica 정량 병렬 심화 배치

명시적 원/최종 두께·내측반경에서만 surface strain과 thinning을 요약하는 성형 이력, SI force/area와
독립 provider stress의 bias를 분할 보정하는 pull-off adhesion, calibrated replica field의 feature density·
area fraction·nearest-neighbor spacing을 계산하는 기하 경로를 추가했다. 세 모델 모두 caller threshold나
feature label을 판정·손상등급·수명·확률로 바꾸지 않는다.

CC BY 4.0 wood coating adhesion workbook과 README 52,925바이트를 provider MD5로 고정했다. 35그룹·
107 raw replicate를 formula cell과 분리했고 단위·dolly geometry·break mode·calibration이 없어 원 단위를
미확정으로 유지한다. 신규 집중 테스트 17건, strict JSON 예제 3개와 변경 Ruff가 통과했다. 현재 230개
계산기, 70개 인터페이스, 415개 능력 항목(115 partial·0 planned), 265개 구현 근거, 209개 공개 schema와
51개 누리온 작업이다. 독립 물리검증이 늘지 않아 진행률은 65%다.

## 2026-10-28 단조 소성·음극방식·계장화 충격 병렬 심화 배치

Pre-necking 단조점의 Hollomon 가중 보정, reference-electrode/IR-drop/current identity를 보존하는
음극방식 현장조사, force-displacement valid window의 trapezoidal energy와 plateau peak를 요약하는
계장화 충격 경로를 추가했다. 모두 caller review와 digest를 필수화하고 외삽·내장 판정·수명·확률을
만들지 않는다.

CC BY 4.0 Zenodo 음극방식 자료에서 관련 CSV 5개와 workbook 1개만 선별 취득했다. DPlot 8곡선·
11,922표본을 검사했고, 모호한 potentiodynamic current-axis 지수는 변환하지 않았다. 신규 집중 테스트
17건, 엄격 JSON 예제 3개와 변경 Ruff가 통과했다. 현재 227개 계산기, 69개 인터페이스, 411개 능력
항목(115 partial·0 planned), 262개 구현 근거, 207개 공개 schema와 50개 누리온 작업이다. 독립 물리
검증이 늘지 않아 진행률은 65%다.

## 2026-10-28 인증서·진공시험·이종용접 병렬 심화 배치

복수 재료 인증서 기록을 caller requirement와 불확도 구간으로 대조하는 하위 모델, 독립 blank/test
절대압력 slope의 known-volume net throughput 모델, base/layer/fusion-boundary/thermal/environment identity를
보존하는 이종용접 evidence 조정 모델을 추가했다. 인증서 계산기의 최초 ID가 상위 capability와 충돌해
기술 전체를 구현으로 잘못 승격시킨 것을 발견하고 `materials.multi_record_certificate_reconciliation`로
좁혀 115개 partial 상태를 복원했다.

CC BY 4.0 pressure-decay workbook 78,721바이트를 provider MD5로 고정하고 10개 series·310표본을 감사했다.
설명상의 reference 구성과 ambient/internal temperature 구분이 workbook에서 확인되지 않아 계산 입력으로
자동 변환하지 않는다. 현재 224개 계산기, 68개 인터페이스, 407개 능력 항목(115 partial·0 planned),
259개 구현 근거, 205개 공개 schema와 49개 누리온 작업이다. 독립 물리검증이 늘지 않아 진행률은 65%다.

## 2026-10-28 마모·경도·인장 병렬 심화 배치

`degradation.archard_wear_coefficient_calibration`은 한 접촉 regime의 유효 관측에서 dimensionless
Archard 계수를 적합하고 지원범위 안의 holdout만 진단한다. `inspection.hardness_reference_block_calibration`은
인증값 불확도를 포함해 한 장비 configuration의 bias와 repeatability를 적합한다.
`inspection.tensile_offset_yield_curve`는 원 engineering stress–strain branch에서 가중 elastic line과
유일한 offset-line 교차를 계산한다. 세 경로 모두 분할 누출과 외삽을 차단하고 수명·합격·확률을 만들지 않는다.

CC BY 4.0 sapphire–copper tribology RDF metadata 57개 파일·15,578,599바이트를 취득하고 제공자 MD5를
전부 확인했다. 이 자료는 linked measurement 자체가 아니므로 metadata audit만 등록했다. 집중 테스트와
중앙 검증 후 현재 221개 계산기, 67개 인터페이스, 403개 능력 항목(115 partial·0 planned), 256개 구현
근거, 203개 공개 schema와 48개 누리온 작업이다. 독립 물리·현장 검증이 늘지 않아 진행률은 65%다.

## 2026-10-28 고분자·충식부식·기준누설 병렬 배치

`materials.polymer_arrhenius_shift_calibration`은 동일 formulation/state/endpoint의 유효한
calibration 자료로 자연로그 time-shift를 reciprocal temperature에 가중 적합한다.
`degradation.erosion_corrosion_power_law_calibration`은 한 regime의 결합 손실률을 velocity와
particle concentration의 power law로 적합하고 2D calibration hull 밖 holdout을 거절한다.
`inspection.reference_leak_response_calibration`은 traceable molar reference leak과 instrument response의
고정 log–log 회귀를 제공하며 non-detect/censored/missing을 대체하지 않는다.

CC0 ESCAPE‑1 파일 12개·2,309,115 byte를 취득해 제공자 MD5를 전부 확인했다.
독립 reader가 11 workbook의 118,606개 time–ppm·m 표본, 헤더, 시각순서, 유한·비음수
응답과 SHA-256을 검사했다. 제공자 slpm의 참조상태와 release/background window가 없어
molar calibration에 자동 연결하지 않았다. 자료 전체는 `data/raw/`에 두고 배포물에서 제외한다.

세 계산기·reader 집중 검사 18건이 통과했고 strict JSON 예제 3개는 `computed`다.
현재 218개 계산기, 66개 인터페이스, 399개 능력 항목(115 partial·0 planned), 253개 구현
근거, 201개 공개 schema와 47개 누리온 작업이다. 실제 시편·장비 자격화가 늘지 않아
전체 진행률은 65%를 유지한다.

## 2026-10-28 수명·민감도·실가스 누설 심화 병렬 배치

`materials.strain_life_coefficient_calibration`은 분리된 elastic/plastic strain amplitude의 calibration failure만 사용해 Coffin–Manson–Basquin 계수를 두 단계 가중 log-linear 적합하고 holdout failure를 사후 평가한다. Runout·검열은 실패로 대체하지 않는다. `creep.accelerated_lognormal_rupture_fit`은 rupture density와 right-censor survival likelihood를 결합한 고정 accelerated lognormal 회귀이며 holdout을 calibration stress-temperature hull 안에서만 평가한다.

`reliability.sobol_replicate_stability`는 caller가 제공한 동일 설계계열의 first/total Sobol replicate를 모아 분산·범위·순위 안정성을 진단한다. 새 지수를 추정하거나 dependent-input 결과를 independent Sobol effect로 바꾸지 않는다. `thermo.gas_pressure_decay_inputs_from_coolprop`는 세 절대압·온도 상태의 compressibility factor와 phase, CoolProp 판본·리비전·상태 digest를 기존 gas-inventory balance에 전달한다.

크리프 계산기 ID가 상위 capability ID와 충돌해 기술 전체를 구현으로 승격시키는 문제를 중앙 통합에서 발견하고 하위 ID로 수정했다. 따라서 115개 partial 상태는 유지된다. 신규 계산기 집중 검사 13건과 CoolProp/기존 압력감쇠 16건이 통과했으며 strict JSON 예제 3개는 `computed`다. 현재 215개 계산기, 65개 인터페이스, 395개 능력 항목(115 partial·0 planned), 250개 구현 근거와 199개 공개 schema다. 독립 검증이 늘지 않아 진행률은 65%를 유지한다.

## 2026-10-28 소성·POD·동적 신뢰도 보정 심화 병렬 배치

`materials.cyclic_ramberg_osgood_fit`은 calibration 안정화 진폭 자료만으로 `log(σa)=log(K′)+n′log(εp,a)`를 가중 적합하고 holdout log-bias/RMSE를 사후 평가한다. 응력과 탄성계수 단위가 정확히 같지 않거나 holdout이 calibration plastic-strain 지원범위를 벗어나면 중지한다.

`inspection.signal_response_pod_calibration`은 고정 threshold와 normal-residual log(size)-linear signal 모델을 calibration에서만 적합한다. Censored/missing 값은 대체하지 않고 holdout 분류·log score·Brier·표준화 잔차를 보고한다. `reliability.ctmc_generator_calibration`은 calibration 전이수/상태 노출로 generator를 만들고 holdout Poisson score를 평가한다. 0-rate 모순은 clipping하지 않는다. 둘 다 현장 확률·규격합격·stationarity·FTA 확률을 자동 주장하지 않는다.

`under_insulation_inputs_from_condensation_result`는 완전한 결로노출 결과만 받아 보수적 결로 가능 상태를 CUI 노출계약에 연결하고 원 결과 digest와 “측정 습윤이 아님”이라는 의미를 보존한다. 이를 정식 통합 인터페이스로 등록했다.

소성 단위 보강을 포함한 신규 계산기 focused test 14건, adapter 3건과 관련 기존 경로 9건 등 집중 검사 26건이 통과했다. Strict JSON 예제 3개는 모두 `computed`, registry/example ID는 212개로 일치한다. 현재 212개 계산기, 64개 인터페이스, 391개 능력 항목(115 partial·0 planned), 247개 구현 근거와 199개 공개 schema다. 독립 물리·현장 검증이 늘지 않아 진행률은 65%를 유지하고 전체 회귀·release는 누리온에 남겼다.

## 2026-10-28 대기부식·산화·상관사건·단열 결로 심화 병렬 배치

`degradation.atmospheric_multi_year_loss_history`는 caller-qualified 1년 손실과 시간지수로 지원기간 안의 `loss(t)=loss₁tⁿ` 이력만 계산한다. `degradation.nonisothermal_parabolic_oxidation`은 온도 이력을 rate-table knot에서 분할하고 선형 `k(T)`를 적분해 산화막 두께 제곱 증가량을 계산한다. 둘 다 외삽과 내장 재료표를 금지하고 독립 calibration/holdout 근거를 요구한다.

`reliability.binary_event_pair_calibration`은 물리 sequence/source/independence group이 분리된 이진 사건쌍 관측으로 2×2 확률표·주변확률·공분산·phi 및 holdout log/Brier score를 계산한다. 미래기간·인과·FTA 확률을 만들지 않는다. `fabrication.insulation_condensation_exposure`는 검토된 외표면 온도와 이슬점, weather-barrier 상태로 결로 가능시간을 계수한다. `thermo.insulation_condensation_inputs_from_coolprop`는 dry-bulb·상대습도·절대압에서 CoolProp HAPropsSI 이슬점을 만들고 판본·리비전·상태 digest를 보존한다.

Focused test 18건, 변경 Ruff와 strict JSON 예제 4개가 통과했다. Registry/example ID는 209개로 일치한다. 현재 209개 계산기, 63개 인터페이스, 387개 능력 항목(115 partial·0 planned), 244개 구현 근거와 199개 공개 schema다. 독립 물리·현장 검증이 늘지 않아 전체 진행률은 65%를 유지하며 전체 회귀·release 재생성은 누리온에 남겼다.

## 2026-10-28 수소 파괴·공식 FFS·크리프-피로·가스켓 병렬 배치

`fabrication.gasket_joint_evidence`, `degradation.hydrogen_fatigue_provider_evidence`, `degradation.hydrogen_cracking_provider_evidence`, `structural.pitting_ffs_provider_evidence`, `structural.creep_fatigue_interaction_provider_evidence`를 추가했다. 가스켓 경로는 직접 측정한 bolt preload와 seating·relaxation provider evidence를 보존하며 torque에서 preload를 추정하지 않는다. 수소 피로 경로는 absolute partial pressure와 fugacity를 구별하고, 수소 균열 경로는 K/J/CTOD endpoint를 바꾸지 않는다.

공식 FFS 경로는 외부 평가기의 geometry·inspection·material·load identity와 qualification evidence를 교환할 뿐 자체 FFS 식이나 capacity를 만들지 않는다. 크리프-피로 경로는 creep와 fatigue quantity를 별도로 보존하고 공급자의 exact interaction basis만 수신하며 독립 선형 손상합을 재계산하지 않는다. 다섯 경로 모두 합격, 성장, 수명, 확률 또는 규격 적합성을 추론하지 않는다.

Focused test 22건, 변경 Ruff와 strict JSON 예제 5개가 통과했다. Registry/example ID는 205개로 일치한다. 현재 205개 계산기, 63개 인터페이스, 383개 능력 항목(115 partial·0 planned), 240개 구현 근거와 199개 공개 schema다. 계획 상태가 사라져도 115개는 partial이며, 전체 회귀·release 재생성은 누리온에 남겼다. 독립 물리/현장 검증이 늘지 않아 전체 진행률은 65%를 유지한다.

## 2026-10-28 교체형 구조·형상 provider 병렬 배치

`fabrication.heat_exchanger_geometry_evidence`, `structural.external_pressure_provider_evidence`, `structural.nozzle_local_stress_provider_evidence`, `structural.finite_element_result_exchange`를 병렬로 추가했다. Heat-exchanger 경로는 shell/bundle/tube/tubesheet/baffle와 외부 coordinate payload를 shape/order/digest로 결속한다. External-pressure 경로는 measured imperfection field와 eigen/nonlinear provider result, calibration/holdout benchmark를 보존한다.

Nozzle 경로는 geometry/load/coordinate/mesh/result-location/averaging과 stress representation을 provider digest에 고정한다. FE exchange는 대형 배열 대신 node/element/region identity, connectivity/geometry/content digest, material assignment, load/boundary, step·time/frequency, field shape/order와 verification partition을 교환한다. 어느 경로도 메시 적격성, 규격 지수, 허용압력, 합격, 수명 또는 확률을 생성하지 않는다.

병렬 작업자와 중앙 검사를 합친 focused test 17건, 변경 Ruff와 strict JSON 예제 4개가 통과했다. Registry/example ID는 200개로 일치한다. 현재 200개 계산기, 63개 인터페이스, 378개 능력 항목(110 partial·5 planned), 235개 구현 근거와 199개 공개 schema다. 전체 회귀·release 재생성은 누리온에 남겼고 독립 물리/현장 검증이 늘지 않아 전체 진행률은 65%를 유지한다.

## 2026-10-28 성형·열교환기·극저온 밸브·peening 병렬 배치

`fabrication.forming_qualification`, `fabrication.tube_bundle_integrity_evidence`, `fabrication.cryogenic_valve_evidence`, `welding.peening_treatment_evidence`를 병렬로 추가했다. Forming 경로는 deformation metric과 forming/post-forming thermal history를 property evidence에 연결한다. Tube-bundle 경로는 tube location·geometry, support/baffle/vibration, operating clock, detection status와 caller disposition record를 분리해 보존한다.

Cryogenic-valve 경로는 body/seat/stem/seal, medium·pressure basis, thermal-pressure-actuation cycle과 leakage/torque/function observation의 below-detection/missing 상태를 유지한다. Peening 경로는 zone별 intensity/coverage와 좌표계·깊이·시편·source group이 붙은 residual-stress evidence를 비교한다. 어느 경로도 결함크기, 서비스 성능, 피로개선, 합격, 수명 또는 확률을 추론하지 않는다.

병렬 작업자와 중앙 검사를 합친 focused test 17건, 변경 Ruff와 strict JSON 예제 4개가 통과했다. Registry/example ID는 196개로 일치한다. 현재 196개 계산기, 63개 인터페이스, 374개 능력 항목(106 partial·9 planned), 231개 구현 근거와 199개 공개 schema다. 전체 회귀·release 재생성은 누리온에 남겼고 독립 물리/현장 검증이 늘지 않아 전체 진행률은 65%를 유지한다.

## 2026-10-28 사용자 규칙·특수 용접 qualification 병렬 배치

`fabrication.joint_efficiency_declaration`, `welding.temper_bead_qualification`, `welding.hot_tap_applicability`, `welding.brazing_bonding_qualification`을 병렬로 추가했다. Joint-efficiency 경로는 사용자가 공급한 rule set/revision/content digest와 계산 이용권한을 요구하고 joint/process/material/examination identity를 exact match한다. 검사범위 미달에는 다른 효율값을 대입하지 않는다.

Temper-bead는 deposition pass/layer 시계와 hardness·microstructure·NDE evidence를, hot-tap은 외부 thermal/burn-through 및 hydrogen-cracking provider 결과와 qualification partition을, brazing/bonding은 member surface·bonding material lot·clearance/overlap·heat-pressure cycle과 mechanical/NDE evidence를 보존한다. 어느 경로도 규격표, 합격, 균열·burn-through 확률, 용량 또는 수명을 생성하지 않는다.

병렬 작업자와 중앙 검사를 합친 focused test 17건, 변경 Ruff와 strict JSON 예제 4개가 통과했다. Registry/example ID는 192개로 일치한다. 현재 192개 계산기, 63개 인터페이스, 370개 능력 항목(102 partial·13 planned), 227개 구현 근거와 199개 공개 schema다. 전체 회귀·release 재생성은 누리온에 남겼고 독립 물리/현장 검증이 늘지 않아 전체 진행률은 65%를 유지한다.

## 2026-10-28 압력시험·용접 균열 applicability 병렬 배치

`inspection.pressure_test_eligibility`, `welding.solidification_cracking_applicability`, `welding.reheat_cracking_applicability`, `welding.lamellar_tearing_applicability`를 병렬로 추가했다. 압력시험 경로는 component/material, test method·medium·pressure basis, pressure-temperature plan, stored-energy definition과 exact prerequisite record를 caller envelope에 비교한다. 완전한 기록의 실제 불충족은 계산 실패나 결측으로 숨기지 않고 `requirements_not_satisfied`로 반환한다.

세 용접 경로는 weld/HAZ/parent-material condition, process·consumable·chemistry, heat input·thermal history, strain·stress·restraint·through-thickness loading과 physical specimen/source group 시험 증거를 보존한다. 규격표, 재료 순위, 균열 민감도·확률, 결함크기, 수명 또는 합격 판정은 생성하지 않는다.

병렬 작업자와 중앙 검사를 합친 focused test 16건, 변경 Ruff와 strict JSON 예제 4개가 통과했다. Registry/example ID는 188개로 일치한다. 현재 188개 계산기, 63개 인터페이스, 366개 능력 항목(98 partial·17 planned), 223개 구현 근거와 199개 공개 schema다. 전체 회귀·release 재생성은 누리온에 남겼고 독립 물리/현장 검증이 늘지 않아 전체 진행률은 65%를 유지한다.

## 2026-10-28 취성·환경 열화 applicability 병렬 배치

`materials.brittle_applicability_evidence`, `degradation.high_temperature_hydrogen_applicability`, `degradation.liquid_metal_embrittlement_applicability`, `degradation.crevice_species_inventory_history`를 병렬로 추가했다. Brittle 경로는 material/product form/thickness/orientation/loading identity와 물리 시편·독립 source group의 시험 증거를 caller envelope에 비교한다. 고온 수소와 액체금속 경로는 조성·열처리·접촉/습윤·온도·압력·응력·변형률속도 및 qualification lineage를 정확한 basis와 unit로 보존한다.

Crevice 경로는 외부에서 공급한 구간별 순 species source rate를 지정된 용액 체적 이력에 적분해 몰 재고와 농도를 계산하고 caller charge-balance tolerance를 확인한다. pH·activity·반응속도·침전·취약성·손상률은 추론하지 않는다. 네 경로 모두 applicability 또는 물질수지를 규격 합격, 균열 발생, 수명이나 위험확률로 변환하지 않는다.

병렬 작업자와 중앙 검사를 합친 focused test 17건, 변경 Ruff와 strict JSON 예제 4개가 통과했다. Registry/example ID는 184개로 일치한다. 현재 184개 계산기, 63개 인터페이스, 363개 능력 항목(95 partial·21 planned), 219개 구현 근거와 199개 공개 schema다. 전체 회귀·release 재생성은 누리온에 남겼고 독립 물리/현장 검증이 늘지 않아 전체 진행률은 65%를 유지한다.

## 2026-10-28 고급 검사 증거 병렬 배치

`inspection.acoustic_emission_campaign`, `inspection.replica_metallography_evidence`, `inspection.fracture_toughness_test_evidence`, `inspection.cryogenic_leak_test_evidence`를 병렬로 추가했다. Acoustic-emission 경로는 zone·좌표계·sensor/channel·calibration·acquisition interval·event feature·source-location provider 결과를 연결한다. Replica 경로는 site/area·surface preparation·microscope configuration·morphology/metric uncertainty를 calibration/holdout/application source group과 caller support에 보존한다.

Fracture-toughness evidence는 specimen/source group, geometry/orientation, temperature/load-rate/environment, initiation/tearing/arrest/user-defined endpoint, raw unit/uncertainty와 caller validity record를 partition 누출 없이 유지한다. Cryogenic leak 경로는 temperature-pressure cycle, medium·pressure basis, background/control/test 역할과 detection limit를 분리하며 below-detection을 0으로 바꾸지 않는다. 네 경로 모두 결함분류·POD·손상률·수명·확률·합격을 생성하지 않는다.

병렬 작업자와 중앙 검사를 합친 focused test 17건, 변경 Ruff와 strict JSON 예제 4개가 통과했다. Registry/example ID는 180개로 일치한다. 현재 180개 계산기, 63개 인터페이스, 359개 능력 항목(91 partial·25 planned), 215개 구현 근거와 199개 공개 schema다. 전체 회귀·release 재생성은 누리온에 남겼고 독립 물리/현장 검증이 늘지 않아 전체 진행률은 65%를 유지한다.

## 2026-10-28 thermal spray·production weld 병렬 배치

`fabrication.thermal_spray_condition`, `welding.duplex_phase_balance`, `welding.production_weld_test_evidence`, `welding.repair_welding_history`를 병렬로 추가했다. Thermal spray는 coating system·process·feedstock lot·substrate·region coverage를 고정하고 qualification/production source group을 분리한 뒤 확장가능한 metric의 정의·단위·불확도를 caller requirement에 비교한다. Duplex phase path는 weld metal·HAZ·base region, process/heat history와 상분율 불확도구간을 caller regional envelope에 비교하며 미측정 상을 보완하지 않는다.

Production-weld test는 용접·절차·소재/소모재 lot와 파괴/비파괴 관측, 물리 시편·source group, provider/result digest를 보존한다. Repair history는 removal→pre-deposition inspection→deposition→heat treatment→subsequent examination의 caller-declared exact stage sequence와 비중첩 시계, provider digest·metric envelope를 비교한다. 모든 경로는 규격표·합격판정·결함크기·수명·확률을 생성하지 않는다.

병렬 작업자와 중앙 검사를 합친 focused test 17건, 변경 Ruff와 strict JSON 예제 4개가 통과했다. Registry/example ID는 176개로 일치한다. 현재 176개 계산기, 63개 인터페이스, 355개 능력 항목(87 partial·29 planned), 211개 구현 근거와 199개 공개 schema다. 전체 회귀·release 재생성은 누리온에 남겼고 독립 물리/현장 검증이 늘지 않아 전체 진행률은 65%를 유지한다.

## 2026-10-28 방화 보호·용접 qualification 병렬 배치

`fabrication.fire_protection_boundary_history`, `welding.local_heat_treatment`, `welding.residual_stress_evidence`, `welding.wps_qualification_envelope`를 병렬로 추가했다. Fire-protection 경로는 caller-supplied incident flux와 전달률의 구간별 선형 적을 정확히 적분하고 기존 `thermal.transient_conduction_1d`의 `prescribed_heat_flux` 경계 조각을 내보낸다. 화재곡선·열물성·피복 열화·파괴는 생성하지 않는다.

Local heat-treatment는 열구역별 동기화 센서 이력에서 가열·냉각속도, hold-band 시간과 공간 구배를 요약한다. Residual-stress 경로는 측정/모델 tensor component·좌표계·불확도·calibration/holdout support를 보존한다. WPS 경로는 production essential variable을 exact identity·unit token·caller envelope·고정된 시편 증거와 비교한다. 세 경로 모두 규격 수치표나 합격·수명·파괴 판정을 내장하지 않는다.

병렬 작업자와 중앙 검사를 합친 focused test 16건, 변경 Ruff와 신규 strict JSON 예제 4개가 통과했다. Registry/example ID는 172개로 일치한다. 현재 172개 계산기, 63개 인터페이스, 352개 능력 항목(84 partial·33 planned), 207개 구현 근거와 199개 공개 schema다. 전체 회귀·release 재생성은 누리온에 남겼고 독립 물리/현장 검증이 늘지 않아 전체 진행률은 65%를 유지한다.

## 2026-10-28 caller-calibrated 부식률 병렬 배치

`degradation.acid_dissolution_history`, `degradation.erosion_corrosion_loss`, `degradation.under_deposit_calibrated_loss`, `degradation.selective_leaching_applicability`를 추가했다. 앞의 세 모델은 provider ID·version·support/state digest, material/environment identity와 정확한 chemistry/particle/deposit 단위를 보존하고 지원영역 안의 interval별 외부 보정 rate만 `rate × duration`으로 적분한다. Selective leaching은 exposure support와 microscopy/composition observation uncertainty 비교를 분리한다.

작업자 focused test는 4·4·5건을 통과했고 under-deposit 4건은 누리온 shard용으로 작성했다. 중앙에서 네 JSON 예제를 strict registry 경로로 실행해 모두 `computed`, 변경 lint와 생성 카탈로그, 168 registry ID/168 example ID 일치를 확인했다. 현재 168개 계산기, 63개 인터페이스, 349개 능력 항목(81 partial·37 planned), 203개 구현 근거와 199개 공개 schema다. 실제 provider 보정자료·독립 holdout·localized geometry와 field validation이 늘지 않아 전체 진행률은 65%를 유지한다.

## 2026-10-28 고온 열화 applicability 병렬 배치

`degradation.sulfidation_exposure_applicability`, `degradation.carburization_applicability`, `degradation.nitriding_applicability`, `degradation.metallurgical_aging_exposure`를 추가했다. 앞의 세 모델은 material/condition, chemical driving-force basis와 exact unit, temperature, absolute pressure, environment descriptor와 caller qualification evidence를 비교한다. Aging 모델은 interval duration에 caller-calibrated equivalent-time multiplier를 곱해 reference-temperature equivalent exposure를 합산하며 provider support 밖은 `out_of_scope`다.

작업자 focused test는 4·4·5건을 통과했고 aging 4건은 누리온 shard용으로 작성했다. 중앙에서 네 JSON 예제를 strict registry 경로로 실행해 모두 `computed`, 변경 lint와 생성 카탈로그, 164 registry ID/164 example ID 일치를 확인했다. 현재 164개 계산기, 63개 인터페이스, 345개 능력 항목(77 partial·41 planned), 199개 구현 근거와 199개 공개 schema다. 실제 고온 노출 kinetics·phase/property 변화와 독립 field validation이 늘지 않아 전체 진행률은 65%를 유지한다.

## 2026-10-28 bonded layer·SCC·preheat 병렬 배치

`materials.bonded_layer_integrity_assessment`, `degradation.ammonia_scc_applicability`, `degradation.alkaline_scc_applicability`, `welding.preheat_procedure_envelope`를 추가했다. Bonded layer는 interface region coverage, 관측 불확실성과 caller disposition을 보존한다. Ammonia와 alkaline SCC는 chemistry unit, phase/electrochemical basis, stress descriptor와 qualification evidence를 exact match한다. Preheat는 material/joint/process/consumable/hydrogen-control/restraint identity와 두께·net heat input 지원범위를 먼저 확인하고 기록된 preheat/interpass 온도 margin과 excursion duration을 반환한다.

작업자 focused test는 4·4·5건을 통과했고 preheat 4건은 누리온 shard용으로 작성했다. 중앙에서 네 JSON 예제를 strict registry 경로로 실행해 모두 `computed`, 변경 lint와 생성 카탈로그, 160 registry ID/160 example ID 일치를 확인했다. 현재 160개 계산기, 63개 인터페이스, 341개 능력 항목(73 partial·45 planned), 195개 구현 근거와 199개 공개 schema다. 실제 interface fracture, 환경 SCC 또는 weld-procedure qualification 검증이 늘지 않아 전체 진행률은 65%를 유지한다.

## 2026-10-28 환경 열화 applicability 병렬 배치

`materials.phase_microstructure_assessment`, `degradation.sour_environment_applicability`, `degradation.chloride_scc_applicability`, `degradation.microbial_campaign_summary`를 추가했다. Sour path는 H₂S absolute partial-pressure basis와 calibration/holdout 시험 분리를 요구한다. Chloride SCC는 dissolved-oxygen 수치 경로와 qualitative oxidizing descriptor를 분리한다. Microbial campaign은 below-detection assay를 0으로 바꾸지 않는다. Phase fraction은 불확실성 구간을 사용자 range와 비교하고 미측정 phase를 보완하지 않는다.

작업자 focused test는 4·4·5건을 통과했고 phase 4건은 누리온 shard용으로 작성했다. 중앙에서 네 JSON 예제를 strict registry 경로로 실행해 모두 `computed`, 변경 lint와 생성 카탈로그, 156 registry ID/156 example ID 일치를 확인했다. 현재 156개 계산기, 63개 인터페이스, 337개 능력 항목(69 partial·49 planned), 191개 구현 근거와 199개 공개 schema다. 실제 환경별 시험 보정·독립 holdout·현장 손상 검증이 늘지 않아 전체 진행률은 65%를 유지한다.

## 2026-10-28 재료 compatibility·제조품질 병렬 배치

`materials.polymer_compatibility_envelope_match`, `materials.composite_compatibility_assessment`, `materials.casting_forging_quality_record`, `degradation.under_insulation_exposure_history`를 병렬 구현했다. Polymer는 exact lot과 명시적 grade-level lot transfer를 분리하고, composite는 coupon/source-group calibration·holdout partition 누출을 차단한다. Casting/forging 기록은 heat·route·heat treatment·inspection coverage와 uncertainty-bound indication을 보존한다. Under-insulation 이력은 caller-defined 온도·wetness·insulation condition 교집합 시간만 분류하고 결측구간을 보간하지 않는다.

작업자 focused test는 각각 4·4·5건을 통과했고 under-insulation 4건은 누리온 shard에 포함하도록 작성했다. 중앙에서는 변경 lint, 생성 카탈로그와 152 registry ID/152 example ID 일치만 확인했다. 현재 152개 계산기, 63개 인터페이스, 333개 능력 항목(65 partial·53 planned), 187개 구현 근거와 199개 공개 schema다. 실제 재료별 qualification·독립 holdout과 field validation이 늘지 않아 전체 진행률은 65%를 유지한다.

## 2026-10-28 제작·보존 모듈 2개 병렬 배치

사용자 요청에 따라 구현을 네 작업축으로 병렬화했다. `fabrication.winterization_inventory`는 구간별 외기·UA·heat tracing·유효 정압비열로 잘 섞인 재고의 1차 열수지를 계산하며, `thermo.winterization_inputs_from_coolprop`가 절대압과 평가온도별 `Cpmass`, phase, CoolProp 판본·리비전 및 상태 digest를 만든다. minimum temperature는 사용자가 공급하며 고체 형성·잠열·과냉각을 예측하지 않는다.

`fabrication.surface_cleanliness_assessment`, `fabrication.chemical_cleaning_envelope`, `fabrication.storage_preservation_history`는 각각 관측 불확실성을 포함한 표면 metric, 단계별 세정 chemistry·시간, 저장 환경·보존상태·점검 간격을 사용자 소유 요구조건과 비교한다. 규격 수치·합격표를 내장하지 않고 결측·무효·미연결 기록을 `needs_data`로 보존한다. coating 수명, 세정 반응·부식률, 보존 손상·잔여수명은 출력하지 않는다.

두 번째 배치에서 `fabrication.coating_qualification_assessment`는 calibration/holdout specimen과 source group을 고정한 채 DFT·adhesion·사용자 metric을 불확실성과 함께 비교한다. `inspection.test_water_quality_summary`는 시간·위치별 온도·pH·conductivity·chloride와 sampling coverage를 사용자 envelope에 비교한다. `fabrication.transport_erection_history`는 활동구간, shock/tilt 등 사용자 metric, lifting/erection inspection stage와 disposition을 보존한다. `welding.consumable_compatibility`는 base-material condition pair, consumable lot, process, service environment의 exact identity와 사용자 선언 온도 지원만 대조한다.

각 병렬 작업의 focused test는 작성됐고 작업자가 배치별 집중 검사를 통과시켰다. 겨울철 계산기의 5건과 기존 model example 집중 검사는 첫 통합 전에 통과했다. 이후 전체 148개 모델 회귀·전체 Ruff·배포물 재생성은 사용자 요청대로 누리온에 이관했으며 task 45를 포함한 46-task Slurm 배열로 준비했다. 중앙에서는 변경 파일 lint, source/capability/reference/schema 생성, 148개 registry ID와 148개 예제 ID의 정확한 일치만 확인했다. 현재 148개 계산기, 63개 인터페이스, 329개 능력 항목(61 partial·57 planned), 183개 구현 근거와 199개 공개 schema다. 독립 물리·현장 검증이 늘지 않았으므로 전체 진행률은 65%를 유지한다.

## 2026-10-28 용접 수소 bakeout 유한 평판 스크리닝

`welding.hydrogen_bakeout_slab`을 독립 구현했다. 사용자 승인 양면 방출 두께, 균일 초기 확산성 수소, time/temperature/effective-diffusivity 이력을 받고 piecewise-linear `D(t)`를 누적 확산시간으로 정확히 적분한다. 유한 평판 odd eigenfunction 급수의 positive tail 상한을 계산해 수치 예산 안에서만 잔류·방출 분율, 평균 농도와 면적당 누적 방출량을 반환한다. 온도에서 재료계수를 만들거나 공개 규격의 절차값·합격표를 포함하지 않았다.

정온 특성시간의 독립 50항 급수와 절대오차 `4.5e-13`, 동일 `∫Ddt` 이력과 오차 0, 기존 보존형 무트랩 80셀 FVM과 상대차 약 `1.12e-3`을 확인했다. 관련 수소 집중 64건과 로컬 HPC task 44가 통과했다. NIST 문서는 Fick 확산과 유한 평판 특성시간의 서지 근거로만 사용하고 문장·표·계수는 복제하지 않았다. 계산기는 140개, 인터페이스는 63개, 능력 항목은 321개, 공개 schema는 199개, Slurm 작업은 45개다. `welding.hydrogen_bakeout` 전체는 trap·weld/HAZ 이질성·상변태·표면 kinetics·procedure evidence 때문에 partial이며 독립 실험 검증이 늘지 않아 전체 진행률은 65%를 유지한다.

## 2026-10-28 배관 공통 평가 결과 교환계약

`pipeline-integrity-toolkit`의 공통 `AssessmentResult`와 기존 MatIntegrity 호출 경계를 검토했다. 상대 프로젝트는 이미 `MaterialJob`/`MaterialReceipt`로 MatIntegrity 결과의 모델·상태·단위·문맥을 검증하므로 운전이력이나 계산식을 중복 구현하지 않았다. 대신 반대 방향의 완전한 공통 결과를 받는 `PipelineAssessmentRecord`를 추가했다. 원 result 전체와 모델·버전·status, 입력·출력 단위, asset/scenario/clock/origin, evidence, runtime, qualification 및 complete-payload digest를 보존하며 screening 결과의 현장·설계 승인 재명명을 금지한다.

상대 저장소에는 아직 commit이 없어 revision을 만들지 않았다. `pyproject.toml`과 `src/**/*.py` 111개의 상대경로·바이트로 계산한 source-tree SHA-256 `446ffe69d10dbcc57427dcc45a37eef39da0e9b92bf7ce0c04a2d29230bb37c0`을 고정하고 실제 `geometry.pipe` 예제를 실행했다. 전용 7건과 provider end-to-end 검증이 통과했다. 최신 wheel을 비편집 core/full 환경에 설치한 전체 1,253건도 실패·오류 없이 통과하고 설치 source tree가 현재 `src`와 일치했다. 송신 exporter 요구는 별도 요청서로 남겼다. 계산기는 139개, 인터페이스는 63개, 능력 항목은 320개, 공개 schema는 198개, Slurm 작업은 44개다. 독립 물리 검증이 늘지 않아 전체 진행률은 65%를 유지한다.

## 2026-10-28 인적신뢰도 공급자 교환계약

공개 `human-reliability-toolkit`의 깨끗한 main commit `d2754bbea16e12d00240e88d13cb4badbe672ac3`과 MIT 라이선스, `HumanFailureEvent`, `Estimate`, `AssessmentEngine` 출력을 읽기 전용으로 검토했다. 공급자의 확률은 정의된 한 작업 기회당 실패확률이며 MatIntegrity의 기간 중 물리 최초고장확률과 다르다.

`HumanReliabilityEstimateRecord`와 생성 adapter를 독립 구현했다. 공급자 revision·assessment input digest·task/procedure/context, 원 event/estimate 전체, failure/opportunity/conditioning, role·step·dependency, evidence·method·uncertainty·trace와 recovery/timing/dependency 포함범위를 원 레코드 및 전체 payload digest에 결속한다. v1은 empirical plant validation claim을 허용하지 않고 작업기회 확률을 기간확률로 재명명하지 않는다. 형제 저장소는 수정하지 않았으며 송신 exporter와 MatIntegrity monitoring-context 수신기 요구를 `extension_requests/HUMAN_RELIABILITY_TOOLKIT_KO.md`에 기록했다.

고정 공급자 checkout의 실제 `AssessmentEngine` 예제를 실행해 확률 `0.07297535529999999`인 research estimate를 계약으로 왕복했다. 전용 7건과 관련 집중 17건은 확률·원 estimate·conditioning·revision 변조, recovery/timing 불일치와 기간확률 재명명을 거절했다. 이는 소프트웨어 end-to-end이지 인간 수행도·현장·요구빈도·의존성 또는 위험 검증이 아니다. 현재 139개 계산기·62개 인터페이스·319개 능력 항목이며 Slurm manifest는 43개 작업이다. 독립 물리 검증이 늘지 않아 전체 진행률은 65%를 유지한다.

## 2026-10-28 수소 재료수송 공급자 교환계약

로컬 `hydrogen-physical-models`의 커밋 `785dae74dad4771e76e2a8e8aad3731e3dfa799e`에서 커밋된 `h2physics.materials` 공개 API를 읽기 전용으로 검토했다. 공급자는 atomic-H/H2를 구분하고 평판·구형 쉘의 이동/포획 농도, 좌우 좌표방향 누적량, 벽 재고와 보존잔차를 반환하지만 버전 JSON 결과계약, material/lattice ID와 payload digest는 없다.

MatIntegrity에 구현 비의존 `HydrogenTransportHistory`를 추가했다. 공급자 revision·native 결과 SHA-256, 운반체·재료·격자·기하·trap·clock identity와 단위가 고정된 mesh/농도/재고/잔차 배열을 complete-payload digest로 묶는다. Shape·시간/격자 순서·수치 음의 농도 허용오차를 fail-closed 검사한다. 공급자 구현을 복사하거나 형제 저장소의 작업 파일을 수정하지 않았다. 상대 저장소에는 exporter 구현과 인수시험만 요구하는 `extension_requests/HYDROGEN_PHYSICAL_MODELS_KO.md`를 작성했다.

전용 7개 검사는 JSON 왕복, 값 변조, 배열 misalignment, trap ID 중복과 음의 수치 허용오차를 확인했다. `scripts/validate_hydrogen_transport_exchange.py`의 작성 보존 항등식·음성대조도 통과했다. 이는 저장소 간 실제 실행, 계수·실험·손상·고장확률 검증이 아니므로 전체 진행률은 65%를 유지한다. 현재 139개 계산기·61개 인터페이스이고 Slurm manifest는 42개 병렬 작업이다.

## 2026-10-28 공정 모니터링 교환계약 자격화

`process-monitoring-toolkit`의 실제 checkout commit
`79b4cf52a0acd0d0cbd3addbe82c3d98d6385e5a`를 읽기 전용으로 다시 대조했다. 기존
`monitoring_record` dict를 `MonitoringAssessmentRecord` 공개 계약으로 승격해 모델·입력·값·단위·
상태·가정·근거·실행환경·자격 수준·확률 의미와 완전 assessment SHA-256을 보존한다. 값·모델 버전·
확률 의미 변조, context identity 불일치와 digest 불일치를 거절하고 `needs_data`를 normal/alarm으로
바꾸지 않는다. 전용 6건, 확률 의미 회귀와 139개 전 모델 예제를 합친 집중 150건, 작성 JSON 왕복·
변조 음성대조와 Ruff가 통과했다. 공개 schema는 195개, Slurm manifest는 41개 작업이다. 상대
저장소에는 아직 이 스키마의 수신 validator가 없어 live 통합으로 주장하지 않고 확장 요청서에 정확한
수신 요구를 기록했다. 외부 통합과 물리 검증이 늘지 않았으므로 전체 진행률은 65%로 유지한다.

## 2026-10-28 사용자 공급 압력–온도 운전경계

`structural.pressure_temperature_envelope`를 독립 구현했다. SHA-256으로 고정한 사용자 경계의 엄격히
증가하는 절대온도 knot 사이에서만 허용압력을 선형 보간하고, 식별된 운전점별 압력여유·이용률·경계
내부 여부와 지배점을 반환한다. 적용성·운전점 검토 gate를 요구하며 지원온도 밖 외삽, 내장 규격표,
안전계수와 자동 합격판정은 하지 않는다. 기존 응력강도 반환문 위치와 엄격 JSON 배열형 문제를 첫
집중시험에서 발견해 수정했다. 전용 6건과 139개 전 모델 예제를 포함한 146건, 작성 affine 산술
검증과 Ruff가 통과했다. 현재 139개 계산기·60개 인터페이스·52개 부분 구현·66개 계획의 317개 능력,
173개 구현 근거와 194개 공개 schema다. Slurm manifest는 이 산술 검증을 39번으로 추가해 40개
작업이 됐다. 실제 설계경계·과도이력 검증이 아니므로 전체 진행률은 65%로 유지한다.

## 2026-10-27 provenance-bound chronoamperometry 창 요약

제공자 notebook의 feature 알고리즘을 복제하지 않고 사용자 지정 분석·baseline 창을 처리하는
`corrosion.chronoamperometry_window_summary`를 독립 구현했다. 비균일 엄격 시간축에서 exact sample
또는 명시적 선형 경계보간을 사용하며 signed charge, 0 교차를 삽입한 absolute charge, 시간가중 평균,
plateau 첫/마지막 극값 시각을 반환한다. 정렬·평활·event picking·확률 변환은 하지 않는다. SECCM
reader adapter는 archive/member/선택배열 digest와 시편·source group을 보존한다. 전용 16건과 전체
모델 예제를 포함한 집중 161건, 기존 전기화학까지 합친 집중 191건과 Ruff가 통과했다. 작성 affine 닫힌식 최대 절대오차는 0이며 고정
SECCM map 1의 7,782개 raw sample에도 실제 적용했다. 현재 138개 계산기·60개 인터페이스·52개 부분
구현·67개 계획의 317개 능력, 172개 구현 근거와 191개 공개 schema다. 한 map 위치의 기술량은 독립
물리 검증이 아니므로 전체 진행률은 65%로 유지한다. 36-task Slurm manifest의 새 35번 작업도 로컬
runner로 통과했다.
재빌드한 wheel 91파일·sdist 684파일·review ZIP 677파일은 제한 원자료·provider notebook·개인 경로
제외 감사를 통과했다. 정확한 해시는 배포물 밖 `dist/checksums.json`에 둔다.

## 2026-10-27 316L SECCM 원시 신호 계약

CC BY 4.0의 SECCM-SEM/EBSD ZIP을 제공자 MD5와 프로젝트 SHA-256으로 고정하고 exact-manifest와
열 개 member hash를 검사하는 `seccm_data.py`를 추가했다. raw CA의 두 header, 205개 map point,
각 7,782개 시간·전류 표본을 전수 파싱하며 위치 하나를 초·A 배열로 반환한다. 제공자 MIT notebook은
고정 commit의 단위 근거로만 검토하고 실행·복제하지 않았다. descriptor·label·footprint·SEM/EBSD
표는 raw signal과 분리했고 cross-table alignment와 물리 시편 독립성은 미확정으로 보존했다. 전용
9건과 Ruff가 통과했다. 현재 134개 계산기·59개 인터페이스·52개 부분 구현·67개 계획의 312개 능력,
166개 구현 근거와 182개 공개 schema다. 구조 감사만으로 실제 부식 검증이 늘어난 것은 아니므로 전체
진행률은 65%로 유지한다.
후속 구조 감사에서 parameter·descriptor 두 표·label·footprint·SEM·filtered EBSD의 행수, ID
완전성/부분집합과 좌표 문자열 유일성을 집계했다. parameter ID가 1–205의 순열이지만 행 순서가 map ID
순서와 다르고 retract charge 한 칸이 비어 있음을 명시했다. 이 결과로 자동 join이나 좌표 정합을
허용하지 않는다.
재빌드한 wheel 91파일·sdist 678파일·review ZIP 671파일은 제한 원자료와 개인 경로 제외 감사를
통과했다. 정확한 산출물 해시는 배포물 밖 `dist/checksums.json`에 기록한다.

## 2026-10-27 검토된 직교 공간장 교환·표본화 계약

서로 다른 shape의 표면형상·응력·변형률·두께 자료를 index로 임의 결합하지 않도록
`spatial_fields.py`를 추가했다. 별도 배열과 Boolean 결측 mask를 dtype·shape·바이트 SHA-256으로
고정하고 물리 시편·source group·물리량·단위·관측시점·직교축·좌표계 근거를 보존한다. 다른
frame은 검토된 direct affine 변환이 있을 때만 허용하며 nearest/bilinear, 격자 밖과 결측 정책을
호출자가 선택한다. 전용 8건과 AA7050 reader 포함 집중 16건, Ruff가 통과했다. 공개 schema 네 개와
`data.reviewed_rectilinear_spatial_field`를 추가해 현재 134개 계산기·58개 인터페이스·52개 부분 구현·
67개 계획의 311개 능력, 165개 구현 근거와 179개 공개 schema다. 이 기능은 정합 품질·보간의 물리적
타당성·pit 분할·성장·POD·수명 검증이 아니므로 전체 진행률은 65%로 유지한다. AA7050에는 좌표·단위·
높이 부호·정합 변환이 확인될 때까지 적용하지 않는다.
재빌드한 wheel 90파일·sdist 670파일·review ZIP 663파일은 제한 원자료와 개인 경로 제외 감사를
통과했다. 정확한 산출물 해시는 배포물 바깥 `dist/checksums.json`에 기록한다.

## 2026-10-27 AA7050 국부 공식 공개자료 구조 계약

한 AA7050 시편의 2일·6일 표면 형태와 stress·strain MAT를 제공하는 CC BY 4.0 Mendeley 자료를
카탈로그에 고정했다. 네 파일의 공개 API ID·직접 URL·바이트 수·SHA-256을 기록하고 원 MAT는 공개
배포에서 제외했다. 가장 작은 stress 파일 2,412,094바이트를 먼저 완성해 제공자 SHA-256을 대조했다.
level-5 MAT의 float32 230×291 배열 10개와 전 값 유한 상태를 확인했지만 단위·좌표계·변수 의미는
확정하지 않았다.

체크섬 고정 level-5 MAT의 최상위 실수 numeric 배열만 읽는 `pitting_data.py`를 추가했다. 구조체·
cell·object·sparse·complex·HDF5 v7.3·과대 파일을 거절하고 원 변수명·dtype·shape·비유한 값을
보존한다. 근거 없는 단위·정합 주장을 계약에서 차단하며 배열을 변환하거나 threshold하지 않는다.
전용 8건과 Ruff 검사를 통과했다. 네 파일 127,766,005바이트의 제공자 SHA-256과 level-5 구조를
완전히 감사했다. 2일·6일 형태 shape는 2,845×3,931과 2,849×3,968로 다르고 strain·stress도
851×1,199와 230×291로 달라 직접 index 결합을 차단했다. 한 시편의 픽셀을 독립 시편으로 세거나
두 시점에서 일반 성장·전이확률·POD·수명·합격을 만들지 않는다. 현재 134개 계산기·57개 인터페이스·52개 부분 구현·67개 계획의
310개 능력, 165개 구현 근거와 175개 공개 schema이며 전체 진행률은 65%로 유지한다.
최종 2회 재빌드한 wheel 89파일·sdist 663파일·review ZIP 656파일은 제한 원자료와 개인 경로 제외
감사를 통과했고 정확한 SHA-256은 배포물 밖 `dist/checksums.json`에 기록했다.

## 2026-10-27 유한 정책 관측·전이확률 보정

`inspection.finite_policy_probability_calibration`과 여섯 공개 입력 계약, 보정결과→정책 epoch 어댑터를
추가했다. 실제상태-관측 라벨과 상태-행동-다음상태의 가중 기록을 calibration/holdout으로 고정하고,
동일 sequence 또는 source group이 두 분할에 걸치면 거절한다. 확률은 weighted frequency와 호출자가
승인한 대칭 pseudocount만 사용한다. untouched holdout에는 negative log likelihood와 multiclass Brier
score를 계산하며 0확률 사건을 clipping하지 않는다.

독립 작성 표의 네 핵심 확률과 두 holdout 점수가 직접계산과 일치했고 전용 8건, 관련 집중시험 42건,
모델 예제 포함 154건과 Ruff가 통과했다. 공개 ILI 3,198,420행은 영속 feature identity와 굴착 truth가
없어 보정에 쓰지 않고 기계판독 검증기록에 제외 사유를 남겼다. 현재 134개 계산기·56개 인터페이스·
52개 부분 구현·67개 계획의 309개 능력, 164개 구현 근거와 173개 공개 schema이며 Slurm manifest는
35개 작업이다. 실제 독립 시편 자료 검증이 늘지 않아 전체 진행률은 65%로 유지한다.
최종 재빌드한 wheel 88파일·sdist 656파일·review ZIP 649파일은 제한 원자료와 개인 경로 제외 감사를
통과했으며 정확한 SHA-256은 배포물 밖 `dist/checksums.json`에 기록했다.

## 2026-10-27 유한 검사정책 경로 생성

`inspection.finite_policy_path_generation`, 8개 공개 계약과 생성→기대손실 평가 어댑터를 추가했다.
시작 생존조건부 초기분포, 상태조건부 관측분포, 관측별 고정 행동, 상태-행동 전이를 ordered epoch마다
완전하게 요구한다. 모든 확률족 합 1, failure 전이에만 결과계수, failure 즉시 경로 종료를 검사한다.
모든 비영 경로의 전체 trace digest를 보존하며 경로한도 초과 시 부분집합으로 절단하지 않는다.

공개 한 epoch 예제의 7개 경로와 전용 두 epoch 검사의 16개 경로에서 확률질량을 보존했다. 생성→평가
결과는 최초고장확률 0.064, 기대 행동비용 19.6, 할인 고장결과 57.6, 총손실 77.2의 독립합과 일치했다.
전용 11건, 관련 정책·모델 예제 168건과 로컬 HPC 작업 33번이 통과했다. 현재 133개 계산기·56개
인터페이스·52개 부분 구현·67개 계획의 308개 능력, 163개 구현 근거와 168개 공개 schema이며
manifest는 34개 병렬 작업이다. wheel 88파일·sdist 648파일·review ZIP 641파일의 제한 원자료 제외
감사가 통과했다. 실제 상태·관측·전이 보정이 아니므로 진행률은 65%로 유지한다.

## 2026-10-27 다기간 검사정책의 제약 우선 비교

`inspection.multi_period_policy_comparison`, 네 공개 계약과 평가결과 어댑터를 추가했다. 동일 사건·
범위·기간·생존조건·비용·할인 기준의 완전한 정책 후보집합에서 evaluator configuration/input/result
digest, 조건부 최초고장확률과 선택적 상한, 기대손실 구성요소, 정확한 자원 ID·단위·점추정/상한을
보존한다. 사용자 승인 확률·자원 hard constraint를 비용보다 먼저 적용하고, 무통과 시 제약을
완화하지 않으며 비용동률을 임의로 깨지 않는다.

독립 예제에서 기대손실 300·400인 정책은 확률 또는 outage 한도를 위반하고, 확률 0.08·outage 7일·
기대손실 450인 정책만 통과했다. 전용 13건, 관련 정책·모델 예제 156건, 로컬 HPC 작업 32번이
통과했다. 현재 132개 계산기·56개 인터페이스·52개 부분 구현·67개 계획의 307개 능력, 162개 구현
근거와 160개 공개 schema이며 manifest는 33개 병렬 작업이다. 전체 목표 진행률은 실제 정책·검사효과
검증이 늘지 않아 65%로 유지한다. wheel 88파일·sdist 637파일·review ZIP 630파일의 제한 원자료
제외 감사도 통과했다.

## 2026-10-27 다기간 고정 검사정책 경로 평가

`inspection.multi_period_policy_evaluation`과 네 공개 계약을 추가했다. 외부 생성기가 만든 한 정책의
완전한 유한 경로 집합에서 각 경로확률·source digest, 시간순 관측/행동, 행동모델 revision과
configuration/input digest, 시점비용·현재가치계수, 최초고장과 결과비용 계수를 보존한다. 경로확률
합 1, 기간 안 시점, 엄격한 순서와 고장 이후 행동 금지를 계약으로 검사한다. 검토 gate가 빠지면
산술을 보류하며 전이·확률·할인·정책 최적성을 추정하지 않는다.

작성한 세 경로의 독립 합에서 기대 할인 행동비용 236.5, 기대 고장결과 160, 총손실 396.5와 조건부
최초고장확률 0.2가 구현과 일치했다. 전용 10건, 관련 집중 회귀 267건, 로컬 HPC 작업 31번과 Ruff가
통과했다. manifest는 32개 병렬 작업이다.

현재 131개 계산기·56개 인터페이스·52개 부분 구현·67개 계획의 306개 능력, 161개 구현 근거와
156개 공개 schema다. 이는 고정 정책 산술·교환계약의 검증이며 실제 경로 생성, 검사효과, 비용·할인,
복수정책 비교, 자원제약 최적화 또는 규격판정을 자격화하지 않는다. wheel 88파일·sdist 630파일·
review ZIP 623파일의 제한 원자료 제외 감사가 통과했다. 전체 목표 진행률은 65%로 유지한다.

## 2026-10-27 검사결과별 처분 의사결정나무

`inspection.disposition_decision_tree`와 두 공개 계약을 추가했다. 한 검사행동의 상호배타·완전분할
결과마다 확률, 처분 identity·definition, 처분효과 모델 revision/configuration/input/result digest,
조건부 잔여 최초고장확률과 비용을 보존한다. 검토 gate와 확률합 1을 요구하고, 선행 검사비용에
확률가중 처분비용을 더하며 결과·처분 조건부 잔여확률도 직접 가중한다. 전용 adapter가 결과 digest에
묶인 estimate-basis 행동 후보를 생성한다.

작성한 세 분기에서 확률 0.7·0.2·0.1, 처분비용 0·400·100, 잔여확률 0.10·0.01·0.05와 검사비용
50의 직접합은 기대 처분비용 90, 총 행동비용 140, 잔여확률 0.077이며 구현과 일치했다. 전용
단위검사 9건은 구조·gate·context·후보 변환과 기존 기대손실 비교까지 검사한다. HPC task 30을
추가해 manifest를 31개 작업으로 확장했다. 이는 유한합 검증이며 POD·오탐·분기확률·처분효과·
상한·다기간 정책을 자격화하지 않는다.

현재 130개 계산기·56개 인터페이스·52개 부분 구현·67개 계획의 305개 능력, 160개 구현 근거와
152개 공개 schema다. wheel 88파일·sdist 623파일·review ZIP 616파일의 제한 원자료 제외 감사가
통과했다. 전체 목표 진행률은 실제 검사 데이터 자격화가 늘지 않아 65%로 유지한다.

## 2026-10-27 행동별 FTA·동적 신뢰성 결과 수신 어댑터

`ActionEventProbabilityEvaluation`과 `inspection_action_expected_loss_inputs`를 추가했다. 외부
FTA·동적 신뢰성 계산의 행동 정의, evaluator ID·revision·configuration/input digest, 위험구조 ID,
상태, `EventProbability`와 선택적 상한을 보존한다. 사전 선언한 행동 ID, 평가행과 비용 map의 정확한
전체 집합을 요구하며 event·asset·scope·failure mode·horizon·conditioning을 행동 사이에서 대조한다.
역순 결과는 선언순서로 복원하지만 누락·추가·중복·미계산 행은 삭제하지 않고 전체 조립을 거절한다.

직접 산술 검증을 세 외부 교환행→수신 어댑터→기대손실 계산의 end-to-end 경로로 확장했다. 전용
어댑터 검사는 각 문맥 필드 불일치, 불완전 상한, status/probability 충돌, result·risk-structure·
common-cause identity 보존과 입력 비변경을 포함한다. 이는 교환계약 검증이며 특정 FTA 저장소,
행동효과, 공통원인 모형 또는 실제 위험을 자격화하지 않는다.

관련 회귀 262건과 Ruff 정적·형식 검사가 통과했다.

현재 129개 계산기·56개 인터페이스·52개 부분 구현·67개 계획의 304개 능력, 159개 구현 근거와
150개 공개 schema다. wheel 88파일·sdist 617파일·review ZIP 610파일의 제한 원자료 제외 감사가
통과했다. 전체 목표 진행률은 실제 외부 저장소·현장 데이터 자격화가 늘지 않아 65%로 유지한다.

## 2026-10-27 검사·정비 행동 기대손실 비교

`inspection.action_expected_loss`와 세 공개 계약을 추가했다. 한 사건·물리 범위·기간·생존조건과
공통 비용 기준에서 정확히 하나의 zero-action-cost baseline과 완전한 intervention 후보를 받는다.
각 행동의 정의, effect-model ID·revision·input digest, 잔여 최초고장확률 점추정·상한과 비용
구성요소를 보존한다. 총 기대손실은 행동비용과 확률×조건부 결과비용의 합이며 점추정/완전 상한
기준을 분리한다. 동률 허용차 안의 최소가 둘 이상이면 임의로 선택하지 않는다.

독립 작성한 결과비용 5,000, 행동비용 0·100·400과 세 행동을 직접 계산해 점추정 총액
500·300·450 및 상한 총액 600·600·500을 등록 계산기와 정확히 대조했다. 전용 단위검사 11건은
구성요소 합, 선택 변경, 동률, review gate, 상한, ID, baseline, 기간·context와 비변경 입력을
검사한다. 관련 회귀 246건과 새 HPC task 29의 로컬 실행이 통과했다. 이는 산술·계약 검증이며 행동효과·사건확률·비용·결과·
위험허용도·법규를 자격화하지 않는다.

현재 129개 계산기·55개 인터페이스·52개 부분 구현·67개 계획의 303개 능력, 159개 구현 근거와
149개 공개 schema다. wheel 88파일·sdist 615파일·review ZIP 608파일의 제한 원자료 제외 감사가
통과했고 Slurm manifest는 30개 작업이다. 전체 목표 진행률은 실제 현장 자격화가 늘지 않아 65%로
유지한다.

## 2026-10-27 과정잡음 포함 선형 두께 상태공간 갱신

`reliability.linear_thickness_state_space_update`와 공개 계약을 추가했다. 두께-부호 있는 손실률
상태를 엄격한 관측 시간순서로 전파하고, 각 구간에 호출자가 검토한 2×2 과정잡음 공분산률×경과시간을
누적한다. update 행은 scalar 두께 관측과 Joseph 공분산식으로 상태를 갱신하며 holdout 행은
one-step-ahead 잔차만 만들고 상태를 바꾸지 않는다. 분석 종료시점 posterior와 미래 특정시점
두께분포를 반환하고 기존 공동표본 adapter가 이 posterior도 받을 수 있게 확장했다.

과정잡음 0의 순차 결과를 독립 batch 정보형 Gaussian 해와 대조하고, 비영 과정잡음의 미래 공분산을
`F P Fᵀ + Q_rate Δt` 직접식과 비교했다. 전용 단위검사 11건은 holdout 불개입, 과정잡음 양의
준정부호, 시간순서, review gate, context와 posterior→공동표본 연결을 포함한다. 새 HPC task 28과
집중 회귀 234건이 통과했다. 이는 필터 수학·소프트웨어 검증이며 과정잡음 보정, smoother, 비선형
열화, 개입 또는 실제 CML의 검증이 아니다.

현재 128개 계산기·55개 인터페이스·51개 부분 구현·68개 계획의 302개 능력, 158개 구현 근거와
146개 공개 schema다. wheel 88파일·sdist 606파일·review ZIP 599파일의 제한 원자료 제외 감사가
통과했다. Slurm manifest는 29개 작업이며 전체 목표 진행률은 실제 현장 자격화가 늘지 않아 65%로
유지한다.

## 2026-10-27 Gaussian 두께 posterior 공동표본과 최초도달 연결

`reliability.gaussian_thickness_posterior_sample_design`과 공개 계약을 추가했다. 검토된 기준시점
두께-부호 있는 일정 손실률 Gaussian posterior의 2차원 공분산을 보존하고, 비음수 손실률과
평가시점 임계두께 생존으로 명시적으로 조건화한다. 64비트 seed, 고정 후보 예산과
`splitmix64_box_muller_cholesky_rejection_v1`을 기록하며 요청 수를 채우지 못하면 부분표본을
반환하지 않는다. 두 중립 adapter는 계산된 Bayesian 갱신→공동표본→선형 최초도달 입력을 연결한다.

독립 작성한 SplitMix64·53비트 개구간 균등수·Box–Muller·2차원 Cholesky·rejection 순회와 4,096개
표본을 행 단위로 정확히 대조했다. 전용 단위검사 12건은 재현성, 경험적 평균·표준편차·상관,
review gate, 예산 부족, 공분산·context·digest와 전체 adapter 사슬을 포함한다. 새 HPC task 27과
집중 회귀 222건이 통과했다. 이는 난수변환·소프트웨어 계약 검증이며 실제 posterior, 과정잡음,
비선형 성장, 일정 부식률 또는 현장 최초도달의 검증이 아니다.

현재 127개 계산기·55개 인터페이스·51개 부분 구현·68개 계획의 301개 능력, 157개 구현 근거와
145개 공개 schema다. wheel 88파일·sdist 601파일·review ZIP 594파일의 제한 원자료 제외 감사가
통과했다. Slurm manifest는 28개 작업이며 전체 목표 진행률은 실제 현장 자격화가 늘지 않아 65%로
유지한다.

## 2026-10-27 표본 기반 선형 두께 최초 임계도달

`reliability.sampled_linear_thickness_first_passage`와 두 공개 계약을 추가했다. 평가시점 생존을
조건으로 한 동일 위치의 잔여두께-비음수 손실률 공동 표본에서 표본별 선형 임계도달시각과 후보별
가중 누적확률을 계산한다. 분포·표본설계 ID, 공동 표본 SHA-256, 사건·물리 범위·시간기준과 다섯
검토 gate를 보존한다. 0 손실률의 비도달 질량과 마지막 후보 이후 양의 손실률 질량을 직접 합산한다.
이미 요구두께 이하인 행은 삭제하거나 재조건화하지 않고 `needs_data`로 남긴다.

작성 표본의 닫힌식 도달시각·확률을 독립 대조하고 출력 forecast를
`inspection.threshold_inspection_schedule`에 전달해 기대 후보 선택까지 검사했다. 전용 단위검사
11건과 기존 일정·균열·공학·전체 모델 예제·취득 체크섬을 합친 집중 회귀 209건이 통과했다. 로컬
HPC task 26도 통과해 manifest는 27개 작업이다. 이는 공급된 공동분포의 수학적 push-forward와
인터페이스 검증이며 실제 posterior 표본, 과정잡음·비선형 성장, 현장 최초도달 또는 신뢰상한의
검증이 아니다.

현재 126개 계산기·54개 인터페이스·51개 부분 구현·68개 계획의 299개 능력, 156개 구현 근거와
144개 공개 schema다. wheel 88파일·sdist 596파일·review ZIP 589파일의 제한 원자료 제외 감사가
통과했다. 전체 목표 진행률은 독립 현장 검증 범위가 늘지 않아 65%로 유지한다.

## 2026-10-27 임계확률 기반 다음 검사후보 선택

`inspection.threshold_inspection_schedule`을 추가했다. 동일 사건·물리 범위·평가시점 생존조건의
누적 최초기준도달 확률곡선, forecast 모델 ID·revision·입력 SHA-256과 후보 ID를 보존한다. 호출자가
점추정 또는 모든 행의 상한을 판정기준으로 선택하고 최대허용확률, 최소 notice, 최대 deferral을
승인한다. 계산기는 허용 창에서 기준을 만족하는 마지막 제공 후보만 고르며 시각 사이를 보간하거나
forecast 밖으로 외삽하지 않는다.

독립 작성한 네 후보의 직접 순회에서 최대확률 0.08일 때 점추정 기준은 세 번째, 상한 기준은 두 번째
후보이며 등록 계산기가 둘을 정확히 재현했다. 전용 단위검사 11건은 비증가 시각·확률, 불완전 상한,
중복 ID, context·검토 gate·후보창과 최초후보 기준초과 경계를 포함한다. 새 HPC task 25도 로컬에서
통과해 manifest는 26개 작업이다. 이는 이산 선택 계약 검증이며 실제 열화 forecast, 허용기준,
검사효과, 비용·결과 또는 규격 검사주기를 검증하지 않는다.

현재 125개 계산기·54개 인터페이스·51개 부분 구현·68개 계획의 298개 능력, 155개 구현 근거와
142개 공개 schema다. 집중 회귀 197건과 로컬 HPC 작업 25번이 통과했다. wheel 88파일·sdist
590파일·review ZIP 583파일의 제한 원자료 제외 감사도 통과했다. 전체 목표 진행률은 독립 현장
검증 범위가 늘지 않아 65%로 유지한다.

## 2026-10-27 균열성장 시나리오 portable map/reduce

`fracture.tabulated_crack_growth_scenario_reduction`과 시나리오 manifest·외부 평가행 계약을 추가했다.
각 배열 작업은 완전입력 시나리오 하나를 계산하고 scenario ID, canonical input digest, evaluator ID·
revision·configuration digest와 결과 digest를 JSON으로 남긴다. reducer는 누락·추가·중복 ID, 입력
digest 불일치와 평가자 혼합을 거절하고 manifest 순서를 복원한다. 한 행이라도 `needs_data`,
`out_of_scope`, `invalid_input`, `execution_failed`이면 그 행을 보존하고 집계를 보류한다.

두 시나리오의 평가행을 역순으로 공급한 검증에서 reducer가 원 manifest 순서를 복원했고 프로세스 내
앙상블의 평균·표준편차·분위수·초과질량과 정확히 일치했다. 단일 작업용
`scripts/crack_scenario_job.py`, 집계용 `scripts/crack_scenario_reduce.py`, Slurm 배열 템플릿
`hpc/crack_scenario_array.sh`를 추가하고 예제 입력으로 로컬 map/reduce smoke test를 통과했다. 이는
실행 분산 계약의 검증이며 입력분포·모델형식·실험 타당성 또는 FTA 기간 확률을 새로 만들지 않는다.

현재 124개 계산기·54개 인터페이스·50개 부분 구현·69개 계획의 297개 능력, 154개 구현 근거와
140개 공개 schema다. 집중 회귀 185건과 로컬 HPC 작업 24번이 통과했다. wheel 88파일·sdist
583파일·review ZIP 576파일의 제한 원자료 제외 감사도 통과했다. 전체 슈퍼컴 회귀와 독립 실험 기반
입력분포 자격화는 남아 있다.

## 2026-10-27 균열성장 완전입력 시나리오 앙상블

`fracture.tabulated_crack_growth_scenario_ensemble`을 추가했다. 전역 배수로 축약하지 않고 각 가중
행이 완전한 단일곡선 또는 곡선군 결정론 입력을 보존하므로 개별 곡선점, 곡선군 구성, 형상계수 knot,
순서 있는 하중 block, 인성과 수치 제어의 공동 변화를 표현한다. scenario ID·source ID·source digest,
normalized weight와 canonical deterministic-input digest를 결과에 남기고 같은 물리 범위만 묶는다.

성장률 0.5배/2배의 전체 입력과 질량 0.25/0.75를 사용한 작성 검증은 닫힌형식 가중 평균과 약
`6.21e-14` 상대차로 일치하고 0.00102 m 초과질량 0.75를 재현했다. 곡선 한 점·형상·하중·인성을
동시에 바꾸는 비축약 경로, 실패 시나리오 집계 보류, 중복 ID·가중합·물리 범위 계약을 검사했다.
계산기는 시나리오 생성·확률 부여·보간·적합을 하지 않으며 입력불확실성 push-forward를 model-form
검증, 기간 고장확률, FTA 기초사건 또는 합격판정으로 바꾸지 않는다.

현재 123개 계산기·54개 인터페이스·50개 부분 구현·69개 계획의 296개 능력, 153개 구현 근거와
137개 공개 schema다. 집중 회귀 179건과 로컬 HPC 작업 24번이 통과했다. wheel 88파일·sdist
577파일·review ZIP 570파일의 제한 원자료 제외 감사도 통과했다. 전체 슈퍼컴 회귀와 독립 실험 기반
입력분포 자격화는 남아 있다.

## 2026-10-27 균열성장 불확실성 표본설계 안정성 진단

`fracture.tabulated_crack_growth_uncertainty_convergence`를 추가했다. 같은 분포 정의와 단일/곡선군
기준모델에 대해 둘 이상의 ordered design을 실행하고 단계별 설계·source digest·표본 수·상태를
보존한다. initial, nested refinement, 일반 refined design, independent replicate 관계를 구분한다.
nested refinement는 표본 수를 늘리면서 기존 ID와 성장률·형상·응력·인성 배수행을 유지해야 하고,
확률질량 재배치에 필요한 정규화 가중치 변화만 허용한다.

인접 단계의 가중 평균·표준편차·요청 분위수·선언 깊이 초과질량 변화를 양의 물리 깊이 척도로
정규화해 호출자 허용값과 비교한다. 동일 퇴화 분포의 2행→4행 검증은 네 변화량이 모두 0이다.
새 표본으로 통계가 달라지면 계산 결과와 기준 미충족을 함께 보존하며, 어느 단계든 적용범위 밖이면
전체 진단을 `out_of_scope`로 두고 주장을 보류한다. 기준 만족은 수렴 증명·오차상한·분포 검증·
표본수 보증이나 위험확률이 아니다.

현재 122개 계산기·54개 인터페이스·50개 부분 구현·69개 계획의 295개 능력, 152개 구현 근거와
135개 공개 schema다. 집중 회귀 172건과 로컬 HPC 작업 24번이 통과했다. wheel 88파일·sdist
575파일·review ZIP 568파일의 제한 원자료 제외 감사도 통과했다. 전체 회귀와 슈퍼컴 25-task
배열 실행은 다음 checkpoint다.

## 2026-10-27 균열성장 공동 입력불확실성 전파

`fracture.tabulated_crack_growth_uncertainty`를 추가했다. 호출자 정규화 공동 표본의 성장률·형상계수·
인장응력·파괴인성 전역 배수를 단일 곡선 또는 곡선군 결정론 계산에 적용한다. 분포·표본설계·원본
digest, 행 ID·가중치와 행내 의존성을 보존하고 내부 난수생성·적합·재정규화·실패행 삭제를 하지 않는다.
한 행이라도 적용범위 밖이면 모든 행 결과는 남기되 평균·표준편차·inverse-CDF 분위수·깊이 초과질량을
전부 보류한다.

성장률 배수 0.5/2.0, 질량 0.25/0.75인 작성 표본의 가중 평균 깊이를 직접 닫힌식과 대조한 상대차는
약 `6.21e-14`이고 0.00102 m 초과질량은 0.75다. 이 출력에 새 확률 의미
`model_implied_input_uncertainty_probability`를 부여해 기간 최초고장확률과 구분했다. 가중합·표본 ID·
분위수 계약, 실패표본 집계 보류와 단일/곡선군 기준입력을 검사했으며 HPC 작업 24번도 통과했다.
현재 121개 계산기·54개 인터페이스·50개 부분 구현·69개 계획의 294개 능력, 151개 구현 근거와
133개 공개 schema다. 집중 회귀 165건과 wheel 88파일·sdist 573파일·review ZIP 566파일의 제한
원자료 제외 감사가 통과했다. 실제 입력분포·model-form·공간/시간장·표본수렴과 독립 실험 검증은 남아 있다.

## 2026-10-27 복수 R·주파수 균열성장곡선 선택

`fracture.tabulated_curve_family_growth`를 추가했다. 한 family의 모든 곡선은 같은 재료상태와 환경을
가져야 하며 curve ID와 R·주파수 조건쌍은 고유해야 한다. 각 인장 block에 대해 R 절대차와 주파수
상대차를 호출자 허용차로 정규화하고 범위 안의 유일한 최근접 곡선만 선택한다. 후보가 없거나 최소
거리 동률이면 중지하며 조건간 보간·평균·회귀는 하지 않는다. 선택 곡선 ID와 모든 후보 진단을
결과에 보존한다.

R=0.1·1 Hz의 `C=1e-28` 3차 곡선과 R=0.5·0.1 Hz의 `C=2e-28` 작성 곡선을 두 block에 순서대로
적용했다. 각 구간 닫힌형식과 최종 깊이 상대차는 약 `1.92e-11`이고 선택 순서가 일치했다. 후보 없음,
동률, 유일한 허용차 내 후보, 재료·환경 혼합 거절을 단위검사하고 HPC 작업 24번도 다시 통과했다.
현재 120개 계산기·54개 인터페이스·50개 부분 구현·69개 계획의 293개 능력, 150개 구현 근거와
131개 공개 schema다. 집중 회귀 158건이 통과했고 wheel 88파일·sdist 571파일·review ZIP 564파일의
제한 원자료 제외 감사도 통과했다. 실제 곡선의 권리·독립성·전이성과 불확실성 검증은 남아 있다.

## 2026-10-27 사용자 표형 피로균열성장곡선과 적분기

`fracture.tabulated_growth_rate`와 `fracture.tabulated_crack_growth`를 추가했다. 사용자가 공급한
양의 `ΔK–da/dN` 점의 재료상태·환경·R·주파수·source group·SHA-256·계산 이용권한·적용성 검토를
계약으로 보존한다. 로그–로그 보간은 곡선 안에서만 수행하고, 순서 있는 인장 block의 R·주파수를
명시적 허용차로 대조한다. 비감소 형상계수표 안에서 `dN=da/(da/dN)`를 적분하며 곡선 상한·최대 K
인성·선언 깊이를 분리한다. closure, 지연, 과대하중 상호작용, 소성, 잔류응력과 확률은 포함하지 않는다.

외부 점을 사용하지 않은 3차 합성 성장곡선에서 기하평균 보간과 닫힌형식 Paris 깊이를 독립 대조했다.
보간 상대차는 약 `2.22e-16`, 1,000 cycle 깊이 상대차는 약 `2.20e-11`이며 곡선 상한 깊이는
독립식과 일치했다. 전용 8건과 기존 균열·전체 모델 예제·취득 체크섬을 합친 152건이 통과했다.
로컬 HPC 작업 24번도 통과해 Slurm manifest는 25개 작업이다. 장부는 119개 계산기·54개 인터페이스·
50개 부분 구현·69개 계획의 292개 능력, 149개 구현 근거와 129개 공개 schema다. wheel 88파일·
sdist 569파일·review ZIP 562파일은 제한 원자료 제외 감사를 통과했다. HyMatBase의 압력 충돌과 권리
미확정 점은 내장곡선·검증값으로 복제하지 않았다.

## 2026-10-27 HyMatBase 4130X 가스 수소 피로 reader

HyMatBase record `j1e8n-2bz97`의 55,972바이트 workbook을 provider MD5와 로컬 SHA-256으로
취득했다. Rights 항목이 비어 있으므로 선택적 로컬 자료로만 유지하고 원 XLSX·점별 표·plot·수식을
공개 배포에서 제외한다. `hydrogen_fatigue_data.py`는 네 ΔK–da/dN curve의 R, 주파수, 원 행·열,
source/material-condition identity와 단위를 보존한다. 데이터 수식·부분 point pair·비양수 값·구조
변경은 거절한다.

실제 감사에서 네 curve는 67·79·62·63점, 총 271점이었다. HyMatBase record의 압력 4.5 MPa와
workbook의 45 MPa가 10배 달라 두 값을 보존하고 명시적 승인 없이는 reader를 중지한다. workbook의
`RT`도 record 298.15 K로 자동 대체하지 않는다. 전용 합성검사 5건과 reader·취득·전체 모델 예제
집중 묶음 135건이 통과했다. 두 원자료 감사를 더한 Slurm manifest는 24개 작업이다. 현재 117개 계산기·
54개 인터페이스·50개 부분 구현·69개 계획의 290개 능력, 147개 구현 근거와 125개 공개 schema다.
현재 wheel 88파일·sdist 561파일·review ZIP 554파일을 재생성해 제한 원자료 제외 감사를 통과했다.

## 2026-10-27 연속 pipeline ILI 원자료 reader와 전수 감사

Mendeley 공개 API에서 CC BY 4.0 원자료의 네 XLSX와 README PDF를 공급자 SHA-256으로 취득했다.
`pipeline_ili_data.py`는 caller-pinned hash, pipeline/run identity, provider 행번호와 결측을 보존하고
명시된 m·mm·degree만 SI로 변환한다. `Year`는 실제 설비 나이가 아니며 각 행에는 물리 feature ID가
없음을 계약에 고정했다. 임의 matching·보간·결측 대체·성장률은 수행하지 않는다.

bounded-memory XLSX XML 감사는 3,198,420행·4회차·269,180,366바이트를 전수 확인했다. year mismatch,
수식, 비수치 값은 모두 0이다. Year 3의 seam orientation은 832,681행 전부 결측이고 Year 5의 end
absolute distance는 759,683행 전부 결측이다. 취득 장부는 30묶음·111파일·3,546,791,157바이트다.
집중 reader·취득·전체 모델 예제 검사 130건이 통과했다. 현재 117개 계산기·53개 인터페이스·
50개 부분 구현·69개 계획의 289개 능력, 146개 구현 근거와 122개 공개 schema다.

## 2026-10-27 누설자속검사 acquisition 계약

`inspection.magnetic_flux_leakage_acquisition_summary`에 자화기, 센서 channel/component mapping,
reference feature, H/B field-state checkpoint, encoded scan과 indication 계약을 추가했다. 검토된 encoder
span과 vector magnitude, 비구성적 B/H magnitude ratio만 계산하며 saturation·field uniformity·검사
감도·결함 크기로 변환하지 않는다. 집중 및 전체 모델 예제 검사 130건, 독립 산술 검증과 Slurm 22번째
작업이 통과했다. 현재 장부는 117개 계산기·52개 인터페이스·50개 부분 구현·69개 계획의 288개 능력,
146개 구현 근거와 120개 공개 schema다.

CC BY 4.0의 연속 ILI 자료 `10.17632/c2h2jf5c54.1`과 이를 사용하는 MIT 저장소 commit
`e153d3e8d0539722abcfaaabb989c6423256278e`을 검토했다. 가공 파일은 원 MFL flux·calibration·lift-off·
독립 excavation truth가 아니므로 MFL 검증으로 승격하거나 공개 배포물에 복제하지 않았다.

## 2026-10-27 와전류검사 acquisition과 DICONDE 계약

`inspection.eddy_current_acquisition_summary`에 probe·coil/channel·주파수·lift-off 근거, reference
standard feature, encoded raster와 indication 연결을 추가했다. 전체 좌표가 검토된 경우에만 raster
span을 계산하고, conductivity·상대투자율·온도·적용성 선언이 완전한 선형 균질 조건에서만 고전
skin depth를 기술값으로 계산한다. 신호 처리·검출·치수·합격·POD는 수행하지 않는다.

CC BY 4.0의 BAM simulation/laboratory archive 두 개를 provider MD5와 SHA-256으로 고정했다. 독립
reader는 DICONDE Eddy Current Image Storage/EC modality와 저장 정수 배열·padding·frame별 rescale·
좌표를 보존하고 rescale 또는 phase rotation을 자동 적용하지 않는다. 공개 자료 감사는 simulation
CSV 12개와 laboratory DICONDE 10개를 확인했다. 전용 및 예제·취득 검사 140건이 통과했고 독립
산술 검증과 21번째 Slurm 작업을 추가했다. 현재 장부는 116개 계산기·52개 인터페이스·49개 부분
구현·70개 계획의 287개 능력, 145개 구현 근거와 112개 공개 schema다.

## 2026-10-27 TOFD acquisition 계약

기존 `inspection.tofd_depth`를 호환 유지하고 `inspection.tofd_acquisition_summary`와 probe-pair/frame/
diffraction-pick/indication 공개 계약을 추가했다. 같은 frame lateral reference와 명시적으로 검토한
대칭 직선경로에서만 upper/lower tip 깊이, tip separation, backwall timing과 encoder 간격을 계산한다.
원 frame hash·순서·중복 encoder를 보존하고 결측 reference, 비인과 pick과 뒤집힌 tip을 자동 수정하지
않는다. 파형 처리, 자동 picking, dead-zone, 곡면 ray tracing, acceptance와 POD는 제외했다.

전용시험 13건과 5/15/25 mm 독립 기하 검증을 추가했다. 현재 장부는 115개 계산기·51개 인터페이스·
48개 부분 구현·71개 계획의 285개 능력, 144개 구현 근거와 105개 공개 schema다. Slurm 배열은
TOFD 검증을 더해 20개 작업이다.

## 2026-10-27 ML-NDT local-clone reader

공개 배포물에 2.63 GB 원자료를 복제하지 않고 사용자가 보유한 고정 commit clone을 읽는
`ml_ndt_data.py`를 추가했다. training/validation partition, 대문자 canonical batch UUID와 `.bins`,
`.meta`, `.jsons`, `.labels` quartet를 보존한다. UInt16 선언 형상과 파일 크기, 연결 JSON object와
label 행 수, 네 파일의 SHA-256을 검사하며 제공자 문자열을 임의 정규화하지 않는다. label과 JSON의
equivalent size 불일치는 고치지 않고 집계한다. 영상 읽기는 meta에 없는 byte order를 호출자가
명시해야 하고 감사 뒤 binary digest를 다시 확인한다.

합성 clone 집중시험 10건이 revision/형상/행 수/바이트 수/UUID/연결 JSON/digest 변경과 C-order
slice를 검사해 통과했다. 현재 장부는 114개 계산기·51개 인터페이스·48개 부분 구현·71개 계획의
284개 능력, 143개 구현 근거와 100개 공개 schema다. 원자료 다운로드·재배포는 추가하지 않았고,
provider split과 virtual flaw를 독립 물리 시편·독립 crack·raw FMC·POD truth로 승격하지 않았다.
다음 검사 확장은 TOFD acquisition/geometry 계약이다.

## 2026-10-27 encoded 위상배열 acquisition 계약

`inspection.phased_array_acquisition_summary`와 probe/wedge/focal-law/frame/indication 공개 계약을
추가했다. pulse-echo와 separate transmit/receive, conventional law와 FMC를 분리하고 active aperture,
delay count, encoder 방향, frame/law/location linkage를 검사한다. 원 frame hash·순서·중복 위치를
보존하며 aperture·wavelength·pitch ratio·delay span·encoder 간격만 계산한다. 파형 처리, TFM,
결함 검출·크기·acceptance·POD는 수행하지 않는다.

전용시험 11건과 독립 합성 산술 검증을 추가했다. 현재 장부는 114개 계산기·50개 인터페이스·48개
부분 구현·71개 계획의 283개 능력, 143개 구현 근거와 97개 공개 schema다. Slurm 배열은 19개
작업이다. ML-NDT 고정 commit은 LGPL-3.0, 804 data blob, 2,628,979,711바이트와 199/2 batch를
확인했지만 한 물리 316L pipe의 세 crack에서 만든 augmented B-scan이므로 metadata-only로 기록했다.
Strathclyde CC BY 4.0 자료는 98.9 MB 파일을 명시하지만 checksum 부재와 403 challenge로 취득하지
못했다. 실제 waveform reader와 physical-specimen holdout 검증은 남아 있다.

## 2026-10-27 방사선투과검사 기록·촬영기하 계약

`inspection.radiographic_geometry_summary`와 source/exposure/detector/image/IQI/image-indication
공개 계약을 추가했다. X-ray tube voltage와 gamma isotope/source activity를 구분하고, 원 영상 hash와
pixel 크기, detector calibration basis, IQI 배치·보고 결과, 영상 bounding box와 선택적 물리 위치
mapping을 보존한다. pinhole 관계에서 magnification, focal-spot geometric unsharpness와 object-plane
pixel pitch만 계산하고 규격 threshold·결함 크기·acceptance·POD를 내장하지 않는다.

집중시험 11건, 전체 등록 예제 집합을 포함한 125건과 독립 합성 산술 검증이 통과했다. 현재 장부는
113개 계산기·50개 인터페이스·47개 부분 구현·72개 계획의 282개 능력, 142개 구현 근거와 91개
공개 schema다. Slurm 배열은 18개 작업이다. X-weld Zenodo 자료는 provider metadata상 Apache-2.0인
475,303,436바이트 선택 후보로 등록했지만 촬영조건·시편·annotation/truth가 없어 취득·검증 완료로
세지 않는다. GDXray는 재배포/상업 이용 제한, RIAWELC는 명시적 license 부재로 공개 catalog에서
제외했다. 실제 detector/IQI 성능과 physical-specimen holdout 검증은 남아 있다.

## 2026-10-27 침투·자분 표면검사 기록 계약

`inspection.liquid_penetrant_summary`와 `inspection.magnetic_particle_summary`, 공통 area/indication,
magnetization pass를 추가했다. 침투검사는 검사계 family·제거방식·소모품 batch·재료/표면·전처리·
건조·절대온도·침투/현상시간·관찰·후세정을 보존한다. 자분검사는 강자성 적용성·particle/carrier·
장비·current mode·field adequacy와 `[0,π)` 무방향 field 각도를 보존한다. 사용자 승인 최소 방향각과
영역별 최대 acute separation을 비교하며 pass가 없거나 한 방향뿐인 영역을 완료하지 않는다.

집중시험 10건과 등록 예제 2건이 통과했다. 독립 합성 검증은 coverage 0.75와 무방향 분리 0.3 rad를
회복했다. 현재 장부는 112개 계산기·50개 인터페이스·46개 부분 구현·73개 계획의 281개 능력,
141개 구현 근거와 88개 공개 schema다. Slurm 배열은 17개 작업이다. 실제 PT/MT 원자료, 절차,
인공결함 truth, field 정량성, 검사자 반복성과 POD/acceptance 자격화는 남아 있다.

## 2026-10-27 육안 표면검사 기록 계약

`inspection.visual_surface_summary`와 area·indication·examination 공개 계약을 추가했다. 사용자
절차/개정, direct/remote 방식, 표면 준비·상태, 조명·분해능 근거, 상호배타 target/examined 영역,
부분 미검사 사유, 물리 위치별 지시와 증거를 보존한다. coverage와 기술 집계만 계산하고 필수
검토가 없으면 관측을 유지한 채 `needs_data`를 반환한다. 빈 지시 목록은 별도 음성결과 검토가
필요하며 합격·결함분류·POD·수명·고장확률을 생성하지 않는다.

합성 3.0/2.5 m² 사례는 coverage 5/6을 오차 0으로 회복했고 금지된 합격·확률 필드가 없었다.
집중시험 9건은 면적·mapping·negative-result·등록 경로를 검사했다. 장부는 110개 계산기·50개
인터페이스·44개 부분 구현·75개 계획의 279개 능력, 139개 구현 근거와 83개 공개 계약 schema다.
Slurm manifest에는 독립 육안검사 검증 작업을 추가해 총 16개 배열 작업으로 늘렸다. 전체 원격
배열과 실제 검사 성능 자격화는 아직 수행하지 않았다.

후속 공개자료 조사에서 Zenodo 공식 API가 CC BY 4.0으로 선언한 다시점 판재 균열 영상
`10.5281/zenodo.18731788`을 optional 취득 대상으로 등록했다. 676,496,455바이트 파일은 두 번의
read timeout으로 전체 취득되지 않았고 성공 건수에 넣지 않았다. 대용량 `.part`에 HTTP Range를
요청하고 서버가 206으로 응답할 때만 append하는 재개 수집기를 추가했으며, 합성 부분파일의 정확한
결합·체크섬 시험을 통과했다. 원 ZIP·부분파일은 공개 배포 경로에서 제외한다.

## 2026-10-27 기준시편 pulse-echo 음속 적합과 보류 검증

사용자 보유 기준시편을 바로 연결할 수 있도록 `inspection.pulse_echo_sound_speed_fit`과 두 공개
입력 계약을 추가했다. 검토된 zero offset·입사각을 고정하고 최소 세 calibration 위치의
`thickness = c (ToF-offset) cos(angle)/2` 관계를 원점 통과 최소제곱으로 적합한다. 물리 위치와
source group이 calibration/holdout을 넘나들면 거절하고, holdout은 적합 뒤 잔차 평가에만 쓴다.
조건부 음속 표준오차와 양쪽 RMSE·최대잔차·두께 지원범위를 반환한다. 두께 변환용 교정 조각은
sample 범위를 비우고 검토 상태를 false로 두어 자동 승격을 막았다.

점별 기준치수·왕복시간 표준불확실성 쌍을 받는 반복 effective-variance 선택을 추가했다. 두
분산을 현재 음속으로 합성해 가중치를 갱신하고 조건부 표준오차·residual-scaled 표준오차·reduced
chi-square·holdout 표준화 잔차를 반환한다. 불확실성 쌍 누락과 반복 비수렴은 중지한다. JSON을
통하지 않고 Python 계약 객체만 사용하는 `examples/pulse_echo_sound_speed_fit.py`도 추가했다.

합성 5920 m/s·30 ns 사례에서 독립 닫힌 식과 구현이 정확히 일치하고 holdout 변경이 적합값을
바꾸지 않음을 `validation/pulse_echo_calibration_math.json`에 기록했다. 실제 기준치수·ToF·zero
offset·온도·probe 및 현장 전달성 불확실성은 검증하지 않았으며 후속 실자료 자격화 대상으로 남긴다.
점별 2 µm·1 ns 합성 불확실성에서 독립 식과 구현의 음속 표준오차가 정확히 일치했다.
현재 장부는 109개 계산기·50개 인터페이스·43개 부분 구현·76개 계획의 278개 능력과 138개 구현
근거, 80개 공개 계약 schema를 기록한다. 로컬 전체 868개 검사는 실패·오류·건너뜀 없이
통과했다.

전체 회귀를 슈퍼컴에서 일괄 실행할 수 있도록 `hpc/task_manifest.json`, 결정론적 pytest 8분할,
배열 작업 실행·집계 도구와 Slurm 예제를 추가했다. 배열은 각자 node-local scratch 사본에서
실행해 생성물 충돌을 피하고 manifest hash·JUnit·명령 출력 hash를 남긴다. 로컬 smoke로 Ruff
작업과 pytest shard 하나를 통과시켰다. 클러스터 전체 배열 실행은 아직 수행하지 않았다.

## 2026-10-27 pulse-echo ToF 두께 교정 계약

CEIT/WATEREYE의 CC BY 4.0 공개 연구 `10.3390/app12020808`을 현장 JSON과 별도로 검토했다.
연구는 연속 후면 에코의 왕복시간, V111 종파 프로브와 S355J2G3 기준시편의 실온 음속
5950 m/s 교정을 제시한다. 여덟 기준 위치·위치별 다섯 ToF, 한 위치당 25회 반복과 표준편차의
의미를 확인했다. 현장 JSON의 시편 표식·프로브·ToF 규모는 호환되지만 장치 교정 계보·zero
offset·`tof_c` 보정식·단위 선언은 연결되지 않는다. 따라서 문헌 값을 현장 기본값으로 넣지 않았다.

`PulseEchoThicknessCalibration`과 `pulse_echo_thickness_observations`를 추가했다. caller가 검토한
재료·시편·프로브 적용범위, 종파 음속·온도, zero offset, 입사각, raw/보정 ToF 선택, 근거를
공급해야 한다. 단위·검토·ID·온도보정 근거가 빠지면 중지하며 교정 digest와 원 레코드 ID를
보존한다. 합성 왕복경로 항등식은 7.5 mm를 오차 0으로 회복했다. 현장 자료에 5950 m/s와 ns를
가정한 4.928~5.414 mm 범위는 호환성 진단으로만 기록하고 자격 있는 두께 series로 내보내지
않았다. 불확실성·공간 위치·독립 치수 참값이 없어 부식속도와 Bayesian 갱신도 차단한다.
전체 862개 검사가 통과했다. 현재 장부는 108개 계산기·50개 인터페이스·43개 부분 구현·76개
계획의 277개 능력과 137개 구현 근거를 기록한다.

## 2026-10-27 CEIT 해안 노출 균일부식 장치 시계열 확보

Zenodo `10.5281/zenodo.13897090`의 CC BY 4.0 JSON 49,918,087바이트를 제공자 MD5와
대조해 확보했다. 하나의 S355 표식 시편·node·piezo에 대한 2,715개 레코드가 엄격 증가하며,
raw·filtered 각 2,048, correlation 64, envelope 512표본을 전수 확인했다. 모든 값은 유한하지만
모든 raw 레코드에 ADC rail 표본 3~77개가 있다. 139개 관측 날짜 중 114일이 20개 레코드를
가지므로 제공자 설명의 하루 두 번을 원행 수나 독립 관측으로 바꾸지 않았다.

`read_ceit_uniform_corrosion_field`는 원 시각·장치 필드·네 신호와 rail 개수를 보존한다. JSON이
ToF·온도·파형 시계 단위를 직접 선언하지 않으므로 호출자가 검토한 단위를 넣을 때만 초·K·표본
시계를 만든다. 음속·경로·zero 보정·공간 footprint·독립 두께가 없어 두께와 부식속도를 만들지
않고, 제공자 요약 134 µm/year도 재현되지 않은 메타데이터로 둔다. 전체 860개 검사와 새 wheel의
비편집 전체 의존성 설치가 실패·오류·건너뜀 없이 통과했고, 설치된 108개 모델 source가 작업본과
일치했다. 능력 장부는 108개 계산기·49개 인터페이스·43개 부분 구현·76개 계획의 276개 항목이며
구현 근거는 136개다.

## 2026-10-27 COQTEL 실제 HDF5의 시편·상태·교란 경계 강화

기존 COQTEL reader와 두 원파일을 다시 감사했다. 새 데이터셋으로 중복 등록하지 않고 기존
`coqtel` 자료의 권리·제약 장부를 보강했다. 파일별 SHA-256을 고정하고 실험 1의 166상태·664
actuator 파형, 실험 2의 263상태·1,052 actuator 파형을 전수 검사했다. 모든 파형은 5×2000,
200 kHz, 2 MHz, 5 cycles이며 EC 행 수와 `State_i` 수가 일치한다.

파일 두 개만 독립 물리 시편 두 개로 기록하고 내부 상태를 반복 관측으로 바꿨다. 실험 1의 동일
시각 10구간과 실험 2의 2구간을 제거하지 않으며, 실험 2 state 30~100은 논문 보고 공기방울
교란으로 표시한다. root image의 state 연결·길이 보정과 상태별 pit 치수가 없음을 API와 집계
검증에 고정했다. 전하·파형 변화를 pit 치수·POD·수명으로 승격하지 않는다. 전체 구조용 합성
검사를 추가하고 공개 집계 `validation/coqtel_dataset.json`을 만들었다. 전체 859개 검사와
새 wheel의 비편집 전체 의존성 설치가 실패·오류·건너뜀 없이 통과했고, 설치된 108개 모델의
source가 작업본과 일치했다. wheel·sdist·review ZIP의 제한 원자료 제외 감사도 통과했다.

## 2026-10-27 동부 하이난 5행 대조와 Egua-2 미리보기 부재 확인

공식 PipeChina API 응답이 동부 하이난 원 논문의 위치 1~4와 60만 재수록한다는 점을 고정 해시로
확인했다. 압력 kPa→bar와 액상·기상 벽면 전단응력의 산술평균을 명시적으로 적용하고, 온도·총압·
CO₂ 분압·유속·pH·전단응력 여섯 필드로 편집본 전체를 검색했다. 각 행은 provider source row
245~248·304에 하나의 후보를 만들었다. 여섯 필드는 모두 일치했고 부식속도는 첫 네 행이
일치했지만 위치 60은 3.11 대 2.86 mm/year로 달랐다. 공개 검증에는 집계와 불일치 하나만 남기고
API 응답·점별 표는 제외했다. 전체 60행 source group이나 독립 위치로 승격하지 않았다.

Egua-2 DOI `10.4028/p-brqaI1`의 출판사 미리보기 12쪽을 텍스트 추출하고 페이지 4·5를 렌더링해
확인했다. 대상 제목은 목차에만 있고 본문은 다른 논문으로 시작하며 대상 DOI와 관측 표가 없다.
따라서 이 미리보기는 74행 대조 자료가 아니며, 공개 기록에는 해시·페이지 수와 부재 판정만 둔다.

## 2026-10-27 습식 CO₂ 문헌 행 대조 계약과 오토클레이브 후보 감사

오토클레이브 자료 근거로 인용된 DOI `10.1016/j.psep.2018.07.006`의 기관 저장소 accepted
manuscript를 로컬 근거로 검토했다. 부록의 학습 16행·시험 6행은 온도·유속·pH·부식속도 순서에서
편집본 provider source row 334–355에 유일한 22행 후보를 만들었다. 그러나 논문 부록은 연계
preprint가 같은 문헌에서 왔다고 보고한 50개보다 28개 적다. CO₂ 압력 MPa를 bar로 명시적으로
변환하면 19개는 일치하고 source row 346·349·355의 세 값은 불일치했다. 이를 자동 오타 수정이나
확정 source-group 연결로 바꾸지 않았다.

호출자가 보유한 근거 행과 검토한 단일값/산술평균 affine 변환을 받는
`audit_wet_co2_literature_row`와 네 공개 계약을 추가했다. 결과는 원값·변환값·편집값·허용오차·
결측·불일치, 서지/행 연결 수준, 출판물 라이선스·관측 재배포 상태와 시편 ID를 분리한다. 모든
선언 필드가 일치해도 경험·기구 보정 준비 상태는 false다. CC BY-NC-ND 4.0 PDF와 점별 표는
배포에서 제외하고 공개 검증에는 집계와 세 불일치만 남겼다. 합성 계약검사 4개를 추가했다.
당시 전체 858개 검사와 비편집 wheel 전체 의존성 설치가 실패 없이 통과했고, 설치된 108개 모델의
source가 작업본과 일치했다. 능력 장부는 108개 계산기·48개 인터페이스·43개 부분 구현·76개
계획의 275개 항목이며 공개 계약 schema는 77개다.

## 2026-10-27 습식 CO₂ 모의 243행의 정확한 외부 출처 대조

Mendeley Data의 CC BY 4.0 자료 `10.17632/4nydhxjymw.1`에서 고정 workbook을 취득하고
제공자 파일 크기와 SHA-256을 대조했다. Workbook의 실제 8개 열, 단위표와 243개 수치행을
읽어 이질적 편집 CSV의 provider source row 2~244와 위치별로 비교했다. 243행 모두에서 헤더와
8개 수치가 정확히 일치했으며 값 집합도 243개가 일치했다. 따라서 이 범위만 하나의
`simulated_model_output` source group으로 연결했다. 대조 함수는 고정 해시·단일 sheet·정확한
헤더·단위표·행 수와 모든 값을 검사하고 하나라도 다르면 결과를 만들지 않는다.

이 자료는 NORSOK M-506 구현에서 생성한 응답이므로 물리 관측, 실험 보정 또는 독립 검증으로
표시하지 않는다. 자료의 CC BY 4.0을 NORSOK 규격·구현 코드·표의 재배포나 공개 surrogate 권리로
확대하지 않는다. 편집본의 나머지 184행은 논문의 집계 수량이나 결측 패턴으로 유형을 추정하지
않고 미확정 상태로 유지했다. `WetCo2SimulationSourceMatch`, 공개 스키마, 검사 스크립트와
두 개의 거절/일치 테스트를 추가했다.

## 2026-10-27 습식 CO₂ 연계 논문의 단위 근거 분리

연계 CC BY 4.0 preprint `10.21203/rs.3.rs-8896642/v1`을 원 CSV와 별도로 검토했다. 동일한
427행 통계표가 °C·m/s·bar·%·Pa·mm/year 단위를 선언하고, 자료가 243개 NORSOK M-506
생성값·50개 오토클레이브 중량감소·60개 중국 해저 배관 현장값·74개 Egua-2 현장값으로
구성됐다는 집계를 확인했다. 논문 문장·표·그림은 복제하지 않고 DOI·라이선스·확인 사실만
근거 장부에 기록했다.

CSV 자체의 단위 부재와 논문의 unit basis를 분리한 `WetCo2SiObservation` 계약을 추가했다.
정확한 Table 1 basis ID를 호출자가 승인해야만 SI 변환하며, 행별 유형·원출처·시편·재료·노출
조건은 계속 미확정이다. 논문이 행 번호 연결을 제공하지 않으므로 배열·결측 패턴으로 그룹을
추정하지 않았고 경험·기구 모델 보정은 모두 차단했다.

## 2026-10-27 습식 CO₂ 후보 데이터의 자격화 중지

Harvard Dataverse의 CC0 표시 CSV 427행을 공식 API와 제공자 MD5로 취득했다. 8개 수치열은
있지만 단위·원 문헌·데이터 유형·시편·재료·노출시간이 없음을 전수 감사했다. 임의 단위 변환이나
회귀로 진행하지 않고, 원행·원값·결측·해시와 미확정 상태를 보존하는 로더 및 공개 스키마를
추가했다. 능력 장부의 `degradation.wet_co2`는 원자료 인터페이스만 가진 부분 구현으로 변경했다.

## 2026-10-27 탄소강 1년 대기부식 전이 진단

CC BY 4.0으로 표시된 조화 자료 ZIP을 고정 해시로 취득하고, 프로그램 617행과 독립 연구 106행을
권리·출처 인식 계약으로 읽는 로더를 추가했다. 공급자 스크립트나 문장을 복제하지 않고 고정 특징의
로그선형 최소제곱을 독립 구현했다. 합성 계수 회복·안전 ZIP·partition 누설·지원범위·context를
검사했다. 실제 A/B 등급 83행 보류에서 전이 기준이 실패했으므로 모델 계약에 기준값과 결과를
고정하고 무검토 예측을 차단했다. 집계 검증만 공개하며 점별 원 관측은 배포하지 않는다.

## 2026년 10월 27일 Gaussian 평균이동 희귀사건 중요도 샘플링

표준정규 잠재공간과 unit-covariance 평균이동 제안분포 사이의 정확 우도비를 사용하는
`reliability.gaussian_mean_shift_importance_sampling`을 추가했다. 외부 부식·파괴·FTA 평가자가
만든 Boolean 사건 지시값을 고유 sample ID로 연결하고 자산·부위·기간·생존조건, 사건 정의,
설계/생성기, 잠재 매핑과 평가자 리비전·설정 digest를 보존한다. 가중치는 자르거나 자동
자기정규화하지 않으며 비정규화 비편향 추정량, 표본 표준오차·정규근사 구간, 전체/사건 ESS,
가중치 평균과 최대 정규화 가중치를 분리했다. 누락 평가를 정상사건으로 바꾸는 경로는 제공하지
않는다.

작성 합성 `Z>4` 사건의 정확값 `3.167124183311998e-05`에 대해 고정 seed `N(4,1)` 표본
32,768개로 `3.1147082116145e-05`를 얻었다. 절대오차 `5.241597169749806e-07`은 사전 선언한
6 표준오차 기준 안이었다. 전체 가중치 ESS가 약 12.62로 낮은 사실도 숨기지 않고 기록했다.
0 이동 crude Monte Carlo 항등식, 직접 우도비, 사건 0건, 검토 gate, 정체성·차원·비유한 값과
context 불일치를 전용 검사 16개로 확인했다. 이는 Gaussian 산술 검증이지 실제 물리 분포,
한계상태, FTA, 최적 제안 또는 고장확률의 독립 검증이 아니다. 희귀사건 확장 항목은 partial로
바꾸고 적응형·혼합 제안, subset simulation, 스트리밍 batch와 실제 보정/holdout은 남겼다.
전체 837개 검사와 비편집 wheel 전체 의존성 설치가 실패 없이 통과했고 설치 source가 현재
작업본과 일치했다. 카탈로그는 106개 계산기·43개 인터페이스·41개 부분 구현·77개 계획의
267개 항목이며 공개 계약 schema는 65개다. 첫 배포 감사에서 wheel 75파일, sdist 404파일,
review ZIP 396파일의 제한 원자료 제외가 통과했다.

## 2026년 10월 27일 유도초음파 pairwise·ensemble descriptor와 실자료 제한 검증

같은 physical specimen·archive의 서로 다른 두 acquisition에서 정확한 주파수와 torsional/flexural
채널을 선택하는 중립 adapter와 `inspection.guided_wave_pair_features`를 추가했다. 호출자 공간창을
그대로 사용하고 정렬·보간하지 않으며, 정렬 거리 grid와 반복 위치를 검사한다. 반복 표본은 보존,
연속 정렬쌍 평균 또는 거절 정책으로 명시한다. RMS·정규화 residual·에너지비·상관·최대/평균 차이를
계산하지만 손상 등급·두께·POD·합격·수명·확률로 바꾸지 않는다. 직접 계산 항등식, 영 baseline,
공간창, 축·identity gate와 세 반복 정책을 전용 검사 17개로 확인했다.

고정 원자료에서는 acquisition 1622를 한 baseline으로 선언하고 1901, 1902, 1930의 14 kHz 두 모드를
+2.0~+3.2 m 창에서 기술 비교했다. 건강기간 내부 1622→1901의 정규화 residual RMS도 torsional
약 0.503, flexural 약 0.241이어서 단일 baseline 변화가 손상 특이적이지 않음을 보존했다. 같은 한 관,
미확정 온도·시각·결합 상태와 미제공 여섯 단계 대응 때문에 이 결과는 분류·위치·POD 검증이 아니다.
공개 검증 JSON에는 집계값과 digest만 기록하고 점별 파형을 복제하지 않았다.

세 개 이상의 고유 baseline, 별도 observation, source group·선택 근거와 mean/median reference를
요구하는 `inspection.guided_wave_reference_ensemble`도 추가했다. baseline spread와 각 record의
leave-one-out residual 분포를 보존하며 observation 비를 확률이나 threshold로 이름 바꾸지 않는다.
실자료에서는 건강기간에 분산한 7개 baseline을 계산 전에 고정했다. 1901·1902·1930 flexural의
leave-one-out 최대 대비 residual 비는 약 0.507·0.732·1.096이었다. 마지막 값이 1을 넘더라도 한 관의
반복과 미확정 환경·결합·결함 치수만으로 분류·거짓경보율·POD를 검증하지 않는다.
전체 820개 검사는 실패·오류·건너뜀 없이 통과했고 비편집 wheel 전체 의존성 환경에서도 105개
모델과 같은 820개 검사 및 설치 source 일치가 통과했다. 능력 카탈로그는 105개 계산기,
43개 인터페이스, 40개 부분 구현, 78개 계획의 266개 항목이며 공개 계약 schema는 64개다.

## 2026년 10월 27일 배관 유도초음파 원자료 reader와 전수 감사

CC BY 4.0의 한 실험관 유도초음파 자료를 고정 SHA-256으로 취득하고 외부 ZIP 안의 내부 ZIP과
236개 legacy XLS를 안전하게 읽는 독립 API를 추가했다. 경로 이탈·중복·암호화·schema 변조를
거절하고 acquisition/workbook/sheet/physical specimen ID, 원 sheet 순서, 다섯 주파수와 세 전압
채널을 보존한다. 1,180개 sheet를 전수 읽어 실제 2,509×4, 숫자 2,958,260행, 동일 거리 grid,
sheet마다 반복 거리 한 구간, 9종 sheet 순서와 DAC 비영 값 0개를 확인했다. 논문 설명의 2,057×4
차이를 수정하지 않고 감사 기록에 남겼다. 207개 건강 기간과 29개 가공 후 기간은 원본 digest에만
적용하며 여섯 가공 단계·치수·시각·온도는 추정하지 않는다. 합성 XLS/ZIP 계약 검사 14개가
통과했고 전체 788개 검사도 실패·오류·건너뜀 없이 통과했다. 새 wheel을 비편집 전체 의존성
환경에 설치한 검사도 788개 통과와 source 일치를 보고했으며 wheel·sdist·review ZIP의 제한
원자료 제외 감사가 통과했다.

2026년 10월 27일에는 반복 검사 두께를 기준시점 잔여두께와 일정 손실률의 Gaussian
사후분포로 연결하는 `reliability.bayesian_linear_thickness_update`를 추가했다. 한 물리 위치,
관측·campaign·source group·측정법/교정 ID와 사전 지정 update/holdout partition을 보존한다.
독립 측정오차 선언 또는 update 행에 정렬된 검토 공분산 중 하나만 허용하고, holdout 값은
posterior에서 제외한다. 요구두께 미달은 특정 시점 상태확률, 양의 손실률은 사후 모수확률로
표시해 기간 최초고장확률과 구분했다. 독립 정보형 해, batch/sequential 동치, holdout 불개입,
상관 공분산·review gate·identity·정규분포 항등식의 전용 검사와 공개 계약 2개를 추가했다.
이는 합성 수학 검증이며 실제 부식성장·UT 오차·POD·과정/모델형식 불확실성 검증이 아니다.
당시 103개 계산기·40개 인터페이스·261개 능력 항목·62개 공개 스키마이며 전체 774개 검사가
통과했다. 당시 추가 118과제는 39개 일부 구현·79개 계획이었다.

2026년 10월 27일에는 Figshare v2의 CC BY 4.0 `Electrochemical Metrics for Corrosion
Resistant Alloys` workbook을 제공자 MD5와 프로젝트 SHA-256으로 고정해 취득했다. 6개 지표
시트의 1,268개 원행을 3,579개 지표 셀로 분리하고 exact 1,605·문자 숫자 1·하한 14·상한
2·정성 44·누락 1,913 상태를 보존하는 `corrosion_metrics_data.py`를 추가했다. SCE 기준
전위를 기준 없는 숫자로 만들지 않고, 시험환경·방법·성분·참조번호와 원행을 유지한다. 공개
설명은 81개 문헌을 말하지만 workbook에는 참조번호 85개가 있고 84개가 실제 사용되며 그중
78개에 DOI가 있어 이 차이를 감사 기록에 남겼다. 참조번호는 물리 시편 ID가 아니고 workbook
라이선스는 원 관측 전체의 재배포 허가가 아니므로 시험 유효성·시편 독립성·원 관측 권리는
미확정이다. 원본·점별 행을 배포하지 않고 집계만
`validation/corrosion_alloy_metrics_package.json`에 보존했다. 현재 취득 장부는 23묶음·99파일·
3,124,049,854바이트이며 전체 759개 검사가 통과한다.

2026년 10월 27일에는 특정 규격식 없이 사용자·상용·외부 저장소의 파열압 예측을 자격화한
실제 시험과 비교하는 `structural.burst_pressure_comparison`을 추가했다. 관측·물리 시편·
source group·calibration/holdout/external-validation·재료·형상·하중·관측/예측 압력 기준·
원본 해시·예측 입력 digest를 보존한다. 중복 시편과 calibration에서 평가로 넘어가는 source
group은 거절하고 이용권한·시험 끝점·형상/재료·압력 기준·예측 동결이 미검토이면
`needs_data`다. 합성 압력비 1.0, 0.8, 1.25의 평균·로그오차 항등식, 엄격한 스키마와 중지
조건을 검사했다. 현재 공개 편집본은 압력 기준·물리 시편·원 관측 권리가 미확정이므로 실제
검증 입력으로 자동 연결하지 않았다. API 설명, 실행 예제, 독립 공급자 확장 요청서와 공개
스키마를 추가했다. 당시 102개 계산기·40개 인터페이스·260개 능력 항목·60개 공개 스키마이며
전체 752개 검사가 통과했다.

2026년 10월 27일에는 배관 파열 편집본의 EXP `Pb`와 FEM `Pb`를 각각 공급자 보고 시험
파열압과 공급자 보고 해석 실패압으로 분리했다. 편집본 범례에 직접 연결된 문헌 430행과
`Ma13Otros` 미해결 표식 23행, 전 453행의 미제공 물리 시편 ID와 미검토 원 관측 권리를
별도 필드로 보존한다. Ma 등 논문의 출판사 페이지는 문헌에서 전척 시험 79그룹을 수집했다고
설명하고 편집본의 직접 문헌 연결 실험도 79행이지만, 이 수의 일치로 23행의 행별 원 문헌,
중복, 독립 시편 또는 권리를 추정하지 않았다. 갱신된 집계는 `data/data_inventory.json`에
있으며 원 관측이나 논문 표를 공개 배포에 복사하지 않는다.

2026년 10월 27일에는 Sandia HELPR 공식 저장소의 `v2.1.0` tag, commit
`ae12d20b6608123af41dd9d5f70db6b6547fece5`, BSD-3-Clause 선언과 실제
`CrackEvolutionAnalysis.save_results` 경로를 검토했다. 공급자 checkout은 제외된 evidence
경로에 두고 소스·wheel에는 포함하지 않았다. HELPR의 다섯 life-criteria CSV 열만 읽는 독립
`HelprLifeCriteriaRecord`와 `read_helpr_life_criteria_csv`를 추가했다. 수신자가 자산·부위·재료·
하중·sample ID·공급자 commit·설정 digest·단위와 결측 의미를 반드시 채우며, 빈 값과 NaN은
0·runout·파단·확률로 바꾸지 않는다. 규격 유래 표·곡선과 HELPR 코드는 복제하지 않았다.
공급자 감사와 작성된 CSV 계약 검사를 각각 `validation/helpr_provider_review.json`과
`validation/helpr_adapter_contract.json`에 분리했다.

이어 공식 HELPR v2.1.0을 별도 제외 가상환경에 설치하고 제공자 통합시험 입력으로 결정론
대표 사례를 실제 실행했다. 생성된 두 CSV의 바이트와 SHA-256, 입력 설정 digest, HELPR 및
수치 의존성 버전을 로컬 manifest에 고정했다. 공개 `validation/helpr_end_to_end.json`에는 원
CSV 대신 해시·criterion 가용성·레코드 digest만 둔다. 실행에서 확인한 공급자 내부 Python
폐기예정 경고와 파괴저항 미도달에 따른 `a/t=0.8` 대체 경고를 각각 구조화해 보존했다.
어댑터 필드는 공급자 보고값으로 이름을 바꾸고 경고 검토가 없으면 수신하지 않도록 했다.
이는 실제 소프트웨어 통합 증거이지 독립 물리 검증, 규격 판정 또는 잔여수명 인증이 아니다.
당시 101개 계산기·40개 인터페이스·259개 능력 항목·58개 공개 스키마이며 전체 738개
검사가 통과했다.

## 2026년 10월 27일 FABEST HCF 종료 프로토콜 해시·적용범위 고정

고정된 경쟁 패키지 v2.1.2에서 규칙, 시험순서, 실험설비와 기술 Q&A PDF의 ZIP 내부 경로·바이트·SHA-256을 대조했다. 해당 경쟁 시험의 시편 끝점은 초기 압력의 10% 이상인 급격한 저하와 시편 압력건전성 상실 확인을 함께 요구한다. 완전 파열과 관통균열을 구분하되 완전 분리를 필수로 하지 않고, 확인 사건 없이 2,000,000 cycle에 도달한 경우만 runout으로 기록한다. 계통 문제 뒤 시편 건전성과 하중 이력이 확인되면 같은 시편의 유효 구간 cycle을 누적하며, 확인할 수 없으면 무효·불명확 상태로 남긴다.

`scripts/inspect_fabest_hcf_data.py`와 `validation/fabest_hcf_package.json`에 이 검토를 재현 가능한 메타데이터로 추가했다. `validation/fatigue_endpoint_contract.json`은 감사 JSON의 10%·2,000,000 cycle 값을 읽어 일반 종료 사건 API와 연결하고 정확한 임계값 포함성, 시편 기원 확인, 계통 중단과 누적 유효 구간을 검사한다. 이 기준은 blind HCF 경쟁 패키지에만 적용하며 별도 FABEST 데이터베이스 workbook의 60개 곡선에 누락된 END 기준·접미사·interruption 의미를 소급하지 않는다. Blind 결과 열은 계속 비어 있으므로 피로강도·수명 보정 또는 독립 실험 검증으로 사용하지 않는다. 전체 728개 검사가 통과했다.

## 2026년 10월 27일 탄화물 트랩 TDS 단위·시험 메타데이터 자격화

공개 논문과 CC BY 4.0 보충자료를 Viewer 내보내기와 대조해 TDS 탈착률·잔류량의 ppm을 시편 질량 기준 수소 질량으로 고정했다. 두 TDS 로더에 기본 `unresolved`를 유지하는 명시적 `ppm_basis`를 추가했고, 해당 원자료 장부에서만 `hydrogen_mass_per_sample_mass`를 선택한다. 보충자료의 100 K/h는 명목 프로그램으로만 기록해 측정되지 않은 elapsed-time 표본을 만들지 않는다. 투과 요약의 오차 막대는 적어도 두 측정의 표준편차로 기록한다.

곡선 크기와 노출시간 요약은 IP0→TiC, IP2→(Ti,Mo)C 대응을 지지하지만 이는 파일 간 재료명 매핑이며 곡선별 물리 시편·반복 ID가 아니다. 투과막 두께·전극 면적·전위 기준, 정확한 충전 원점, 검출기 응답, TDS source-integral 단위와 실제 시계는 계속 미확정으로 유지했다. 원문 문장·그림·표·점별 관측은 공개 소스에 포함하지 않았다. 전용 로더 검사 37개와 전체 727개 검사가 통과했다. `validation/hydrogen_carbide_applicability.json`은 확인한 메타데이터와 세 역추정 준비 상태의 false 및 차단조건을 공개 인벤토리 해시와 함께 보존한다.

## 2026년 10월 27일 한 모수 수소 수송–flow 역추정

`transport.hydrogen_slab_flow_multiplier_fit`과 공개 `HydrogenSlabFlowMultiplierFit` 계약을 추가했다. 이미 보정된 평판 표면 signed outward 수소 원자 mol/s를 정방향 `HydrogenSlab`에 연결하고, 격자 확산계수·한 트랩의 capture/release 빈도·한 표면의 transfer/absorption/desorption capacity 중 하나의 완전한 양수 이력에만 공통 배수를 적합한다. 관측·series·시편·검출기 보정·표면·경계·source group·partition·정확한 시계와 실제 면적을 보존한다. 모든 다른 입력의 독립 검토, 한 모수 범위와 holdout 사전 선언을 요구하며 calibration 행만 log-multiplier least-squares 목적함수에 사용한다.

배수 2.0의 합성 확산계수 이력에서 회수 절대오차 `8.9e-16`, fitted history와 재사용 계약 최대 절대오차 `8.3e-17 m²/s`, holdout 값 변경에 따른 적합 배수 변화 0과 최대 상대 질량잔차 `5.1e-16`을 기록했다. 전용 19개 검사는 target identity, uncertainty basis, review gate, 정확한 시계, source-group 겹침 보고, zero-history와 잘못된 경계 종류도 검사한다. `examples/hydrogen_slab_flow_fit.py`, `scripts/validate_hydrogen_inverse.py`, `validation/hydrogen_slab_flow_inverse_math.json`이 재현 경로다. 이는 같은 모델의 한 모수 recovery이며 원 TDS/투과 신호 역산, 전역 식별성, 다중 모수·모델형식·고정입력·검출기·source-group 불확실성 또는 독립 실험 검증이 아니다. 현재 101개 계산기·39개 인터페이스·258개 능력 항목·57개 공개 스키마이며 전체 726개 검사가 통과한다.

## 2026년 10월 27일 fugacity 기반 축약 수소 표면반응

`transport.hydrogen_dissociative_surface_rates`와 공개 `ThermallyActivatedSurfaceFlux`·`HydrogenDissociativeSurfaceRates` 계약을 추가했다. Caller-supplied H₂ fugacity 또는 별도로 검토한 ideal-gas partial-pressure 근사를 빈 격자 표면의 흡수 capacity에 `sqrt(f/f_ref)`로 반영하고, 흡수·방출 capacity는 각각 검토된 Arrhenius 법칙으로 계산한다. material/lattice/surface/species·gas-state provider·시계·reference fugacity·두 rate ID와 지원 범위를 보존하며 범위 밖 또는 표현 불가능한 양의 flux를 clipping하지 않는다. 정확히 0인 기체 구동량만 흡수 capacity 0으로 유지한다.

공통 `LatticeBoundary`에 `dissociative_surface_reaction`을 추가했다. 평판과 유한 원통 계산기는 `J_abs(1-theta_surface)-J_des theta_surface`를 인접 반 셀 확산저항과 대수적으로 결합하고 기존 signed 교환·atom-mol 재고 계약을 유지한다. IUPAC fugacity 정의는 서지로만 기록했고 외부 문장·표·계수는 포함하지 않았다. `validation/hydrogen_surface_reaction_math.json`은 합성 Arrhenius/제곱근 fugacity 항등식, 평판 초기 flux, 원통 곡면적 적분 flow와 질량보존을 검사한다. 이는 bulk solubility, Langmuir 피복률, 상세 surface microkinetics, CoolProp fugacity, 실제 표면계수 보정이나 독립 실험 검증이 아니다. 현재 100개 계산기·39개 인터페이스·257개 능력 항목·56개 공개 스키마이며 전체 706개 검사가 통과한다.

## 2026년 10월 27일 수소 열활성화 속도 보정·식별성

`transport.hydrogen_thermal_rate_fit`과 공개 `HydrogenThermalRateFit` 계약을 추가했다. 관측·source group·calibration/holdout·trap/material/lattice/energy-reference ID를 보존하고, calibration 행만 이용해 Arrhenius 또는 고정 transmission coefficient 전이상태 속도식을 로그 공간에서 가중 적합한다. 최소 세 온도와 호출자 지정 온도 span을 요구하며 holdout 외삽을 검증으로 허용하지 않는다. 선택적 log-frequency 표준불확실성 또는 calibration 잔차로 조건부 모수 공분산·표준불확실성을 계산한다. Rate-only 전이상태식에서 transmission coefficient와 entropy가 구조적으로 분리되지 않으므로 coefficient를 고정 입력으로 요구한다.

NumPy 공식 least-squares 문서를 수치 API 근거로 기록했다. 독립 가중 직선식 대비 Arrhenius log-prefactor 오차는 `3.55e-15`, 활성화에너지 오차는 `7.28e-12 J/mol`이고, 합성 전이상태 모수와 holdout 제외 및 기존 thermal-rate 공급자 조합도 검사했다. 재현은 `scripts/validate_hydrogen_thermal_rate_fit.py`, 기록은 `validation/hydrogen_thermal_rate_fit_math.json`이다. 실제 TDS/투과 원신호에서 rate를 식별하거나 model-form/source-group/transport 불확실성을 포함한 결과가 아니다. 현재 99개 계산기·39개 인터페이스·256개 능력 항목·53개 공개 스키마이며 전체 687개 검사가 통과한다.

## 2026년 10월 27일 수소 수송–검출 관측 브리지

`transport.hydrogen_detector_observation`과 공개 `HydrogenDetectorObservation` 계약을 추가했다. 검토된 named surface의 signed outward 수소 원자 mol/s를 전자수·전류효율·부호·배경전류가 명시된 이상 전기화학 전류 또는 시편 질량·수소 원자 몰질량이 명시된 TDS ppm/s로 정방향 변환한다. `hydrogen_observation_inputs_from_transport_result`는 평판 flux에 검토된 실제 면적을 곱하고, 유한 원통의 이미 적분된 곡면·끝단 flow는 추가 면적 없이 연결한다. 원 결과 digest, 재료·시편·시계·표면·보정 ID와 음수 신호를 보존한다.

BIPM의 SI 정의 상수 페이지를 서지 기준으로 기록했으며 문장·표를 복제하지 않았다. 합성 Faraday 항등식, 질량기준 항등식과 평판 어댑터의 절대 오차는 모두 0이다. 재현은 `scripts/validate_hydrogen_detector_observation.py`, 기록은 `validation/hydrogen_detector_observation_math.json`이다. 실제 detector calibration, 지연·배관/진공계·pumping·재결합·흡착·잡음·불확실성이나 신호→경계 역산은 구현하지 않았다. 현재 98개 계산기·39개 인터페이스·255개 능력 항목·52개 공개 스키마이며 전체 670개 검사가 통과한다.

## 2026년 10월 27일 수소 트랩 열활성화 속도 공급자

`transport.hydrogen_trap_thermal_rates`와 공개 `ThermallyActivatedFrequency`·`HydrogenTrapThermalRates` 계약을 추가했다. Capture와 release가 각각 절대 Arrhenius 또는 Eyring 전이상태 표현을 선택하며 trap·재료·격자·에너지 기준·시계·온도 지원과 파라미터 근거를 보존한다. 계산은 log 빈도에서 수행하고 양의 부동소수점 범위를 벗어나면 0·무한대·비가역 트랩으로 치환하지 않는다. 결과는 두 속도 이력과 파라미터 digest, `-RT ln(release/capture)` 진단 및 `HydrogenKineticTrap`에 합성 가능한 독립 속도 필드를 제공한다.

Eyring 원 논문은 DOI 서지 참조만 기록하고 원문·표·그림·계수를 포함하지 않았다. 합성 Arrhenius·전이상태 항등식과 지원/검토 중지, JSON 조각 계약, 평판 수송과 독립 DOP853 반응해의 조합을 검사했다. 재현은 `scripts/validate_hydrogen_thermal_rates.py`, 기록은 `validation/hydrogen_thermal_rates_math.json`이다. CoolProp은 유체 상태 공급자이므로 이 활성화 속도 계산에 사용하지 않는다. 현재 97개 계산기·38개 인터페이스·253개 능력 항목·51개 공개 스키마이며 전체 658개 검사가 통과한다.

## 2026년 10월 27일 수소 트랩 독립 포획·방출 속도

`HydrogenKineticTrap`에 `binding_energy_ratio`와 `independent_frequencies` 속도 모드를 추가했다. 기존 모드는 검토된 `release/capture=exp[-E/(RT)]` 비를 유지한다. 독립 모드는 공통 시간 knot의 capture/release 빈도, 별도 근거와 검토 플래그를 요구하며 결합에너지나 온도로 값을 다시 계산하지 않는다. 모드에 맞지 않는 방출 이력, 누락·길이 불일치와 미검토 입력을 거절하고 결과에 속도 모드·이력 digest를 보존한다. 이 변경은 평판과 유한 원통이 같은 국소 반응식을 사용하도록 공통 보간 함수를 둔다.

닫힌 균일계에서 capture=release인 해석식, 300→900 K와 큰 결합에너지에 대한 독립 모드 불변성, capture 0/release 양수 경로, 질량보존과 두 형상 일치를 검사했다. 재현 스크립트는 `scripts/validate_hydrogen_independent_rates.py`, 결과는 `validation/hydrogen_independent_rates_math.json`이다. 이는 유효 입력 속도의 계산 계약이며 Arrhenius prefactor·활성화 엔트로피의 물리 공급자나 실험 보정을 대신하지 않는다. 전체 644개 검사가 통과한다.

## 2026년 10월 27일 수소 선형 표면전달 경계

공통 `LatticeBoundary`에 `linear_surface_transfer`를 추가했다. 사용자가 근거 있는 평형 격자
농도와 양의 전달계수(m/s)를 시간 이력으로 제공하면 표면저항과 반 셀 확산저항을 직렬 결합한다.
평판은 면적당 flux, 유한 원통은 곡면·양 끝단의 총 flow와 누적 mol을 기존 질량보존 경로에
포함한다. 두 이력의 누락·길이 불일치를 거절하고 음의 방출을 자르지 않는다. 별도 산술 검증은
직렬저항 항등식과 재고–표면교환 일치를 확인한다. 이는 진공·압력·전류에서 계수를 추정하거나
비선형 흡착·재결합, TDS 검출기 응답을 보정한 결과가 아니다. 전체 637개 검사가 통과한다.

## 2026년 10월 27일 반경–축 유한 원통 수소 수송

`transport.hydrogen_finite_cylinder_kinetic`과 공개 `HydrogenFiniteCylinder` 계약을 추가했다. 환형
셀 체적과 반경 면, 양 끝단 면을 보존하고 곡면·하단·상단의 농도/무유량 경계와 inward mol/s,
누적 mol을 분리한다. 고정 단일 점유 trap은 평판과 같은 검토된 상세평형 속도비를 사용하며
sparse bounded Newton과 보존적 step doubling으로 푼다. Bessel 체적평균·반경 격자 세분화,
축방향 선형 정상해·끝단 유량, 폐쇄 반응·질량보존 및 계약 중지를 검사했다. 공개 TDS 치수와
형상은 연결 가능하지만 곡선별 시편, 초기 분포, 표면 방출, clock·검출기 조건이 없어 실제
적합이나 검증으로 표시하지 않는다. 현재 96계산기·38인터페이스·252개 능력 항목·49개 공개
스키마다. 전체 632개 검사가 통과한다.

## 2026년 10월 27일 수소 투과·열탈착 신호 변환 계약

공개 `HydrogenPermeationSignalCalibration`과 `HydrogenTdsSignalCalibration` 계약 및 두 변환기를
추가했다. 투과는 export 해시·원/처리 전류·시계·원점·막 면적·부호·전자수·전류효율을 모두
고정한 경우에만 signed 수소 원자 mol 플럭스와 누적량을 만든다. TDS는 정확한 series,
수소 질량 ppm 기준과 검출기 검토가 있으면 mol/(kg-sample·s)로 변환하며, 검토된 시편 질량이
있을 때만 전체 mol/s도 만든다. 음수 신호와 원 온도
순서를 보존하고, 투과 전류에서 경계농도를 만들거나 TDS 온도에서 시계를 만들지 않는다.
작성한 Faraday·질량 ppm 항등식과 해시·채널·시계·series·검토 중지를 검사했다. 실제 장치 보정,
시험 형상, 수송·트랩 모수 적합 또는 독립 실험 검증은 아니다. 현재 95계산기·38인터페이스·
251개 능력 항목이며 전체 616개 검사가 통과한다.

## 2026년 10월 27일 구간별 상수 유한상태 동적 신뢰성

`reliability.piecewise_continuous_time_markov_chain`과 공개
`PiecewiseContinuousTimeMarkovChain` 스키마를 추가했다. 연속된 운전 구간별 생성행렬을 공급된
순서대로 전파하고, 경계별 상태점유·최초진입확률과 구간별·누적 기대 점유시간·전이횟수를
분리한다. 구간 ID·경계·전이율 근거·공급자 리비전·원본 해시를 보존하며 공백·중첩·역순·
미검토 구간을 중지한다. 동일 생성행렬 분할이 단일구간 계산과 일치하고 비가환 생성행렬에서
순서가 실제 결과를 바꾸는지 검사했다. 상태확률 정규화 허용오차와 초당 생성행렬 행합
허용오차도 단위별 필드로 분리했다. 이는 실제 운전조건별 전이율 보정이나 연속 시간가변·노화·
semi-Markov 모델 검증이 아니다. 현재 95계산기·37인터페이스·250개 능력 항목이며 전체 602개
검사가 통과한다.

## 2026년 10월 27일 유한상태 동적 신뢰성

`reliability.continuous_time_markov_chain`과 공개 `ContinuousTimeMarkovChain` 스키마를
추가했다. 사용자 공급 시간 불변 생성행렬의 종료 상태 점유, 기대 상태 점유시간과 기대
전이횟수를 계산하고, 상위사건 상태를 흡수시킨 복사본에서 기간 최초진입확률을 별도로 구한다.
두 상태 고장·수리 폐형식, 수리율 0 한계, 생성행렬·초기확률·검토 상태·context 및 사건 전달
의미를 검사했다. 실제 전이율 보정, 노화·시간가변·semi-Markov 전이와 불확실성 검증은 아니다.
현재 94계산기·37인터페이스·249개 능력 항목이며 전체 585개 검사가 통과한다.

## 2026년 10월 27일 공동 사건분포와 상위사건 확률

`reliability.joint_event_probability`와 공개 `JointEventDistribution` 스키마를 추가했다. 같은
자산·부위·물리 범위·기간·생존조건의 최대 12개 이진 사건에 대해 빠짐없는 `2^n` 상태표와
상위사건 진리값을 받는다. 상위사건 확률, 주변·쌍별 동시확률, 공분산·phi와 같은 주변분포를
독립으로 가정한 비교값을 계산한다. 누락·중복·정규화 오류, 미검토 분포, context·기간 불일치와
퇴화 주변분포를 검사한다. 작성된 정확 분포의 산술 검증일 뿐 실제 공통원인율·인과성·고차
의존성·동적 수리모델의 보정은 아니다. 현재 93계산기·37인터페이스·248개 능력 항목이며 전체
570개 검사가 통과한다.

## 2026년 10월 27일 CoolProp 캐비테이션 열역학 선별

`degradation.cavitation_margin`, `degradation.cavitation_history`와 두 CoolProp 입력 조합기를
추가했다. 절대 국부 정압,
평형 증기압, 액체 밀도와 호출자 정의 특성속도로 정압·정수두 여유, 동압과 국부 캐비테이션
수를 계산한다. CoolProp backend·판본·리비전과 포화액 상태 digest를 보존하고 게이지압,
미검토 압력/상태와 0 속도를 거절한다. 이 하위 기능은 기포핵·inception·붕괴·침식률·재료
손상·수명·합격을 추정하지 않는다. 300 K 물 상태와 독립 대수식을 검사했으며 실제 장치와
재료 실험 검증은 남아 있다. 이력 계산은 선형 교차 구간·지속시간과 clipped pressure-deficit을
계산하고 무효 표본을 거절한다. `OperatingHistory`에서 검토된 국부 정압·특성속도 이력으로
변환하는 어댑터와 공개 `CavitationHistory` 스키마도 제공한다. 현재
92계산기·37인터페이스·247개 능력 항목이며 전체 558개 검사가 통과한다.

## 2026년 10월 27일 국부 tensor 이력 교환 계약

`matintegrity.local_tensor_history.v1`과 임계면 입력 어댑터를 추가했다. 자산·재료·부위·하중
identity와 함께 공급자/solver 판본, solution revision, mesh와 field location, 공간 평균,
표본 시계, 오른손 직교 좌표 기저, stress/strain measure, shear convention, 원본과 설정 digest를
보존한다. 무효 표본·미검토 field·지원하지 않는 measure·context 불일치를 중지하고 engineering
shear만 명시적으로 tensor shear로 변환한다. 합성 정삼각형 경로의 chord/최소포위 원 조합과
엄격한 JSON 왕복을 검사했다. 현재 90계산기·36인터페이스·244개 능력 항목이며 전체 539개
검사가 통과한다. 실제 FE 공급자, mesh/time 수렴, 노치근 장과 실험 피로수명 검증은 남아 있다.

## 2026년 10월 27일 임계면 minimum-enclosing-circle 경로 진폭

`fatigue.critical_plane_minimum_enclosing_circle_factors`를 추가했다. 각 선언 평면에서 두 성분
engineering shear 표본을 모두 포함하는 최소 원의 반지름을 FS 전단 진폭으로 사용한다. 원을
결정하는 최대 3개 support 표본 ID와 면내 좌표계 중심을 보존하고, 기존 최대 chord 절반과 그
비를 별도로 보고한다. 두 range 정의를 같은 것으로 취급하지 않으며 SWT 법선항은 변경하지 않는다.

8개 전용 검사와 별도 기하 검증에서 정삼각형의 원/chord 비, 직선 한계, 불규칙 점군의 exhaustive
1·2·3점 후보 해, 면내 축 회전·반전과 점 순서·이동·스케일 불변성을 확인했다. 현재
90계산기·35인터페이스·243개 능력 항목이며 전체 527개 검사가 통과한다. 이 계산은 유한
점군 range이며 continuous-time extremum, cycle counting, 방향 수렴, 피로수명 보정이나 독립
실험 검증이 아니다.

## 2026년 10월 27일 임계면 적응형 국소 방향 탐색

`fatigue.critical_plane_adaptive_search`를 추가했다. 하나의 유한 위도형 또는 Fibonacci 격자에서
FS와 SWT seed를 각각 선택하고, 각 목적함수를 중심 유지 tangent ring과 축소 반경으로 독립
탐색한다. 단계별 반경·후보 수·계수 변화·방향 없는 법선 이동을 모두 보존한다. 중심 후보를
계속 포함해 표본 목적값은 감소하지 않지만, seed와 탐색 일정에 의존하는 탐욕적 국소 검색이므로
전역 연속 최적이나 수렴 증명으로 표시하지 않는다.

8개 전용 계약 검사와 기울어진 단축 폐형식 검증을 추가했다. 16개 Fibonacci seed에서 6단계,
각 24점 ring을 적용해 SWT 계수·법선 및 FS 계수를 독립 연속 해에 대조했고 결정적 추적과 잘못된
탐색 일정을 검사했다. 현재 89계산기·35인터페이스·242개 능력 항목이며 전체 518개 검사가
통과한다. 수학·소프트웨어 검증과 피로수명 보정·독립 실험 검증은 계속 분리한다.

## 2026년 10월 27일 임계면 격자 계열·phase 교차 비교

`fatigue.critical_plane_grid_family_comparison`을 추가했다. 같은 tensor history에 둘 이상의
위도형/Fibonacci 격자를 적용하고 사용자가 명시한 한 유한 기준 격자에 대한 FS/SWT 상대
변화와 지배 법선 회전을 기록한다. 생성기 정의를 그대로 보존해 Fibonacci 후보 수와 phase를
재현하며 중복 격자 ID와 누락 기준 ID를 거절한다.

6개 전용 계약 검사와 단축 해석 검증에서 241개 위도형 기준 및 phase가 다른 128개 Fibonacci
격자 둘을 비교했다. 상대 변화 보고 오차는 0이었지만 FS 지배 법선은 기준에서 약 0.30 및
0.97 rad 이동해 엄격한 0.1%·1° 선언 기준은 의도대로 미충족이었다. 검증 통과와 사용자 기준
충족을 분리한다. 현재 88계산기·35인터페이스·241개 능력 항목이며 전체 509개 검사가 통과한다.

## 2026년 10월 27일 임계면 시간 표본 세분화 진단

`fatigue.critical_plane_time_refinement`를 추가했다. 동일 tensor source·주기 구간·유한 평면
집합을 유지하면서 표본 수가 증가하는 중첩 시간 이력을 비교한다. 각 단계의 최소·최대 시간
간격, FS/SWT 최대값과 지배 법선, 직전 단계 대비 상대 변화·법선 이동을 보존한다. 시간축
비증가, 표본/텐서 불일치, 주기 구간 불일치, 비중첩 시각과 표본 수 비증가를 거절한다.

8개 전용 계약 검사와 별도 수학 검증에서 위상 이동 sine 주기의 5·9·17·33개 표본을 고정된
두 평면에 적용했다. 각 이산 결과를 독립식과 대조하고 이 예제의 연속 한계 오차 감소를
확인했다. 이는 일반 파형의 표본 사이 오차 상한이나 수렴 증명이 아니다. 현재
87계산기·35인터페이스·240개 능력 항목이며 전체 502개 검사가 통과한다.

## 2026년 10월 27일 면적 층화 Fibonacci 평면 후보

`fatigue.area_uniform_fibonacci_plane_grid`를 추가했다. 방향 없는 평면을 양의 `z` 반구 안에서
한 번씩 표현하고, 동일 면적 `z` 층의 중점과 golden-angle 방위에 후보를 배치한다. 사용자가
후보 수와 방위 phase를 정하며, 각 후보에는 하위 임계면 API가 그대로 받는 결정적 프레임과
반구 적분용 동일 명목 가중치를 제공한다.

7개 계약 검사와 별도 수학 검증에서 후보 수, `z` 중점, golden angle, 단위·직교 프레임,
부호 중복 부재, 명목 가중치 합과 `z`/`z²` midpoint 적분을 확인했다. 명목 가중치는 실제
Voronoi cell 면적이 아니며 covering radius·nested refinement·연속 최적점을 증명하지 않는다.
현재 86계산기·35인터페이스·239개 능력 항목이며 전체 493개 검사가 통과한다.

## 2026년 10월 27일 임계면 격자 세분화 진단

`fatigue.critical_plane_grid_refinement`를 추가했다. 동일한 검토 완료 tensor cycle을 사용자가
선언한 두 단계 이상의 격자에 적용하고, 각 단계의 후보 수·최대 FS/SWT·지배 법선과 직전 단계
대비 상대 계수 변화·방향 없는 평면 회전을 보존한다. 두 분할 수가 감소하거나 후보 수가 늘지
않는 순서는 거절한다. 열린 주기는 `needs_data`로 중지하며 안정성 판단을 만들지 않는다.

해석적 지배 방향이 포함된 단축 이력을 13·57·241 후보 중첩 격자에서 대조하는 검증 스크립트와
6개 계약 검사를 추가했다. 선언 허용값은 사용자 진단 기준일 뿐 미표본 방향 오차 상한이나
연속 평면·시간 수렴 증명이 아니다. 현재 85계산기·35인터페이스·238개 능력 항목이며 전체
485개 검사가 통과한다.

## 2026년 10월 27일 임계면 반구 격자 공급자

`fatigue.hemisphere_plane_grid`를 추가했다. 방향 없는 평면의 `n/-n` 대칭을 사용해 상반구를
위도·방위로 이산화하고, 극점 한 개와 적도 절반만 남겨 정확한 부호 중복을 제거한다. 각
후보에는 안정된 ID와 최소 정렬 Cartesian 축에서 만든 결정적 면내 단위방향을 제공한다.
각도 메타데이터는 downstream 엄격 계약을 깨지 않도록 후보 객체와 분리했다.

폐형식 후보 수, 모든 프레임의 단위길이·직교성, 중복 부재, 결정성과 임계면 벡터 경로로의
무변환 연결을 검사했다. 이 격자는 equal-area가 아니며 각도 간격은 covering error bound가
아니다. 명시적 세분화 비교 전 수렴된 연속 임계면으로 부르지 않는다. 현재
84계산기·35인터페이스·237개 능력 항목이며 최종 검사 수는 `validation/summary.json`에서
갱신한다.

## 2026년 10월 27일 면내 전단벡터 경로

기존 한 방향 성분 계산을 보존하면서 `fatigue.critical_plane_vector_path_factors`를 추가했다.
평면 법선과 선언한 면내 방향에서 직교 보완 방향을 만들고, 두 engineering shear 성분의 모든
표본쌍 Euclidean 거리를 비교한다. 최대 chord 절반, 지배 sample ID 쌍, 동일 방식의 전단응력
chord를 보존한다. Euclidean 거리는 면내 기준축의 회전·반전에 불변이지만 계산량은 표본 수의
제곱에 비례한다.

비스듬한 직선 전단경로에서 한 성분 모델이 `r/sqrt(2)`를 내는 반면 벡터 경로가 `r`을
회복하고, 기준축을 회전·반전해도 결과가 같음을 독립 폐형식으로 검사했다. 이산 표본 chord는
minimum-enclosing-circle·연속시간 극값·rainflow가 아니며, 평면 집합도 사용자 공급 유한
후보다. 수명·보정·독립 실험 검증으로 표시하지 않는다. 현재 83계산기·35인터페이스·236개
능력 항목이며 최종 검사 수는 `validation/summary.json`에서 갱신한다.

## 2026년 10월 26일 이산 임계면 피로 계수

`fatigue.critical_plane_factors`를 추가했다. 외부에서 검토한 대칭 Cauchy stress·small-strain
tensor 한 주기와 사용자가 선언한 직교 plane/direction 후보를 받아 법선·전단 성분을 독립
투영한다. Tensor shear strain을 engineering shear로 두 배 변환하고 후보별 FS·SWT 계수 및
서로 독립적인 최대 후보 ID를 반환한다. 재료/위치/history/tensor source와 sample ID, 텐서
Frobenius 폐합 오차를 보존한다. 열린 주기에는 계수를 계산하지 않는다.

Fatemi–Socie 1988 원 논문과 Smith–Watson–Topper 1970 원 논문은 서지·계수 정의 확인에만
사용했고 문장·그림·표·코드·데이터는 포함하지 않았다. 단축·45도·순수 전단의 독립 폐형식
검증과 계약 검사를 추가했다. 이 구현은 유한 후보의 한 방향 전단 성분 계산이며 연속 평면
탐색, 회전 전단 경로 알고리즘, 노치 해석, 보정, 수명이나 합격 판정이 아니다. ECP 공개자료의
provider factor는 국부 tensor가 없으므로 새 구현의 독립 정답으로 사용하지 않았다. 현재
82계산기·35인터페이스·235개 능력 항목이다. 최종 검사 수와 배포 감사는 현재
`validation/summary.json` 및 package audit를 기준으로 한다.

## 2026년 10월 26일 ECP 다축·비비례 피로 공개자료

Zenodo 14198237의 CC BY 4.0 선언을 API로 확인하고 28개 text 파일 9,032바이트를 제공자
MD5와 대조해 취득했다. 14개 조건에는 원 `ASS`·`TOR`·`MULTI` load code, blunt/sharp,
stress ratio -1·0.1·0.5와 조합 하중의 위상 0°·45°·90°가 있다. FS와 SWT 파일은 같은
실험수명을 같은 행 순서로 반복하므로 294행을 294개 시편으로 세지 않는다.

`read_ecp_multiaxial_fatigue`는 147개 실험 관측과 FS/SWT 각 147개의 처리 factor·provider
prediction을 분리한다. Pair 누락, 행 수·실험수명 불일치, filename schema와 값 범위를
검사하는 전용 검사 10개와 고정 집계 JSON을 추가했다. 실제 시편 ID·검열·끝점 정의·국부
tensor history·FE mesh가 파일에 없으므로 추론하지 않고, 같은 연구의 provider prediction을
독립 검증으로 표시하지 않는다.
전체 450개 검사가 통과했다. 현재 81계산기·35인터페이스·234개 능력 카탈로그 항목이며
추가 118과제는 35개 일부 구현·83개 계획이다.

## 2026년 10월 26일 내압 피로시험 종료 사건 계약

`fatigue.pressure_loss_endpoint`를 추가했다. 검토된 loading segment의 물리 시편 ID,
하중 case ID, 유효 cycle과 계수 근거를 보존하고 한 시편의 연속 이력만 합산한다. 선언
임계 압력 저하만으로 파손을 만들지 않고 확인된 관통균열/파열, 압력계통·계측 중단,
우측 검열 runout, 진행 중과 불명확 결과를 분리한다. 시편·하중 case 불일치, 중복 segment,
초기압보다 큰 압력 저하와 사건 출처에 맞지 않는 확인 표식은 거절한다.

합성된 확인 파손·설비 중단·runout·미확정 사건을 독립 기대값과 대조하는
`validation/fatigue_endpoint_contract.json`과 전용 검사 12개를 추가했다. 이 검사는 사건
분류와 검열 계약만 확인하며 피로강도·수명·압력 임계값 또는 고장확률을 보정하지 않는다.
전체 440개 검사가 통과했다. 현재 81계산기·34인터페이스이며 추가 118과제는 35개 일부
구현·83개 계획이다.

## 2026년 10월 26일 FABEST HCF blind 하중상태 모듈

CC BY 4.0의 FABEST HCF Competition package v2.1.2를 고정 Zenodo record에서 취득했다. ZIP 46,329,584바이트의 SHA-256과 제공자 MD5를 대조하고 36개 member, 실제 파일 15개, 암호화·상위경로 이탈 0개를 확인했다. Blind matrix는 Plain/Notched 각 10행, 위상 0°/90° 각 10행, 목표 반복수 5수준 각 4행이다. 제출 template의 20개 case ID는 같은 순서이고 결과 열은 모두 비어 있다. 따라서 이 자료를 피로강도나 수명모델의 독립 결과 검증으로 사용하지 않는다.

`fatigue.pressurized_annulus_load_state`를 추가했다. 식별된 환형단면에 대해 축력과 토크의 평균·진폭을 명목 응력으로 바꾸고, 선언한 벽 반경에서 내·외압의 Lamé 응력을 계산한다. 폐쇄단 압력 축응력을 평균성분으로 분리하고 외부 축력 기준 진폭과 섞지 않는다. 노치근, 임계면, 비비례 추가경화, 피로강도·수명·합격판정은 범위 밖이다. 독립 환형단면 식과 압력 경계를 대조한 검증 JSON, 고정 package 감사 JSON, 9개 전용 검사를 추가했다.

전체 427개 검사가 통과했다. 현재 80계산기·34인터페이스이며 추가 118과제는 35개 일부 구현·83개 계획이다. 실제 종료 이벤트 계약, 국부 노치 응력, 임계면 다축 기준, 공개 결과를 이용한 보정·독립 검증은 후속 과제다.

## 2026년 10월 26일 FABEST 종료·시편 표식 감사

FABEST workbook의 내장 데이터 사전과 60개 고주기 곡선 sheet를 매크로 없이 대조했다. 데이터 사전은 `finished/interrupted`, cycles till END, 별도 cycles till break와 곡선별 END 기준을 구분하지만 실제 곡선 sheet에는 END/END_PAR가 없다. 관측 663행은 break cycle 보고 567행, provider interruption 95행, 종료 미확정 1행이다. 95개 interruption 가운데 15개는 별도 주석이 있고 나사부·그립부 등 목표부 밖 손상 가능성이 있어 전체를 runout으로 재명명하지 않았다.

기존 `possible_retest_label`은 근거가 강한 이름이어서 제거했다. 문자 접미사 54행은 `letter_suffix_semantics_unresolved`로 보존하며 물리 시편 관계를 만들지 않는다. 자유문 89행에는 온도 문자열 8, 나사부 표식 13, 그립부 fretting 1, 제외 2, 실수 1, buckling 의문 3 등을 검토 태그로만 추가했다. Break cycle과 no-crack 계열 주석이 함께 있는 18행도 양쪽 원 필드를 유지한다. `calibration_role`은 깨끗한 행도 candidate로만 분류하고, 기존 FAB005 시범 적합은 선택 범위에서 provider interruption을 우측 검열로 보는 명시적 가정으로 제한했다. `scripts/inspect_fabest_data.py`가 고정 SHA-256·구조·집계를 검사하며 실제 종료 기준·재시험·self-heating·시험 유효성을 대신 판정하지 않는다.

새 자유문·종료 계약 검사를 포함해 전체 417개 검사가 통과했다. 계산기 79개·교환/확장 인터페이스 34개 수는 바뀌지 않았다.

## 2026년 10월 26일 전이구간 파괴인성 편집 자료

Meshii 외 저자의 CC BY 4.0 공개 ZIP 2,666,905바이트를 추가했다. Workbook에는 provider training 448행과 test 192행이 있으며 총 640행, 14재료, CT 394·SEB 165·PCCv 81행이다. 보고 KJc 36.1~255.4 MPa√m와 항복강도 348.8~990.1 MPa를 확인했다. 전체 취득은 20묶음·69파일·3,077,405,770바이트가 됐다.

`read_fracture_toughness_temperature`를 추가해 partition·source sheet/row·재료·탄소·항복강도·specimen type·W/B/a·KJc를 보존한다. 원 온도 열은 `K`로 적혔지만 음수를 포함한다. 후속 1차 논문 검토에서 machine-learning의 시험 온도 특징과 재료별 범위가 °C로 명시된 것을 확인해 workbook 충돌을 기록하고 기본 K 변환을 추가했다. W/B/a에는 workbook 단위 표기가 없지만 논문이 치수와 T 크기를 mm로 정의하고 전 행의 B 4.07~101.6이 일치함을 확인해 기본 `article_mm` SI 변환을 추가했다. 원 표기 부재를 보존하고 검토 비활성화·명시적 override 경로를 유지한다. 재료·시편형식·W/B를 상대 3%·절대 0.1 mm 허용오차로 묶은 34개 형상 조건 그룹이 모두 training/test에 함께 나타남을 확인했다. 그룹은 누설 점검용이며 물리 시편 독립성 표식은 명시적으로 false다. 논문 표의 재료/참고문헌 그룹을 독립 대조해 정확 614행, `S55CFY2012`→`S55C` 유력 변형 18행, 대응 없는 `SS400` 8행을 구분했다. 참고문헌 9개 중 DOI 7개를 확인했고 실제 행은 DOI 그룹 176·서지만 확인 456·출처 그룹 미해결 8행이다. Crossref의 출판물 라이선스/TDM 정보와 편집 관측의 권리를 분리해 관측 권리는 640행 모두 미확정으로 유지했다. Article-local 그룹은 행별 원 문헌 ID가 아니므로 `underlying_literature_id`는 계속 비워 둔다. 행 번호나 조건 그룹을 물리 시편 ID로 만들거나 reported KJc를 시험 유효성·서비스 하한·FAD 파괴저항으로 승격하지 않는다.

새 reader 전용 검사 11개를 포함해 전체 416개 검사가 통과했다. 현재 79계산기·34인터페이스·41공개 Schema, 추가 118과제는 34개 일부 구현·84개 계획이다. 다음은 원 문헌별 행·시편/유효성 및 관측 권리 연결, constraint·검열 검토, tearing 자료와 자격 있는 K/reference-stress 공급자 및 독립 부품 파괴 비교다.

## 2026년 10월 26일 사용자 FAD 경계와 crack-arrest 원자료

`structural.failure_assessment_points`를 추가했다. 각 평가점의 material/location/load case와 K geometry·reference stress·toughness source ID를 유지하고 `Kr=K/Kmat`, `Lr=sigma_ref/sigma_norm`을 사용자가 공급한 비증가 구간선형 경계 안에서만 평가한다. 곡선 근거에 license/entitlement를 요구하며 마지막 Lr 밖을 외삽하지 않는다. 규격 곡선·cutoff·안전계수·잔류응력 조합·허용표는 내장하지 않는다.

Puyi Gao의 CC BY 4.0 C1/C2 crack-arrest raw ZIP 943,565바이트를 추가해 전체 19묶음·68파일·3,074,738,865바이트가 됐다. C1 9·C2 9파일의 79,341행에서 원 0.05초 시계와 signed displacement/force/extensometer/cycle을 보존했다. 힘 음수 76,285개와 양수 3,056개를 유지하고 한 파일의 정확한 전체-header 인용 결함만 복구한다. 시편 기하·동적 reduction·유효성 근거가 없어 toughness 값이나 FAD 검증으로 만들지 않았다.

FAD·자료 계약 전용 27개 검사와 등록 예제 확장을 포함해 전체 405개 검사가 통과했다. 49개 합성 Lr에서 독립 구간 보간과의 최대 차이는 약 1.67e-16이고 지원 밖 중지를 확인했다. 현재 79계산기·33인터페이스·41공개 Schema, 추가 118과제는 34개 일부 구현·84개 계획이다. 실제 initiation/tearing 자료, 자격 있는 K/reference-stress 공급자와 독립 cracked-component 검증은 후속 과제다.

## 2026년 10월 26일 과도 열전도와 두께방향 열응력

평판과 원통 반경 방향의 셀 중심 유한체적 열전도를 추가했다. 온도 의존 열전도율·체적 열용량, 엔탈피 저장, 지정 온도/부호 있는 열유속/단열/대류·회색복사 경계, 체적 발열과 분포 대류를 받는다. 후진 Euler의 비선형 반복과 자체 삼중대각 풀이를 사용하고 에너지 각 항·잔차·출력 시각을 보존한다. 별도 탄성 단면 모델은 일축 또는 등방 이축 평면응력과 합력/변형 제어, 온도별 E·열팽창·포아송비·탄성 한계를 받는다.

CC BY 4.0 공개 rod 자료 1묶음 2,099,328바이트를 추가해 전체 18묶음·67파일·3,073,795,300바이트가 됐다. 77개 CSV의 215,001 시간행·1,290,006 열전대 관측과 처리 workbook의 77개 적합 행을 구분했다. 음수 초과온도와 controller setting을 보존했다. `50ss1`의 0.6335 K RMSE는 같은 자료에 적합된 계수로 수행한 재현이며 독립 보류 검증으로 표시하지 않는다.

공간/시간 수렴, 열경계·발열·복사·원통 보존, 자유/구속 열응력·합력·범위 중지를 포함한 전용 검사 33개와 기존 공통 검사 확장을 반영해 전체 377개가 통과했다. 현재 78계산기·32인터페이스·38공개 Schema, 추가 118과제는 33개 일부 구현·85개 계획이다. 독립 열시험, 잠열·이력, 이동 열원, 다차원·접촉, 비선형 소성/크리프 및 압력·균열 결합은 후속 과제다.

## 2026년 10월 26일 실측 분극과 비선형 전류 평형

공개 분극 자료의 고정 리비전에 포함된 시험 방법 파일을 선택 취득하고 제공자 체크섬을 대조했다. 24곡선·19,680점은 증가 방향·원 행·부호를 보존하며, 공개 연구 6쪽의 전위 기준·온도·전해질·질소 처리·스캔 속도를 대조했다. 본문의 명목 끝 전위와 실제 워크시트 차이, 실제 면적·기준 전극 충전 용액·저항·준정상 전달의 미확정 조건을 남겼다. 취득 합계는 17묶음·66파일·3,071,695,972바이트다.

`corrosion.mixed_potential`과 네 가지 Python/JSON 계약을 추가했다. 양극 방향 양수 순전류를 실제 노출 면적으로 가중하고 공통 지원 구간에서 부호를 보존한 선형 보간의 모든 근을 조사한다. 다중 근·영전류 구간·접선/끝점·큰 전류 소거·조건 불일치를 별도로 드러내며 대표 결과를 임의 선택하지 않는다. 순전류를 금속 용출 부분 전류·부식 속도·안정성·기간 확률로 승격하지 않는다. 기존 선형 회로 계산도 유지한다.

새 전용 검사 30개와 등록 예제 1개를 포함해 342개 검사가 통과했다. 선형 회로와 독립 비선형 폐형식을 비교했고, 마지막 합성 격자의 전위 절대 오차는 약 1.8e-9 V, 전극 전류 최대 절대 오차는 약 4.3e-10 A였다. 실제 곡선의 계약 왕복은 검사했지만 결합 실험의 독립 검증은 수행하지 않았다. 자료 감사는 `needs_data`를 유지한다. 외부 관측·논문 내용은 배포에 넣지 않고 집계·출처·해시·검토 기록만 공개한다.

현재 76계산기·31인터페이스·38공개 Schema, 추가 118과제는 32개 일부 구현·86개 계획이다. 매뉴얼·API·재개 지침·모니터링/위험성 확장 요청서를 갱신했다. 수치 검증·실제 보정·독립 검증·상대 저장소 통합의 상태는 계속 구분한다.

## 2026년 10월 26일 독립 입력 전역 민감도

미구현 목록의 전역 민감도를 독립 입력의 실제 Sobol 분석 경로로 확장했다. SciPy의 공개 추정기·QMC API와 SALib의 방법 범위를 비교하고 기존 SciPy 의존성의 paired-array 추정기를 사용했다. 자체 설계는 2d scrambled Sobol·native 단위 주변분포·A/B 혼합·중첩 prefix와 독립 scramble 반복을 보존한다. 개별 QMC 행을 iid로 bootstrap하지 않고 scramble 평균의 근사 t 구간과 표본 크기 차이를 함께 기록한다.

입력 설계·외부 평가 배치·응답/상태·최종 보고서의 버전 있는 JSON 계약을 분리했다. 입력 배치에도 native 단위·요청 digest·평가자 판본을 포함하며 선택 의존성이 없는 설치에서도 해당 계약을 읽도록 했다. 다른 순서의 응답은 점 ID로 정렬하고, 중복·다른 설계·누락/실패·비유한 출력·비재현 응답을 거절하거나 자료 부족으로 중지한다. 해시는 실제 실행이나 물리 타당성 인증이 아님을 명시했다. 레지스트리 편의 연결은 모델 판본과 scalar 입력/출력의 단위 변환을 대조한다. 합성 쿠폰 범위의 8,224점 예제를 실행했으며 그 범위를 실제 재료 불확실성으로 보정하지 않았다.

새 검사 31개를 포함해 전체 311개 검사가 통과했다. 가산/순수 상호작용/무관 변수의 해석값, affine 변환·극단 척도, 독립 모멘트로 구한 Ishigami 지수, 상수/미해상 분산, 순서 변경/해시/재현/예산과 쿠폰 산술을 확인했다. 비선형 benchmark의 주/총 효과 최대 절대 오차는 약 0.00100·0.00128이며 구간 포함률 보증이나 실험 검증으로 해석하지 않는다. 현재 75계산기·30인터페이스·34공개 Schema, 추가 118작업은 32개 일부 구현·86개 계획이다. 입력 상관·Shapley·잡음·실제 분포 보정과 상대 저장소의 실통합은 후속 과제다.

## 2026년 10월 26일 유한 평판 수소 수송

공개 2025년 수송 연구의 주파수 단위 포획·탈리와 빈 격자 site 인자를 대조했다. 고정 독립 단일 점유의 유한 평판 보존식·셀 평균 유한체적·반 셀 경계·backward Euler 소거식·bounded Newton 반복은 독립 작성했다. SciPy banded 선형계를 호출하고 FiPy의 공식 수치 문서를 다차원 확장 후보로 검토했다. 새 입력은 재료/격자/시계 ID, 초기 분포·공간적으로 균일한 변온·D/capture 이력·표면 농도/무유량 경계·지원 범위·근거를 받는다. 현재 release/capture 비율은 결합에너지 근사를 검토해야 한다.

시간 적응은 점유율과 양쪽 경계 통과량을 함께 비교한다. 상태가 정상이어도 변하는 D의 통과량 적분에 오차가 생기는 사례를 확인해 이를 별도 제어에 포함했다. 승인된 두 반 단계의 flux와 상태를 함께 보존하고, 질량/점유율/시간 예산 실패를 완료된 계산으로 내보내지 않는다. 외부 표면 전류·가스압에서 경계 농도를 만드는 자동 공급자는 추가하지 않았다.

새 검사 29개와 새 등록 예제 1개를 포함해 전체 280개가 통과했다. 닫힌 반응의 해석식·독립 두 트랩 ODE·빠른 속도의 기존 평형 한계·Fourier 셀 평균·경계 반사·변온 폐쇄 질량·일정 상태의 가변 유량을 대조했다. 먼 출력 시각과 빠른 초기 반응이 공존할 때 초기 단계와 시간 해상도를 현재 물리 시간척도에서 정하도록 보완했다. 수학 벤치마크에서 시간 간격 절반의 오차 감소 약 1.95~1.98배, 12→24셀의 오차 감소 약 3.78배를 기록했다. 국소 허용오차를 전역 오차 상한으로 주장하지 않는다. 현재 75계산기·29인터페이스·28공개 Schema이며 118개 추가 작업의 31개 일부 구현·87개 계획을 유지한다.

실제 공개 시험은 TDS 원통 형상과 질량 ppm을 명시하므로 평판 모델에 직접 적합하지 않았다. 투과막 치수·면적·전위 기준·시간 원점과 TiC의 선택 노출 표식 대응을 미확정으로 보존했다. source·외부 관측·그림·도구의 공개 경계를 유지하고 원자 규모 공급자 요청서·설명·재개 지침을 갱신했다. 원통·표면 반응·독립 release/capture·생성 trap·응력·다중 점유·파괴와 실험 보정은 후속 과제다.

## 2026년 10월 26일 수소 수치 내보내기 확인

공식 Origin Viewer의 서명과 파일 버전 10.4.0.25를 확인해 로컬 제외 도구로 사용했다. 투과 OPJU에서 고유 CSV 6개와 같은 내용의 별칭 2개를 확인했고 TDS의 원시 workbook 두 개와 원 노출 요약 시트를 추가로 내보냈다. 원본·CSV 해시·도구·worksheet 검토 상태를 연결하는 `TabularExportProvenance`와 네 로더를 추가했다. 명시적 단위 선언·이동 시계와 원 시계 분리·정확한 알려진 쉼표 복구·미기록과 미충전 구분·내보낸 바이트 대조를 검사한다. 원파일을 고치거나 내장 스크립트를 실행하지 않았다.

실제 투과 40,859행은 시계가 증가하며 처리 전류 음수 2,493행을 보존했다. BQ2 주석과 이동 시계에 1초 차이가 있었다. TDS 18곡선의 수치 98,983점은 온도 반복 17,328·역전 8,786구간과 음의 탈착률 869행을 포함한다. 한 기록의 끝에는 숫자가 없는 표식 411행이 있어 별도 집계했다. 원 적분 열과 제한 온도 요약을 독립 실험으로 중복 계산하지 않는다. 유효 D와 격자 D, ppm 기준·오차 통계량·시편 대응·형상·경계조건은 추가 검토 대상으로 남겼다.

새 합성 검사 22개를 포함해 전체 250개 검사가 통과했다. 현재 74계산기·28인터페이스·26공개 Schema이며 추가 118작업의 31개 일부 구현·87개 계획 상태는 유지한다. 이 단계는 수치 자료 연결과 소프트웨어 계약의 확인이다. 동역학 수송·열탈착·균열 모델 보정이나 독립 실험 검증을 완료했다고 표시하지 않는다. 재현 절차는 `HYDROGEN_EXPORTS_KO.md`, 배포·설치 증거는 `validation/`에 보존한다.

## 2026년 10월 26일 수소 분배와 자료 확장

가스 수소 문헌 편집 자료의 기본 파일 11개와 1차 탄화물 트랩 실험 ZIP 1개를 추가했다. 총 취득은 17묶음·65파일·3,063,203,536바이트다. 대형 선택 파일은 명시적 데이터 ID와 `--include-optional`로만 취득하고 파일별 용량·권리 정책을 유지하도록 수집기를 확장했다. 모의 검사로 metadata-only 정책을 우회하지 않음을 확인했다. 전체 2.64 GB ZIP의 제공자 MD5와 SHA-256을 기록했다.

편집본 113행은 9출처·31조성에 연결되지만 성분 불일치 15행, 단위 미확정 4행, 열 번호 미보고 97행을 확인했다. 성분 두 스냅샷·미보고 원소·파생값의 0 가정을 분리하고 동일 조건/값을 자동 독립 또는 중복 시편으로 확정하지 않았다. 원 문헌 권리 검토 전 원본·점별 파생 관측은 배포에서 제외한다. 1차 실험의 투과/TDS는 OPJU이며 DFT workbook을 실험곡선으로 오인하지 않았다.

전체 site 점유 관계를 사용하는 다중 population의 국소 수소 평형과 농도 의존 미분 저장/확산계수를 구현했다. 로그 질량·빈자리 근과 미분을 사용하고 단위는 mol의 수소 원자로 고정했다. 국소 평형의 수학 검사와 실제 동역학·균열 실험 자격을 구분했다. 이 단계 당시 74개 계산기·27개 인터페이스·25개 공개 Schema·228개 검사였으며 추가 확장 118개 중 31개 일부 구현·87개 계획을 유지했다. 당시 남았던 OPJU 수치 내보내기는 위 후속 기록에서 진행했다. 동역학 수송·원자 에너지/밀도 공급자·독립 실험 검증은 후속 과제다.

## 2026년 10월 26일 크리프 확장

BAM CMSX-6의 CC BY 4.0 자료에서 13파일을 추가해 누적 취득량이 15묶음·53파일·418,313,273바이트가 됐다. workbook 종료 조건으로 파단 9개와 시간 한도 미파단 3개를 확인했다. 처리 LIS 140,032행은 파일-local h·%·°C를 SI로 읽고 중복 시각 23구간을 원 순서대로 보존한다. 파형의 끝을 수명으로 삼거나 표본 수를 시편 수로 늘리지 않았다.

단일 온도 응력 수명과 식별 가능한 다중 온도 응력·Arrhenius 수명을 같은 검열 우도 계약으로 구현했다. 독립 파단·미파단 우도, 세 초기점·해석적 gradient·관측 정보행렬·원 조건 hull·시간 외삽 선언을 추가했다. 조건부 확률은 일정 조건과 fresh-material 시계를 확인한 경우에만 제공한다. 엄격한 JSON 모델 계약을 Python 객체로 읽는 예제와 기간 사건 시계 검사도 포함했다.

실제 시범 보정은 응력 수준별 한 시편을 ID 해시로 보류하는 8/4 분할이다. 보류 파단 3개의 로그 수명 RMSE는 약 0.02694이며 외부 검증으로 해석하지 않는다. Q는 미추정 상태이고 다중 온도 계수 회복은 합성 검사로만 확인했다. 코드 검사는 213개, 계산기는 73개, 인터페이스는 25개다. 추가 확장 118개 중 31개 일부 구현·87개 계획을 유지한다. 소스 공개 범위·설치 검증은 현재 `validation/`의 기록과 함께 판단한다.

## 2026년 10월 26일

독립 Python 패키지, 공통 입력·결과 계약, 모델 레지스트리, SI 변환, 사용자 파라미터·물성 표·규칙·워크플로 구조를 구축했다. 손상·구조·피로·파괴·크리프·용접·제작·검사·신뢰성의 첫 계산 경로와 CoolProp 공급자를 추가했다.

데이터 취득을 먼저 수행했다. 첫 7개 묶음 이후 BAM P92와 FABEST를 추가해 9개 데이터 묶음에서 23개 파일, 총 382,582,529바이트를 확보했다. 제공자가 체크섬을 제공한 파일은 비교했고 모든 파일에 SHA-256을 기록했다. 취득 파일과 재배포 승인 상태를 구분했다.

실제 데이터를 연결하면서 다음 문제를 발견하고 처리했다.

- CORR-DATA의 24,721행 중 수치 한 점은 5,896행, 구간은 18행이다. 나머지는 등급·텍스트 등이므로 임의의 부식속도로 바꾸지 않았다.
- COQTEL의 분 단위 전기화학 시계와 HDF 파형 축을 확인했다. 실험별 10개·2개의 같은 시각 반복 구간이 있어 기본 정책은 거절하고, 동일 전류·전위가 반복될 때만 명시된 정책으로 보존하도록 했다.
- 용접 피로 248행 중 반복 시편 행 7개와 미확정 입력을 구분했다. 제한된 보정 예제에서 이를 제외하고 미파단 관측을 우도에 포함했다.
- MetroPT-3의 실제 기록 간격은 주로 10초다. 메타데이터의 명목 취득 주기를 그대로 계산 시계로 사용하지 않았다. 압력의 게이지·절대 기준은 별도 확인 대상으로 남겼다.
- 코팅 자료의 초기 파일은 Origin 프로젝트와 그림·발표 파일이었다. 수치 테이블을 확보한 것으로 표시하지 않았다.
- BAM 파형 630,582행을 읽고 MPa·변형률 %·섭씨를 SI로 변환했다. 기록된 시간의 반올림 때문에 시험별 1,623·46,144·66,194개의 같은 시각 구간이 있어 원래 순서를 보존했다. 미세 시간이나 변형률 속도를 임의로 만들어내지 않았다.
- FABEST 73개 시트에는 61개 시험 그룹 시트와 회귀·정리 정보가 함께 있었다. 매크로를 실행하지 않고 자료 구조만 읽었으며 실험 시편 행 수는 아직 확정하지 않았다.

검증 중 얇은 막 근사와 유한 두께 탄성해가 특정 두께에서 사실상 동일해야 한다는 초기 시험 조건이 부적절함을 확인했다. 얇아질수록 오차가 감소하는 수렴 시험으로 고쳤다. 코드 계산식에 임의 보정을 넣지는 않았다.

수치 경계도 추가 점검했다. 벽이 소진된 이후의 감육 예측은 0 두께로 잘라 유효 결과처럼 반환하지 않고 범위 밖으로 표시한다. 매우 짧은 Weibull 평가기간과 열용량비가 1에 가까운 기체 팽창에서는 차분 상쇄를 줄이는 형태를 사용했다. 결과에 입력 자체와 의존성 버전을 남겨 해시만 있는 기록보다 재실행 가능성을 높였다.

각 단계의 실행 결과는 검증 기록과 데이터 목록으로 갱신한다. 기능 목록의 계획 항목은 구현·적용성·검증 근거가 준비된 뒤에만 상태를 바꾼다.

같은 날 두 번째 확장에서 도금강 전기화학·표면 시험 5개 파일을 추가해 실제 취득량이 10개 묶음·28개 파일·382,898,050바이트가 됐다. 3개 용액의 24개 분극곡선에서 19,680개 점을 SI로 읽었다. 요약 저항의 면적 정규화가 확정되지 않아 부식 전류 보정값으로 자동 연결하지 않았다.

계산기는 58개로 늘었다. 소신호 전기화학, 선형 갈바닉 회로, 반무한 확산, 산화막 성장, 마모, 결측 두께 지도, 오프셋 항복, TOFD 기하, 경도, 기체 재고·진공 압력상승, 원통 열전달, 열처리 센서 이력, 안정화 응력–변형률 및 변형률 수명을 추가했다. 물성 공급자는 재료·상태·제품·판본 대조와 외삽 거절을 구현했다.

압력 이력에서 막 응력·rainflow·Basquin·Miner로 이어지는 경로는 품질 마스크·형상·온도·응력 범위·응력비를 확인한다. 자산·부위가 문맥과 다르면 거절하고 자료가 빠진 구간을 이어 붙이지 않는다. 최종 로컬 검사는 116개가 통과했으며 모델 수와 시험 수를 실험 인증 건수로 해석하지 않는다.

같은 날 후속 단계에서는 FABEST 관측 663행과 별도 strain-life 8행을 매핑했다. 정적 기준 60개와 회귀 출력 2,885점을 제외하고 미확정 끝점 1행, 재시험 가능 표식 54행과 끝점 주석 89행을 보존했다. 선택한 작은 FAB005 수명 적합은 매우 가파른 기울기·큰 산포를 보여 qualified curve로 채택하지 않았다.

BAM의 사이클 extrema 표와 파형 peak는 일치했다. 두 표 모두 선택된 사이클만 포함하며 열린 경로가 있어 전체 시험 이력이나 소산 에너지로 확대하지 않았다. 시간 미분을 사용하지 않는 응력–변형률 경로 계산을 추가했다.

POD의 exact binomial 근거와 독립 hit/miss MLE·프로파일 한계를 구현하고 분리·중복 시편·비식별 상태를 명시했다. 250회 합성 진단 결과는 명목 수준의 보증이 아닌 finite-sample 진단으로 보존했다. 보정된 POD에서 무지시 갱신으로 이어지는 워크플로 예제도 실행했다.

균열은 순서가 있는 인장 블록·사용자 형상표·문턱·인성·성장 보정 범위를 받도록 확장했다. 닫힌 해와 독립 ODE, 하중 순서와 numerical tolerance를 검사했다. 계산기는 62개, 인터페이스는 18개이며 로컬 136개 검사가 통과했다. 전체 확장 범위와 독립 실험 자격은 계속 진행 상태다.

다음 확장에서 Charpy 편집 자료·이용조건·설명을 고정 리비전으로 확보했다. 취득량은 11개 묶음·31개 파일·383,732,423바이트가 됐다. 4,961행 중 4,871행이 기본 수치·형상 조건을 만족했다. 293개 보고 ID를 단독 그룹 기준으로 쓰면 조사 조건을 섞는 사례가 두 개 있어 모든 재료·처리·형상 메타데이터로 532개 조건 그룹을 만들었다. 동일 보고 행 25개는 자동으로 독립 또는 중복 시험으로 확정하지 않았다. 원 문헌 109개의 식별자를 보존하고 편집 저장소의 MIT 선언과 개별 관측의 권리 검토를 구분했다.

성분 구간·명칭·heat 대조, 공칭/제작 후 실측 두께 예산, 용접 표면 오프셋과 각도·경도 구간·질량 희석, 음극방식 전하/전류 예산과 충격 전이곡선을 추가했다. 음극방식에서는 두 선형 이력의 곱이 2차식이므로 내부 peak와 정확한 전하 적분을 구현했다. 표면 적합은 쌍별 Theil–Sen의 큰 표본 비용을 명시하고 soft-L1 대안을 제공했다. 충격곡선은 shelf·수치 경계·식별성을 검사하며 실제 14행 시범 결과는 기술적 적합으로만 기록했다.

중첩 tuple 근거를 포함한 JSON 입력이 Python의 엄격한 타입 경로에서 거절되는 문제를 확인했다. `ModelRegistry.run_json`으로 엄격한 JSON 경로를 분리하고 CLI·프로필·워크플로에서 사용했다. 비유한 값을 null로 바꾸는 직렬화는 허용하지 않았다. `computed`인 비교 결과가 후속 절차를 자동 허용하지 않도록 선택적 `SatisfactionGate`를 추가했다. 요구 충족·미확정·미충족과 원 계산 상태를 분리했다.

현재 69개 계산기·21개 인터페이스·164개 로컬 검사가 있다. 충격 전이곡선의 계획 행은 실제 계산기로 이동했고 카탈로그 중복 ID 검사를 추가했다. 118개 추가 확장 중 28개 일부 구성요소와 90개 계획을 유지한다. 계산기 수·시험 수를 실험 적합성 인증 건수로 해석하지 않는다. 설치 환경·빌드 포함 목록은 `validation/`의 현재 리비전 증거를 확인한다.

후속 데이터 확장에서 WILLOW 합성 4파일과 실제 해상 노출 4파일을 확보했다. 누적 취득은 13묶음·39파일·412,766,195바이트다. 합성 2,000건의 HDF 참조 셀·특징표 기하를 대조하고 실제 774건의 시각을 연결했다. MAT는 v7.3으로 일반 `loadmat`이 읽지 못하므로 h5py를 사용했다. 원 파일의 501·1,024 표본을 보존하고 부재한 sample clock을 만들지 않았다. 문자 false의 Python truthiness, 제공자 처리 실패와 개별 특징 누락, 비유한 합성 파형을 별도로 처리했다. 실제 V212에는 약 48일의 공백과 gain/filter 변화가 있어 직접 성장·진폭 추세로 전환하지 않았다.

배관 파열 편집 후보는 CC0 선언과 수치/실험 구성 설명까지 확인했으나 파일 API가 인증을 요구해 취득하지 못했다. 공개 자산 경로·원 문헌 독립성·단위·권리를 검토할 후보로만 남겼다. 확보되지 않은 453건을 실험 검증 자료로 계산하지 않았다.

동일 노출의 면적 블록 최대값에 Gumbel MLE·재적합 AD 진단·파라미터 bootstrap을 추가했다. 표본 독립·모집단·미검열과 면적 외삽·음의 물리 깊이·적합도 기준을 명시한다. 공간 초과를 기간 최초고장으로 바꿀 수 있던 일반 어댑터의 경계를 보강했다. 모델·결과·카탈로그에 확률 의미를 남기고, 사건 변환은 명시된 기간 조건부 최초고장만 허용한다. Weibull 시계도 대조하며 모니터링은 원 결과와 독립된 스냅샷을 제공한다.

현재 70계산기·22인터페이스·182검사다. 추가 118작업은 29개 일부 구현·89개 계획이다. 극값의 150회 합성 포함률 진단과 WILLOW 전수 매핑을 보존했으며, 국부감육 구조 FFS·파열압·실제 공간 극값의 실험 검증은 완료하지 않았다. 과학 확장 SciPy 하한을 modern rng API에 맞춰 1.15로 조정했다. MAT 원자료도 빌드·배포 제외 검사에 명시했다.

후속 단계에서는 API 인증 때문에 보류했던 파열 편집본의 일반 공개 화면에서 ZIP 주소와 제공자 SHA-256을 확인했다. 원 공개 다운로드 경로로 취득하고 체크섬을 대조했다. 최종 응답이 임시 서명 주소로 바뀌는 사례를 확인해 수집기·기존 장부를 정리했다. 공개 기록에서 query·fragment·URL 자격정보를 제거하고, 모의 응답·캐시 체크섬 검사와 빌드 단계 장부 검사를 추가했다. 누적 데이터는 14묶음·40파일·412,842,695바이트다.

주 표 453행을 실험 102건과 FEM 351건으로 분리했다. 색상 범례에 따라 참조 물성으로 보완된 항복강도 62셀·탄성계수 326셀과 추정 폭 302셀을 보존했다. 9개 반복 입력/표적 행은 모두 FEM에 있었으며 삭제하지 않았다. `Ma13Otros` 23행의 직접 문헌 연결, 실제 시편 독립성, 주 표에 명시되지 않은 지름·압력 기준은 미확정이다. 보조 시트는 추가 시편으로 합치지 않았다. 설명의 19개 깊은 결함과 실제 16개 명확한 초과·3개 반올림 경계의 차이도 기록했다.

사용자 기준 차압·형상 보정표를 공급받는 축 방향 면적 스캔을 구현했다. 기본 벽 두께와 각 절점 구간의 투영 손실 면적을 명시하고, 전체 구간에서 가장 낮은 계산 용량을 선택한다. 공개 연구 수식을 눈으로 교차확인했으며 인쇄·기호 불일치가 있는 설명을 그대로 구현하지 않았다. 규격의 보정계수·판정표·문장·그림은 포함하지 않았다. 독립 적분·해석적 극한·지배 구간·기하학적 상사·절점 세분화·적용성·공급자 조건을 검사했다.

새 기준·출력은 차압 이름으로 명시해 공정의 절대 내압과 혼동하지 않게 했다. 계산기는 71개, 인터페이스는 24개, 로컬 검사는 197개다. 118개 추가 작업 중 30개 일부 구현·88개 계획을 유지한다. 실제 파열압 검증과 전체 규격 FFS는 진행 대상으로 남기고, 새 공급자 스키마·예제·데이터 감사·재개 지침을 갱신했다.
# 2026-10-27 - FABEST LCF 공개 벤치마크 계약 착수

공식 규칙과 CC BY 4.0 데이터 기록을 확인하고 주기 응답의 평균/진폭 가중 상대오차, 피로수명 RMS
로그오차, 압축 분지 동적탄성률 저하 종료점을 `models/fatigue_benchmark.py`에 독립 구현했다. 평균값
정규화가 0에 가까울 수 있어 정규화 크기를 필수 양수 입력으로 분리했고, 시험마다 먼저 평균한 후
시험들을 같은 비중으로 평균한다. 수명 metric은 검열값 대체를 금지한다. 종료점은 첫 관측점과
명시적 구간 선형보간을 구분하고 닫힌 무교차 관측을 우측 검열로 남긴다.

공개 계약 스키마 4개와 단위시험 12건, 손계산 가능한 고정 검증 JSON을 추가했다. 현재 레지스트리는
138개 계산기, 공개 스키마는 191개다. LCF v2 대용량 ZIP은 531,469,245바이트와 제공자 MD5·프로젝트
SHA-256으로 고정했다. 24개 calibration 실험의 96개 수치표와 25,213,349행을 압축 해제 없이 감사했고
별도 물리 시편 ID가 없음을 보존했다. 전체 목표 진행률은 실제 물리 holdout 검증이 늘지
않았으므로 65%로 유지했다.

## 2026-10-29 대기부식 예측 공분산 계약

대기부식 첫해 예측 모델의 회귀계수 공분산 검증을 대칭성에서 양의 준정부호까지 강화했다. 음의 고윳값이 기계정밀도 허용범위를 넘으면 입력을 거부하고, 특이 양의 준정부호 행렬은 수용한다. 비정상 행렬 거부 및 특이 행렬 수용 회귀를 기존 `batch44-atmospheric-scenario-ensemble` 파일에 추가했다. 로컬 pytest 및 누리온 작업은 실행하지 않았다.

## 2026-10-29 Davies 활동도 구성요소

`chemistry.davies_activity_coefficients`를 추가했다. 완전한 molality species inventory를 입력받아 ionic strength와 charge-balance residual을 계산하고 온도·용매 기준의 caller-provided Davies A로 charged species의 활동도 계수를 반환한다. 중성종 gamma=1 관례와 molality 표준상태, charge-balance review, source/configuration digest, 0.5 mol/kg 이하 한도를 계약으로 드러냈다. USGS PHREEQC 식 문서와 USGS WSP 2254의 활동도 근사 범위 논의를 공개 근거로 등록했으며, 농축 염수와 가스-액 평형, 부식률은 포함하지 않는다. synthetic example, schema, wet-CO₂ partial capability 연결을 만들고 focused 회귀를 batch59에 추가했다. 후속 점검에서 carbonate alkalinity 모델의 1 mol/L activity standard state를 계약에 고정하고 필수 review gate를 추가해 molal Davies 결과의 직접 전달을 막았다. 테스트 코드는 batch58 입력 파일에 추가했고 로컬 테스트와 누리온 작업은 실행하지 않았다.


## 2026-10-29 — 공개 CT110 용접부 부식속도 비교 자료/API

PLOS ONE 논문 DOI `10.1371/journal.pone.0244237`의 Figshare S1/S2 API metadata에서 CC BY 4.0과 provider MD5를 확인하고 두 XLSX를 `data/raw/` 제외 경로에 고정했다. 온도 및 CO₂ 분압 각 3조건에서 용접금속/모재 부식속도 6쌍을 출처표시·단위변환과 함께 공개 fixture `validation/ct110_weld_corrosion_rates.json`에 정리했다. 동일 논문에 coupon ID, replicate count, 불확실성이 없으므로 한 연구의 descriptive example로 제한한다.

`corrosion.material_rate_contrast`는 비음수 caller rate 두 개의 차·비·로그비를 계산하고 재료/조건/source identity와 조건 signature digest를 보존한다. 이를 부식 예측, 보편적 용접 배수, 위험확률 또는 합격판정으로 해석하지 않는다. API 문서, catalog, schema, 합성 example, 권리표시와 `batch60-material-corrosion-rate-contrast` 회귀를 추가했다. 로컬 pytest와 누리온 제출은 하지 않았다.


## 2026-10-29 — CT110 공개 관측의 설치 reader 연결

설치 wheel에서 CC BY fixture를 바로 읽도록 `matintegrity.ct110_data.read_ct110_weld_corrosion_dataset()` typed reader를 추가했다. reader는 packaged dataset catalog의 SHA-256과 fixture bytes를 확인하고, Pydantic 계약으로 두 가지 제공자 파일 hash, citation/attribution/license, 조건, 단위변환, 미확정 시편·반복·불확실성 상태를 검증한다. `contrast_input(comparison_id)`는 지정된 한 행을 `corrosion.material_rate_contrast` 입력으로 변환하며 알 수 없는 ID를 대신 채우지 않는다. 4개 공개 schema, `data.ct110_weld_corrosion_reference` 인터페이스, runnable example과 batch61 회귀를 추가했다. pytest 실행 및 누리온 제출은 하지 않았다.


새 corrosion.rate_joint_scenario 구현은 등록 계산기 수를 288개로 갱신한다. 독립 표본 분위수 기반 시나리오와 임의 의존성/분포를 추가 추정하지 않는 완전 입력 계약을 제공한다.
# 2026-10-29 — wet-CO₂ 시뮬레이션 행의 벽손실 시나리오 연결

제공자 시뮬레이션 출력과 독립된 실제 시편 부식률 계약을 유지하면서 `corrosion.simulation_rate_wall_loss_scenario` 계산 API를 추가했다. 명시적 caller weights, 재료 상태·조건 전이·선형 손실 리뷰 ID를 요구하고 DOI·CC-BY evidence·provider row·archive SHA-256을 결과에 보존한다. 이는 고정률 선형 감육 시나리오이며 실험 예측, 보정, 고장확률 또는 FTA 사건확률을 만들지 않는다.

합성 입력 예제, 공개 schema, capability catalog, API 설명과 batch76 Nurion 회귀 명세를 연결했다. Ruff 및 catalog/schema/package 정적 생성을 마무리할 예정이다. pytest는 로컬에서 실행하지 않으며 Nurion 작업도 제출하지 않는다.

# 2026-10-29 — 부식 시나리오의 최초 통과/FTA 경계 연결

`corrosion_model_output_to_first_passage_inputs` adapter를 추가해 범용 비실험 rate scenario를 `SampledLinearThicknessFirstPassage` 입력으로 넘긴다. 평가시각의 두께, 분포·생존 조건, 요구두께, 후보시간, 사건 및 물리 범위는 caller가 명시한다. 공통 source lineage와 별도 검토 참조 ID가 최초 통과 결과까지 보존된다. 최초 통과 모델만 선언된 기간 고장확률을 제공하고 기존 `probability_event` 경계를 거쳐 `EventProbability`로 표현할 수 있다. synthetic Python composition 예제와 batch78 회귀를 추가했으며 계산 테스트는 로컬/Nurion 모두 대기 중이다.


순수 CO2 EOS fugacity를 제공하는 `thermo.co2_fugacity_coolprop`을 추가했다. CoolProp AbstractState 저수준 API를 optional dependency로 지연 호출하며 절대 CO2 부분압, 온도, 순수성분 근사 검토 및 단일상 검토를 요구한다. 공식 phase enum을 사용해 기체·초임계 기체·초임계 상태만 계산하고 나머지는 제외하며 provider revision/configuration/result digest를 남긴다. 기존 fixed-fugacity carbonate 입력 필드용 adapter를 제공하고 CoolProp 미설치면 `needs_data`를 반환한다. registry/example 293개, capability 507개(101 partial), source basis 321개, HPC manifest 127개로 확장했다. Ruff, compileall, registry/catalog 정합성, rights metadata(51 dataset/321 sources, finding 0), 패키지 allowlist 검사(265 wheel·1582 sdist·1575 review files)가 통과했다. 패키지 빌드는 no-isolation으로 완료했다. pytest와 Nurion 계산은 실행/제출하지 않았으며 batch96에서 대기한다. 독립 혼합물/실험 기반 자격화는 미완료다.



CO2 fugacity 결과에서 AquaSolDB의 고정 fugacity 비교 계약으로 provider·온도·digest 필드를 옮기는 adapter를 추가했다. 기존 AquaSolDB 비교기는 측정/계산 출처 구분, partial-pressure 기준, solvent·Henry record 검토를 계속 요구한다. 새 연결은 자료에 계수를 적합하지 않으며 독립 Henry record 기반 단일 관측 비교에 한정한다. 연결 adapter 회귀는 batch96에 포함한다. 로컬 pytest/Nurion 미실행.



CoolProp CO2 기능의 HPC 검증 누락 가능성을 닫았다. manifest batch96 pytest는 CoolProp 없이 provider 회귀를 skip할 수 있으므로, 별도 필수 command scripts/validate_co2_fugacity.py를 추가해 optional dependency가 없는 환경은 실패하게 하고 저압 ideal-gas limit, fugacity coefficient×partial-pressure identity, supercritical gas phase, compressed-liquid withholding 및 두 adapter의 digest/temperature 연결을 검증하도록 했다. HPC 안내에는 .[science,thermo,dev] 환경과 CoolProp 사전 설치 확인을 명시했다. manifest 127 task 및 0–126 array 범위 preflight 통과. command는 Nurion에서 아직 실행/제출하지 않았다.


CoolProp CO2 provider의 Nurion validation 산출물에 정확한 입력 조건, acceptance tolerance, 관측 fugacity/phase, provider version/revision 및 config/record digest를 기록하도록 정리했다. 
alidation/co2_fugacity_coolprop.json과 docs/VALIDATION_KO.md에 어떤 내부 일관성 검사를 하는지, 독립 실험·mixture qualification을 증명하지 않는지와 HPC task 126 stdout 결과 경로를 명시했다. pytest/validation 실행은 하지 않았다.

## 2026-10-29 CoolProp CO₂ 혼합기체 fugacity 확장

순수 CO₂ 경로와 별도로 `thermo.co2_mixture_fugacity_coolprop`를 추가했다. 호출자가 성분·정규화 몰분율·전체 절대압을 제공하고 조성, EOS 적합성, 단일상 가정을 각각 근거와 함께 검토해야 한다. CoolProp `AbstractState`가 상태를 평가하지 못하거나 기체/초임계 phase가 아니면 결과를 제한하고 대체 EOS/이상혼합 근사를 적용하지 않는다. CO₂ 성분 fugacity가 `phi_i × y_i × P`와 일치하는지 내부 일관성을 확인하고 두 carbonate/AquaSolDB provenance adapter를 제공한다. CO₂/N₂ 합성 예제와 provider command 검증을 기존 task 126에 반영했다. registry 294, examples 294, capability 508(101 partial), source basis 321, public schema 581이며 HPC manifest는 127 task다. Ruff, compileall 및 manifest/index guard를 통과했고 schema·source·capability·model reference catalog를 재생성했다. pytest와 CoolProp validation command, Nurion 작업은 실행하지 않았다.

## 2026-10-29 보존 이력의 구간별 감사 출력

`fabrication.storage_preservation_history` 계산기 출력을 확장해 horizon 전체를 기록 구간·inspection boundary별로 분할하는 `environment_timeline`과 각 점검 간격·초과량을 나열하는 `inspection_schedule`을 추가했다. 행에는 observed/invalid/uncovered 상태, 원 interval ID, 결측 근거 및 caller 선언 한계의 초과 차원이 들어간다. 빈 구간은 분명히 남기고 상태·환경을 보간하지 않는다. 신규 합성 회귀를 batch97로 manifest에 등록해 현재 128 tasks(0–127)로 늘렸다. Ruff·compileall·manifest 검사 및 schema/model/capability/source catalog 재생성과 release review archive 제한자산 검사는 통과했다. pytest 및 누리온 작업은 미실행이다.

## 2026-10-29 HPC 병렬 결과에 소스 스냅샷 결속

HPC task runner가 실행에 사용한 `src/scripts/tests/examples/hpc` 및 build configuration 파일의 deterministic SHA-256 tree digest와 파일 수를 task 결과에 기록하도록 했다. 데이터 원본, 결과 디렉터리, build/cache 폴더는 해시 범위에서 제외한다. Collector는 모든 task result의 manifest digest뿐 아니라 동일 source-tree digest와 유효 file count를 요구해 서로 다른 staged snapshot의 결과를 성공 집계에서 거부한다. mixed-source regression을 batch98에 등록했고 전체 129 task(0–128)로 manifest를 갱신했다. 검증 테스트는 로컬에서 실행하지 않았다.

HPC source fingerprint의 범위를 수동 디렉터리 목록에서 `scripts/build_release.py`의 public allowlist로 통합했다. 따라서 실행 코드뿐 아니라 문서, validation fixture, 공개 catalog와 release configuration도 같은 snapshot digest에 결속되고 raw/derived/evidence 바이너리는 기존 allowlist 규칙으로 제외된다. 적용 검사는 기존 batch98 task contract regression에 포함한다.

## 2026-10-29 — GitHub 확장 요청 색인과 HPC 검증 명세

확장 요청 디렉터리에 존재하던 Human Reliability Toolkit 및 Hydrogen Physical Models 요청서를 공통 색인 표에 추가했다. 색인의 참조 집합이 README를 제외한 실제 요청 Markdown 파일 집합과 일치하는지 검사하는 regression을 추가하고 HPC manifest batch99에 등록했다. 총 130개 검증 작업(0–129)이다. manifest 구조검사, GitHub integration catalog 오프라인 감사, Ruff, compileall 및 release/package 포함 경로 감사는 통과했다. pytest 실행과 Nurion 제출은 하지 않았다.

## 2026-10-29 — 데이터 카탈로그 출처·권리 감사기

독립 오프라인 감사 명령 `scripts/audit_dataset_catalog.py`를 추가했다. 카탈로그의 dataset/asset identity, HTTPS 취득 URL, 정책, 크기와 checksum 형식을 확인하고 로컬 원본이 있으면 선언된 제공자 checksum과 byte count를 재검증한다. 제공자 checksum 부재와 해당 상태에서의 로컬 파일은 qualified asset으로 취급하지 않고 finding으로 따로 보고한다. 현재 조사 결과 51개 dataset, 261개 asset이며 publisher checksum 없는 11개가 모두 로컬 보유본에서도 미검증 상태로 명시된다. MIT/CC-BY 등 편집물 라이선스와 관측값 권리의 차이는 rights status별로 계속 보존한다. 회귀는 batch100에 등록했다. 로컬 pytest 및 Nurion 제출은 하지 않았다.

## 2026-10-29 — 선택 허용 데이터의 명시적 취득 경로

`fetch_data.py`가 `allowed` 정책만 선택해 `allowed_selected_assets` 및 `allowed_selected_text_assets`로 승인된 자료가 명시적 ID와 `--include-optional`을 제공해도 수집되지 않던 경로를 수정했다. 새 `selected_assets` 정책 함수는 허용 목록 외의 정책을 거부하고, 선택 허용 정책은 ID와 optional flag가 모두 명시됐을 때만 파일을 반환한다. 회귀를 HPC manifest batch101로 추가했다. 실제 원격 다운로드와 pytest는 실행하지 않았다.

선택 정책 경로에서 함께 확인한 캐시 무결성 문제도 같은 batch101에 포함했다. `fetch_asset`은 publisher checksum이 없는 경우도 기존 캐시·신규 응답 모두 카탈로그의 정확한 byte count와 max_bytes를 통과해야 downloaded로 기록한다. 크기 불일치 파일은 유효 취득 성공으로 남지 않는다.

batch101의 취득기 통합 회귀 fixture도 `allowed_selected_assets`와 `allowed_selected_text_assets`로 확장해 `acquire()`가 명시된 ID/옵션 요청에서 실제로 파일 작업을 생성하는지 HPC에서 확인하도록 했다. 작업 경로는 해당 통합 회귀와 크기·정책 단위 회귀를 모두 포함한다.

## 2026-10-29 — HPC manifest 회귀 경로 사전 검증

manifest의 focused pytest 경로가 실제 파일인지, 프로젝트 밖을 가리키지 않는지 `validate_manifest`에서 확인하도록 했다. 이전의 focused test 경로 누락 점검을 반복 가능한 제출 전/실행 시 invariant로 옮기고, 존재하지 않는 경로와 프로젝트 외부 경로 거절 회귀를 batch98이 이미 포함하는 `tests/test_hpc_task_contract.py`에 추가했다. 경로 검사는 심볼릭 링크 resolve 이후 project root 포함 여부를 확인한다. pytest는 실행하지 않았다.

## 2026-10-29 — Slurm/PBS 원자료 staging 일치

Slurm array가 PBS array와 달리 `data/raw`, `data/derived`, `data/evidence`를 scratch로 전부 복제하던 동작을 맞췄다. Slurm도 세 디렉터리와 wheelhouse/HPC 결과를 rsync에서 제외하고 실행 시 원 project data 경로를 링크한다. 공개 source digest는 기존처럼 release allowlist 경로만 대상으로 하며 raw bytes는 hash snapshot에 추가하지 않는다. 두 scheduler script의 staging 제외·link 정책 회귀를 batch98의 test_hpc_task_contract에 추가했다. pytest와 scheduler 제출은 하지 않았다.

## 2026-10-29 — 데이터 권리 검토 날짜 freshness 보고

권리 metadata 감사가 `checked_on`의 ISO calendar 유효성·미래날짜를 검사하고, 기준일에서 기본 365일이 지난 dataset review를 별도 freshness 결과와 ID로 표시한다. CLI에서 `--as-of`와 `--freshness-days`를 지정해 재현할 수 있다. stale은 재검토 알림이며 structural metadata status와 법적 권리 판단을 혼합하지 않는다. 오래된/invalid/future 합성 회귀를 기존 release-rights focused task에 추가했다. pytest는 실행하지 않았다.

freshness result의 명칭을 `review_date_freshness`와 `within_threshold`/`older_than_threshold`로 바꿔 제공자 권리 검토의 최신성이나 완료를 암시하지 않고 `checked_on` 날짜만 해석하도록 했다. unresolved redistribution status는 데이터셋별 rights_status에 계속 남고 이 날짜 보고와 독립적이다.
 
HPC에 batch102-rights-review-date-freshness focused task를 추가해 오래된·invalid·future checked_on 회귀를 결과에서 별도로 식별한다. 전체 pytest shard에도 이미 포함되지만 focused task는 빠른 분류용이며 중복 실행은 의도된 검증 비용이다.

## 2026-10-29 — 공개 데이터 권리 근거 재확인

공식 Mendeley Data v1 페이지에서 304L chloride SCC archive의 CC BY 4.0 dataset license를 재확인했다. 공식 HyMatBase 4130X 레코드에서는 4.5 MPa/25°C metadata와 XLSX asset은 확인했지만 Rights 영역은 비어 있어 redistribution review_required를 유지했다. Data.gov의 NIST CORR-DATA catalog는 NIST open terms와 함께 1997 update, 250개 초과 source document에서 취합된 기록 및 source-specific reuse review 필요성을 재확인했고, NIST licensing guidance가 SRD와 기타/외부 기여 자료를 구분하는 점을 문서화했다. 해당 provider review 날짜를 카탈로그에 반영했으며 raw/pointwise NIST data는 계속 배포하지 않는다.

## 2026-10-29 — 배포 카탈로그 원본·wheel 동기화 게이트

공개 데이터·source metadata는 data/catalogs와 validation에 있고 wheel용 복사본은 src/matintegrity/catalog_data에 따로 있어 수동 sync 누락 시 source archive와 wheel의 검토일·라이선스 metadata가 달라질 수 있음을 확인했다. build_release.public_files()에서 네 설치 카탈로그의 원본/패키지 byte equality를 강제해 stale이면 scripts/sync_catalogs.py 안내와 함께 실패하게 했다. HPC source fingerprint에서도 같은 guard가 적용된다. 동일/불일치 합성 회귀를 batch103으로 추가했으며 pytest 실행은 하지 않았다.

## 2026-10-29 — 직접 wheel 빌드의 카탈로그 동기화 게이트

`python -m build`가 `build_release.py`를 거치지 않고 호출되어도 wheel 생성 시 공개/설치 카탈로그 byte equality를 검사하도록 setuptools hook을 두었다. 검토 과정에서 `setup.py` 자체가 source-review 허용 목록과 sdist manifest에서 빠져 있음을 찾아 두 경로에 포함했다. 배포 매뉴얼에 직접 빌드 동작을 설명했다. 로컬 테스트와 Nurion 제출은 하지 않았다.

격리된 PEP 517 환경은 `scripts`를 import 경로로 노출하지 않아 첫 sdist build-requirements 단계에서 훅 import가 실패했다. `setup.py`가 프로젝트 내 `scripts/build_release.py`를 파일 경로로 로드하도록 바꿔 해결했다. Windows 로컬에서 sdist와 wheel 빌드 및 `audit_packages.py`가 통과했고, 결과물에서 setup hook/validator 포함과 wheel의 네 카탈로그 존재를 확인했다. source-review 1,583개 파일, sdist 1,590개, wheel 265개이며 제한 파일 검사는 모두 통과했다. Ruff, format, compileall 및 HPC manifest 134 task 구조검사가 통과했다. pytest와 Nurion 제출은 수행하지 않았다.

## 2026-10-29 — 부식 pit 면적 극값의 GEV 선택지

기존 동등면적 독립 블록 최대 Gumbel 모델에 `extreme_value_family` 입력을 추가해 Gumbel(기본값)의 기존 호출과 SciPy generalized extreme value(`gev`)를 함께 지원한다. 가족별 MLE·매 반복 재적합 Anderson–Darling 진단·parameter bootstrap 구간·음수 물리 깊이 질량 검사를 동일하게 적용한다. 면적별 목표 최대 분위수는 `Fblock^k` 최대 안정성 관계와 survival-function 역산으로 계산하고 공간 초과확률은 log-CDF로 안정화했다. 이 계산은 단일 노출 조건의 공간 극값만 다루며 시간 성장, 구조 파손 또는 분포 꼬리의 실험 자격화를 주장하지 않는다. 결정적 GEV 비교 회귀를 `tests/test_pitting_area.py`에 추가하고 Nurion batch104에 등록했다. 방법/API 설명을 보강하며 capability 전체 상태는 partial로 유지했다. 로컬 pytest와 Nurion 제출은 하지 않았다.

## 2026-10-29 — PBS array 범위와 확장 회귀 추적

GEV 입력을 검증하는 `test_pitting_area.py`와 전 모델 입력 계약 회귀를 batch104에 등록했다. PBS 전처리 확인 중 `pbs_array.sh`에 명시적인 `#PBS -J` 범위가 없어 repository preflight가 script를 읽지 못하는 기존 설정 누락도 확인했다. 현재 135개 manifest 작업에 맞춰 범위를 `0-134%16`으로 추가했고 PBS/HPC manifest 검사에서 범위와 동시성 한도를 확인했다. GEV 회귀 자체와 전체 pytest는 Nurion 일괄 검증 대상으로 두며 제출하지 않았다.


## 2026-10-29 — WILLOW 공개자료 권리 metadata 재확인

Zenodo 공식 record API의 license metadata를 재조회해 WILLOW 합성 자료와 HarshLab 자료 모두 `cc-by-4.0`임을 확인했다. catalog review date를 2026-10-29로 갱신하고 rights evidence를 API endpoint로 고정했다. 데이터 역할의 경계(시뮬레이션 기하 truth 대 두 실제 시편 반복 기록)는 유지하며 두 자료를 독립 pit-population 또는 field POD qualification로 사용하지 않는다. Nurion 공유 연결은 지정된 재사용 경로에 유효 세션이 없어 원격 검증을 중단했고 새 연결·비밀번호·OTP를 시도하지 않았다.

GEV 근거에 대해 SciPy 공식 `genextreme` 문서를 확인했다. shape `c`가 일부 다른 참고문헌/소프트웨어와 반대 부호일 수 있다는 내용을 Methods 문서에 설명하고 source catalog의 공식 API 참조로 기록했다. 상단 분위수 계산은 inverse survival function을 사용해 CDF 반올림으로 분위수가 1.0으로 붙는 위험을 피한다.

`examples/pitting_area.py`에 `--family {gumbel,gev}` 선택을 추가해 기본 Gumbel 호환을 유지하면서 GEV 합성 API 실행 경로를 사용자에게 노출했다. 사용 명령과 출력 의미를 API 문서에 연결했다. 로컬 pytest와 Nurion 계산 제출은 하지 않았다.

## 2026-10-29 — EBSD 자료 취득 기록 및 phase-map 감사 경계

Aalto 저합금강 용접금속 EBSD 자료의 선택 ZIP을 로컬 제외 원자료 캐시에 취득했다. Zenodo API의 CC BY 4.0 선언, 53,622,850바이트 크기와 제공자 MD5를 대조했고, 취득본 SHA-256을 기록했다. archive는 ZIP CRC 검사를 통과했으며 안전 검사에서 `CV_3`, `HY_1`, `LA_1`의 Oxford `.cpr/.crc` 여섯 member를 확인했다. 아직 공식 reader로 phase label을 불러오거나 map coordinate·phase ID·specimen identity를 검토하지 않았으므로 실측 면적분율이나 검증 데이터로 세지 않는다. `summarize_phase_label_map()`의 회귀는 batch106에 등록되어 있으나 실행은 Nurion 일괄 검증에 남아 있다.

카탈로그 설치본을 동기화하고 오프라인 dataset audit를 재실행했다. 현재 52 dataset·262 asset이며, 133개 로컬 자산은 공급자 checksum과 일치한다. 공급자 checksum이 없는 11개 자산은 모두 미검증 finding으로 유지한다. HPC manifest와 PBS array의 137개 작업(0–136), 최대 동시성 16의 구조검사가 통과했다. 이번 확인에서 Nurion wrapper는 사용 가능한 공유 연결이 없다고 반환했다. 지침에 따라 새 SSH나 인증을 시도하지 않았고 원격 작업도 실행·제출하지 않았다.

## 2026-10-29 — Oxford EBSD DefDAP reader integration

사용자가 Nurion shared connection을 다시 설정했다고 알려 지정 wrapper를 통해 `HPC_LOGIN_NODE` / `HPC_USER`와 qstat을 확인했다. 기존 계정 job이 다수 실행·대기 중이므로 별도 요청 없이는 새 job을 넣지 않는다.

선택 DefDAP 1.3 extra를 사용한 `read_oxford_ebsd_phase_labels()`를 구현했다. 입력 archive SHA-256, exact pair stem, ZIP member 경로·중복·암호화·symlink·크기, extracted byte count를 검증한 뒤 선택한 `.cpr/.crc` 한 쌍만 임시 디렉터리에 쓴다. reader 결과의 integer dtype·2D shape를 검증하고 raw labels를 read-only로 반환하며 member/array digest, reader version, provider step 숫자와 단위 미확인 상태를 기록한다. 자료의 `.cpr`에 없는 acquisition-orientation group은 DefDAP 형식 호환 때문에 임시 reader copy에만 0 Euler placeholder로 제공하고 해당 처리 상태를 결과에 기록한다. 실험 orientation으로 해석하지 않는다.

mocked safety/API regressions는 batch107로 등록했고 실제 Aalto 세 맵을 읽어 aggregate label histogram과 파일/reader digest를 확인하는 별도 HPC command를 등록했다. 실제 reader 명령에는 `ebsd` extra가 필요하다. Source catalog, public schema, API/data/HPC 문서와 package extra를 갱신했다. 생성 catalog는 326 source basis, 591 public schemas, 139 HPC tasks(0–138)다. 전체 Ruff lint 및 포맷, compileall, manifest/PBS preflight, 52 dataset·262 asset 오프라인 감사, rights metadata와 public source boundary 감사, wheel/sdist/review ZIP 재빌드 및 제한 자산 패키지 감사가 통과했다. 로컬 pytest와 누리온 array/reader command는 실행하지 않았으며 새 job도 제출하지 않았다.
## 2026-10-29 — 해상용 고강도 강재 피로 공개자료 메타데이터 조사

University of Strathclyde 저장소의 S355 이상 강재 S–N 및 fatigue-crack-growth/ΔK workbook을 catalog에 metadata-only로 등록했다. 제공 페이지는 dataset package에 CC BY 4.0을 선언하지만 자료가 논문에서 디지타이즈됐고 원 관측별 권리·시편·runout·단위가 검토되지 않았다. 파일 링크의 익명 요청은 HTTP 403을 반환했고 provider checksum도 확인할 수 없었다. 따라서 파일 취득·모델 적합·점별 재배포는 막고 catalog·설치 사본·피로 자료 경계 문서·제3자 고지를 동기화했다. 검증/패키지 작업은 실행하지 않았다.

# 2026-10-29 — 일반 FCGR CSV 입력 경로

기존 표형 균열성장 API에 명시 단위의 UTF-8 CSV를 연결하는 `fcgr_curve_import` 모듈을 추가했다. ΔK 세 단위와 da/dN 두 단위를 SI로 정규화하며, 행 순서를 바꾸거나 중복을 합치지 않는다. 선택·제외를 행마다 명시하고 제외 사유, 선택 행 ID, 원본 레코드 순번, stage 원문, mapped 원 셀, 원본 SHA-256, citation/license ID와 rights/applicability review ID를 보존한다. 권리와 적용성 검토는 입력 gate로 요구한다. 이 계보 필드는 `TabulatedCrackGrowthCurve`에도 선택적으로 추가해 calculator 입력에도 유지한다. 열 매핑은 고유성을 요구하고 제외 사유 열 이름은 사용자 지정할 수 있다. CSV parser는 malformed quoting을 거부한다. `FcgrCsvImportRequest.from_file()`은 파일 바이트를 요청에 고정하고 선택적 expected SHA-256으로 잘못된 파일을 거부한다. Strathclyde 원자료는 아직 취득하지 못했으므로 이 변경은 전용 workbook reader, 자료 검증, 권리 승인을 제공하지 않는다. importer 계약 세 개를 public schema export에 추가하고 tabular import capability catalog에 연결했다. 테스트와 패키지 작업은 사용자 지시에 따라 수행하지 않았다.

# 2026-10-29 — AM HEA 공개 FCGR 자료 메타데이터 추가

Dryad DOI `10.5061/dryad.vq83bk48n`의 metadata API에서 공개 상태, CC0-1.0, fatigue archive의 크기 34,007,234 bytes와 SHA-256을 확인했다. Provider README는 처리 macroscale SENB CSV에 ΔK/da/dN과 3개 AM HEA 시편 조건을 설명한다. 공식 익명 API 다운로드는 HTTP 401이므로 파일은 받지 않았고 카탈로그에 metadata-only로 등록했다. 따라서 행 구조, checksum 대조, 권리/적용성 세부, 실험 검증은 미완료다. Dryad README에 설명된 microscale J 자료를 ΔK curve input과 혼합하지 않는다.

# 2026-10-29 — S460 fatigue FCGR workbook 취득 및 구조 감사

Mendeley Data `10.17632/ytny53v2fn.2`에서 CC BY 4.0이 명시된 `Paris Law Constants.xlsx`만 다운로드했다. 210,307-byte 파일의 로컬 SHA-256이 provider API checksum과 일치한다. openpyxl 구조 확인에서 CT01–CT06 및 요약 시트를 확인했고, specimen별 R과 처리된 ΔK/da/dN 열, numeric point count 및 각 시트 안의 증가 ΔK 순서를 기록했다. 253개 다른 파일은 취득하지 않았다. 주파수는 해당 workbook sheet에서 확인되지 않으므로 현재 frequency-required tabulated curve에 자동 변환하지 않았고 material/environment suitability도 미승인이다. 카탈로그와 취득 이력에 attribution, CC BY 4.0, digest 및 비독립 시편 한계를 기록했다. 이는 구조 감사이며 모델 시험 검증은 아니다.


## 2026-10-29 — 부분 범위 감사와 구현 상태 재조정

구현 점검표의 code_incomplete 13건을 현재 계산 API와 대조했다. 조건-손실 이력, caller FAD 평가, 순차 균열성장, 열교환기 기본 형상, 튜브 재고, 대류·복사 단열 표면, 화재 열응답의 8개 bounded 계산 경로를 확인하고 감사 분류를 데이터·공급자 의존으로 정정했다. 실제 남은 계산 범위 5건은 CO₂ 반응/이동경계 확장, 가변 형상 또는 대류 crevice, 연속 임계면과 임의 cycle counting, gasket 시간/경로 의존 응답, rare-event 반복 추정 오차 처리다. 관련 소스와 제한 범위를 data/catalogs/implementation_scope_audit.json 및 data/catalogs/objective_progress.json에 기록했다. 테스트·패키징은 실행하지 않았다.

## 2026-10-29 — Gasket preload-retention exchange API

fabrication.gasket_relaxation_curve를 추가했다. Caller 계약은 source/specimen/source-group/provider/condition identity, source·condition digest, 이용권한, normalized time-retention knots와 initial preload를 보존한다. zero-time unit retention, 시간 knot 단조성, 비증가 retention을 입력 조건으로 두고 piecewise-linear interpolation은 명시된 시간 범위 안에서만 허용한다. 예제·공개 schema·source catalog·API/manual reference를 생성해 맞췄다. static path/AST audit에서 204개 source path가 존재하고 구문 분석되며, 계산 테스트와 물리 validation은 수행하지 않았다.

## 2026-10-29 — 고정 형상 틈부식 transport의 축방향 이류

RestrictedTransportRequest에 caller가 provenance/revision을 제공하는 면별 비음수 고정 속도 프로필을 연결했다. mouth-to-tip donor-cell upwind flux가 기존 diffusion/Scharfetter-Gummel flux와 함께 face area weighting 및 누적 경계 inventory ledger에 들어간다. 역류·시간변화 유동·형상 진화는 거절/미지원 범위로 보존한다. 합성 CO2 campaign example과 schema/API/manual 근거를 갱신한다. 계산 테스트는 실행하지 않는다.

## 2026-10-29 — Coupled wall metal-loss exchange

Added corrosion.coupled_wall_metal_loss to convert a digest-pinned signed integrated wall-metal species ledger into total amount, mass, volume change and caller-area-averaged recession. The transport output retains species ordering, physical reference area and reactive-wall/reference-area ratio; phase-split transport exposes the same area lineage. Require metal stoichiometry, wall flux sign, area basis and interpretation reviews. Added synthetic API input, schema/catalog/manual references, and retained limitations on local loss, alloy selectivity and moving boundaries. No numerical test or physical validation was run.

## 2026-10-29 — 부분 구현 분류 및 CO₂ 손실 연동 정정

현재 source audit에서 reliability.rare_event_sampling의 독립 반복 설계, run 간 산포, 표준오차/상대오차 및 목표 정밀도 진단 코드를 확인했다. 해당 과제는 code_incomplete에서 data_validation_pending으로 옮기고 편향·수렴·물리 자격화만 남겼다. 기존 고정-grid transport의 틈부식 advection을 연결해 audit current scope도 정정했다. corrosion.coupled_wall_metal_loss는 금속 wall ledger를 signed 총 몰·질량·부피 변화와 반응 벽면 평균 recession으로 바꾼다. 현재 partial audit은 101항목 중 code_incomplete 4, data_validation_pending 51, provider_dependent 46이다. 실제 실행/수치 검증은 미실행이다.
## 2026-10-29 — 셀별 벽 금속손실 원장과 후퇴량

고정 틈부식 수송 solver의 내부 적분 상태를 확장해 벽 플럭스를 종·축방향 셀별 signed 원장으로 누적한다. 기존 종별 전체 원장과 inventory balance 계산은 셀 합으로 계속 제공한다. 평형-수송 operator-splitting 경로도 각 시간 구간의 셀 원장을 누적 전달한다. `corrosion.coupled_wall_metal_loss`에는 선택형 `cellwise_recession_interpretation_reviewed`를 연결했다. 이 선택을 켜면 고정 셀 폭·단면적·벽 면적밀도에서 셀별 반응면적을 구성하고 총 반응면적과 재조정한 뒤 셀 평균 금속량·질량·부피·후퇴량을 반환한다. 결과는 셀 내부 국부장이나 pit 분포가 아니며 이동 형상·선택용출·scale·수명·합격판정은 제공하지 않는다. source/capability/catalog/reference와 공개 schema를 갱신했다. AST/path scope audit은 206개 경로를 파싱하고 누락 경로 없이 끝났다. 계산 테스트와 패키징은 실행하지 않았다.

## 2026-10-29 — Caller-calibrated gasket Prony history

`fabrication.gasket_prony_history`를 추가했다. 조건·시편·온도·provider revision·source/condition SHA-256 및 computational-use authorization에 결속한 generalized Maxwell 평형 modulus와 Prony branch를 받아, caller가 공급한 초기 내부 branch 응력에서 구간별 선형 압축변형률 이력을 해석적으로 적분한다. hold, unload, reload와 zero-strain recovery를 표현하며 tensile total stress가 나타나면 contact separation law가 없는 범위로 반환한다. registry, synthetic example, source basis, catalog, API/model reference와 branch/model/request 공개 schemas를 추가했다. 예제는 계산 자격 증거가 아니다. 테스트와 패키징은 실행하지 않았다.

## 2026-10-29 — 시간변화 유동과 역류를 받는 틈 수송 API

기존 고정 비음수 advection profile을 유지하면서 restricted transport에 시간별 signed face-velocity Python callback을 연결했다. 내부 face는 방향별 upwind cell을 선택하고 mouth/tip 외부 경계는 signed exchange ledger로 적분한다. distal 방향 역류를 쓸 때 caller는 별도 tip inflow concentration과 flow-reversal/boundary review를 제공해야 한다. callback configuration digest와 provider ID를 요청에 고정하고 출력 clock 속도 프로필을 보존한다. Electrochemical, CO₂ campaign, equilibrium-split wrapper까지 callback을 전달한다. 기존 solver는 geometry를 고정하며 continuity·momentum 방정식을 계산하지 않는다. source basis/API 문서와 scope audit를 갱신했다. 테스트/패키징은 실행하지 않았다.

## 2026-10-29 — 시간변화 유동과 역류를 받는 틈 수송 API

기존 고정 비음수 advection profile을 유지하면서 restricted transport에 시간별 signed face-velocity Python callback을 연결했다. 내부 face는 방향별 upwind cell을 선택하고 mouth/tip 외부 경계는 signed exchange ledger로 적분한다. distal 방향 역류를 쓸 때 caller는 별도 tip inflow concentration과 flow-reversal/boundary review를 제공해야 한다. callback configuration digest와 provider ID를 요청에 고정하고 출력 clock 속도 프로필을 보존한다. Electrochemical, CO₂ campaign, equilibrium-split wrapper까지 callback을 전달한다. 기존 solver는 geometry를 고정하며 continuity·momentum 방정식을 계산하지 않는다. source basis/API 문서와 scope audit를 갱신했다. AST/path audit는 206개 경로에서 누락이나 미파싱 파일 없이 끝났다. 테스트/패키징은 실행하지 않았다.

## 2026-10-29 — 다축 피로 연속 임계면 상한

`fatigue.critical_plane_continuous_bound`를 추가했다. 단위구면의 icosphere 삼각분할을 정제하고 모든 꼭짓점의 FS/SWT sampled-cycle factor를 계산한다. 비방향성 면의 antipodal 중복을 제거하고 각 완전 평가 mesh의 최대 구면 edge 각도를 covering 반경으로 사용한다. 대칭 응력·변형률 텐서의 Frobenius 노름에서 유도한 chord-amplitude, 최대 인장 정상응력, 정상변형률 진폭 Lipschitz 상수로 연속면 최대값의 보수적 upper bound와 gap을 산출한다. 한 단계 전체 평가 전에 candidate/pair-work budget을 확인하므로 중단된 다음 단계의 반쪽 mesh를 상한 근거로 쓰지 않는다. 이 상한은 공급된 이산 시간표본의 해당 factor 정의에만 적용하며 cycle counting·시간 사이 극값·보정/모델오차는 제외한다. 모델/예제/schema/reference/전용 유도 문서를 연결했다. 테스트와 물리검증은 실행하지 않았다.

## 2026-10-29 — 다축 tensor 이력의 면별 scalar rainflow

`fatigue.critical_plane_projected_rainflow`를 등록했다. 임의의 ordered tensor record를 caller가 선택한 normal stress/strain, signed directional shear, 또는 nonnegative shear-vector magnitude 채널로 투영하고 각 채널에 scalar `rainflow` package를 독립 적용한다. tensor/engineering strain shear 관례를 입력으로 받으며 turning-point index를 원본 sample ID와 선택 time에 연결한다. open record의 residual half-cycle을 보존한다. signed component와 방향을 잃는 magnitude 신호를 결과에서 구분한다. 모델은 cross-channel pairing, 다축 damage/수명이나 합격판정을 추론하지 않는다. registry, 예제, source basis, capability/model reference, API guide와 공개 schema를 추가했다. 계산/회귀/물리 검증은 실행하지 않았다.

## 2026-10-29 — 셀별 부식 이력 기반 planar slit 형상 갱신

`corrosion.planar_slit_aperture_history`를 추가했다. digest로 고정한 셀별 cumulative signed average wall recession을 초기 cell aperture에 반영해 시간별 단면적, 부피, 반응면적과 벽면/부피비를 만든다. 양면 반응은 같은 recession을 양 벽에 배분하는 사용자의 명시 검토를 요구하며, 공급자 aperture support 범위를 벗어나면 전체 형상 이력을 보류한다. 반환 형상은 후속 고정형상 수송의 입력을 다시 구성하기 위한 operator split 단계이며, 유동·화학·부식의 동시 연성 해석은 아니다. registry, synthetic example, source basis, public schema, API guide와 제한사항 문서를 연결했다. 테스트·계산·패키징은 실행하지 않았다.

이 API를 확장해 `corrosion.coupled_wall_metal_loss`의 직렬화 결과를 canonical digest로 고정한 뒤 직접 전달할 수 있게 했다. cellwise recession review가 포함된 계산 결과의 output clock과 정렬된 cell index를 확인하고, geometry remap을 위해 값·순서를 수동 복사하지 않게 연결했다. 기존 direct-history 입력도 유지한다. 합성 입력 예제는 digest-pinned upstream result 경로를 보여준다. 테스트는 여전히 실행하지 않았다.

추가로 매 시간 상태에서 `RestrictedTransportRequest`용 셀·면 단면적과 벽면/부피 비를 포함한 `restricted_transport_geometry`를 반환한다. 비균일 mesh의 cell-center area를 거리 가중 선형 보간해 내부 face를 만들고 경계면은 가장 가까운 셀로 상수 외삽한다. 이 규칙은 별도 review gate이며, upstream wall-loss가 선언한 total/per-cell reactive area가 입력 slit 형상과 맞지 않으면 remap을 거절한다. 기준 단면적도 upstream 계산과 정확히 일치해야 한다.

## 2026-10-29 — 다축 피로 piecewise-linear 시간 재구성

`fatigue.critical_plane_piecewise_linear_time_history`를 추가했다. caller가 timed closed tensor cycle 사이를 piecewise linear로 해석한다고 검토하면 유한 plane set에서 FS/SWT vector-chord 또는 minimum-enclosing-circle factor를 계산하고 tensor Frobenius segment rate를 반환한다. 선형 scalar normal 성분의 extrema는 꼭짓점에서 발생하고, 두 shear vector 꼭짓점을 연결하는 선분은 endpoint convex hull 안에 있으므로 선언한 chord/MEC path range가 그 재구성에 대해 정확하다는 경계를 기록한다. 이 API는 측정 사이 실제 물리의 복원, orientation continuum, rainflow 채널 짝짓기, damage/life를 주장하지 않는다. 평가 전 plane/sample work budget을 확인한다. 예제·registry·source basis·schema·API와 유도 문서를 추가했으며, 수치 시험은 실행하지 않았다.

# 2026-10-29: 다축 피로 명시 cycle map 손상 API 연결

`fatigue.explicit_critical_plane_cycle_pair_damage`를 추가하고 registry, capability/source catalog, Python package catalog, JSON Schema와 API/model reference에 연결했다. `examples/model_inputs.json`에는 digest가 고정된 합성 입력을 추가했다. 사용자가 독립 투영 rainflow 결과의 같은 finite plane에서 normal-stress와 engineering-shear-strain cycle index 및 allocation을 직접 대응시킨다. 각 채널 cycle count의 초과 할당과 미배정 count를 확인하며 미배정이 있으면 합계 손상을 보류한다. pair별 FS factor를 caller 보정 shear strain-life support 안에서 계산하고 전체 pairing이 유효할 때에만 선형 Miner 누적량을 반환한다. pairing 자동 추정, 일반 경로 의존 비비례 피로, 재료 자격화는 구현 범위에 포함하지 않는다. 정적 카탈로그/스키마/모델 reference 생성과 101행 소스·AST 경로 감사만 수행했고 계산 테스트와 패키징은 실행하지 않았다.



# 2026-10-29: 전기화학 수송의 분포형 벽 반응 경로

`ElectrochemicalTransport`에 caller 보정 Butler–Volmer 벽 반응을 추가했다. 반응별 조성 kinetics는 기존 support-bounded law를 공유하며, 각 셀의 용액전위를 평가하고 `wall_area_per_volume_m2_m3`와 곱해 signed 종 원장에 적용한다. 벽 provider와 반응표는 tip 표면과 분리 digest로 결속한다. 금속전위 하나를 전체 벽에 쓰는 가정, 벽 반응 조성/기준전위와 flux basis를 별도 review gate로 요구하고 외부 벽 callback과 내장 반응의 동시 적용을 거부한다. 레지스트리 모델 `electrochemistry.restricted_transport_campaign`, 합성 model input, 공개 스키마/카탈로그/모델 참조 및 전용 범위 문서를 연결했다. 소스 기반 101행 감사를 갱신했다. 사용자의 요청에 따라 수치 테스트, 패키징, HPC 제출은 실행하지 않았다.


# 2026-10-29: 피로 cycle pairing 전역 배분 개선

`fatigue.propose_critical_plane_interval_overlap_pairing`의 overlap 점수 기반 탐욕 배분을 연속 cycle-count 용량을 갖는 이분 그래프 min-cost max-flow로 교체했다. 먼저 총 배분 cycle 등가량을 최대화하고, 그 최대유량 중 할당량 가중 interval IoU를 최대화한다. 동률은 원본 cycle index 순서로 결정되며 그래프 후보 수와 flow augmentation 횟수에 별도 예산을 둔다. 예산 초과 시 부분 pairing을 결과로 내지 않고 `out_of_scope`를 반환한다. proposal method ID를 v2로 갱신했다. 이 목적함수는 temporal overlap heuristic일 뿐 물리적 cycle 대응·비비례 피로법칙이 아니며 기존 downstream review gate는 유지한다. 스키마/카탈로그/레퍼런스와 101행 소스 경로 감사는 정적으로 갱신했다. 수치 테스트와 HPC 실행은 요청에 따라 보류한다.


# 2026-10-29: 비선형 Prony 가스켓 조인트 이력 API

`fabrication.nonlinear_gasket_prony_joint_history`를 추가했다. 평형 응력–변형률 backbone과 각 generalized-Maxwell branch의 caller 단조 piecewise-linear backbone, branch relaxation time/초기 내부응력, 비선형 볼트 force-extension curve를 계약화했다. knot 사이 선형 strain 경로가 backbone knot를 지날 때 구간을 분할하고 각 부분구간에서 exponential branch-state update를 닫힌형으로 계산한다. 시간 knot의 단일 자유도 force balance는 지원 범위 안의 bisection으로 풀며 볼트/가스켓 curve 외삽을 거부한다. capability/source registry, four public contracts/schema, 합성 example, API/model reference, 전용 범위 문서 및 partial-scope evidence를 갱신했다. contact opening/recontact, spatial flange field, leakage와 acceptance는 미지원이다. 계산 테스트/HPC/패키징은 실행하지 않았다.


# 2026-10-29: Excel FCGR data import with unreported frequency

S460 Mendeley v2 dataset page reports six CT specimens and CC BY 4.0; the acquired workbook hash is catalog-pinned. The workbook omits test frequency. Added an explicit row/header/column-mapped Excel importer using optional openpyxl, caller-declared SI conversions and rights/applicability lineage. The tabulated crack-growth curve now accepts explicit `frequency_Hz=None`; delta-K versus da/dN-per-cycle query remains available, while load-block life integration and frequency-matched family selection reject unknown frequency. This avoids dropping an open processed dataset or inventing its missing condition. The raw workbook remains outside distribution; attribution and DOI are in `docs/FCGR_WORKBOOK_IMPORT_KO.md`. A six-specimen import profile is stored under `data/profiles/`, and the future release allowlist includes reviewed public profiles while excluding `data/raw`. Regenerate schemas/catalogs statically; no calculation tests or package build requested.

# 2026-10-29: Explicit material/environment gate for crack-growth life

Added target `material_condition_id` and `environment_id` plus an explicit mapping review to single-curve and curve-family life requests. The integrators stop with `needs_data` when the mapping is absent or unreviewed, and return `out_of_scope` when the target differs from the curve or family declaration. Curve-family evaluation propagates the reviewed target into each selected single-curve calculation. Frequency-unknown curves remain usable for delta-K rate queries but cannot pass life integration or family frequency matching. Updated nested examples, API guide and model applicability notes. Generated schemas and catalogs statically; no tests or package build were run.

# 2026-10-29: Knotwise unilateral nonlinear gasket contact history

Added `fabrication.unilateral_nonlinear_gasket_prony_joint_history` as a separate single-degree-of-freedom history API based on the existing caller-calibrated nonlinear Maxwell/bolt curves. It enforces zero gasket force at zero compression, records open/reclose transitions at supplied time knots, and freezes Maxwell branch state while separated under an explicit review gate. The model does not locate transition times between knots and does not calculate flange fields, leakage or sealing acceptance. Registry, source derivation, synthetic input example, schema, model reference and scope documentation were connected. No tests, HPC work or packaging have been run.

# 2026-10-29: Self-consistent Davies activity/speciation coupling

Added chemistry.aqueous_davies_self_consistent_speciation. It wraps the caller-defined square aqueous mass-action system in a damped log-gamma fixed-point loop, converts mol/L to molality using an explicit caller-supplied kg-water/L-solution factor, recalculates Davies coefficients from the complete species inventory, and checks both charge residual and the declared ionic-strength ceiling (maximum 0.5 mol/kg water). It preserves inner solver and iteration diagnostics and withholds results when the fixed point does not converge. Registry, synthetic example, source/capability catalogs, public schema, API reference, method note and wet-CO2 scope audit were added or refreshed. Multiphase equilibria, automated species networks, kinetic scale response and Pitzer/SIT remain out of scope. No tests or package build were run.

# 2026-10-29: Spatial flange/gasket contact field from caller compliance

Added 
abrication.flange_contact_field, a bounded contact calculation that consumes a caller-provided symmetric positive-semidefinite relative flange compliance matrix, composed no-gasket closure vector, per-node gasket stiffness and contact area. It solves the unilateral complementarity conditions with a deterministic active set, checks operator support, and enforces a cubic dense-solve work budget. Output retains response-provider digests and nodewise force, mean pressure, compression and gap. This does not generate an FE flange response, local contact stress, leakage or seal acceptance. Added a synthetic example, public schema, source/capability registration, API reference and scope documentation. No tests or package build were run.

# 2026-10-29: Caller-calibrated single-phase scale kinetics

Added chemistry.caller_surface_scale_kinetics for one identified scale phase. Caller supplies constant saturation ratio per ordered interval, separate precipitation/dissolution molar-flux coefficients and orders, initial uniform thickness, phase molar volume, condition/source lineage and review gates. Dissolution cannot exceed the current inventory; net area-specific amount maps to a volume-equivalent thickness. No phase equilibrium, protection credit, corrosion rate or life is inferred. Added registry, synthetic example, public schemas, source/capability links, API reference and an applicability note. No tests or package build were run.


# 2026-10-29: Layered scale diffusion bound and scale-history adapter

Added `chemistry.layered_scale_diffusion_limit` for caller-defined steady diffusion resistance through an ordered scale-layer stack plus a bare solution film. A layer contributes `L/(D_eff K)` where `K` is the reviewed solution-to-layer concentration partition coefficient. Covered and bare-area fluxes are mixed in parallel from a caller-declared coverage fraction, and the transported-species flux is converted to a Faraday-equivalent diffusion-limited current bound. The transport calculation does not infer coverage or morphology, actual reaction current, metal loss or a protection factor; a separate history-binding adapter can now apply an explicitly reviewed caller thickness-to-coverage relation at one recorded time knot.

Added `layered_scale_transport_request_from_history()` and typed `ScaleHistoryTransportLink`. The adapter accepts only a computed scale-kinetics `AssessmentResult`, matching physical scope, substrate/solution conditions and phase identity. It binds an exact recorded time knot to one uniquely identified caller transport layer, retains the complete result digest and review declaration, and performs no time interpolation or inference of layer properties. Extended the adapter with an optional caller-reviewed thickness-to-coverage relation, `1-exp(-(thickness/characteristic_thickness)^exponent)`, whose parameters and selected-knot result digest are preserved in the bound scale-state identity. This is an explicit user model and not an inferred morphology law. Public schema export and static source audit succeeded; no numerical tests or package build were run.


# 2026-10-30: Sequential crevice geometry/transport campaign

Added `CreviceGeometryTransportCampaign` and `solve_crevice_geometry_transport_campaign()` to run the existing conservative restricted-transport calculation over a digest-pinned aperture history. Geometry knots must coincide exactly with the transport output clock and share the fixed reference cross-section, cell count and axial length. Each interval uses the left-knot geometry; callbacks receive campaign-global time. At every geometry boundary, concentration is rescaled by old/new cell volume so per-cell species inventory is conserved. The output retains per-segment results and pre/post remap states, sums mouth/tip/homogeneous/wall ledgers and rechecks the campaign-wide species balance. A failed segment returns its successful prefix and failing result; a campaign-wide balance failure prevents an overall computed status. This is one-way operator splitting: geometry recession remains an independent input and is not inferred from transport; moving-boundary substeps, momentum, multiphase chemistry and physical qualification remain absent. Added typed schema, source/capability interface and dedicated scope documentation. No tests or package build were run.

# 2026-10-30: Spatial Prony gasket contact history and caller-tabulated aqueous activities

Added `fabrication.flange_viscoelastic_contact_history`: caller-supplied per-node equilibrium and Maxwell branch moduli, relaxation times, initial branch state, gasket area/thickness, flange relative-compliance matrix and knotwise free-closure histories are coupled through a unilateral contact solve. Branch states use the exact exponential update for each declared linear strain segment. The initial knot is defined as an instantaneous load from a reviewed zero-compression state. Contact is solved only at supplied knots; nonlinear spatial viscoelasticity, within-interval transitions, flange FE response generation, leakage and sealing acceptance are not included.

Added `chemistry.aqueous_tabulated_activity_speciation`: species-specific caller tables map ionic strength to positive activity coefficients; `ln(gamma)` is interpolated linearly in ionic strength within the declared finite support and coupled iteratively to the existing general aqueous mass-action equations. The request preserves table/provider digests and temperature/solvent/species mapping review. It does not fit, extrapolate or qualify a thermodynamic model, or add multiphase chemistry.

Both APIs have synthetic JSON inputs, exported Pydantic contracts, registry/capability/source registration, API-reference entries and Korean method notes. Static catalogs now record 341 calculations, 141 interfaces, 583 capabilities and 716 schemas. The partial-scope audit links 316 components across 215 source paths with zero missing or unmapped paths/symbols. These are registration and source-trace checks only. No tests or package build were run.

# 2026-10-30: Explicit cubic-Hermite reconstruction for closed tensor work-life

Extended `fatigue.closed_tensor_work_life` with an optional caller-selected cubic-Hermite path representation. Each cycle must then include strictly increasing sample times plus six-component stress and strain time derivatives at every sample, and a separate reconstruction review. The segment work `integral(sigma : d epsilon)` is evaluated exactly as a finite polynomial product; endpoint state closure and the existing same-condition work-life calibration gates still apply. Piecewise-linear input remains the default. Slopes are never estimated, and this extension does not identify cycles or add a universal multiaxial damage law. Updated the synthetic example, public schema/API reference, method note and scope audit. Static catalog/schema/source audit generation completed. No tests or package build were run.

# 2026-10-30: Spatial nonlinear Maxwell gasket contact history

Added `fabrication.flange_nonlinear_viscoelastic_contact_history`. A shared caller nonlinear gasket equilibrium backbone and branch-specific monotone Maxwell backbones are combined with per-node areas/thicknesses, initial branch states, knotwise free closure and a caller flange-compliance operator. Branch state advances over piecewise-linear strain intervals with exact exponential updates split at backbone knots. At each declared knot, a bounded active-set Newton solve enforces compression-only contact; the local constitutive tangent is estimated within caller support and must remain positive. The initial knot is an instantaneous load from the reviewed zero-strain branch state. Nonpositive tangent, unsupported strain, inability to produce positive traction, residual failure, or work-budget exhaustion fails closed. The model does not generate flange FE response or infer transitions between knots, leakage, sealing or acceptance. Added synthetic input, public schema, registry/catalog entry and Korean method note. Static catalogs record 342 calculations, 141 interfaces, 584 capabilities and 717 schemas. Source audit found 317 linked components across 215 paths with no missing or unmapped symbols. No tests or package build were run.
# 2026-10-30 — CO₂ campaign wall metal-loss 연결

`Co2CorrosionCampaign.wall_metal_loss_selection`을 추가해 기존 `coupled_wall_metal_loss` adapter를 CO₂ campaign 결과 경로에 연결했다. Wall reaction set의 선택 금속 종 존재와 참조 단면 일치를 확인하고, 완결된 solver wall species ledger를 caller 몰질량·밀도·reactive area 기준으로 signed area-average recession에 매핑한다. Tip reaction 기반 용출 결과와 wall ledger 결과를 따로 반환하고 `metal_loss_results`로 함께 제공한다. Wall 변환을 요청한 경우 해당 변환이 미완료면 campaign 상태를 함께 제한한다. 이는 net signed wall transfer 요약이며 local thickness field, 자격화 corrosion rate, moving geometry나 acceptance는 아니다. 계산 시험 및 패키징은 보류했다.

# 2026-10-30 — Wall 금속손실 기준 명시

기존 coupled wall metal-loss 결과에 `wall_transfer_basis=solver_integrated_signed_species_ledger`와 `current_efficiency_factor_applied=false`를 명시했다. Wall 변환은 전류에서 용출량을 추정하지 않고 solver-integrated signed species amount를 직접 금속량으로 바꾼다. 따라서 tip의 `DissolutionSelection.dissolution_current_efficiency`나 gross-anodic 해석을 wall ledger에 중복 적용하지 않는다. 설명서에도 두 경로의 구분을 추가했다. 계산시험은 보류했다.


## 2026-10-30: Scale-history series binding

Added `ScaleHistoryTransportSeriesLink` and `bind_scale_history_series_to_transport()` so callers can bind every strictly increasing scale-kinetics history knot to the same selected layer and base transport request in one operation. Each returned request retains the complete result lineage and applies the optional caller-reviewed thickness-to-coverage relation at that exact knot. The adapter rejects missing, malformed, nonfinite, negative, duplicate or unordered knot times and does not interpolate or invoke transport. Added `evaluate_scale_history_transport_series()` to run the registered steady layered diffusion model independently at each exact knot, return digest-pinned `AssessmentResult` objects directly consumable by `ScaleLimitedSurfaceFlux`, retain full request/result/provider/source/condition and knot-state digests, and withhold a complete result if any knot is unresolved. Exported the public input schema and updated interface/source/capability references. Schema export produced 721 contracts; static scope audit reports 101 rows, 321 components, no missing paths and no unmapped symbols. Numerical tests remain deferred.

The scale-history-to-transport binding now also requires exact equality of condition digests, in addition to matching physical scope and condition identifiers. This prevents a same-name but differently parameterized solution or substrate condition from being silently linked. The source catalog and API documentation record the stronger lineage gate. Static source audit was refreshed; numerical tests remain deferred.

The scale-history adapter now verifies both the scale calculation's input digest against its recorded inputs and the enclosing `AssessmentResult` digest against model ID/version, inputs and run context before binding a knot. This closes a lineage gap where a caller could alter returned scale values while retaining stale digest fields. Catalogs and API guidance were updated; execution tests remain deferred.
## 2026-10-30 — caller stateful multiaxial damage integration

`CallerStatefulMultiaxialDamageRequest`와 `evaluate_caller_stateful_multiaxial_damage`는 caller가 정의한 dimensionless state evolution과 nonnegative damage-rate를 고정 최대 시간간격 classical RK4로 적분한다. Cycle tuple 순서와 정수 cycle count가 sequence를 정하며 state는 반복·cycle 사이에서 이어진다. Callback의 absolute sequence time은 각 cycle의 local sample time과 sequence offset을 합성한다. 코드 검토에서 offset을 RK4 substep마다 전체 interval duration만큼 증가시키던 오류를 수정했고, offset은 interval 내에서 그대로 두며 cycle repetition 종료 때 실제 cycle duration으로 한 번 증가시킨다. Callback identity 변화, state bounds 이탈, provider 오류, damage/time overflow와 evaluation budget 초과는 computed aggregate로 내놓지 않는다. Cycle별 결과에 누적 sequence start/end, 첫·마지막 반복 손상 및 최초·첫 반복 후·최종 state checkpoint를 추가해 순서 효과를 압축 기록한다. 이 변경은 code review 결과이며 수치 회귀·step convergence·피로법칙/재료 자격화는 실행하지 않았다.



## 2026-10-30 — deterministic saturation-index intervals

Extended `SaturationScreenSpecies` and `CandidateSolid` with optional, caller-reviewed absolute bounds in log10 activity and log10 solubility-product space. For positive stoichiometric exponents, the implementation propagates a conservative symmetric interval by the triangle inequality and reports lower/upper saturation-index bounds plus a three-way deterministic classification. The arithmetic rejects nonfinite interval endpoints and never converts the interval into a probability or confidence claim. Added explicit field descriptions and dimensionless output units. Schema, capability/source catalogs, model reference and continuation/API guidance were refreshed. This is code and contract work only; numerical tests, chemistry validation and packaging remain deferred.

The saturation interval extension now has two independent review gates. Nonzero activity bounds require `activity_interval_bounds_reviewed`; nonzero solubility-product bounds require `solubility_product_interval_bounds_reviewed`. Both default false for backward-compatible zero-bound inputs. If a nonzero bound lacks its review, the calculation returns `needs_data` and does not report a saturation interval class. This prevents unreviewed caller values from being presented as a definite interval result. Tests remain deferred.

The `screen_mass_action_calculation()` adapter now accepts `activity_log10_absolute_bounds` keyed by upstream species ID. If supplied, its key set must equal the full upstream species set, preventing silent omission or misapplication. The per-bound review flag remains explicit; bounds without review return `needs_data`. This closes the direct-request versus composed-API gap without treating point-valued upstream activities as having an inferred uncertainty. Numerical tests remain deferred.

Saturation-screen results now echo both the caller's `review_flags` and the per-input `review_requirements` (including whether interval reviews were required). These appear on computed and noncomputed calculation returns through the common result base, so downstream consumers do not need the original request merely to see review state. Flags remain caller declarations, not independently verified evidence.

## 2026-10-30 — transient CO2 mixture history exchange

Added `Co2MixtureFugacityHistory` as a versioned exchange contract for aligned measured/predicted PSA-like gas histories. It retains case/input/source/solver identities, asset/location/stream, a strict sample clock, total absolute pressure, temperature, explicit component order, per-sample mole fractions and validity. Valid rows require finite in-range fractions that sum to one within caller-declared tolerance and a positive CO2 fraction. The adapter `co2_mixture_fugacity_requests_from_history()` emits one review-gated CoolProp mixture request for each valid sample while retaining invalid rows as `needs_data`; it performs no EOS call or aqueous/corrosion inference. Added a synthetic mapping example, public schema, capability interface row, API docs and a grounded PSA-Dyna extension request. Tests and live PSA-Dyna/CoolProp integration remain deferred.
The transient gas-history contract now permits `None` for pressure, temperature and individual composition values on source-invalid rows, preserving explicit missingness with the original sample ID/time and validity mask. Valid rows still require complete finite state and normalized composition before any CoolProp request is emitted. The synthetic example now includes a missing invalid sample. This is contract-shape and adapter work only; no numerical EOS run was performed.
## 2026-10-30 — CO2 혼합 기체 이력의 명시적 CSV 입력기

`read_co2_mixture_history_csv()`를 추가했다. caller가 sample ID, 초 단위 시간, 절대 Pa, K, 유효성 열과 성분별 몰분율 열을 명시해 원본 UTF-8 CSV bytes를 `Co2MixtureFugacityHistory` 계약으로 읽는다. 원본 bytes SHA-256을 기록하며 단위 추정, 조성 정규화, 잘못된 값의 보정은 하지 않는다. 유효하지 않다고 표시한 행은 빈 압력·온도·조성 값을 nullable로 보존하고, 시간은 반드시 있어야 한다. API 문서에 열 단위와 동작을 기록했다. 런타임 테스트, 외부 공정자료 연결, 실제 CoolProp 호출은 수행하지 않았다.

## 2026-10-30 — 공개 N₂-PSA 공정 데이터 구조 감사

FH Münster의 Mendeley N₂-PSA 데이터 기록에서 provider API의 파일 메타데이터를 확인하고, CC BY 4.0 표시가 있는 65,405-byte workbook을 provider SHA-256과 대조해 `data/raw`에 보관했다. workbook은 단일 sheet의 520 data rows와 18 columns를 가진 설정·주기·결과 표이며 시간별 transient 이력이 아니다. 데이터 카탈로그, acquisition log, aggregate inventory를 갱신했다. experimental/simulated row별 구분과 독립 run 계층은 사용하지 않았고, CO₂ 부식 적합성이나 개별 관측 재사용 권리를 추론하지 않는다. 원출처: https://doi.org/10.17632/d2vx7w6x74.1.

## 2026-10-30 — PSA-Dyna cycle-mean CO₂ fugacity bridge

`co2_mixture_fugacity_requests_from_psa_dyna_mean_stream()` now consumes the public `dynamic-psa-mean-stream/v1` wrapper and its `dynamic-psa-dwsim-mean-stream-input/v1` payload for explicitly selected streams. The adapter validates declared units and component ordering, converts bar to Pa only after an explicit caller review of the absolute-pressure basis, and requires independent composition/EOS/single-gas-phase reviews before marking a request ready. It preserves upstream status/release flags, case/result/source-archive hashes, and canonical digests of both upstream report and mean payload in `PSADynaMeanStreamFugacityBatch`. Missing phase-aligned P/T remain `needs_data`; missing CO2 or invalid state remains `out_of_scope`. The contract is explicitly cycle-mean and not a corrosion-boundary qualification. Added public schemas, capability row, API/extension documentation and a synthetic request example. Tests and CoolProp execution remain deferred.

## 2026-10-30 — PSA-Dyna report file reader와 raw digest

`load_co2_mixture_fugacity_requests_from_psa_dyna_mean_stream()`를 추가해 사용자 지정 JSON 경로에서 upstream report bytes를 읽고 UTF-8 JSON object를 검증한 뒤 기존 typed adapter에 넘긴다. 파일 byte SHA-256과 canonical report digest를 별도 필드에 저장한다. JSON 내부의 case/result paths를 resolve하거나 원본 파일을 자동 재열지 않는다. 공개 schema, capability interface와 API/extension 설명을 동기화했다. 계산·CoolProp 테스트는 실행하지 않았다.

## 2026-10-30 — 경쟁 중성 고체상 평형 API

`chemistry.competitive_solid_equilibrium`은 caller가 선언한 공통 액상 종과 둘 이상의 중성 순수 고체상 사이의 고정-gamma 평형 후보를 계산한다. 각 침전 반응의 charge/element balance, 최종 용액농도와 고체량의 비음수 제약을 검증하고 SLSQP로 dimensionless Gibbs potential을 최소화한다. 종료코드 외에 상 존재 시 포화 equality, 고체 부재 시 saturation inequality, complementarity residual 및 농도 extent balance를 모두 확인하며 미달 시 `out_of_scope`를 반환한다. candidate phase set 완전성·고정 활동도·온도 적용성·단일 액상/고정 부피 가정은 명시 review gate다. 자동 speciation·activity iteration·kinetics·surface protection은 제공하지 않는다. 공개 schema, registry model, capability/source catalog, 합성 입력 예제와 한글 방법서를 추가했다. 수치·화학 검증은 실행하지 않았다.


## 2026-10-30 — 경쟁 고체상 caller-rate 수지 ledger

`CompetingSolidKineticLedger`에 상별 signed extent-rate 입력과 연속 구간 시간 이력을 구현했다. 중성 고체 생성 반응은 caller 선언 조성으로 전하·원소 보존을 확인한다. 구간 갱신은 고체 재고량 한도 내 용해를 우선 적용한 다음 동시 침전 요청을 공통 용액 반응물 계수로 제한하며, 각 knot에 초기 대비 inventory 잔차와 적용 extent를 기록한다. Registry가 모듈을 찾던 위치를 고쳐 root package의 계산 모듈로 등록했다. API 안내, 4개 공개 contract schema, wet-CO₂ capability/source catalog, 구현 감사, 합성 계약 예제를 연결했다. 속도식 추정·상 선택·포화/평형·수송 연성은 추가되지 않았다. Schema/capability/model-reference 생성은 완료했고 수치 실행, 테스트 및 패키징은 사용자의 순서 지시에 따라 미실행이다.

## 2026-10-30 — 다상 kinetics ledger의 고정 형상 transport 연동

`CompetingSolidKineticTransport`와 `solve_competing_solid_kinetic_transport()`를 추가했다. caller 입력의 interval clock를 `RestrictedTransportRequest.output_times_s`에 정확히 맞추고, phase extent rate를 상×cell 단위의 SI 배열로 받는다. 각 구간의 solver callbacks는 interval-local clock에서 campaign 절대시간으로 이동한다. 고정 형상 수송을 먼저 계산한 뒤 수송 종료 농도에서 cell별 `CompetingSolidKineticLedger`를 적용하며 aqueous concentration와 phase inventory를 다음 구간에 전달한다. 고체 반응망의 종 ID, 양론, charge 및 elemental balance를 공통 validator로 검증하도록 재사용 경로를 정리했다. Campaign-level aqueous balance에는 누적 transport 및 kinetic source를 별도로 넣고 cellwise wall ledgers와 upstream provider/configuration/source digests도 보존한다. 이는 구간 끝 operator split이며 rate provider·상평형·activity-feedback을 제공하지 않는다. API/schema/catalog/source/audit/method docs와 합성 Python wiring 예제를 갱신했다. 스키마·catalog 생성만 수행했고 transport·kinetics 수치 실행, 테스트와 패키징은 미실행이다.

## 2026-10-30 — 경쟁 고체상 caller-rate ledger의 공간 transport 조합 API

단일 고체 equilibrium projection에 종속되지 않도록 별도 `CompetingSolidKineticTransport` typed interface를 추가했다. `RestrictedTransportRequest` clock에 맞춘 셀별/상별 속도를 받고, 각 transport interval 끝에서 다상 inventory ledger를 적용한다. callback 시간 offset과 transport/kinetic 수지원을 분리해 기록하고, 초기 및 구간별 phase inventory, 벽 source ledger, 결과 digest를 보존한다. 별도의 `integration.*` interface로 노출해 callback이 필요한 API를 입력만으로 계산되는 `ModelRegistry.run()` 계산기로 잘못 표시하지 않았다. 독립 문서·합성 실행 예제·공개 schema 4개·source/capability 및 implementation audit 연결을 갱신했다. 생성기 임포트·schema/capability catalog 생성은 완료했으나 예제/solver 수치 실행, 테스트, package build는 실행하지 않았다.

## 2026-10-30 — 셀별 다상 transport 실패 경계 보강

직전 operator-split API의 실패 경로를 소스 검토로 보강했다. phase update와 transport source ledger를 구간 임시 상태에서 먼저 검증한 뒤 모든 cell이 성공할 때만 campaign state에 commit하도록 바꿨다. 중간 cell이나 ledger failure에서는 앞서 완료한 knot의 aqueous/solid/source prefix를 유지하고, 실패 구간은 `partial_step`으로 따로 반환하며 다음 구간을 수행하지 않는다. `physical_scope_id`를 campaign 입력에 추가하고 kinetics scalar record budget을 제한했다. Schema·capability·source·구현 감사 생성은 다시 완료했고, cell solver 계산 및 테스트/패키징은 아직 수행하지 않았다.

## 2026-10-30 — 공간 비선형 gasket 접촉의 caller 검토 transition sampling

`fabrication.flange_nonlinear_viscoelastic_contact_history`에 `maximum_contact_transition_step_s`와 명시적 보간 검토 gate를 추가했다. 원래 시간점 사이 자유 닫힘량을 선형 보간하고 생성 입력을 Pydantic 계약으로 재검증한 뒤 knotwise 접촉해를 계산한다. 인접 sampled contact state 변화만 bracket으로 보고하며 정확 event root나 한 bracket 내 복수 변화를 해석하지 않는다. 시간 knot 예산은 10,000개로 제한하고 비유한/과대 step ratio를 ceil 전에 거절한다. 결과 단위, method note 및 synthetic API wiring 예제를 연결했다. 테스트 및 패키지 빌드는 실행하지 않았다.

## 2026-10-30 — 경쟁 고체 평형과 Davies 활동도 반복 결합

새 `CompetitiveSolidDaviesIteration` contract와 `chemistry.competitive_solid_davies_equilibrium` API를 추가했다. caller가 명시한 고정 부피 단일 액상·완전 종 목록·전하/원소 보존 경쟁 중성 고체 set 및 Ksp를 기존 Gibbs extent optimizer에 공급하고, 액상 mol/m³에서 kg-water 기준 molality로 변환한 이온강도로 Davies gamma를 damping 반복한다. inner phase inequality, complementarity/KKT 및 extent balance 결과와 outer fixed-point residual, provider/config/record digest를 보존한다. Davies 최대 0.5 mol/kg ceiling, charge tolerance, temperature/solvent/water conversion/phase scope review를 요구한다. 자동 speciation 구성, kinetics, 고농도 활동도, scale evolution과 corrosion law는 구현하지 않는다. 문서와 synthetic example을 추가했으며 numerical tests/package build는 실행하지 않았다.

## 2026-10-30 — 셀별 경쟁 고체상 평형과 수송 operator split

`CompetitiveSolidEquilibriumTransport`와 `solve_competitive_solid_equilibrium_transport()`를 추가했다. 각 output interval을 고정 geometry에서 `solve_restricted_transport()`로 풀고, 그 결과로 cell별 aqueous concentration과 phase inventory를 갱신한 뒤 caller가 나열한 경쟁 중성 고체상 Davies equilibrium을 적용한다. 초기 projection부터 phase source(침전 extent의 반대 부호), transport mouth/tip/homogeneous/wall ledgers와 aqueous inventory residual까지 보존한다. transport activity provider/config digest는 Davies phase 설정과 같아야 하며, caller의 activity callback 연결 review를 요구한다. callback이 포함된 API라 capability catalog의 interface로 기록하며 registry 입력 전용 calculator로 위장하지 않는다. 완전 동시 연성, kinetics 및 moving geometry는 제공하지 않는다. contract 예제·schema·API/method note·source/capability/audit 항목을 연결했다. numerical tests/package build는 실행하지 않았다.


같은 개발 단계에서 transport와 phase 입력 종 ID 집합의 완전한 일치, charge vector 필수 조건, physical scope ID 및 종/상 record budget을 추가했다. 각 interval의 phase update와 transport source ledger 검증을 임시 상태에서 마친 뒤 전부 유효할 때만 commit하며, failure 시 완료 prefix/partial step을 보존한다. 정적 source 감사는 이 변경 뒤 다시 생성한다.

2026-10-30 코드 대조 수정: `planar_slit_aperture_history`에서 signed recession 부호가 다른 crevice feedback API와 반대로 적용되어 있었다. 양의 recession은 금속 제거·간극 증가, 음의 recession은 재석출·간극 감소로 일관되도록 `initial_aperture + face_count * recession`으로 수정했다. 공개 schema/catalog와 implementation scope 정적 감사(101행, 225 경로, 338 구성요소)를 재생성했다. 계산 시험은 지시대로 실행하지 않아 방향 동작은 아직 수치 검증 전이다.
2026-10-30 activity table→transport 연동: 기존 `AqueousTabulatedActivityIteration` 표를 restricted transport의 Nernst–Planck activity callback으로 재사용하는 `build_tabulated_activity_transport_callback()`를 구현했다. 종 ID와 순서, system 온도, 종×위치 농도 shape, 비음수·유한성, mol/m³→molality 물 환산, 이온강도 상한 및 표 외삽 금지를 확인하고 request의 provider/configuration/record digest lineage를 callback에 부여한다. 공개 capability interface, API/범위/재개 문서를 추가했다. 이 조합은 gamma 표 적용이며 전해질 모델·확산 보정·전기화학 자격화를 의미하지 않는다. 수치 테스트는 지시대로 미실행이다.

2026-10-30 전기화학–경쟁 고체상 수송 연동: `solve_electrochemical_transport()`의 선택 phase adapter가 기존 단일 고체상 request 외에 `CompetitiveSolidEquilibriumTransport`도 받도록 연결했다. Caller 반응망 source와 electrode tip/wall kinetics를 고정형상 transport 구간에 전달하고 각 output knot에 cellwise competing-neutral-solid Davies projection을 적용한다. 초기 phase/transport species의 원소 구성과 transport 요청 일치 검사는 유지한다. capability interface 및 한글 범위 설명을 추가했다. 이 기능은 output-clock operator split이라 phase kinetics·자동상 선택·moving geometry·완전 연성 해석을 의미하지 않는다. 수치 계산 검증은 보류했다.

2026-10-30 gasket contact-transition refinement: nonlinear Maxwell gasket/flange contact now has optional replayed-path bisection for an already observed contact-state transition. The request declares a target bracket width, sampled max step, interpolation review, a one-transition-per-refined-interval-per-node review, solve count and aggregate replay-work budgets. Every midpoint and replay request digest is returned; failed/budget-exhausted refinement is not promoted to a computed refined event. It does not find transitions hidden inside the sampled maximum step or establish an exact root. Updated public contract schema, catalog, documentation and static scope evidence. No numerical tests or package build were run.


2026-10-30 gasket transition budget edge-cases: contact replay now counts work from failed solver replays before reporting; sets `transition_refinement_complete=false` for failed/budget-exhausted refinements; and explicitly returns out_of_scope when a midpoint is unrepresentable or the 10,000-knot limit prevents insertion. Generated 760 schemas and registry catalogs successfully; static scope audit is 101 rows / 225 paths / 340 components with zero missing or unmapped entries. No numerical execution or tests were run.

2026-10-30 gasket replay budget correction: aggregate work-unit totals now include solver replays that return a non-computed status when they expose a valid work count. Every early refinement failure sets `transition_refinement_complete=false`; an adjacent floating-point bracket with no representable midpoint and a full 10,000-knot replay path fail as out_of_scope. Public schema/model catalogs regenerated; static audit is current at 101 rows, 225 paths, 340 components, zero missing/unmapped. No numerical solver run.

2026-10-30 scale inventory boundary fix: dissolution-limited scale thickness is clamped to nonnegative inventory at each interval boundary. This prevents floating-point residue after complete dissolution from creating a negative available inventory and reversing the next dissolution increment. Numerical tests remain deferred by instruction.

2026-10-30 gasket structure-response composition: the nonlinear Maxwell contact-history API now accepts optional caller-supplied flange compliance matrices aligned to each time knot. Reviewed componentwise linear interpolation is carried through max-step sampling and transition replay, and each evaluated matrix is checked for symmetry and positive semidefiniteness before solving. Results record history usage and the minimum eigenvalue observed. The fixed-matrix request remains supported. Tests and package work remain deferred.

2026-10-30 gasket compliance lineage refinement: each time-history row now records the digest of the exact flange compliance operator and that knot's minimum eigenvalue, while the aggregate retains the minimum over the full history. This makes matrix interpolation/replay inputs auditable at the response-knot level. Public contract export and model reference regenerated; static scope audit reports 101 rows, 225 source paths, 340 components, with no missing or unmapped items. Numerical tests remain unrun.

2026-10-30 gasket operator consistency: compliance matrices accepted within the declared symmetry tolerance are explicitly symmetrized before residual/Jacobian use, aligning the actual contact operator with the PSD check. Response lineage identifies the digest of the symmetrized operator; outputs expose the operation. No numerical tests were run.

2026-10-30 mass-action callback contract hardening: reject negative/nonfinite species-by-cell concentrations and negative/nonfinite evaluation time before evaluating concentration powers. The generated callback now exposes stable provider ID/revision, network ID, species order and its canonical configuration digest for downstream composition provenance. Numerical tests remain deferred.

2026-10-30 crevice callback lineage: segment time-shift wrappers now preserve allowlisted callback provider/revision/configuration, reaction-network ID/species order and activity-provider metadata, and expose the segment's global-time offset. This keeps caller callback provenance available after local-to-global clock composition. Tests remain deferred.

2026-10-30 crevice segment lineage output: each segment result now includes a role-keyed callback lineage map containing available provider/configuration/network/species metadata, the campaign global-time offset and a canonical digest for each callback identity mapping. This makes the local-to-global callback composition inspectable in persisted campaign output. Tests remain deferred.

2026-10-30 gasket API usability: add a standalone synthetic wiring example for knotwise time-varying flange compliance. It preserves the unchanged canonical fixture, scales its matrix per declared knot, and sets the explicit interpolation review. Documentation states those factors are synthetic and the example has not been executed as a numeric validation.

2026-10-30 stateful multiaxial damage integration: retain the default fixed-step classical RK4 and add opt-in adaptive step-doubling with one-full/two-half RK4 error estimation across state and cumulative damage. Caller declares separate absolute/relative tolerances, min/max step and rejection/evaluation budgets. Adaptive use requires explicit numerical-control review and review that provider reevaluation is deterministic. Results record method, error ratio and step counts; docs and synthetic wiring example updated. Numerical tests remain deferred.

2026-10-30 stateful fatigue adaptive integration: preserved fixed RK4 compatibility and added opt-in one-full/two-half RK4 error control, dimensionless state and damage tolerances, bounded min/max step, rejection/evaluation budgets, and explicit review of adaptive settings plus deterministic callback reevaluation. Expanded the synthetic example to wire both methods; exported the updated request schema and model reference. Static source audit passed; numerical calculations/tests and packaging were not run.

2026-10-30 stateful fatigue integration diagnostics: endpoint evaluation now lands exactly on each declared path sample. Per-cycle results expose provider evaluations and adaptive accepted/rejected steps plus the cycle-local maximum error ratio, alongside the sequence aggregate counters. Numerical tests remain deferred.

2026-10-30 stateful fatigue integration diagnostics: endpoint evaluation now lands exactly on each declared path sample. Per-cycle results expose provider evaluations and adaptive accepted/rejected steps plus the cycle-local maximum error ratio, alongside the sequence aggregate counters. Numerical tests remain deferred.

2026-10-30 adaptive RK4 rejection lineage: persist bounded per-attempt rejection records with global sequence time, cycle/repetition/interval identity, attempted and proposed next step, state/damage error ratios and rejection reason. The caller-declared record cap fails closed rather than truncating the history; success and failure results pin the ordered rejection ledger with a canonical digest. Public request schema and API documentation updated; tests remain deferred.

2026-10-30 adaptive rejection audit correction: compute the proposed next step before serializing a rejected-error record; the prior order could raise on the first tolerance rejection. Centralize integration diagnostics and include the same provider-evaluation, accepted/rejected, tolerance, ledger and digest fields on downstream failures after integration begins. This closes missing lineage on elapsed-time, damage-aggregate and final provider-identity exits. No numerical tests were run.

2026-10-30 cycle-local adaptive rejection lineage: each completed stateful multiaxial fatigue cycle now stores its adaptive rejection records, global half-open ledger index range and a cycle-local canonical digest. Repeated cycle IDs remain distinguishable by their independent result rows and sequence ledger indices. Numerical tests and packaging remain deferred.

2026-10-30 implementation backlog progress semantics: clarify that the original 13 code-incomplete rows are an initial classification and four currently retain wider partial-domain scope despite having bounded calculations. Explicitly prohibit summing heterogeneous capability rows into a single implementation percentage. Regenerated the public Korean backlog from its source data; no execution tests or package builds were run.

2026-10-30 crevice interval-rate history: preserve the legacy constant-rate contract while allowing caller-supplied start/end net species source rates under an explicit linear-interpolation review gate. Integrate the declared linear trajectory by its exact trapezoidal integral, retain species-aligned endpoint and average-rate lineage separately from the backwards-compatible amount-change map, and reject nonfinite or misaligned endpoints. If finite endpoints overflow during integration, withhold affected increments as null diagnostics and return out-of-scope without passing infinity into the result contract. Updated synthetic contract input, public schemas/reference, capability metadata and Korean method/API notes. Numerical tests and packaging were not run.

2026-10-30 crevice derived-value finite support: guard amount-to-concentration conversion and signed charge-inventory aggregation against overflow, including integer charge values outside floating-point range. Failure results retain finite inventory/rate lineage and explicit affected time/species indexes while omitting nonfinite derived arrays and imbalance claims. The public model reference and capability output units were refreshed; numerical tests remain deferred.

2026-10-30 crevice inventory reconciliation lineage: hash the ordered initial species/charge inventory, time-volume history, rate-interval records and provider supports, then bind their canonical digests in a composite inventory-lineage digest. Successful results add the cumulative net species source and the arithmetic final-minus-initial-minus-source residual per species; aggregate overflow returns out-of-scope. Documentation explicitly says this residual is traceability, not independent physical validation. Numerical tests and packaging remain deferred.

2026-10-30 crevice state-boundary ledger: add a digest-pinned per-interval audit row with ordered interval ID/index, start/end clock and solution volume, plus start/end inventory and concentration digests and integrated-source digest. This compact ledger ties returned knot histories to interval transitions without duplicating species arrays. Public model-reference and capability output descriptions were regenerated; no calculation tests were run.

2026-10-30 crevice interval atomicity and failure prefix: calculate every species increment into temporary per-interval proposals, then commit all species together only when all increments are finite and inventory remains in scope. On failure, retain the failed interval's rate diagnostics and ID while returning only the aligned last-completed-knot inventory prefix with a digest; no species from the failed interval is committed. Numerical tests remain deferred.

2026-10-30 crevice exposure-condition path: add optional interval endpoint temperature and gap values with an explicit linear-path review gate, preserving the original single-condition interval form. Validate both endpoints against the provider's rectangular support and expose start/end support findings and endpoint values in interval diagnostics. This only checks the declared exposure path; it does not derive or interpolate provider rates. Updated the synthetic input, schemas, model reference, capability catalog and API/scope notes. No numerical tests were run.

2026-10-30 crevice condition history output: emit a time-ordered interval exposure ledger with start/end temperature and gap, interval deltas, support ID and provider state/record digests. Pin the ledger independently and include it in the composite inventory lineage so condition evidence is available in failed as well as completed calculations. The ledger records caller inputs; no thermochemical rate is inferred from the conditions.

2026-10-30 crevice boundary-condition jumps: construct an n+1 knot ledger that preserves left/right temperature and gap at every shared interval boundary. A boundary discontinuity beyond the recorded comparisons (relative tolerance 1e-12, temperature absolute tolerance 1e-12 K, gap absolute tolerance 1e-15 m) requires explicit review on the following interval; first/last external boundaries are represented as single-sided values. The knot ledger receives its own digest and is included in inventory lineage. These tolerances classify continuity only and do not alter caller values. Updated the synthetic example and public references; tests remain deferred.

2026-10-30 crevice condition interval means: report arithmetic endpoint-average temperature and gap in each interval condition record. These values are descriptive summaries only and are excluded from provider-rate generation and inventory integration. The existing condition-history digest automatically pins the added fields; API and scope docs updated. Numerical tests remain deferred.

2026-10-30 crevice condition-rate record cross-link: enrich each attempted rate diagnostic with its interval index/ID/support, provider identity and record digest, a canonical digest of the corresponding exposure-condition row, and a digest of the exact time-bounded rate input. Pin the ordered attempted-rate ledger, including a failed interval attempt, with a dedicated digest and expose it through the failure prefix. No tests or package builds were run.

2026-10-30 사전검증 원장 보강: 틈부식 재고 계산에서 지원자료 누락·공급자 기록 불일치·지원 범위 이탈로 조기 반환할 때도 각 interval의 순번, ID, 시작/종료 시각, 조건기록 digest, 정확 입력 digest, provider record digest와 실패 사유를 반환한다. 조기 종료 응답에 원장 digest와 실패 interval ID 목록도 포함한다. 따라서 사전검증 단계에서 계산되지 않은 구간을 식별할 수 있다. 실행 및 수치 검증은 보류했다.

2026-10-30 원장 연결 보완: 사전검증 원장의 digest를 interval 적분 prefix에도 포함했다. 따라서 지원범위·자료 검토에서 조기 반환하는 경우와 실제 interval 적분 후 반환하는 경우 모두 같은 preflight 입력 원장을 식별한다. 자동화 테스트 및 패키징은 수행하지 않았다.

2026-10-30 구현: `fabrication.gasket_calibrated_leakage_history`를 추가했다. joint별 caller calibration의 접촉압력×차압 격자에서 local molar leakage flux를 양선형 보간하고 접촉면적 합으로 시간 knot별 total rate와 trapezoidal cumulative leakage를 계산한다. 외삽하지 않으며 joint/조건 matching, pressure basis, contact-to-flux transfer, area partition과 temporal alignment review를 요구한다. 새 모델은 caller calibration source basis, 합성 API 입력, capability, public contract schemas 및 모델 참조에 연결했다. registry 수는 models 356, interfaces 152, partial capability 101이며 전체 capability 609, 공개 schema 767이다. 101-row source audit는 Python 경로 226, 구현 요소 341, 누락/미매핑 0을 기록한다. 이는 구조 및 연결 추적 결과이고 계산 테스트·패키징·물리 qualification 결과가 아니다.

2026-10-30 flange-to-gasket leakage adapter: `gasket_leakage_request_from_flange_contact_history()`가 두 spatial viscoelastic flange contact history model 중 하나의 `AssessmentResult`를 받아, computed 상태·정확한 시간 knot·node ID 순서를 검토하고 contact pressure 이력 및 upstream result digest를 누설 요청에 결속한다. caller는 면적, 차압 이력과 joint-specific leakage calibration을 공급한다. 이 adapter는 결과 계보를 잇는 배선이며 접촉·유동 계산이 아니다.

2026-10-30 gasket contact-to-leakage 연동 후 카탈로그를 다시 생성했다: 356 models, 153 interfaces, 101 partial capability rows (총 capability row 610), public schemas 767. scope source audit는 226 경로·342 component로 갱신됐다. 이는 계산 시험이 아니다.

2026-10-30 연동 계약 강화: flange-to-leakage adapter는 이제 upstream AssessmentResult의 원래 input/context digest를 재계산해 확인하고, joint ID, physical scope ID, contact node 순서, 시간 knots 및 gasket contact area 배열을 누설 요청과 정확히 일치시킨다. 불일치·변조 입력은 거부된다. 수치 테스트는 실행하지 않았다.

2026-10-30 nonlinear contact time refinement 정합: upstream flange input의 원래 knots와 contact result의 refined knots를 구분한다. adapter는 history가 원 시간 support 전체를 정확히 덮는지 확인하고, caller가 `refined_contact_time_interpolation_reviewed`로 승인한 경우에만 차압 이력을 refined knots로 선형 보간한다. 요청을 재검증해 길이·단조시간 계약을 지킨다. Review 없이는 거부한다.

2026-10-30 신규 wet-CO2 계산 경로: `chemistry.caller_scale_coverage_kinetics`는 caller가 검토한 구간별 상수 포화비, attachment/detachment rate coefficient와 차수로 면적 평균 피복률의 1차 상태식을 닫힌형식 적분한다. 동적 scale morphology를 범용 예측하지 않으며, 이력은 기존 scale-history transport binding으로 exact knot별 covered-area fraction에 연결되고 scale layer 두께/물성은 caller 입력으로 유지된다. 합성 예제·source basis·public schema·모델 참조·capability catalog·scope audit를 갱신했다. 최신 catalog 357 models/153 interfaces/101 partial capabilities, 768 public schemas. Static source audit: 101 rows, 227 paths, 343 components, missing/unmapped 0. Numeric tests, physical qualification and package build were not run.

2026-10-30 scale coverage ledger correction: knotwise scale transport-series output now reports source thickness and coverage separately from the final transport covered-area input. Sequential scale-limited electrochemical campaign rows additionally retain each binding's scale state ID, transport-result digest, originating history model/time/layer and optional coverage fraction; duplicate ambiguous coverage keys were removed.

2026-10-30 scale/electrochemistry lineage gate: the sequential campaign now recomputes the source scale AssessmentResult input/context digest and verifies the scale transport assessment's source-history digest, source model, exact segment-start knot, and scale_state_id against its binding. Segment validation independently checks transport context metadata agrees with result values. Mismatched or stale scale states fail contract validation before transport execution.

2026-10-30 피복률 kinetics 물질수지 진단: `chemistry.caller_scale_coverage_kinetics`의 각 구간에서 닫힌형식 해의 피복률 변화와 누적 부착량−이탈량을 대조한다. 구간 잔차, 최대 절대 잔차, 전체 이력 잔차를 결과에 남기며 부동소수점 폐합 허용치를 넘으면 계산 prefix와 함께 `out_of_scope`로 종료한다. 이 검사는 수치 원장 폐합만 확인하며 kinetics의 실험 타당성·계수 적합성·보호 성능을 입증하지 않는다. 공개 스키마(768), 모델 참조, 카탈로그(357 models/153 interfaces/101 partial capabilities, 총 611 capabilities), backlog와 101-row 정적 소스 감사를 재생성했다. 감사 결과: 227 소스 경로, 343 구성요소, AST/심볼/경로/구성요소 누락 0. 수치 테스트·물리 검증·패키징은 실행하지 않았다.

2026-10-30 피복률 forcing 경로 확장: `ScaleCoverageKineticInterval`에서 구간 시작·끝 saturation ratio를 받아 구간 내 선형 경로를 표현할 수 있다. 변동 경로는 선형 보간 review, 피복률/부착·이탈 재고별 절대·상대 허용오차, 최소·최대 시간간격 및 계산 budget을 명시해야 하며, 상수 경로는 기존 닫힌형식 해를 유지한다. Adaptive RK4 step-doubling 결과에 수용/거부 단계, kinetic rate 평가수, 최대 정규화 오차비와 구간/전체 재고 폐합 잔차를 기록한다. 합성 입력은 상수 성장, 선형 포화변화, 상수 용해 구간을 포함한다. 공개 입력 스키마 768개, 계산기 357개·인터페이스 153개·추가 capability 101개(총 611개)를 재생성했고 정적 scope 감사는 101행/227 경로/343 구성요소, 누락·미매핑 0이다. 적응형 적분의 수치 동작, 오차수렴, 실험 타당성은 검증하지 않았다. 계산 테스트와 패키징은 보류했다.

2026-10-30 stateful multiaxial fatigue contract 보강: `ClosedTensorCycle`은 piecewise-linear 경로의 표본시각만 입력할 수 있고, cubic-Hermite에만 응력·변형률 미분 이력을 함께 요구하도록 검증을 정리했다. 경로시간·텐서·미분·cycle 반복수가 유한한지 확인한다. stateful 요청은 유한 양의 정수 반복수, 고정/적응 적분에 필요한 최소 callback 평가수, integration/closure/tolerance를 사전 검사한다. 동일한 경로 반복이 2회 이상이면 마지막 두 terminal state 차이를 출력하고, caller가 검토한 절대·상대 허용치를 함께 제공한 경우에만 tolerance pass/fail 진단을 낸다. 이 진단은 점근 주기상태나 피로 안정화를 증명하지 않는다. 합성 adaptive example과 공개 request schema/source description/API 문서를 갱신한다. 계산 테스트와 package build는 보류한다.

2026-10-30 stateful fatigue 반복상태 개선: 상태기반 다축 피로 callback API의 `ClosedTensorCycle`은 이제 선형 경로에 필요한 sample time만 받을 수 있고, cubic-Hermite 경로에서만 응력·변형률 미분 이력 쌍을 요구한다. cycle 표본·미분·시간·반복수 및 solver tolerance의 finite support를 계약에서 확인하고, 양의 정수 cycle 반복수와 최소 provider 평가예산을 적분 전에 산정한다. 같은 cycle이 반복되면 마지막 두 cycle 종료 상태 차이를 기록하며, explicit review와 절대/상대 허용치가 입력된 경우 제한된 cycle-local tolerance 진단을 제공한다. 이는 발산·수렴 증명이나 물성/피로 적격성 판단이 아니다. 합성 adaptive 요청, 공개 schema, source basis와 구현 백로그 설명을 갱신했다. 생성 결과는 768 public schemas, 403 source bases, catalog 357 models/153 interfaces/101 partial rows (611 total); scope audit 101 rows/227 paths/343 components, missing/unmapped 0. 단위 수치 테스트, 반복상태 실제 계산, 물리 검증, 패키징은 실행하지 않았다.
2026-10-30 크리프 되먹임 선택 적응 제어: `CreviceTransportRecessionFeedback`에 최대 상대 간극 변화 한도, 명시적 정책/결정론 review, refinement 예산을 추가했다. 시도 구간 변화가 한도를 넘으면 계산 상태를 commit하지 않고 중간 시각으로 분할해 두 구간을 재평가한다. 거절 시도 결과 digest와 시작/시도 간극을 기록하고, 실제 accepted internal times만 결과 경로에 반영한다. 내부 구간·transport record 예산 및 부동소수점 분할 가능성을 확인한다. API 문서, source basis, 스키마 768개, model/capability catalog와 implementation backlog를 갱신했고 정적 audit는 101 rows/227 paths/343 components, 누락·미매핑 0이다. 계산 테스트/물리 검증/패키징은 실행하지 않았다.
2026-10-30 크리프 형상-유동-수송 순차 연결: recession feedback API에 opt-in 압력 history와 fluid-property lineage를 받아 초기 간극 유동을 첫 transport segment에 적용하고, 각 확정된 recession/aperture 갱신 후 steady planar-slit resistance 관계를 재평가해 다음 segment의 face velocity로 넘기는 모드를 추가했다. 압력 표본 수는 요청 시각과 일치해야 하고 유동 연속성·압력 정렬·Newtonian/비압축·층류/완전발달 가정 review를 요구한다. 별도 advection provider와 동시 지정은 차단한다. 내부 시간 세분화·적응 refinement와 현재 조합하지 않는다. 유동 계산과 수송 ledger/remap이 모두 통과한 segment만 상태와 hydraulic history에 commit하도록 정리했다. 한글 범위 문서, 768 schema, source/capability/model catalogs, backlog와 101행 정적 audit를 갱신했다. 최신 정적 감사 227 paths/343 components, 누락·AST 오류·미연결 0이다. 계산 테스트·물리 qualification·패키징은 실행하지 않았다.
2026-10-30 gasket 전이 traceability: 시간별 compliance 입력이 이미 contact-time refinement 및 replayed bisection에서 선형 보간되는 구현을 감사표와 한글 방법 문서에서 명확히 했다. `sampled_contact_transition_brackets`는 하한/상한에서 실제 사용된 flange compliance operator digest를 이제 보존하며, refinement가 수행되면 최종 좁혀진 bracket endpoint의 digest로 갱신한다. API/source/backlog 상태 문구를 정정하고 public schemas 및 정적 scope audit를 재생성했다. 계산 테스트·물리 검증·패키징은 미실행이다.
2026-10-30 aqueous activity interpolation option: `AqueousTabulatedActivityIteration` now accepts default piecewise-linear or optional `shape_preserving_pchip` interpolation for log gamma over caller ionic-strength knots and temperature slices. The PCHIP implementation uses monotonicity-preserving weighted harmonic interior slopes and bounded endpoint slopes, handles two-knot data as a linear segment, and rejects out-of-support queries. Explicit review is required for PCHIP; method and review state are included in output and the request digest. Added a synthetic input-wiring example and Korean usage/scope documentation, updated source basis/catalog and wet-CO2 residual scope. Schemas/catalog/backlog/static source audit regenerated; no numerical tests, physical validation or package build ran.
2026-10-30 aqueous activity interpolation implementation selection: replaced the in-house PCHIP slope/evaluation routine with SciPy `PchipInterpolator`, already available through the optional `science` extra. Import is lazy; requesting PCHIP without that extra fails with an actionable dependency message, while default piecewise-linear use keeps the core dependency set unchanged. Updated Korean API/scope docs and audit wording. Schemas and static catalog/audit were regenerated; no tests or package build ran.
2026-10-30 aqueous activity data lineage: measured/open-dataset activity knots now require paired `source_id` and `source_record_id`; the source must resolve to declared Evidence with a measured/open_dataset origin, and Evidence source IDs must be unique. The module computes normalized table-content, source-record mapping and evidence-bundle SHA-256 values. Speciation results expose these digests; the transport activity callback carries them plus interpolation method and source request digest into `solve_restricted_transport` output. Global-time wrapper callbacks preserve the same attributes for crevice campaign lineage. Korean data-use/API scope text and audit records were updated. Regenerated public schemas/catalog/backlog/static audit; no calculation tests or package build ran.

2026-10-30 수용액 평형 반응 보존 진단: signed 반응식의 전하수지 검사를 계약 단계에 추가했다. 선택적으로 모든 종의 원소식을 받으면 원소별 반응수지도 확인하고, 불균형 입력은 계산 전에 거절한다. 원소식 입력에는 명시 검토 플래그가 필요하며 계산 결과는 반응별 전하·원소 잔차를 보존한다. Aqueous mass-action schema, API reference, source basis와 backlog를 갱신했다. 정적 scope audit는 101 rows, 228 source paths, 343 components에서 누락/미매핑 0이다. 계산 테스트·수치 solver·물리 qualification·패키징은 실행하지 않았다.

2026-10-30 구현 사용 예제 정합: PCHIP work-life, memoryless/stateful damage path 및 원소/전하 보존형 aqueous mass-action을 보여주는 합성 예제를 추가했다. PCHIP rate closure 계약 오류 문구를 Hermite 전용에서 Hermite/PCHIP 공통으로 고쳤다. 예제는 실행하지 않았다.
## 2026-10-30 — Aqueous reaction candidate lineage IDs

The bounded atom/charge stoichiometry enumerator now assigns each normalized direction-neutral split a deterministic SHA-256-derived `candidate_id` and full `candidate_sha256`. This gives downstream network-authoring tools a stable reference independent of candidate list position. Removed a duplicated total-order guard in the candidate loop. The ID only anchors the exact normalized stoichiometric proposal; it does not assert chemical feasibility, direction, equilibrium data, or reaction identity. Updated the source-catalog derivation and API reference. Schema/catalog generation only; no model calculation or test was run.

## 2026-10-30 — Explicit aqueous candidate-to-equilibrium binding API

Added `bind_aqueous_candidate_reactions()` and strict binding/selection contracts. The helper accepts a computed balance-candidate result and caller-selected candidate IDs/digests, explicit forward/reverse orientation, temperature-specific caller `log10(K)`, record IDs/checksums and matching Evidence. It recomputes candidate payload identities, rejects stale/malformed selection lineage, converts to signed mass-action coefficients, and negates `log10(K)` only for an explicitly requested reverse direction. Unreviewed selection/constants return `needs_data` with no reaction list. Registered the interface metadata, exported both request schemas, and wrote a public method note/example. Catalog generation and static path/hash/AST audit completed (101 rows, 229 paths, no missing path or unmapped component). No candidate calculation, numerical test or package build was run. Temperature/standard-state matching to the downstream mass-action system remains a caller gate.

## 2026-10-30 — Candidate binding contract alignment

Review of the new aqueous binding helper found that provenance fields had been mixed into each reaction dictionary, which would violate the downstream `AqueousEquilibriumReaction` extra-forbid contract. Split output into solver-ready `reactions` and separate `reaction_lineage`; added an explicit target mass-action temperature, bounded parameter-temperature match tolerance, and the exact molarity activity standard-state declaration. Added structural checks for malformed/duplicate candidate terms. This is a source-level contract correction only; the binding function and thermodynamic result were not executed.

## 2026-10-30 — Aqueous mass-action system assembly adapter

Added `AqueousMassActionSystemAssemblyRequest` and `assemble_aqueous_mass_action_system()` to turn a computed reaction-binding result plus caller-owned species, constraints, activity provider records and solver settings into a strict `AqueousMassActionSystem` payload. The adapter rejects mismatched target temperature/standard state, malformed reaction/lineage arrays, missing parameter Evidence, reaction/lineage identity mismatch, nonconservation under the declared species formulas, and a non-square equation count before returning the solver payload. Numerical Jacobian rank/conditioning is evaluated by the solver, not this assembly adapter. Ordered reaction lineage is retained and reduced to the system equilibrium-record digest. Added a full synthetic wiring example and an integration catalog entry. Schema/catalog generation and static audit completed; no equilibrium solve or test was run.

## 2026-10-30 — Piecewise-linear pressure support for crevice substeps

Extended `CreviceTransportRecessionFeedback` so internal geometry-update and adaptive aperture-refinement segments can recalculate steady slit hydraulics from explicitly reviewed piecewise-linear pressure interpolation between requested output knots. The pressure samples must cover and align exactly with the original requested clock; interpolation never extrapolates. Each accepted hydraulic endpoint records its source bracket and interpolation fraction, and the selected policy/review is retained in campaign lineage. The calculation remains a sequential operator split with fixed geometry over each transport interval. Updated the capability/source catalog, public schema and crevice feedback manual. Catalog generation and static source audit completed; no transport execution or test was run.

## 2026-10-30 — Bound reaction payload-to-lineage cross-check

Strengthened the candidate-binding/assembly handoff: each reaction lineage now stores the canonical digest of the exact strict reaction payload, the caller's source `log10(K)`, and the signed value after the explicitly selected direction. Assembly recomputes the reaction payload digest, checks the direction/sign relation and confirms the candidate-enumeration result digest is internally consistent before building the mass-action system. This catches accidental or partial mutation between the two helper results; it is not a signature/authentication mechanism. No chemistry solve or test was run.

## 2026-10-30 — Caller Arrhenius scaling for scale coverage rates

Extended `chemistry.caller_scale_coverage_kinetics` with optional temperature scaling for both attachment and detachment coefficients. The caller supplies a reference temperature, separate activation energies, an absolute-temperature support interval, and an explicit applicability review. Target and reference temperatures must remain inside support; non-finite overflow or underflow returns `out_of_scope`. Results retain the original coefficients, effective rates at the requested temperature, scaling policy and input digest. Existing coefficients declared directly at the requested temperature remain supported. Updated the synthetic input, source derivation, schemas, API and focused documentation; no kinetic calculation, independent-data validation or test was run.

## 2026-10-30 — Caller Arrhenius scaling for scale-thickness rates

Extended `chemistry.caller_surface_scale_kinetics` with independent precipitation and dissolution activation energies and a caller-declared temperature applicability interval. The target/reference temperature checks are fail-closed, and the selected rate constants are scaled before per-interval molar flux and bounded-inventory dissolution are evaluated. Results retain reference/effective coefficients, scaling policy and interval fluxes. A review flag is required; existing directly-at-target-temperature inputs remain valid. Updated source derivation, synthetic fixture, schema, API and focused manual. No numerical calculation or test was run.



## 2026-10-30 — Deterministic gasket leakage pressure-interval envelope

Added `fabrication.gasket_calibrated_leakage_rate_envelope`. Each node has caller-declared contact-pressure and differential-pressure intervals; the model splits those rectangles at calibration knots, evaluates exact bilinear extrema at every subcell corner, retains witness pressures, and sums area-weighted node bounds. The uncertainty set assumes independent node intervals and a fixed calibration/area; it is not a probability distribution and does not cover cross-node correlation, calibration error, temporal integration or seal acceptance. Added focused Korean method/API documentation and a synthetic wiring example. No execution, numerical testing, packaging or HPC job was run.


## 2026-10-30 — Additional coupled-analysis code increments

Added analytic local equilibrium sensitivities for the fixed-gamma aqueous mass-action solver; a caller-provider crevice Nernst half-cell potential history with an inventory-binding adapter; a lineage-checked mapping from a certified continuous-plane Fatemi–Socie factor bracket to a caller-calibrated life interval; and a deterministic exact gasket leakage-rate envelope for independent nodal pressure intervals under a fixed bilinear table. Each increment has a focused Korean method note and a synthetic wiring example. Scope audits now link the code evidence. No tests, example execution, packaging or HPC jobs were run.


## 2026-10-30 — First-order covariance propagation for aqueous equilibrium

Extended the fixed-gamma aqueous mass-action request and assembly adapter with an optional parameter covariance in the published order (reaction log10(K), analytical/charge constraint targets, species ln(gamma)). The contract requires explicit review and finite symmetric positive-semidefinite covariance. At a supported equilibrium root, the analytic implicit Jacobian derivatives propagate it through first-order JΣJᵀ to log activities, log concentrations and molar concentrations; singular/ill-conditioned sensitivity remains unavailable without discarding the equilibrium result. Updated Korean method/API guidance, the synthetic sensitivity example, source derivation and wet-CO2 scope evidence. No tests or example execution were run.


## 2026-10-30 — Nernst-to-Butler–Volmer electrochemical adapter

Added `electrochemistry.nernst_driven_butler_volmer_history` to compose the digest-verified crevice Nernst half-cell potential profile with one caller-calibrated Butler–Volmer reaction at exact shared time knots. Added explicit standard-potential reference identity to the Nernst request and cross-checked it against the electrode input reference; reaction identity, upstream input/result/history digests, rate support and reaction/species flux review gates are retained. The output is a partial-current and stoichiometric species-flux history without interpolation, integration or mixed-potential closure. Updated schemas/API/method docs, synthetic example and wet-CO2 scope evidence. No execution or tests were run.


## 2026-10-30 — Shared clock identity for Nernst/kinetics composition

Strengthened `NernstDrivenButlerVolmerHistory`: the caller kinetics request must now carry the same explicit clock ID as its digest-verified upstream Nernst assessment, in addition to exact time-knot alignment. Updated the synthetic composition example, API/method documentation and source derivation. This avoids treating numerically identical time arrays as proof of a common physical clock. No execution or test was performed.


## 2026-10-30 — Crevice multi-reaction mixed-potential history

Added a knotwise multi-branch mixed-potential API that binds digest-checked Nernst half-cell assessment histories to caller-calibrated Butler–Volmer branches. It enforces shared asset, location, physical scope, clock, reference, exact time/temperature knots and source inventory; scales branch currents by declared area onto a reference-area basis; and solves the common zero-net-current potential only within intersecting calibrated supports. The registry, exported Pydantic contracts, source derivation catalog and Korean API/method documents now expose the interface. Replaced a SciPy-only Brent dependency in the solver path with bounded deterministic bisection. This is code/catalog integration only; no numerical tests, experimental validation, packaging or HPC run occurred.


## 2026-10-30 — Crevice electrochemical flux-to-inventory ledger

Added `integration.crevice_electrochemical_inventory_transfer` to connect a computed multi-reaction mixed-potential history to a receiving transport/material module. It verifies upstream input/result/history digests, preserves the fixed caller reference-area basis, and integrates branch/species flux on each exact interval under an explicit caller-reviewed piecewise-linear reconstruction. It reports signed net, inward and outward mole transfer with exact zero crossing and cumulative totals, without claiming concentration, chemistry, phase, wall loss or corrosion rate. Registered and exported the API, source derivation, method note and API reference. No numerical tests, experimental validation or packaging were run.


## 2026-10-30 — Crevice transfer-to-composition adapter

Added `integration.crevice_electrochemical_composition_history`. The API verifies the digest-pinned area-scaled transfer assessment, requires initial amounts for each affected species and liquid-volume samples exactly at every transfer knot, then constructs a caller-volume well-mixed species amount/concentration history. Complete species inventory, other source/sink accounting, mixing and transfer mapping are explicit review gates; negative amounts fail closed. This composes transfer into a useful downstream aqueous interface but does not solve equilibrium, transport, precipitation or metal loss. Added public schema/catalog/source derivation and Korean guidance. No calculations, numerical tests, experimental validation or package build were run.


## 2026-10-30 — End-to-end synthetic crevice electrochemistry wiring

Added `examples/crevice_electrochemical_composition.py`, a synthetic-only multi-reaction workflow that calls the public registry separately for two Nernst histories, mixed-potential closure, area-scaled flux integration and caller-volume composition. Extended each method guide with this cross-reference and prominent non-validation disclaimer. Per instruction the example was not executed and no tests were run.


## 2026-10-30 — Crevice composition to aqueous mass-action adapter

Added `integration.crevice_composition_to_aqueous_mass_action_history`. It requires one caller-owned, fixed-topology `AqueousMassActionSystem` at every exact composition temperature; converts mol/m3 to mol/L under the declared standard state; forms positive gamma-weighted initial activity guesses; rebuilds each declared linear constraint target from the current composition; and invokes the existing mass-action solver. Zero species require a separately reviewed positive numerical starting guess. Context identity is checked against the upstream asset, location and clock. The adapter does not discover chemistry, interpolate thermodynamic data, add phases or infer corrosion/wall loss. Added registry/schema/source catalog/manual/API and synthetic pipeline wiring; no example execution, numerical tests, physical validation or packaging was performed.


## 2026-10-30 — Preserve fixed aqueous constraints in composition adapter

Refined the composition-to-mass-action adapter after reviewing constraint semantics. It no longer rebuilds every linear target from composition, which could silently alter fixed conditions such as a zero-charge target. Callers explicitly list the constraint IDs that represent composition-derived conserved totals and review their meaning; every unselected target remains unchanged. Schema, synthetic wiring input, source derivation and method/API guidance were aligned. No example execution or tests were run.


## 2026-10-30 — Aqueous mass-action activity-to-Nernst adapter

Added `integration.aqueous_mass_action_to_crevice_nernst_history`. It accepts only a computed digest-pinned aqueous mass-action knot history, maps its positive dimensionless species activities into the existing Nernst contract, and requires caller reaction quotient, electron number, reference identity, exact-knot E0 history, parameter lineage and local applicability reviews. It preserves composition and solver result digests and enforces run-context asset/location/clock identity. This is an explicit sequential composition → speciation → potential handoff, not a coupled current/chemistry iteration. Added public schema, registry/source/capability entries, focused Korean guide, API note and synthetic example wiring; no calculation, example execution, numerical test or packaging was run.


## 2026-10-30 — Downstream crevice electrochemistry extension request

Added a dedicated extension request for consumers of the Nernst → mixed-potential → species-transfer → caller-volume composition → aqueous mass-action sequence. It specifies digest and knot/reference identity retention, explicit calibration and review evidence, noncomputed status handling, and separate qualification boundaries for species transfer, wall loss, failure probability and FTA. Updated the extension-request index. It documents a request for other sessions/repositories and does not claim external code changed. No tests were run.
## 2026년 10월 30일 열응력 재료 물성 계보

두께방향 탄성 열응력 입력에 선택적 quantity별 Evidence 연결을 추가했다. 열팽창계수, 탄성계수, 포아송비, 탄성한계 각 profile은 provider/revision/record, source SHA-256, 일치하는 Evidence 및 선택적 material condition ID로 추적한다. 결과는 위치와 입력값을 포함한 profile digest와 provenance 상태를 quantity별로 남긴다. 미연결 값은 caller 공급·미출처로 표시하며 출처 검증이나 재료 적용성 판단을 주장하지 않는다. 합성 연결 예제는 출처마다 `synthetic` origin을 사용하고 결과 lineage를 출력한다. 설명 문서를 갱신했다. 계산 테스트 및 패키징은 실행하지 않았다.

## 2026년 10월 30일 전기화학 partial current 금속손실 연결

`integration.electrochemical_metal_loss_to_crevice_geometry`를 추가했다. digest-pinned metal-loss AssessmentResult의 각 reaction 누적 signed 질량을 Evidence-linked density로 체적화하고, caller가 모든 시간 knot에서 제공한 reaction별 셀 volume fraction으로 공간배분한다. reaction/셀 매핑, face 및 면적 basis, allocation/volume conservation, geometry basis, two-face equality 및 computational authorization review를 요구한다. 각 knot에 upstream-vs-allocated signed volume과 closure residual을 기록하고 기존 `planar_slit_aperture_history` sequential remap을 호출한다. registry, public schemas, capability/source catalogs, implementation audit, 모델 reference, API/method/전용 CREV-1 문서 및 synthetic wiring example을 연결했다. 생성 결과는 801 schemas, capability 372 calculators·157 interfaces·101 partial (630 total), source basis 422, 정적 audit 101 rows·252 paths·364 components이며 누락·AST 실패·stale symbol·unmapped 0이다. 계산 예제·수치 회귀·실험 검증·HPC 제출·패키징은 실행하지 않았다. 이 코드는 공간 배분 provider를 대신하거나 local current, within-interval moving boundary, 성공-prefix adaptation 또는 fully coupled flow/chemistry를 제공하지 않는다.


## 2026년 10월 30일 외부 crevice solver 교환 receipt

`integration.external_crevice_solver_receipt`와 `ExternalCreviceSolverHistory`를 구현했다. 외부 solver result SHA와 matching Evidence, provider revision/run, mesh revision, coordinate system, caller time basis, explicit SI units, mouth origin/positive direction, face fields 및 digest-pinned aperture history 간 exact knot/cell mapping을 요구한다. Piecewise-linear face-velocity callback은 receipt clock 내부만 보간하고 범위 외 입력은 거절한다. 기존 `solve_restricted_transport(..., axial_advection_velocity=provider)` callable 경계에 연결 가능하며 normalized receipt에 pressure/velocity field, geometry/mesh/source lineage를 유지한다. provider parser와 실제 consumer 실행 기록, 독립 CFD validation이 없어 CREV-2는 end-to-end 완료가 아니다. 한강 CPU 접속은 읽기 전용으로 확인했고 계산 제출은 하지 않았다. 합성 fixture는 실행하지 않았다. 정적 catalog/audit 수치는 생성 완료 후 갱신한다.
정적 catalog/schema/source/audit generation 결과: 802 public schemas, 373 registered calculation models·157 interfaces·101 partial (631 catalog rows), 423 implementation bases. Scope audit: 101 rows, 253 source paths, 365 components; missing paths, AST parse failures, stale/unmapped symbols and unmapped components all zero. These are static registry/provenance navigation checks only; no calculation example, numerical test, CFD provider consumer, validation, HPC job or package build was run.

## 2026년 10월 30일 다축 피로 material-law profile binding

`MultiaxialFatigueLawProfile` 및 `bind_caller_multiaxial_material_law()`를 추가해 memoryless와 stateful caller damage callback에 법칙/제공자/교정 ID와 digest, 재료 상태, stress/strain 정의와 단위, tensor 순서 및 shear convention, 성분별 support, cycle population/duration/repetition, reconstruction family를 결속한다. binding 단계에서 request scope를 확인하고 callback 표본마다 실제 재구성 tensor를 범위와 대조한다. 범위 위반/provider identity change는 fail-closed exception으로 damage law 평가를 중단한다. profile 내용과 digest, 원 configuration digest를 결과 lineage에 싣고 calibration 및 usage-rights Evidence를 별도로 보존한다. Schema/interface/catalog, scope audit, Korean API/detail docs, synthetic wiring example을 갱신했다. 합성 계산·테스트·HPC 제출·패키징은 실행하지 않았다. 현재 정적 산출물은 803 schemas, 373 calculators·158 interfaces·101 partial (632 catalog rows), 424 implementation bases; scope audit 101 rows·253 paths·366 components에서 누락·AST 실패·stale/unmapped 항목 0이다. broader multiaxial method transfer, physical validation과 calibration/holdout 증거는 남아 있어 capability 전체 구현 완료를 의미하지 않는다.

## 2026년 10월 30일 WCO2·CREV·FAT·GASK 잔여 code path 병렬 추가

WCO2-2 digest-bound chemistry stage boundary audit, CREV external solver receipt, FAT material-law support profile and ordered cycle-block receipt, GASK external FE compliance receipt and correlation-preserving finite-scenario leakage envelope를 추가해 각 API를 registry/schema/catalog/source/audit에 연결했다. FAT callback wrapper는 재구성 stress/strain을 매 표본 검사하며 WCO2 stage auditor는 species 누락/명시 제외와 chemistry state mismatch를 추적한다. GASK scenarios는 node-pressure/area/calibration-grid correlation을 유지한다. 실제 provider parser/consumer exchange, independent physical validation, calibration/holdout은 남아 있어 네 broad capability는 미완료다. 최신 정적 생성은 812 schemas, 376 calculators·159 interfaces·101 partial (636 rows), 428 bases; audit 101 rows·257 paths·370 components이며 누락/AST/stale/unmapped는 0이다. 계산 테스트·예제 실행·HPC 제출·패키징은 하지 않았다.

## 2026년 10월 30일 병렬 후처리 API 추가

CREV-3 `integration.crevice_aperture_history_refinement`를 등록해 digest-pinned geometry history의 큰 aperture 변화 구간을 제한된 횟수로 선형 보간 세분화하고 실패 시 연속 prefix/failed interval을 출력한다. 결과에서 원본 물리 state와 보간 state를 나눠 전달한다. WCO2-3 `integration.wet_co2_elemental_phase_handoff`는 이미 계산된 phase/transport history를 caller formula와 cell solution volume으로 원소별 mol 재고 이력으로 변환한다. 비정상/음수 값·축 불일치·비단조 clock·불완전 종 매핑을 거절하고 RunContext 자산/위치/time basis를 입력 identity와 맞춘다. registry, schema exporter, capability/source catalog 및 101-scope audit에 연결했다. 정적 결과는 815 schemas, 378 calculator models·159 interfaces·101 partial rows (638 total), 430 source bases; audit 101 rows·259 paths·372 components, missing/AST/stale/unmapped 0이다. 이 생성은 물리 검증이 아니다. 테스트·합성 계산·패키징·HPC submission은 보류했다.

CREV-3 추가 보강: 원본 기하 이력은 0초 시작과 단조 시간을 요구한다. 원본 `AssessmentResult`를 제공한 경우 model/input/context/result digest 및 registry `RunContext`의 asset/location/time identity를 대조한다. 큰 분할 요청 때 list slice 재배치를 반복하던 알고리즘을 `deque` 기반 왼쪽 우선 깊이 처리로 바꿔 처리비용을 분할 개수에 선형으로 유지한다. 실패 prefix에도 원본/보간 knot 분리 metadata를 포함한다. exporter/model reference/static source audit를 갱신했으며 수치 검증은 실행하지 않았다.

## 2026년 10월 30일 FAT cycle receipt provider lineage 보강

Ordered cycle-block receipt binding에서 stateful damage output에 receipt digest, block order, clock, source-state endpoint만 보존하던 부분을 보강해 provider ID, revision, run ID와 원본 provider result digest도 request와 evaluator 결과로 전달한다. 이 값들은 기존 receipt의 matching Evidence에 묶인 provider provenance이며 provider cycle parser 구현이나 fatigue state-variable 변환을 뜻하지 않는다. Public schema와 source/capability catalog, scope audit 및 FAT cycle exchange 안내를 갱신했다. 정적 생성은 816 schemas, 380 calculator models·159 interfaces·101 partial rows (640 entries), 431 source bases; audit 101 rows·261 paths·374 components, missing/AST/stale/unmapped=0이다. Model reference regeneration은 다른 capability의 미등록 source ID 때문에 실패했고, test/HPC/package는 수행하지 않았다.

## 2026-10-30 WCO2 후보 반응망 assembly workflow

`integration.aqueous_candidate_network_workflow`를 추가했다. 기존 `enumerate_aqueous_reaction_candidates` → `bind_aqueous_candidate_reactions` → `assemble_aqueous_mass_action_system`를 하나의 입력 계약으로 구성하고 모든 단계 input/result digest를 반환한다. enum과 assembly species의 ID·charge·complete formula가 같아야 하고, binding temperature·activity standard state도 assembly와 정합해야 한다. reaction 방향과 logK/온도는 기존처럼 caller가 수동으로 Evidence를 제공한다. 이는 automatic network/phase discovery, mass-action solve, kinetics 또는 WCO₂ qualification이 아니다. registry, schema, capability/source catalogs, implementation audit와 API 안내를 연결한다. 테스트·계산 예제·HPC는 수행하지 않았다.

## 2026년 10월 30일 병렬 구현 snapshot: WCO2/FAT/GASK

WCO2-4 `integration.aqueous_candidate_network_workflow`가 bounded stoichiometric candidate enumeration, human/Evidence-backed direction/logK binding, strict mass-action system assembly를 하나의 workflow로 구성한다. 종 ID·전하·원소식, 온도 및 activity standard state 정합과 단계별 input/result digest를 보존한다. 반응·상 자동발견이나 speciation solve는 하지 않는다.

FAT cycle exchange 결과에 provider ID/revision/run/result digest를 추가 전파해 block/clock/material state/receipt digest만 있던 lineage를 외부 provider result까지 연결했다.

GASK-3 `integration.gasket_leakage_scenario_exposure`는 correlated finite scenario leakage-rate AssessmentResult를 고정해 snapshot time부터 caller-reviewed constant-state duration으로 scenario별 mol amount/min/max witness를 계산한다. 시간변화 pressure/contact/gasket relaxation은 모델링하지 않는다. Consequence/risk/FTA adapter가 사용할 수 있는 amount basis다.

정적 카탈로그 및 API/schema reference를 재생성했다. 최종 snapshot 817 schemas·380 models·159 interfaces·101 partial entries (640 total)·434 source bases. 101-row audit는 262 paths·375 components에서 missing/AST/stale/unmapped=0이다. completion flag는 47/101 (46.5%), code-incomplete 4, data-validation-pending 51, provider-dependent 46으로 기록되며 code complete와 validation complete를 분리한다. 모델 reference의 source ID 부재는 PSA Dyna contract와 competitive-solid transport split basis를 source catalog에 추가해 해소했다. 테스트·실험/수치 validation·package/HPC 작업은 실행하지 않았다.

## 2026-10-30 multiaxial life finite-scenario envelope

Added `fatigue.multiaxial_life_scenario_envelope` for an ordered set of complete computed `fatigue.multiaxial_life_campaign` AssessmentResults. It pins scenario-set/result/input/context digests, checks common model revision, material condition, calibration digest, cycle support and asset/location/time identity, and reports min/max cycle-life witnesses over the supplied finite cases. It keeps each complete row intact so correlated scenarios are not recombined parameter-wise. The output is explicitly not a probability, confidence interval, or continuous bound. Registered schema/API/source/audit references and added a usage/extension guide. Numerical testing, benchmark/experiment validation, package builds and HPC work were not run.

## 2026년 10월 30일 GASK transient/FAT scenario/WCO2 solve composition

`integration.gasket_leakage_scenario_rate_interval`은 같은 시나리오 ID와 calibration realization을 보존한 두 correlated-leakage endpoint를 검증하고, caller-reviewed piecewise-linear total-rate reconstruction에 대해 trapezoid amount를 계산한다. `fatigue.multiaxial_life_scenario_envelope`는 상관을 보존한 finite computed life campaigns에서 calibration/material/support/context 일치 후 extrema/witness를 내며, probability/confidence/continuous bound는 추론하지 않는다. `integration.aqueous_candidate_network_speciation`은 candidate workflow 결과와 조립 system digest 및 standard-state/temperature를 검증하고 기존 speciation solver를 호출한다. 새 API 세 개의 schemas, registry, capability/source catalog, audit paths 및 한국어 API/detail/extension 문서를 연결했다. 기본 registry 조회에서 이번 라운드 API 7개를 정적으로 확인했다. 821 schemas, 383 models·159 interfaces·101 partial (643 entries), 437 source bases; scope audit 101 rows·262 paths·375 components, missing/AST/stale/unmapped 모두 0. 완전 구현 표시 47/101(46.5%)로 남는다. 수치 tests/benchmarks, physical validation, packaging, HPC 계산은 하지 않았다.

## 2026-10-30 gasket leakage covariance propagation

Added `fabrication.gasket_leakage_covariance_propagation`, a caller-evidence-bound first-order uncertainty calculation for one nominal gasket leakage state. The covariance variable order is fixed as node contact pressures, common differential pressure, node areas, then row-major calibration flux values. Validation checks dimensions, finiteness, symmetry, nonnegative variances, zero-variance cross-covariances and positive semidefiniteness after conversion to a correlation matrix, avoiding scale domination by mixed physical units. Analytic local derivatives are evaluated inside one bilinear calibration cell; any calibration knot or support boundary is rejected because the local perturbation may cross a cell/support boundary. Calibration and covariance provider IDs/digests, scenario digest and usage license are tied to Evidence. The output is nominal rate, Jacobian, first-order variance and standard uncertainty only. Numerical tests, independent benchmark, calibration uncertainty qualification, nonlinear uncertainty bounds and packaging remain pending.

### Parallel verification follow-up — gasket leakage covariance

Ran `tests/test_gasket_leakage_covariance.py` (20 cases) and `tests/test_gasket_joint.py` (4 cases) concurrently as independent pytest processes; all 24 passed. Coverage includes analytic nominal rate/Jacobian variance path, knot/support fail-closed behavior, mixed-unit covariance normalization, symmetric/PSD constraints, evidence/provider/license links, and existing gasket joint contracts. This is local software regression evidence only, not independent engineering benchmark, experimental qualification, full-suite validation, or publication clearance.

## 2026-10-30 parallel regression defect repairs

The four-shard local suite first reported 2,314 passed and 60 failed. Focused parallel reproduction exposed production defects in storage-inspection interval pairing, CO2 alkalinity closure stopping, corrosion-profile strict tuple reconstruction, fatigue digest import, atmospheric ensemble model-version registration, and JSON tabular import validation. These paths were corrected. The CUI receipt now validates JSON round-trips while remaining digest-bound; wet-CO2 archive mismatches identify the digest field. Regression fixtures now include reviewed crevice boundary jumps and crack-growth material/environment mapping, and sampled spatial exceedance tests no longer treat it as a time-period failure probability.

Subsequent targeted parallel runs passed 87 cases across the affected domains. The complete existing example execution parameterization also passed 346 examples; its one remaining failure is the registry/example inventory equality check because 38 registered APIs still lack examples. The entire suite has not been rerun after these repairs, so no full-suite pass is claimed. HPC connection availability was reported, but no remote task was submitted because the standing instruction requires a separate submission request.


## 2026-10-30 Findley 임계면 응력 screening

`fatigue.critical_plane_findley_parameter`를 추가해 caller 응력 텐서 cycle, 후보 면, 보정 계수와 한 기준 수명 강도를 digest 및 review gates와 함께 처리한다. finite-plane 결과는 sampled shear-traction 벡터의 최대 쌍별 chord 절반으로 진폭을 정의하고, 지표·지배 면·기준 강도 비율 및 margin만 반환한다. 수명 예측, 허용기준 또는 확률 계산은 하지 않는다. 합성 예제와 run context, DOI 근거, 독립 derivation, API 설명을 연결했다. 정적 catalog/schema/reference 생성 후 385개 model input, 159 interface, 101 partial item, 821 schema, 440 source basis를 기록했다. Scope audit는 101행·265 source path·379 component에서 missing/AST/stale/unmapped 0이며 신규 API를 기존 multiaxial-fatigue 영역에 반영했다. 계산 테스트, 패키징, HPC 제출은 하지 않았다. 전체 진행률 기준은 47/101(46.5%)로 유지한다.

## 2026-10-30 — 벽두께 초기 한계상태 명시

침식·부식 wall limit-state 출력에 손실 누적 전의 초기 여유 `measured_thickness - required_thickness`와 초기 상태의 한계 이하 여부를 추가했다. 초기 측정이 이미 최소두께 이하인 상황을 첫 interval 종료 후의 margin과 분리해 downstream FTA/신뢰성 연결에서 시점 혼동을 막는다. 계산 로직·단위 metadata 및 해석 안내를 갱신했다. 정적 카탈로그·모델 참조·schema·구현 경로 감사를 다시 생성했다: 386 models, 159 interfaces, 101 partial entries (646 total), 821 schemas, 444 source bases; audit 101 rows, 265 paths, 380 components, missing/AST/stale/unmapped=0. 이는 정적 연결 근거이며 계산 테스트가 아니다. 테스트·패키징·HPC 실행은 하지 않았다. 전체 scope 완료 표시는 47/101 (46.5%)로 유지하며, 이 증분은 기존 범위 안의 보강이다.

## 2026-10-30 — SIT 상호작용 계수 Evidence 해시 바인딩

`SITInteraction` 입력에 `evidence_sha256`를 추가하고, 계산 및 aqueous mass-action 반복 결합 시 Evidence의 같은 source ID·원자료 파일 SHA가 있는지 계약 단계에서 강제한다. 결과 lineage에는 source record ID와 파일 digest를 함께 남긴다. 개별 record bytes 자체의 해시라고 주장하지 않도록 필드 의미를 고정했다. source ID 중복도 거절해 Evidence 선택이 모호해지지 않게 했다. 이 엄격한 계약은 `SITActivityCoefficientInput.v2`와 `AqueousSITIteration.v2`로 명시해 구버전 payload를 암묵 수용하지 않는다. synthetic examples, API 안내, schema/model reference와 catalogs를 갱신했다. 정적 생성 결과는 386 models·159 interfaces·101 partial (646 total)·821 schemas·444 source bases; scope audit 101 rows·265 paths·380 components, missing/AST/stale/unmapped 0이다. 이 turn에서는 계산 tests·수치/물리 검증·package·HPC를 수행하지 않았다. 이는 provenance 강화이며 47/101 (46.5%) 전체 scope 진행 표시는 바꾸지 않는다.

## 2026-10-30 — 수용액 반응 평형상수 cycle consistency audit

`chemistry.aqueous_thermodynamic_cycle_audit`는 caller가 제공한 species formula/charge와 evidence-bound 반응 `log10(K)`에 대해 개별 원소·전하 균형을 확인하고, species-by-reaction matrix의 오른쪽 null-space를 SVD로 구해 cycle closure residual을 계산한다. 이어서 `integration.aqueous_mass_action_cycle_audit`가 기존 `AqueousMassActionSystem`과 반응별 evidence bindings를 재사용하도록 연결했다. Adapter는 비어 있는 elemental formula, reaction Evidence hash 불일치, 공개 dataset license 누락을 `needs_data`로 반환하고 값이나 권리를 추정하지 않는다. 입력에 provider, Evidence file hash, activity standard state, temperature, numerical rank·closure tolerances와 review gates를 포함하고 basis/residual/rank lineage를 반환한다. 정적 생성 결과는 388 models·159 interfaces·101 partial entries (648 total)·821 schemas·446 source bases이며, source audit는 101 rows·265 paths·380 components에서 missing/AST/stale/unmapped=0이다. 자동 species/phase discovery와 speciation/corrosion 계산은 제공하지 않는다. 테스트·실제 parameter 비교·패키징·HPC는 아직 하지 않았다. 전체 범위 진행률은 47/101(46.5%)로 유지한다.



2026-10-30: `integration.external_flange_compliance_history` 구현. Ordered caller times에 digest-verified provider receipt bindings를 일대일 대응하고, 동일한 provider/model revision·asset scope·coordinate frame·DOF/contact mapping을 요구한다. 기존 history reducer를 재사용하고 각 절점 결과에 receipt, provider, mesh, result-field 및 transform lineage를 남긴다. Receipt schema에 물리 timestamp가 없으므로 caller review 전에는 계산을 실행하지 않는다. Synthetic example/context, source basis, docs, registry-derived schema/catalog/backlog를 갱신했다. 정적 catalog generation과 source audit는 성공했다: 389 models·159 interfaces·101 partial (649 total)·821 schemas·447 source bases, 101 rows·265 paths·380 components에서 누락/AST/stale/unmapped 0. 계산 테스트·실제 provider 교환·물리 qualification·패키징/HPC는 미실행. 전체 진행률은 47/101(46.5%)이다.


2026-10-30: `integration.aqueous_mass_action_vant_hoff_history` 구현. Reference `AqueousMassActionSystem` 반응별 기준 log10(K)에 caller reference enthalpy를 연결해 constant-ΔH integrated van 't Hoff correction을 계산하고 매 온도 knot마다 기존 fixed-gamma, single-phase mass-action solver에 전달한다. exact reaction coverage, source-record/Evidence-file SHA, open dataset license, validity interval, standard-state alignment, fixed-gamma temperature applicability, caller time mapping, review gates 및 max |log10(K)| budget을 넣었다. 미승인 상태에서는 solver를 호출하지 않으며 온도 support 외삽/clip하지 않는다. 기존 mass-action solver의 상태별 진단과 원 Evidence에 thermo Evidence를 더해 lineage를 남긴다. 합성 example, docs, registry/source/capability/schema/model reference/backlog를 갱신했다. 정적 catalog generation·source audit 성공: 390 models·159 interfaces·101 partial (650)·821 schemas·451 source bases; 101 rows·265 paths·380 components에서 missing/AST/stale/unmapped 0. 계산 테스트/benchmark, 실 chemistry validation, package/HPC 미실행. 범위 완료 진행률은 47/101(46.5%) 유지.


2026-10-30: van 't Hoff temperature-history API에 caller temperature-specific activity-coefficient records를 추가. 각 knot별 coefficient vector는 exact reference species ordering/count를 따라야 하고 별도 Evidence/source/license/provider ID·revision·configuration digest lineage 및 `activity_coefficient_temperature_history_reviewed`를 요구한다. 모든 절점의 provider configuration 일치를 확인한다. 입력이 없는 고정-gamma 모드는 원래 system의 gamma를 재사용하고 기존 applicability review를 계속 요구한다. 계산기법/API는 gamma 값을 추정하거나 knot 사이 보간하지 않는다. 합성 fixture에 두 temperature knots gamma rows를 추가했고 method documentation/source derivation을 갱신했다. 이 수정으로 390개 모델/650개 capability 수와 47/101 completion flag는 그대로이며, numerical tests 및 chemistry validation 미실행.


2026-10-30: van 't Hoff API의 reaction thermochemistry를 optional constant ΔCp까지 확장. 정확 적분항은 `ΔCp/R*(ln(T/Tref)+Tref/T-1)`이며, ΔCp 제공 rows가 있을 때 별도 review gate를 요구한다. ΔCp가 없으면 constant-ΔH 식을 그대로 쓴다. `ReactionEnthalpyReference`의 ΔCp support, per-reaction output, units 및 formula docs/source catalog reference를 연결하고 synthetic example에서 다중 반응 ΔH/ΔCp 배선을 선언했다. 모델 390·capability 650·schema 821·source 451 수 및 47/101 progress 불변. 이후 정적 generation/source audit 수행; 물리 calculation/chemical validation/tests/package/HPC는 미실행.


2026-10-30: Added optional caller `delta_cp_reference_J_mol_K` to aqueous van 't Hoff history. The rate relation is integrated to include constant-ΔCp correction; constant ΔH remains the path when Cp is omitted. A separate review is required whenever any reaction supplies ΔCp. Supported per-knot activity coefficient inputs retain provider/revision/configuration digest, source record and license lineage, with either caller gamma history or an explicit fixed-gamma applicability gate. The TUDOdata 2024 mean-gamma dataset remains metadata-only: underlying-literature rights are unresolved and its mean coefficient is not a species-specific gamma vector. Existing public NORSOK simulation data is documented only as a same-family code comparison source, not independent physical validation. Updated data reuse and thermochemistry guides. Regenerated source/capability/schema/model reference/backlog and static source audit: 390 models·159 interfaces·101 partial (650 total)·821 schemas·452 source bases; 101 rows·265 paths·380 components with no missing/AST/stale/unmapped entries. No solver calculations, tests, physical qualification, package/HPC run. Scope progress 47/101 (46.5%).

2026-10-30 추가 구현: van 't Hoff aqueous history에 온도에 따라 선형 변하는 reaction heat-capacity difference 입력 `delta_cp_slope_J_mol_K2`를 추가했다. 기준 `delta_cp_reference_J_mol_K`와 동반 입력을 요구하고 `temperature_dependent_reaction_heat_capacity_reviewed`를 별도 gate로 분리했다. `ln K` 적분식, output lineage, SI 단위, JSON schema, capability/source catalog, synthetic registry example 및 API/method documentation에 연결한다. OECD NEA TDB temperature-correction 문서를 근거로 연결하고 caller 열화학 값은 추정하지 않는다. 이는 계산 코드 범위를 넓히는 증분이며 WCO2 전체 구현 완료나 검증을 뜻하지 않는다. 수치계산·테스트·패키징·HPC 미실행; scope 진행률은 47/101(46.5%) 유지.

2026-10-30 선형 ΔCp 식 점검: analytical antiderivative에서 온도 항 `Tref²(1/Tref−1/T)` 부호를 확인해 코드·method formula·가이드의 동일 표현을 맞췄다. 소구간 전개에서 이 기울기 항이 0차/1차/2차를 상쇄하고 양의 3차항으로 시작함을 손으로 대조했다. 이는 계산/수치 검증 실행이 아니므로 회귀 테스트와 독립 수치 benchmark는 일괄 검증 시 남아 있다.

2026-10-30 추가 WCO₂ 연동: `integration.aqueous_vant_hoff_saturation_history`는 digest-pinned computed van't Hoff equilibrium history의 각 knot를 기존 saturation screen으로 연결한다. 사용자 제공 CandidateSolid, Evidence 및 정확한 시간별 solubility 입력 digest를 받으며, 각 source record의 온도 지원을 확인하고 knot 간 Ksp 보간을 금지한다. activity-standard-state/complete species/temp-applicability review와 upstream asset/location/time context 일치를 검사한다. supersaturation을 phase selection, precipitation extent, kinetics 또는 corrosion으로 해석하지 않는다. 계산 테스트·모델 실행은 미실행; 전체 scope 완료율은 유지한다.

2026-10-30: Registered `integration.aqueous_vant_hoff_saturation_history`, composed from a computed digest-pinned van't Hoff AssessmentResult, exact history clocks, temperature-supported per-knot solubility candidates and evidence/data digests. Candidate IDs and ion-activity-product term definitions remain fixed across knots; Ksp is never interpolated. Each knot calls the existing activity/saturation screen. Added three public schema contracts, a synthetic-only executable example, WCO2 capability wiring, source-path audit mapping and API/scope documentation. Static generation: 391 models·159 interfaces·101 partial (651 capabilities)·452 source bases·827 schemas. Source/path audit: 101 rows, 266 paths, 381 components; missing/AST/stale/unmapped=0. Public source-boundary audit passed its allowlist check, not a legal clearance. Code-incomplete count and strict progress remain 4 and 47/101 (46.5%). No calculation/test/package/HPC execution.

2026-10-30 API contract hardening: the van't Hoff saturation adapter now verifies every internal equilibrium knot contract, status agreement, time and temperature alignment, and its history ID before calling the existing saturation screen. The guide explicitly limits digests to content integrity/linkage, not producer authentication or physical correctness. Static registry/schema/model-reference generation and the 101-row scope audit were rerun; no model calculation or tests were executed.
2026-10-30 추가 구현: `solve_crevice_transport_recession_feedback()`에 opt-in 구간 내부 aperture fixed-point 경로를 추가했다. 각 반복은 caller relaxation으로 끝 aperture guess를 정하고 cell/face cross-section 및 wall-area-density 이력을 구성해 보존형 moving-volume diffusion/reaction transport를 다시 푼다. signed cellwise metal-wall ledger에서 endpoint를 갱신하며 aperture 상대 잔차와 반복 예산을 통과한 구간만 commit한다. 반복별 입력·결과 digest와 commit 상태를 남기고, moving-geometry time basis를 segment별로 분리했다. 축방향 advection/hydraulic feedback은 geometry-aware flow가 없어 차단한다. review 기록을 기본 fixed-geometry/remap 모드와 별도로 분기해 검토 의미가 뒤섞이지 않게 했다. 문서·source/capability description을 갱신했다. 정적 재생성 결과 391 models·159 interfaces·651 capabilities(101 partial)·828 schemas·455 source bases이며, source audit 101 rows·266 paths·381 components에서 missing/AST/stale/unmapped=0이다. 계산 테스트·패키징은 보류한다.

2026-10-30 수용액 활동도 표준상태 교정: Davies/SIT 자기일관 질량작용 반복에서 molality 기준 `gamma_m`을 molarity 기준 질량작용기에 직접 전달하던 부분을 수정했다. `gamma_c = gamma_m / w` 변환을 log 공간에서 적용하며, `w`는 caller 공급 kg-water/L-solution이다. 결과에는 molality/molarity 두 gamma를 모두 표시하고, binary64 지원 이탈은 `out_of_scope`로 종료한다. 한글 API·방법 설명과 수식 근거 source basis를 연결했다. 정적 재생성은 391 models·159 interfaces·651 capabilities(101 partial)·828 schemas·456 source bases다. 소스 감사 101 rows·266 paths·381 components에서 누락·AST·stale·unmapped=0. 수치 계산과 테스트는 보류한다.

## 2026-10-30 — 외부 조성 의존 활동도 callback

2026-10-30 외부 조성 의존 활동도 공급자 연결 완료: `integration.aqueous_external_activity_provider` callback API와 `ExternalAqueousActivityIteration` schema를 catalog에 등록했다. JSON-native provider 응답의 ordered species/molality gamma/ionic strength와 provider/request/result digest를 검증하고 `gamma_c=gamma_m/w`로 기존 mass-action solver의 damped fixed-point 반복에 연결한다. Pytzer는 옵션 caller provider 자료로만 기록했으며 GPLv3/beta upstream 문서를 notice에 인용했다. Pytzer 코드는 포함·import·실행하지 않는다. 정적 생성: 391 models·160 interfaces·652 capabilities(101 partial)·829 schemas·458 source bases; scope audit 101 rows·267 paths·382 components, missing/AST-unavailable/stale-or-unmapped/unmapped=0. 전체 진행률 47/101(46.5%) 유지. 테스트·계산·패키징·HPC 미실행.

2026-10-30 외부 조성 의존 활동도 exact-knot history 구현 완료: `integration.aqueous_external_activity_speciation_history`가 caller가 준 시간 절점마다 별도 mass-action system과 동일한 composition-dependent provider를 연결한다. 공통 species/formula·reaction/constraint topology 및 provider identity/revision/configuration/single-ion convention을 확인하고, 각 절점의 온도별 parameter record/Evidence를 허용한다. 리뷰 부족이면 호출 전 `needs_data`; callback 실패/비수렴이면 실패 knot와 이전 prefix만 반환하며 전체 이력은 computed가 되지 않는다. 사이 구간 보간·속도론·수송·상 선택은 수행하지 않는다. Schema/catalog/API/source/backlog 및 scope-source audit 연결 완료. 정적 생성 결과 392 models·160 interfaces·653 capabilities(101 partial)·830 schemas·459 source bases; audit 101 rows·268 paths·383 components, missing/AST-unavailable/stale-or-unmapped/unmapped=0. 전체 목표 코드-scope 진행률 47/101(46.5%) 유지. 계산 테스트·패키징/HPC는 사용자 지시대로 보류.

2026-10-30 external activity transport adapter: added `ExternalAqueousTransportActivity` and `build_external_aqueous_transport_activity_callback()` for restricted transport. The caller provider receives each exact mouth/cell state as ordered species molality, charge-derived ionic strength, time, temperature, fixed solvent-mass basis and a canonical request digest. Its returned provider/config/record lineage, species order, echoed request digest and ionic strength are checked before a molality-standard-state gamma vector is returned for chemical-potential correction. The callback retains a rolling digest transcript and evaluation count. Scope is fixed-temperature, fixed solvent conversion and caller-declared single liquid; it does not solve local speciation, charge balance, precipitation, phase change, or electrochemical kinetics. Schema/API/source/scope docs are connected. No examples, tests, numerical calculations, package builds, or HPC jobs were run. Progress remains 47/101 (46.5%).

2026-10-30 restricted transport 외부 활동도 연동 추가: 같은 caller-owned activity provider를 mouth/cell 조성에 적용하는 `ExternalAqueousTransportActivity` 및 `build_external_aqueous_transport_activity_callback()`를 구현했다. mol/m³ 상태를 고정 caller 물 질량 기준 molality로 환산하고, 전하 기반 ionic strength와 species 순서를 확인한 뒤 request digest를 echo하는 JSON provider 응답의 gamma_m을 반환한다. transport solver 진입부에서 callback 종 순서 및 configuration digest를 request와 대조한다. Provider 예외와 유효하지 않은 gamma vector는 transport solver 경계에서 정제된 오류 유형과 실패 구간을 포함하는 `out_of_scope` 결과로 변환하며, 구간별 geometry 적분에서는 완료된 구간 수를 보존한다. provider callback은 실행 횟수와 request/result rolling digest를 보유하고, restricted transport 반환값의 activity callback lineage에 runtime trace를 포함한다. callback lineage SHA는 불변 설정 필드에만 적용하고 runtime transcript는 별도 누적 digest로 연결한다. 온도·용매량 고정과 단일 액상 review 아래의 chemical-potential gamma correction이며 local speciation, 침전, 상변화 또는 반응속도 계산은 아니다. 정적 카탈로그는 392 models·160 interfaces·653 capabilities(101 partial)·831 schemas·459 source bases; scope audit 101 rows·268 paths·383 components, missing/AST-unavailable/stale-or-unmapped/unmapped=0. 전체 코드 범위 추적 47/101(46.5%) 유지. 테스트·계산·패키징/HPC 미실행.

## Registry runtime dependency injection

Added declared `ModelSpec.runtime_dependency_names` plus exact-key runtime injection in `ModelRegistry.run()`/`run_json()` and top-level `evaluate()`. JSON inputs keep provider objects out of persisted payloads; `describe()` exposes the names required by caller. The aqueous external activity history now declares `activity_provider`, so the registry AssessmentResult wraps the computation correctly. Missing or extra dependencies fail before evaluator entry. This does not authenticate callback code: provider lineage remains the request's caller-supplied ID/revision/configuration/record digest and Evidence.

2026-10-30 registry provider injection and example repair: `ModelSpec` now declares exact `runtime_dependency_names`, and `ModelRegistry.run()`/`run_json()` accept only the named Python dependency mapping; `describe()` exposes these requirements. The external activity history declares `activity_provider`, and its synthetic Python example invokes the assessment registry with that provider. Added the history contract to `examples/model_inputs.json` and regenerated the model reference. Structural inventory is 392 registered models, 391 JSON input examples, and one prior-result-dependent model with a compositional Python example. Static catalogs remain 392 models·160 interfaces·653 capabilities (101 partial)·831 schemas·459 source bases; scope audit 101 rows·268 paths·383 components with missing/AST/stale/unmapped=0. No model calculation, tests, packaging or HPC were run. Strict code-scope progress remains 47/101 (46.5%).

2026-10-30 gasket independent rectangular box envelope: added `fabrication.gasket_leakage_box_envelope` with Evidence-bound calibration/box records, rights review, explicit independence/coverage declarations and strict no-extrapolation support. It evaluates node contact-pressure bounds and all interior calibration knots, positive area endpoints, common differential-pressure bounds and knots, and entrywise nonnegative calibration-flux bounds to produce exact total-leak extrema and witness states under the declared piecewise-bilinear map. This is a deterministic box guarantee only; it does not model correlated uncertainty, covariance inference, seal acceptance or physical qualification. Added a synthetic JSON input and method/API explanation. Static output: 393 models·160 interfaces·654 capabilities(101 partial)·833 schemas·460 source bases; audit 101 rows·268 paths·383 components, missing/AST/stale/unmapped=0. Strict code-scope progress remains 47/101 (46.5%). No tests, calculations, packaging or HPC were run.
2026-10-30 전기화학→벽두께 handoff: `integration.electrochemical_metal_loss_wall_thickness_history`를 추가했다. 입력은 computed metal-loss AssessmentResult 전체 digest, 첫 구간 시작시각에 맞춘 Evidence-linked measured baseline, caller 공통 벽면적, 유효 밀도 source/revision/record/hash/Evidence와 material/coverage/area/projection/use review를 요구한다. 각 interval의 exact ordered selected reaction set과 upstream exposed-area 대 common-area tolerance를 검사한다. gross anodic mass만 density×area로 환산해 baseline 두께에서 차감하고 cathodic equivalent/signed net은 상쇄하지 않는다. margin, baseline limit state 및 최초 crossing interval bracket을 제공하며 시간 보간·기간 외 extrapolation·remaining life·acceptance·probability는 주장하지 않는다. Registry/schema/source/capability/model reference와 Korean API/method/scope/manual 문서를 연결했다. 정적 산출물: 394 models, 160 interfaces, 655 capabilities(101 partial), 834 schemas, 461 source bases. Scope audit 101 rows·268 paths·383 components에서 missing/AST/stale/unmapped=0. 코드-scope 진행은 47/101(46.5%) 유지; 이 bounded adapter는 101개 code-incomplete 분류 항목을 닫지 않는다. 계산·회귀 테스트·수치/물리 검증·HPC·패키징은 실행하지 않았다.
2026-10-30 CREV source-clock origin handoff: `integration.electrochemical_metal_loss_to_crevice_geometry` no longer requires the upstream metal-loss history to start at source time 0. The first source knot is now the initial geometry reference and maps to elapsed time 0; a nonzero source origin requires an explicit `source_clock_origin_rebasing_reviewed` decision. Output preserves the origin and each source-to-elapsed time pair. This allows absolute or run-relative source clocks while keeping the geometry solver's elapsed-time convention explicit; it does not alter current integration or rerun upstream electrochemistry. Capability/source catalogs, schema, model reference, dedicated guide, remaining-work ledger and continuation note were refreshed. Static inventory remains 394 models·160 interfaces·655 capabilities (101 partial)·834 schemas·461 source bases. Static scope audit: 101 rows·268 paths·383 components; missing/AST/stale/unmapped=0. Scope progress remains 47/101 (46.5%). No model calculations, tests, physical validation, HPC submission or packaging were run.

2026-10-30 CREV hydraulic endpoint-path integration: `CreviceTransportRecessionFeedback` now has a separately reviewed mode that combines bounded within-segment aperture fixed-point iteration with steady planar-slit flow at the start aperture and each guessed end aperture. It sends transport a local-time callback that linearly joins those endpoint face-velocity vectors, binds the path to endpoint input/result digests and pressure-interpolation lineage, and requires explicit flow-continuity, pressure-path, endpoint-velocity-path and reversal/distal-inflow review. Each segment still commits only after aperture convergence; transient momentum and fully simultaneous geometry/flow/chemistry are outside scope. Corrected stale catalog/backlog descriptions that had called the feature diffusion-only, then regenerated static schema/catalog/source/reference/audit outputs. No transport execution, test, package or HPC job was run; code-scope progress remains 47/101 (46.5%).

2026-10-30 reusable CREV velocity-path contract: added `PlanarSlitEndpointVelocityPath` as a strict callable contract for reviewed interpolation between hydraulic endpoint fields. It pins ordered face vectors, global times, endpoint input/result digests, pressure/fluid source identities and pressure-knot bracket lineage. Validation checks matching face counts, finite values, pressure bracket containment, consecutive knot indices and interpolation fraction consistency. Its callback accepts local elapsed seconds and refuses extrapolation. `solve_crevice_transport_recession_feedback()` now passes this object to `solve_restricted_transport()` so provider/configuration/source digests come from the same immutable contract. Added public schema and updated capability/source descriptions and Korean API notes. Static generation: 395 models, 160 interfaces, 656 capabilities (101 partial), 837 schemas, 462 source bases; source audit 101 rows, 271 paths, 385 components, all missing/AST/stale/unmapped counts zero. No calculation, test, packaging or HPC run; strict progress remains 47/101 (46.5%).
## 2026-10-30 — Gasket 가중 유한 시나리오 moments

`GasketLeakageWeightedScenarioMoments`를 추가해 digest-bound joint leakage scenarios와 명시적 ordered weights를 연결했다. 입력 가중치는 양수이며 1로 합쳐져야 하고 자동 정규화하지 않는다. 계산은 유한 집합의 가중 평균·모집단 분산·표준편차와 extrema/witness를 보고하며 확률·신뢰구간·연속 bound 해석을 부여하지 않는다. evidence, provider revision, rights 및 review gate를 API에 포함하고 registry, schema, capability/source catalog, implementation scope audit와 한국어 API/범위 문서에 연결했다. 수치 검증과 테스트·패키징·HPC는 실행하지 않았다.

## 2026-10-30 — Findley 수명 곡선 API 연결

`CriticalPlaneFindleyCalibratedLife`가 기존의 유한 평면 Findley 파라미터 계산을 caller 제공 단조 parameter-life curve와 연결한다. 정렬 순서, canonical digest, provider Evidence 및 rights Evidence를 확인하고, `log(parameter)`-`log(cycles)` 구간 선형 보간으로 제공 support 안에서만 수명을 반환한다. material/load basis, 단조성, support/no-extrapolation, 권리, 계산 승인 gates를 추가했다. 프로젝트 합성 Findley fixture를 재사용하는 Python wiring example과 registry, capability/source catalog, schema export, model reference 및 FAT residual scope 문서를 연결했다. 정적 audit는 101 rows/274 source paths/387 components, missing paths·AST failures·stale/unmapped symbols·unmapped components 0이다. 수치 테스트·계산·패키징·HPC는 실행하지 않았다.

## 2026-10-30 — 잔여 CREV/WCO2/GASK 계산 경로 추가

`degradation.crevice_lumped_exchange_reaction_history`는 고정 체적의 well-mixed 단일 종 교환+1차 sink ODE를 caller piecewise-constant 조건에서 폐형식으로 전파하고 analytically integrated mass ledger를 반환한다. `chemistry.layered_scale_history_stack_transport`는 서로 다른 caller 단일상 scale-thickness histories를 동일 exact knot에서 ordered layer stack에 결합하고 기존 diffusion limit 계산을 호출한다. `fabrication.gasket_contact_pressure_screen`는 digest-pinned flange contact field와 caller pressure screening window 사이 node-wise margin을 반환한다. 세 calculator는 각각 공간/반응망 완결성, 상 자동 탐지/공침, sealing acceptance를 주장하지 않는다. 관련 source/capability/catalog/schema/model reference와 scope audit를 재생성했다. 정적 범위 audit는 101 rows·277 paths·391 components에서 missing path, AST-unavailable, stale/unmapped symbol, unmapped component가 0이다. 수치 테스트·예제 실행·패키징·HPC는 실행하지 않았다.



2026-10-30 추가 구현: `corrosion.planar_slit_transient_hydraulic_history`와 `fatigue.multiaxial_weighted_life_scenario_moments`를 구현하고 registry, capability/source catalog, 공개 schema, standalone synthetic input 및 scope audit에 연결했다. 전자는 digest-bound geometry·pressure·fluid evidence로 구간 상수 lumped momentum history를 계산하고 후자는 기존 finite multiaxial life scenario set의 caller weighted moments를 계산한다. 두 모델 모두 descriptive/calculation boundaries 및 rights review를 기록한다. Dataset release rights 정적 감사 도구와 보고서를 추가해 63 dataset·276 asset, 구조 오류 0·경고 31을 명시했다. warning은 원자료 checksum 18건 누락, asset size 10건 미고정, 파일명 재사용 3건이다. 체크섬은 형식만 확인하며 실제 원격 bytes와 대조하지 않았고 archive 최종 내용도 아직 검사하지 않았다. 정적 재생성 현황: 402 models·167 interfaces·670 capabilities(101 partial)·847 schemas·469 source bases; 395/402 standalone JSON inputs. 소스 감사 101 rows·281 paths·393 components에서 missing/AST/stale/unmapped 0. 넓은 코드 완료 표시는 47/101(46.5%)로 유지한다. 테스트·수치 계산·패키징·HPC는 실행하지 않았다.


2026-10-30 구현 보강: transient slit hydraulic API는 단일 cell 요청도 허용하도록 계약 하한을 수정했고, 구간 적분 체적에 더해 초기 0 기준 부호 포함 누적 체적 history와 out-of-scope 성공 prefix를 반환한다. 문서와 JSON Schema를 다시 생성·동기화했다. 정적 schema 확인에서 cell ID/길이 모두 단일 항목 허용을 확인했고, 101행·281 경로·393 구성요소 source audit에서 missing/AST/stale/unmapped는 0이다. 이는 contract/source 검사이며 계산이나 시험 실행이 아니다. scope 진행률 47/101(46.5%)은 그대로다.


2026-10-30 추가 연동: `matintegrity.bind_planar_slit_transient_hydraulic_interval()`은 digest 검증된 transient slit history의 한 구간을 동일한 local-clock restricted transport 요청에 연결하고, exact exponential Q(t)를 face-velocity callback으로 제공한다. Callback 구성 digest와 원 결과 digest·시작 시간·time basis를 bound request에 기록한다. cell-aperture-to-face 재구성은 caller review가 필수이며, 구간 시간 외삽은 거부한다. transport chemistry/recession으로 hydraulic state를 갱신하지 않는 one-way 연결이다. Registry model이 아닌 typed Python integration helper로 공개 API와 capability interface에 연결했다. 정적 catalog 현황: 402 models·168 interfaces·671 capabilities(101 partial)·847 schemas·469 source bases; source audit 101 rows·281 paths·394 components에서 missing/AST/stale/unmapped 0. `catalog_component_drift_reconciled=1`은 이번 새 helper component를 감사 목록에 연결한 단일 reconcile이며 이후 상태는 audit 데이터에 반영됐다. 넓은 구현 진행률은 47/101(46.5%) 유지한다. 계산 시험/패키지/HPC는 실행하지 않았다.


2026-10-30 추가: transient slit flow history와 restricted transport를 여러 연속 구간에서 묶는 `bind_planar_slit_transient_hydraulic_history_series()`를 추가했다. upstream AssessmentResult input/result digest를 한 번 검증하고, 각 interval에 대응하는 local-clock request와 analytic face-velocity callback을 순서대로 반환해 전체 결과를 구간마다 반복 해시하는 비용을 제거한다. 각 callback 구성과 원 결과 digest, global start time/time basis는 bound request에 남는다. docs, root public API, capability interface 및 implementation-scope component map을 연결했다. 카탈로그 정적 재생성은 402 models·169 interfaces·672 capabilities(101 partial)·847 schemas·469 source bases다. 재실행한 source audit 101 rows·281 paths·395 components에서 missing/AST/stale/unmapped/component-drift 0이다. 계산 시험·수치·패키징은 수행하지 않았고 전 범위 완료율은 47/101(46.5%) 유지다.


2026-10-30 연동 무결성 보강: transient hydraulic binder가 digest를 계산된 것으로 간주하지 않고, 요청된 각 interval에서 입력 aperture/pressure와 출력 row를 대조하고 slit 저항·관성·평형 유량·연속 flow endpoint를 재구성해 일치하지 않는 upstream AssessmentResult를 거부한다. 여러 구간 series 경로는 전체 input/result digest를 한 번 확인한 뒤 interval별 내부 일관성을 검사한다. 문서에 무결성 검사와 미검증 한계를 기록했다. static source audit는 101 rows·281 paths·395 components, missing/AST/stale/unmapped/component-drift 모두 0이다. 계산 테스트·수치 검증·패키징은 실행하지 않았으며 넓은 코드 진행률 47/101(46.5%) 유지다.


2026-10-30 구현: `chemistry.fixed_fugacity_carbonate_history`를 추가했다. 각 ordered time knot의 caller 제공 FixedFugacityCarbonateEquilibrium 요청을 기존 carbonate-only solver에 순차 전달한다. Sample/assessment ID와 asset/location/time basis, strict clock, max point budget를 고정한다. 첫 needs_data/out_of_scope에서 중단하고 완성 prefix·실패 시간·sample/status를 유지한다. 절점 사이 보간·유한 gas inventory·kinetics·scale·corrosion rate를 추정하지 않는다. Registry, synthetic JSON input, schema, model reference, wet-CO₂ capability category, API/method 문서 및 audit component map을 연결했다. 정적 생성 현황: 403 models·169 interfaces·673 capabilities(101 partial)·848 schemas·469 source bases; 396 standalone JSON inputs. Source audit 재실행은 101 rows·281 paths·396 components, missing/AST/stale/unmapped/component-drift 0. Code-target progress remains 47/101(46.5%): the broad WCO₂ scope still has additional kinetics, activity/phase, transport and validation gaps. Tests, numerical examples, package builds and HPC were not run.


2026-10-30 추가 구현: `thermo.co2_pure_fugacity_history`는 같은 CoolProp backend로 고정된 ordered pure-CO₂ PT 요청들을 exact time knot에서 순서대로 평가한다. 첫 review/dependency/state failure 또는 표준 CoolProp 계산 예외에서 멈추고 성공 prefix, 실패 sample/time/index, 요청 digest 및 provider error type을 남긴다. Time interpolation이나 mixture interaction은 계산하지 않는다. Registry, synthetic JSON input, schema, model reference, wet-CO₂ capability category, API/전용 문서와 audit map에 연결했다. 정적 현황 404 models·169 interfaces·674 capabilities(101 partial)·849 schemas·469 source bases; 397/404 standalone JSON inputs. 재실행 source audit 101 rows·281 paths·397 components, missing/AST/stale/unmapped/component drift=0. 전체 구현 추적은 47/101(46.5%) 유지한다. 계산 테스트, CoolProp 설치 확인, 수치 검증, 패키징, HPC는 실행하지 않았다.


2026-10-30 성능 구현: 	hermo.co2_pure_fugacity_history의 ordered PT 절점 계산에서 검토를 통과한 첫 절점에 CoolProp AbstractState를 생성하고 후속 절점에서 재사용한다. review 누락은 기존과 같이 dependency 초기화 전에 
eeds_data로 반환하며, 점별 phase 판단·digest·실패 prefix 계약은 그대로 유지한다. 회귀 테스트/수치 실행은 하지 않았다. 전체 구현 추적은 47/101 (46.5%)이며 이번 최적화만으로 카운트는 증가하지 않는다.

2026-10-30 구현: `thermo.co2_mixture_fugacity_history`를 추가해 혼합기체 CO2 성분 fugacity를 ordered exact-time knots에서 산출한다. History는 성분 ID/순서와 backend를 고정하고 조성·온도·전체압력은 절점별 값으로 허용하며 CoolProp AbstractState를 재사용한다. 절점별 조성/EOS/phase review, context 일치, point budget, 첫 실패 시 prefix 및 request digest를 보존한다. registry, synthetic example/context, API/method note, capability catalog 및 public schema 연결을 추가했다. 계산 테스트, CoolProp 설치/실행, 수치 검증 및 패키징은 하지 않았다. 넓은 scope 진행표시는 47/101(46.5%) 유지.

2026-10-30 데이터 공개 재현성 보강: `data/catalogs/datasets.json`에서 정확한 `data/raw/<dataset-id>/<filename>` 경로로 존재하는 14개 asset의 local snapshot SHA-256/byte count pin을 보완했다. NIST CORR-DATA와 compiled pipe-burst의 기존 SHA-256은 재계산 값과 일치했다. 다른 12개 hash는 공급자 검증값이 아니라 local bytes pin이다. `scripts/verify_local_dataset_asset_pins.py`를 추가하고 선택한 7개 dataset ID의 14 assets를 재검사해 모두 checksum/size match를 얻었다. Release metadata audit 경고는 checksum 누락 6, byte size 누락 6, basename 중복 3이다. Raw/derived/evidence는 manifest에서 계속 제외되고 권리 허가는 추론하지 않는다. 전체 code-scope 진행률은 47/101(46.5%) 유지; 계산 테스트·패키징은 미실행.
## 2026-10-30 — B-dot 활동도와 질량작용 반복 연성

독립적으로 구현한 `AqueousBdotIteration`/`BdotSpeciesParameter`가 caller-owned extended Debye–Hückel 계수로 기존 일반 수용액 mass-action system을 반복한다. `build_bdot_transport_activity_callback()`은 위치별 molality gamma를 restricted transport에 공급하고, `build_bdot_transport_saturation_callback()`은 그 활동도 모델을 caller Ksp screen과 competing-solid kinetic transport에 연결한다. 단일 액상·완전 종 목록·molality/molarity standard-state mapping·온도 match·provider/source SHA 및 parameter support review를 strict contract에 넣었다. 비수렴/전하불균형/ionic-strength support 이탈은 computed equilibrium을 반환하지 않는다. API 문서, USGS method reference metadata, schema/catalog, top-level Python exports와 fabricated-only synthetic input을 추가했다. 정적 생성은 406 models·171 interfaces·678 capabilities(101 partial)·852 schemas·470 source bases이며, scope audit 101 rows/281 source paths/401 components에서 missing/AST/stale/unmapped와 2차 capability drift는 모두 0이다. 코드 테스트·계산 검증·패키징은 미실행, 넓은 범위 진행은 47/101(46.5%)다.


## 2026-10-30 — B-dot 수용액 exact-knot 이력

`integration.aqueous_bdot_speciation_history`가 시점별 complete `AqueousBdotIteration`을 순서대로 독립 solve한다. 정확한 time/temperature/parameter mapping, computational-use authorization, 고정 species order·reaction·constraint topology, 동일 provider/revision, knot 간 무보간 검토를 요구한다. 온도별 계수·평형상수·constraint target·water basis·parameter file hash는 완전한 knot 입력에 명시할 때만 달라진다. 실패하면 직전 계산 prefix와 실패 knot를 보존하고 불완전 history를 computed로 승격하지 않는다. registry, schema, capability catalog, 합성 JSON/context, API/method와 continuation docs를 연결했다. 정적 카탈로그는 407 models·171 interfaces·679 capabilities(101 partial)·853 schemas·470 source bases·400 standalone inputs다. scope audit 101 rows/282 source paths/402 components에서 missing/AST/stale/unmapped 및 2차 catalog drift는 모두 0이다. 계산 테스트·수치 실행·패키징은 미실행이며 전체 scope 진행은 47/101(46.5%)다.

## 2026-10-30 — B-dot history to Nernst adapter

The existing mass-action-to-crevice-Nernst adapter now accepts either the composition-bound aqueous mass-action history or the exact-knot B-dot speciation history. It verifies input/result and knot-history digests, aligned B-dot knot time/temperature/parameter hashes, shared asset/location/scope/clock identity, exact species/activity coverage, and a caller-provided standard-potential vector. For B-dot history, the emitted lineage identifies the activity-history digest and kind rather than labeling it as a raw composition inventory; the upstream result retains the knotwise parameter hashes. The adapter remains a sequential half-cell potential handoff and does not feed current back into chemistry. Updated the API guide, method note, capability reference, and synthetic wiring example. Static catalogs remain 407 models/171 interfaces/679 capabilities/853 schemas/470 source bases; scope audit is 101 rows/283 paths/402 components with zero missing, AST, stale/unmapped, or catalog-drift findings. No tests, example execution, numerical verification, or packaging were run; overall implementation remains 47/101 (46.5%).

## 2026-10-30 — 경쟁 고체 평형과 caller-parameterized SIT 반복

`CompetitiveSolidSITIteration`과 `chemistry.competitive_solid_sit_equilibrium`을 추가했다. 고정-gamma 경쟁 중성 고체 optimizer의 결과 molality에서 caller 제공 방향성 SIT 상호작용으로 gamma를 재계산하고, `gamma_c = gamma_m / w`로 molarity standard state에 되돌리는 damped fixed-point API다. 온도별 A·epsilon 계수·Evidence·provider digests, 전하잔차·이온강도 한계, phase/parameter review 및 비수렴 종료를 계약에 포함했다. 현재 `activity_reference_concentration_mol_m3=1000`만 adapter 범위로 받아 표준상태 가정을 제한한다. 합성 wiring 예제, 전용 사용 안내, API/schema/catalog/reference를 생성했다. capability catalog 409 models/681 entries, schemas 854개다. 수치 시험, 테스트, 패키징은 실행하지 않았다. 넓은 구현 추적은 code-incomplete 분류가 그대로 남아 진행률 47/101(46.5%)이다.

## 2026-10-30 — SIT 경쟁 고체상과 반응수송 operator split 연결

`CompetitiveSolidEquilibriumTransport.initial_cell_equilibria`가 Davies와 SIT 요청을 모두 받도록 확장했다. 수송 provider/revision configuration identity를 phase activity request와 대조하고, 모든 cell에서 phase law·Ksp·SIT interaction/Evidence·용매/표준상태 설정이 같도록 digest 비교한다. 각 고정-geometry transport output knot에서 기존 SIT 또는 Davies competitive-equilibrium evaluator를 dispatch하며 phase projection, 종별 농도·고체재고 및 누적 수지 ledger를 기존 방식으로 유지한다. 전기화학 adapter lineage에 활동도 모델을 기록하고 SIT 합성 wiring 예제와 API 문서를 추가했다. capability 409 models/171 interfaces/101 partial, schemas 854개. `scripts/export_schemas.py`는 API contract import와 schema 생성을 수행했으며 계산시험·pytest·HPC·패키징은 실행하지 않았다. wet-CO2의 자동 반응/상 발견, 연속 연성 및 검증은 여전히 미완성이라 넓은 지표는 47/101(46.5%)이다.
## 2026-10-30 — 경쟁 고체 B-dot 평형과 수송 연동

`CompetitiveSolidBdotIteration`과 `chemistry.competitive_solid_bdot_equilibrium`을 추가했다. 온도 일치 범위의 caller A/B, 종별 ion-size 및 b 계수와 Evidence SHA를 사용하고, liquid molality에서 B-dot gamma를 구해 `gamma_c=gamma_m/w`로 molarity 표준상태에 변환한다. 물 질량, 1 mol/L reference concentration, charge residual, ionic strength support, fixed-point 수렴을 모두 명시한다. Davies/SIT/B-dot 중 하나로 셀별 경쟁 고체 평형을 고정형상 수송의 각 output knot에서 operator-split 적용하도록 확장하고 전기화학 lineage에 법칙 ID를 기록한다. 합성 API/수송 예제, 전용 안내, capability/schema/API reference를 추가했다. 정적 카탈로그 410 models, 171 interfaces, 101 partial / 682 capabilities, 855 schemas다. 범위 감사는 101행/286 source paths/403 components, missing·AST·stale/unmapped·catalog drift 0이다. 이 모델은 기존 wet-CO2 code-incomplete 범주를 좁히는 bounded implementation이며 자동 reaction/phase discovery·동시 연성·실험 검증은 남아 있어 전체 지표는 47/101(46.5%)로 유지한다. numerical tests, pytest, HPC와 packaging은 미실행이다.
# 2026-10-31 implementation increment — row lineage and two composition APIs

The wet-CO2 simulation-grid adapter also now supports a digest- and Evidence-bound finite scenario calculation from provider corrosion-rate rows to caller-defined uniform wall-loss histories. Its use requires explicit scenario mapping, constant-rate, physical-scope and finite-set review. It returns `out_of_scope` if a scenario's proposed loss exceeds the measured baseline. It makes no field-performance, probability, acceptance or qualification claim.

The gasket extension evaluates caller-ordered exact-time snapshots with the bounded elastic two-spring joint load model. It reports a first supplied snapshot below a user threshold and preserves the valid prefix when the model leaves closed-contact scope. This finite history does not infer inter-knot events or gasket leakage/seal acceptance.

The static scope/path audit now links the recent Findley, crevice, wet-CO2 and gasket integration APIs into the 101-row scope inventory. It reports 301 paths, 418 components and zero missing paths, AST parse gaps, stale symbols or unmapped components. This is traceability evidence only.

An independent read-only review found and closed four contract gaps: exact geometry-boundary remap time and from/to digest checks; wet-CO2 output unit declarations; wet-CO2 baseline/limit Evidence-origin gates; and the required `cycle` unit on every Findley life assessment. The reviewer did not run tests or calculations. Updated schemas, sources, capabilities and model reference are being regenerated; separate Hangang contract tasks are queued against the corrected snapshot.

A new caller-defined corrosion-rate time-history API now integrates piecewise-linear nonnegative rate knots by exact interval trapezoids. It carries Evidence and digests per knot, enforces a measured baseline and scoped run context, bounds itself to supplied support, and brackets the first required-thickness crossing under the reviewed reconstruction. It does not extrapolate or assign probability/acceptance.

The galvanized polarization reader now has a typed row view for its three catalogued workbook assets. Each row carries provider-file MD5, local SHA-256, original parser row, signed current in provider and parser units, and attribution/authorization lineage. The potential reference stays unresolved, and no Tafel/corrosion-rate estimate is added. Zenodo API metadata reports CC BY 4.0; the rights check is recorded for 2026-10-31.

## What changed

- Registered a typed, local-only cathodic-protection sample-row audit and exposed its authorization contract and sample schema.
- Added local-only and authorization-digest fields to pressure-decay samples. MetroPT-3 rows now carry the matching authorization digest, and documentation labels local hashes as copy-integrity pins rather than publisher checksum verification.
- Added an ordered finite-cycle API that connects digest-consistent calibrated Findley life results to explicitly caller-reviewed linear Miner accumulation. It preserves block order and reports only the first integer threshold crossing in the supplied blocks.
- Added a crevice composition bridge that binds computed transport segments to the exact campaign and geometry input. It reports cell inventory and a volume-weighted summary while retaining local fields and both sides of geometry remapping.
- Regenerated model schemas, source bases, capability catalog and package catalog synchronization.

## Boundaries

No raw dataset rows are copied into public packages. The cathodic-protection and pressure-decay row APIs require attribution and local-use authorization. The fatigue calculation assumes the caller's linear, sequence-independent model; the crevice bridge performs bookkeeping and does not solve chemistry. Neither provides acceptance, probability or qualification.

## Validation record

No tests, example programs, numerical runs, package build, or Hangang result retrieval were performed. Catalog generators were run to create schemas and metadata. Hangang tasks are tracked separately in `CONTINUATION_KO.md` and remain `submitted_not_validated` or in asynchronous staging/retry until reported otherwise.

## 2026-10-31 — GSA 수명·Crevice 국소 inventory·Gasket 임계 이벤트·스케일 전달 병렬 구현

독립 코드 작업 네 갈래를 병합했다. GSA 곡선 연결은 유한 평면 GSA와 동일 재료상태의 caller calibration만 연결하고, curve support 내부 log-log interpolation으로 제한했다. Crevice 국소 inventory는 기존 transport cell/knot과 별도 수행된 aqueous mass-action result를 digest로 묶고 cell 부피를 적용해 species mole, charge-equivalent 및 가능한 elemental inventory를 기록한다. Gasket threshold API는 digest가 있는 계산 누설 이력에 caller rate window를 적용해 선형 재구성 조건부 초과 구간을 표시한다. 다층 scale history series API는 서로 다른 상별 두께 이력을 caller 지정 diffusion layer에 연결해 공유 exact knot마다 정상 확산 한계를 평가한다. 각 모듈별 한국어 설명서 및 registry/schema/source/capability/model-reference 경로를 갱신했다.

Hangang snapshot freeze 전 정적 검토에서 layered-scale adapter의 `AssessmentResult`에 없는 최상위 assessment ID 필드 접근 두 곳을 발견해 `values["assessment_id"]` 추적으로 수정했다. 보정 후 scope digest/path audit를 재생성했다. 정적 산출: 945 schemas, 510 source bases, 726 capabilities. 정적 scope 추적은 101행, 309 source paths, 426 components이며 누락 경로·AST 불가·stale/unmapped·unmapped component가 0이다. 이 정적 감사를 테스트/실행/물리 검증으로 간주하지 않는다. 테스트, 수치 실행, 예제 실행 및 패키징은 보류했다.

## 2026-10-31 — 부식률 이력과 FTA 이벤트 교환

부식률 두께 이력 결과와 기존 FTA basic-event contract를 연결하는 adapter를 추가하고 ModelSpec, 3개 public schema, source/capability catalog 및 model reference에 통합했다. `required_thickness_crossing_within_history_support` 조건은 caller가 이름과 문장으로 명시한다. 확률·ProbabilityMeaning·conditioning·FTA 공통 scope·Evidence·rights boundary는 별도 입력이고, deterministic corrosion result에서 확률을 생성하지 않는다. `IntegrityEventBasis`와 `FaultTreeBasicEvent`를 함께 구성하며, 요청/결과 digest, asset/location/clock/horizon, 두께 기준 및 원천/확률 근거를 유지한다. Registry RunContext도 요청의 asset/location/time basis에 묶어 다른 자산·시간기준을 거부한다. 빠진 입력은 `needs_data`, 다른 model/digest/scope 입력은 거부한다.

정적 catalog는 727 capabilities(448 calculators, 178 interfaces, 101 partial), 948 schemas, 511 source records로 재생성했다. static scope audit는 101행/310 경로/427 구성요소에서 missing path, AST, stale symbol, unmapped component가 0이다. 이 문서 증거는 실행이나 FTA 수치검증이 아니다. 테스트·수치 실행·예제·패키징은 보류한다. Hangang snapshot은 별도 immutable task로 제출 중이며 job/result는 `CONTINUATION_KO.md`에 기록한다.

## 2026-10-31 — COQTEL 전기화학 행 typed lineage

기존 checksum-pinned COQTEL electrochemistry parser를 재사용하는 local-only typed row iterator를 추가했다. 행별 Pydantic contract는 provider 순서, 1-based EC/State 행 식별자, repeated timestamp 표식, experiment/specimen, 전류·전위·elapsed time, source archive SHA-256, canonical source-row SHA-256, CC BY attribution, authorization digest와 `Evidence`를 보존한다. 상태별 pit 크기는 제공되지 않으므로 `None`으로 남기며, 전기화학 값에서 corrosion rate나 material performance를 만들지 않는다. 파일구조/행 수만 반환하는 metadata-only `ModelSpec`도 제공한다. dataset manual과 Python API 문서를 추가했다.

## 2026-10-31 — scale precipitation finite reactant inventory ledger

`chemistry.scale_precipitation_inventory_budget`는 caller가 계산한 digest-pinned 단일상 scale history의 각 interval gross precipitation을 exposed-area 기반 formula-unit demand로 바꿔 Evidence-bound 초기 reactant inventory 및 interval별 공급과 비교한다. 모든 interval을 ordered exact support에 맞추고, 화학량론·면적/물리범위 mapping·재고 접근성·계산 권한 review가 없으면 `needs_data`로 닫는다. 첫 재고 부족 interval은 commit하지 않으며 성공 prefix와 species별 부족량만 남긴다. 용해 재생, speciation, 평형, transport, feedback, corrosion rate 또는 wall loss는 추정하지 않는다. ModelSpec RunContext asset/location/time basis는 상류 scale result와 일치해야 한다. API/schema/source/capability/model-reference 및 정적 scope 감사에 연결했다. 정적 산출물은 729 capabilities·954 schemas·512 source bases, scope audit 101 rows/311 paths/428 components로 재생성했다. Hangang 계약 검증은 별도 제출 대기/진행 상태이며 계산 결과가 아니다. 모델 테스트·계산·예제·패키징은 수행하지 않았다.

카탈로그상 dataset license는 CC BY 4.0 (`reviewed_license`)이며 선택된 HDF5 파일의 MD5/byte-size와 기존 parser의 SHA-256 pin이 있다. raw archive는 읽거나 복사하지 않았고, public distribution에는 원자료 또는 point rows를 추가하지 않았다. registry/schema/catalog sync는 중앙 통합 작업에서 진행한다. 테스트, 예제 실행, numerical calculations, package build는 이 변경에서 수행하지 않았다.

## 2026-10-31 — 열전달 데이터 typed rows 및 질량작용 finite envelopes

Mendeley thermal-rod dataset의 기존 CSV parser에 archive SHA/byte pin 검사와 `ThermalRodObservationRow` lineage wrapper를 추가했다. `source_row_order`, provider CSV row, 6개 ambient-excess 온도차 채널, controller count 단위, archive/member/row digest, Evidence, attribution/auth digest 및 `local_only`를 유지한다. Official Mendeley record를 2026-10-31 다시 확인해 dataset이 선언한 CC BY 4.0과 DOI를 기록했다. raw ZIP/point rows는 열거나 배포하지 않았다. Controller count는 power/heat flux로 바꾸지 않는다.

수용액 fixed-topology scenario envelope는 2–256개의 caller 완전 입력계를 별도로 풀고 정확히 선언된 finite cases에 대한 비가중 activity/concentration extrema를 제공한다. 대안 reaction-topology envelope는 같은 용액·온도·species fixed state·balance constraints 안에서 2–64개의 caller 네트워크를 비교한다. 두 API 모두 어떤 사례가 실패하면 전체 요약을 보류하고 성공 prefix와 최초 실패를 유지한다. Sampling, weighting, probability, confidence, global bound, auto-network selection, phase, kinetics 또는 corrosion 추론은 없다.

Scale diffusion metal-loss bound는 computed steady scale flux ceiling과 caller가 근거로 묶은 productive reaction branches, metal stoichiometry 및 물성 Evidence를 연결한다. area flux를 conditional uniform penetration-rate 및 기간 손실 ceiling으로 변환하고, unknown branch allocation은 최대 metal/transported-species 비율로 보수 상한을 만든다. RunContext asset/location/time basis는 upstream transport AssessmentResult와 일치해야 한다. 이는 actual corrosion rate나 remaining life가 아니다.

중앙 schema/catalog/source/model-reference 생성과 정적 scope audit를 별도 병렬 작업으로 수행했다. 테스트·실제 계산·예제 실행·패키징 및 Hangang 결과 조회는 하지 않았다.

## 2026-10-31 — fixed-fugacity carbonate to scale kinetics bridge

Caller-provided activities and temperature-supported Ksp now bind exact knots from an existing fixed-fugacity carbonate assessment to one selected solid saturation screen; only a complete successful saturation history proceeds to the existing caller surface-scale kinetic API. Context and canonical result digests are checked, and the adapter does not select phases or infer activities, Ksp, kinetic constants, corrosion, protection, or life. Registry/schema/catalog synchronization and a separate Hangang synthetic contract snapshot are being handled centrally. No tests or numerical calculations were run.

## 2026-10-31 — crack-arrest CC BY source typed rows

공식 Mendeley record(https://data.mendeley.com/datasets/g69875w65c/1)의 CC BY 4.0 선언을 2026-10-31 재확인했다. 기존 `fracture_data.read_crack_arrest_series` 앞에 archive filename/byte/SHA-256 pin을 요구하는 typed adapter를 추가했다. 결과행은 C1/C2 family, filename-token 온도 provenance, signed force/displacement, zero, source CSV 순서와 행 번호, archive/member/row digest, attribution/auth digest 및 Evidence를 보존한다. 두 specimen을 합치지 않고 fracture toughness, FAD, acceptance 또는 failure probability를 추정하지 않는다. 원 archive/point rows는 공개 배포물에 포함하지 않는다. 테스트·원자료 접근·패키징은 수행하지 않았다.

## 2026-10-31 — pipeline guided-wave typed samples

기존 pinned guided-wave parser 위에 선택한 acquisition/frequency의 `GuidedWaveSampleRow` iterator와 metadata audit ModelSpec을 추가해 중앙 registry/API/source/schema/catalog에 연결했다. 원 샘플 순서와 반복 거리, 원 전압 신호, outer/nested/workbook 및 row digest, Evidence·attribution·local-only authorization을 보존한다. 손상 단계·시각·온도·감육·부식률·POD는 유추하지 않는다. 권리 검토일은 dataset catalog 기록의 2026-10-27이며 원자료/point rows를 배포물에 넣지 않는다. tests/calculation/package work are deferred.

중앙 static outputs after guided-wave registration: 735 capabilities (456 models, 178 interfaces, 101 partial), 969 public schemas, and 518 source records. Static scope audit remains 101 rows/314 paths/431 components with zero unmapped entries. Code progress remains 47/101 (46.5%); no runtime checks were run.

## 2026-10-31 — CEIT 및 DEIS typed-row 자료 어댑터

CEIT 균일부식장 JSON에 기존 parser를 재사용하는 local-only typed row API를 추가했다. 원 observation 순서, provider array index, caller가 선택한 ToF/온도 단위와 sample clock, file/row digest, Evidence 및 권한 digest를 보존한다. 단위·시계 선택이 없거나 소스 데이터에 없는 온도·두께 정보는 비워 두고 신호에서 감육·부식률·수명을 도출하지 않는다. Dataset catalog의 Zenodo DOI 10.5281/zenodo.13897090 권리 기록(CC BY 4.0)을 따른다.

WE43/AZ31 DEIS matrix 자료에도 기존 bounded ZIP/member parser를 감싸는 typed rows를 추가했다. parser row/column 순서 및 native numeric values, archive/member/row digest, Evidence와 local-only authorization을 보존하며 axis/time/frequency/physical units는 해석하지 않는다. Dataset catalog의 Zenodo DOI 10.5281/zenodo.10482561 권리 기록(CC0-1.0)을 따른다.

두 어댑터는 registry, standalone schemas, source/capability catalogs, generated model reference 및 package catalog에 연결됐다. 공개 raw data를 복사하지 않았다. 중앙 생성 결과는 738 capabilities·980 schemas·521 source records이며, code-only scope는 47/101 (46.5%)로 유지한다. Tests, numerical calculations and packaging remain deferred.

Hangang mock-contract snapshots for the Ksp record gate, CEIT typed rows and DEIS typed rows are being transferred in separate immutable archives. Their partitions exercise request rights/schema, exact lineage, and fail-closed behavior using synthetic/mock parser outputs only. Job IDs/results have not yet been reported or queried; these snapshots are not physical validation.

## 2026-10-31 — alloy metrics typed rows and crevice spatial chemistry

The Figshare compilation reader now emits typed, ordered local-only rows with explicit byte/MD5/SHA pin checks and caller authorization. It preserves censoring and unit fields and explicitly does not claim underlying publication observations are redistributable under the compilation license. A caller-local registry audit does not redistribute workbook rows.

The spatial crevice mass-action workflow applies the existing local equilibrium solver to every caller-provided exact cell system and runs the existing volume ledger only after all cell systems compute. Both APIs are schema/catalog connected. Static outputs now show 740 capabilities, 984 schemas and 523 source records; source-scope audit shows 101/314/431 with no missing/unmapped items. Runtime tests and numerical calculations remain deferred.

Scope traceability was expanded for both latest calculation adapters: `integration.fixed_fugacity_carbonate_to_scale_kinetics` maps under `degradation.wet_co2`, and `integration.crevice_spatial_mass_action_workflow` under `degradation.crevice_chemistry`. The regenerated static audit now reconciles 101 scope rows, 316 source paths and 433 components, zero missing/AST/stale/unmapped entries, and zero catalog drift. Their parent categories remain incomplete; coding progress remains 47/101 (46.5%).

## 2026-10-31 — GSA Miner and fracture-toughness typed reader

Added a caller-cycle-group GSA Miner campaign that composes the existing Ince–Glinka GSA life mapping with the existing Miner fraction calculator after all group life calculations complete. It requires exact common calibration/material/scope identity and explicit cycle-count/linear Miner reviews; it does not count cycles or fit calibration. The Mendeley fracture dataset adapter preserves parser source partition labels, workbook row order, units, Evidence and local-only authorization. A static integration review caught and corrected a `test` versus `testing` label mismatch before a fracture Hangang archive was frozen. Latest counts are 742 capabilities, 989 schemas, 525 source records; static audit 101/317/434 with no missing/unmapped items. Runtime tests and package work remain deferred.

## 2026-10-31 — 병렬 계산 API·공개 데이터 연결 증분

- crevice: 침전 고체 체적을 caller-reviewed 면적/coverage 기준 간극 history에 매핑하고, 셀별 후보 고체 포화도와 양의 `log10(Q/K)` 시간 노출을 보존하며, 침전 유래 aperture를 기존 sequential transport geometry contract로 바꾸는 API를 추가했다. 모두 upstream digest, 시간/영역/셀 순서를 검사한다. phase selection, precipitation amount, morphology, kinetics, simultaneous flow/chemistry/geometry는 주장하지 않는다.
- multiaxial fatigue: 두 engineering shear-strain 좌표의 닫힌 finite polygon 면적과, 최대 대수 주응력축의 sample-to-sample projective rotation을 계산하는 별도 descriptors를 추가했다. 경로 재구성, material damage/life, qualification은 하지 않는다. principal-axis solver는 유한 stress 입력 크기에 따른 overflow를 줄이도록 입력 tensor를 크기 정규화한다.
- gasket: caller가 검토한 single continuous monotone sign-change bracket을 외부 provider callback으로 좁히는 API를 registry runtime dependency로 연결했다. provider query/receipt digest 및 Evidence를 보존하고 bracket만 반환한다.
- 공개 데이터: PLOS Figshare CT110 weld/base-metal supporting workbook(9,331 bytes, CC BY 4.0)의 publisher MD5와 local SHA-256을 확인하고 구조만 읽었다. 세 온도 행, WM/BM 열, 빈 worksheet 두 개를 확인했으며 모델 적합이나 점별 배포는 하지 않았다. 원본은 ignored `data/raw` 아래 local-only로 유지하고 typed-row reader와 attribution/권리 문서를 공개 source에 연결했다.
- 중앙화: registry, generated capability/source catalogs, 1,037 public contract schemas, API guide, model reference 및 package catalog synchronization을 갱신했다. scope 추적에 관련 code paths를 연결하고 정적 재조정 중이다.
- 검증 경계: 수치 테스트, 모델 계산, 예제 실행, 패키징은 사용자 요청대로 실행하지 않았다. API addition은 parent scope 완료나 과학적 검증으로 계산하지 않는다.

## 2026-10-31 — 대량 병렬 구현 및 중앙화

- 신규 계산 API를 동일 저장소 내 3개 독립 작업 스트림(wet CO₂, crevice transport/chemistry, multiaxial fatigue)에서 동시에 구현하고, 통합 작업은 registry/schema/source/capability/API docs/model reference를 묶음 생성했다.
- 구현 범위에는 wet-CO₂ film coefficient, 유한 gas/liquid inventory, disjoint-zone transfer, carbonate-only speciation, reactive film, condensate state; crevice Arrhenius calibration-to-history/flux, multispecies boundary callback, wall-transfer inventory, fixed-geometry solid volume and boundary remap, saturation-path average kinetics; Papadopoulos P1 screen/calibration/life/Miner, Carpinteri–Spagnoli finite screen/life, periodic Fourier tensor reconstruction/rates/work/work-life가 추가됐다.
- 공개 catalog: 801 capabilities (522 models, 178 interfaces, 101 partial), 1,075 public schemas, 586 source records. Package metadata sync 완료.
- Static scope traceability: 101 rows/353 source paths/472 components, missing paths 0, AST unavailable 0, stale/unmapped symbols 0, unmapped components 0.
- 잔여 의존성: fully coupled evolving geometry–momentum–chemistry/phase solvers; composition-specific EOS/electrolyte/kinetics and wall-law providers; material-matched fatigue data/curve transfer; external FE/contact and rights-cleared validation data. New submodels do not mark broad categories complete.
- 목표 대비 tracked code estimate: 47/101 = 46.5%; scope classification 4 broad code-incomplete, 51 data/validation-pending, 46 provider-dependent.
- 요청에 따라 tests, physical/numerical model calculations, examples, HPC submissions and packaging were not run.
## 2026-10-31 — 응축막 재고 및 geometry-aware 크리비스 화학 provider

`integration.wet_co2_condensate_film_history`는 caller가 준비한 net retained-water flux를 고정 patch의 액상 면적 재고, uniform-equivalent 두께, wet duration과 dryout 경계에 적산한다. condensation/retention/drainage/evaporation 각각의 기구를 생성하지 않는다. `integration.crevice_geometry_aware_aqueous_chemistry_provider`는 기존 recession fixed-point 안에서 시도 aperture에 따라 caller aqueous reaction callback을 재평가한다. species 순서, support, digest 계보, 반응 stoichiometry 원소/전하 균형을 확인하지만 고체상 석출/용해, 활동도, phase selection 및 완전 동시 유동 모델은 아니다. 두 기능의 공개 contracts, capability/source records, API/model 문서 및 package catalog를 생성·동기화했다. 정적 범위 추적은 101행·354경로·475구성요소, 누락·AST 실패·미매핑 0이다. 수치 테스트, 실제 계산, HPC 제출 및 패키지 빌드는 하지 않았다.

## 2026-10-31 — 공개 배포 메타데이터 감사 보완

정적 공개 소스 경계 감사는 2,716개 파일에서 통과했고 `data/raw`, `data/derived`, `data/evidence`, `artifacts`, `tmp` 제외 규칙을 확인했다. dataset release-rights 메타데이터 감사 중 구형 CT110 Figshare 레코드의 CC BY 선언, 권리 증거 URL, 취득정책, 검토일 및 selected asset 연결이 누락된 점을 발견해 catalog를 정규화했다. 후속 감사는 68 dataset / 291 assets, 오류 0, 경고 16으로 통과했다. 경고는 checksum·byte-size 미고정 일부와 source 간 중복 basename이다. 두 결과는 metadata/source-archive 규칙의 구조 점검이며 법률 검토나 wheel build가 아니다.

## 2026-10-31 — 가변 응축액/용존 CO₂* 재고 연동

`integration.wet_co2_variable_condensate_transfer_history`를 등록했다. caller 지정 기·액막 전달량, 액상 volume flux, 응축 유입액의 CO₂* 조성, 완전혼합 유출을 exact piecewise-constant interval로 받아 액체 체적과 용존 CO₂* 재고를 함께 갱신한다. 실제 응축량·기상 reservoir depletion·선택적 증발·반응·종분포·공간구배는 생성하지 않는다. 공개 schemas/capability/source/API guide/model reference 및 package catalogs를 갱신했다. 전체 capability는 805 (525 models/179 interfaces/101 partial), schemas 1,080, source records 590이다. 정적 scope traceability는 101행/357경로/476구성요소, 미매핑 0이다.

## 2026-10-31 — 유한 기상/가변 액상 CO₂* 이력과 공개자료 후보

`integration.wet_co2_finite_gas_variable_liquid_history`를 registry/API에 연결했다. 사용자 지정된 유한 기상 fugacity capacity, 기·액막 계수, Henry 계수, 액상 부피 유량과 응축 유입 CO₂* 조성으로 gas fugacity, well-mixed liquid inventory와 두 상 사이 누적 전달을 SciPy DOP853으로 적분한다. solver revision/설정 digest, 면적기준 재고수지 closure 및 허용오차를 기록한다. EOS, 응축 생성, 반응, pH/speciation, 공간 변화 및 부식률은 포함하지 않는다.

Dryad DOI 10.5061/dryad.fn1r084의 downhole-tool 자료를 공개자료 후보로 catalog에 추가했다. 공식 정책은 accepted datasets를 CC0로 배포하고 depositor가 재사용 권리를 보증하도록 명시한다. 이번 단계에서는 원본을 받거나 열지 않았고 metadata-only 취급이다. 조건·원시 관측/계산 출력 구분·문헌 중복은 미확인이라 reader나 보정자료로 쓰지 않는다. 연계 논문 DOI는 10.1098/rsos.181899로 공식 Dryad record 및 PMC에서 확인했다.

현재 capability/catalog counts: 806 (526 models, 179 interfaces, 101 partial), schemas 1,082, sources 594. Static scope traceability: 101 rows/358 paths/477 components, missing/unmapped 0. Dataset rights audit: 69 records/291 assets, errors 0, warnings 16. 기능테스트·실제계산·패키징은 수행하지 않았다.


## 2026-10-31 — 크리비스 고체 침적 provider 카탈로그 연결 및 메타데이터 점검

`integration.crevice_geometry_aware_solid_deposition_provider`를 capability/source catalog와 공개 contract schema에 연결하고 model reference 및 package catalog를 동기화했다. caller가 제공한 원소·전하 균형 reaction extent와 Evidence로 고정된 고체 inventory/molar volume을 사용해 geometry fixed-point 반복에서 고체 체적 변화와 aperture를 연결한다. endpoint operator-split 방식이며 Ksp, 침전속도, phase selection, morphology 또는 연속 동시 용액-고체 반응은 추론하지 않는다.

중앙 생성 결과는 807 capabilities(526 models, 180 interfaces, 101 partial), 1,086 schemas, 595 source records다. 정적 scope audit은 101행/359경로/478구성요소, 누락·AST 오류·미매핑 0이다. 공개 경계 감사는 2,730개 파일에서 통과했고 rights metadata 감사는 69 dataset/291 asset, 오류 0/경고 16이다. 기능 테스트, 모델 계산, 예제, HPC 작업, package build는 수행하지 않았다. 상위 범위 추정은 47/101(46.5%)이며 하위 API 추가량과는 별도 지표다.
## 2026-10-31 — 병렬 chemical-cleaning 및 gasket 접촉압력 API 등록

두 독립 계산 API를 추가하고 중앙 경로에 연결했다.

- `fabrication.chemical_cleaning_bath_component_inventory`: caller가 선언한 세정조 용액 부피와 성분 질량에 대해 이벤트 순서대로 보충, 완전혼합 액 배출, 외부에서 계산된 성분 소비를 적용한다. 재고 부족 또는 0 액량에서 잔류 성분이 있으면 `needs_data`로 중단한다. 반응속도, 약품 적합성, 세정효율, 폐액 분류 및 승인 기준은 계산하지 않는다.
- `mechanics.gasket_nominal_contact_pressure`: 동일 범위로 검토된 압축 반력과 caller 제공 유효면적 또는 원환 지름에서 평균 압력 F/A를 계산한다. 국부 접촉장, 누설률, gasket sealing, 코드 승인 또는 접촉 비선형성은 예측하지 않는다.

두 모델 모두 기본 registry, standalone JSON input schema, capability/source catalogs, model reference, package data catalog, API guide 및 101-item scope traceability에 연결됐다. Scope audit은 101행/361개 source path/478개 고유 구성요소, 누락·AST 실패·미매핑 0이다. 생성 카탈로그는 809 capabilities(528 models, 180 interfaces), 1,088 schemas, 597 source records다. Dataset rights metadata audit은 69 datasets/291 assets, 오류 0/경고 16이다. 후속 공개 경계 감사는 2,736개 파일에서 통과했다. 넓은 scope 완료 추정치 47/101(46.5%)는 상위 범위 기준이라 그대로 유지한다. 테스트, 예제, 수치 계산, HPC 제출, wheel/package 빌드는 보류했다.
# 2026-10-31 — CMSX-6, 활동도, 다축 피로, LH2DT 병렬 API 연결

상위 101개 범위 진행률은 47/101(46.5%)이다. 이 분모는 완결 처리된 부모 capability만 세므로 하위 API가 추가되어도 값이 바뀌지 않는다. 혼선을 없애기 위해 향후 개발 보고는 parent completion과 하위 구현 증분을 따로 기록한다.

- `data.bam_cmsx6_creep_lis_typed_rows`: provider가 공개한 CMSX-6 LIS 단일 자산을 로컬에서만 읽고 원행 순서, 원시 토큰, 구문 분석 형태, 행/file/auth digest와 Evidence를 보존한다. creep law나 수명은 추론하지 않는다. dataset catalog의 Zenodo `10.5281/zenodo.14750432` 및 CC BY 4.0 표기를 그대로 참조하고, raw 원본과 third-party 문서의 권리는 별도 경계로 유지한다.
- `chemistry.aqueous_extended_debye_huckel_activity`: caller Evidence로 제공된 A/B·이온크기 매개변수만 사용하는 수용액 활동도계수 계산기다. 용매·온도·이온강도·표준상태 적용범위 밖의 입력은 계산하지 않는다. 계수 표나 외부 데이터베이스는 포함하지 않는다.
- `fatigue.wang_brown_reviewed_excursion_parameter`: caller가 고른 유한 shear 평면과 검토된 closed-cycle reversal arc에서 normal-strain excursion을 반영하는 파라미터를 산출한다. cycle counting이나 수명 곡선은 포함하지 않는다.
- `integration.lh2dt_dynamic_network_node_state_history`: 사용자 소유 공개 MIT LH2DT 동적네트워크 결과의 버전·구성·결과 digest와 node 매핑을 요구하고 선택된 node의 열역학 상태만 전달한다. 수소 유입·취화·벽 응답은 추론하지 않는다.

이번 작업에서 registry, schema-export 선언, scope traceability 및 API 안내서를 연결했다. 카탈로그 재생성 전의 상태이며 테스트·예제·실제 계산·패키지 빌드·HPC 제출은 수행하지 않았다. 구현 진척을 부모 비율과 혼합해 표현하지 않는다.

같은 시각 확인한 이전 Hangang job `1186453`의 결과는 job-level FAILED (`1:0`)였다. source-order mock-only partition은 통과했지만 data-import assessment partition은 `qualification="data_import"`가 `AssessmentResult`의 Literal 목록에 없어서 실패했다. result contract에 `data_import`를 추가했다. 이 결과는 신규 모델들의 runtime/물리 검증으로 계산하지 않으며 재실행하지 않았다. 이번 카탈로그 생성 후 새 result schema를 다시 export해야 한다.
## 2026-10-31 — 추가 계산 API 병렬 구현과 중앙 연결

병렬 구현으로 6개 계산/어댑터 API를 추가했다: `integration.wet_co2_carbonate_transport_boundary_history`, `fatigue.dang_van_finite_parameter_life`, `integration.multi_bolt_joint_to_flange_contact_request`, `integration.gasket_joint_spatial_resultant_balance`, `integration.wet_co2_finite_gas_wall_reaction_inventory_history`, `fatigue.wang_brown_parameter_life_fit`. 함께 `integration.extended_debye_huckel_transport_activity_callback`도 crevice/wet-CO₂ 하위 연결로 추적한다. 새 구현은 각각 carbonate exact-knot boundary composition, same-condition caller fatigue curve mapping, multi-bolt to spatial flange request, force/moment contact resultants, finite CO₂* gas/liquid/wall-loss balance, caller-curve Wang–Brown life fitting을 제공한다. 외부 자료·계수·경계조건이 필요한 곳은 Evidence와 digest로 caller 제공을 요구하며, 범위를 넘어 수명·누설·qualification을 주장하지 않는다.

Registry, schemas, source/capability catalogs, generated model reference, package catalog, API guide 및 implementation scope trace를 갱신했다. 현재 catalog는 829 capabilities (547 models, 181 interfaces, 101 partial), 1,110 schemas, 619 sources다. 정적 scope audit는 101 rows, 380 paths, 499 components, missing/AST/stale/unmapped 0을 기록했다. 넓은 상위 완료율은 47/101 (46.5%)이며 새 하위 구현은 해당 parent 전체의 완료 기준을 닫지 않았다. Static catalog generation exposed and fixed an invalid `pydantic.Literal` import and missing source-basis records.

계산 테스트, 과학/실험 검증, 예제 실행, 패키지 빌드 및 HPC 제출은 수행하지 않았다. 새 API는 아직 실행·수치검증을 통과한 것으로 해석하면 안 된다.

## 2026-10-31 — 가스켓 fatigue, 간극 확산, CO₂ 혼합전위 계산 추가

추가 병렬 구현: `fabrication.gasket_bolt_cyclic_damage`는 다중 볼트 명목 인장 응력 이력에 caller source/rights-bound Basquin·Goodman·Miner 조건부 screen을 연결한다. `transport.crevice_component_diffusion_1d`는 고정 형상 단일 성분 간극의 backward-Euler finite-volume 확산과 경계/재고 질량수지를 제공한다. `integration.wet_co2_film_transport_limited_mixed_potential`은 digest-pinned 탄산염 경계·caller Butler–Volmer 계수·steady Fick film-cap으로 제한한 zero-current potential을 푼다. 각 기능은 registry, capability/source catalogs, public schemas, model reference, package catalog 및 scope audit에 연결했다. Integration 과정에서 public schema exporter가 수동 계약 목록을 사용한다는 점을 확인해 새 계약들을 명시적으로 추가했다.

현재 생성값: 832 capabilities (550 models, 181 interfaces, 101 partial), 1,129 public schemas, 625 sources. Static scope: 101 rows/383 source paths/502 components, missing paths/AST/stale/unmapped 0. 상위 범위 구현 추정은 47/101(46.5%)로 유지한다. 신규 API들은 계산 및 독립 검증 전이며, 요청에 따라 테스트·계산·패키징·HPC는 실행하지 않았다.

## 2026-10-31 — 원주 접촉, 다종 CO₂ 재고 및 Crossland 증분

병렬 구현으로 세 계산기를 더했다. `fabrication.gasket_circumferential_contact_continuity`는 caller threshold와 periodic ring geometry를 써서 pressure-qualified 각도 coverage 및 wrap-around open-arc descriptors를 이산 Voronoi cell로 계산한다. `integration.wet_co2_finite_gas_multispecies_wall_flux_history`는 유한 기상 CO₂/용액 CO₂*를 caller Henry·film transfer와 연결하고, 나머지 종은 별도 inventory로 유지하며 caller 벽면 flux를 반영한다. `fatigue.multiaxial_crossland_proportional_limit_screen`는 tensor history가 caller tolerance 내 proportional path인지 먼저 확인한 뒤 same-condition caller coefficients로 finite-sample Crossland screen을 수행한다. 각각 누설/보편 수명/전체 speciation 또는 비비례 경로 결과를 추론하지 않는다.

중앙 생성값은 835 capabilities (553 models, 181 interfaces, 101 partial), 1,134 public schemas, 631 sources다. Implementation scope audit: 101 rows, 386 source paths, 505 components, missing/AST/stale/unmapped = 0. Registry, public schemas, catalogs, model reference, package catalog sync, API guide와 scope trace가 재생성됐다. broad parent completion은 여전히 47/101 (46.5%); 새 API들은 네 partial parent의 전체 잔여를 다 닫지 않는다. 이번 증분도 모델 실행, 수치/실험검증, 패키징 또는 HPC를 포함하지 않는다.

## 2026-10-31 — path variation, scale-metal coupling, gasket distribution

병렬 구현에서 `fatigue.multiaxial_deviatoric_stress_path_variation`, `integration.wet_co2_scale_corrosion_moving_geometry_history`, `fabrication.gasket_contact_distribution_statistics`를 추가했다. 첫 번째는 caller가 준 finite ordered tensor path의 adjacent deviatoric/hydrostatic variation descriptor다. 두 번째는 current scale thickness에 따라 film-limited mixed potential을 재계산하고 metal loss 및 scale inventory를 구간별 operator split으로 갱신한다. 세 번째는 caller mesh area를 검증해 contact pressure 분포 통계와 caller threshold 면적비를 요약한다. 전부 registry, schema, source/capability catalog, model reference, package catalog와 path scope에 등록됐다.

현재 카탈로그 838 capabilities (556 models, 181 interfaces, 101 partial), 1,140 schemas, 637 sources. 정적 감사는 101 rows, 389 paths, 508 components, missing/AST/stale/unmapped 0이다. 15개의 calculator/adapter와 1개 activity callback이 최근 증분에 추가됐지만 상위 scope closure는 47/101(46.5%)로 동일하다. 실행시험, 물리/실험 검증, package build, HPC 제출은 사용자의 지시에 따라 보류한다.

## 2026-10-31 — 병렬 계산 API 6개 중앙 연결

- Crossland 비례 블록 Miner campaign, wet CO₂ 유한기상 탄산/알칼리도 과도 평형, gasket contact subthreshold exposure, wet CO₂ gas-film condensation inventory, electroneutral crevice multispecies diffusion, Sines parameter-to-life mapping을 계산 API로 등록했다. 모듈별 상세 가정과 미포함 물리는 각 `docs/models/` 문서에 기록했다.
- 각 API를 Registry, 공개 schema, source derivation, capability catalog, model reference, API guide, package catalog 및 broad-scope trace에 연결했다. 생성 상태는 844 capabilities (562 models, 181 interfaces, 101 partial), 1,151 schemas, 652 sources; static audit 101 rows/395 paths/514 components, missing/AST/stale/unmapped=0이다.
- 여전히 전체 broad-scope 구현 추정은 47/101 (46.5%)다. 이번 여섯 child API는 넓은 wet-CO₂/crevice/fatigue/gasket 상위 범위를 완성하지 않는다. 테스트, 모델 계산, 예제, package build 및 HPC 제출은 보류했다.

## 2026-10-31 — 추가 병렬 계산기 3개 중앙 연결

- `integration.crevice_neutral_reactive_transport_1d`는 고정 형상 중성종 확산과 caller 가역 반응을 유한체적으로 결합했다. `fatigue.multiaxial_sines_life_fit`은 동일조건 Sines 표본의 로그-로그 적합을 제공한다. `integration.wet_co2_finite_gas_water_condensation_history`는 유한 수증기 기상재고와 벽 액막의 응축·증발을 지수해로 적분한다.
- 세 API의 registry, 공개 schemas, source derivations, scope/capability catalogs, model reference, API guide, package catalog를 생성·동기화했다. 총 847 capabilities (565 models, 181 interfaces, 101 partial), 1,159 schemas, 660 source records; scope audit 101 rows/398 paths/517 components, 누락·AST/stale/unmapped=0이다.
- broad scope는 47/101 (46.5%)이며 부모 모델 적합성이 완료되었다고 표시하지 않았다. 요청대로 계산 테스트, 패키징, HPC 제출은 실행하지 않았다.

## 2026-10-31 — 반응·열·전기화학 API 병렬 증분 중앙 연결

- `integration.crevice_neutral_reactive_transport_1d`는 중성종 확산과 caller 가역 반응, `integration.crevice_spatial_ohmic_mixed_potential`은 공간 전해질 저항과 지역 Butler–Volmer branch를 결합했다. `fatigue.multiaxial_sines_life_fit`은 표본 수명식을 적합하고 `fatigue.j2_armstrong_frederick_strain_history`는 단일 비선형 backstress J2 응답을 적분한다. Wet CO₂에는 유한 수증기 inventory 및 `integration.wet_co2_lumped_wall_thermal_condensation_history`의 벽 열/잠열 동시 적분을 추가했다.
- Registry·schema·source rationale·API guide·model reference·capability catalog·package catalog를 동기화했다. 현재 생성값은 850 capabilities (568 models, 181 interfaces, 101 partial), 1,165 schemas, 670 sources다. Static trace audit는 101 rows/401 paths/520 components, 누락·AST/stale/unmapped=0이다.
- 공개 schema 생성 도중 AF 입력계약의 미수입 `Evidence` 참조를 발견해 보완했고, 이후 전체 catalog generation을 완료했다. 모델 계산 검증·시험, 패키징, HPC는 실행하지 않았다.

## 2026-10-31 — 전기화학 손실·Prony 온도이동·동시 scale coupling 연결

- `integration.wet_co2_scale_corrosion_simultaneous_history`는 ODE 단계 안에서 film 두께에 따라 혼합전위를 재평가하고 금속손실·scale 재고·후퇴량을 함께 갱신한다. `fabrication.gasket_prony_temperature_shift_history`는 caller Arrhenius/WLF reduced time을 기존 Prony solver에 전달한다. `integration.crevice_spatial_ohmic_partial_current_metal_loss`는 digest-pinned 공간 전류로부터 양극 Faraday 등가 손실만 산출한다.
- 세 모델에 대한 registry, 공개 schemas, source derivations, capability/scope mapping, API guide, model reference 및 package catalog 생성을 완료했다. 생성 결과는 853 capabilities (571 models, 181 interfaces, 101 partial), 1,171 schemas, 677 source records; audit 101 rows/404 paths/523 components, 누락·AST/stale/unmapped=0이다.
- 계산·물리 검증과 패키징은 사용자 지시에 따라 보류했다.

## 2026-10-31 — gasket Prony 적합·crevice local equilibrium·316L 분극 reader 연결

- `fabrication.gasket_prony_relaxation_spectrum_fit`은 caller step-strain relaxation test로 bounded generalized-Maxwell 스펙트럼을 적합한다. `integration.crevice_transport_to_local_mass_action`은 digest-pinned transport concentration을 명시적 셀 constraint와 부피에 연결해 caller mass-action system을 각 지점에서 계산한다. `data.zenodo_316l_polarization_typed_rows`는 CC BY 4.0 원시 분극 곡선을 순서 보존 typed reader로 들여온다. ZIP과 raw observations는 public source 경계 밖에 남긴다.
- 중앙 registry/schema/source/model-reference/API guide/catalog를 생성·동기화했다. 현재 수치는 856 capabilities (574 models, 181 interfaces, 101 partial), 1,180 schemas, 683 sources; scope audit 101 rows/406 paths/525 components, 누락·AST/stale/unmapped=0이다.
- dataset-rights audit는 새 Zenodo reader 추가 후 70 datasets/292 assets, errors 0/warnings 17이다. Public source boundary audit는 316L reader/docs 반영 상태로 2,920개 파일에서 통과했다. 두 결과는 release metadata 경계검사이며 법률 의견 또는 계산 검증이 아니다. 테스트·계산·패키징·HPC 제출은 보류 중이다.



## 2026-10-31 — wet-CO₂ 원통 수송·피로 이전·FE 연동 및 중앙 카탈로그 증분

- `integration.wet_co2_cylindrical_scale_kinetics_to_geometry`, `fatigue.multiaxial_power_law_life_transfer`, `integration.wet_co2_cylindrical_multilayer_transport_resistance`를 추가 연결했다. 직전 중앙 집계는 880 capabilities (598 models, 181 interfaces, 101 partial), 1,271 schemas, 766 sources다. 세 모델 ID는 Registry와 capability catalog에 각각 정확히 한 번 존재함을 확인했다.
- 직전 scope trace는 101 rows, 430 source paths, 549 components, 누락/AST/stale/unmapped/component drift 0이다. Public source boundary는 3,069 files에서 통과했고 manifest SHA-256은 `493ac59cfd4f94c3fae37ffe991c0354e3115d2803348e6294b6f48fd30b3453`다. Rights metadata는 73 datasets/302 assets, errors 0, warnings 16이다.
- Broad scope 분류는 code-incomplete 2, data-validation-pending 51, provider-dependent 48로 갱신했다. Gasket와 multiaxial-fatigue 항목은 bounded 계산 경로가 구현됐으나 FE solver/provider, 재료별 법칙·자료, 전이 타당성 및 qualification이 남아 provider-dependent이며 완료가 아니다. 완료 추정은 47/101 (46.5%)를 유지한다.
- 생성 중 새 원통 transient 모듈의 `ModelSpec` import 누락과 registered geometry source ID의 source-basis 기록 누락을 발견해 보완했다. 이후 schema/capability/source 생성, scope reconciliation 및 sync가 성공했다. 모델 테스트, 물리 계산, 패키지 빌드와 HPC는 수행하지 않았다.








## 2026-10-31 — 활동도 보정 반응-수송 및 액상 전달용량 중앙 연결

`transport.crevice_activity_corrected_reactive_nernst_planck_1d`를 registry/schema/capability/source/API/scope에 연결했다. caller 시간·셀별 gamma field가 화학퍼텐셜 flux와 dimensionless activity mass-action kinetics에 함께 적용되고, 전기중성·전하/원소 보존·knotwise detailed balance를 확인한 뒤 BDF 상태계에서 함께 적분한다. cumulative reaction source를 finite-volume inventory balance에 반영하고 허용오차를 넘으면 실패 상태를 반환한다. 별도 `integration.wet_co2_cylindrical_liquid_transfer_capacity_history`는 원통형 hydraulics/geometry와 caller diffusivity를 기존 액상 전달 상관식에 연결한다.

현재 생성은 890 capabilities (608 models/181 interfaces/101 partial), 1,295 schemas, 793 sources다. scope audit 101 rows/439 paths/559 components; missing/AST/stale-unmapped/unmapped/drift 0. rights 73 datasets/302 assets, errors 0/warnings 16. 공개 경계는 3,111 files/50,243,567 bytes, SHA-256 `466692fd103da9a9175e9c94c01533c5bc0f591bbb1e998d09f901a2bdf6123f`로 통과했다. `degradation.crevice_chemistry`는 full speciation/phase discovery/qualified wall law가 남아 code-incomplete다. 테스트·수치 검증·패키징·HPC는 하지 않았다.

## 2026-10-31 — 원통형 유한 액상 전달 재고 API 연결

`integration.wet_co2_cylindrical_finite_liquid_transfer_inventory`를 registry/schema/capability/source/API/scope에 연결했다. upstream 전달용량 및 정확히 맞춘 geometry/hydraulics knot를 사용해 caller 제공 bulk/wall 액상 농도·체적과 외부 구획별 재고 교환으로 유한 두 구획 수지를 닫고, 음수 재고 또는 폐쇄 허용오차 초과를 실패 처리한다. 생성: 891 capabilities (609 models/181 interfaces/101 partial), 1,298 schemas, 799 sources. scope 101 rows/440 paths/560 components; missing/AST/stale/unmapped/drift 0. rights 73/302 (errors 0/warnings 16). public boundary 통과 3,115 files/50,314,236 bytes, SHA `02cfe06979de96f653bc8babd93b04d0abd2d43cf646276f20664963e86c5964`. `degradation.crevice_chemistry` remains code-incomplete; no tests/package/HPC.


## 2026-10-31 — 유한 액상 재고의 포화-kinetics-원통형 geometry 연결

`integration.wet_co2_finite_inventory_saturation_scale_geometry`를 registry/schema/capability/source/API/scope에 연결했다. finite liquid concentration/inventory, caller wall activities 및 Ksp, 기존 caller scale kinetics를 선택된 단일 고체의 반응 stoichiometry 및 원통형 layer geometry에 잇는다. 액상 교환, 고체 생성량/두께와 inventory closure는 digest·시간 knot·부피/면적 기반을 결합하고 재고 음수 또는 허용오차 이탈 시 닫힌다. 범위는 하나의 선택된 고체상에 제한되며 다상 speciation, 핵생성, kinetics parameter 생성 및 corrosion qualification은 수행하지 않는다.

최신 생성은 892 capabilities (610 models/181 interfaces/101 partial), 1,300 schemas, 804 sources다. scope 101 rows/441 paths/561 components; 누락·AST 실패·stale/unmapped·drift 0. rights 73 datasets/302 assets, errors 0/warnings 16. public boundary passed at 3,118 files/50,433,749 bytes, SHA `30e680027d4622d1ca5dafff3bf16639d17cc455e9f7cf51fde2e5cc7dce7a06`. wet_CO2 및 crevice_chemistry parent는 code-incomplete 유지. 테스트·수치 실행·패키징·HPC는 하지 않았다.

## 2026-10-31 — 재부동태 전위 여유 비교 API

`validation.crevice_repassivation_margin_history`를 registry/schema/capability/source/API/scope에 연결했다. caller가 제공한 운전전위와 동일 재료·환경·온도·염화물 조건·reference electrode에서 관측한 재부동태 potential을 exact knot별로 비교하고 signed margin과 결합 표준불확도 밴드 분류를 반환한다. 이 값은 확률이나 부식 예측이 아니다. 생성 893 capabilities (611 models/181 interfaces/101 partial), 1,303 schemas, 807 sources; static scope 101 rows/442 paths/562 components, 모든 누락·AST·미매핑·drift 0. rights 73/302, errors 0/warnings 16. 공개 경계 통과: 3,123 files/50,495,585 bytes, SHA `05efb9081a025246de2a46a4afcd049f46064472f64c7d8b39fa87012b68b460`. 테스트·수치 실행·패키징·HPC 미실행.

## 2026-10-31 — 유한재고 BV 혼합전위 모델 중앙 연결

`integration.wet_co2_finite_inventory_electrode_mixed_potential`을 registry/schema/capability/source/API/scope에 연결했다. caller의 BV branch set으로 lumped mixed potential을 풀고 wall-side 유한 종 재고로 반응 extent를 제한하며 bulk/wall volume과 caller 외부 source/sink에 대한 두 구획 수지를 닫는다. **이 모델은 lumped 두 구획 계산기이며 spatial PDE가 아니다.** 따라서 wet_CO2 parent는 spatially distributed transient electrode/transport 및 이동 geometry와의 직접 동시결합 잔차가 남아 code-incomplete다.

생성: 894 capabilities (612 models/181 interfaces/101 partial), 1,310 schemas, 812 sources. scope 101 rows/443 paths/563 components; missing/AST/stale-unmapped/unmapped/drift 0. rights 73 datasets/302 assets, errors 0/warnings 16. public boundary 3,134 files/50,651,804 bytes, SHA `a99fb9ce46fedfe5a4fc3aafbb3238225132001a81ee3d0a2a6997367c98c3e4`. 테스트·패키징·HPC 미실행.


# 2026-10-31 — spatial wet-CO2 and crevice duration APIs

- `integration.wet_co2_cylindrical_spatial_mixed_potential`을 registry, public schemas, source basis, capability catalog와 wet-CO2 parent component 목록에 연결했다. Radial FV transient transport, common BV zero-current potential, moving cylindrical inventory remapping 및 species/element/charge/current closure ledger를 가진 caller-bound screen이다.
- `validation.crevice_repassivation_excursion_duration_history`를 registry가 제공하는 `crevice_repassivation_margin` module의 두 번째 ModelSpec으로 연결했다. 상위 component 목록, schema export, source basis와 API index도 추가했다. 인접 exact knots만으로 definite/possible/unresolved duration을 분류하며 knot 사이 crossing 시각은 보간하지 않는다.
- 로컬 정적 결과: 896 capabilities (614 models/181 interfaces/101 partial), 1,313 schemas, 814 source bases. Scope audit 101 rows/443 paths/565 components; missing path, AST-unavailable, stale symbol, unmapped component 0; component drift 1건을 새 API link로 조정했다. Dataset catalog 73/302이며 publisher checksum 미확인 6건. Public boundary 통과: 3,137 files/50,781,720 bytes, SHA-256 `857592e3bf1a59525896b66831d73a1a8cc649f3b4755b54301169d49d03abdb`.
- 수행하지 않음: 계산기 numerical tests, examples, packaging, HPC jobs. 구조 감사와 schema/catalog generation만 완료했다.


## 2026-10-31 — competing crevice solid equilibrium

Added `chemistry.crevice_competing_solid_equilibrium` for caller-defined neutral pure solid phases competing over a shared fixed-volume aqueous state. The input binds species records, phase stoichiometry and equilibrium-constant records by digest. Sequential phase sweeps use caller-fixed activity coefficients and Ksp values; commit requires state convergence, phase presence/absence complementarity, aqueous charge closure and aqueous/solid extent closure. The model does not perform global Gibbs minimization, automatic phase discovery/speciation, kinetics/nucleation, spatial wall precipitation or corrosion prediction. Korean method and scope notes are in `docs/models/CREVICE_COMPETING_SOLID_EQUILIBRIUM_KO.md`.

Central integration added the module to `ModelRegistry`, exported three contracts, registered source basis records, added the API guide and mapped the model/path/docs into `degradation.crevice_chemistry`. Generated counts: 897 capabilities (615 models/181 interfaces/101 partial), 1,316 public schemas, 817 source bases. The first static scope run occurred before package catalog sync and showed one unmapped component; after `sync_catalogs.py`, the final scope audit reported 101 rows/444 paths/566 components, with missing paths, AST-unavailable, stale/unmapped symbols, unmapped components and drift all 0. Dataset rights audit: 74 datasets/303 assets, 0 errors/16 warnings; `data/raw`, `data/derived` and `data/evidence` pruned. Release metadata audit: 74 dataset records/817 sources, findings 0. Public source boundary passed: 3,146 files/50,894,272 bytes, SHA-256 `a2162b0ca8b3b532e8fc227da3d5eb4d04f26d80359480fc23073a0fa1f2e332`.

`degradation.crevice_chemistry` stays `code_incomplete`: global phase-stability selection, automatic speciation/activity, omitted-phase discovery, nucleation/metastability and finite kinetics, and spatial deposition/transport/wall-law coupling remain outside the implemented API. No tests, numerical executions, examples, package builds or HPC jobs were performed.
# 2026-10-31 — wet-CO2, crevice and open-data increments

- Centralized `chemistry.wet_co2_neutral_solid_formula_proposals` as a bounded neutral binary formula enumerator from caller ion formulas/charges. It lists formulas only; no stability, Ksp, precipitation or mineral identity is inferred.
- Added the Dryad formate-packer H2S/CO2 workbook local-only reader and four public contract schemas. The provider CC0 workbook is pinned by file size/MD5 and local SHA-256 outside the public boundary; no cell values are bundled. It preserves cell coordinates/types and raw row order but does not interpret figure blocks or assign conditions/units.
- Current local generation: 899 capabilities (616 models, 182 interfaces, 101 partial), 1,322 schemas, 820 source bases. Scope audit: 101 rows/445 source paths/567 components; missing paths, AST-unavailable paths, stale symbols, and unmapped components 0; one new wet-CO2 component reconciled. Rights metadata: 74 datasets/303 assets, 0 errors/16 warnings; six publisher checksums unavailable. Release metadata audit: 74 dataset records/820 sources, no findings.
- Public source boundary passed: 3,152 files, 50,934,113 bytes, SHA-256 `09a4bc7a544a264132d4c25ebfe8e1e2db2245f0da9e32cb3f40cf874e71f3b3` (structural boundary check only, not legal clearance). Tests, examples, package build and HPC were not run.



## 2026-10-31 — 로컬 병렬 증분 중앙 통합

`integration.wet_co2_cylindrical_bv_wall_recession`은 digest-pinned cylindrical mixed-potential extent를 caller alloy composition/density로 원소 용출량에 연결해 exact-knot annular bore recession으로 변환한다. 이는 one-way geometry replay다. `integration.crevice_activity_transport_spatial_phase_aperture_handoff`는 고정 형상 activity-corrected transport와 유한 phase kinetic extent를 순차 연결해 다음 구간 equivalent aperture를 만든다. `data.mendeley_mdea_co2_eis_typed_rows`는 Mendeley Data v3의 13개 experimental/simulated text asset을 local-only typed rows로 보존하고 회로 피팅을 수행하지 않는다. 각 API 한계는 전용 문서와 API_KO에 기록했다.

중앙 schema/catalog generation 완료: 902 capabilities (619 models, 182 interfaces, 101 partial), 1,328 schemas, 826 source records. Dataset catalog 75 records/316 assets; rights metadata audit passed (75 records/826 sources, findings 0, legal clearance 미주장). 정적 scope audit 101 rows/447 source paths/569 components, missing/AST/stale/unmapped 0. 전체 parent 진행률은 47/101 = 46.5%로 유지했다. 수치 테스트, package build, HPC 계산은 수행하지 않았다.

공개 source boundary 구조 감사 보고서는 `validation/public_source_boundary_audit.json`에 기록한다. 이 감사는 배포 허용목록/비공개 자산 경계만 점검하며 법률상 승인이나 모델 시험이 아니다.


## 2026-10-31 — 데이터 소비와 구간 geometry 재계산 경로

- `electrochemistry.mendeley_mdea_eis_complex_channel_conversion`은 한 파일/한 data-kind로 제한된 digest-bound EIS rows에서 caller 선택 frequency, real, imaginary channels를 복소 impedance로 바꾸고 optional provider magnitude 일치도를 검사한다. 회로 피팅이나 부식률 산출은 하지 않는다.
- `data.mendeley_internal_corrosion_doobn_typed_rows`는 CC BY 4.0 Mendeley Data v3 workbook 구조와 local rows를 해시 고정해 읽는다. 제3자 자료 재사용 가능성을 문서화했고 동봉 PDF는 내려받거나 해석하지 않았다.
- `integration.wet_co2_cylindrical_geometry_fixed_point_controller`는 caller solver를 반복 호출하는 bounded damped-Picard controller다. 물리 solver를 제공하지 않으며 내장 spatial BV evaluator를 곧바로 callback으로 쓸 수 없다는 제한을 문서화했다.
- `integration.crevice_activity_transport_sequential_aperture_campaign`은 각 caller segment 시작 geometry에서 반응수송을 다시 풀고 solid/aqueous inventory와 균일 aperture를 다음 segment에 넘긴다. 현재 scalar cross-section solver 한계로 비균일 간극은 거부하며 segment 내부 수렴 주장을 하지 않는다.
- 중앙 generation: 906 capabilities (623 models/182 interfaces/101 partial), 1,336 schemas, 832 source records. Dataset catalog: 76 records/318 assets; six provider checksums unavailable. Rights metadata audit: no findings, legal clearance not claimed. Static scope: 101 rows/451 paths/573 components; missing, AST, stale/unmapped and unmapped component counts are zero. Broad scope estimate remains 47/101 (46.5%); lower-level APIs do not falsely close either wet-CO2 or crevice parent. Tests, packaging, examples and HPC were deferred.
## 2026-10-31 — 로컬 병렬 증분: X80 데이터·가변 면적 crevice·wet-CO₂ trial geometry

`data.mendeley_x80_srb_scc_typed_rows`를 네 공개 schema 및 source record와 연결했다. reader는 v1의 세 XLS 자산을 크기/SHA-256 pin으로 검사하고 승인된 로컬 typed row만 제공한다. `transport.crevice_variable_area_activity_corrected_reactive_nernst_planck_1d`를 registry/schema/capability/source/API/scope에 연결했다. wet-CO₂ spatial BV 요청은 geometry trial mode에서 종·전하·수용액 원소 수지를 유지하면서 geometry closure를 보류하고 target bore radius와 재고 residual scale을 내보내 fixed-point callback과 연결된다. 반복 반경은 부식에 맞춰 비감소 방향이며 외경 한계를 거부한다. 생성: 908 capabilities(625 models), 1,341 schemas, 835 sources; 정적 범위 감사 101행/452경로/574구성요소, 누락·AST·stale/unmapped 0. 데이터 77건/321 assets, 오류 0/경고 16; 공개 경계 3,189 files에서 통과. 상위 범위는 47/101(46.5%) 그대로다. 모델 테스트·패키징·HPC는 수행하지 않았고, 카탈로그/경계 감사는 법적 clearance가 아니다.

## 2026-10-31 — Crevice cellwise external activity projection

Implemented `integration.crevice_local_external_activity_projection` as a runtime-provider extension of the exact-knot/cell mass-action projection. Each cell receives transported composition only to set explicitly selected constraint targets; the existing caller-owned molality activity provider and damped fixed-point solver are run independently for that cell. The inner mass-action system is rebuilt with the gamma vector actually used by the converged inner solve and its canonical digest is compared with the external solver transcript before the result is committed. Failed cells prevent the current knot from being written; earlier complete knots remain available. The final cell ledger exposes the actual molarity-standard-state gamma vector, provider/configuration identity, fixed-point iterations and residual, and a digest of the provider iteration transcript so downstream saturation calculations can trace the composition model. Added a fixed-topology and standard-state validator, explicit `activity_provider` registry dependency, public schema, source basis, parent-scope mapping and Korean model/API references. Schema/catalog generation and static scope audit succeeded: 910 capabilities, 1,345 schemas, 837 source records; 101 scope rows, 452 source-path evidence records, 576 component links, zero missing paths/AST failures/stale symbols/unmapped components. No runtime tests, numerical calculations, package build or HPC execution was performed; external activity applicability and model quality remain unvalidated.

## 2026-10-31 — external activity to crevice solid saturation handoff

Implemented `integration.crevice_external_activity_local_solid_saturation` to route a computed external-activity projection result into existing candidate-solubility screening. Its contract requires the upstream typed projection request and canonical result digest, exact knot index, caller candidate solid/Ksp list, solubility Evidence and review decisions. The evaluator independently validates exact cell identity and source transport context, standard state, gamma and concentration maps, and provider/configuration/parameter digests; it computes `dimensionless_activity = gamma_molarity * concentration_mol_L` and invokes the existing saturation screen cell-by-cell. It stops at the first failed cell while retaining the successful prefix. Registered and generated the public schema, catalog/source lineage, partial-scope mapping and Korean API/model docs. Generated totals: 911 capabilities, 1,346 schemas, 838 sources; static scope audit: 101 rows/453 path evidence records/577 component links with no missing, AST-unavailable, stale or unmapped entries. Numerical runtime tests, package build, empirical validation and HPC execution remain deferred.

Handoff review tightened the saturation adapter before numeric validation: it now requires the upstream complete knot count and commit count to match the typed request, and each cell must carry a positive provider iteration count, finite converged log-gamma residual within the declared tolerance, and valid last-response/transcript SHA-256 values. This prevents a downstream phase screen from accepting a projected gamma state without explicit convergence/provenance evidence. Static scope and public-boundary audits were rerun after the change; model calculations/tests remain deferred.

## 2026-11-01 — stage activity, CoolProp single-phase state and Ni–P dataset metadata

Parallel local coding added optional BDF-stage wet-CO₂ concentration/activity diagnostics and a separately review-gated B-dot activity refresh for current-carrying Crevice transport. The latter applies only in the spatial mixed-potential BDF mode, uses one evidence-bound constant-temperature parameter record per interval, shares coefficients across the same-stage transport/kinetics/Nernst–BV calculation, and has an independent callback budget. It does not solve stage equilibrium/speciation or phase balance. Existing endpoint defaults remain unchanged.

Added `thermo.coolprop_pure_water_single_phase_state` with an explicit exact phase declaration and digest-pinned pure-water thermophysical output. CoolProp remains optional/lazy-loaded; the provider rejects two-phase or mismatched-phase results and makes no mixture or corrosion inference. The public JSON schema and Korean API/model docs were regenerated. A static API review corrected phase-enum access to CoolProp's canonical `CP.phases.iphase_*` names against its current official docs.

Added Mendeley record `mendeley-ni-p-alkaline-electrolyzer-corrosion` as metadata-only with 155 IDs, URLs, provider filenames, sizes and provider checksums. Provider declares CC BY 4.0 but flags third-party content; original files remain unacquired. Unique catalog-local filename identities use file IDs while retaining original names.

Regenerated 1,400 schemas / 883 sources / 932 capabilities. Static scope audit: 101 rows / 466 paths / 590 components with zero path, AST, symbol or mapping findings. Rights/source metadata audits passed structurally; public source tree audit passed at 3,292 files. Bounded-code progress remains 99/101; the two parent code gaps and all qualification/independent validation work remain open. No numerical test, package build, property calculation or HPC job was run.

# 2026-11-01 — Crevice 닫힌 batch 평형 및 Wet-CO₂ BDF 전단 제거

## 구현

- `chemistry.crevice_closed_batch_aqueous_equilibrium`는 caller 초기 종별 몰수와 고정 용액 부피에서 보존 성분 제약 목표를 구성한 뒤 기존 Davies 자기일관 질량작용 solver를 호출한다. constraint별 역할 전체 분할, 정확한 0 charge row, 반응별 component 불변성, 초기 전하 inventory, nested 반복 ceiling과 최종 mol inventory closure를 확인한다. 고체·기체·reservoir·transport·기존 Crevice BDF 연결은 포함하지 않는다.
- `integration.wet_co2_cylindrical_stage_speciation_scale_feedback`에 opt-in schema v5를 추가했다. caller exact-knot wall shear와 상별 임계응력 detachment law를 Evidence와 digest로 고정한다. BDF 내부 detachment source를 제한된 phase inventory에서 빼고, detached solid/element export를 분리 추적해 수지에 포함한다. 전단은 절점 사이 left-held이며, geometry 재계산에 따른 shear 갱신은 하지 않는다. 기존 v1–v4 상태 구성을 보존한다.
- API·extension 요청 문서, 공개 스키마와 generated source/capability/reference catalog를 갱신했다.

## 정적 확인과 보류

중앙 생성은 934 capabilities, 1,408 schemas, 887 source bases를 기록했다. scope source audit는 101 rows/466 paths/590 components이며 누락 경로, AST 실패, 미연결 심볼·구성요소가 없다. 이는 모델 실행·정확성·재료/환경 qualification의 증거가 아니다. 요청대로 수치 테스트·패키지 빌드·HPC 계산/제출은 하지 않았다. 두 부모 범위 모두 `code_incomplete`로 유지된다.

# 2026-11-01 — 보존성분 Crevice BDF와 유한기체 전단-형상 연성

## 구현

- `integration.crevice_component_state_bdf`를 추가했다. 각 셀의 보존 성분 inventory가 ODE 상태이며, trial stage의 성분 몰수/고정 부피에서 Davies mass-action 제약 목표를 재구성한다. 기존 caller reaction network를 이용해 종 농도와 활동도를 얻고, 내부면 activity-gradient Nernst–Planck diffusion에서 algebraic migration gradient로 이온전류를 0으로 닫는다. caller 확산계수·면적·중심간격과 explicit component map을 사용하며 양쪽 외부면은 no-flux다. 성분별 BDF 상태와 누적 face-transfer를 별도로 적분하고 RHS·equilibrium·nested work·출력 예산, digest chain 및 잔차를 반환한다. 현 API는 혼합전위, Faradaic source, 고체상, advection, variable volume/aperture에 연결되지 않은 독립 child solver다.
- `integration.wet_co2_cylindrical_finite_gas_stage_geometry_feedback` schema v2는 v1의 finite-gas/stage chemistry/BV/scale/움직이는 원통 상태에 shear removal을 opt-in으로 결합한다. stage detachment는 phase inventory에서 별도 차감하고 export state에 적분한다. live scale inventory가 bore geometry 계산에 들어가며 scale 및 전체 gas/liquid/solid/wall 원소수지에 detached-solid export를 더한다. schema v1 기본 동작은 유지한다.
- 닫힌 batch API 입력구조 예제는 synthetic-only 비승인 초안으로 추가했다. 예제는 review/Evidence/authorization이 모두 false이고 typed request 검증이나 계산을 실행하지 않는다.
- Schema·registry·source/capability/model-reference 생성과 Crevice extension request 문서를 연결했다.

## 정적 확인과 한계

정적 생성은 935 capabilities, 1,412 schemas, 890 sources이며 scope audit는 101행·468 경로·592 구성요소에서 누락/AST/symbol/component 연결 오류 0건이다. 두 Crevice 신규 API를 explicit parent-scope map에 등록했다. 잔여 백로그의 두 `remaining_implementation` 값이 문자 배열로 잘못 들어간 데이터도 두 명확한 항목 목록으로 정규화했다. 수치/API 테스트와 실제 chemistry 계산은 실행하지 않았고, 이 코드 구조 검토를 검증 통과나 물리 qualification으로 간주하지 않는다. HPC·패키징도 실행하지 않았다.

# 2026-11-01 — Conserved-component source schedule and scale-shear data boundary

`integration.crevice_component_state_bdf` now accepts optional exact-knot, per-cell signed reaction-extent-rate schedules. At BDF trial stages rates are linearly interpolated, projected through declared aqueous stoichiometry to component-state derivatives, and also integrated as reaction extents. The external reservoir element/component/charge change is recorded separately. Request validation requires complete reaction species mapping, element and component conservation, charge closure, finite rate bounds, digest-backed Evidence, operation budget and review gates. Because the transport solver enforces zero ionic current at every interior face, only charge-neutral aqueous source reactions can enter; net charged Faradaic branches are explicitly rejected. A static unit review corrected the face-current calculation to convert equivalent molar flux to A with the CODATA Faraday constant.

Open-data research found no verified public scale adhesion/detachment measurements with an accessible file manifest and redistribution license. Updated the NORSOK M-506 catalog record and added a guide stating that its flow/shear rows are model-generated and therefore cannot validate a scale-removal law. A 2026 FeCO3/Fe3C flow paper remains an unverified data lead (publisher page blocked; no verified repository/license), so no dataset was fabricated. The Mendeley endpoint was checked using HTTP HEAD without downloading or parsing the file.

Generated catalogs: 935 capabilities, 1,416 schemas, 891 source records. Scope audit: 101 rows, 468 paths, 592 components; no missing paths/AST/symbol/component issues. Dataset rights metadata audit: 82 datasets/511 assets, 0 errors/16 warnings; source rights metadata: 82 datasets/891 sources, 0 findings. These remain metadata/structure checks, not model tests, legal clearance, or scientific qualification. No numerical tests, package build, or HPC submission was run.

## 2026-11-01 — Crevice 이중층 전하 API와 부식-FTA 의미 제약

병렬 코드 작업으로 `integration.crevice_double_layer_charge_history`를 추가했다. 입력 knot에서 caller 전위와 면적, caller 전위 의존 차분용량 곡선, 초기 저장전하, 단위·검토 증거를 받아 exact-knot stored charge와 구간 평균 capacitive current를 계산한다. 곡선은 선형 보간, support 밖 외삽 금지다. 이력의 물리적 전위계·면적 범위 적합성은 caller 책임이며 계산 결과는 BDF/Faradaic transport에 아직 결합되지 않았다.

기존 corrosion-history FTA adapter가 요구두께의 기간 내 최초 통과 사건을 대상으로 하면서도 point-state/detection/spatial-size/unscoped probability 의미를 허용하던 contract 불일치를 수정했다. 이제 `conditional_first_failure_in_period`만 허용한다. 외부에서 제공한 확률·조건·범위·증거를 받아 묶는 adapter이며, 확률을 계산하거나 검증하지 않는다.

Schemas/source/capability catalogs, sync, backlog 및 model reference를 재생성했다. 1,420 schemas, 895 implementation bases, 937 capabilities. AST/scope audit 101행·469경로·593구성요소로 누락/미매핑 0; public-source boundary audit 3,325개 파일에서 passed. raw data는 배포 범위에서 제외했다. 수치 테스트, 패키징, HPC 실행은 하지 않았다. bounded-code 추적은 100/101이며 Crevice broad parent는 여전히 code_incomplete다.

## 2026-11-01 — 이중층 용량 자료 후보와 API 예제

Zenodo API metadata에서 Pt(111)-수용액 계면 미분용량 자료를 확인했다. 레코드 `10.5281/zenodo.5834860`는 CC BY 4.0을 표기하고 `capacitance data files.zip` (2,001,400 bytes, provider MD5 `a205c0c4efb8236556c7d87c909c4e08`) 한 파일을 제공한다. 설명상 논문 그림 1, 2, 3, 5, 6, S2의 원자료다. 이번 회차에는 올바른 저장소에 원자료를 남기지 않았으며, archive 내부의 실제 열·단위·곡선 형식은 확인하지 않았다. Pt(111) mean-field/흡착수 계면은 steel crevice와 재료·표면·환경이 달라 보정 또는 물리검증 후보가 아니다. metadata candidate로만 문서화했다.

`examples/crevice_double_layer_charge_history.py`에 합성값 기반 Python 사용 예제를 추가하고 Korean API 문서를 정리했다. 숫자는 계약 사용법만 보여주며 실험·보정·검증값이 아니다. BDF와의 결합 검토 결과, 현 상태에는 전위·계면전하 상태식이 없어 이 API의 용량전류를 Faradaic-only stage RHS에 넣으면 전류 폐합과 모델 의미가 달라진다. 일관된 연성 모드에는 계면전하 상태, E–q 구성식, stage 전류수지와 보존성분/저장소 장부가 필요하다고 문서화했다.

## 2026-11-01 — caller-tabulated SCC da/dt API와 capacitance data candidate

`degradation.scc_crack_velocity_history`를 추가해 caller가 승인한 mode-I `K_I → da/dt` 곡선을 유한 시간별 `K_I` 이력에 적용한다. 표 support knot를 통과하는 각 linear `K_I(t)` 구간을 잘라 piecewise-linear velocity를 trapezoid 적분한다. curve/history canonical digest와 licensed Evidence, material/metallurgy/environment/loading identity, RunContext, operation budget을 묶으며 support 밖 extrapolation은 결과 이력을 commit하지 않고 거절한다. `da/dN` Paris 피로성장과 구별되고 geometry feedback/환경변화/개시/확률/자격화를 주장하지 않는다. local Mendeley 304L data는 provenance와 specimen hierarchy 문제로 fitting에 쓰지 않는다. double-layer와 SCC API의 Python examples는 합성값만 사용해 입력계약 작성법을 설명한다.

Zenodo 10.5281/zenodo.5834860의 Pt(111)-수용액 capacitance 후보를 CC BY 4.0, 2,001,400-byte ZIP, provider MD5와 함께 metadata 수준에서 기록했다. Pt 표면 계산자료는 구조재 Crevice 부식에 전용할 수 없고 실제 archive/열 구조를 검토하지 않아 importer나 검증자료로 등록하지 않는다. double-layer API의 synthetic Python example을 추가했다. BDF/Faradaic 연성 검토에서는 현재 RHS에 계면전하/전위 state가 없으므로 독립 average capacitive current를 혼합하면 charge closure와 governing model 의미가 깨짐을 문서화했다.

1,422 public schemas, 896 implementation bases, 938 capabilities were regenerated and synced. Static scope/source audit found no missing paths or unmapped symbols/components. Public source boundary audit passed for 3,329 files; `data/raw`, `data/derived`, `data/evidence`, `artifacts`, and `tmp` remain excluded. No numerical tests, package build, or HPC job was run.
# 2026-11-01 — SCC growth to FTA event binding and ten-task pass

Completed the ten previously ranked quick-win tasks in the active work queue and registered the SCC crack-advance event bridge. The adapter accepts only a computed `degradation.scc_crack_velocity_history` request/result pair, recomputes the full deterministic source result and compares canonical digests, then binds a caller-declared crack-advance limit and a separately assessed `conditional_first_failure_in_period` probability to `FaultTreeBasicEvent` / `IntegrityEventBasis`. It records the first adjacent knot interval as a crossing bracket but does not estimate crossing time or infer probability. Added the API guide and exported the request/probability/output contracts. Registry, source catalog, capability catalog, model reference and implementation backlog were regenerated. Final static audit: 939 capabilities (656 models), 1,425 schemas, 897 implementation source bases; scope audit 101 rows/469 paths/593 components with zero missing paths, unavailable ASTs, stale or unmapped symbols, or component mapping drift. Public source boundary audit passed for 3,337 files / 58,581,181 bytes. Bounded code trace remains 100/101 (99.0%); this is not overall project progress. No tests, numerical validation, package build, or HPC job was run.

## 2026-11-01 — crevice dynamic geometry, nucleation event timing, hydraulic calibration

Parallel code work added schema-v4 opt-in solid-occupancy aperture/volume feedback to the component-state BDF stage. Each aqueous/solid partition is iterated against caller-evidenced phase molar volumes and gap occupancy with damped updates, a final re-partition/residual gate, minimum-aperture checks and per-stage/aggregate work limits. The converged geometry changes Nernst–Planck current-density area and integrated component transfer. Fixed-volume v1-v3/default behavior remains the default; hydraulic advection and spatial Faradaic coupling are rejected in dynamic mode. This is not mechanics, kinetic precipitation, or a monolithic solve.

The nucleation-history API now calculates seed event time from inventory deficit divided by the declared constant molar source rate, verifies threshold attainment with the conservative ledger, commits the pre-seed substep, then applies the caller seeded growth/dissolution law to the remainder. Resource-limited or unverified threshold events fail without committing a sampled crossing.

Added grouped, uncertainty-weighted calibration for positive planar-slit resistance/inertance correction factors, disjoint holdout predictions, local covariance, digest-pinned transfer, and strict calibration-support checks. This is a user-model fit, not qualification. Documentation and downstream extension requests were added. Central schema/catalog generation and audits are underway; numerical tests, packaging and HPC were not run.

Central integration completed: 949 capabilities (666 models, 190 interfaces, 101 partial), 1,454 public schemas, and 911 implementation bases; package mirror synced. Scope audit reconciled 101 rows, 474 source paths and 597 components with zero missing paths, stale/unmapped symbols or unmapped components. Broader classification remains 48 provider-dependent / 52 data-validation-pending / 1 code-incomplete. Model reference and implementation backlog regenerated. No numerical tests, package build or HPC jobs were run.

The public-source boundary audit passed for 3,404 files / 60,541,174 bytes. It checks the allowlist, restricted assets and local/source-document markers; it is not a legal opinion or copyright clearance.

Follow-up bounded APIs: `corrosion.crevice_hydraulic_stage_rhs` returns instantaneous slit `dQ/dt` from caller stage geometry/pressure/fluid evidence; `integration.crevice_double_layer_to_component_bdf_binding` verifies cellwise interval charge closure before binding prescribed capacitive current to a BDF request; `integration.crevice_cellwise_nucleation_kinetic_history` applies exact seed-event ledgers in independent fixed-volume cells and aggregates amounts only after all cells commit. These are composition steps and retain their documented operator-split/physics limits. Integration completed: 952 capabilities (669 models, 190 interfaces, 101 partial), 1,458 schemas and 914 implementation bases; mirror sync succeeded. Scope audit: 101 rows / 477 source paths / 600 components, with zero missing paths or unmapped components/symbols. Public-source boundary audit passed for 3,416 files / 61,178,814 bytes (static boundary check, not legal clearance). No numerical tests, package build or HPC were run.



## 2026-11-01 — 우선순위 묶음 및 BDF 핵생성 연산자 분할 연결

`integration.crevice_bdf_nucleation_operator_split`의 새 코드를 중앙 등록·스키마·소스/기능 카탈로그·모델 참조·scope 추적·API/모델/확장 문서에 연결했다. 입력 BDF 한 구간을 먼저 계산하고, 결과의 각 고정 체적 cell에서 seed-event kinetics를 연산자 분할로 적용한 뒤 액상 성분 재고를 재투영한다. 고체상 재고는 별도 전달하고, 모든 cell/interval이 성공해야 해당 구간을 commit한다. 별도 구간 시간 ledger가 요구하는 0-origin을 이용해 원래 절대 시간 구간과 이벤트 시각 간 affine map을 보존한다. 동시 반응/유동/전위/이동 경계 결합은 구현하지 않는다.

검토 시점 생성 현황은 954 capabilities / 1,461 schemas / 917 source entries, scope audit 101 rows / 478 paths / 601 components였고 missing/AST/symbol/component/drift 항목은 모두 0이었다. 분류는 provider-dependent 48, data-validation-pending 52, code-incomplete 1로 유지한다. 공개 경계 감사는 통과(3,420 files / 61,729,767 bytes; manifest `33e5e08bdd92ee1e48872102c53222526bfd2fe9f70b2a9016f0ac735672dc8e`)했다. 이는 법률 clearance가 아니다. 수치 검증·패키징·HPC는 보류했다.


## 2026-11-01 — 코드 범위 추적 100% 기준 확정

101개 scope 행의 source/evidence path tracing을 감사기에서 기계적으로 계산하도록 `trace_coverage`를 추가했다. 누락 evidence 경로였던 `structural.strain_life`는 해당 행의 선언 source map을 근거로 연결했다. 재감사 결과를 101/101 scope rows, 478/478 source paths present+AST parsed, 601/601 mapped components, stale/unmapped symbols 0으로 추적한다. 구현 미완성 카운트와 별도로 관리한다. `degradation.crevice_chemistry`의 잔여 범위 설명은 현재 BDF/API 코드와 대조하여 joint moving-volume hydraulic conservation, potential-Cdl-Faradaic state, BDF-stage spatial kinetics로 갱신했다. 이 회차는 static trace audit이며 수치 테스트·패키징·HPC는 실행하지 않았다. 상세: `docs/CODE_SCOPE_TRACE_KO.md`.


## 2026-11-01 — caller-curve dynamic double-layer/Faradaic API

`integration.crevice_dynamic_double_layer_faradaic_history` adds a digest/Evidence-bound BDF solver for independent lumped cells. It integrates potential from caller-supplied exact-knot total current, signed polarization tables, time-varying active area and a piecewise-linear differential-capacitance curve. `Q=A∫C_d(E)dE` includes the area-derivative contribution to `dQ/dt`; results report Faradaic, capacitive and total current plus knotwise closure residuals and work counts. Out-of-support table requests and solver/work failures return uncommitted outcomes. The API does not close spatial ohmic/NP transport, component BDF coupling, moving geometry, calibration or procedural qualification.

Registry, schemas, source/capability catalogs, scope mapping, model reference, backlog, API guide, synthetic example and downstream extension request are connected. Scope trace remains 101/101 (100%); source paths 479, components 602, missing/AST/symbol/unmapped errors 0. The broad Crevice parent retains `code_incomplete` status for remaining spatially coupled dynamic Cdl, joint moving-volume hydraulics and BDF-stage precipitation. Public boundary audit passed: 3,427 files / 61,815,624 bytes (not legal clearance). No numerical test, package build or HPC calculation was run.


## 2026-11-01 — dynamic Cdl/Faradaic history to component BDF handoff

Added `integration.crevice_dynamic_double_layer_to_component_bdf_binding`. It recomputes the dynamic history from its typed request/digest, requires one evidenced reaction/electron map per Faradaic branch, maps electrode current signs to aqueous source extents and capacitive current, then reconstructs zero-external-current ionic face schedules from exact-knot charge continuity. The adapter returns a typed component BDF request only after reaction element/component/charge validation succeeds. It does not run BDF or feed BDF chemistry back into the potential history; same-stage spatial Cdl/BV and moving-volume hydraulic coupling remain open. Added Korean guide and downstream request. Numerical tests/package/HPC remain deferred.
2026-11-01 trace coverage 갱신: 새로운 dynamic double-layer history 및 component-BDF handoff source를 `build_source_catalog.py`의 independently authored derivation records에 연결했다. Source catalog 919건으로 재생성하고 capability/schema/source mirror를 동기화했다. 정적 scope audit와 model reference/backlog를 재생성한 결과 101 rows, 480/480 source paths present+AST parsed, 603/603 components mapped; missing paths, AST failures, stale/unmapped symbols/components 모두 0. Trace coverage 101/101 (100%). 이는 위치·정적 구문 추적이며 전체 bounded implementation completeness는 100/101 (99.0%); `degradation.crevice_chemistry`는 spatial potential/Cdl/Faradaic coupling, joint moving-volume hydraulic conservation, BDF-stage kinetics의 잔여 코드로 `code_incomplete` 유지. 테스트·수치 검증·패키징·HPC는 수행하지 않았다.

2026-11-02 보완: `integration.crevice_component_state_bdf`의 schema v6 same-stage kinetic 경로를 event BDF 드라이버·phase-wise seed law·moving-volume geometry에 접합했다. 독립 상태별 BDF 절대허용오차, 적분 전류 상태의 C 단위 허용오차 스케일, 이벤트 종료 seed latch 복원 및 음수 aqueous component 재고 fail-closed 처리를 정리했다. 이 코드는 구문 컴파일만 확인했다. 계산 테스트/수치 실행은 0회이며 물리 검증도 미완료다. crevice 잔여 코드 항목은 dynamic potential/double-layer/Faradaic feedback으로 좁혀 기록하고 kinetics는 `implemented_unverified`로 분류한다.

2026-11-02 검증 보완: seed-aware BDF helper가 legacy cell×phase 입력과 component-state BDF의 phase×cell 입력을 명시적으로 구분하도록 고쳤다. 두 셀 동시 핵생성, 근접 이벤트 분리, 이벤트 예산 실패 경로에서 배열 인덱스 오류가 재현되어 수정 전 3건이 실패했고, 수정 뒤 관련 kinetics/event 및 analytical dynamic-double-layer 묶음 29건이 통과했다. 별도 RC 해석해 확인에서 1초 전위는 0.4323323573 V, 해석값은 0.4323323584 V, 전류 잔차는 0 A였다. 이 검증은 event helper와 precursor stage kinetics/chemistry, 독립-cell dynamic-double-layer solver를 다룬다. 공개 schema-v6 component-state BDF 요청을 조립한 end-to-end 수치 케이스와 dynamic double-layer/chemistry 동시 피드백은 아직 검증하지 않았다.

동일 날짜 추가 검증: schema-v6 component-state BDF 요청을 두 셀 synthetic NaCl kinetic seed 사례로 실제 검증·실행했다. 입력/phase-set digest를 정상 계약으로 생성해 Davies 단계 평형, 같은 trial의 포화도·핵생성 rate, phase×cell event law grid, 동시 seed 경계, 고체 inventory 출력 및 성분 폐합을 한 번에 확인했다. 초기 실행에서 kinetic-mode 초기화 순서, cell identity, NumPy bool seed flag, event boundary tuple 전달 오류가 드러나 수정했다. mapped aqueous component species에 대해서만 원소 기저 재구성을 적용하도록 바꾸어 무관한 solvent 종이 고체 반응 보존 검사에 끼어들지 않게 했다. 수정 뒤 focused kinetics/event/double-layer/BDF suite를 재실행해 30/30 통과(122.76초)를 확인했다. 이는 synthetic API end-to-end 계산 확인이며 현장 재료 파라미터나 실험 검증을 대신하지 않는다. 동적 Cdl/Faradaic potential과 공간 화학의 동시 피드백은 코드 공백으로 남는다. caller가 명시한 유한 후보군의 경쟁 고체 평형은 기존 API 범위에 포함하며, 후보 밖 자동 상 발견은 자료 공급자 의존이다.

2026-11-01 moving-volume continuity primitive: `integration.crevice_moving_volume_liquid_continuity` accepts digest-pinned exact-knot aperture and signed left/right boundary-flow histories, computes interval liquid-volume rates, recursively reconstructs all face flows from `dV/dt = Q_left - Q_right`, and commits only when cell and terminal right-boundary closure meet declared tolerances. Registered the calculation, exported its public request schema, mapped it into the Crevice scope trace/source catalog, and documented its API and limitations. This is a kinematic fixed-mesh incompressible balance primitive, not yet a pressure/momentum/species/precipitation coupled BDF. No numerical tests, package build or HPC job was run.

2026-11-01 pressure-driven moving-volume solver: added `corrosion.crevice_moving_volume_hydraulic_history`. Each interval applies caller linear aperture history to cell-volume rates, enforces incompressible face-flow continuity, and integrates the remaining inlet-flow state from caller pressure using the reduced series planar-slit resistance/inertance law. It reconstructs per-cell pressure-drop closure and enforces digest/Evidence, aspect-ratio, Reynolds, solver-work and residual bounds. Added API guide, synthetic wiring example, downstream integration request, registry/schema/source/capability/scope and generated-reference wiring. The API does not couple species/component transport or precipitation into the hydraulic state. No numerical tests, package build, public boundary audit or HPC job was run.

2026-11-02 schema v7 same-stage double-layer/Faradaic implementation closeout: `crevice_component_state_bdf.py` now accepts a digest- and Evidence-pinned per-cell initial interfacial state and differential-Cdl curve under schema v7. It appends integrated charge to the BDF state, inverts Cdl without extrapolation, refreshes Nernst potential/conductivity from trial chemistry, reconstructs spatial Ohmic face currents, evaluates caller-pinned Butler–Volmer branches, and computes component sources and capacitive charge continuity in the same RHS. The path is limited to fixed geometry and insulated ionic ends; caller schedules, external circuit forcing, and moving hydraulics are excluded. Updated ModelSpec assumptions, capability/source catalogs, exported schemas, package catalog mirrors, model reference, API guide, and remaining-scope notes. Regeneration/audits report 757/757 registered inputs covered by 1,809 schemas, and 101/101 scope rows with 483/483 source paths and 605/605 components mapped. Existing Cdl inversion/contract and v6 focused regression suite previously passed 4/4; the complete v7 BDF request-to-result path still awaits numerical execution and physical/material validation. No package build or HPC submission was performed.

