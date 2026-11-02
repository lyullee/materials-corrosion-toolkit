## 2026-10-29 CoolProp CO₂ fugacity provider 내부 일관성 확인 항목

`scripts/validate_co2_fugacity.py`는 필수 CoolProp `HEOS::CO2`와 CO₂/N₂ mixture command다. 검사는 순수 CO₂ 저압 ideal-gas limit, `f = phi × absolute CO₂ partial pressure`, 초임계 phase 지원, 액상 상태에서 fugacity 미출력, 300 K·100 Pa·CO₂/N₂ 0.8/0.2 조성에서 component fugacity identity, carbonate/AquaSolDB adapter의 provider digest·온도 보존을 확인한다. 입력값·허용오차·관측 출력·CoolProp version/revision과 digest를 결과 JSON에 기록한다. manifest task 126의 stdout JSON은 `hpc-results/<job>/task-126/result.json`에 보존된다. 이 검증은 provider 소프트웨어와 내부 정의의 일관성 확인이며 독립 EOS·공개 관측자료·실험 자격화가 아니다. Nurion에서 아직 실행되지 않았다.

## 2026-10-29 공개 JSON Schema 목록 보완

`structural.profile_capacity_corrosion_scenario`의 input contract가 registry/capability에는 존재하지만 JSON Schema standalone export inventory에서 누락된 점을 확인했다. `ProfileCapacityCorrosionScenario`를 exporter 목록에 등록하여 `docs/schemas/ProfileCapacityCorrosionScenario.json`을 추가했고 고유 공개 schema 수는 545개다. 실행 예제나 물리 검증 근거를 바꾸지 않으며, 모델 계산 테스트는 미실행 상태다.

# 검증 과정과 해석 범위

## 2026-10-29 부식 시나리오에서 최초 통과/FTA 교환까지

범용 non-empirical rate scenario adapter가 `SampledLinearThicknessFirstPassage` 입력을 만들고, 별도 joint-distribution·assessment-thickness·survival·loss-law·threshold·horizon 리뷰 참조를 전달하도록 composition 회귀를 추가해 HPC batch78에 등록했다. regression은 임계두께 최초 통과 곡선의 직접 가중 push-forward, source lineage 보존 및 `probability_event`의 EventProbability 생성 경계를 검사한다. 입력 예제 계약과 Ruff·manifest/schema/package audit은 통과했으나 pytest는 실행하지 않았으므로 composition 회귀와 과학 검증은 Nurion에 대기 중이다.

## 2026-10-29 범용 model-output 부식률 벽손실 시나리오

`CorrosionRateProjectionRow`는 `source_dataset_id`·`source_group_id`·`source_record_id`·archive SHA-256과 일치 evidence, scenario role, SI rate를 요구한다. model-output/assumed 시나리오를 물리 관측 row와 분리하고 혼합 lineage 및 물리 시편 ID를 거절하도록 focused tests를 작성해 HPC batch77에 등록했다. 새 입력 strict JSON 계약 검증과 Ruff/manifest/schema/package inclusion 검사는 통과했지만 pytest evaluator 회귀는 실행하지 않았다. 따라서 이는 정적·계약 구조 확인이며 계산 회귀나 과학 검증을 뜻하지 않는다.

## 2026-10-29 carbonate alkalinity speciation

모델에 synthetic closure, review gate, 음수 carbonate-alkalinity 상태, activity underflow, temperature mismatch, context binding과 총알칼리도 expanded uncertainty의 exact linear propagation focused assertions를 추가해 batch58 HPC manifest에 등록했다. 로컬 테스트는 실행하지 않았다. 이 구현은 실제 부식률·실험 적합성 근거가 아니다.


## 2026-10-29 불균일 두께 지도 및 저항성 갈바닉 입력 계약

계약 테스트 두 묶음을 `batch56-rectilinear-thickness-map`, `batch57-galvanic-resistive-coupling`으로 HPC manifest에 등록했다. PBS/Slurm 작업 범위는 `0–86`이며 manifest 정적 검사에서 87개 task와 두 array 범위의 일치를 확인했다. 이는 계산 테스트 실행이나 실험 검증 결과를 뜻하지 않는다. 신규 focused tests는 실행하지 않았다.

## 2026-10-29 304L chloride-SCC 데이터 구조 감사

Mendeley Data version 1의 이중 ZIP·Excel archive를 로컬 캐시에서 읽어 archive/member/workbook digest,
시트 수, dimensions, 비어있지 않은 셀 수 및 formula 셀 수만 집계한다. 점별 값·헤더·원문 텍스트를
감사 JSON에 저장하지 않는다. provider SHA-256은 제공되지 않아 관측한 로컬 digest만 pin했다. Excel
수식 계산값의 정확성, salt-condition 연결, physical specimen independence, third-party workbook rights와
SCC 성장 법칙은 검증하지 않았다. 합성 ZIP/workbook 계약 테스트는 batch48에 등록했으며 로컬 pytest는
실행하지 않았다.

타 저장소 교환 계약의 strict validation, digest binding과 offline GitHub integration catalog 검사는
[`CROSS_REPOSITORY_EXCHANGE_KO.md`](CROSS_REPOSITORY_EXCHANGE_KO.md)에 범위와 한계를 기록한다.

## 2026-10-28 AE·thermal-spray·열물성 보정 집중 검사

AE는 합성 source 복원, pick/wave-speed uncertainty, rank, clock, partition와 spatial support를 검사했다.
Thermal-spray는 field calibration, thickness/porosity, duplicate·overlap·bounds·edge와 holdout support를
검사했다. Thermal parameter는 synthetic coefficient 복원, sensor/time alignment, sensitivity 식별성,
partition leakage와 holdout support를 검사했다. 공개 AE reader는 실제 11 waveform·180,224표본과 좌표/
event table, 누락 source/channel을 감사했다. 집중 테스트 18건과 strict JSON 3개가 통과했다. 현장
localization, coating qualification 또는 thermal model 자격화는 아니다.

## 2026-10-28 성형·pull-off·replica feature 집중 검사

성형은 strain convention, thinning, geometry support와 caller margin을 검사했다. Pull-off는 force/area
불확도, provider bias/repeatability, partition 누출, support와 break-mode 보존을 검사했다. Replica는 px/SI
calibration, density/area fraction/spacing, duplicate·overlap·bounds·edge·missing gate를 검사했다. 공개
workbook reader는 digest, sheet/layout, raw/formula 분리와 실제 35그룹·107표본을 감사했다. 집중 테스트
17건, strict JSON 3개와 변경 Ruff가 통과했다. 금속 코팅·성형·replica 현장 자격화는 아니다.

## 2026-10-28 단조 소성·음극방식·계장화 충격 집중 검사

Hollomon 합성계수 복원, holdout support와 시편/source 분할 누출을 검사했다. 음극방식은 전위 convention,
reference calibration 온도범위, IR-drop, missing record와 caller threshold 방향을 검사했다. 충격 신호는
force 부호, trapezoidal energy, peak plateau, invalid window와 independent machine-energy gate를 검사했다.
공개 DPlot reader는 digest·layout·유한수치 오류와 실제 8곡선·11,922표본을 감사했다. 집중 테스트 17건,
엄격 JSON 예제 3개와 변경 Ruff가 통과했다. 물리시험 자격화나 보호·충격 합격판정은 아니다.

## 2026-10-28 인증서·진공시험·이종용접 집중 검사

인증서 경로는 duplicate·missing·contradiction·uncertainty overlap과 alias/unit/context gate를 검사했다.
Known-volume pressure rise는 blank/test 가중 slope, 음의 net 값 보존, 온도 support, clock·source 독립성과
선택적 molar 변환 gate를 검사했다. 이종용접은 material/layer/boundary/frame/thermal 순서와 unresolved/
out-of-scope review를 검사했다. 공개 pressure-decay reader는 합성 구조 오류와 실제 10 series·310표본을
감사했다. 신규 focused test 18건, 변경 Ruff와 strict JSON 예제 3개가 통과했다. 실제 누설·재료인증·
이종용접 현장 자격화는 아니다.

## 2026-10-28 마모·경도·인장 집중 검사

Archard 계수의 합성 복원, support 이탈과 시편/source 분할 누출을 검사했다. 경도 기준블록은 bias와
repeatability 적합, 인증값·온도 지원범위, configuration 불일치와 독립 holdout을 검사했다. Offset-yield는
가중 elastic line, 유일한 선형 교차, 무교차·복수교차와 독립 reference 경계를 검사했다. Tribology
metadata reader는 합성 manifest 오류와 실제 57개 RDF 파일·15,578,599바이트의 크기·provider MD5를
감사했다. 신규 focused test 16건, Ruff, registry/example 221개 일치와 strict JSON 예제 3개가 통과했다.
이는 연결된 원 wear measurement나 실제 경도·인장 장비의 독립 물리 검증이 아니다.

## 2026-10-28 고분자·충식부식·기준누설 집중 검사

Polymer shift는 합성 Arrhenius 기울기 복원, support 이탈, review·partition gate를 검사했다.
충식부식은 2D power-law 계수, holdout 진단, convex-hull 외삽 차단과 identity/unit 불일치를
검사했다. 기준누설은 알려진 log–log 응답, 검열·누락 보존, clock alignment, support와
partition 중단을 검사했다. ESCAPE‑1 reader는 합성 workbook 거절 6건과 실제 11 workbook·118,606
표본의 전수 구조 감사를 통과했다. 이 배치 focused test 18건, Ruff, strict JSON 예제 3개가 통과했다.
실제 고분자·충식부식 시편 및 기준누설 장비 자격화는 아니다.

## 2026-10-28 수명·민감도·실가스 집중 검사

- Strain–life 적합은 합성 계수 복원, partition/count/review gate, runout·censor 배제와 holdout support 이탈을 검사했다.
- 검열 크리프 적합은 rupture/right-censor likelihood, 식별 불가, 자료 부족과 stress–temperature hull 이탈을 검사했다.
- Sobol replicate 진단은 안정/불안정 진단, identity 불일치, 누락 uncertainty 계약을 검사했다.
- CoolProp 압력감쇠 조합은 `Z`·phase·provider digest 전달, 일부 provenance와 two-phase 거절을 검사했다.

신규 계산기 13건과 CoolProp/기존 압력감쇠 16건의 focused test가 통과했다. 이는 합성 자료 기반 수학·계약 검증이며 실제 시편·설비·누설 시험 자격화가 아니다. 전체 회귀·배포물 재생은 46개 누리온 작업을 집계한 뒤 실행한다.

## Chronoamperometry 창 요약

`tests/test_chronoamperometry_summary.py` 16건은 비균일 affine trace의 닫힌식 signed charge 6 C,
0 교차를 포함한 absolute charge 6.5 C, baseline 시간평균 -1 A와 극값을 오차 0으로 대조한다.
exact/선형 경계정책, 창 support, 단위·순서·부호 review gate, 비유한·중복 시간, plateau 첫/마지막
시각, registry JSON과 SECCM adapter의 hash 계보도 검사한다. 전 모델 예제와 SECCM reader를 포함한
집중 회귀 161건에 이어 기존 전기화학까지 합친 집중 회귀 191건이 통과했다.

`scripts/validate_chronoamperometry_summary.py`는 같은 닫힌식과 고정 SECCM map 1의 전체 7,782개
raw sample을 실제 API로 처리한다. 공개 기록에는 배열 대신 선택배열·archive·member hash와 집계값만
남긴다. 이는 수치 적분과 reader-to-model 통합 검사이며 제공자 descriptor 재현, 전기화학 극성,
독립 시편, pit truth·POD·수명 검증이 아니다. 결과는
`validation/chronoamperometry_window_summary_math.json`에 있다.
36-task Slurm manifest의 35번 작업으로 이 검증을 등록했고 같은 task runner의 로컬 실행이 통과했다.

## 316L SECCM raw chronoamperometry 감사

`tests/test_seccm_data.py` 9건은 정확한 ZIP manifest, archive/member checksum, path traversal·중복·
암호화·크기 제한, 두 header와 205개 위치 schema, 유한 수치, 엄격히 증가하는 시간, map identity와
단위 경계를 검사한다. `scripts/inspect_seccm_data.py`의 실제 전수 감사는 205×7,782 = 1,595,310개
전류값이 모두 유한하고 0–59.9915 s, 7.02e-12–3.58e-09 A임을 기록했다. 제공자 MD5도 별도로
대조한다. 이는 파일·수치 계약 검사이며 map point의 독립 시편성, parameter/descriptor/label/SEM/EBSD
정합, descriptor 재현, pit truth·치수·POD·수명 또는 합격 검증이 아니다. 결과는
`validation/seccm_316l_pitting_dataset.json`에 있다.
같은 스크립트는 관련 표를 실행하지 않고 CSV로 직접 읽어 parameter 205행·ID 순열, descriptor 두
표의 205개 ID, label 98개 고유 ID, footprint 205개 oval·22,821점, SEM 194,512좌표와 filtered EBSD
194,513좌표를 집계한다. parameter 행 순서가 map ID 순서와 다르고 retract charge 한 칸이 비어 있는
상태도 보존한다. 이 집계는 cross-table join이나 imaging registration 자격화가 아니다.

## 검토된 직교 공간장 계약

`tests/test_spatial_fields.py` 8건은 dtype·shape·바이트 해시 결속, 비균일 축에서 선형 평면의
bilinear 복원, nearest 선택, 검토된 affine frame 변환, 지원영역 밖·결측 정책과 잘못된 shape·dtype·
digest·비유한값·퇴화 변환의 거절을 검사한다. 이는 수치 표본화 계약의 소프트웨어 검사이며 실제
계측 좌표의 정합 품질, 보간 오차, pit 경계·성장·stress 인과 또는 독립 시편 검증이 아니다.

## AA7050 국부 공식 MAT 구조 감사

