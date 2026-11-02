# 습윤 CO₂ 기상측 물질전달 계수

## 역할

`degradation.wet_co2_gas_side_mass_transfer`는 caller가 검토한 기상 유속·벽면전단응력·기체 물성으로 기상측 농도기준 전달계수 `k_g,c`를 산정하고, 이어서 fugacity 기준의 `k_g`로 변환한다. 이전 액상측 모듈은 액체막 계수를 제공하고, [`wet_co2_two_film_transfer`](WET_CO2_TWO_FILM_TRANSFER_KO.md)는 두 막 계수와 Henry 상태를 사용하므로 이 결과를 그 API의 gas-film 입력으로 연결할 수 있다.

Paolinelli와 Nesic의 [기–액 배관 질량전달 연구(2021)](https://doi.org/10.1016/j.ijheatmasstransfer.2020.120689)는 기상–액상 유동의 전달계수 산정에 기계론적 유동 상태 및 Chilton–Colburn 유사 관계를 이용하는 접근을 다룬다. 본 모듈은 한 가지 caller-selected 난류 유사식을 코드로 독립 구현한 범위 제한형 계수 추정기이며, 해당 연구의 전체 near-wall 또는 다상 유동 모델을 재현하지 않는다. 문헌 문장·그림·실험 측정값은 포함하지 않는다.

## 사용 관계식

```text
Re_g = ρ_g u_g D_h / μ_g
Sc_g = μ_g / (ρ_g D_CO2,g)
f_F = 2 τ_w / (ρ_g u_g²)
k_g,c = u_g (f_F/2)^n Sc_g^(−2/3)
k_g,f = k_g,c · (∂C_g/∂f_CO2)
```

`n`은 요청에서 명시하는 마찰–전달 지수이며 기본 상수를 숨겨 두지 않는다. `∂C_g/∂f_CO2`는 온도·압력·혼합물에 맞춰 caller의 EOS/property provider가 제공하는 국소 감도다. 이상기체를 채택할 경우의 `1/(RT)`도 caller가 계산해 출처와 함께 입력할 수 있다. 계산은 이를 EOS에서 추정하지 않는다. 압력기준 출력 `k_g,f`의 단위는 `mol/(m²·s·Pa)`다.

## 적용 가정 및 제한

- 기상 평균속도, 전단응력, 밀도, 점도, CO₂ 분자확산계수와 유압직경은 정확히 같은 조건·위치·시간 기준이어야 한다.
- 이 관계식은 난류 기상측 계수의 integral estimate로 제한한다. 전이/층류와 별도 검토되지 않은 유동 영역에는 적용하지 않는다. 구현의 Reynolds 하한 4000은 모델 사용 경계로 선택된 gate이지, 보편적인 기–액 전이 기준이나 출판 검증범위를 뜻하지 않는다.
- `two_phase_gas_core`는 외부 다상 유동 provider가 가스 코어의 상태와 계면 인근 전단을 실제로 제공하고 caller가 비교 가능성을 검토한 경우에만 사용할 수 있다.
- 면적, 젖음, 액상측 저항, 계면 반응, Henry 평형, 화학종 전환과 부식률은 계산하지 않는다.
- 입력 provider, diffusivity record 및 result/configuration digest가 있어야 하며, digest와 review flag는 물성 정확성을 자동 인증하지 않는다.

## 공개 범위와 검증

코드와 설명은 독립 작성했다. 출판 논문의 본문, 수치 자료, 상관표를 복사하지 않는다. 이 API는 구현 상태이며 수치·실험 검증이 완료되기 전 설계 계산 또는 안전판정에 단독 사용하지 않는다.
