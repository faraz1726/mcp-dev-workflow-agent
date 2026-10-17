"""Input validation shared by every tool. Fails early with clear messages."""
import re

MIN_LEN, MAX_LEN = 10, 2000
PROJECT_KEY_RE = re.compile(r"^[A-Z][A-Z0-9]{1,9}$")


class ValidationError(ValueError):
    """Raised for bad tool input. The server converts it to a ToolError."""


def validate_feature_request(text: str) -> str:
    if not isinstance(text, str):
        raise ValidationError("feature_request must be a string.")
    text = " ".join(text.split())  # normalise whitespace
    if len(text) < MIN_LEN:
        raise ValidationError(
            f"feature_request is too short ({len(text)} chars). Describe the feature "
            f"in at least {MIN_LEN} characters, e.g. 'Add password reset via email'."
        )
    if len(text) > MAX_LEN:
        raise ValidationError(f"feature_request is too long ({len(text)} chars). Max is {MAX_LEN}.")
    return text


def validate_project_key(key: str) -> str:
    key = (key or "").strip().upper()
    if not PROJECT_KEY_RE.match(key):
        raise ValidationError(
            "project_key must be 2-10 chars, start with a letter, and contain only "
            "letters/digits (e.g. 'PROJ', 'APP2')."
        )
    return key


def validate_risk_level(level: str) -> str:
    level = (level or "").strip().lower()
    if level not in {"low", "medium", "high"}:
        raise ValidationError("risk_level must be one of: low, medium, high.")
    return level