`tests/test_pitting_data.py` 8건은 checksum 고정 level-5 MAT에서 실수 numeric 배열과 비유한 값을
그대로 읽고, struct·complex·해시 불일치·근거 없는 단위와 좌표 정합 주장을 거절하는지 검사한다.
`scripts/inspect_aa7050_pitting_data.py`는 제공자 바이트 수에 못 미치는 파일을 `incomplete_files`로
분리하고 완전한 파일만 SHA-256 대조 뒤 감사한다.
`validation/aa7050_local_pitting_dataset.json`은 네 파일의 완전한 구조, 형태 shape 불일치,
strain 7개와 stress 10개 배열의 서로 다른 grid 및 전 값 유한 상태를 기록한다. 이는 파일 구조와 소프트웨어 계약 검사이며 좌표 정합·단위·pit
치수·성장·stress 인과·독립 실험 검증이 아니다.

## 침투·자분 표면검사 기록

`scripts/validate_surface_examination.py`는 침투검사 target 2.0 m² 중 1.5 m²의 coverage 0.75와,
자분 field 방향 0.1 rad 및 π−0.2 rad 사이 무방향 acute separation 0.3 rad를 독립 계산한다.
최소 요구 1.0 rad보다 작으므로 해당 영역이 `needs_data`로 남는 것도 확인한다. 전용 10개 검사는
공정 검토·음성결과·면적·indication/pass identity·미등록 영역·방향 부족·레지스트리 의미를
검사한다. 이는 실제 소모품, 공정, 자장, 검사원, 검출성능 또는 합격기준 검증이 아니다. 결과는
`validation/surface_examination_math.json`에 있다.

## 육안 표면검사 기록

`scripts/validate_visual_surface.py`는 서로 겹치지 않는다고 검토된 두 영역의 target 3.0 m²와
examined 2.5 m²에서 coverage 5/6을 독립 산술과 오차 0으로 대조한다. 합격·POD·고장확률 필드가
출력에 생기지 않는지도 검사한다. 전용 계약 검사는 면적 초과, 부분 검사 사유 누락, 중복 영역 ID,
미선언 영역에 연결된 지시, 검토되지 않은 coverage와 음성 결과를 거절하거나 `needs_data`로
유지한다. 이는 실제 절차, 조명, 표면상태, 검사원, 결함 분류 또는 검출성능의 검증이 아니다.
고정 결과는 `validation/visual_surface_math.json`에 있다.

`scripts/validate_radiography.py`는 독립 작성한 pinhole 사례에서 SOD 1.0 m와 ODD 0.2 m로
SDD 1.2 m와 magnification 1.2를, 1 mm focal spot으로 geometric unsharpness 0.2 mm를,
0.2 mm detector pitch로 object-plane pitch 1/6 mm를 대조한다. 고정 결과는
`validation/radiography_math.json`에 있다. 이는 산술·계약 검증이며 실제 source/detector/IQI,
지시 검출·크기 또는 절차 자격화가 아니다.

`scripts/validate_phased_array.py`는 independently authored 4-element probe에서 aperture 3.8 mm,
5900 m/s와 5 MHz의 nominal wavelength 1.18 mm, 30 ns focal-law delay span, encoder 위치
0·1·3 mm의 span 및 1·2 mm nonzero increment를 직접 대조한다. 고정 결과는
`validation/phased_array_math.json`에 있다. 이는 acquisition 산술·계약 검증이며 probe field,
wedge/law, encoder, waveform, reconstruction, indication detection·sizing 또는 acceptance 자격화가 아니다.

`tests/test_ml_ndt_data.py`의 합성 local clone 10건은 canonical UUID quartet, partition, 고정 revision,
연결 JSON parsing, label/metadata mismatch 보존, UInt16 형상-바이트 수, 한 영상 C-order 읽기와 읽기 전
SHA-256 재검사를 확인한다. 작은 파생 fixture는 provider 원자료나 물리 검증이 아니며, 201개 batch의
전수 실행 결과를 대신하지 않는다. 실제 clone 전수 감사는 공개 패키지 밖에서 수행해야 한다.

`scripts/validate_tofd.py`는 독립 작성한 40 mm probe index separation, 5900 m/s 종파 속도에서
5 mm upper tip, 15 mm lower tip과 25 mm backwall의 대칭 Pythagorean path 시간을 만든다. 구현이
각 깊이, 10 mm tip separation과 backwall 깊이를 절대오차 `1e-14 m` 이내로 회복하는지 확인하고
`validation/tofd_math.json`에 기록한다. 전용 13개 검사는 ID/role/encoder 연결, lateral reference 누락,
비인과 pick, 뒤집힌 tip, mapping/review와 음성결과를 검사한다. 이는 waveform, dead-zone, 실제 sizing,
POD 또는 절차 자격화 검증이 아니다.

## Pulse-echo ToF 두께 변환

`scripts/validate_pulse_echo_calibration.py`는 알려진 5920 m/s와 30 ns zero offset의 합성
기준시편에서 원점을 지나는 최소제곱 닫힌 식과 구현값이 정확히 일치하는지 확인한다. 세 calibration
위치로 얻은 값은 5920 m/s, 독립 holdout 잔차는 0이며, holdout 기준치수만 바꿔도 적합 음속은
변하지 않는다. 위치·source-group 분할 누수와 zero correction 뒤 비양의 시간은 단위검사에서
거절한다. 2 µm 치수 표준불확실성과 1 ns 시간 표준불확실성을 준 effective-variance 사례의
음속 표준오차 1.9635649718358414 m/s도 독립 식과 차이 0으로 대조했다. 불확실성 쌍 누락과 반복
비수렴은 명시적으로 거절·중지한다. 이는 산술과 분할 검증이며 실제 치수계·probe·재료·온도 전달성 검증이 아니다. 결과는
`validation/pulse_echo_calibration_math.json`에 있다.

`scripts/validate_pulse_echo_thickness.py`는 저자가 만든 균질 종파·수직 입사 합성 사례에서 알려진
두께와 음속으로 왕복시간을 만든 뒤 별도 계산 경로가 두께를 정확히 회복하는지 검사한다.
`validation/pulse_echo_thickness_math.json`은 time-zero correction을 포함한 7.5 mm 항등식의
절대오차와 교정 digest를 기록한다. 단위 미검토, 교정 미검토, 시편/프로브 ID 불일치와 보정 ToF의
근거 누락은 단위검사에서 거절한다. 이는 수학·계약 검증이며 실제 재료 음속, probe delay,
couplant, 위치 재현성 또는 측정 불확실성의 실험 검증이 아니다.

`scripts/inspect_ceit_pulse_echo_method.py`는 고정 공개 연구의 해시와 관련 쪽의 방법 항목을 검사하고
원문을 복제하지 않는 집계만 남긴다. 현장 raw ToF에 ns·5950 m/s·zero offset 0을 적용한 후보
범위는 수치 규모 확인용이다. 제공자 확인 단위, 현장장치 교정 lineage, `tof_c` 정의, 동일 위치의
독립 치수와 점별 불확실성이 없으므로 field thickness·corrosion rate 자격 flag는 모두 false다.

## 이질적 습식 CO₂ 편집 자료

`scripts/inspect_wet_co2_data.py`는 고정 CSV 427행의 정확한 열 순서·해시·유한 수치·결측을
검사한다. 완전행 243개, 완전 중복 원값 3행과 네 가지 결측 패턴을 삭제 없이 기록한다.
CSV에는 단위와 source group이 없다. 연계 CC BY 4.0 preprint Table 1의 동일 통계값과 열 단위를
검토하여 명시적 opt-in SI 변환의 °C→K, bar→Pa, %→fraction, mm/Julian-year→m/s 산술을
합성 테스트로 확인한다. 논문의 243·50·60·74개 유형별 집계도 기록한다. 별도 CC BY 4.0
Mendeley workbook `10.17632/4nydhxjymw.1`은 제공자 해시·헤더·단위표·243개 수치행을 검사하고,
편집 CSV의 처음 243행과 같은 위치의 8개 수치가 모두 정확히 같은 경우에만 source group을
부여한다. 한 값이라도 다르면 전체 대조를 거절한다. 이 243행은 NORSOK M-506 구현의 모의
출력이며 물리 관측이나 독립 검증이 아니다. 나머지 184행에는 집계 수량으로 행별 유형을 만들지
않는다. 따라서 이 검사는 데이터 구조·단위 변환·출처 대조 계약 근거일 뿐 부식속도 보정·실험
검증이 아니다. Schema drift, 해시 불일치, 비유한 값과 검토되지 않은 단위 근거는 거절한다.

`scripts/inspect_wet_co2_literature_evidence.py`는 배포에서 제외된 호출자 보유 accepted manuscript의
부록 구조와 해시를 확인하고, 16개 학습행과 6개 시험행을 읽는다. 온도·유속·pH·부식속도의 연속
순서로 전체 편집본을 검색해 provider row 334–355 하나만 후보임을 확인한다. 명시적 MPa→bar
변환 뒤 압력 19개 일치·3개 불일치를 기록한다. 합성 계약검사는 단일값 affine, 두 source 값의
산술평균, 결측·불일치 보존과 중복/미선언 mapping 거절을 확인한다. 공개
`wet_co2_literature_crosswalk.json`에는 집계만 있고 원문 점별 표는 없다. 22행 대 50개 집계 충돌,
압력 불일치와 미확정 시편 ID 때문에 이 결과는 source-group 자격화나 보정 자료가 아니다.

`scripts/inspect_wet_co2_hainan_evidence.py`는 고정한 공식 PipeChina API 응답에서 원 논문의
위치 1~4와 60만 읽는다. kPa→bar와 액상·기상 전단응력 산술평균을 명시적으로 적용한 여섯
비응답 필드가 편집본 provider row 245~248·304에 각각 하나의 후보를 만드는지 검사한다. 다섯
후보의 여섯 필드는 모두 일치하며 부식속도는 4개 일치·1개 불일치다. 위치 60의 3.11 대 2.86
mm/year 차이는 자동 수정하지 않는다. 이 검사는 재수록된 5/60행에만 해당하며 전체 source group,
55개 누락행, 독립 위치 또는 보정 자격을 증명하지 않는다.

`scripts/inspect_wet_co2_egua_preview.py`는 고정한 12쪽 출판사 미리보기의 해시와 구조를 검사한다.
대상 제목은 페이지 4 목차에만 있고 대상 DOI는 없으며, 페이지 5에서 다른 논문의 DOI와 본문이
시작한다. 페이지 4·5는 이미지로도 확인했다. 따라서 Egua-2 표의 부재를 기록할 수 있을 뿐
74개 관측의 행 대조·조건·권리·독립성을 제공하지 못한다.

## COQTEL 국부부식·Lamb-wave 자료

`scripts/inspect_coqtel_data.py`는 제공자 체크섬과 프로젝트 SHA-256을 대조하고 HDF5 두 파일의
consecutive state, EC 행, 네 actuator, 5×2000 파형, 200 kHz/2 MHz/5-cycle 정의와 유한값을
전수 검사한다. 실험 1은 166 EC 행·664 actuator 파형과 같은 시각 10구간, 실험 2는 263 EC 행·
1,052 actuator 파형과 같은 시각 2구간이다. 실험 2 state 30~100의 71상태는 논문 보고 공기방울
교란으로 보존한다. 전체는 물리 시편 두 개이며 429상태가 독립 시편은 아니다.

각 파일의 root image에는 state 연결·길이 보정이 없고 상태별 pit 치수도 없다. 처음–마지막의 한
actuator–sensor 경로 신호 변화는 reader 조합의 기술 검사일 뿐 pit-sizing·POD·잔여수명 검증이
아니다. `validation/coqtel_dataset.json`은 원 파형·이미지·점별 EC 행 없이 이 집계와 자격 상태만
보존한다.

## 탄소강 1년 대기부식의 source-group 전이

`scripts/validate_atmospheric_corrosion.py`는 프로그램 617행과 독립 A/B 등급 83행을 겹치지 않는
source group으로 분리한다. 직접 NumPy 최소제곱과 구현 계수는 일치한다. 그러나 보류 log-RMSE
1.20494와 보정지원 이탈 33/83은 사전 기준 `log(2)`와 0.1을 넘으므로 전이 기준은 실패한다.
검증 JSON은 이 실패를 그대로 보존하고 `operational_prediction_qualified=false`로 기록한다.
소프트웨어·수학 검증 통과를 외부 환경 예측 자격으로 바꾸지 않는다.

Batch94는 holdout observation 수가 크게 다른 두 source group에서 작은 그룹의 큰 오차가 전체 행 RMSE에
희석되는 synthetic boundary를 검사한다. 새 구현은 그룹별 RMSE와 absolute log-bias를 산출하고 각 그룹의
최댓값이 caller threshold 안에 들어올 것을 요구한다. 회귀를 manifest에 등록했으며 아직 pytest/Nurion 실행
전이다. 기존 실제자료 aggregate 보고서는 group-wise 재계산 및 새 gate 검증 결과가 아니다.

Batch95는 calibration·holdout 입력 digest를 별도로 고정하고 fitted model 및 집계 validation report에
보류 입력 digest가 전달되는지 확인한다. 해시는 재현 revision pin이며 공급자 checksum이나 점별 관측
재배포 권리를 대체하지 않는다. 회귀는 누리온 일괄 manifest에 등록했고 실행 전이다.

## 배관 유도초음파 archive와 XLS 구조

