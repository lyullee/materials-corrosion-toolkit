# 누설자속검사 acquisition 계약

`inspection.magnetic_flux_leakage_acquisition_summary`는 MFL 신호를 자동 해석하는 모델이 아니라 검사
acquisition의 물리·디지털 identity를 보존하는 계약이다. 사용자 절차와 리비전, 자화기 종류·방향·
제어 근거, 센서 array의 channel과 축 성분 mapping, lift-off와 calibration, 물리 reference feature,
검토된 H/B field-state checkpoint, encoded scan과 indication evidence를 입력한다.

reference standard는 실제 magnetizer와 모든 sensor array를 명시적으로 포함해야 한다. scan은 선언된
array channel만 사용할 수 있고 data SHA-256, pass 방향, 속도·근거, sample 수와 원 acquisition 순서를
보존한다. sample spacing·origin·mapping basis가 모두 있을 때만 `(N-1) dx` encoded span을 계산한다.

field checkpoint는 호출자가 지정한 좌표계의 H 또는 B vector와 측정 근거를 보존한다. 계산기는
Euclidean magnitude와, H가 0이 아닐 때 B/H magnitude ratio를 기술값으로 반환한다. 이 ratio는 재료의
constitutive permeability, hysteresis curve, magnetic saturation, field uniformity 또는 검사 감도를
뜻하지 않는다. 벡터 상태의 물리 위치·온도·자화 이력이 다르면 서로 대체할 수 없다.

baseline 제거, 속도/lift-off 보상, sensor fusion, filtering, anomaly detection/classification, 결함
내·외면 구분, 깊이·길이·폭 sizing, acceptance, POD, 남은 수명과 고장확률은 수행하지 않는다. indication이
없으면 검토된 negative-result 기록이 필요하고, indication을 자산 위치에 연결하려면 physical location과
mapping basis를 함께 제공해야 한다.

## 공개자료 조사 경계

Mendeley Data의 `10.17632/c2h2jf5c54.1`은 CC BY 4.0으로 공개된 네 차례 ILI 외부부식 기록이다.
자료 설명은 200 km가 넘는 한 pipeline의 7년 이상 연속 검사라고 밝히지만 검사기의 MFL raw flux,
sensor calibration, lift-off, velocity 또는 독립 excavation truth를 제공한다고 확인되지 않았다. 따라서
MFL 신호 검증 자료로 등록하지 않는다. README와 네 XLSX를 제공자 체크섬으로 취득했고 3,198,420개
행을 전수 감사했다. `pipeline_ili_data.py`는 source row·누락·단위·회차를 보존하는 별도 reader이며,
회차 간 feature matching이나 성장률은 만들지 않는다. 세부사항은 `PIPELINE_ILI_HISTORY_KO.md`에 있다.

`Farhad-Davaripour/AI_Applications_in_Pipeline_Engineering`의 고정 검토 commit
`e153d3e8d0539722abcfaaabb989c6423256278e`은 MIT를 선언하고 위 자료를 이용한 가공 parquet/CSV와
추적·ML 코드를 제공한다. 로컬 검토 clone은 배포 경로 밖 `tmp/`에만 있다. upstream code, notebook,
가공 파일이나 모델을 복제하지 않았고 그 anomaly matching을 MatIntegrity의 자격화된 feature tracking
또는 성장 truth로 사용하지 않는다. 이 자료는 별도의 ILI history provenance reader와 calibration/
holdout 설계 후보이며 MFL 원신호 자료와 분리한다.

수학 재현은 `scripts/validate_magnetic_flux_leakage.py`, 결과는
`validation/magnetic_flux_leakage_math.json`, 합성 실행 예는 `examples/magnetic_flux_leakage.py`다.
