# 환경 열화 applicability와 증거 기록

이 문서의 모델은 서비스 조건이 사용자가 검토한 시험·qualification envelope에 포함되는지 구조화한다. 표준 threshold, 열화속도, 균열성장, 수명 또는 합격 기준은 포함하지 않는다.

## Sour environment

`degradation.sour_environment_applicability`는 material grade·heat·microstructure, hardness와 unit, H₂S absolute partial pressure와 그 산정 basis, pH·temperature·chloride·exposure duration·stress descriptor를 exact identity와 범위로 비교한다. Qualification envelope 정의에는 calibration test record만 사용할 수 있고 holdout source group은 분리한다. Partial pressure와 total/gauge pressure를 자동 교환하지 않는다.

결과는 caller envelope에 대한 applicability다. SSC/HIC 발생, crack growth, hydrogen uptake, failure probability 또는 service acceptance를 계산하지 않는다.

## Chloride SCC

`degradation.chloride_scc_applicability`는 material condition·metallurgy, chloride unit, temperature·pH, oxidizing basis, applied/residual stress descriptor와 누적 노출시간을 caller-owned envelope에 비교한다. Dissolved oxygen 수치 경로와 qualitative oxidizing-state 경로를 섞지 않는다. Unit·basis·identity 불일치는 `needs_data`, 검토된 service condition의 범위 이탈은 `out_of_scope`다.

결과는 SCC threshold, initiation time, growth rate, lifetime 또는 probability가 아니다.

## Ammonia와 alkaline SCC

`degradation.ammonia_scc_applicability`는 ammonia phase·concentration unit, water/oxygen/impurity state와 applied/residual stress descriptor를 caller qualification envelope에 비교한다. `degradation.alkaline_scc_applicability`는 alkaline species·concentration unit, temperature, electrochemical descriptor·reference·potential, applied/residual stress definition과 linked test evidence를 비교한다. 두 모델 모두 완전한 검토 기록의 지원범위 이탈은 `out_of_scope`, identity·unit·evidence 결손은 `needs_data`로 구분한다. Threshold, initiation, growth, lifetime과 probability는 계산하지 않는다.

## Microbial campaign

`degradation.microbial_campaign_summary`는 campaign/site/clock, sampling location coverage, sample validity, target·method·unit·detection limit가 붙은 assay, water context와 biofilm/deposit observation을 보존한다. `below_detection`은 0으로 바꾸지 않고 detection-limit censored record로 유지한다. Caller indicator와 exact target/method/unit가 맞을 때만 정량 비교한다.

미생물 또는 biofilm 관측은 corrosion causality, MIC rate, metal loss, lifetime 또는 failure probability의 증거로 자동 승격하지 않는다.

## 고온 sulfidation·carburization·nitriding

`degradation.sulfidation_exposure_applicability`는 sulfur species와 quantity kind·basis·unit, temperature, absolute pressure, flow/deposit descriptor를 qualification evidence와 비교한다. `degradation.carburization_applicability`는 carbon activity 또는 carburizing-potential basis, gas descriptor와 누적시간을 비교한다. `degradation.nitriding_applicability`는 nitrogen species와 driving-force basis·unit, gas descriptor와 linked test evidence를 비교한다. 이들은 scale thickness, carbon/nitrogen profile, diffusion·reaction kinetics, phase·property 변화나 수명을 계산하지 않는다.

## Metallurgical aging equivalent exposure

`degradation.metallurgical_aging_exposure`는 각 온도 interval에 외부에서 보정된 nonnegative equivalent-time rate multiplier를 적용한다. 하나의 material condition, aging mechanism과 provider ID를 전체 history에서 유지하고 provider 온도 support를 외삽하지 않는다. Equivalent exposure와 caller limit의 비교는 phase fraction, embrittlement, strength·toughness 저하 또는 remaining life 예측이 아니다.

## Caller-calibrated loss histories

`degradation.acid_dissolution_history`와 `degradation.erosion_corrosion_loss`는 interval별 외부 보정 rate와 provider support/state digest를 받아 두께 손실을 적분한다. `degradation.under_deposit_calibrated_loss`는 같은 방식으로 local loss를 적분하면서 deposit-covered area-time도 별도로 계산한다. 세 모델 모두 chemistry, flow, particle 또는 deposit observation에서 rate를 자체 생성하지 않으며 provider support 밖을 외삽하지 않는다.

`degradation.under_deposit_local_environment_review`는 공통 `LocalEnvironmentHistoryAssessment` 계약에서 domain이 `under_deposit`로 명시된 기록을 받아 caller-defined 기준과 측정값의 불확도 구간을 비교한다. `computed`는 기준 비교 계산이 끝났다는 뜻이며, 부식 원인 진단이나 재료 합격을 뜻하지 않는다. 누락·무효·단위/기준 불일치는 근거 부족으로 보존하고, 이 API는 rate 적분이나 확률 추론을 하지 않는다. 예제는 합성 값만 사용한다.

`degradation.selective_leaching_applicability`는 alloy/composition/phase와 environment·redox/potential support를 먼저 비교하고 microscopy/composition 관측의 value·expanded uncertainty를 exact method/definition/unit caller range와 따로 비교한다. Dealloyed-depth growth, residual strength, fracture 또는 lifetime은 계산하지 않는다.

## 취성 시험 applicability

