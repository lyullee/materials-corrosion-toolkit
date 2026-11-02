"""Build visible module directories from the executable public API, not guessed names.

Input contracts and declared output units are extracted from ModelRegistry.
Observed examples and mathematical checks remain distinct from full validation.
"""

import inspect
import json
import re
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
    # The main README remains bounded; every model gets a one-click complete page.
    records_by_id = {r["id"]: r for r in records}
    intro = f"""# Materials Corrosion Toolkit · 재료·부식 건전성 평가 툴킷

재료, 부식, 전기화학, 확산, 구조 건전성, 제작·용접, 비파괴검사와 평가 결과 연결을 위한 **독립 Python 단위 모듈 모음**입니다. 각 모듈은 목적·입력 계약·단위·적용 조건·출력과 계산 근거를 드러내도록 구성했습니다. 사용자가 파라미터와 자료를 제공하고 필요한 모듈만 선택하여 호출할 수 있습니다.

**배포 이름:** `materials-corrosion-toolkit` · **Python import:** `matintegrity` · **첫 공개 버전:** `{VERSION}` · **라이선스:** MIT(코드)

> **연구용 알파 버전입니다.** 계산 실행, 수식 확인, 데이터 보정, 독립 실험 검증, 현장 적용성은 서로 다른 상태입니다. 이 툴킷은 규격 인증·자동 설계 합격·운전 안전 보증을 제공하지 않습니다. 미확인 값을 정상값으로 채우거나 결정론적 손상을 고장확률로 바꾸지 않습니다.

공개 배포 주소·파일 해시·배포 검사 기록: [공개 배포 기록](https://github.com/lyullee/materials-corrosion-toolkit/blob/main/docs/PUBLICATION_RECORD_KO.md).

## 빠른 찾기

- **아래 [63개 핵심 계산군](#핵심-물리-계산군-63개)**: 어떤 물리를 계산하며 무엇을 넣고 받는지 먼저 확인
- **아래 [전체 단위 API](#전체-단위-api-목록)**: 757개 등록 API를 목적·주요 입출력과 함께 한눈에 찾기
- **[상세 단위 모듈 설명서](docs/MODULE_DIRECTORY_KO.md)**: 모든 최상위 입력·필수값·기본값·제약·중첩 스키마·출력 단위·구현·예제
- **[처음부터 사용하는 설명서](docs/GETTING_STARTED_KO.md)** · [입력/출력 공통 계약](docs/API_KO.md)
- **[개발 과정 전체 기록](docs/DEVELOPMENT_HISTORY_KO.md)** · [검증 재현·연구 재개](docs/RESEARCH_CONTINUATION_KO.md)
- **[검증 현황과 알려진 한계](docs/RELEASE_STATUS_KO.md)** · [원자료·의존성·라이선스](THIRD_PARTY_NOTICES.md)

## 설치

```bash
python -m pip install materials-corrosion-toolkit=={VERSION}
# 과학 계산·파일 읽기·CoolProp을 함께 사용할 경우
python -m pip install "materials-corrosion-toolkit[science,thermo]=={VERSION}"
# 소스 개발 환경
git clone {REPO}.git
cd materials-corrosion-toolkit
python -m pip install -e ".[science,thermo,dev]"
```

기본 설치는 NumPy·Pydantic·Pint만 필요합니다. SciPy, CoolProp, pandas, rainflow, 파일 형식 라이브러리는 해당 기능에서 사용합니다. 별도 `ebsd` extra는 DefDAP 연동용입니다. 필요한 물성·속도상수·판정 기준을 툴킷이 임의로 만들어 주지는 않습니다.

## 바로 실행되는 작은 예제

질량 감소량을 밀도와 노출 면적으로 나누어 평균 손실 두께를 구하고, 시간을 적용해 평균 부식속도를 계산합니다. 여기의 숫자는 자체 작성한 설명용 값입니다.

```python
from matintegrity import evaluate
from matintegrity.contracts import RunContext

result = evaluate(
    "corrosion.coupon_loss",
    {{"mass_loss_kg": 0.001, "exposed_area_m2": 0.01,
     "density_kg_m3": 1000.0, "duration_s": 100.0}},
    RunContext(asset_id="example-asset", location_id="example-coupon", time_basis="elapsed seconds"),
)
assert result.status == "computed"
print(result.values["mean_penetration_m"])  # 0.0001 m
print(result.values["rate_m_s"])            # 0.000001 m/s
print(result.units)
print(result.model_dump_json())             # 입력·출력·근거·문맥·해시를 함께 보관
```

## 모듈 입력과 출력 확인

```python
from matintegrity.registry import default_registry

registry = default_registry()
print(registry.list_models())
definition = registry.describe("corrosion.coupon_loss")
print(definition["input_schema"])  # 필수 입력, 타입, 한계, 중첩 $defs
print(definition["output_units"])
print(definition["assumptions"])
```

`evaluate()`/`run()`은 Python 입력, `run_json()`은 JSON 입력을 받습니다. 엄격한 Python 계약에서는 중첩 tuple/list 구분이 적용되므로 JSON 파일·웹 API에서 받은 자료는 `run_json()`이 편리합니다. 입력 숫자를 문자열에서 자동 변환하거나 단위를 임의 추측하지 않습니다.

### 공통 결과 계약

| 필드 | 의미 |
|---|---|
| `status` | `computed`: 선언 모델 계산 완료, `needs_data`: 자료·검토·선행 결과 부족, `out_of_scope`: 적용·수치 범위 밖 |
| `inputs`, `values`, `units` | 실제 사용 입력, 계산 결과, 선언 단위 |
| `model_id`, `model_version` | 단위 API 식별자와 계산 모델 버전 |
| `context` | 설비·위치·시간 기준과 사용자가 제공한 문맥 |
| `assumptions`, `notes`, `qualification` | 가정·진단·결과 해석 범위 |
| `input_digest`, `source_ids`, `runtime` | 입력 해시·구현 근거·실행 라이브러리 정보 |
| `probability_semantics` | 확률을 반환하는 API의 명시적 확률 의미 |

`computed`가 곧 구조 안전이나 기준 적합은 아닙니다. `needs_data`와 `out_of_scope`를 후속 계산의 정상 결과로 처리하지 마세요. 초기 두께·기준 두께·균열 형상·물성·환경·하중·교정·자료 사용권한은 사용자가 근거와 함께 제공해야 합니다.

## 핵심 물리 계산군 63개

63개는 물리 기능 묶음입니다. 이 묶음의 개별 실행 감사 대상은 232개 API이며, 전체 757개 등록 API에는 자료 읽기·교환·검사 기록·워크플로도 포함됩니다. **757개의 독립 물리 솔버를 검증했다는 뜻이 아닙니다.** 아래는 군별 대표 API의 입출력입니다. 전체 입력은 해당 API 링크에서 바로 확인할 수 있습니다.

| 번호 | 계산 목적 | 대표 단위 API | 주요 입력 | 선언 출력 |
|---|---|---|---|---|
"""
    lines = [intro.rstrip()]
    for group in groups:
        r = records_by_id[representative[group["group"]]]
        lines.append(
            f"| {group['group']} | {group['name']} | [`{r['id']}`]({r['documentation']}) | {names(r['input_parameters'], 4)} | {names(r['declared_output_units'], 3)} |"
        )
    lines += [
        "",
        "## 전체 단위 API 목록",
        "",
        "아래 요약의 **외 N개**는 항목을 생략했다는 표시입니다. API 이름을 누르면 해당 단위 모듈의 모든 최상위 입력과 출력 단위가 펼쳐진 별도 문서로 이동합니다. 중첩 항목은 전체 JSON Schema로 연결됩니다. 동적으로 구성되는 `values`는 분기마다 달라질 수 있습니다.",
        "",
    ]
    for domain, items in sorted(domains.items()):
        lines += [
            f"### {domain} · {DOMAIN.get(domain, '사용자 계약·계산 기능')} ({len(items)}개)",
            "",
            "| 단위 API / 상세 설명 | 목적 | 주요 입력 | 선언 출력 |",
            "|---|---|---|---|",
        ]
        for r in items:
            purpose = r["purpose"] if len(r["purpose"]) <= 135 else r["purpose"][:132] + "…"
            lines.append(
                f"| [`{r['id']}`]({r['documentation']}) | {esc(purpose)} | {names(r['input_parameters'], 2)} | {names(r['declared_output_units'], 2)} |"
            )
        lines.append("")
    lines += [
        """## 커스터마이징과 다른 시스템 연동

1. 실제 재료·표면·환경·하중·시간·검사 위치를 고정하고 근거를 준비합니다.
2. 필요한 단위 API를 고른 뒤 `describe()`로 계약과 가정을 확인합니다.
3. 계수·물성·판정표는 해당 근거와 적용 범위를 함께 제공합니다. 외부 공급자는 ID/revision·설정·자료 해시로 구분합니다.
4. 선행 결과 전체와 문맥·해시를 다음 모듈에 전달하고, 좌표·단위·압력 기준·물리 범위가 맞는지 확인합니다.
5. 사용자 규칙은 별도 선언하고 계산 결과와 규칙 판정 상태를 따로 저장합니다.

열역학이 필요한 기능에는 CoolProp 상태·퓨가시티 연동이 있습니다. 위험성 평가와의 연결에는 명시적 확률 의미를 가진 교환 계약을 사용합니다. FTA는 가능한 후속 소비자의 한 예이며 결정론적 두께 손실 자체에서 고장확률을 자동 생성하지 않습니다. [연동 설계](docs/ARCHITECTURE_KO.md), [Python API](docs/API_KO.md), [확장 요청서](docs/extension_requests/README_KO.md)를 참고하세요.

## 검증 현황과 공개 버전 한계

| 확인 항목 | 기록된 결과 | 해석 범위 |
|---|---|---|
| 공개 입력 스키마 | 757/757 API 일치 | 입력 계약 제공 여부 |
| 핵심 API 전수 실행 | 230/232개 계산 | 2개는 실측 초기 두께·기초 관측자료 사용권한 필요 |
| 대표 기준값·물리 항등식 | 63개 군, 79개 시험 통과 | 모든 하위 분기·실험 검증을 뜻하지 않음 |
| 추가 불변량·보존법칙 | 57개 시험 통과 | 대표 수소·열수지 재검사 포함, 위 묶음과 일부 중복 |
| 공개 전 추가 시험 | 25/25개 통과 | 누락 변수·경계·선택 의존성·배포 경계 |
| 주 JSON 예제 실행 | 400/400개 통과 | 주 파일에 전체 API 예제가 들어 있는 것은 아님 |
| 설치 wheel 수치 시험 | 59/59개 통과 | 작업 소스 폴더 밖의 실제 설치본 사용 |
| 기본/전체 설치본 | 2/2개 코드·카탈로그 일치 | 기본 설치에 SciPy·CoolProp 없이 동작 |

**알려진 미해결 사항:** 전체 Ruff 정적 지적 885건, 주 예제 파일의 전체 API 포함 검사 1건, 정상 전수 실행의 외부 근거 보류 2건을 남겨 둡니다. 기존 엄격한 전체 검증 workflow는 이 상태를 숨기지 않고 실패를 표시할 수 있습니다. 알파 배포용 검사는 별도 범위로 표시하며 전체 검증을 대체하지 않습니다. 근거 파일·시험 묶음이 중복되므로 위 숫자를 더해 검증 모델 수를 만들지 않습니다.

자세한 상태는 [공개 전 점검](docs/PREPUBLISH_CHECKS_KO.md), [개별 실행](docs/CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](docs/PHYSICAL_REVIEW_KO.md), [개발·검증 이력](docs/DEVELOPMENT_HISTORY_KO.md)에 기록합니다.

## 연구와 개발을 이어가는 방법

```bash
python -m pytest -q tests/test_physical_consistency_review.py
python scripts/verify_core_physics_formulas.py
python scripts/audit_schema_coverage.py
python scripts/audit_public_source_boundary.py
# 기존의 엄격한 전체 검증. 알려진 미해결 항목 때문에 실패할 수 있음.
python scripts/verify.py
```

[연구 재개 설명서](docs/RESEARCH_CONTINUATION_KO.md)에는 현재 숫자의 분모, 저장 위치, 재현 순서, 데이터 취득과 권리 검토, 모델 추가, HPC 병렬 검사, 관련 저장소 확장 요청, 다음 검증 우선순위를 정리했습니다. 이 채팅이 없어도 저장소의 문서·스키마·시험·영수증에서 이어갈 수 있도록 유지합니다.

## 저작권·자료·보안

코드는 MIT로 공개합니다. 외부 데이터·라이브러리·규격·상업 공급자의 권리는 각각 유지되며 MIT가 이를 대신 허가하지 않습니다. 원자료·서적·문서 파일·실험 워크북·장치 원시 신호·로컬 실행 로그·인증정보는 공개 배포에 포함하지 않습니다. 공개 데이터라고 해서 기초 관측자료까지 자동으로 재배포 가능한 것으로 판단하지 않습니다.

모델명·일반적인 물리 법칙·독립적으로 작성한 수식 구현·자체 합성 검사를 식별 가능하게 문서화합니다. 근거는 [THIRD_PARTY_NOTICES](THIRD_PARTY_NOTICES.md)와 출처 카탈로그에 분리해 기록합니다. 권리·문장·배포 경계 검사는 위험을 줄이기 위한 확인이며 법적 무위험 인증은 아닙니다. [기여 방법](CONTRIBUTING.md) · [보안 제보](SECURITY.md) · [변경 이력](CHANGELOG.md) · [인용](CITATION.cff).
"""
    ]
    readme = "\n".join(lines) + "\n"
    readme = re.sub(
        r"\]\((?!https?://|#|mailto:)([^)]+)\)",
        lambda match: "](" + REPO + "/blob/main/" + match[1] + ")",
        readme,
    )
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
