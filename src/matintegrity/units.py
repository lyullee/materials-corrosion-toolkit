"""Dimensional conversion with declared pressure basis and elapsed-time units."""

import math

import pint

_UNITS = pint.UnitRegistry(autoconvert_offset_to_baseunit=True)
SECONDS_PER_YEAR = 365.25 * 86400.0


def convert(value: float, source_unit: str, target_unit: str) -> float:
    if isinstance(value, bool) or not math.isfinite(value):
        raise ValueError("finite numeric value required")
    result = float(_UNITS.Quantity(value, source_unit).to(target_unit).magnitude)
    if not math.isfinite(result):
        raise ValueError("conversion produced a non-finite value")
    return result


def absolute_pressure(value: float, unit: str, *, basis: str, ambient_pa: float | None = None) -> float:
    pressure = convert(value, unit, "Pa")
    if basis == "gauge":
        if (
            ambient_pa is None
            or isinstance(ambient_pa, bool)
            or not math.isfinite(ambient_pa)
            or ambient_pa <= 0
        ):
            raise ValueError("gauge pressure requires positive declared ambient pressure")
        pressure += ambient_pa
    elif basis != "absolute":
        raise ValueError("pressure basis must be absolute or gauge")
    if not math.isfinite(pressure) or pressure <= 0:
        raise ValueError("absolute pressure must be positive and finite")
    return pressure
