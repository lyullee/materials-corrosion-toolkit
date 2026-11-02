# 용접 파형 열입력의 공분산 불확도 전파

`welding.waveform_energy_uncertainty`는 기존 `WaveformEnergy` 요청으로 계산하는 아크 에너지와 순 선형 열입력에 caller가 제공한 전압·전류·효율·이동거리 공분산을 1차 전파한다. 입력 파형의 기준 계산은 `waveform_energy()`와 동일한 시간별 `V I` 사다리꼴 적분이다.

## 계산 범위

`N`개 샘플의 고정 covariance 좌표 순서는 다음과 같다.

1. `voltage_V[0]`부터 `voltage_V[N-1]`
2. `current_A[0]`부터 `current_A[N-1]`
3. `efficiency`
4. `travel_distance_m`

공분산 행렬 크기는 `(2N+2) × (2N+2)`이며 단위 토큰도 같은 순서로 `V`, `A`, `1`, `m`을 사용한다. 행렬은 유한값, 대칭, 양의 준정부호여야 한다. 파형 벡터는 기존 `WaveformEnergy` 계약을 따라 길이와 시계가 정렬되어야 하고, 이 확장 API는 전체 공분산 행렬 비용을 제한하기 위해 최대 256개 샘플을 받는다.

시간축은 정확한 값으로 취급한다. 따라서 샘플 시각의 불확도는 전파되지 않으며 caller가 이 가정을 검토해야 한다. 전압·전류 채널 보정, 열효율의 적용성, 이동거리 측정과 공분산의 추정 방법도 caller 책임이다.

## 적분과 민감도

사다리꼴 가중치 `w_i`는 양 끝 샘플에서 인접 시간 간격의 절반이고, 내부 샘플에서는 좌우 시간 차의 절반이다. 아크 에너지 `E`와 순 선형 열입력 `q`는 다음과 같다.

```text
E = Σ_i w_i V_i I_i
q = η E / L
```

여기서 `η`는 caller 제공 열효율이고 `L`은 caller 제공 이동거리다. 샘플 민감도는 다음과 같다.

```text
∂E/∂V_i = w_i I_i       ∂E/∂I_i = w_i V_i
∂q/∂V_i = (η/L) w_i I_i ∂q/∂I_i = (η/L) w_i V_i
∂q/∂η = E/L             ∂q/∂L = -ηE/L²
```

요청의 전체 공분산 행렬 `C`와 각 출력의 gradient `g`에서 분산을 `gᵀ C g`, 표준불확도를 그 제곱근으로 계산한다. 결과에는 계산값, 분산, 표준불확도, 입력·파형·공분산 digest를 기록한다. 수치상 0에 가까운 음의 분산만 0으로 제한하고, 양의 준정부호 입력에서 유의한 음의 분산이 발생하면 결과를 `out_of_scope`로 반환한다.

## 공분산 기록과 Evidence

`waveform_energy_covariance_digest()`는 공분산 source ID, provider revision, record ID, 정규화된 `WaveformEnergy` digest, 좌표 순서·단위와 전체 행렬을 하나의 canonical digest로 묶는다. `Evidence` 중 하나는 공분산의 source ID, SHA-256 및 computational-use license ID와 일치해야 한다. 공개 데이터나 외부 측정 자료를 사용할 때는 해당 공분산 자료의 이용 권리와 사용 범위를 별도로 보존한다.

API 계산을 활성화하려면 covariance 좌표·단위, clock을 정확값으로 다루는 가정, 1차 국소 선형화의 적용성 및 computational use를 caller가 검토해야 한다. 검토가 빠지면 결과는 `needs_data`다.

## 해석 한계

보고하는 값은 caller가 제시한 covariance를 국소 1차 민감도로 전달한 표준불확도다. 확률분포, 신뢰수준, 합격 판정, WPS 적격성 또는 용접 품질을 뜻하지 않는다. API는 welding-code 열효율이나 허용 열입력 한계를 공급하지 않는다. 그 기준과 측정값의 적합성은 권한이 있는 caller-owned procedure envelope API에서 별도로 평가해야 한다.
