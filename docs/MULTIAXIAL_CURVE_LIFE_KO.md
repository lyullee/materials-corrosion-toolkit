# 사용자 지정 다축 수명 곡선

## 목적과 범위

`fatigue.multiaxial_life_campaign`의 `shear_normal_strain_curve` 모드는 caller가 보유한 동일 재료상태의 보정 곡선을 유한 샘플 평면의 변형률 결합 지표에 연결한다. 특정 출판 기준식이나 재료법칙을 재현하지 않는다. 계수, 데이터의 사용권, 보간 적합성과 실제 적용성은 caller가 검토해야 한다.

각 샘플 평면에서 다음 무차원 사용자 정의 지표를 사용한다.

```text
P = shear_strain_amplitude + normal_strain_weight * normal_strain_amplitude
```

최대 `P`를 갖는 샘플 평면을 선택하고 caller 곡선의 두 인접 점 사이에서 `log(P)`와 `log(cycles_to_failure)`를 선형 보간한다. 곡선 범위 밖에서는 외삽하지 않는다. 정확히 같은 최대값을 가진 모든 샘플 평면 ID를 결과에 보존한다.

## 입력 조건

- 곡선점은 2개 이상이어야 한다.
- 곡선점은 수명 오름차순이며 지표값은 엄격한 내림차순이어야 한다.
- 수명 곡선점의 정규화 JSON 배열 digest를 `curve_sha256`에 제공한다.
- `calibration_sha256`는 전체 `ShearNormalStrainLifeCalibration` 계약 JSON digest와 일치해야 한다.
- 이력과 곡선의 `material_condition_id`가 일치해야 한다.
- 캠페인 유효 수명 범위가 곡선의 수명 범위 안에 있어야 하며 계산된 수명도 캠페인 범위 안에 있어야 한다.
- `Evidence`는 출처, 인용, 라이선스(해당 시), provider checksum(해당 시)을 명시한다. 각 curve point는 선언한 Evidence와 일치하는 `evidence_source_id`와 고유한 `source_record_id`를 제공해 행 또는 시편 추적성을 보존한다.
- 보간·지표 정의 및 권리·재료상태 검토 flag가 모두 참이어야 계산한다.

수명점 순서와 출처를 직접 맞추지 않으려면 `build_shear_normal_strain_life_calibration()`에 계약점 또는 dict, Evidence, 재료상태와 review flag를 전달한다. 함수는 곡선 검증 후 `(calibration, calibration_sha256)`를 반환한다. [합성 배선 예](../examples/shear_normal_curve_calibration.py)는 입력 구조만 보여주며 재료 데이터나 수명 예측 근거가 아니다.

## 결과와 한계

결과에는 선택 평면, 동률 평면, 확장된 factor 결과 digest, 곡선 digest와 Evidence가 포함된다. 제한된 샘플 평면 집합에 대한 계산이며 연속 방향 전체의 최적값, 임의 하중 이력의 cycle counting, 비비례 경로 법칙, 보정 곡선의 독립 검증, acceptance 판단을 추정하지 않는다. 수치 실행과 독립자료 검증은 별도의 검증 작업에서 수행한다.

## 재현성

곡선 digest는 `matintegrity.contracts.canonical_digest`로 `curve_points`를 입력 순서대로 JSON 직렬화한 값에 대해 계산한다. 외부 데이터는 공개가 허용된 경우에만 배포하고, 그 외에는 식별자·인용·license 상태 및 checksum만 기록한다. 원 자료 문장이나 그림을 코드와 문서에 복제하지 않는다.

## Kandil–Brown–Miller 경로

별도 `KandilBrownMillerLifeCalibration` 계약은 KBM 계수를 `normal_strain_range_coefficient`로 받고, 같은 재료조건의 caller 수명곡선을 요구한다. 구현은 `maximum_pairwise_chord` 방식으로 유한 샘플 변형률 이력에서 각 후보 평면의 전단 변형률 진폭을 계산한다. 최대 전단 범위와 정확히 같은 후보 평면만 남긴 뒤, 그 평면에서 다음 매개변수를 계산한다.

```text
P_KBM = shear_strain_amplitude + S_KBM * normal_strain_range
```

여기서 `normal_strain_range`는 진폭의 두 배이고, `S_KBM`은 재료·시험조건에 맞춰 caller가 보정하고 검토해야 한다. 최대 전단 범위 후보가 복수이면 그 집합 안에서 `P_KBM`이 가장 큰 평면을 수명 곡선에 연결하며, 동일한 최대값을 가진 평면 ID를 보존한다. 최대 전단면 탐색은 caller가 제공한 유한 후보 집합과 시간 표본에 한정된다. 이 기능은 임의의 이력에서 cycle counting을 하지 않고, 수명 곡선 밖으로 외삽하지 않으며, 보편 계수나 재료 자격·수락판정을 주장하지 않는다.

모델 근거는 Brown과 Miller가 최대 전단면의 전단 변형률과 그 면에 수직인 인장 변형률을 함께 고려한 원 논문, 그리고 KBM의 재료계수형 매개변수를 기술한 후속 연구다: [Brown & Miller (1973)](https://journals.sagepub.com/doi/10.1243/PIME_PROC_1973_187_069_02), [A multiaxial fatigue criterion for various metallic materials (2006)](https://www.sciencedirect.com/science/article/abs/pii/S014211230500174X). 구현은 이들 출판물의 표현이나 곡선을 복제하지 않고, 유한표본 계산과 caller 제공 계수를 명시적으로 제한한다.
