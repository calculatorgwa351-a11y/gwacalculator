from sqlalchemy.orm import Session
from typing import Optional, List
from app.models import SubjectGrade, User, Post, Department, Course, Admin

def compute_gwa_for_user(user_id: int, db: Session) -> Optional[float]:
    grades = db.query(SubjectGrade).filter(SubjectGrade.user_id == user_id).all()
    total_units = sum(g.units for g in grades if g.units is not None and g.grade is not None)
    if total_units == 0:
        return None
    total = sum(g.units * g.grade for g in grades if g.units is not None and g.grade is not None)
    return round(total / total_units, 3)

def analyze_latin_honors(user_id: int, db: Session) -> dict:
    grades = db.query(SubjectGrade).filter(SubjectGrade.user_id == user_id).all()
    if not grades:
        return {"eligible": False, "reason": "No grades recorded", "title": None}

    total_units = 0
    total_weighted_grade = 0
    has_failed = False
    has_below_2_5 = False

    for g in grades:
        if g.grade is None or g.units is None:
            continue

        # Exclude NSTP/ROTC from GWA
        subj_upper = (g.subject or "").upper()
        if "NSTP" in subj_upper or "ROTC" in subj_upper:
            continue

        total_units += g.units
        total_weighted_grade += (g.units * g.grade)

        if g.grade > 3.0:
            has_failed = True
        if g.grade > 2.5:
            has_below_2_5 = True

    if total_units == 0:
        return {"eligible": False, "reason": "No valid academic units", "title": None, "status": "Regular"}

    gwa = round(total_weighted_grade / total_units, 3)
    status = "Regular"

    if has_failed:
        return {"eligible": False, "reason": "Has failing grades (>3.0)", "title": None, "gwa": gwa, "status": status}
    
    if has_below_2_5:
        return {"eligible": False, "reason": "Has grades below 2.50", "title": None, "gwa": gwa, "status": status}

    title = None
    if 1.00 <= gwa <= 1.20:
        title = "Summa Cum Laude"
    elif 1.21 <= gwa <= 1.45:
        title = "Magna Cum Laude"
    elif 1.46 <= gwa <= 1.75:
        title = "Cum Laude"

    if title:
        return {"eligible": True, "reason": "Meets all CTU academic criteria", "title": title, "gwa": gwa, "status": status}
    else:
        return {"eligible": False, "reason": "GWA does not meet honors cutoff", "title": None, "gwa": gwa, "status": status}

def get_global_analytics(db: Session) -> dict:
    from sqlalchemy import func, cast, Float
    
    # Calculate individual GWAs
    user_gwas = db.query(
        SubjectGrade.user_id,
        (func.sum(SubjectGrade.units * SubjectGrade.grade) / func.sum(SubjectGrade.units)).label("gwa")
    ).filter(SubjectGrade.units > 0).group_by(SubjectGrade.user_id).subquery()
    
    # Average of GWAs
    avg_gwa_result = db.query(func.avg(user_gwas.c.gwa)).scalar()
    
    # Global failure rate
    fail_metrics = db.query(
        func.count(SubjectGrade.id).label("total"),
        func.sum(cast(SubjectGrade.grade > 3.0, Float)).label("failed")
    ).first()
    
    fail_rate = (fail_metrics.failed / fail_metrics.total) if fail_metrics and fail_metrics.total > 0 else None
    
    return {
        "average_gwa": round(avg_gwa_result, 3) if avg_gwa_result else None,
        "failure_rate": round(fail_rate, 4) if fail_rate is not None else None
    }


def _noop_cache_clear() -> None:
    return None


compute_gwa_for_user.cache_clear = _noop_cache_clear
analyze_latin_honors.cache_clear = _noop_cache_clear
get_global_analytics.cache_clear = _noop_cache_clear
