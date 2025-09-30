from sqlalchemy.inspection import inspect

def sa_to_dict(obj, exclude=None, prefix=None):
    """Convert a SQLAlchemy ORM object to a plain dict.

    Args:
        obj: SQLAlchemy ORM instance to convert.
        exclude: Optional set/list of attribute names to exclude from the dict.
        prefix: Optional string to prefix to each dict key.

    Returns:
        dict: Mapping of column attribute name -> value for the given ORM object.
    """
    exclude = exclude or set()
    prefix = prefix or ""
    return {
        prefix + c.key: getattr(obj, c.key)
        for c in inspect(obj).mapper.column_attrs
        if c.key not in exclude
    }