`scripts/inspect_guided_wave_data.py`는 고정 외부·내부 ZIP, 236개 workbook과 1,180개 sheet를
전수 읽는다. 다섯 주파수별 236개, 2,509×4 shape 1,180개, 숫자 2,958,260행, 동일 거리 grid와
sheet당 반복 거리 한 구간을 확인했다. 원 sheet 순서는 9종이며 DAC 열의 비영 값은 0개다.
논문 설명의 2,057×4와 실제 shape 차이를 실패나 자동 보정으로 숨기지 않고 검증 기록에 남긴다.
`tests/test_guided_wave_data.py`는 합성 OLE BIFF workbook으로 path traversal, digest, 중복 acquisition,
header·축 변조, sheet 순서, 파생 archive의 상태-label 차단을 검사한다. 이 증거는 reader와 자료
구조의 검증이며 손상 검출·위치·크기·POD 또는 자연 부식 성장의 실험 검증이 아니다.

`tests/test_guided_wave_features.py`는 직접 계산한 RMS·에너지·상관 항등식, 폐구간 선택,
영 baseline, 정렬되지 않은 축·grid mismatch, 반복 거리의 보존·평균·거절, reader adapter의
archive/specimen/acquisition/frequency gate와 등록 API를 검사한다.
`scripts/validate_guided_wave_features.py`는 acquisition 1622를 한 baseline으로 고정하고 1901,
1902, 1930을 14 kHz의 torsional/flexural 채널, +2.0~+3.2 m 창에서 기술 비교한다. 결과 6건은
`validation/guided_wave_pair_features.json`에 파형 배열 없이 집계값과 입력 digest로 남는다.
건강 기간 내부 1622→1901 비교에서도 정규화 residual RMS가 torsional 약 0.503,
flexural 약 0.241이므로 단일 baseline 차이를 손상 특이 신호로 볼 수 없다. 같은 한 관의 반복
취득이고 온도·시각·결합 변화와 여섯 가공 단계가 미확정이므로 이 비교는 손상 분류·위치·POD의
보정 또는 독립 실험 검증이 아니다.

`inspection.guided_wave_reference_ensemble`의 합성 검사는 mean reference, leave-one-out 직접식,
baseline spread, 영 spread, 반복 거리, identity·shape·axis gate와 reader adapter를 확인한다.
실자료 검증은 건강기간에 분산한 7개 ID를 계산 전에 고정하고 median reference를 만든다. 1901,
1902, 1930의 observation-to-baseline-spread 비는 torsional 약 0.810·1.179·1.750,
flexural 약 1.207·1.744·2.608이다. 같은 비교의 leave-one-out 최대 대비 비는 각각 torsional
약 0.381·0.554·0.822, flexural 약 0.507·0.732·1.096이다. 이는 선택 집합의 기술 비교이고
독립 시편 분류 성능·거짓경보율·threshold·POD가 아니다.

## 구분하는 근거 수준

크리프 신규 경로는 완전 관측의 폐형식 정규 회귀, 검열 자료의 독립 Nelder-Mead 우도 적합, 해석적 gradient의 중앙 차분, 알려진 두 요인 합성 법칙의 계수 회복과 비교한다. 단일 온도 Q 비식별성, 시편 중복, 전부 미파단·퇴화 산포, 관측 지지 영역의 convex hull, 시간 지원 범위, 생존 구간 분할의 일관성, 극소 기간의 위험률 극한과 z=40 꼬리를 확인한다. 수치 검사와 실제 데이터 보류 비교를 구분한다.

실제 BAM CMSX-6 자료는 8개 보정·4개 보류이며 파단 보류 시편은 3개다. 자연로그 수명 RMSE 약 0.02694는 이 작은 동일 출처 분할에서만 성립한다. 단일 온도이므로 다중 온도 모델의 실제 열 효과·장기 외삽·기구 전이 검증은 없다. 산포만 포함한 조건부 확률을 설비 전체 고장확률이나 모수 불확실성을 포함한 상한으로 해석하지 않는다. 원 시편별 수명·파형·점별 예측은 배포하지 않는다.

| 수준 | 확인하는 것 | 확인하지 못하는 것 |
|---|---|---|
| 계약 검사 | 스키마·단위·값 범위·모델 ID·상태 보존 | 실제 설비 정확도 |
| 수학적 검증 | 보존식, 해석해, 독립 수치 적분, 극한·수렴 | 재료 파라미터의 실험 적합성 |
| 보정 | 선택한 실험에서 모델 계수 추정 | 별도 실험·현장으로의 전이 |
| 보류 표본 비교 | 보정에 쓰지 않은 시편에 대한 제한된 비교 | 독립 기관·장치·환경의 검증 |
| 통합 검증 | 실제 공급자·소비자 연결과 의미 보존 | 코드 형식만 맞췄을 때의 물리적 완결성 |

## 실행하는 검사

- Bayesian 선형 두께 갱신은 작성한 두 update 관측의 사후 평균·공분산을 독립 정보형
  Gaussian 해와 대조한다. batch/sequential 동치, holdout 값 변경에 대한 posterior 불변,
  전체 상관 측정공분산의 대칭·양의 정부호, 중복 관측·위치·context, review gate와 source-group
  중첩을 검사한다. 신용구간과 요구두께 미달확률을 정규분포 항등식으로 대조하고 확률 의미를
  point-in-time state와 posterior parameter로 고정한다.
  `validation/bayesian_thickness_update_math.json`은 합성 수학·계약 검증이며 실제 부식성장,
  검사오차, POD, 과정/모델형식 불확실성이나 현장 독립 검증이 아니다.

- 표본 기반 선형 두께 최초도달은 가중치 0.5, 0.2, 0.3의 작성 공동 표본에서 양의 손실률 두
  행의 도달시각과 0 손실률 행의 비도달을 닫힌 식으로 대조한다. 후보별 누적확률, 마지막 후보
  이후 도달 질량과 영구 비도달 질량을 표본 가중치에서 직접 합산한다. 같은 출력으로 임계확률
  일정 계산을 호출해 기대 후보가 선택되는지도 확인한다. 평가시점 임계 이하 행, review gate,
  가중치 합, 후보순서, context와 digest 변화를 별도 단위검사한다.
  `validation/sampled_linear_thickness_first_passage_math.json`은 작성 표본의 변환과 인터페이스
  검증이며 실제 두께-부식률 분포, 과정잡음, 모델형식 또는 현장 최초도달의 검증이 아니다.

- Gaussian 두께 posterior 표본 설계는 독립 구현한 SplitMix64 정수 전이, 53비트 개구간 균등수,
  Box–Muller 정규쌍, 2차원 Cholesky와 rejection 순회를 등록 계산과 표본 단위로 대조한다. 4,096개
  수락 표본의 정확 행·후보 수, 평가시점 생존과 비음수 손실률을 확인한다. 단위검사는 재현성,
  경험적 평균·표준편차·상관, review gate, 고정 예산 부족 시 부분표본 차단, 공분산, context,
  Bayesian→표본→최초도달 어댑터 사슬을 포함한다.
  `validation/gaussian_thickness_posterior_sampling_math.json`은 난수변환·계약 검증이며 실제
  posterior 모형, 과정잡음, 일정 부식률 또는 현장 자료의 검증이 아니다.

- 선형 두께 상태공간 갱신은 과정잡음 0에서 두 update 관측의 분석 종료시점 평균·공분산을 독립
  batch 정보형 Gaussian 해와 대조한다. 비영 과정잡음에서는 마지막 posterior를 직접 전이하고
  `F P Fᵀ + Q_rate Δt`로 계산한 미래 두께 표준편차와 비교한다. holdout 행의 `state_updated=false`,
  값 변경에 대한 최종 posterior 불변, 시간순서·공분산 양의 준정부호·검토 gate·context와 상태공간
  posterior→공동표본 어댑터를 단위검사한다. `validation/linear_thickness_state_space_math.json`은
  Gaussian 필터 산술·계약 검증이며 과정잡음 보정, 비선형 열화 또는 실제 CML의 검증이 아니다.

- 공동 사건 확률은 두 Bernoulli 사건의 완전한 네 상태 분포에서 주변확률 0.1·0.2,
  동시확률 0.05, 공분산 0.03, phi 0.25, OR 상위사건 확률 0.25와 독립 비교값 0.28을
  대조한다. 누락·중복 상태, 정규화 오류, 퇴화 주변분포의 정의되지 않은 phi, 자산·부위·시계와
  기간 불일치를 검사한다. `validation/joint_event_probability_math.json`은 작성된 유한
  확률공간의 산술 검증이며 실제 공통원인 빈도나 의존성 보정 근거가 아니다.
- 동적 신뢰성은 고장률 0.1/s, 수리율 0.2/s인 두 상태 CTMC의 행렬지수 점유확률,
  실패상태 기대 점유시간과 흡수 복사본의 최초진입확률을 폐형식과 대조한다. 수리율 0 한계,
  생성행렬 부호·행합·정렬, 초기확률·초기 사건질량, 미검토 입력, context와 사건 전달의 기간·
  의미 보존을 검사한다. `validation/dynamic_reliability_math.json`은 작성된 수학 검증이며 실제
  고장·수리율 보정이나 Markov 가정의 실험 검증이 아니다.
- 구간형 동적 신뢰성은 동일한 두 상태 생성행렬을 4초·6초로 나눈 결과가 단일 10초 행렬지수,
  폐형식 종료 점유·최초진입 및 기대 전이횟수와 `1e-12` 이내로 일치하는지 확인한다. 서로
  교환되지 않는 세 상태 생성행렬의 순서 효과, 경계별 순차 전파, 구간 공백·중첩·역순·중복,
  잘못된 행렬과 미검토 구간을 검사한다. `validation/piecewise_dynamic_reliability_math.json`은
  구간 전파의 수학·소프트웨어 검증이며 실제 운전조건별 전이율의 보정이나 실험 검증이 아니다.

- 전이구간 파괴인성 reader는 provider training/test 분할, 연속적인 partition-local ID, one-hot CT/SEB/PCCv, source row와 명시된 MPa·MPa√m 변환을 검사한다. 충돌하는 workbook `K` 표기와 연계 논문의 °C 선언을 함께 보존하고 기본 113.15~373.15 K 및 명시적 override를 검사한다. W/B/a 원 단위 표기는 비워 두면서 논문의 T 크기 mm 정의와 B 4.07~101.6 전수 일치를 근거로 640행을 m로 변환하고, 검토 비활성화 시 SI 치수와 조건 그룹이 비는지 검사한다. 실제 고정 workbook의 640행·14재료·형상별 수와 범위, partition 사이 완전 동일 행 0개를 대조한다. 기본 상대 3%·절대 0.1 mm 허용오차의 형상 조건 그룹은 34개이고 모두 두 partition에 있음을 고정 검사한다. 이는 누설 경고이며 물리 시편 독립성 검증이 아니다. 논문 표 그룹은 정확 614행·유력 이름 변형 18행·미해결 8행이며, 알려진 재료명의 탄소량 불일치를 정확 연결로 바꾸지 않는 계약을 검사한다. 참고문헌 카탈로그 9개·DOI 7개와 행의 `resolved_doi` 176·`bibliography_only` 456·출처 그룹 미해결 8개를 대조하고, 모든 행의 관측 권리가 미확정인지 검사한다. 이는 행별 원 문헌 추적·시편 독립성·시험 유효성·FAD 적용성이나 법률 의견이 아니다.

- 사용자 FAD는 49개의 합성 Lr 점에서 별도 구간식과 선형 보간을 비교하고 절점·경계 안/밖·마지막 Lr 지원 밖 중지를 검사한다. 최대 보간 차이는 약 `1.67e-16`이며 `validation/failure_assessment_math.json`에 소스 해시를 보존한다. 이는 실제 K/reference stress, toughness, 상용 규격 곡선이나 cracked component의 자격이 아니다. C1/C2 공개 자료는 signed raw channel과 파일 구조만 감사하며 FAD 검증 관측으로 사용하지 않는다.

- 과도 열전도는 평판 Fourier 셀 평균 해, 공간·시간 격자 세분화, 단열·지정 열유속·발열·대류·복사, 온도 의존 엔탈피 저장과 원통 에너지 보존을 검사한다. 열응력은 자유 선형 온도분포, 균일 고정 가열, 지정 합력·모멘트와 탄성 한계 중지를 검사한다. `validation/thermal_gradient_math.json`은 소스 해시와 수렴 수치를 보존한다. 공개 rod `50ss1`의 RMSE 약 0.6335 K는 같은 자료에서 적합된 계수를 사용한 재현이며 독립 실험 검증이 아니다.

- 분극 혼합 전위는 독립 선형 회로·면적비·전류 보존과 비선형 반응 합의 폐형식 및 보간 격자 세분화를 대조한다. 다른 절점·세 전극·다중/접선/끝점 근·평탄 구간·부호/조건 검토·원 분기·공급자 배열·수치 소거와 표현 범위를 검사한다. `validation/electrochemistry_math.json`은 소스 해시·합성 파라미터·digest와 오차를 보존한다. 실제 24곡선의 계약/프로토콜 감사는 실제 결합 전류·용출·물질 손실의 독립 검증이 아니다.

- Sobol 민감도는 가산 분산·순수 상호작용·무관 입력의 해석값과 Ishigami 폐형식 모멘트를 대조한다. 단위/affine 변환과 극단 척도, 상수·해상도 부족 분산, 미달 수치 기준, 음수 추정, PPF/로그 단위, 모델 판본, 원 설계·점 ID·순서 변경·중복·누락·실패·반복 확인 중지도 검사한다. `validation/sensitivity_math.json`은 source 해시·scramble별 지수·표본 크기·근사 구간과 해석값 오차를 보존한다. 실제 입력 상관·분포 추정·stochastic 관측의 검증은 이 합성 검사에 포함되지 않는다.

