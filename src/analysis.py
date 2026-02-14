import pandas as pd
from src.config import ECONOMIC_EVENT_YEAR, ANALYSIS_START_YEAR


def analyze_seasonality(df: pd.DataFrame) -> dict:
    df_clean = df.dropna(subset=["dat_reestr"]).copy()
    df_clean["month"] = df_clean["dat_reestr"].dt.month
    df_clean["quarter"] = df_clean["dat_reestr"].dt.quarter
    
    registrations_by_month = df_clean.groupby("month").size()
    registrations_by_quarter = df_clean.groupby("quarter").size()
    
    peak_month = registrations_by_month.idxmax()
    low_month = registrations_by_month.idxmin()
    
    return {
        "registrations_by_month": registrations_by_month,
        "registrations_by_quarter": registrations_by_quarter,
        "peak_month": peak_month,
        "peak_count": registrations_by_month.max(),
        "low_month": low_month,
        "low_count": registrations_by_month.min(),
    }


def analyze_legal_forms(df: pd.DataFrame, event_year: int = ECONOMIC_EVENT_YEAR) -> dict:
    df_forms = df.dropna(subset=["dat_reestr"]).copy()
    df_forms["year"] = df_forms["dat_reestr"].dt.year
    
    def extract_form(name):
        import re
        name_upper = str(name).upper()
        name_upper = name_upper.replace('I', 'І')
        
        if (re.search(r'\bТОВ\b', name_upper) or 
            re.search(r'ТОВАРИСТВО.*ОБМЕЖЕН.*ВІДПОВІДАЛЬН', name_upper)):
            return "ТОВ"
        
        elif (re.search(r'\bПП\b', name_upper) or 
              re.search(r'ПРИВАТНЕ.*ПІДПРИЄМСТВО', name_upper)):
            return "ПП"
        
        elif (re.search(r'\bЗАТ\b', name_upper) or 
              re.search(r'ЗАКРИТЕ.*АКЦІОНЕРНЕ.*ТОВАРИСТВО', name_upper)):
            return "ЗАТ"
        
        elif (re.search(r'\bАТ\b', name_upper) or 
              re.search(r'\bПАТ\b', name_upper) or
              re.search(r'\bВАТ\b', name_upper) or
              re.search(r'АКЦІОНЕРНЕ.*ТОВАРИСТВО', name_upper) or
              re.search(r'ПУБЛІЧНЕ.*АКЦІОНЕРНЕ', name_upper) or
              re.search(r'ВІДКРИТЕ.*АКЦІОНЕРНЕ', name_upper)):
            return "АТ"
        
        elif 'ООО' in name_upper:
            return "ООО"
        
        return "Інше"
    
    df_forms["form"] = df_forms["name"].apply(extract_form)
    
    forms_by_year = df_forms.groupby(["year", "form"]).size().unstack(fill_value=0)
    
    before_event = df_forms[df_forms["year"] < event_year].groupby("form").size()
    after_event = df_forms[df_forms["year"] >= event_year].groupby("form").size()
    
    pp_before = before_event.get("ПП", 0)
    pp_after = after_event.get("ПП", 0)
    tov_before = before_event.get("ТОВ", 0)
    tov_after = after_event.get("ТОВ", 0)
    
    pp_change_pct = ((pp_after - pp_before) / pp_before * 100) if pp_before > 0 else 0
    tov_change_pct = ((tov_after - tov_before) / tov_before * 100) if tov_before > 0 else 0
    
    return {
        "forms_by_year": forms_by_year,
        "before_event": before_event,
        "after_event": after_event,
        "pp_before": pp_before,
        "pp_after": pp_after,
        "pp_change_pct": pp_change_pct,
        "tov_before": tov_before,
        "tov_after": tov_after,
        "tov_change_pct": tov_change_pct,
        "pp_declined": pp_after < pp_before,
        "tov_increased": tov_after > tov_before,
    }


def analyze_economic_impact(
    df: pd.DataFrame,
    start_year: int = ANALYSIS_START_YEAR,
    event_year: int = ECONOMIC_EVENT_YEAR
) -> dict:
    df_economic = df.dropna(subset=["dat_reestr"]).copy()
    df_economic["year"] = df_economic["dat_reestr"].dt.year
    
    registrations_per_year = df_economic.groupby("year").size()
    
    period_before = df_economic[
        (df_economic["year"] >= start_year) & (df_economic["year"] < event_year)
    ]
    period_after = df_economic[df_economic["year"] >= event_year]
    
    count_before = len(period_before)
    count_after = len(period_after)
    
    years_before = period_before["year"].nunique()
    years_after = period_after["year"].nunique()
    
    avg_before = count_before / years_before if years_before > 0 else 0
    avg_after = count_after / years_after if years_after > 0 else 0
    
    change_percent = ((avg_after - avg_before) / avg_before * 100) if avg_before > 0 else 0
    
    return {
        "registrations_per_year": registrations_per_year,
        "before_event": {
            "period": f"{start_year}-{event_year - 1}",
            "total": count_before,
            "years": years_before,
            "avg_per_year": avg_before,
        },
        "after_event": {
            "period": f"від {event_year}",
            "total": count_after,
            "years": years_after,
            "avg_per_year": avg_after,
        },
        "change_percent": change_percent,
        "hypothesis_confirmed": avg_after > avg_before,
    }
