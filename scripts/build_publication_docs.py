"""Build visible module directories from the executable public API, not guessed names.

Input contracts and declared output units are extracted from ModelRegistry.
Observed examples and mathematical checks remain distinct from full validation.
"""

import inspect
import json
from collections import defaultdict
from pathlib import Path

from matintegrity.registry import default_registry

ROOT = Path(__file__).resolve().parents[1]
REPO = "https://github.com/lyullee/materials-corrosion-toolkit"
VERSION = "0.1.0a1"
DOMAIN = {
    "adapter": "다른 시스템으로 결과 전달",
    "calibration": "재료·수송·관측 계수 보정",
    "chemistry": "수용액·활동도·평형·고체 반응",
    "corrosion": "부식속도·전류·손실·틈 부식",
    "creep": "크리프 속도·파단·누적손상",
    "data": "허용된 외부 자료 구조 확인·읽기",
    "degradation": "열화·침식·산화·마모·환경 영향",
    "design": "설계 입력·사용자 기준 적용",
    "electrochemistry": "전위·편극·전극반응",
    "fabrication": "가공·볼트·가스켓·제작 품질",
    "fatigue": "피로·다축 경로·소성·수명",
    "fracture": "균열·응력확대계수·파괴역학",
    "geometry": "형상·손실 프로파일·공간 자료",
    "inspection": "검사·영상·관측·품질·절차",
    "integration": "여러 계산 단계의 증거 기반 연결",
    "kinetics": "반응속도·온도 이동",
    "maintenance": "유지관리·이력·사용자 지표",
    "materials": "재료 구성식·조성·시험 해석",
    "mechanics": "압력응력·열응력·접촉·탄성",
    "piping": "배관 조건·사용자 기준",
    "probability": "명시된 의미의 확률 계산",
    "reliability": "신뢰도·위험도 계산",
    "structural": "두께·압력 용량·FAD·구조 평가",
    "testing": "재료시험·통계·시험 지표",
    "thermal": "열전도·열이력·열처리",
    "thermo": "열역학 상태·퓨가시티",
    "transport": "확산·이온·성분 수송",
    "validation": "증거 정렬·비교·검증 지표",
    "welding": "용접 열·수소·야금·절차",
    "workflow": "사용자 기준과 평가 절차",
}


def esc(value):
    return str(value).replace("|", "\\|").replace("\n", " ")


def names(values, limit=None):
    values = list(values)
    shown = values if limit is None else values[:limit]
    text = ", ".join(f"`{esc(v)}`" for v in shown) or "—"
    if limit is not None and len(values) > limit:
        text += f" **외 {len(values) - limit}개**"
    return text


def unit(name):
    # Only unambiguous SI suffixes are expanded; unknown bases stay explicit.
    suffixes = {
        "_Pa_sqrt_m": "Pa·√m",
        "_W_m2_K": "W/(m²·K)",
        "_W_m_K": "W/(m·K)",
        "_J_kg_K": "J/(kg·K)",
        "_J_mol_K": "J/(mol·K)",
        "_mol_m2_s": "mol/(m²·s)",
        "_mol_m3_s": "mol/(m³·s)",
        "_kg_m2_s": "kg/(m²·s)",
        "_kg_mol": "kg/mol",
        "_m3_mol": "m³/mol",
        "_Pa_s": "Pa·s",
        "_N_m": "N·m",
        "_W_m2": "W/m²",
        "_J_m3": "J/m³",
        "_m_per_s": "m/s",
        "_per_s": "1/s",
        "_per_K": "1/K",
        "_m_s": "m/s",
        "_kg_m3": "kg/m³",
        "_mol_m3": "mol/m³",
        "_mol_kg": "mol/kg",
        "_A_m2": "A/m²",
        "_ohm_m2": "Ω·m²",
        "_m2_s": "m²/s",
        "_m3_s": "m³/s",
        "_J_mol": "J/mol",
        "_Pa": "Pa",
        "_MPa": "MPa",
        "_K": "K",
        "_m": "m",
        "_s": "s",
        "_kg": "kg",
        "_N": "N",
        "_V": "V",
    }
    for suffix, value in suffixes.items():
        if name.endswith(suffix):
            prefix = name[: -len(suffix)].split("_")[-1]
            if prefix not in {"per", "sqrt", "Pa", "m", "m2", "m3", "kg", "mol", "K", "J", "W", "N", "s"}:
                return value
    return "계약·필드 설명 참조"


