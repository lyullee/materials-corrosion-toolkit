# 음향방출 위치추정·thermal-spray 단면·열물성 보정

기준일은 2026년 10월 28일이다. 이 배치는 세 개의 정량 경로와 통제 음향방출 공개자료 reader를
추가했다. 모든 모델은 caller/provider evidence를 계산 가능한 형태로 제한하며 규격 판정, 수명 또는
확률을 자동으로 만들지 않는다.

## Acoustic-emission arrival localization

`inspection.acoustic_emission_arrival_localization`은 하나의 3D frame에 있는 sensor 위치·channel·
calibration/coupling digest, 공통 clock, caller가 고정한 homogeneous isotropic wave speed와 support,
event arrival pick·불확도·method·trace/result digest를 받는다. Weighted nonlinear least squares로
source `(x,y,z)`와 origin time을 구하고 pick residual, weighted RMS, design rank, iteration과 caller 3D
support를 반환한다. Calibration과 holdout의 physical source/source group/independence group은 겹칠 수
없으며 known holdout source가 있을 때만 위치오차를 계산한다. Arrival pick이나 wave speed를 생성하지
않고 event mechanism, damage severity, acceptance, life, POD 또는 failure probability를 추론하지 않는다.

공개자료 `10.5281/zenodo.22011152`는 BAM의 controlled wire-cut/Schmidt-hammer AE 자료이며 CC BY 4.0이다.
상용 binary DB와 detail PDF를 제외하고 11개 text waveform, coordinate table과 event-feature text를
선별 취득했다. 각 waveform은 5 MHz, 16,384 samples로 총 180,224 amplitude samples다. Sensor 좌표는
channel 9–12 네 개지만 waveform source `C_A2`, `C_I2`는 coordinate table에 없고, coordinate source
`C_I1`은 선택 waveform이 없다. `C_A2`는 channel 10 waveform도 없다. 따라서 raw reader 결과를 새
위치추정 모델로 자동 연결하지 않는다.

```bash
python scripts/inspect_controlled_ae_data.py
```

## Thermal-spray cross-section

`fabrication.thermal_spray_cross_section_summary`는 specimen/location/layer/substrate, spray batch/process,
px-to-m field calibration, field area, thickness traverse, caller-segmented pore geometry, uncertainty, edge/
overlap, method/provider revision과 immutable digest를 보존한다. Field별 mean/min/max thickness와 area
porosity, calibration/holdout partition별 field-level repeatability만 계산한다. Duplicate·bounds·overlap·
edge·invalid 상태와 calibration field-area support를 gate한다. Image segmentation, pore classification,
bond strength, specification limit, acceptance와 service life는 산출하지 않는다.

## Transient thermal parameter calibration

`structural.thermal_gradient_parameter_calibration`은 외부 provider가 공급한 baseline temperature와 한
parameter의 sensitivity를 이용해 thermal-property multiplier 또는 thermal diffusivity 하나를 가중
선형 보정한다. Specimen/material/state, geometry/boundary, provider solver identity/digest, sensor position/
clock/calibration, uncertainty와 calibration/holdout partition을 보존한다. Fitted parameter와 holdout
time/position이 calibration support 안일 때만 bias/RMSE/residual을 계산한다. 별도 PDE solver를 복제하지
않으며 phase mechanism, thermal stress, acceptance, life 또는 probability를 추론하지 않는다.

## 검증·누리온 실행

신규 모델 세 개의 strict JSON 예제는 모두 `computed`다. 공개 reader를 포함한 집중 테스트 18건이
통과했다. 후속 배치에서는 `inspection.acoustic_emission_arrival_pick`의 명시적 threshold/AIC 원표본
선택, `fabrication.thermal_spray_thickness_uncertainty`의 반복성·측정·교정 불확도 결합과 holdout 비교,
`structural.thermal_gradient_observation_comparison`의 엄격히 정렬된 외부 solver/관측 잔차 진단을
추가했다. 후속 세 계산기의 strict JSON 예제도 모두 `computed`이고 집중 테스트 13건이 통과했다.
전체 회귀·생성물 재현은 53개 누리온 작업과 `hpc/slurm_array.sh`의 `0-52` 배열에 남겼다.
이 결과는 계산 및 자료구조 검증이며 독립 물리·현장 자격화가 아니다.

## 후속 파속·기공률·수렴 진단

`inspection.acoustic_emission_wave_speed_calibration`은 known-source emission reference와 sensor까지의
거리를 이용해 travel-time slowness와 clock offset을 가중 보정한다. Holdout은 calibration distance
support 안에서만 잔차를 계산한다. 이방성·분산을 균질 파속으로 숨기거나 미지 source를 위치추정하지
않는다.

`fabrication.thermal_spray_porosity_uncertainty`는 caller-segmented pixel area와 검토된 area calibration을
사용해 field/replicate porosity, segmentation·repeatability 결합 불확도와 독립 holdout reference 오차를
계산한다. Pixel scale이 fraction의 분자·분모에서 상쇄되는 항을 중복 계상하지 않으며 segmentation이나
pore class를 만들지 않는다.

`structural.thermal_gradient_discretization_convergence`는 외부 solver의 ordered refinement level을 동일
time/position query에서 비교한다. 인접 weighted signed/RMS/max temperature change와 유한 observed-order
진단을 기록하지만 tolerance 만족을 수렴 증명이나 error bound로 표시하지 않는다. 이 세 경로의 집중
테스트 13건과 strict JSON 예제 3개가 통과했으며 전체 회귀는 Nurion `0-53` 배열에 남겼다.
