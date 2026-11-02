# lh2dt_models 동적 네트워크 상태 이력 어댑터

## 목적

`integration.lh2dt_dynamic_network_node_state_history`는 `lyullee/lh2dt_models`의 동적 네트워크 스텝 결과에서 caller가 선택한 node의 열역학 상태를 추출해 재료·부식 해석 입력에 전달할 수 있는 digest-bound 이력으로 바꾼다. upstream 코드나 데이터를 복제하지 않고 public result object에서 필요한 field만 읽는다.

## 사용 계약

- `adapt_lh2dt_dynamic_network_steps(steps, ...)`는 upstream `DynamicNetworkStepResult` 형태의 객체 iterable에서 명시된 `node_id`만 추출한다.
- `LH2DTNodeStateHistory`는 upstream repository revision, package version, run/configuration/result digest, node-to-asset mapping, material condition, clock, Evidence와 검토 상태를 보존한다.
- `evaluate_lh2dt_dynamic_network_node_state_history(request)`는 수렴과 junction conservation이 모든 지점에서 성공하고 모든 검토가 완료된 경우에만 이력을 방출한다.
- `ModelRegistry` 등록 ID는 `integration.lh2dt_dynamic_network_node_state_history`다.

주요 반환 상태는 압력(Pa), 온도(K), 밀도(kg/m³), 비내부에너지(J/kg), 내부에너지(J/kg), 비엔트로피(J/kg/K), phase/quality 및 node mass flow(kg/s)다. Time은 upstream의 seconds 축을 유지하고 adapter가 환산하지 않는다.

## 연결 예시

```python
from matintegrity.lh2dt_adapter import (
    adapt_lh2dt_dynamic_network_steps,
)
from matintegrity.registry import default_registry
from matintegrity.contracts import Evidence, RunContext

# `steps`는 사용자 환경에 설치된 lh2dt_models에서 생성된 결과 목록이다.
history = adapt_lh2dt_dynamic_network_steps(
    steps,
    upstream_revision="0123456789abcdef0123456789abcdef01234567",
    upstream_package_version="0.1.2",
    source_run_id="tank-network-run-01",
    upstream_result_sha256="a" * 64,
    upstream_configuration_sha256="b" * 64,
    node_id="tank-outlet",
    asset_id="asset-01",
    location_id="material-location-01",
    material_condition_id="material-heat-01",
    clock_id="simulation-seconds-from-start",
    evidence=(Evidence(
        source_id="lh2dt-model-run",
        origin="user_declared",
        citation="Caller-held, revision-pinned simulation receipt",
        sha256="c" * 64,
    ),),
    node_to_physical_asset_mapping_reviewed=True,
    fluid_and_material_scope_reviewed=True,
    upstream_convergence_reviewed=True,
)

assessment = default_registry().run(
    "integration.lh2dt_dynamic_network_node_state_history",
    history,
    RunContext(asset_id="asset-01", location_id="material-location-01"),
)
```

해시와 식별자는 예시 골격이다. 실제 run, repository revision, configuration과 node-to-asset 대응에 맞는 근거를 제공해야 한다.

## 가정과 제한

- upstream public result가 `time_s`, `thermo_states`, `node_mass_flow_kg_s`, `network_solution`을 제공하고 각 thermo state가 pressure/temperature/density/enthalpy/internal-energy/entropy/quality/phase를 노출한다고 가정한다. 다른 upstream 버전은 caller가 adapter 전단에서 변환하고 그 변환 코드와 출력 digest를 고정해야 한다.
- node 이름은 물리 설비나 노출 위치를 뜻하지 않는다. 위치 대응은 caller가 명시적으로 검토한다.
- 결과는 bulk-fluid 상태뿐이다. 표면 온도, 국부 유속·전단, 수소 용해도/퓨가시티, 물 조성, 산소, pH, 재료 열화율·수명·합격 여부는 추론하지 않는다.
- upstream 수렴/보존 상태가 하나라도 실패하면 전체 exposure history를 `needs_data`로 보류한다.
- 외부 package는 optional runtime dependency이며, adapter는 `lh2dt`를 import하지 않는다. 원본 모델 구현을 복사하거나 외부 저장소에 변경을 가하지 않는다.

## upstream 근거와 라이선스 구분

공개 upstream project 문서와 package metadata는 [lh2dt_models repository](https://github.com/lyullee/lh2dt_models), [public dynamic-network result contract](https://github.com/lyullee/lh2dt_models/blob/main/src/lh2dt/dynamic_network.py), [thermodynamic state contract](https://github.com/lyullee/lh2dt_models/blob/main/src/lh2dt/properties.py), [package metadata](https://github.com/lyullee/lh2dt_models/blob/main/pyproject.toml)에서 확인할 수 있다. upstream distribution은 MIT로 선언되어 있고 CoolProp·NumPy·SciPy를 요구한다. 이 어댑터는 upstream source를 복사하지 않으며 실행 시 결과 객체를 전달받는다. 실제 적용 시 caller는 commit, version 및 결과/configuration 해시를 보존한다.

