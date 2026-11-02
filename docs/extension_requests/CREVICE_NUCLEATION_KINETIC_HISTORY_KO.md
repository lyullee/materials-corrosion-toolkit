# Crevice 핵생성·성장 kinetics downstream 확장 요청

이 API는 closed-batch aqueous/solid inventory history를 생성하며 probability, damage, failure, risk 또는 qualification 결과를 만들지 않는다. Downstream consumer는 다음 lineage를 그대로 전달해야 한다.

- assessment, physical scope, clock, provider/revision, request digest
- aqueous species·phase stoichiometry source digest와 initial state
- per-phase nucleation/growth law source digest, 단위 및 calibration support
- saturation interval record digest와 Evidence
- interval ledger별 requested/applied extent, resource factor 및 aqueous/solid history
- element/charge residual과 결과 commit status

소비자는 caller saturation을 계산된 열역학 saturation으로 바꾸어 해석하지 말고, molar nucleation source를 핵 개수나 입자분포로 변환하지 말아야 한다. 이 API는 공간수송, 고정형상/이동경계 advection, deposit morphology 또는 보호막 성능을 포함하지 않는다. 별도의 사용자 검토가 있는 후속 module에서 geometry나 risk interface를 구성해야 한다.