- 수소 분배는 무트랩·결합에너지 0의 폐형식, 질량·화학퍼텐셜 평형, 독립 전방식의 중앙 차분 저장계수, 트랩 분할/순서 불변성, 점유율 범위, 미분 확산계수 underflow와 미량 농도의 표현을 확인한다. 이는 국소 평형 수학의 검사이며 실제 투과·TDS·수소 균열의 실험 검증이 아니다.
- 유한 평판의 kinetic trap은 닫힌 반응의 해석식과 시간 간격 수렴, Fourier 셀 평균과 격자 수렴, 두 트랩 변온의 독립 DOP853 ODE, 빠른 속도의 Oriani 한계, 경계 반사, 비균일 폐쇄 질량, 일정 농도 분포의 변하는 통과량 적분을 확인한다. `validation/hydrogen_slab_math.json`은 소스 해시·합성 입력 digest·오차 감소를 보존한다. release/capture 비율·형상·시편·표면 관측의 실제 자격은 이 검사에 포함되지 않는다.
- 유한 원통 kinetic trap은 환형 셀 체적·반경 면적·양 끝단 면적과 세 표면별 교환을 보존한다. 무트랩 반경 확산의 Bessel 급수 체적평균과 반경 격자 세분화, 축방향 선형 정상해·끝단 유량, 폐쇄 트랩 반응과 전체 mol 질량보존을 확인한다. `validation/hydrogen_finite_cylinder_math.json`은 작성한 수학 검증이며 실제 TDS의 표면 방출, 검출기, 트랩 모수 또는 독립 실험 검증이 아니다.
- 선형 수소 표면전달은 `1/(1/k_surface+d_half/D)` 직렬저항 항등식과 평판 면적당 flux·원통 곡면 총 flow, 누적 교환–재고 보존을 대조한다. `validation/hydrogen_surface_transfer_math.json`은 작성한 경계조건 검증이며 표면계수·평형농도의 재료 보정이나 흡착/재결합 기구 검증이 아니다.
- 독립 수소 트랩 속도는 닫힌 평판·유한 원통에서 `capture=release`인 균일 반응의 해석식과 대조한다. 매우 큰 결합에너지와 300→900 K 이력을 함께 넣어도 명시한 두 빈도가 바뀌지 않는지, capture가 0이어도 독립 release가 작동하는지, 선택 모드의 검토·이력 길이·상충 입력을 검사한다. `validation/hydrogen_independent_rates_math.json`은 작성한 수학·계약 검증이며 실제 속도, prefactor/엔트로피 또는 비가역 트랩의 보정이 아니다.
- 열활성화 수소 트랩 속도는 절대 Arrhenius와 Eyring 전이상태 식을 별도 산술과 대조하고, 생성한 독립 속도 JSON 조각을 평판 수송에 연결해 동일한 piecewise-linear 빈도를 사용한 DOP853 반응해와 비교한다. 온도 지원·검토·상충 파라미터·부동소수점 범위 중지도 검사한다. `validation/hydrogen_thermal_rates_math.json`은 합성 수학·조합 검증이며 실제 장벽·엔트로피·기구·실험 적합의 증거가 아니다.
- 열활성화 속도 적합은 중심화·척도화된 가중 최소제곱 결과를 독립 가중 직선 폐형식과 대조한다. Arrhenius log-prefactor/활성화에너지, 고정 transmission coefficient 전이상태 엔탈피/엔트로피, holdout 완전 제외와 생성 계약의 기존 속도 공급자 연결을 검사한다. `validation/hydrogen_thermal_rate_fit_math.json`은 합성 수학·계약 검증이며 실제 rate 추출, 실험 보정, model-form/source-group/transport 불확실성 또는 독립 검증이 아니다.
- 수소 검출 관측은 signed outward mol/s에 대한 Faraday 전류와 시편 질량기준 TDS ppm/s 항등식, 평판 inward flux×면적의 outward flow 변환을 독립 산술과 대조한다. `validation/hydrogen_detector_observation_math.json`의 세 절대 오차는 0이다. 이는 실제 detector calibration, 동특성, 배관·진공계, 재결합·흡착, 잡음·불확실성 또는 역문제 검증이 아니다.
- 수소 평판 flow 역추정은 알려진 확산계수 배수 2.0으로 만든 signed outward atom-molar flow에서 calibration 행만 사용해 배수를 복원하고, fitted slab 재실행, holdout 값 변경에 대한 적합값·digest 불변, 정방향 질량보존을 검사한다. `validation/hydrogen_slab_flow_inverse_math.json`의 배수 절대오차는 약 `8.9e-16`, fitted history와 재사용 계약의 최대 절대오차는 약 `8.3e-17 m²/s`, holdout 변경에 따른 배수 변화는 0이다. 이는 같은 구현으로 만든 합성 자료의 한 모수 recovery 검사이며 전역 식별성, 실제 재료·표면·검출기 보정, 다중 모수 공분산 또는 독립 실험 검증이 아니다.
- 수소 축약 표면반응은 Arrhenius와 `sqrt(f/f_ref)` capacity를 독립식과 대조하고, 동일 경계 조각을 평판과 유한 원통에 합성해 반 셀 직렬저항 flux·곡면적 적분 flow·atom-mol 보존을 검사한다. `validation/hydrogen_surface_reaction_math.json`은 합성 산술·형상 조합·보존 근거이며 실제 fugacity 공급자, 표면계수, 산화막·오염 또는 실험 자격을 검증하지 않는다.
- 탄화물 트랩 자료의 적용성 게이트는 공개 인벤토리와 내보내기 계약에서 TDS 질량 ppm 기준, 명목 가열률의 비시계성, 제한된 IP0/IP2 재료 후보 대응을 다시 검사한다. `validation/hydrogen_carbide_applicability.json`은 TDS와 투과 역추정 준비 상태가 false이고 시계·검출기·표면경계·막 두께·면적·전위 기준·시편 대응 차단조건이 유지되는지 확인한다. 이는 원자료 보정이나 실험 검증이 아니라 과대해석 방지용 메타데이터 자격화 기록이다.
- HE-Austenite 로더는 원자재료 구분·단위·누락·1보다 큰 보존비·성분 연결 불일치·원 시편 독립성의 미확정을 보존한다. 실제 자료에서 15개의 성분 연결 불일치와 4개의 미확정 소성 변형률 단위를 확인했다. 원 문헌 재검토 전 이를 자동 보정 자료로 채택하지 않는다.
- 수소 수치 내보내기는 해시 변경 거절, 단위 미확정 유지와 선언 변환, 시계 보존 정책, 1초 불일치와 음수 처리 신호, 중간 잘못된 행 거절, 정확한 쉼표 복구 정책, 가변 길이 온도 곡선·역전·미기록 꼬리, 미충전과 0시간의 구분을 합성 자료로 검사한다. 실제 파일 집계와 조건 미확정은 [내보내기 기록](HYDROGEN_EXPORTS_KO.md)에 있다. 이 검사는 물리적 보정·장치 교정·시편 독립성을 증명하지 않는다.
- 수소 신호 변환은 작성한 전류·면적·전자수·전류효율에 Faraday 관계를 적용한 signed 투과
  플럭스, 질량 ppm/s에서 얻은 TDS mol/(kg-sample·s), 그리고 검토된 시편 질량이 있을 때의
  전체 mol/s를 독립 산술값과 대조한다. 시편 질량과 검토 상태의 모순도 거절한다. export 해시,
  채널/배경처리, clock 원점·단조성, series ID/label, ppm 기준과 검토 상태 불일치를 거절한다.
  `validation/hydrogen_signal_calibration_math.json`은 단위·계약 검증이며 실제 전극·검출기 보정,
  경계농도, 트랩 모수 적합 또는 실험 검증이 아니다.

- Lamé 해는 내·외면의 압력 경계조건, 정수압 한계에서의 편차응력 0, 얇은 벽 극한과 비교한다.
- 내압 환형단면 하중상태는 직경형과 반경형으로 독립 작성한 면적·극2차모멘트,
  축력/면적, 토크·외반경/극2차모멘트, 내·외면 반경응력과 폐쇄단 축응력을 대조한다.
  피로 종료 사건 계약은 네 개의 합성 사례로 확인된 시편 끝점, 압력계통 중단,
  우측 검열 runout과 출처 미확정을 구분한다. `validation/fatigue_endpoint_contract.json`은
  분류 계약 검사이며 압력 저하 임계값이나 실제 피로수명의 실험 검증이 아니다.
- ECP 다축 피로 reader는 14개 조건의 FS/SWT 파일쌍, 행 수와 실험수명의 정확한 순서
  일치를 요구한다. 실제 28파일·294개 방법별 처리행에서 실험 관측은 147개만 만든다.
  누락 pair, 행 수·수명 불일치, 잘못된 filename token과 비수치·비양수 행을 거절한다.
  `validation/ecp_multiaxial_dataset.json`은 파일 해시와 집계를 보존하지만 시편 독립성,
  끝점, 검열, 국부 응력장 또는 provider 수명모델의 독립 검증을 증명하지 않는다.
  `validation/pressurized_annulus_math.json`의 최대 상대오차는 선언 허용오차 `1e-12`
  이하이다. 고정 blind package의 hash·archive 안전성·20개 case ID·상수 하중열·빈 결과열과
  네 프로토콜 문서 해시, 10% 압력저하·2,000,000 cycle runout·재개 누적 규칙은
  `validation/fabest_hcf_package.json`에서 별도로 감사한다. 정량 종료 기준은 이 경쟁 패키지에만
  적용하고 별도 FABEST workbook의 누락 END 기준에는 전파하지 않는다. 전자는 수학 검증이고 후자는
  입력 프로토콜 감사이며 둘 다 피로기준·노치응력·강도·수명의 실험 검증이 아니다.
- 이산 임계면 계수는 단축 폐쇄 이력의 축방향 SWT와 45도 평면 FS, 순수 tensor shear의
  engineering shear 변환을 독립 폐형식과 대조한다. 벡터 경로 계산은 비스듬한 면내 경로의
  최대 표본쌍 chord와 면내 기준축 회전·반전 불변성, collinear 한계를 확인한다. 열린 주기,
  비단위·비직교 방향, 중복 ID와 정렬되지 않은 tensor를 거절한다.
  `validation/critical_plane_math.json`은 소스 해시와 오차를 보존한다. 이는 연속시간/평면
  수렴, minimum-enclosing-circle, 재료 보정·노치 해석·피로수명 또는 독립 실험 검증이 아니다.
- 국부 tensor 교환 어댑터는 합성 정삼각형 engineering-shear 경로를 tensor shear로 바꾼 뒤
  최대 chord와 minimum-enclosing-circle 진폭의 독립 기하값에 대조한다. 시간·공급자/solver,
  revision·mesh·field location·공간 평균·좌표 기저·measure·원본/설정 digest 보존, 엄격한 JSON
  왕복, 미검토 field·무효 표본·지원하지 않는 measure·좌표계 오류·context 불일치를 검사한다.
  `validation/local_tensor_adapter_math.json`은 교환과 계산의 합성 조합 검사이며 실제 FE 해,
  mesh 수렴, 노치근 장, 피로수명 보정 또는 실험 일치를 검증하지 않는다.
- minimum-enclosing-circle 전단 경로 계산은 정삼각형 점군의 원 반지름·최대 chord 절반·
  `2/sqrt(3)` 비와 세 support 표본을 독립 기하식에 대조한다. 직선 경로 한계, 불규칙 점군의
  exhaustive 1·2·3점 후보 해, 면내 축 회전·반전 및 순서·이동·스케일 불변성도 검사한다.
  `validation/critical_plane_minimum_enclosing_circle_math.json`에 결과와 해시를 보존한다.
  이는 유한 점군 계산 검증이며 연속시간 range, cycle counting, 방향 수렴, 수명 보정 또는
  독립 실험 검증이 아니다.
- 반구 평면 격자는 폐형식 후보 수, 단위 법선·면내 방향, 직교성과 법선 부호 중복 부재를
  검사하고 생성 후보가 벡터 경로 API에 직접 들어가는지 확인한다.
  `validation/hemisphere_plane_grid_math.json`은 소스·검사 해시와 최대 기하 오차를 보존한다.
  비등면적 유한 격자의 angular coverage, refinement 수렴 또는 연속 최적점 검증은 아니다.
- 면적 층화 Fibonacci 평면 후보는 `z` 층 중점·golden angle·단위/직교 프레임·부호 중복
  부재와 동일 명목 가중치의 합 `2π`를 검사한다. `z` 및 `z²`의 가중 적분을 해석값과 유한
  midpoint 합에 대조하며 `validation/area_uniform_fibonacci_plane_grid_math.json`에 해시와
  오차를 보존한다. 이는 정확한 equal-area Voronoi tessellation, covering radius, nested
  refinement 또는 연속 최적점 검증이 아니다.
- 격자 계열 비교는 단축 해석해를 포함하는 241개 위도형 기준과 서로 다른 phase의 128개
  Fibonacci 후보 두 세트를 같은 이력에 적용한다. 기준에 대한 FS/SWT 상대 변화가 독립식과
  일치하는지 검사하고, 엄격한 0.1%·1° 선언 기준이 실제로 미충족임을 보존한다.
  `validation/critical_plane_grid_family_comparison_math.json`에 phase별 계수·법선 차이와 해시를
  기록한다. 검증 통과는 사용자 진단 기준 충족이나 연속 최적점 자격을 뜻하지 않는다.
- 임계면 격자 세분화 보고는 단축 폐쇄 이력의 해석적 지배 방향을 모두 포함하는
  13·57·241 후보 중첩 격자에서 FS/SWT 최대값과 단계 변화를 독립식과 대조한다.
  `validation/critical_plane_grid_refinement_math.json`에 소스·검사 해시와 최대 절대오차를
  보존한다. 선언 허용값 충족은 미표본 방향 오차 상한, 연속 평면·시간 수렴 또는 실험 검증이 아니다.
- 임계면 시간 세분화 보고는 고정된 두 평면과 위상이 이동된 해석적 sine 주기의
  5·9·17·33개 중첩 표본을 사용한다. 각 단계의 이산 FS/SWT를 독립 표본식과 대조하고 이
  예제에서 연속 sine 한계 오차가 감소하는지 확인한다. 결과와 소스·검사 해시는
  `validation/critical_plane_time_refinement_math.json`에 보존한다. 이는 일반 파형의 표본 사이
  오차 상한, 연속 평면 수렴, 수명 보정 또는 실험 검증이 아니다.
