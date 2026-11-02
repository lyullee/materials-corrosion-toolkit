# 공간별 구간 반응 source callback

`matintegrity.spatial_piecewise_reaction`은 `RestrictedTransport`의 반응 callback 자리에 연결할 수 있는 caller 지정 균질 mass-action source를 제공합니다. 종·정수 화학량론·전하와 선택적 원소 조성, 농도 기반 속도상수, 사용 근거를 입력으로 받습니다. 반응별 정·역 속도상수는 모든 시간 구간에 대해 명시해야 하며 구간은 틈이나 겹침 없이 이어져야 합니다. 각 구간은 왼쪽을 포함하고 오른쪽은 다음 구간에 귀속하며, 전체 끝점만 포함합니다. 선언된 시간 범위 밖에서는 외삽하지 않고 오류를 냅니다.

속도상수 단위는 해당 반응 방향의 농도 차수에 맞춰 `1/s` 또는 `(mol/m3)^(1-order)/s`로 고정합니다. caller는 calibration record ID·SHA-256과 이를 일치시키는 Evidence를 제공해야 합니다. 이용 라이선스와 rights Evidence, 계산 이용 허가, 로컬 전용 처리 허가도 계약 입력입니다. 전하 보존은 항상 확인하고, 원소 조성을 제공하면 지정 원소 보존도 검사합니다.

농도 또는 농도에 활동도 계수를 곱한 유효농도를 쓰는 근사 가정은 caller가 검토해야 합니다. 활동도 계수 callback은 선택 사항이며 사용하는 경우 provider ID·revision·configuration SHA-256 세 값이 계약과 callback 속성에서 일치해야 합니다. 이 확장은 반응속도나 활동도, 평형상수, 부식률을 추정하지 않습니다. 열역학적 평형, 표준상태 변환, 표면 반응은 범위 밖입니다.

```python
callback = build_spatial_reaction_callback(network)
transport_request = RestrictedTransportRequest(
    ...,
    reaction_provider_id=callback.provider_id,
    reaction_configuration_sha256=callback.configuration_sha256,
)
result = solve_restricted_transport(transport_request, callback)
```

요청 객체와 합성 구성 예시는 `examples/spatial_piecewise_reaction_synthetic.py`를 참고하세요. 이 예제는 실행하지 않았습니다.
