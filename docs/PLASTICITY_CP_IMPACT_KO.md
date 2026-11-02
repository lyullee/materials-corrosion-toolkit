# 단조 소성곡선·음극방식 조사·계장화 충격 신호

기준일은 2026년 10월 28일이다. 이 배치는 세 개의 독립 계산 경로와 한 개의 공개 데이터 감사
경로를 추가했다. 계산 결과는 입력 근거를 요약하거나 보정할 뿐 규격 합격, 잔여수명 또는 고장확률을
자동으로 만들지 않는다.

## 단조 Hollomon 보정

`materials.monotonic_hollomon_calibration`은 검토된 pre-necking 단조점에서
`plastic strain = total strain - stress / elastic modulus`를 계산하고, 사용자가 선언한 true 또는
engineering 관례를 바꾸지 않은 채 `log(stress) = log(K) + n log(plastic strain)`을 가중 적합한다.
Calibration과 holdout의 물리 시편·source group·independence group을 분리하며, holdout 오차는
calibration 소성변형률 범위 안에서만 계산한다. Necking 이후 외삽, true/engineering 자동 변환,
순환 재료상수, 피로수명 또는 판정값은 출력하지 않는다.

## 음극방식 현장조사

`fabrication.cathodic_protection_field_survey`는 native, on, off, instant-off 전위 관례를 분리한다.
Reference electrode와 calibration 온도범위·offset·불확도, IR-drop 처리상태, rectifier/anode current의
부호 기준, electrolyte·environment·provider revision·digest를 보존한다. 사용자가 자신의 권한으로
threshold를 넣을 수 있지만 결과는 선언한 방향의 signed margin일 뿐 compliance 판정이 아니다.

공개 자료 `10.5281/zenodo.18735817`은 CC BY 4.0 메타데이터를 확인한 뒤 관련 파일 6개만 선별
취득했다. `cathodic_protection_data.py`는 5개 DPlot CSV의 8개 곡선·11,922표본을 provider digest로
고정하고 구조를 검사한다. OCP는 seconds와 volts versus calomel로 보존한다. 분극 CSV의 current-axis
지수 표기가 모호하므로 단위를 추정하지 않는다. Workbook은 원본 증거지만 중복 plot sheet와 시험
배치를 일반화하지 않았다. 노출용액, 온도, 정확한 reference electrode subtype, 면적 정규화와 불확도
근거가 완전하지 않아 현장조사 입력으로 자동 변환하거나 부식전류·부식률을 적합하지 않는다.

```bash
python scripts/inspect_cathodic_protection_data.py
```

## 계장화 충격 신호

`inspection.instrumented_impact_signal_summary`는 specimen/notch/orientation/material condition,
시험온도, striker와 force/displacement/timebase calibration, 원 신호 digest를 명시한다. 엄격 증가
시간과 비감소 변위를 요구하고, 선택한 valid window 안에서 명시적 force-direction multiplier를 적용해
trapezoidal work를 구한다. Peak plateau의 첫·마지막 sample/time/displacement를 보존하며, 별도 데이터
경로라고 선언한 machine energy가 있으면 signed difference와 불확도만 비교한다. Crack initiation,
transition temperature, fracture toughness 변환, 합격 또는 확률은 계산하지 않는다.

## 검증과 재현

신규 계산기 3개의 엄격 JSON 예제는 모두 `computed`이고, 데이터 reader를 포함한 집중 테스트 17건과
변경 Ruff 검사를 통과했다. 실제 파일 감사 결과는 `validation/cathodic_protection_data_audit.json`에
저장된다. 전체 회귀·배포 재생성은 `hpc/task_manifest.json`의 50개 작업과
`hpc/slurm_array.sh` 배열 `0-49`로 누리온에서 수행한다. 이 검사는 소프트웨어 동작과 자료 구조를
확인한 것이며 물리시험 자격화가 아니다.
