# Ti-12Mo-5Zr EIS 복소 임피던스 변환

`corrosion.ti12mo5zr_eis_complex_impedance`는 로컬 전용 Zenodo CC0 자료 reader가 반환한 단일 Ti-12Mo-5Zr 또는 Ti-12Mo EIS 워크북의 74개 원행을 입력받습니다. 허용된 6개 멤버의 archive/member digest, EIS 자료 종류, 75행×5열 구조, 정확한 헤더, 행 순서 2–75와 공통 workbook provenance를 확인합니다. 원본 행은 수정하지 않으며 각 출력점에는 원행 SHA-256, 멤버와 archive lineage를 남깁니다.

입력 열 `|Z| [Ohm]`과 `WE.-Phase [deg]`로부터 caller가 선택·증거화한 부호 규약에 따라 다음 성분을 계산합니다.

\[
Z = |Z|\exp(i\,s\phi),\qquad Z'=|Z|\cos(s\phi),\qquad Z''=|Z|\sin(s\phi)
\]

여기서 \(\phi\)는 제공자 위상 각도를 라디안으로 환산한 값이고 \(s\in\{+1,-1\}\)입니다. `phase_convention_evidence`는 선택한 규약의 근거를 가리켜야 하고 `phase_convention_reviewed`, `computational_use_authorized`, `local_only_authorized`가 명시돼야 합니다. 규약 승인이 없으면 `needs_data` 상태가 반환됩니다.

열의 `Time [s]` 값은 장비 스캔 행에 기록된 값으로 보존합니다. 이를 침지 경과시간으로 바꾸거나 주파수/시간으로 행을 정렬하지 않습니다. 출력은 복소 임피던스 변환 자료이며 면적 정규화, equivalent-circuit 피팅, polarization resistance 산출, 부식률, 수명, 위험도 또는 합금 순위가 아닙니다. 제공자 실험 설명은 EIS 면적 0.785 cm²를 언급하지만 이를 이 변환에 적용하지 않습니다.

독립적인 합성 입력 예제는 `examples/ti12mo5zr_eis_complex_local.py`에 있습니다. 이 예제는 실행하거나 실제 행을 평가하지 않았습니다.
