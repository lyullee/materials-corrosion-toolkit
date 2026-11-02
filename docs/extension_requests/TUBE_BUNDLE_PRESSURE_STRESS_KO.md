# 튜브 bundle 증거 모델 압력응력 확장 요청

## 목표

`fabrication.tube_bundle_integrity_evidence` 소비자가 `integration.tube_bundle_lame_stress_history`의 계산 결과를 받아 같은 asset/location/exchanger/bundle/tube/material-condition 및 clock을 확인하고, 결과 digest와 압력/형상 Evidence 계보를 보존하도록 확장한다.

## 현재 제공 계약

독립 API는 튜브별 current inner diameter/minimum wall와 exact-knot internal/external absolute pressure에서 inner/outer surface hoop, radial, axial, von Mises stress를 반환한다. 각 pressure/geometry record는 digest와 Evidence로 핀된다. 결과는 응력 descriptor이며 allowable, pressure capacity, life 또는 acceptance를 포함하지 않는다.

## 요청 사항

- evidence input에 완전한 tube stress-history request/result pair와 canonical result digest를 받는다.
- tube, material condition, asset/location, pressure reference, time basis/order 불일치는 fail closed 처리한다.
- caller-owned allowable/envelope를 추가하는 경우 독립된 revision, units, applicability evidence와 authority를 유지한다.
- Lamé 결과를 tube-bundle empirical inspection/qualification evidence로 오인하지 않고 독립된 analysis provenance로 보존한다.
- plugged/isolated tube의 pressure boundary는 외부 caller decision으로 확인한다.

## 범위 바깥

이 요청은 bundle module에서 pressure stress를 직접 다시 구현하거나 code allowable, collapse/instability, tubesheet/baffle restraint, thermal/residual stress, corrosion defect, vibration 또는 remaining life를 추론하지 않는다.

## 사용 위치

현재 독립 모듈: `src/matintegrity/tube_bundle_lame_stress_history.py`; 가이드: `docs/models/TUBE_BUNDLE_LAME_STRESS_HISTORY_KO.md`. 대상 모듈 확장은 별도 세션에서 수행한다.
