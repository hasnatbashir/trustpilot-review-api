# Simple, explicit PII tagging & masking helpers.
# Extend this map in production or connect to an enterprise catalog.

from app.constants import F_EMAIL, F_IP, F_USER_NAME


def mask_email(email: str) -> str:
    """Mask an email address keeping first char and domain.

    Args:
        email: raw email string.

    Returns:
        Masked email string, or original falsy input.
    """
    if not email:
        return email
    parts = email.split("@")
    return parts[0][0] + "***@" + parts[1]

def mask_name(name: str) -> str:
    """Mask a person name keeping only the first character.

    Args:
        name: raw user name.

    Returns:
        Masked name string, or original falsy input.
    """
    if not name:
        return name
    return name[0] + "***"

def mask_ip(ip: str) -> str:
    """Mask an IP address to a consistent obfuscated pattern.

    Args:
        ip: raw IP address string.

    Returns:
        Masked IP string, or original falsy input.
    """
    if not ip:
        return ip
    return "***.***.***.***"

PII_COLUMNS = {
    F_EMAIL: mask_email,
    F_USER_NAME: mask_name,
    F_IP: mask_ip,
}

def mask_row(row: dict) -> dict:
    """Apply PII masking functions to a dict row for known PII columns.

    Args:
        row: mapping of column name -> value.

    Returns:
        A new dict with masked values for PII columns when present.
    """
    result = dict(row)
    for col in PII_COLUMNS:
        if col in result and result[col] is not None:
            result[col] = PII_COLUMNS[col](result[col])
    return result
