
import customtkinter as ctk

def apply_date_mask(event):
    """
    Tarih maskeleme: "1205" -> "12.05.2026"
    """
    entry = event.widget
    val = entry.get().replace(".", "")
    if not val.isdigit():
        return
    
    # Sadece rakam kalsın
    if len(val) == 4:
        # Örn: 1205 -> 12.05.2026
        from datetime import datetime
        year = datetime.now().year
        new_val = f"{val[:2]}.{val[2:4]}.{year}"
        entry.delete(0, "end")
        entry.insert(0, new_val)
    elif len(val) == 8:
        # Örn: 12052026 -> 12.05.2026
        new_val = f"{val[:2]}.{val[2:4]}.{val[4:]}"
        entry.delete(0, "end")
        entry.insert(0, new_val)

def format_price(value, precision=2):
    """Fiyat formatlama"""
    try:
        return f"{float(value):.{precision}f}"
    except:
        return value
