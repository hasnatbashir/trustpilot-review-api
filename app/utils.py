from sqlalchemy.inspection import inspect

def sa_to_dict(obj, exclude=None, prefix=None):
    """Convert SQLAlchemy ORM object to dict, with optional prefix for keys."""
    exclude = exclude or set()
    prefix = prefix or ""
    return {
        prefix + c.key: getattr(obj, c.key)
        for c in inspect(obj).mapper.column_attrs
        if c.key not in exclude
    }