`materials.brittle_applicability_evidence`는 material specification·condition, product form, governing thickness·orientation, service temperature와 loading/rate descriptor를 사용자가 검토한 시험 envelope에 비교한다. 시험 record는 물리 시편, source/independence group, 방법, 원 단위, 불확도와 provider/result digest를 보존한다. 요구 시험 수가 충족돼도 설계 최저온도, 취성파괴 확률, 허용 결함 또는 규격 합격을 생성하지 않는다.

## 고온 수소와 액체금속 접촉

`degradation.high_temperature_hydrogen_applicability`는 절대 수소 분압 basis, 온도·누적시간, 재료 조성·열처리와 microstructure inspection evidence를 caller qualification support에 비교한다. `degradation.liquid_metal_embrittlement_applicability`는 structural material/condition, liquid composition·impurity profile, contact/wetting descriptor, 온도·응력·변형률속도와 시험 evidence를 비교한다. 두 결과는 지원범위 확인이며 attack·embrittlement 발생, 손상률, 균열성장, 수명 또는 고장확률이 아니다.

## Crevice species inventory

`degradation.crevice_species_inventory_history`는 외부 rate provider가 주는 각 species의 순 source rate를 구간별로 적분한다. Species 집합, material/bulk-solution identity, temperature·gap support, clock, provider digest와 지정된 solution volume을 유지한다. 구간의 온도·gap은 기존 시작점 값만 지정할 수 있고, 필요 시 끝점 값과 명시적 선형 경로 검토를 추가한다. 시작과 끝 조건 모두 provider support 안에 있어야 하며, 직선 보간 경로는 사각형 지원 범위 안에 머문다. 결과 interval exposure ledger에는 시작·끝 조건과 두 endpoint 산술평균을 보고용으로 포함한다. 이 평균은 provider rate 산출이나 시간적분에 사용하지 않는다. 인접 구간 경계에서 이전 끝 조건과 다음 시작 조건이 다르면 경계 step을 숨기지 않고 별도 검토 플래그를 요구한다. 경계 연속성의 수치 판정은 상대 허용치 1e-12, 온도 절대 허용치 1e-12 K, gap 절대 허용치 1e-15 m를 사용하며 이 비교 기준은 결과 ledger에 그대로 기록된다. 이 기준은 판정용일 뿐 경계 입력값을 평균·수정하지 않는다. 결과는 각 knot의 좌/우 온도·gap과 jump 크기 및 검토 여부를 포함하는 knot history를 반환한다. 시간 순서 condition history digest는 같은 interval의 rate diagnostics가 condition record digest로 참조하며, 각 rate row에는 provider state/record digest와 interval input digest도 함께 보존된다. 시도된 interval rate ledger에는 별도 SHA-256이 있어 실패한 구간 prefix도 확인할 수 있다. 입력된 구간 조건 이력과 provider identity/record digest도 계산 결과에 시간 순서대로 출력하고 각각의 SHA-256 및 composite lineage digest에 연결한다. 이 조건 경로는 rate 법칙을 생성하거나 rate를 보간하는 기능이 아니다. Rate 자체는 기존 구간 상수 입력을 사용하거나 시작/끝 rate 쌍과 별도 선형 rate 검토를 제공해 해당 구간의 속도를 사다리꼴 적분한다. 결과에는 초기 재고, 시계·부피 이력, rate interval 및 provider support 장부의 digest를 포함해 계산 lineage를 재구성할 수 있게 한다. 종별 누적 source와 최종 재고 수지 잔차도 제공하지만, 잔차는 산술 추적 자료이며 보존법칙의 독립 검증이나 화학 모델 검증이 아니다. 각 interval의 경계 시각·부피와 시작/끝 inventory·농도 digest를 묶은 순서 ledger도 포함해 반환된 시계열과 구간 ledger가 일치하는지 확인할 수 있다. 계산 중 실패하면 마지막 공통 완료 knot까지만 species 재고 prefix를 반환하고, 실패 interval은 `failed_interval_id`와 후보 rate 진단으로 식별한다. 해당 interval은 어느 종의 재고에도 commit하지 않는다. 음의 재고는 0으로 자르지 않고 범위 이탈로 보고한다. 전하 불균형은 caller tolerance와 함께 `needs_data`로 보존하고, 농도 변환·inventory 적분·전하 집계가 유한 수치 지원을 넘으면 `out_of_scope`로 fail-closed 처리한다. 이 모델은 electroneutrality를 강제로 맞추거나 pH, activity coefficient, transport/reaction kinetics, precipitation, corrosion rate를 자체 계산하지 않는다.

## Phase/microstructure

`materials.phase_microstructure_assessment`는 sample·region·phase identity가 붙은 fraction과 expanded uncertainty를 caller-owned range에 비교한다. 한 sample-region의 nominal measured fractions가 1을 넘으면 거절하지만, 합이 1보다 작다고 미측정 phase를 나머지로 추정하지 않는다. Phase fraction만으로 strength, toughness, corrosion resistance 또는 cracking을 계산하지 않는다.

## 위험성 평가 연결

Applicability 결과를 FTA basic event나 기간 고장확률로 직접 변환하지 않는다. 실제 손상 사건으로 연결하려면 독립 calibration/holdout, 노출기간·조건부 기준, inspection detection, competing mechanisms와 model-form uncertainty를 포함하는 별도 모델과 adapter가 필요하다.
