# 용접 수소 bakeout 유한 평판 스크리닝

`welding.hydrogen_bakeout_slab`은 사용자가 검토한 두께와 유효 확산계수 이력으로, 양면이 방출 경계인 유한 평판의 평균 확산성 수소 잔류분율을 계산한다. 공개 규격의 온도·시간 표나 합격기준은 포함하지 않는다.

```python
from matintegrity import evaluate
from matintegrity.contracts import RunContext

result = evaluate(
    "welding.hydrogen_bakeout_slab",
    {
        "procedure_id": "procedure-revision-1",
        "material_condition_id": "weld-condition-1",
        "diffusivity_source_id": "reviewed-effective-diffusivity",
        "thickness_source_id": "reviewed-release-path",
        "elapsed_time_s": [0.0, 1800.0, 3600.0],
        "temperature_K": [423.15, 473.15, 473.15],
        "effective_diffusivity_m2_s": [2e-9, 8e-9, 8e-9],
        "slab_thickness_m": 0.012,
        "initial_diffusible_hydrogen_atoms_mol_m3": 50.0,
        "both_faces_exposed_reviewed": True,
        "uniform_initial_concentration_reviewed": True,
        "diffusion_limited_surface_reviewed": True,
        "diffusivity_history_reviewed": True,
        "temperature_history_reviewed": True,
    },
    RunContext(asset_id="joint-1", location_id="weld", time_basis="bakeout-clock"),
)
```

모델은 공간적으로 균일하고 시간에 따라 변하는 확산계수에 대해 `∫D(t)dt`를 확산시간으로 사용한다. 입력 knot 사이의 `D(t)`는 선형으로 선언되어 사다리꼴 적분이 정확하다. 초기 농도가 균일하고 두 표면 농도가 0인 평판의 odd eigenfunction 급수를 계산하며, 다음 항부터의 양의 tail 상한이 사용자 절대오차 허용값보다 작을 때만 결과를 반환한다. 시간 0은 정확히 잔류분율 1로 둔다.

결과에는 누적 확산시간, Fourier 수, 잔류·방출 분율, 평균 농도, 면적당 누적 방출량, 급수 tail 상한과 사용 항 수가 포함된다. 온도는 절차 증거로 보존할 뿐 숨은 확산계수를 생성하지 않는다. Arrhenius나 실험 적합으로 얻은 유효 확산계수를 사용하려면 재료상태·온도범위·측정법·trap 포함 의미를 사용자가 별도로 검토해야 한다.

이 축약모델은 trap을 직접 풀지 않고, weld metal/HAZ/base metal의 공간 이질성, 상변태, 응력구배, 유한 표면 재결합, 단면 모서리, 다차원 방출과 수소균열 기준을 포함하지 않는다. 양면 노출·균일 초기상태·확산 지배 표면·입력 이력을 모두 승인하지 않으면 `needs_data`다. 급수 예산 안에서 수치오차 상한을 만족하지 못하면 `out_of_scope`다.

수학적 기준은 NIST가 제시한 양면 진공 유한 평판의 Fick 확산 및 특성시간 설명을 서지 근거로 사용했으며 문장·표·재료계수는 복제하지 않았다. 구현식과 tail bound는 프로젝트에서 독립 작성했다. 재현 검증은 `scripts/validate_hydrogen_bakeout.py`, 결과는 `validation/hydrogen_bakeout_math.json`, 공개 입력 Schema는 `docs/schemas/HydrogenBakeoutSlab.json`이다.

