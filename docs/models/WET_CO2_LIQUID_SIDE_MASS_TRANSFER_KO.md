# 습윤 CO₂ 배관의 액상측 물질전달계수

## 목적

`degradation.wet_co2_liquid_side_mass_transfer`는 외부 다상 유동 해석이나 사용자가 검토한 유체 상태에서 얻은 **액상 평균 속도와 벽면 전단응력**을 받아, 용해된 부식종의 액상측 평균 물질전달계수 `k_m`을 계산한다. 기상막, 기–액 계면적, Henry 계수, 수용액 반응, 부식률은 이 API의 입력·출력 범위에 포함하지 않는다.

계산은 Paolinelli와 Nesic의 2021년 기–액 배관 부식 물질전달 연구에서 비교한 Chilton–Colburn 운동량/물질전달 유사식을 독립적인 코드로 적용한다. 출판 논문은 저작권이 유지되는 자료이므로 원문, 도표, 시험 행 데이터는 코드나 문서에 복사하지 않았다. 공개 문서에는 논문 식별과 구현 출처만 남긴다. [원 논문 및 DOI](https://doi.org/10.1016/j.ijheatmasstransfer.2020.120689).

## 계산 관계

caller 입력 전단응력으로 Fanning friction factor를 만든다.

```text
f_F = 2 τ_w / (ρ u²)
Sc  = μ / (ρ D_AB)
Re  = ρ u d_h / μ
Sh  = (f_F / 2)^n Re Sc^(1/3)
k_m = Sh D_AB / d_h
```

동일한 전달계수는 다음 표현으로도 계산한다.

```text
k_m = (f_F / 2)^n u Sc^(-2/3)
```

기본 지수 `n=0.96`은 cited study가 제한된 Schmidt-number support에서 제안한 값이다. 다른 지수는 요청 파라미터로 선택할 수 있으나 그 선택과 적용 범위는 caller가 검토해야 한다.

## 입력과 연결

- `liquid_mean_velocity_m_s`, `liquid_wall_shear_stress_Pa`: 한 시간·위치·액상 영역의 hydrodynamic provider 결과. 이 API는 다상 유동장이나 전단응력을 생성하지 않는다.
- `liquid_density_kg_m3`, `liquid_dynamic_viscosity_Pa_s`, `corrosive_species_diffusivity_m2_s`: 같은 용매·온도·조성의 물성. Evidence와 자료 digest를 함께 기록한다.
- `hydraulic_diameter_m`: Reynolds·Sherwood 수의 characteristic length.
- provider ID·revision·configuration/result digest, property record ID/digest와 Evidence: 외부 입력의 추적성 자료.
- `outside_published_schmidt_range_reviewed`: 계산된 `Sc`가 문헌에서 `n=0.96`에 대해 제시한 100–1000 범위 밖일 때만 필요한 명시적 검토.

반환된 `liquid_side_mass_transfer_coefficient_m_s`는 [2막 전달 API](WET_CO2_TWO_FILM_TRANSFER_KO.md)의 `liquid_film_coefficient_m_s`에 넣을 수 있다. 두 API 사이에 자동으로 상태를 옮기거나 조건 호환성을 추정하지 않는다. 물성, 시간, 위치, 용매, 유동영역 및 면적 기준이 동일한지는 호출자가 확인해야 한다.

## 적용 경계

- 이 구현은 `Re ≥ 4000`인 난류 액상 상태만 받는다. 전이 또는 층류 유동에는 사용하지 않는다.
- 상별 평균 속도와 벽 전단은 신뢰할 수 있는 multiphase hydrodynamics 결과여야 한다. gas superficial velocity를 액상 속도로 대체할 수 없다.
- 이 식은 적분형 coefficient다. 반응이 수송 경계층 안에서 진행되거나 이온 이동·비선형 다종 반응이 지배적이면 농도 분포를 푸는 별도 반응-수송 해석이 필요하다.
- 계산값은 시험 보정값, 부식률, 물질손실, 허용성, 수명 또는 위험확률이 아니다.
- 지수 기본값과 문헌의 Schmidt 범위는 모델 적용을 보증하지 않는다. 실제 배관·유동형태·표면 젖음에 대한 별도 검토와 검증이 필요하다.

## 배포 및 검증 상태

코드와 이 문서는 독립적으로 작성했으며, 저널 논문 원문, 그림, 실험 원자료를 포함하지 않는다. 현재 추가한 API는 검토 전 구현 상태다. 수치 테스트와 독립 재현은 전체 검증 작업에서 수행할 예정이며, 아직 이 기능의 성능을 검증했다고 주장하지 않는다.
