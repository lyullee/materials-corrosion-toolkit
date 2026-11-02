# 용접 절차 열입력 소비자 공분산 확장 요청

## 목표

WPS/preheat/temper-bead의 caller-owned heat-input envelope 소비자가 `welding.waveform_energy_uncertainty` 결과를 전달받을 수 있게 확장하고, nominal heat input과 표준불확도를 분리해 보존한다.

## 현재 제공 계약

독립 API는 고정된 voltage samples→current samples→efficiency→travel distance 좌표 순서의 full covariance를 trapezoidal arc-energy/net-heat-input 민감도에 1차 전파한다. 결과에는 waveform/covariance/request digest와 covariance source/revision/record/license lineage가 포함된다. Sample clock은 exact로 가정한다.

## 요청 사항

- upstream `WaveformEnergyUncertainty` request/result와 digest를 받는다.
- procedure envelope에 nominal heat input을 적용하고, 표준불확도는 별도 field로 보존한다. Caller가 별도 criterion을 제시하지 않는 한 불확도를 확률 또는 승인 margin으로 환산하지 않는다.
- welding process, calibration, consumable, thickness/position 및 procedure revision identity를 확인한다.
- covariance basis/unit, sample clock 정확 가정, first-order local approximation과 use rights review를 결과에 남긴다.

## 범위 바깥

이 확장은 전압·전류 계측의 교정/대역폭, efficiency model, timing covariance, welding code allowable, WPS qualification 또는 weld quality를 추론하지 않는다.

## 사용 위치

현재 독립 모듈: `src/matintegrity/waveform_energy_uncertainty.py`; 가이드: `docs/models/WAVEFORM_ENERGY_UNCERTAINTY_KO.md`. 대상 절차 consumer 변경은 별도 세션에서 수행한다.
