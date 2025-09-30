# Simple, explicit PII tagging & masking helpers.
# Extend this map in production or connect to an enterprise catalog.

def mask_email(email: str) -> str:
    if not email:
        return email
    parts = email.split("@")
    return parts[0][0] + "***@" + parts[1]

def mask_name(name: str) -> str:
    if not name:
        return name
    return name[0] + "***"

def mask_ip(ip: str) -> str:
    if not ip:
        return ip
    return "***.***.***.***"

PII_COLUMNS = {
    "email": mask_email,
    "user_name": mask_name,
    "ip_address": mask_ip,
}

def mask_row(row: dict) -> dict:
    result = dict(row)
    for col in PII_COLUMNS:
        if col in result and result[col] is not None:
            result[col] = PII_COLUMNS[col](result[col])
    return result
