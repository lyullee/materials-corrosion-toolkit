# 분할 상 라벨 지도의 면적분율

연결 성분 및 격자 경계 descriptor는 [PHASE_MAP_TOPOLOGY_KO.md](PHASE_MAP_TOPOLOGY_KO.md)를 참고한다.

연결 성분 및 범주별 격자 경계 요약은 [PHASE_MAP_TOPOLOGY_KO.md](PHASE_MAP_TOPOLOGY_KO.md)를 참고한다.

`matintegrity.phase_map_data.summarize_phase_label_map()`은 caller-provided 정수 라벨 배열에서 검토된 ROI 안의 상별 픽셀 수와 면적을 집계한다. 라벨 배열, ROI mask, missing mask 각각에 dtype·shape·바이트를 포함하는 SHA-256 digest를 요구한다. 상 ID와 정수 라벨, 미분류 label, 균일 pixel width/height, 좌표계, 분할 방법, source group 및 물리 시편을 caller metadata로 고정한다.

Oxford Instruments `.cpr/.crc` 입력은 선택 의존성 DefDAP 1.3 계열 reader를 통해
`matintegrity.oxford_ebsd.read_oxford_ebsd_phase_labels()`로 읽을 수 있다. 설치는
`python -m pip install 'matintegrity[ebsd]'`를 사용한다. 함수는 caller가 고정한 전체 archive SHA-256과
member stem을 확인하고, 요청한 한 쌍만 임시 폴더에 추출한 뒤 raw 정수 phase-label array와 읽기 기록을
반환한다. 기록에는 원래 member SHA-256, 배열 해시·shape·dtype, 라벨 값, reader 버전과 provider grid-step
숫자가 포함된다. raw 배열은 읽기 전용으로 반환하며 원 archive나 pointwise map을 내보내지 않는다.

DefDAP가 방향 메타데이터가 누락된 이 자료를 읽을 때만, 독립 임시 입력본의 `.cpr`에 0 회전 placeholder를
추가한다. 이는 reader가 phase label을 파싱하도록 하는 형식 호환값이며 실제 acquisition orientation으로
주장하지 않는다. 적용 여부는 `reader_compatibility_patch`에 남고 원 member hash는 수정 전 파일 기준이다.
grid-step `0.1`의 물리 단위는 이 reader에서 확인되지 않아 값과 `not_declared_by_adapter` 상태를 함께 둔다.
DefDAP phase descriptor와 정수 label 간의 재료상 의미도 자동 연결하지 않으므로 사용 전에 별도 mapping review가
필요하다.

`scripts/validate_oxford_ebsd.py`는 Aalto 공개 ZIP의 세 map을 읽고 형상·격자 값 및 합계가 닫히는 label
histogram을 aggregate 진단으로 출력한다. HPC manifest의 전용 command와 batch107의 mocked reader 회귀가
등록되어 있지만, 연결 확인만으로 실행한 것은 아니므로 아직 DefDAP 실자료 reader 검증 결과는 없다.

## 산출량

ROI 픽셀 중 missing으로 표시되지 않은 픽셀을 analyzed area로 둔다. 각 상의 면적은 상 label count와 caller가 검토한 pixel area의 곱이다. 상별 `area_fraction_of_analyzed_region`은 모든 analyzed pixel(미분류 pixel 포함)을 분모로 하고, 선택적 `area_fraction_of_classified_region`은 이름이 지정된 상 pixel만 분모로 쓴다. 두 비율은 서로 다른 질문에 답하므로 자동 정규화하거나 혼용하지 않는다. ROI·missing·analyzed·classified·unclassified pixel 및 면적 합계는 결과 계약에서 닫힌다.

## 다른 모델로 전달

`phase_label_map_to_observations()`는 검토된 지도의 상분율을 기존 `PhaseFractionObservation` 계약으로 넘길 수 있다. 호출자가 모든 phase ID에 대해 별도 근거가 있는 expanded uncertainty를 제공해야 하며, transfer helper는 이를 생성하지 않는다. caller가 지정한 불확도 basis는 결과 Evidence로 추가된다. 관측은 이후 `materials.phase_microstructure_assessment` 또는 새 `materials.phase_fraction_linear_contrast` 입력에 연결할 수 있다. 선형 대비의 교차 상 공분산은 별도 계측/분석 결과를 caller가 제공한다.

합성 입력 실행은 `examples/phase_label_map.py`에서 확인할 수 있고, 독립 수치 계약 회귀는 batch106에 있다. 회귀는 로컬 실행하지 않았으며 누리온 제출도 하지 않았다.

## 한계

픽셀 비율은 영상 분할의 편향, 해상도, 대표성, 결정립 상관, sectioning/etching 오류 또는 field-to-bulk bias를 정량화하지 않는다. 픽셀을 독립 Bernoulli 표본으로 취급한 confidence interval이나 binomial standard error를 만들지 않는다. 배열에 표시된 label의 공학적 상 식별도 입증하지 않는다. 균일한 직사각형 픽셀 면적과 ROI 정합은 사용자가 별도로 검토해야 한다. 이는 영상 기반 기하 요약이며 상평형·열처리 예측, 용접 적합, 규격 수용, 강도·인성·부식 또는 수명 평가가 아니다.
