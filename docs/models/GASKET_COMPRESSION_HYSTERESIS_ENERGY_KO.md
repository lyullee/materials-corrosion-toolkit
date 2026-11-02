# 가스켓 반복 압축 이력의 루프 일과 에너지 손실 요약

## 목적과 모델 ID

`fabrication.gasket_compression_hysteresis_energy`는 caller가 제공한 반복 압축 force–displacement 원자료의 닫힌 루프를 적분하여 루프당 일, 체적 기준 에너지, 압축 입력 일, 언로딩 반환 일 및 caller 반복 수에 따른 합계를 계산합니다. 이는 가스켓의 반복 기계응답을 측정 기반으로 요약해 assembly model에서 쓸지 검토할 수 있게 하는 API입니다. 보편적 구성방정식이나 손상 법칙을 맞추지 않습니다.

## 계산 방법

각 샘플 사이의 힘–변위는 선형으로 연결합니다. 힘–변위 일은 trapezoidal rule을 사용합니다.

```text
segment_work = 0.5 * (force_i + force_(i+1)) * (displacement_(i+1) - displacement_i)
signed_loop_work = sum(segment_work)
dissipated_energy_per_cycle = abs(signed_loop_work)
energy_density = energy / (initial_thickness * loaded_area)
```

양의 segment work는 압축 입력 일로 집계하고 음의 값의 절댓값은 반환 일로 집계합니다. `hysteresis_loss_fraction_of_positive_work`는 적분된 절대 닫힌 루프 일과 총 양의 압축 일의 비입니다. 입력 반복 수는 동일 loop가 그만큼 반복된다는 caller의 가정 아래에만 에너지를 곱하는 bookkeeping에 사용합니다.

## 필요한 자료

- 재료 상태, 시편 ID, 시험 온도, 초기 두께 및 하중 면적
- 각 loop의 증가 순서 샘플 ID, 시간, 압축 변위, 압축력
- loop별 반복수와 허용 endpoint force/displacement closure 오차
- 변위 측정에서 시험기/지그 순응도를 제거했는지, 힘·면적 단위와 압축 부호, 압축 중 시험 온도 및 시편 조건을 점검한 Evidence
- 시험이 가스켓 서비스 조건을 대표하고 반복수 적용이 적합한지에 대한 caller 검토

입력 Evidence는 데이터·시편 상태·시험 조건을 같은 기록 digest로 묶어야 합니다. endpoint 오차가 caller 허용치보다 크면 해당 loop를 계산하지 않습니다.

## 적용 한계

- 출력 에너지 손실은 계측된 loop work의 기하학적 적분값입니다. 내부 마찰, 점탄성 열, 회복 가능한 저장 에너지, 지그 순응도, 안정화/ Mullins 효과의 기여를 구분하지 않습니다.
- 변형률은 caller 초기 두께로 계산된 engineering compression basis입니다. 두께 변화, 접촉면적 변화, 측면 팽창, 실제 sealing-line의 공간 압력 분포를 모델링하지 않습니다.
- sample 사이 곡선은 선형으로 재구성하며 숨은 반전점이나 시간 의존 재료응답을 추정하지 않습니다. 반복 수 합산은 고정 측정 loop가 변하지 않는다는 단순 가정만 표현합니다.
- 이 모델은 조립체의 bolt preload, flange compliance, stress field, 누설량, 피로손상, 수명, qualification 또는 acceptance를 추론하지 않습니다.

## 독립 참고자료

- A. Czerwinski et al., “Optimized design of a semimetal gasket operating in flanged bolted connections,” *Open Engineering* (2021). [DOI: 10.1515/eng-2021-0004](https://doi.org/10.1515/eng-2021-0004)
- H. Willis and A. Fatemi, “An Experimental Investigation of Compressive Behavior of a Gasket Material,” SAE Technical Paper 930119 (1993). [DOI: 10.4271/930119](https://doi.org/10.4271/930119)
- A.-M. M. R. Persson and E. Andreassen, “Cyclic Compression Testing of Three Elastomer Types—A Thermoplastic Vulcanizate Elastomer, a Liquid Silicone Rubber and Two Ethylene-Propylene-Diene Rubbers,” *Polymers* 14(7) (2022), 1316. [DOI: 10.3390/polym14071316](https://doi.org/10.3390/polym14071316) ([open article](https://pmc.ncbi.nlm.nih.gov/articles/PMC9002981/))

문헌은 가스켓 압축·반복 측정과 루프 응답의 배경을 제공할 뿐입니다. 이 구현의 입력 스키마, trapezoidal path 적분, 면적·두께 정규화, 검토 게이트 및 경계는 이 프로젝트가 독립적으로 정리했으며 문장이나 데이터를 복사하지 않았습니다.

## API와 source ID 인계

- Model ID: `fabrication.gasket_compression_hysteresis_energy`
- Schema: `matintegrity.gasket_compression_hysteresis_energy.v1`
- Evaluator: `evaluate_gasket_compression_hysteresis_energy(request)`
- Source IDs: `caller_gasket_compression_force_displacement_loops`, `caller_gasket_specimen_area_thickness_and_condition`, `piecewise_linear_force_displacement_loop_work_integral`, `closed_loop_work_as_measured_hysteresis_energy_summary`
