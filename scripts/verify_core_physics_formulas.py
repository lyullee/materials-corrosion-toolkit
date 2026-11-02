"""Execute the explicit representative reference tests and reconcile all 63 groups."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]

def main():
    manifest = json.loads((ROOT/'tests/data/core_physics_formula_cases.json').read_text(encoding='utf8'))
    groups = manifest['groups']
    assert sorted(row['group'] for row in groups) == list(range(1,64))
    for row in groups:
        for path, digest in row['source_sha256'].items():
            assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest() == digest, f'Review changed test source: {path}'
    nodes = list(dict.fromkeys(node for row in groups for node in row['nodes']))
    output = ROOT/'artifacts/validation/formula_63'
    output.mkdir(parents=True,exist_ok=True)
    receipt = output/'results.xml'
    code = subprocess.call([sys.executable,'-m','pytest','-q',*nodes,f'--junitxml={receipt}'],cwd=ROOT)
    cases = list(ET.parse(receipt).iter('testcase'))
    rows=[]
    for row in groups:
        findings=[]
        for node in row['nodes']:
            path, name = node.split('::')
            classname=path.removesuffix('.py').replace('/','.')
            matches=[c for c in cases if c.get('classname')==classname and (c.get('name')==name or c.get('name','').startswith(name+'['))]
            status='passed' if matches and all(not any(c.find(tag) is not None for tag in ('failure','error','skipped')) for c in matches) else 'unresolved'
            findings.append({'node':node,'status':status,'executed_cases':len(matches)})
        rows.append(row|{'status':'passed' if all(f['status']=='passed' for f in findings) else 'unresolved','results':findings})
    passed=sum(r['status']=='passed' for r in rows)
    result={'scope':manifest['basis'],'passed_groups':passed,'target_groups':63,'executed_cases':len(cases),'pytest_exit_code':code,'groups':rows}
    (output/'coverage.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    lines=['# 63개 계산군 계산식 확인 결과','',f'대표 기준값 시험 통과: **{passed}/63개 계산군**. 실행 사례: {len(cases)}개.','',
           '각 계산군에 지정한 대표 문제의 수치 비교 결과다. 하위 모델과 물리 분기 전체, 실험자료 검증 및 시스템 통합 완료를 뜻하지 않는다.',
           'Sines의 입력검사 우회 fixture는 이 계산식 시험에 사용하지 않는다.','',
           '| 번호 | 계산군 | 결과 | 실행한 비교 시험 |','|---|---|---|---|']
    for row in rows:
        lines.append(f"| {row['group']} | {row['name']} | {row['status']} | {'; '.join(row['nodes'])} |")
    lines += ['', '재현: `.venv\\Scripts\\python.exe -X utf8 scripts/verify_core_physics_formulas.py`',
              '', '실행 근거: `artifacts/validation/formula_63/results.xml`, `coverage.json`. 시험 소스 해시는 `tests/data/core_physics_formula_cases.json`에 고정한다.']
    lines += ['', '## 해석 범위', '',
              '- 5번은 선형 전류수지, 19번은 고정 원통 한 셀 확산을 확인했다. 비선형 전극·이동경계 전체 결합은 별도다.',
              '- 25번은 원통 수소 확산, 31번은 구간 선형 변형률 Prony 끝점 평형 사례다. 모든 포획·방출·연속시간 분기의 검증을 뜻하지 않는다.',
              '- 44번은 비례 순수전단 Crossland, 45번은 추가 경화계수 0인 Itoh 수명 한계 사례다. 다른 다축 기준과 비비례 경로 전체는 별도다.',
              '- 49번은 대류 저항, 53번은 비영 응축 질량·액막 수지다. 복사·잠열을 포함한 모든 결합 분기의 검증은 아니다.',
              '', '63/63은 각 계산군에 최소 하나의 대표 수학적 기준값 비교가 통과했다는 뜻이다. 극단값·연결·전체 실행 완료율로 전용하지 않는다.']
    (ROOT/'docs/FORMULA_VERIFICATION_PROGRESS_KO.md').write_text('\n'.join(lines)+'\n',encoding='utf8')
    print(f'formula_reference_groups={passed}/63; executed_cases={len(cases)}')
    return code or (0 if passed==63 else 1)

if __name__=='__main__':
    raise SystemExit(main())
