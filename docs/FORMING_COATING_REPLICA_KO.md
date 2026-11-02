# 성형 형상·코팅 pull-off·replica feature 정량화

기준일은 2026년 10월 28일이다. 이 배치는 기존의 증거 조정 모델을 대체하지 않고, 원 측정과 기하
관례가 충분할 때만 실행되는 세 개의 좁은 정량 경로를 추가했다. 규격표나 PDF 문장을 포함하지 않으며
합격, 잔여수명 또는 고장확률을 자동으로 생성하지 않는다.

## 성형 형상 이력

`fabrication.forming_geometry_history`는 원두께·최종두께, 내측반경, 굽힘각, 열간/냉간, 방향,
재료조건, 시편·source·불확도·digest를 보존한다. 지원되는
`mid_thickness_neutral_axis_circular_arc` 관례를 호출자가 명시한 경우에만 표면변형률과 thinning을
계산한다. Engineering과 true strain은 하나만 선택하며 자동 변환하거나 혼합하지 않는다. Caller가
제공한 최대 변형률·thinning threshold는 `threshold - calculated` signed margin으로만 반환한다.
내장 forming limit, PWHT 요구, 재료열화 또는 판정은 없다.

## Pull-off adhesion 보정

`fabrication.pull_off_adhesion_calibration`은 dolly, 위치, 층, substrate, surface preparation, cure,
exposure, adhesive, calibration, provider revision과 configuration/input/result digest를 보존한다. Force가
N, area가 m²로 완전할 때만 force/area stress와 1차 불확도 전파를 계산한다. Provider stress는 별도
관측으로 유지하고, paired calibration에서 provider-minus-force/area bias와 repeatability를 적합한 뒤
지원범위 안의 독립 holdout만 비교한다. 파단형태 component fraction은 호출자 분류를 그대로 보존하며
cohesive/adhesive 우열을 자동 해석하지 않는다.

공개 보조자료 `10.5281/zenodo.4777893`은 CC BY 4.0이다. README와 adhesion workbook만 선별 취득해
35개 그룹·107개 raw replicate를 감사한다. Formula mean/std는 관측으로 세지 않는다. 원본에 adhesion
unit, dolly area/force, break mode, calibration과 불확도가 없고 substrate가 wood이므로 값은
`provider_native_unresolved`로 남긴다. 이 자료는 reader 구조 검증용이지 금속 공정설비 코팅의 보정·
자격화 자료가 아니다.

```bash
python scripts/inspect_coating_adhesion_data.py
```

## Replica feature geometry

`inspection.replica_feature_density_summary`는 physical location, material condition, service temperature/
clock, replica·field·frame identity와 pixel 또는 SI calibration을 보존한다. Segmentation provider,
observer review, feature type, centroid, bounding box, area, uncertainty, overlap, edge handling, validity와
digest를 그대로 기록한다. 출력은 field area, reviewed count와 density, segmented area fraction,
nearest-neighbor spacing 같은 순수 기하 요약이다. 중복 feature/digest, 비대칭 overlap, bounds 이탈,
미검토 edge와 missing/invalid record는 계산을 중지한다. Feature를 creep cavity로 재분류하거나 손상등급,
creep life, 합격 또는 확률로 바꾸지 않는다.

## 검증·병렬 실행

신규 모델 3개의 엄격 JSON 예제는 모두 `computed`다. 공개 reader를 포함한 집중 테스트 17건과 변경
Ruff 검사를 통과했다. 전체 회귀·생성물 재현은 `hpc/task_manifest.json`의 51개 작업과
`hpc/slurm_array.sh` 배열 `0-50`으로 누리온에서 수행한다. 현재 결과는 소프트웨어와 데이터 구조
검증이며 독립 물리·현장 자격화가 아니다.
