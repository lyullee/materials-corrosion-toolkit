# Contributing

Start with the README module directory, `docs/RESEARCH_CONTINUATION_KO.md`, and the model's executable contract. Keep a change small enough to review against an independent mathematical case and its intended physical scope.

For every new model document purpose, geometry/material/environment assumptions, input units and conventions, declared outputs, missing-data behavior, source provenance, optional providers and validation limits. Preserve `RunContext`, result status, input/result digests and probability meanings. Never convert a deterministic damage quantity to an event probability without an explicit, supported model.

Provide independent reference values or physical invariants where practical. Keep calibration and holdout specimens/source groups separate. A fitted curve reproducing its own observations is not independent validation. Avoid implementation-mirroring tests that simply repeat the same calculation.

Do not contribute copied publication prose, figures, commercial standard tables, proprietary code, unlicensed observations, raw workbooks, credentials or private execution paths. Scientific model names and public references are useful, but a citation does not grant redistribution permission. Use independently written explanations and synthetic fixtures with explicit provenance.

Run the appropriate pytest subset, schema checks and relevant static checks; report outstanding failures honestly. The initial alpha release retains known full-quality-gate failures documented in `docs/RELEASE_STATUS_KO.md`. Do not remove those gates to make the release look fully verified.

Regenerate catalogs and documentation after changing public contracts. Review the generated diff, re-run affected numerical cases, and record why any test-source hash changed. API-breaking changes need a migration note and version change. Cross-project extensions should describe exact units, identities, contracts and expected checks in `docs/extension_requests/`.
