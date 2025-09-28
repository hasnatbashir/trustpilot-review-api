# Simple, explicit PII tagging & masking helpers.
# Extend this map in production or connect to an enterprise catalog.
PII_COLUMNS = {"email"}

def mask_email(value: str | None) -> str | None:
    if not value:
        return value
    try:
        name, domain = value.split("@", 1)
        return "***@" + domain
    except Exception:
        return "***"

def mask_row(row: dict) -> dict:
    result = dict(row)
    for col in PII_COLUMNS:
        if col in result and result[col] is not None:
            result[col] = mask_email(result[col])
    return result
