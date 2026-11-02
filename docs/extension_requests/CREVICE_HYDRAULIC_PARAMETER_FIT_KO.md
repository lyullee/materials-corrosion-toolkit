# Downstream extension request: calibrated slit hydraulics

`calibration.crevice_slit_hydraulic_law_parameters` fits two global correction multipliers for the registered reduced planar-slit resistance/inertance model. Use independent complete groups for calibration and holdout, preserve measurement uncertainty and rights Evidence, and pin the complete fit result before transferring parameters through `apply_hydraulic_parameter_fit`.

Downstream integration should provide independently traceable pressure, aperture, fluid-property and flow records; assess identifiability and residual patterns across more than one operating condition; retain holdout predictions; and refuse transfer outside the recorded provider/grid and calibration support. The fit is user-model calibration and does not establish turbulence, moving-wall behavior, general momentum validity, or qualification.
