"""Keep authored request descriptions and index newly added local request files."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
DIRECTORY = ROOT / 'docs/extension_requests'
INDEX = DIRECTORY / 'README_KO.md'
MARKER = '<!-- generated-extension-request-index -->'


def main():
    original = INDEX.read_text(encoding='utf-8')
    manual = original.split(MARKER, 1)[0].rstrip()
    listed = set(re.findall(r'`([A-Z0-9_]+_KO\.md)`', manual))
    actual = {p.name for p in DIRECTORY.glob('*.md') if p.name != INDEX.name}
    stale = listed - actual
    if stale:
        raise ValueError(f'Authored index references missing request files: {sorted(stale)}')
    missing = sorted(actual - listed)
    suffix = [MARKER, '', '## 추가 연동 요청', '',
              '아래 목록은 실제 요청서 파일에서 생성한다. 요청서의 존재는 상대 프로젝트의 구현 완료를 뜻하지 않는다.',
              '', '| 요청서 | 제목 |', '|---|---|']
    for name in missing:
        lines = (DIRECTORY / name).read_text(encoding='utf-8').splitlines()
        title = next((line.lstrip('# ').strip() for line in lines if line.startswith('#')), name)
        suffix.append(f'| `{name}` | {title.replace("|", "/")} |')
    INDEX.write_text(manual + '\n\n' + '\n'.join(suffix) + '\n', encoding='utf-8')
    print(f'authored_requests={len(listed)}; generated_requests={len(missing)}; total={len(actual)}')


if __name__ == '__main__':
    main()
