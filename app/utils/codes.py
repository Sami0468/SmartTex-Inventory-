"""
Code generators — produce human-friendly sequential codes like FB-0001, INV-2026-0001.
"""
from datetime import datetime


def next_code(model, column_name, prefix, pad=4):
    """Generate next sequential code, e.g. FB-0001 -> FB-0002, based on max existing code."""
    column = getattr(model, column_name)
    last = model.query.order_by(column.desc()).first()
    if not last:
        return f"{prefix}-{1:0{pad}d}"
    last_value = getattr(last, column_name)
    try:
        last_num = int(last_value.split("-")[-1])
    except (ValueError, AttributeError):
        last_num = model.query.count()
    return f"{prefix}-{last_num + 1:0{pad}d}"


def next_invoice_number(model, column_name="invoice_number"):
    """Generate invoice number like INV-2026-0001 scoped to current year."""
    year = datetime.utcnow().year
    column = getattr(model, column_name)
    prefix = f"INV-{year}-"
    last = model.query.filter(column.like(f"{prefix}%")).order_by(column.desc()).first()
    if not last:
        return f"{prefix}0001"
    last_value = getattr(last, column_name)
    try:
        last_num = int(last_value.split("-")[-1])
    except (ValueError, AttributeError):
        last_num = 0
    return f"{prefix}{last_num + 1:04d}"
