"""Wire a caller-selected exact matched pair from the existing local dataset reader."""

from matintegrity.wet_co2_data import read_wet_co2_simulation_grid
from matintegrity.wet_co2_matched_contrast import (
    WetCo2MatchedContrastRequest,
    wet_co2_matched_contrast,
)


def assess_pair(local_workbook_path: str, *, lower_provider_row: int, upper_provider_row: int):
    # The caller supplies the approved local input path and chooses an exact pair.
    loaded = read_wet_co2_simulation_grid(local_workbook_path)
    by_row = {row.provider_row: row for row in loaded.rows}
    request = WetCo2MatchedContrastRequest(
        lower_factor_row=by_row[lower_provider_row],
        upper_factor_row=by_row[upper_provider_row],
        varied_factor="co2_pressure_Pa",
        provider_pairing_and_ceteris_paribus_reviewed=True,
        simulation_output_scope_reviewed=True,
    )
    return wet_co2_matched_contrast(request)


# Deliberately not executed: caller must verify their local source archive,
# row selection, redistribution rights and the two explicit review decisions.
