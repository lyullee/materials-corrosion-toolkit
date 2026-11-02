# Ti-12Mo-5Zr AESEC signed mass-balance 변환

## 목적과 허용 범위

이 API는 Zenodo 공개 Ti-12Mo-5Zr AESEC 원소별 areal dissolution-rate 행을 소비해, caller가 승인한 밀도를 사용하여 부호 있는 등가 평균 침투 속도와 제공 시간축에서의 적분 침투량을 계산합니다. 결과는 균일 재료가 동일 면적에 같은 속도로 줄었다고 놓은 평균 두께 환산입니다. 위치별 손상, 최대 pit depth, 벽두께 국부 손실, 수명, 적격성, 위험 확률을 뜻하지 않습니다.

데이터 제공자의 열 단위는 `ng·s^-1·cm^-2`입니다. SI areal mass flux 변환은 다음과 같습니다.

```text
1 ng·s^-1·cm^-2 = 1e-8 kg·m^-2·s^-1
v_signed(t) = sum_i(j_i(t) × 1e-8) / rho_caller
```

여기서 `rho_caller`의 단위는 `kg·m^-3`이고, `v_signed`는 `m·s^-1`입니다. 시간 행 사이에는 caller가 검토·승인한 선형 보간을 사용하고 trapezoid 적분으로 부호 net 두께와 양/음 별 누적량을 분리합니다. 양의 부호가 outward material loss라는 해석 역시 caller가 별도 승인해야 합니다.

Faraday 법칙, 전하량, 산화수, 전자 수, 몰질량 또는 외부 전류는 사용하지 않습니다. 분석원소 전체가 Ti/Mo/Zr 행에 포함된다는 점도 보편적 사실로 가정하지 않습니다. caller는 해당 계산 목적에 대해 이 세 분석 성분의 완전성을 명시적으로 승인합니다.

## 입력 검토 항목

`Ti12Mo5ZrMassBalanceRequest`는 다음 항목을 모두 제공해야 합니다.

- `density_kg_m3`와 밀도를 뒷받침하는 `Evidence` (출처·인용·원하는 경우 SHA-256 포함)
- `analyzed_elements=("Ti", "Mo", "Zr")`의 명시적 순서 및 이 conversion 대상에 대한 완전 coverage 승인
- source sign 검토: 양의 제공자 용출률을 바깥쪽 손실로 해석
- provider time [s]를 구간 적분 좌표로 사용하는 검토
- 면적 평균 질량 플럭스를 균일 등가 침투로 취급하는 검토
- 관측점 사이 선형 보간 검토
- 명시적 계산 사용 및 로컬 전용 처리 승인

승인 값이 없거나 source member/헤더가 달라지면 fail-closed 합니다. 시간은 음수가 없고 strict 증가해야 합니다. 누락, 비수치, 비유한 값, source row 누락/재배열, SHA 불일치는 보정 없이 실패합니다. 외삽은 하지 않으며 누적 적분은 실제 첫/마지막 source time 사이에만 정의됩니다.

## 산출과 provenance

각 time row의 `signed_net_mass_flux_kg_m2_s`, `signed_equivalent_penetration_velocity_m_s`, 양의 누적 침투량, 음의 누적 침투량 및 부호 net 누적량을 보존합니다. 결과는 양수·음수 방향 각각의 signed 부호가 유지되므로 음수 적분량을 임의로 양의 재료손실로 바꾸지 않습니다.

`Ti12Mo5ZrMassBalanceResult`에는 input request digest, canonicalized full raw row stream digest, per-row digest, provider archive/member SHA-256 및 밀도 Evidence digest를 담습니다. 데이터 point 결과는 계산 시 메모리에서만 생성하며 저장소 raw cache나 추적 문서에 쓰지 않습니다.

## 모듈과 ModelSpec

- Python API: `matintegrity.ti12mo5zr_mass_balance.calculate_mass_balance`
- API wrapper: `evaluate_mass_balance`, 반환형 `Calculation`
- ModelSpec ID: `corrosion.ti12mo5zr_aesec_signed_equivalent_penetration`
- schema IDs: `matintegrity.ti12mo5zr_mass_balance_request.v1`, `matintegrity.ti12mo5zr_penetration_point.v1`, `matintegrity.ti12mo5zr_mass_balance_result.v1`
- source ID: `zenodo-ti12mo5zr-aqueous-corrosion`

## 합성 단위 예시 (실행되지 않음)

세 원소의 합성 rate가 각각 1, 2, 3 `ng·s^-1·cm^-2`, 합성 밀도가 `6000 kg·m^-3`라고 가정하면, 합계 플럭스는 `6e-8 kg·m^-2·s^-1`, 등가 속도는 `1e-11 m·s^-1`입니다. 이 일정한 합성 속도를 10초 유지하면 두께 증분은 `1e-10 m`입니다. 이는 단위 설명만을 위한 수치이고 제공자 측정값이 아닙니다.

실행하지 않은 local API 호출 예제는 `examples/ti12mo5zr_mass_balance_local.py`입니다. 테스트, 실제 자료 계산, 피팅 또는 결과 배포는 수행하지 않았습니다.