- 적응형 임계면 검색은 기울어진 단축 폐쇄 이력을 16개 Fibonacci seed와 6단계 축소
  tangent ring으로 계산한다. SWT 계수·법선과 FS 계수를 독립 연속 해에 대조하고, 중심 유지로
  단계별 표본 목적값이 감소하지 않는지 확인한다. 결과와 해시는
  `validation/critical_plane_adaptive_search_math.json`에 보존한다. 이는 이 합성 예제의
  수학·소프트웨어 검증이며 일반 이력의 전역 최적, 방향 수렴, 수명 보정 또는 실험 검증이 아니다.
- Paris 적분은 독립적인 적응형 수치 적분과 비교하며 지수 2 및 그 근처의 수치 안정성을 확인한다.
- 용접 전력 파형은 전압·전류의 상관을 잃는 평균값 계산과 차이를 확인한다.
- 단위 차원·섭씨 오프셋·게이지압 변환에 필요한 대기압을 검사한다.
- 두께 증가 추세를 음의 부식속도 없이 예측 모델에 조용히 넣지 못하도록 검사한다.
- 검사에서 무지시 결과가 나왔을 때의 베이지안 갱신과, 물리적 수리의 의미를 구분한다.
- 확률의 기간·초기 생존 조건, 상호배타 경로의 빈도 보존, 독립성 미확정 상태를 검사한다.
- 합성 검열 수명 자료에서 알려진 지수·산포를 회복하는지 확인한다.
- CoolProp 물·수소 상태가 합리적 범위에 있는지 확인하고 실행 버전을 보존한다.
- 겨울철 재고 열수지는 상수 계수 지수 닫힌해, 최소온도 도달시간과 구간 에너지수지로 검사한다. CoolProp 조합은 1 atm 물의 단상 `Cpmass`·phase·판본을 보존한다. 동결·잠열·국부 열전달 또는 현장 heat tracing 검증은 아니다.
- 캐비테이션 선별은 300 K 물의 CoolProp 포화압·포화액 밀도와 조합해 정압 여유, 정수두,
  동압과 국부 캐비테이션 수를 독립식에 대조한다. 음의 여유, 미검토 상태, 게이지압과 0 속도
  중지도 검사한다. `validation/cavitation_math.json`은 열역학·대수 조합 검증이며 기포핵,
  비정상 inception, 붕괴, 침식률, 재료 손상 또는 실험 검증이 아니다.
- 캐비테이션 이력은 `+1000 -> -1000 -> +1000 Pa`의 합성 선형 여유에서 정확한 0.5~1.5 s
  비양수 구간, 1 s 지속시간과 500 Pa·s clipped deficit을 대조한다. 전 구간 음수와 한 점
  접촉을 구분하고 정렬·identity·digest·유효성 오류를 거절한다. CoolProp 온도 이력의 표본별
  상태 digest와 전체 이력 digest도 보존한다. 이는 표본 사이 선형 수학 검증이지 미표본
  압력극값이나 실제 캐비테이션·침식 실험 검증이 아니다.
- HDF 파형 축·분 단위 시계·중복 시각 정책과 사용자 파라미터·워크플로 상태 전달을 검사한다.
- 모든 등록 계산기에 명시된 합성 입력 예제가 있고 유한한 버전 결과 계약을 반환하는지 검사한다.

마지막 항목은 API 실행 검사다. 예제가 실행된다는 이유로 해당 재료·환경의 실험 검증이 끝났다고 표시하지 않는다.

추가 확장에서는 확산 농도의 공간 적분과 표면 유입의 질량 보존, 갈바닉 회로 전위 수지와 선형 범위, 두께 지도 결측 면적과 대각선 분리, 원통 열저항 직렬 해와 복사 에너지 수지를 확인했다. 열처리는 동시·연속 유지시간, 기체 재고는 온도 변화에 의한 가짜 누설 방지, TOFD는 독립 경로 기하, 경도는 단위와 기하, 항복은 교차점과 자료 부족 상태로 확인했다. 변형률 수명의 알려진 사이클 회복, 보정 범위 밖 거절, 압력 이력의 반 사이클·응력 범위·손상 관례와 물성 판본·보간 범위도 검사했다.

## 공개 데이터 적용

용접부 피로의 첫 예제는 S355, as-welded, 응력비 0.1, 단일 시험 단계로 식별되는 시편을 선택했다. 반복 시편과 표기된 이상치·미확정 입력을 제외했다. 시편 ID의 SHA-256으로 결정적인 분할을 만들어 훈련 26행과 보류 6행을 나눴다. 훈련의 미파단 관측 3개는 생존 우도에 포함했다. 보류 6행 중 파단 5행에 대해 계산한 로그 수명 RMSE는 약 0.340이다. 이는 동일 데이터 묶음 안의 작은 시편 분할이며 독립 장치 검증이 아니다.

COQTEL 두 실험은 166·263개 상태를 읽고 전류를 적분하며 파형 변화를 계산했다. 전기화학 시계의 동일 관측 반복을 명시적으로 처리했다. 파형 변화의 부식 깊이 보정이나 POD 검증은 아직 수행하지 않았다.

MetroPT-3 1,516,948행을 청크로 읽어 실제 시간 간격과 역전 여부를 확인했다. 이 자료에는 부식 성장의 정답이 없으므로 운전 이력 로더 검증과 향후 모니터링 연동에 한정한다. 수소 316L 자료의 여섯 인장 시편과 경도 자료 역시 해당 충전·제조 조건에 대한 관측이며 일반적인 수소 설비 고장모델을 검증하지 않는다.

부식저항 합금 편집 workbook은 제공자 MD5와 프로젝트 SHA-256을 대조하고 수식·매크로·
외부링크 실행 없이 읽었다. 합성 workbook 검사 7개는 지표·통계량 ID, SCE 전위·온도·
전류밀도·부식속도의 변환, `>800`·`<-2.5`·`Transpassive`·누락 분리, 공백이 있는 과학
표기, 참조 DOI와 권리 상태, pin·macro·필수 시트 거절을 확인한다. 실제 집계는 1,268개
원행·3,579개 지표 셀·정규화 가능한 숫자 1,622개다. 이는 편집 구조와 변환 계약 검증이며
원 문헌 시험 재현, 물리 시편 독립성, 재료 순위 또는 부식수명 검증이 아니다.

## 재현 명령

누설자속검사 집중검사는 magnetizer/reference/array/channel 연결, current·encoder pair 완전성,
field-vector 유한성, indication mapping과 review gate를 확인한다. 전체 모델 예제를 포함한 집중 묶음
130건이 통과했다. `validation/magnetic_flux_leakage_math.json`은 2 mm 간격 6표본의 10 mm span,
3-4-5 H vector, 0.6-0.8-1 B vector와 B/H ratio를 독립식으로 대조해 절대오차 0을 기록한다. 이는
수학·계약 검사이며 saturation, field uniformity, 신호처리, 검출·치수·POD의 실험 검증이 아니다.

와전류 집중검사는 probe/frequency reference coverage, raster geometry, skin-depth 항등식, indication
mapping/review와 negative-result 경계를 확인한다. 합성 DICONDE fixture는 raw signed integer, padding,
frame order, hash, 좌표 일치/불일치와 잘못된 SOP/modality를 검사한다. 모델 예제와 취득 체크섬까지
포함한 집중 묶음 140건이 통과했다. `validation/eddy_current_math.json`의 오차는 span과 skin depth에서
모두 0이며 수학 항등식·계약 검사일 뿐 검사 성능 검증이 아니다.

`validation/eddy_current_dataset_audit.json`은 고정 archive에서 simulation CSV 12개와 laboratory
DICONDE 10개, 2×20×253 형상, 150 kHz, 좌표 source 일치와 decode 경고를 집계한다. 원 point data를
포함하지 않으며 결함 치수·검출·POD·합격의 독립 검증이 아니다.

BAM의 3개 P92 시험은 630,582행과 시험 조건을 읽고 기록 사이클의 최대·최소 표와 stress peak가 일치함을 확인했다. 반올림된 같은 시각을 미세 시간으로 바꾸지 않았고 열린 경로를 소산 에너지로 바꾸지 않았다. FABEST는 관측 663행·변형률 수명 8행을 정적 기준·회귀 출력에서 분리했다. 고정 SHA-256과 73개 sheet, break-cycle 567·interruption 95·미확정 1행, END 기준 누락 60그룹, 문자 접미사 54행, 주석 89행과 검토 태그를 전수 대조한다. 이는 자유문에서 파단·runout·재시험·self-heating·유효성을 확정하는 검사가 아니다. 도금강의 24개 분극곡선은 부호·단위 로더를 적용했고, 공개 저항의 면적 기준이 미확정이므로 부식 전류의 독립 검증 자료라고 표시하지 않았다.

현재 로컬 결과 수는 `validation/summary.json`과 JUnit XML에서 확인한다. 각 검사는 소프트웨어 계약·수학·자료 구조 중 명시된 범위만 다루며, 통과 개수가 서로 다른 물리 현상의 독립 실험 검증 수를 뜻하지 않는다. GitHub CI 구성은 아직 호스팅된 실행 증거가 아니다.

HELPR 외부 공급자 검토는 `validation/helpr_provider_review.json`에 공식 v2.1.0 commit,
라이선스 선언, 검토 파일 해시와 CSV 열을 기록한다. `validation/helpr_adapter_contract.json`은
작성된 2행 CSV로 리비전·설정·자산·표본 ID 보존, NaN/빈 값 유지와 확률 비승격을 검사한다.
`validation/helpr_end_to_end.json`은 별도 제외 환경에서 공식 v2.1.0·고정 commit으로 대표
결정론 입력을 실제 실행하고, 생성한 life-criteria CSV를 공개 어댑터로 읽은 통합 증거다.
입력 설정 digest, 실행환경, 원 출력 해시, 공급자 경고 두 건과 결측 criterion을 보존한다.
공급자가 파괴저항에 도달하지 못해 `a/t=0.8`을 사용한 경우 `a(crit)`을 물리 파괴저항
교차점으로 부르지 않는다. 다른 한 건은 공급자 내부 불리언 비트 반전의 Python 폐기예정
경고로 분리한다. 원 CSV는 공개 검증 기록에 재배포하지 않는다. 이는 소프트웨어 통합
검사이며 규격 적용성, 균열성장 물리, 특정 배관 또는 독립 실험 검증이 아니다.

별도 가상환경의 비편집 wheel도 검사한다. 핵심 의존성만 있는 환경에서 SciPy·CoolProp·rainflow·pandas 없이 import·모든 스키마·쿠폰 계산·입력 스냅샷·JSON 왕복을 확인한다. 선택 의존성 환경의 NumPy 2.5.4·pandas 3.1.0·SciPy 1.18.1·CoolProp 8.0.0과 개발 환경의 NumPy 2.3.5·pandas 3.0.1을 구분한 실행 증거는 `clean_install.json`, `clean_full_install.json`, `clean_full_tests.xml`이다. 해당 기록의 모델·검사 수와 설치 코드 해시가 현재 소스에 대응하는지 함께 확인한다. Windows Python 3.12.14에서 확인하며 다른 OS·Python 버전은 CI 실행 증거가 추가로 필요하다.

## POD와 변동 하중 균열의 추가 검사

POD는 세 크기에서 정확히 0.1·0.5·0.9의 실험 비율을 갖는 합성 자료의 알려진 logit을 회복하는지 확인했다. 프로파일 경계에서는 별도 scalar 최적화로 구한 likelihood ratio와 비교한다. 크기 배율 변화, 분리·반복 시편·독립성 미선언, 검색 범위 안에서 한계를 찾지 못한 상태, 선언된 logistic 곡선과의 일치 및 무지시 갱신 연결도 검사한다.

`scripts/benchmark_pod.py`는 크기별 20개 독립 관측으로 구성된 알려진 실험을 250회 생성한다. 고정 seed 270626에서 247회는 적합되고 3회는 식별 부족으로 남았다. 목표 크기 상한의 포함률은 적합된 실험에 조건부로 약 0.935, 그 비율의 Monte Carlo 95% 구간은 약 [0.897, 0.963]이었다. 중간 크기의 점별 POD 하한 포함률은 약 0.951이다. 명목 95%의 유한 표본 정확성을 증명한 결과가 아니며, 독립 실제 검사나 operator/specimen 상관을 검증한 것도 아니다. 원시 진단 수치는 `validation/pod_synthetic_diagnostic.json`에 둔다.

