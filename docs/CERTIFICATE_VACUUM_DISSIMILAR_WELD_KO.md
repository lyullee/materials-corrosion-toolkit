# 재료 인증서·진공 pressure-rise·이종용접 evidence

## 복수 재료 인증서 대조

`materials.multi_record_certificate_reconciliation`은 한 heat·lot·material condition에 대한 caller 소유
요구조건과 복수 certificate·독립시험·보충 기록을 비교한다. Chemistry mass fraction과 SI property를
서로 다른 quantity domain으로 유지하고, alias 상태, sample/source/provider/method, 단위, 확대불확도와
coverage factor, result/record digest를 보존한다. Duplicate, missing, 불확도 구간 중첩과 서로 배타적인
모순을 평균이나 자동 수정 없이 보고한다. 규격표를 내장하거나 재료명을 추측하지 않으며, 결과는
caller 요구조건과의 기록 대조이지 코드 합격 또는 고장확률이 아니다.

## Known-volume pressure rise

`inspection.known_volume_pressure_rise`는 같은 apparatus의 독립 blank와 test 절대압력 이력을 각각
원 clock에서 불확도 가중 직선으로 적합한다. 순 throughput은 `V(dp_test/dt-dp_blank/dt)`이며 음의 값도
0으로 자르지 않는다. 기준 절대온도가 명시적으로 검토된 경우에만 mol/s 표현을 추가한다. 이 계산은
outgassing과 관통누설의 물리적 원인을 분리하거나 누설 위치·합격·FTA 확률을 만들지 않는다.

## 공개 pressure-decay 자료

Zenodo `10.5281/zenodo.20582921`의 CC BY 4.0 workbook을 provider MD5로 고정했다.
`read_pressure_decay_leak_workbook`은 다섯 gas와 100/20 mm capillary의 10개 시계열, 각 31개 표본을
seconds, kelvin, gauge Pa로 읽는다. 제공자 설명에는 reference 상태와 ambient/internal temperature가
있지만 workbook에는 reference series가 없고 각 series의 temperature 열도 하나뿐이라 역할을 구분할 수
없다. Vessel volume, 절대압력, blank/outgassing history와 불확도도 없어 known-volume 모델에 자동 연결하지 않는다.

## 이종용접 검토 evidence

`welding.dissimilar_weld_applicability_evidence`는 base material A/B, filler/deposit, buttering/overlay,
fusion-boundary region, layer sequence, WPS, PWHT와 service thermal history, environment, 선택적 dilution·
transition measurement를 identity와 digest에 결속한다. Caller compatibility review와 unresolved item을
그대로 조정하며 alloy pairing 규칙, 자동 compatibility, cracking/life, 합격 또는 확률을 생성하지 않는다.

```powershell
python scripts/inspect_pressure_decay_leak_data.py
python -m pytest -q tests/test_certificate_reconciliation.py tests/test_vacuum_pressure_rise.py tests/test_dissimilar_weld_evidence.py tests/test_pressure_decay_leak_data.py
```
