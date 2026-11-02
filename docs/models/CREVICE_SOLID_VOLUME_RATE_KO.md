# Crevice signed solid-volume rate adapter

## Purpose

`corrosion.crevice_solid_volume_rate` converts signed cellwise phase molar rates into solid volume growth and displaced liquid volume rates. Positive phase rate means precipitation; negative rate means dissolution.

## Calculation

For cell `i`, only phases explicitly declared to occupy the crevice gap contribute:

`dV_solid,i/dt = Σ_j occupies_gap(i,j) × V_m(i,j) × dn_solid(i,j)/dt`

`dV_liquid,i/dt = -dV_solid,i/dt`

No rate is clipped at zero. The returned closure residual is the floating-point sum of the equal-and-opposite rates.

## Inputs and lineage

Inputs retain ordered cell and phase IDs, one signed rate and one positive molar volume per phase, and an explicit gap-occupancy flag. A geometry digest binds the ordered phase-volume/occupancy map. A separate kinetic digest binds assessment, physical scope, clock, stage time, cell/phase order and signed phase rates. Each digest requires matching licensed Evidence; computational-use authorization is also required.

## Connection and limitations

`bind_solid_volume_rates_to_hydraulic_stage()` composes a committed rate result with a hydraulic stage request. It requires matching assessment, physical scope, exact stage time and ordered cell IDs. The helper calculates a digest over the full hydraulic cell geometry, liquid-volume rates and complete phase-volume result digest. It requires caller-provided `composition_authorization` whose source ID is `composed_crevice_stage_geometry_and_phase_volume_rate`, digest matches exactly, and license ID is populated. This explicit authorization avoids assuming that separate input licenses automatically permit a derived combined use.

For direct registry and Python/JSON use, `integration.crevice_solid_volume_hydraulic_stage` accepts the phase-rate request/result, hydraulic stage request, and composition authorization, then returns both the composed hydraulic request and its evaluated RHS. Use `composed_crevice_stage_geometry_digest()` with the complete volume-result digest to calculate the exact digest that the authorization must bind. A wiring example is in `examples/crevice_solid_volume_hydraulic_stage.py`.

This is a same-stage API composition with digest and permission checks. It still does not form one jointly solved BDF RHS: the caller supplies an already computed phase-rate result. The adapter does not estimate phase kinetics, update the BDF aperture state, perform species transport or integrate pressure flow. It makes no physical qualification claim.
