"""Scientific calculation helpers for VO2MAX AI MVP."""

KG_TO_LB = 2.2046226218

def rockport_vo2max(age: int, equation_sex: str, weight_kg: float,
                    walk_minutes: float, finishing_hr: float) -> float:
    """
    Estimate VO2 max using the published Rockport 1-mile walk equation.

    Equation:
      VO2max = 132.853
               - 0.0769 * weight_lb
               - 0.3877 * age
               + 6.315 * sex_code
               - 3.2649 * time_min
               - 0.1565 * finishing_HR

    sex_code: male=1, female=0 (the equation's original binary coding).

    This is a field-test estimate, not a direct measurement or diagnosis.
    The implementation limits age to 30-69 and uses conservative input
    checks to avoid silently extrapolating beyond the intended MVP protocol.
    """
    if not isinstance(age, int) or not 30 <= age <= 69:
        raise ValueError("The Rockport equation in this app is restricted to ages 30–69.")
    if equation_sex not in {"male", "female"}:
        raise ValueError("This equation only supports its original male/female coding.")
    if not 35 <= float(weight_kg) <= 200:
        raise ValueError("Weight must be between 35 and 200 kg.")
    if not 10 <= float(walk_minutes) <= 30:
        raise ValueError("One-mile walk time must be between 10 and 30 minutes.")
    if not 60 <= float(finishing_hr) <= 220:
        raise ValueError("Finishing heart rate must be between 60 and 220 bpm.")

    weight_lb = float(weight_kg) * KG_TO_LB
    sex_code = 1 if equation_sex == "male" else 0
    result = (
        132.853
        - (0.0769 * weight_lb)
        - (0.3877 * age)
        + (6.315 * sex_code)
        - (3.2649 * float(walk_minutes))
        - (0.1565 * float(finishing_hr))
    )
    if not 5 <= result <= 100:
        raise ValueError(
            "The calculated value is outside the app's plausibility guardrail. "
            "Check the inputs and test protocol; do not use this result."
        )
    return round(result, 1)
