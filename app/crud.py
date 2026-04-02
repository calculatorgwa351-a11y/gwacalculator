from sqlalchemy import case, func, or_, and_
from sqlalchemy.orm import Session
from typing import Optional
from app.models import SubjectGrade

def compute_gwa_for_user(user_id: int, db: Session) -> Optional[float]:
    result = (
        db.query(
            (
                func.sum(SubjectGrade.units * SubjectGrade.grade)
                / func.nullif(func.sum(SubjectGrade.units), 0)
            ).label("gwa")
        )
        .filter(
            SubjectGrade.user_id == user_id,
            SubjectGrade.units.isnot(None),
            SubjectGrade.grade.isnot(None),
        )
        .scalar()
    )
    if result is None:
        return None
    return round(float(result), 3)

def analyze_latin_honors(user_id: int, db: Session) -> dict:
    valid_subject_filter = or_(
        SubjectGrade.subject.is_(None),
        and_(
            ~SubjectGrade.subject.ilike("%NSTP%"),
            ~SubjectGrade.subject.ilike("%ROTC%"),
        ),
    )

    stats = (
        db.query(
            func.sum(SubjectGrade.units).label("total_units"),
            func.sum(SubjectGrade.units * SubjectGrade.grade).label("total_weighted_grade"),
            func.max(case((SubjectGrade.grade > 3.0, 1), else_=0)).label("has_failed"),
            func.max(case((SubjectGrade.grade > 2.5, 1), else_=0)).label("has_below_2_5"),
            func.count(SubjectGrade.id).label("grade_count"),
        )
        .filter(
            SubjectGrade.user_id == user_id,
            SubjectGrade.grade.isnot(None),
            SubjectGrade.units.isnot(None),
            valid_subject_filter,
        )
        .first()
    )

    if not stats or not stats.grade_count:
        return {"eligible": False, "reason": "No grades recorded", "title": None}

    total_units = float(stats.total_units or 0)
    total_weighted_grade = float(stats.total_weighted_grade or 0)
    has_failed = bool(stats.has_failed)
    has_below_2_5 = bool(stats.has_below_2_5)

    if total_units <= 0:
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
        func.sum(case((SubjectGrade.grade > 3.0, 1), else_=0)).label("failed")
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