def main():
    registry = default_registry()
    sources = {
        row["id"]: row
        for row in json.loads((ROOT / "data/catalogs/sources.json").read_text(encoding="utf8"))["sources"]
    }
    examples = json.loads((ROOT / "examples/model_inputs.json").read_text(encoding="utf8"))["models"]
    schema_index = json.loads((ROOT / "docs/schemas/schema_index.json").read_text(encoding="utf8"))["models"]
    groups = json.loads((ROOT / "tests/data/core_physics_full_run_targets.json").read_text(encoding="utf8"))[
        "groups"
    ]
    handoffs = json.loads(
        (ROOT / "tests/data/core_physics_rule_handoff_cases.json").read_text(encoding="utf8")
    )["cases"]
    representative = {r["group"]: r["model_id"] for r in handoffs}
    folder = ROOT / "docs/modules/api"
    folder.mkdir(parents=True, exist_ok=True)
    domains = defaultdict(list)
    records = []
    for identifier in registry.list_models():
        spec = registry._models[identifier]
        desc = registry.describe(identifier)
        schema = desc["input_schema"]
        purpose = " ".join(spec.assumptions).split(". ")[0].rstrip(".") + "."
        props = schema.get("properties", {})
        required = schema.get("required", [])
        inputs = [k for k in props if k not in {"schema_version"}]
        record = dict(
            id=identifier,
            domain=identifier.split(".")[0],
            purpose=purpose,
            input_parameters=inputs,
            required_parameters=required,
            declared_output_units=spec.units,
            qualification=spec.qualification,
            runtime_dependencies=list(spec.runtime_dependency_names),
            schema="docs/schemas/" + schema_index[identifier]["filename"],
            documentation=f"docs/modules/api/{identifier}.md",
            has_main_json_example=identifier in examples,
            model_version=spec.version,
            source_ids=list(spec.source_ids),
        )
        records.append(record)
        domains[record["domain"]].append(record)
        lines = [
            f"# `{identifier}`",
            "",
            f"**목적:** {purpose}",
            "",
            f"**모델 버전:** `{spec.version}` · **구현 분류:** `{spec.qualification}` · **배포 버전:** `{VERSION}`",
            "",
            "[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)",
            "",
            "## 입력 파라미터",
            "",
            "각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.",
            "",
            "| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |",
            "|---|---|---|---|",
        ]
        for key, value in props.items():
            constraints = {k: v for k, v in value.items() if k not in {"title", "description"}}
            lines.append(
                f"| `{key}` | {'예' if key in required else '아니오'} | `{esc(json.dumps(constraints, ensure_ascii=False))}` | {esc(value.get('description') or unit(key))} |"
            )
        lines += [
            "",
            f"[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/{schema_index[identifier]['filename']})",
            "",
            "## 출력 파라미터",
            "",
            "공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.",
            "",
            "| `values` 내 선언 경로 | 단위 |",
            "|---|---|",
        ]
        lines += [f"| `{esc(k)}` | `{esc(v)}` |" for k, v in spec.units.items()] or [
            "| 가변 구조·진단·증거 결과 | 구현·예제의 `values` 확인 |"
        ]
        lines += [
            "",
            "공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.",
            "",
            "## 모델 가정·주의 사항",
            "",
        ]
        lines += [f"- {a}" for a in spec.assumptions]
        lines += ["", "## 구현 근거·독립 설명", ""]
        for source_id in spec.source_ids:
            source = sources.get(source_id, {})
            title = source.get("title", source_id)
            if source.get("url", "").startswith("https://"):
                lines.append(f"- [{title}]({source['url']}) · `{source_id}`")
            else:
                lines.append(
                    f"- `{source_id}`: {source.get('derivation', source.get('basis', '출처 카탈로그의 해당 항목 참조'))}"
                )
        if spec.probability_semantics:
            lines += [
                "",
                "확률 의미: `"
                + json.dumps(spec.probability_semantics, ensure_ascii=False)
                + "`. 손상량을 확률로 재명명하지 않는다.",
            ]
        lines += [
            "",
            "## 실행 방법",
            "",
            "```python",
            "import json",
            "from matintegrity.registry import default_registry",
            "from matintegrity.contracts import RunContext",
            "",
            "registry = default_registry()",
            f'model_id = "{identifier}"',
            "# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.",
            'payload = open("inputs.json", encoding="utf-8").read()',
            'context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")',
        ]
        if spec.runtime_dependency_names:
            lines += [
                "# 아래 이름의 실제 Python provider를 준비한 뒤 runtime_dependencies로 전달한다.",
                "# JSON만으로 외부 callable을 직렬화하거나 실행하지 않는다.",
                "providers = {" + ", ".join(repr(k) + ": ..." for k in spec.runtime_dependency_names) + "}",
                "result = registry.run_json(model_id, payload, context, runtime_dependencies=providers)",
            ]
        else:
            lines += ["result = registry.run_json(model_id, payload, context)"]
        lines += [
            "print(result.status)",
            "print(result.values)",
            "```",
            "",
            "위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.",
        ]
        if identifier in examples:
            lines += [
                "",
                f'주 JSON 예제 키: `examples/model_inputs.json` → `models["{identifier}"]`. 합성값이며 물성·허용값·실측값이 아니다.',
                "",
                "```json",
                json.dumps(examples[identifier], ensure_ascii=False, indent=2),
                "```",
            ]
        else:
            lines += [
                "",
                "주 JSON 예제 파일에는 이 API의 독립 예제가 없다. 연결 API는 선행 계산의 실제 `AssessmentResult`가 필요할 수 있고 데이터 API는 별도로 확보한 파일·권한이 필요하다. 단위·계약·증거를 임의로 채워 실행 성공을 만들지 않는다.",
            ]
        path = inspect.getsourcefile(spec.evaluator)
        if path:
            try:
                rel = Path(path).resolve().relative_to(ROOT).as_posix()
                number = inspect.getsourcelines(spec.evaluator)[1]
                lines += ["", f"[계산 구현과 주석 확인](../../../{rel}#L{number})"]
            except (OSError, ValueError, TypeError):
                pass
        lines += [
            "",
            "## 검증과 연구 재개",
            "",
            "등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.",
            "",
            "해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.",
        ]
        (folder / f"{identifier}.md").write_text("\n".join(lines) + "\n", encoding="utf8")
    from publication_readme_en import build_readme

    readme = build_readme(records, groups, representative, VERSION)
    (ROOT / "README.md").write_text(readme, encoding="utf8")
    directory = [
        "# 전체 단위 모듈 설명서",
        "",
        "각 링크에는 목적, 모든 최상위 입력, 필수 여부, 기본값·제약, 전체 중첩 스키마, 선언 출력 단위, 호출 방법, 적용 한계, 구현 위치와 예제 보유 여부가 있다.",
        "",
        "[README의 요약표](../README.md) · [기계 판독 API 목록](API_DIRECTORY.json)",
        "",
    ]
    for domain, items in sorted(domains.items()):
        directory += [f"## {domain}: {DOMAIN.get(domain, domain)}", "", "| API | 목적 |", "|---|---|"]
        directory += [f"| [`{r['id']}`](modules/api/{r['id']}.md) | {esc(r['purpose'])} |" for r in items]
        directory.append("")
    (ROOT / "docs/MODULE_DIRECTORY_KO.md").write_text("\n".join(directory) + "\n", encoding="utf8")
    (ROOT / "docs/API_DIRECTORY.json").write_text(
        json.dumps(
            dict(
                schema_version="materials-corrosion-toolkit.api-directory.v1", version=VERSION, models=records
            ),
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf8",
    )
    print(
        f"README {len(readme.encode('utf8'))} bytes; {len(records)} model pages; {len(domains)} domains; 63 physics groups"
    )


if __name__ == "__main__":
    main()
