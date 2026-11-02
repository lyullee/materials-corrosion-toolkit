# Downstream extension request: dynamic crevice geometry

## Available API

`integration.crevice_component_state_bdf` schema v4 can opt into `instantaneous_solid_aperture_feedback`. It accepts Evidence/digest-bound cell dimensions and phase molar-volume/gap-occupancy maps, then closes each instantaneous aqueous/solid stage with bounded damped iteration. The resulting aperture and face area affect liquid volume, Nernst–Planck current density, and integrated component transfer.

## Requested downstream work

Connect this API to the project-level corrosion/material-integrity assessment by supplying validated phase molar volumes, deposition-location/occupancy evidence, and a versioned geometry provider. Preserve the full request/result digest chain and compare predicted aperture/volume histories against independently measured crevice geometry.

Do not interpret caller geometry as validated material behavior. Current implementation excludes nucleation/kinetics, porosity and packing, mechanical deformation, cell remapping, and joint hydraulic/Faradaic-stage feedback. Those need independently reviewed extensions with their own bounded contracts and data.

## Acceptance evidence to collect downstream

- traceable license and provenance for every phase/property and geometry record;
- independent material/environment/geometry validation covering the declared support;
- water/component/charge and geometry residuals, including work-budget records;
- explicit review before combining with hydraulic or spatial Faradaic coupling.
