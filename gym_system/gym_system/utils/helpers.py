def format_currency(value):
    return f'${value:,.0f}'

def days_until(date):
    from utils.colombia_time import today_bogota
    delta = date - today_bogota()
    return delta.days

def membership_status(end_date):
    days = days_until(end_date)
    if days < 0:
        return 'vencido'
    if days <= 3:
        return 'por_vencer'
    return 'activo'
