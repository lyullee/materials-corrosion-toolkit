# 공정 시뮬레이터 이력 연동 요청

수명 곡선의 지정 온도와 대표 측정 재료 온도는 `temperature_basis`로 구분한다. 시뮬레이터의 유체 온도나 순간 센서값을 근거 없이 두 기준 중 하나로 표시하지 않는다.

크리프 수명 연동에서는 유체 온도 대신 실제 부위 재료 온도와 국부 응력·하중 제어 관례를 공급한다. `creep.conditional_life`는 새 재료 상태부터 일정 조건이었다는 선언을 요구하며 변동 시계열을 직접 받지 않는다. 초기 명목 정하중과 일정 진응력의 공급자 ID를 구분하고, 실제 조건 변화를 기준 곡선에 구간별로 대입해 확률을 더하지 않는다. 변동 이력 손상 경로와 재시작 상태는 후속 별도 계약으로 구축한다.

검토한 기준 소스는 lh2dt_models `b2f276333c1b1793c39f25763703d196d36742ec`, hydrogen-station-sim `9f8fa941c611abc092a10516a09e31ec2908c1d6`이다.

## psa-dyna 다성분 공정상태 연동

검토 기준 저장소는 [lyullee/psa-dyna](https://github.com/lyullee/psa-dyna)다. 2026-10-30 확인 시 public repository이며 GitHub가 표시한 코드 라이선스는 [MIT](https://github.com/lyullee/psa-dyna/blob/main/LICENSE)다. 공개 README는 비등온 1D 다성분 PSA/VPSA 모델, 압력·온도·조성 상태, cycle/step ledger, 그리고 별도 qualification gate가 있는 cycle-average FEED/PRODUCT/TAIL 스트림을 설명한다. 현재 DWSIM 전달 가능 여부나 cycle-average 수렴을 재료부식 입력의 적합성으로 간주하지 않는다.

상대 저장소 확장 요청:

1. 재료 평가 대상 위치를 식별하는 `asset_id`, `location_id`, `stream_id`, bed/step/cycle ID, case ID 및 `clock_id`를 각 이력에 보존한다. PSA-Dyna bed 내부 기체 상태를 실제 금속 표면 경계로 자동 간주하지 않는다. 부식 대상 위치와 stream/bed 사이의 물리적 연결은 별도 검토 입력으로 둔다.
2. cycle-average 제품 스트림과 transient within-cycle 상태를 별도 제품으로 내보낸다. 시간 의존 손상·부식·흡착/탈착 평가에는 기준시계가 있는 transient 표본을 사용하며 cycle 평균만 전달해 극값·노출 시간을 대체하지 않는다.
3. transient 표본마다 단조 시간, 총 절대압, 온도, 모든 성분 ID와 mole fraction, 품질 mask, 측정/모델 예측 기원, case/input digest, solver revision/source-tree digest를 함께 내보낸다. 성분은 고정된 순서로 직렬화하고 mole fraction 합계·허용오차·결측 의미를 계약에 명시한다. 시간·압력 기준을 바꾸거나 유효하지 않은 표본을 조용히 제거하지 않는다.
4. MatIntegrity 측에는 `matintegrity.co2_mixture_fugacity_history.v1` (`Co2MixtureFugacityHistory`)와 caller-mapped CSV reader가 구현됐다. `read_co2_mixture_history_csv()`는 bytes, `load_co2_mixture_history_csv()`는 파일 경로를 받고 초·절대 Pa·K·몰분율 열을 명시적으로 연결한다. 둘 다 원본 CSV digest를 유지한다. `co2_mixture_fugacity_requests_from_history()`는 유효 표본별 `thermo.co2_mixture_fugacity_coolprop` 입력을 만들고 invalid row를 `needs_data`로 남긴다. 이는 기체 상태량 연결이며 수용액 활성도·pH·부식률을 만들지 않는다.
5. 현재 MatIntegrity에는 PSA-Dyna의 `dynamic-psa-mean-stream/v1` report에서 선택한 FEED/PRODUCT/TAIL cycle-mean stream을 `PSADynaMeanStreamFugacityBatch`로 변환하는 dict 및 JSON-file adapter가 있다. 파일 adapter는 raw file SHA-256과 canonical report digest를 분리해 보존하며, 보고서 내부의 절대경로를 따라가지 않는다. 명시적 absolute-pressure review와 조성/EOS/phase review가 필요하고 upstream case/result/source-archive digests 및 mean-stream basis를 보존한다. 이 adapter는 주기 평균 상태에 대한 CO₂ 기체 퓨가시티 평가만 요청하며 transient/표면 노출/부식률로 해석하지 않는다. 실제 upstream output 파일 인수, 물리 boundary mapping과 수치 검증은 별도 과제다.
6. CoolProp 경로에는 각 표본의 mixture composition, 전체 절대압, 온도, backend/EOS, phase 판정 및 provider digest를 전달한다. 부적합 상태는 이상혼합 fallback 없이 그 표본을 `needs_data`/`out_of_scope`로 남긴다. 이후 수용액 반응망에 CO₂ fugacity를 연결하려면 용해·수화, 물 조성, 전하/알칼리도, 이온 활동도, 용해도 자료와 온도 적용성을 별도 공급한다.
7. PSA 흡착제 ID/열역학 및 kinetic parameter는 배관·용기 alloy의 재료 상태나 부식 상수로 재사용하지 않는다. H₂ 분율만으로 수소취성·투과량을 추론하지 않고, H₂S·염화물·수분·액상 응축·벽온도는 PSA에 포함되지 않으면 추정하지 않는다.
8. 인수 기록은 고정 commit/source digest와 case hash, species-order 고정, 표본 clock/quality mask, cycle-average와 transient 분리, 성분 합계·질량보존, 알려진 순수/혼합 CoolProp 상태와의 별도 비교를 포함한다. 이는 양 저장소 계약/수치 인수이며 실제 설비의 부식·수명·위험성 자격화가 아니다.

이 요청서는 상대 저장소를 수정하거나 완료했다고 주장하지 않는다. 공개 PSA-Dyna 문서는 산출물 중 `last_cycle_trace.csv`가 존재한다고 밝히지만, 이 요청 작성 시점에 해당 파일의 정확한 헤더·단위·공간 위치 의미와 개별 stream/bed 추출 규칙은 확인되지 않았다. 따라서 CSV reader는 일반 caller-mapped 입력기이며 PSA-Dyna와의 직접 호환을 보장하지 않는다. Mendeley의 FH Münster N₂-PSA workbook은 CC BY 4.0 표시와 provider checksum이 확인됐지만 시간 trace가 아니라 520행 설정·주기·결과 표이므로 CO₂ 부식 경계 history에 직접 연결하지 않는다. 연결을 마치려면 upstream이 시간별 outlet/bed location CO2-mixture 상태와 절대압·온도·성분 순서·품질·단위·고정 clock 및 run provenance를 별도 export로 명세하고, 그 실제 export를 별도로 매핑·수용해야 한다.

`matintegrity.operating_history.v1`에 맞춰 자산·부위·공통 시계·측정/예측 기원·시간·절대압·온도·품질 마스크·출처 해시를 공급한다. 벽온도와 유체온도는 다른 물리량으로 내보내며 향후 계약 확장으로 구분한다. 국부 응력을 공급할 때는 사용한 구조모델과 형상·위치·좌표계도 함께 식별한다.

캐비테이션 선별에 사용할 압력은 해당 평가 위치의 절대 국부 정압이라는 물리적 의미를 별도
필드 또는 검토 기록으로 선언해야 한다. 용기 대표압·정체압·게이지압을 자동 변환하지 않는다.
같은 `clock_id`와 표본 길이를 가진 양의 특성속도 이력, 속도 정의와 위치 정의를 공급한다.
`cavitation_history_inputs_from_operating_history`는 자산·부위·시계·측정/예측 기원과 원본
digest를 보존하고 결정적 표본 ID를 만든다. 각 온도의 CoolProp 상태 digest와 전체 물성 이력
digest도 수신 측에서 유지한다. 품질이 거짓인 표본을 삭제·정렬·보간해서는 안 된다. 실제
연동 인수 시험에는 공급자 commit, export hash, 압력 센서/CFD 위치와 시간 해상도를 고정한다.

station의 재충전 카운터는 운영 이력 근거로 유지하고 그 자체로 부식률·강도 저하·누출빈도를 바꾸지 않는다. 반복 하중 평가는 시간에 따른 압력 범위와 운전 모드에서 실제 사이클을 추출하는 경로를 사용한다.

초기 연동은 공정 상태에서 재료 평가로 흐르는 단방향 계산으로 한다. 감육 후 형상을 공정 솔버에 되돌리는 양방향 연동은 질량·에너지·시간 단계와 구조 상태의 일관성을 검증한 뒤 추가한다.

인수 시험은 같은 구간을 나눠 전달했을 때의 재현성, 시간 중복·역전·결측, 절대압 기준, 시뮬레이션 초와 실제 시각의 혼동, 측정·예측 혼합 방지를 포함한다.

MatIntegrity의 첫 실행 소비자는 `workflow.pressure_fatigue`다. `examples/process_history.py`와 `tests/test_process_workflow.py`에 계약·손상 관례·거절 예제가 있다. 상대 저장소에서는 구조모델에 필요한 실제 부위 반지름·두께와 외압을 함께 연결하고, 피로 파라미터의 재료·온도·응력비·범위 근거를 별도 공급한다. 이력 구간을 나눠 전달할 때는 rainflow의 잔여 극값을 보존하는 스트리밍 계약이 추가로 필요하다. 현재 모델은 한 번의 완결된 구간을 평가하므로 구간별 손상값을 무조건 더하지 않는다.

감육 용량과 비교하는 경우에는 외부 절대압도 제공해 내부−외부의 차압을 구성한다. `declared_model_pressure_difference_capacity_Pa`는 차압 용량이며 절대 내압이나 규격 MAWP가 아니다. 외압·온도·형상/재료 상태·기준 공급자의 적용 범위를 확인하고, 이 정보가 없으면 여유·파손 확률 계산으로 승격하지 않는다.