변동 Paris는 상수 형상에서 닫힌 해, 형상표 절점을 지나는 경우 별도 전방 ODE와 비교한다. 인성·보정 범위·선언한 깊이 종료를 구분하고, 문턱·외삽 거절·하중 순서에 따른 높은 평균응력 peak의 영향·불충분한 root 해상도 거절을 확인한다. 이 검사는 closure·하중 지연·소성 또는 환경별 성장 계수의 실험 타당성을 증명하지 않는다.

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe scripts/fetch_data.py
.\.venv\Scripts\python.exe scripts/inspect_open_data.py
```

정확한 파일 해시·적합 계수·데이터 규모는 JSON 기록을 기준으로 한다. 실행 환경과 최신 검증 결과는 `validation/`에 보존한다.

## 재료·제작·용접·방식·충격시험의 추가 검사

성분 확인은 원소 미측정·요구 경계와 겹치는 구간·완전 불일치, heat 정책과 물리 범위, 매핑 판본·한 단계 명칭 조회·중복 별칭을 검사한다. 중첩 `Evidence`가 JSON·CLI·프로필·워크플로를 통과해 같은 의미를 유지하는지 확인했다. 절차 중지는 충족·미확정·미충족과 결과 필드 누락을 분리하며 계산 완료를 요구 충족으로 읽지 않는다.

두께 예산은 제조 차감과 성형의 순서 및 제작 후 실측값에 같은 손실을 다시 차감하지 않는지 검사한다. 용접 형상은 알려진 두 직선과 이상점에서 OLS·Theil–Sen·soft-L1을 비교한다. 경도는 영역 누락·확장 불확실성의 경계 교차를, 희석은 질량 보존과 미보고 원소 전파를 확인한다. 이는 형상 계측 정확도나 실제 절차 자격의 실험 검증은 아니다.

음극방식 예산은 f가 0→1, i가 1→0으로 바뀌는 합성 구간에서 끝점 전류가 0이어도 내부 peak가 생기는 경우를 검사한다. 독립 SciPy 적분, 시간 절점의 세분화, 전하와 전류가 각각 다른 양극 개수를 요구하는 경우를 대조한다. 전위·차폐·설치 간섭과 현장 보호성능은 별도 검증 대상이다.

충격 전이곡선은 알려진 네 파라미터와 목표 교차 온도 회복, shelf가 충분하지 않은 자료의 미확정, 관측 범위 밖 교차의 미제공, 이상점에서 robust loss의 영향을 검사한다. 별도 합성 통합 파일로 °C·mm 변환과 같은 보고 ID의 서로 다른 조사 조건을 구분했다. 실제 편집 자료의 14행 시범 적합은 같은 자료에 대한 기술적 적합이며 독립 시편 검증이 아니다. 입력 파일 SHA-256과 요청 해시를 남기되 원 관측과 점별 잔차는 배포하지 않는다.

## 면적 극값과 초음파 자료

적합도 Monte Carlo p값의 최소 해상도는 1/(모의 수+1)이다. 현재 빠른 합성 예제·반복 진단은 99회와 최소 p값 0.01을 사용하므로 이 진단 기준만으로는 어떤 표본도 거절되지 않는다. 150회 전부 계산됐다는 사실을 적합도 검정력의 증거로 사용하지 않는다. 별도 두 집중 모집단 거절 시험은 기준 0.05를 사용한다. 실제 분석에서는 기준·Monte Carlo 오차에 맞춰 모의 수를 늘리거나 표본/모형을 보강한다.

Gumbel MLE는 별도로 계산한 두 score 방정식이 성립하는지 확인한다. 면적 CDF의 직접 거듭제곱·한 블록과 k블록의 위치 차이·1,000 및 10²⁰⁰ 배 길이 배율·상수 관측의 비식별을 검사한다. 1−CDF를 직접 빼면 사라지는 작은 꼬리 확률도 확인한다. 동등·독립·미검열 조건 미확인, 면적 상한 초과, 음의 깊이 확률과 두 집중 모집단의 적합도 거절을 검사했다.

`scripts/benchmark_pitting.py`는 위치 0.002 m·척도 0.0002 m인 알려진 분포에서 40블록씩 150회 생성하고 400블록 면적을 평가한다. 99회 적합도 모의와 199회 파라미터 재표집에서 150회가 계산됐다. 명목 95% 파라미터 구간의 참 분위수 포함률은 142/150≈0.947, 참 초과확률 포함률은 143/150≈0.953이다. 각각의 Monte Carlo 95% 구간은 약 [0.898, 0.977], [0.906, 0.981]이다. 모형 가정 아래의 유한 반복 진단이며 정확한 명목 포함률이나 공간 독립성·현장 성능을 증명하지 않는다. 원시 진단은 `validation/pitting_synthetic_diagnostic.json`에 seed·환경·알고리즘 해시와 보존한다.

WILLOW는 합성 MAT 2,000건과 특징표의 깊이·폭·변환자 길이를 전수 비교했다. 최대 기하 차이는 약 4.34×10⁻¹⁹ m이고 형상 불일치는 0개다. 파형의 비유한 값 25건과 제공자 처리 실패 30건은 서로 다른 품질 표식으로 남긴다. 실제 두 시편의 308·466개 시각은 원 신호와 특징표에서 일대일 일치했다. 170건의 처리 실패와 장기 공백을 보존했다. 합성 파일 시험은 단위·축·불완전 특징 처리의 검증이며 실제 결함 치수·POD의 독립 검증이 아니다.

CEIT 해안 노출 JSON은 고정 SHA-256에서 2,715개 레코드, 하나의 시편·node·piezo ID와 엄격 증가 시계를 전수 검사했다. 네 배열 길이는 모든 행에서 각각 2,048·2,048·64·512이고 전 표본은 유한하지만 2,715개 raw 레코드 모두 ADC rail 값을 3~77개 포함한다. 139개 관측 달력일 중 114일에 20개 레코드가 있으므로 제공자 요약의 하루 두 번을 행 수나 독립 관측 수로 해석하지 않는다. 파일에 없는 ToF·온도 단위, 음속·경로·교정·독립 치수는 검증되지 않았고 134 µm/year 요약도 재현하지 않았다. `validation/ceit_uniform_corrosion_field.json`은 구조·품질 집계이지 두께·부식속도 모델 검증이 아니다.

확률 연동에서는 공간 초과·POD·의미 미선언 값을 기간 사건으로 보내지 못하도록 검사했다. Weibull의 나이 시계와 기간이 다른 변환, 큰 절대 나이에 비례해 허용오차가 커지는 문제도 거절한다. 모니터링 스냅샷을 변경해 원 평가 결과가 바뀌지 않는지 확인했다. 사용자 플러그인은 확률 의미를 명시해야 하며 단위가 없는 확률 선언을 길이 출력에 붙일 수 없다.

## 축 방향 감육 용량과 배관 편집 자료

절점 면적 스캔은 모든 구간을 별도로 SciPy 적분한 결과와 대조한다. 무손상·균일 손실·M=1의 닫힌 해, 긴 대부분 건전한 프로파일 안에서 짧은 구간이 지배하는 경우, 모든 길이의 기하학적 상사와 압력비 불변을 확인했다. 원 절점을 포함하는 세분화에서 최소 용량이 증가하지 않는지도 검사한다. 이것은 연속 끝점 최적해 또는 실제 파열압 정확성의 증명이 아니다. 공급자 ID·길이 범위·이용근거·단조성, 깊이 한계·0 잔존벽·겉보기 증육·적용성 미확인의 상태 전파를 검사한다.

파열 편집본은 공개 ZIP 체크섬과 주 표의 453행·실험/FEM 구분·색상 범례를 대조했다. 합성 workbook 검사로 SI 변환, 시험 파열압/FEM 실패압 역할, 범례 문헌/미해결 표식, 보완/추정 셀, 물리 시편·원 관측 권리의 미확정과 원 수식의 비실행을 확인한다. 실제 자료의 388개 보완 물성 셀·302개 추정 폭, 지름·압력 기준과 `Ma13Otros` 23행의 원 문헌·중복·시편 독립성은 압력 예측 자격과 분리한다. Ma 논문 출판사 페이지의 79개 수집 시험과 편집본의 직접 문헌 실험 79행이 수치상 같다는 사실만으로 행 대응을 만들지 않는다. 현재 이 자료로 새 모델의 독립 파열압 검증을 수행하지 않았다.

`validation/burst_prediction_comparison_math.json`은 합성 자료에서 calibration과 holdout
source group을 분리하고 예측/관측비 0.8과 1.25의 평균 1.025 및 로그오차 RMS를 독립 식으로
대조한다. 검사에서는 중복 물리 시편, calibration/evaluation source-group 누설, 미검토
끝점·형상·압력 기준·이용 권한, 미고정 예측을 거절하거나 `needs_data`로 유지한다. 이는 비교
산술과 계약 검증이며 실제 압력모델이나 파열시험의 독립 검증이 아니다.

수집기에서는 임시 서명·query·fragment·URL 자격정보가 기록되지 않는지 모의 응답으로 검사했다. 캐시 파일의 체크섬 불일치를 취득 성공으로 표시하지 않는지도 확인했다. 빌드 단계는 취득 장부에 이런 URL 구성요소가 남아 있으면 중지한다. 실제 외부 자격증명이나 서명을 시험 입력으로 저장하지 않는다.
## HyMatBase 4130X 수소가스 피로 workbook

`scripts/inspect_hymatbase_hydrogen_fatigue.py`는 provider MD5와 일치하는 55,972바이트 workbook을
고정 SHA-256으로 읽었다. R=0.1/0.5와 0.1/1 Hz의 네 curve에서 각각 67·79·62·63점, 총 271점을
확인했다. ΔK 범위는 9.0593–33.452 MPa√m, da/dN 범위는
7.3406×10⁻⁹–4.0967×10⁻⁶ m/cycle이다. workbook에는 24개 수식 셀이 있지만 reader는 이를
실행하지 않으며 curve 데이터 열의 수식은 거절한다.

합성 검사는 SHA-256·sheet/header 변경, 압력 충돌 미승인·불필요 승인, 수식 data cell, 한쪽만
누락된 point pair, SI ΔK 변환과 원 행 보존을 검사한다. 실제 감사 결과는 record 4.5 MPa와 workbook
45 MPa의 충돌을 그대로 보고한다. 이는 파일 구조와 reader 계약 검증이며 271개 독립 시편, 시험
유효성, 서비스 성장곡선 또는 수명모델 검증이 아니다. 결과는
`validation/hymatbase_4130x_hydrogen_fatigue_audit.json`에 있다.

## Gaussian 평균이동 중요도 샘플링

`scripts/validate_importance_sampling.py`는 작성 합성 표준정규 변수에서 `Z > 4`인 사건의
정확 확률 `3.167124183311998e-05`를 기준으로 한다. 고정 seed 20261027과 `N(4,1)` 제안분포의
32,768개 표본에서 추정값은 `3.1147082116145e-05`, 표준오차는
`3.683496362471136e-07`, 절대오차는 `5.241597169749806e-07`이었다. 사전 선언한 6 표준오차
한계 `2.2100978174826816e-06` 안에 들었다. 제안 사건은 16,085건이었다.

전체 가중치 평균은 약 0.7500이고 전체 ESS는 약 12.62로 낮지만 사건 가중치 ESS는 약
5,869.55다. 이는 목표분포 전체의 왼쪽 꼬리를 평균이동 제안이 드물게 표본화하는 유한표본 현상을
그대로 드러낸다. 가중치를 정규화해 평균 1로 만들거나 진단을 숨기지 않았다. 0 이동에서 crude
Monte Carlo와 정확히 같아지는지, 직접 계산 우도비, 사건 0건, 정체성·차원·정렬·비유한 입력,
검토 gate와 context 불일치도 단위검사로 확인한다.

이 증거는 한 차원 Gaussian 우도비와 추정 산술의 수학 검증이다. 실제 물성분포·상관 매핑,
부식/파괴 한계상태, FTA 사건, 제안분포 최적성, 독립 물리 검증이나 허용위험 판정을 검증하지
않는다. 고정 결과는 `validation/gaussian_mean_shift_importance_sampling.json`에 있다.

## 연속 배관 ILI workbook

`scripts/inspect_pipeline_ili_data.py`는 제공자 SHA-256이 고정된 네 XLSX의 3,198,420행,
269,180,366바이트를 제한된 메모리로 전수 감사했다. 회차별 행은 735,755·832,681·759,683·870,301개다.
모든 파일에서 15개 header와 기대 회차 token이 일치했고 수식·비수치 셀은 없었다. Year 3의 seam
orientation과 Year 5의 end distance는 전부 누락되어 있으며 이를 채우지 않는다. 합성 단위검사는
SI 변환, 원 행·누락·음수 보존, 명시적 행 범위, hash/header/year 불일치 및 수식 거절을 확인한다.
이 결과는 workbook 구조·reader 계약 검증이며 feature matching, 성장률, 원 MFL 또는 결함 치수
정확성의 검증이 아니다. 고정 집계는 `validation/pipeline_ili_history_audit.json`에 있다.

## 사용자 표형 균열성장곡선

`scripts/validate_tabulated_crack_growth.py`는 외부 시험점 대신 독립적으로 작성한
`da/dN=1e-28(ΔK)^3` 점을 사용한다. 기하평균 `ΔK`에서 로그–로그 보간 상대차는 약
`2.22e-16`이고, 상수 형상·응력범위의 닫힌형식 Paris 해와 1,000 cycle 뒤 깊이 상대차는 약
`2.20e-11`이다. 곡선 상한에 해당하는 깊이는 독립 대수식과 일치하며 `out_of_scope`와
`growth_curve_upper_bound_reached`를 보존한다.

R=0.1·1 Hz와 R=0.5·0.1 Hz의 작성 곡선을 순서대로 선택한 두 block 계산도 각 power-law의
구간별 닫힌형식과 비교했다. 최종 깊이 상대차는 약 `1.92e-11`이고 선택 ID 순서를 보존했으며
조건 사이 보간은 수행하지 않았다. 단위검사는 유일한 근접 후보, 후보 없음과 동일거리 동률을
별도 종료 사유로 확인한다.

작성한 두 공동 표본은 성장률 배수 0.5/2.0과 가중치 0.25/0.75를 사용한다. 각 배수의 닫힌형식
깊이를 직접 가중한 값과 계산기 평균의 상대차는 약 `6.21e-14`이고, 선언한 0.00102 m 초과질량은
0.75다. 가중합 불일치·중복 sample ID·비증가 분위수 요청을 거절하며, 한 표본이 성장곡선 지원범위를
벗어나면 해당 행을 삭제하지 않고 모든 집계와 초과확률을 `null`로 보류하는지 확인한다. 단일곡선과
곡선군 기준입력 두 경로를 모두 검사한다.

같은 퇴화 공동분포를 2행과 4행 nested design으로 표현한 검증에서는 평균·표준편차·분위수·초과질량의
단계간 변화가 모두 0이고 진단 기준을 만족한다. 새 표본이 통계를 바꾸는 경우는 계산 결과와 기준
미충족을 함께 보존한다. 적용범위 밖 표본이 포함된 단계는 삭제하거나 재정규화하지 않고 전체 진단을
`out_of_scope`로 만들며, 기존 nested ID 삭제·기존 배수 변경·첫 단계 관계 위조는 거절한다. 이는
표본설계 계약과 변화량 산술 검증이며 수렴 증명이나 오차상한 검증이 아니다.

완전입력 시나리오 앙상블에는 성장률 0.5배/2배의 독립 전체 입력과 질량 0.25/0.75를 사용했다.
닫힌형식 가중 평균 대비 상대차는 약 `6.21e-14`, 선언 깊이 초과질량은 0.75로 전역 배수 경로와
일치한다. 곡선 한 점·형상 knot·하중 block·인성을 함께 바꾼 비축약 시나리오는 서로 다른 canonical
input digest와 계산 결과를 보존한다. 실패 시나리오를 포함하면 모든 집계를 보류하고, 중복 ID·
가중합 불일치·물리 범위 혼합을 거절한다. 이는 완전입력 전달과 집계 검증이지 입력분포·시나리오
확률·model-form 또는 실제 재료의 검증이 아니다.

portable map/reduce 검증에서는 두 완전입력 시나리오를 별도 job 함수로 계산하고 평가행 순서를
반전해 reducer에 전달했다. reducer 출력은 manifest 순서를 회복했고 in-process 앙상블 평균과 절대차
0으로 일치했다. 평가 ID 집합 불일치, deterministic-input digest 변경, evaluator revision 혼합을 각각
거절한다. `execution_failed` 행은 삭제하지 않고 모든 집계를 보류한다. CLI smoke test는 같은 예제에
대해 두 JSON map 결과와 하나의 reduction artifact를 만들었다.

단위검사는 이용권한·적용성 gate, 증가하지 않는 `ΔK`, 명시하지 않은 문턱, 지원범위 외 보간,
응력비·주파수 불일치와 곡선 상한/인성 종료 분리를 확인한다. 결과는
`validation/tabulated_crack_growth_math.json`에 있다. 이는 수학·계약 검증이며 실제 수소환경,
재료곡선, 장·단균열 전이, closure·지연, 형상 K 해, 파괴인성 또는 서비스 수명의 검증이 아니다.

## 임계확률 검사시점 선택

`scripts/validate_inspection_scheduling.py`는 독립 작성한 네 개 후보와 최대확률 0.08을 사용한다.
점추정치 `[0.01, 0.03, 0.07, 0.12]`를 직접 순회한 기대값은 세 번째 후보이고, 상한
`[0.02, 0.05, 0.09, 0.14]`의 기대값은 두 번째 후보다. 등록 계산기가 두 결과를 정확히 재현하고
보간·consequence optimization flag가 모두 거짓인지 확인했다.

단위검사는 비증가 시각·누적확률, 점추정치보다 작은 상한, 상한 누락, 중복 ID, context 불일치,
검토 gate 누락, 허용 창 후보 부재와 첫 후보 이전 기준초과를 포함한다. 고정 결과는
`validation/inspection_scheduling_math.json`에 있다. 이는 이산 후보 선택 계약의 검증이며 실제
열화 forecast, 확률기준, 검사효과, 비용·결과 또는 현장 주기 검증이 아니다.

## 검사·정비 행동 기대손실

`scripts/validate_inspection_action_expected_loss.py`는 독립 작성한 baseline·검사·수리 세 행동,
총 결과비용 5,000과 행동비용 0·100·400을 직접 계산한다. 점추정 확률 0.10·0.04·0.01에서는
총 기대손실 500·300·450으로 검사를 고르고, 상한 0.12·0.10·0.02에서는 600·600·500으로
수리를 고른다. 등록 계산기의 모든 후보 총액과 선택이 직접 산술과 정확히 일치한다.

같은 검증은 세 외부 결과를 `ActionEventProbabilityEvaluation`로 만들고 수신 어댑터를 거쳐 실행한다.
어댑터 단위검사는 역순 평가행의 선언순서 복원, 결과·구조·common-cause identity 보존, 누락·추가·
중복·미계산 행동 차단과 event/asset/scope/failure-mode/horizon/conditioning 각각의 불일치를 확인한다.

전용 단위검사는 비용 구성요소 합, baseline 대비 순편익, 상한 기준의 선택 변경, 비용 동률에서
임의 선택 차단, 검토 gate, 상한 누락·역전, 중복 행동 ID, baseline 수·비용, 기간과 context를
확인한다. 고정 결과는 `validation/inspection_action_expected_loss_math.json`에 있다. 이는 산술과
교환계약의 검증이며 실제 사건확률, 검사·수리 효과, 비용·결과, 위험허용도 또는 법규 판정의
검증이 아니다.

## 검사결과별 처분 의사결정나무

`scripts/validate_inspection_disposition_tree.py`는 작성한 세 결과분기의 확률 0.7·0.2·0.1,
처분비용 0·400·100, 조건부 잔여확률 0.10·0.01·0.05와 선행 검사비용 50을 직접 합산한다.
등록 계산기의 기대 처분비용 90, 총 행동비용 140과 잔여확률 0.077이 직접합과 일치하고, 변환된
행동 후보가 같은 비용과 확률을 보존하는지 확인한다.

전용 단위검사는 결과확률 합·중복 ID·기간·common-cause ID, 검토 gate, context, 예약 비용 ID,
잘못된/미계산 결과의 후보변환 차단과 기존 기대손실 비교까지의 end-to-end 조합을 포함한다. 고정
결과는 `validation/inspection_disposition_tree_math.json`에 있다. 이는 유한합·계약 검증이며 POD,
오탐, 실제 결과분포, 처분효과, 경제비용이나 규격판정의 검증이 아니다.

## 유한 검사정책 경로 생성

`scripts/validate_finite_policy_path_generation.py`는 초기상태 확률 0.8·0.2와 한 decision epoch의
상태별 clear/alert 관측, monitor/repair 규칙, 전이표를 독립 전개한다. 생성된 7개 비영 경로의 확률합은
1이며 기존 평가기로 연결한 최초고장확률은 0.064, 기대 행동비용 19.6, 할인 고장결과 57.6, 총손실
77.2다.

전용 단위검사 11건은 2개 epoch의 16개 경로와 확률질량, 실패 뒤 중단, 생성→평가 end-to-end,
검토 gate, 경로한도, 초기·관측·전이 확률합, 결정규칙 coverage, failure factor와 시점순서·context를
검사한다. 결과는 `validation/finite_policy_path_generation_math.json`에 있다. 실제 상태분류·POD·전이
확률·정책 성능이나 최적성 검증이 아니다.

## 유한 정책 관측·전이확률 보정

`scripts/validate_finite_policy_probability_calibration.py`는 독립 작성한 가중 빈도에서
`P(clear|healthy)=0.75`, `P(alert|degraded)=0.75`, `P(failure|healthy,monitor)=0.2`,
`P(failure|degraded,monitor)=0.4`를 직접 계산하고 holdout log loss와 등록 계산기를 대조한다.
전용 단위검사 8건은 분할 누출, 미지원 conditioning row, 명시적 smoothing, 0확률 holdout 사건,
알 수 없는 라벨·비양수 시간구간과 정책 epoch 어댑터를 검사한다. 결과는
`validation/finite_policy_probability_calibration_math.json`에 있다.

같은 산출물은 공개 ILI 3,198,420행을 `not_qualified_for_probability_calibration`으로 기록한다. 해당
자료에는 영속 feature identity와 독립 굴착 truth가 없기 때문이다. 따라서 이 검증은 빈도·점수 산술과
계약 검증이며 실제 검사기의 혼동확률, 부식전이, 행동효과 또는 현장 적용성 검증이 아니다.

## 다기간 고정 검사정책

`scripts/validate_multi_period_inspection_policy.py`는 작성한 세 경로 확률 0.5·0.3·0.2를 직접
합산한다. 경로별 할인 행동비용은 145·480·100이고 고장 경로의 할인 결과비용은 800이다. 등록
계산기의 기대 할인 행동비용 236.5, 기대 고장결과 160, 총손실 396.5와 조건부 최초고장확률 0.2가
독립 합과 일치한다.

전용 단위검사는 확률합·중복 경로 ID·시점순서·기간·고장 이후 행동, 검토 gate, context, 고장필드의
정확한 동시 존재와 입력 불변성을 확인한다. 고정 결과는
`validation/multi_period_inspection_policy_math.json`에 있다. 이는 유한 경로 산술·계약 검증이며
경로 생성, 상태전이, 검사효과, 비용·할인, 정책 최적성 또는 규격판정의 검증이 아니다.

## 다기간 정책의 제약 우선 비교

`scripts/validate_multi_period_policy_comparison.py`는 확률한도 0.15와 예상 outage 8일 한도를 세 정책에
직접 적용한다. 기대손실 300인 정책은 고장확률 0.30으로 제외되고, 기대손실 400인 정책은 확률 0.20과
outage 10일로 제외된다. 확률 0.08·outage 7일·기대손실 450인 정책만 통과하며 등록 계산기의 선택과
일치한다.

전용 단위검사 13건은 검토 gate, 무통과, 비용동률, 공통 사건문맥, 정확한 자원집합·단위·상한,
비용 항등식, 평가결과 어댑터 digest, 입력 불변성과 context를 검사한다. 고정 결과는
`validation/multi_period_policy_comparison_math.json`에 있다. 이는 제약 적용 순서와 유한집합 산술
검증이며 실제 정책·확률·자원·비용·제약·전역 최적성 또는 규격판정 검증이 아니다.

## LCF 벤치마크 산술과 종료점

`scripts/validate_fatigue_benchmark_metrics.py`는 독립 작성 값으로 세 계약을 검사한다. 두 시험의
주기응답 점수는 시험별 점수 0.15와 0을 같은 비중으로 평균해 0.075가 된다. 수명을 10배 과대·과소
예측한 두 case의 10진 로그 잔차는 +1과 -1이므로 RMS 로그오차는 1이다. 기준 탄성률 100, 10% 저하
임계값 90, 관측값 95와 85 사이의 교차는 관측점 정책에서 cycle 10, 선형보간 정책에서 cycle 7.5다.

전용 단위시험 12건은 배열 정렬, 고유 ID, 양수 정규화·수명, 가중치 합, 관측점/보간 교차,
닫힌 무교차 관측의 우측 검열과 열린 관측창의 `needs_data`를 확인한다. 고정 결과는
`validation/fatigue_benchmark_metrics.json`에 있다. 이 검사는 산술과 API 계약 검증이며 실제
42CrMo4+QT 보정, blind 결과, 실험 독립성, 재료 적용성 또는 설계 허용 검증이 아니다.

`scripts/inspect_fabest_lcf_data.py`는 고정 v2 archive의 제공자 MD5·프로젝트 SHA-256, 170개 member,
경로 안전성, 중복·암호화 부재, 24개 calibration experiment, 96개 table, 25,213,349개 data row와
7개 header 계열을 검사한다. 전용 합성 archive 단위시험 4건은 계층 보존, validation outcome CSV
차단, exact header 요구와 ragged row 거절을 확인한다. 이 증거는 archive/software 계약 검증이며
점별 수치의 물리 타당성, 물리 시편 독립성, blind outcome 또는 재료모델 성능 검증이 아니다.

## 압력–온도 운전경계 산술

`scripts/validate_pressure_temperature_envelope.py`는 두 개의 작성 선형 구간을 사용한다. 200–300 K에서
허용압력이 14–10 MPa, 300–500 K에서 10–6 MPa로 변할 때 250 K와 400 K의 독립 보간값은 각각
12 MPa와 8 MPa다. 운전압력 11 MPa와 9 MPa에 대한 압력여유 1 MPa와 -1 MPa가 등록 계산기와
일치한다.

전용 단위시험 6건은 정확 knot와 내부 보간, 경계 초과, 지원범위 밖 외삽 차단, 적용성·운전점 검토
gate, 비증가 knot·중복 ID·비양수 허용압력·알 수 없는 보간법을 확인한다. 139개 전체 모델의 합성
예제도 함께 실행했다. 고정 결과는 `validation/pressure_temperature_envelope_math.json`에 있다.
이는 보간·계약 검증이며 실제 설계표, 재료 적용성, 공정 과도이력, 불확실성 또는 규격 판정 검증이
아니다.

## 공정 모니터링 교환계약

`scripts/validate_monitoring_exchange.py`는 작성 P–T 평가 결과를 `MonitoringAssessmentRecord` JSON으로
왕복하고 모델 결과·입력 digest·문맥이 보존되는지 확인한다. 값 하나를 바꾼 레코드는 원 assessment
digest와 불일치해 거절된다. 별도의 `needs_data` 결과는 상태를 유지하며 normal 또는 alarm 필드를
생성하지 않는다.

전용 단위시험 6건은 JSON 왕복, 값·모델 버전·확률 의미 변조, flat/context identity 불일치와
미계산 상태를 검사한다. 고정 결과는 `validation/monitoring_exchange_contract.json`에 있다. 검토한
`process-monitoring-toolkit` revision은 아직 이 스키마 수신기를 구현하지 않았으므로 이는 송신 계약과
음성대조 검증이지 실제 저장소 간 end-to-end 실행, 고장진단, 경보 성능 또는 고장확률 검증이 아니다.

## 수소 재료수송 교환계약

`scripts/validate_hydrogen_transport_exchange.py`는 작성한 보존 이력의 JSON 왕복과 complete-payload digest를 확인한다. 재고 한 값을 바꾼 레코드와 셀 길이가 어긋난 농도장은 거절된다. 검토한 `hydrogen-physical-models` revision은 `TransportResult`를 제공하지만 이 교환 Schema의 exporter는 아직 없다. 따라서 고정 결과 `validation/hydrogen_transport_exchange_contract.json`은 계약·배열·변조 음성대조 검증이며 실제 저장소 간 실행, 계수 자격화, 수렴, 실험 또는 손상·고장확률 검증이 아니다.

## 인적신뢰도 교환계약

`scripts/validate_human_reliability_exchange.py`는 작성 레코드의 JSON 왕복, 확률·conditioning·revision 변조 거절과 작업기회 확률의 기간 최초고장확률 재명명 차단을 검사한다. `--provider-root` 실행에서는 고정 `human-reliability-toolkit` revision의 실제 `AssessmentEngine` 예제를 실행해 event와 estimate를 수신했다. 고정 결과는 `validation/human_reliability_exchange_contract.json`이다. 이는 software end-to-end와 의미보존 계약 검증이며 인간 수행도, 현장 전이성, 요구빈도, 의존성, 재료고장 또는 기간 위험 검증이 아니다.

## 배관 평가 결과 교환계약

`scripts/validate_pipeline_exchange.py --provider-root <checkout>`는 검토한 실제 배관 소스 트리에서 `geometry.pipe`를 실행하고 완전한 `pipeline_integrity.result.v1`을 `PipelineAssessmentRecord`로 왕복한다. 검토 트리는 111개 파일, SHA-256 `446ffe69d10dbcc57427dcc45a37eef39da0e9b92bf7ce0c04a2d29230bb37c0`이며 commit이 없는 상태라 revision으로 부르지 않는다. clock 변조와 screening 결과의 현장·설계승인 재명명을 거절했다. 고정 결과는 `validation/pipeline_exchange_contract.json`이다. 이는 소프트웨어 교환검증이며 배관 물리·부식·설계규격·현장 또는 시스템 위험 검증이 아니다.

## 용접 수소 bakeout 유한 평판

`scripts/validate_hydrogen_bakeout.py`는 정온 특성시간 `d²/(π²D)`에서 독립 급수 50항과 비교하고, 동일한 `∫Ddt`를 갖는 서로 다른 knot 이력의 시간변환 불변성을 확인한다. 별도로 기존 보존형 `transport.hydrogen_slab_kinetic`의 80셀·무트랩·양면 0농도 계산과 대조했다. 고정 결과 `validation/hydrogen_bakeout_math.json`에서 급수 절대오차는 약 `4.5e-13`, 시간변환 오차는 0, 유한체적 상대차는 약 `1.12e-3`이다. 이는 수학·소프트웨어 교차검증이며 실제 weld diffusivity, trap, HAZ 이질성, 수소균열, procedure 또는 규격 검증이 아니다.

## NIST CORR-DATA archive 구조 감사

`scripts/inspect_nist_corr_data.py`는 제공자 SHA-256, ZIP 구성/CRC, 고정 CSV header와 row width를 확인하고 필드별 결측 및 혼합 token 유형만 집계한다. 고정 archive에서 24,721행·15열, 239 reference key와 두 rate 필드의 numeric scalar 5,896/5,823개·range token 16/15개가 확인됐다. `validation/nist_corr_data_audit.json`은 aggregate 값과 digest만 저장한다.

합성 단위시험 `tests/test_nist_corr_data.py`는 schema drift, member 불일치, token 유형과 manifest pin 거절을 검사하도록 작성했으나 아직 실행 전이다. 누리온 검증 목록 batch46에 포함됐다. 이 감사는 row-level 출처·제3자 권리·단위·시험조건·물리 시편 독립성·모델 정확도를 확인하지 않으며 적합·재료 선정·위험 평가의 근거가 아니다.

## 공개 JSON Schema 파일 식별성

서로 다른 모듈의 동명 계약이 같은 JSON 파일명으로 덮어써지던 문제를 수정했다. 중복 클래스명은 모듈 basename을 포함해 출력하며, 과거의 충돌 산출물 네 개는 제거된다. 현재 exporter는 계약 543개에서 고유한 JSON Schema 543개를 만든다. helper의 합성 회귀 테스트는 `tests/test_export_schemas.py`와 HPC batch47에 추가됐으며 아직 실행 전이다.

## 2026-10-29 Davies 활동도 계수 검증 준비

탄산 알칼리도 activity standard state 고정 및 review gate 회귀를 batch58에 추가했다. Davies 활동도 계수의 독립 계산 회귀, 전하 불균형·선언 적용상한·review gate·중복 종 ID 거부와 종합성 예제를 batch59에 등록했다. 로컬 pytest 및 누리온 작업은 실행하지 않았다. 이 계산은 고염수 보정이나 습식 CO₂ 부식률의 검증이 아니다.

CT110 공개 보충자료의 수치비교 회귀를 `batch60-material-corrosion-rate-contrast`에 추가했다. 동일 연구의 여섯 조건에서 원 수치의 WM/BM 비가 보고된 한 자리 비율과 일치하는지 확인하도록 구성했으며, 이는 자료 전사 및 산술 재현이지 독립 실험 검증이 아니다. 로컬 테스트와 누리온 실행은 아직 하지 않았다.

## 최초 통과 계약의 계보 경계

`SampledLinearThicknessFirstPassage`의 nested `source_lineage`에 있는 모든 수치를 재귀적으로 유한성 검사하고, 공백 review reference key/value를 거부하도록 했다. NaN 주입 및 빈 review ID 회귀는 기존 HPC batch78 테스트 파일에 추가했다. 이번 변경의 pytest 및 누리온 실행은 하지 않았으며 일괄 검증 대기 상태다.

## 국부 용접 열처리 band dwell 추정

센서 이력에서 인접한 두 온도 사이를 선형으로 놓고 사용자 지정 hold band와 교차하는 시간 구간을 적분한다. 시험에는 가열·냉각 중 부분 교차 및 flat/단조/비단조 segment 경계를 포함했다. 회귀는 batch79에서 실행 대기이며, 센서 샘플 간 실제 파형·peak 검증이나 야금학적 절차 자격을 검증하지 않는다.

## 용접 잔류응력 불확도 support 경계

provider stress support 검사는 응력 중심값뿐 아니라 중심값 ± caller expanded uncertainty 구간에도 적용한다. 중심은 범위 안이지만 불확도 상단이 범위를 넘어가는 합성 사례를 batch80에 등록했다. 회귀는 Nurion 일괄 실행 대기이며 불확도 모델의 적합성이나 weld acceptance를 검증하지 않는다.

같은 계약에서 지원범위 밖인 모든 record와 application record ID를 최상위 결과로도 반환한다. 이 목록은 계산 성공 상태와 별도로 후속 모듈에서 screening/제외 기준으로 사용할 수 있으며, 위험 확률이나 승인 판정을 뜻하지 않는다. 회귀는 batch81에 등록했고 실행은 대기 중이다.

## 용접 잔류응력 qualification metric 단위 일치

Holdout metric 값·허용 상한에 명시된 단위 문자열이 정확히 일치하는지 계약에서 검사한다. 단위가 서로 다르면 환산을 추측하지 않고 입력을 거절하며, 호출자는 한 단위 체계로 값을 공급해야 한다. 회귀는 batch82에 등록했고 Nurion 검증 대기 상태다.

## 용접 잔류응력 자료 partition 격리

Calibration, holdout, application의 source-group ID 집합을 서로 겹치지 않도록 요구하고, 결과에 각 partition별 record ID 목록을 반환한다. calibration/holdout record가 application 목록에 포함되지 않으며 source group 재사용을 거절하는 회귀를 batch83에 등록했다. 이는 split 누수 방지의 계약 검사이며 provider 예측력 또는 물리적 검증을 뜻하지 않는다.

비교 row에는 record/support Evidence, source group, provider revision/state와 record·dataset digest를 보존하도록 했다. 입력 객체를 잃은 뒤에도 결과만으로 lineage에 접근하는 회귀가 batch84에 등록됐으며 아직 실행 전이다.

Application coverage는 입력 행 수와 provider 비교 완료 행 수를 별도로 반환한다. provider와 매칭되지 않거나 여러 지원 후보가 있어 비교 못 한 application 행도 coverage를 실패시키고 unsafe ID에 포함하며, 좌표 차원·영역 이탈 사유는 비교행에 남긴다. 이 경계 회귀는 batch85에 등록돼 있고 실행 대기다.

매칭된 application의 좌표 차원 불일치와 declared coordinate support 영역 밖 위치에는 각각 reason code를 기록하고 unsafe ID를 확인한다. 합성 회귀를 batch86에 등록했으며 실측 좌표 등록/변환 정확도 검증은 아니다.

Record가 축 이름·순서를 명시하고 provider support와 순서가 정확히 같아야 비교한다. frame ID가 같더라도 축 순서가 다르면 자동 permute하지 않는 회귀를 batch87에 등록했다. 좌표 변환·registration 정확도 또는 실측 잔류응력 검증은 아니다.

같은 frame ID와 axis token을 써도 정의된 origin/rotation/축 방향 내용이 다를 수 있어 record와 support에 frame-definition SHA-256 pin을 요구하고 비교한다. digest mismatch 제외 회귀는 batch88에 등록했고 실제 좌표계 surveyed accuracy 검증은 아니다.

동일 provider/frame 후보는 있으나 tensor/stress component 정의가 다른 입력은 generic unmatched로만 두지 않고 `component_definition_mismatch` 원인을 반환한다. 회귀 batch89는 axial 대 transverse 성분을 비교대상으로 승격하지 않는지 확인하며 물리 측정 유효성을 검증하지 않는다.

복수 support 후보에 매칭되는 application 행은 arbitrary candidate를 고르지 않고 ambiguous ID/reason을 반환하며 coverage 실패로 남긴다. 회귀는 batch90에 등록했고 아직 계산 실행 전이다.

입력 전체 record와 support lineage를 partition과 관계없이 결과에 보존한다. unmatched application row와 calibration/holdout row가 비교 테이블 밖에서도 digest/Evidence를 유지하는지 batch91로 회귀 명세했다.

## 2026-10-31 추가 모델의 증분 검증 계획

- **Scale moving boundary:** 구간별 정확 적분을 독립 `solve_ivp` 기준 적분과 비교한다. 농도차 0, 용해 소진 시각, 구간 분할 불변성, 온도 지원범위 거부, finite overflow 종료를 분리한다. 이 수치 비교는 일대일 몰수지·정상 근사·고정 물성을 검증할 뿐 scale 보호나 부식률을 검증하지 않는다.
- **Scale reaction demand balance:** 독립 `solve_ivp` 공급·소비 ODE 참조와 DOP853 adaptive integration을 비교한다. 공급/수요 무구동, 공급만/소비만, 평형점 양쪽 방향 접근, 비통과, 소진 시각, 구간 분할 불변성, 직접 몰 flux와 부호 검토된 부분전류 변환, 잘못된 부호, Faraday/좌표 overflow 및 0 underflow를 분리한다. 모델의 공급 장부는 두께 변화와 소비에서 복원된 값이므로 별도 보존 증거로 간주하지 않는다.
- **Gasket leakage map fit:** 생성한 비음수 bilinear surface로 알려진 knot 복원과 내부점 보간을 대조한다. Holdout이 계수를 바꾸지 않는지, calibration rank 부족, 서로 다른 시편/source group partition 경계를 확인한다. 이는 실제 seal law·시편 간 전이·acceptance를 검증하지 않는다.
- **Crevice kinetic network:** 단일 1차 반응 및 선형 교환계의 독립 행렬 지수 기준해를 BDF와 Radau 결과와 비교하고, 원소/전하/종 inventory closure, interval prefix, 음수 농도/계산 예산 실패를 평가한다. Caller rate law와 well-mixed 가정의 적용성은 별도 자료 검토가 필요하다.
- **Ince–Glinka GSA:** 독립 scalar tensor projection으로 finite-plane GSA 결과를 계산하고, 좌표 회전·전단 부호·mean normal stress·cycle closure 허용오차 및 plane×sample work budget 경계를 확인한다. 이 모델은 한 cycle 지표이며 수명/수명예측 검증으로 오해하면 안 된다. 해당 원 논문은 GSA의 regime별 예측 정확도가 같지 않음을 보고하므로 다른 수명영역으로의 전이를 독립 데이터로 평가해야 한다.
- **Zenodo DEIS import:** 로컬 전용 pinned archive SHA-256/byte count, 16개 member와 CRC, 두 54×8640 numeric matrix, 각 member digest, 선택된 row/pair 개수를 확인한다. 선택형 인접 real/imaginary 열 view는 pinned depositor metadata와 명시적 caller review가 필요하며 row axis/time/frequency/unit을 정하지 않는다. 예제/검증 로그는 측정 셀을 출력하지 않는다.
- **Ti-12Mo-5Hf archive audit:** 고정 ZIP에 대해 publisher byte count/MD5와 caller SHA-256, 경로탈출 member, member 수와 총 확장 크기 제한을 확인했다. 51개 entry와 declared expanded bytes만 기록했으며 CRC/file content, worksheet schema, units, images, observations는 점검하지 않았다. Reader regression remains unverified until parallel HPC checks; archive structure audit is not scientific validation.
- **Adaptive cycle block damage:** constant derivative/damage closed form 및 nonlinear scalar ODE reference, block order/split, fine-step tolerance convergence, callback identity/revision/configuration/calibration/state-ID/unit/cycle-basis matching before/after each call, extra failure status rejection, state stage bound, event bracket non-commit, exact 12-call budget and rejected call accounting, minimum step below remainder, error-scale overflow/underflow, and large integer cycle coordinate resolution. This verifies integration of a declared law only, not fatigue calibration or material validity.

위 task는 최신 revision에 대해 한강에서 병렬로 준비 중이다. 이 계획을 실행 결과로 간주하지 않는다. 로컬 계산·테스트는 아직 실행되지 않았다.
