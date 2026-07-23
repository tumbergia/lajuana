"""Deterministic conversational analysis for analytics modules.

Produces 3–4 short paragraphs with findings, conclusions and recommendations.
Used by the dashboard payload, XLSX export and mirrored on mobile as fallback.
"""

from __future__ import annotations

from statistics import median, pstdev

from app.schemas.analytics_v2 import AnalyticsModule, ModuleStatus


def _fmt(n: float, *, digits: int = 1) -> str:
    if abs(n - round(n)) < 1e-9:
        return str(int(round(n)))
    return f"{n:.{digits}f}"


def _unit_of(mod: AnalyticsModule, fallback: str = "") -> str:
    if mod.primary_value and mod.primary_value.unit:
        return mod.primary_value.unit
    if mod.series and mod.series[0].unit:
        return mod.series[0].unit
    if mod.breakdown and mod.breakdown[0].unit:
        return mod.breakdown[0].unit
    if mod.ranking and mod.ranking[0].unit:
        return mod.ranking[0].unit
    return fallback


def _share(share: float | None, raw: float, total: float) -> float | None:
    if share is not None:
        return share
    if total > 0:
        return round(raw / total * 100, 1)
    return None


def _period_clause(mod: AnalyticsModule) -> str:
    if not mod.period:
        return "el periodo analizado"
    label = (mod.period.label or "").strip()
    return label if label else "el periodo analizado"


def _cmp_phrase(mod: AnalyticsModule) -> str | None:
    cmp_ = mod.comparison
    if not cmp_:
        return None
    if cmp_.label:
        return cmp_.label.rstrip(".")
    if cmp_.percentage_delta is None:
        return None
    d = cmp_.percentage_delta
    sign = "+" if d > 0 else ""
    caution = "" if cmp_.sufficient_sample else " (con muestra limitada del periodo anterior)"
    return f"variación de {sign}{_fmt(d)}% frente al periodo anterior{caution}"


def _series_stats(mod: AnalyticsModule) -> dict[str, float | str | int] | None:
    if not mod.series or not mod.series[0].points:
        return None
    series = mod.series[0]
    values = [p.raw for p in series.points]
    n = len(values)
    total = sum(values)
    avg = total / n if n else 0.0
    peak = max(series.points, key=lambda p: p.raw)
    trough = min(series.points, key=lambda p: p.raw)
    first, last = values[0], values[-1]
    half_pct: float | None = None
    if n >= 4:
        mid = n // 2
        a1 = sum(values[:mid]) / mid
        a2 = sum(values[mid:]) / (n - mid)
        if a1 != 0:
            half_pct = (a2 - a1) / abs(a1) * 100
        elif a2 == 0:
            half_pct = 0.0
    return {
        "n": n,
        "total": total,
        "avg": avg,
        "median": float(median(values)),
        "min": min(values),
        "max": max(values),
        "peak_label": peak.label,
        "trough_label": trough.label,
        "first": first,
        "last": last,
        "sd": float(pstdev(values)) if n >= 3 else 0.0,
        "cv": (float(pstdev(values)) / avg * 100) if n >= 3 and avg else 0.0,
        "zeros": sum(1 for v in values if v == 0),
        "half_pct": half_pct if half_pct is not None else 0.0,
        "has_half": 1 if half_pct is not None else 0,
        "unit": series.unit or _unit_of(mod),
    }


def _breakdown_stats(mod: AnalyticsModule) -> dict[str, object] | None:
    items = mod.breakdown
    if not items:
        return None
    total = sum(i.raw_value for i in items) or 0.0
    ordered = sorted(items, key=lambda i: i.raw_value, reverse=True)
    top = ordered[0]
    top_share = _share(top.share_percentage, top.raw_value, total) or 0.0
    top2 = sum(i.raw_value for i in ordered[:2]) if len(ordered) >= 2 else top.raw_value
    hhi = 0.0
    if total > 0 and len(items) >= 2:
        hhi = sum((i.raw_value / total) ** 2 for i in items) * 10000
    by_key = {i.key: i for i in items}
    return {
        "n": len(items),
        "total": total,
        "top": top,
        "top_share": top_share,
        "top2_share": (top2 / total * 100) if total else 0.0,
        "hhi": hhi,
        "ordered": ordered,
        "by_key": by_key,
        "unit": items[0].unit or _unit_of(mod, "reservas"),
    }


def _ranking_stats(mod: AnalyticsModule) -> dict[str, object] | None:
    items = mod.ranking
    if not items:
        return None
    total = sum(i.raw_value for i in items) or 0.0
    top = items[0]
    gap = (top.raw_value - items[1].raw_value) if len(items) >= 2 else 0.0
    top3 = sum(i.raw_value for i in items[:3]) if len(items) >= 3 else total
    return {
        "n": len(items),
        "total": total,
        "avg": total / len(items) if items else 0.0,
        "top": top,
        "second": items[1] if len(items) >= 2 else None,
        "gap": gap,
        "top3_share": (top3 / total * 100) if total else 0.0,
        "unit": items[0].unit or _unit_of(mod),
    }


def _empty_or_error(mod: AnalyticsModule) -> list[str] | None:
    if mod.status == ModuleStatus.EMPTY:
        msg = mod.empty_message or "Todavía no hay datos suficientes para este indicador."
        return [
            msg,
            (
                f"Cuando haya actividad en {_period_clause(mod)}, aquí verás un "
                "resumen con hallazgos y recomendaciones accionables."
            ),
        ]
    if mod.status == ModuleStatus.ERROR:
        return [
            mod.insight_text or "No pudimos actualizar esta información en este momento.",
            "Reintenta en unos segundos; el resto de indicadores sigue disponible.",
        ]
    return None


def _paras_action_center(mod: AnalyticsModule) -> list[str]:
    bd = _breakdown_stats(mod)
    total = int(bd["total"]) if bd else int(mod.primary_value.raw if mod.primary_value else 0)
    if total <= 0:
        return [
            "Ahora mismo no hay pendientes críticos en la cola operativa.",
            (
                "Mantén el ritmo de revisión diaria: cuando aparezcan comprobantes "
                "por verificar, datos de participantes incompletos o cuidados "
                "vencidos, este panel los priorizará primero."
            ),
            "La operación está al día. Sigue monitoreando al abrir la jornada.",
        ]
    top = bd["ordered"][0] if bd else None  # type: ignore[index]
    lead = f"La cola principal es «{top.label}» con {_fmt(top.raw_value)} ítems." if top else ""
    return [
        (f"Hay {total} pendientes que requieren atención en {_period_clause(mod)}. {lead}").strip(),
        (
            "Prioriza primero lo que bloquea ingresos o salidas (pagos por verificar "
            "y participantes incompletos); después atiende cuidados equinos y "
            "alertas de bienestar para no acumular riesgo operativo."
        ),
        (
            "La carga está concentrada en pocas colas. "
            "Cierra hoy al menos la mitad de la cola principal "
            "antes de abrir nuevos frentes."
        ),
    ]


def _paras_reservation_trend(mod: AnalyticsModule) -> list[str]:
    st = _series_stats(mod)
    cmp_ = _cmp_phrase(mod)
    total = int(st["total"]) if st else int(mod.primary_value.raw if mod.primary_value else 0)
    unit = (st["unit"] if st else _unit_of(mod, "reservas")) or "reservas"
    p1 = (
        f"En {_period_clause(mod)} se registraron {_fmt(total)} {unit} nuevas"
        + (f", con un promedio de {_fmt(float(st['avg']))} por tramo" if st else "")
        + "."
    )
    if cmp_:
        p1 += f" Respecto al periodo anterior: {cmp_}."
    p2 = ""
    if st and int(st["n"]) >= 2:
        p2 = (
            f"El punto más alto fue {_fmt(float(st['max']))} ({st['peak_label']}) "
            f"y el más bajo {_fmt(float(st['min']))} ({st['trough_label']})."
        )
        if int(st["has_half"]):
            hp = float(st["half_pct"])
            if abs(hp) < 5:
                p2 += " La segunda mitad del periodo se mantuvo estable frente a la primera."
            elif hp > 0:
                p2 += f" La segunda mitad aceleró cerca de {_fmt(hp)}% respecto a la primera."
            else:
                p2 += f" La segunda mitad bajó cerca de {_fmt(abs(hp))}% respecto a la primera."
        if float(st["cv"]) >= 40:
            p2 += " Hay bastante variabilidad entre tramos: conviene mirar picos y huecos."
    insight = (mod.insight_text or "").strip()
    if insight and insight not in p1:
        p1 = f"{insight} {p1}" if not insight.endswith(".") else f"{insight} {p1}"
    rec = (
        "El flujo de reservas nuevas marca el pulso comercial. "
        "Si la tendencia baja, refuerza captación en los canales "
        "que ya convierten; si sube, asegúrate de que operaciones (cupos y equinos) "
        "acompañen el ritmo."
    )
    return [p for p in [p1, p2, rec] if p]


def _paras_confirmed_value(mod: AnalyticsModule) -> list[str]:
    st = _series_stats(mod)
    cmp_ = _cmp_phrase(mod)
    value = mod.primary_value.formatted if mod.primary_value else "—"
    unit = mod.primary_value.unit if mod.primary_value else "COP"
    p1 = (
        f"Tienes {value} {unit} en ingresos comprometidos durante {_period_clause(mod)}: "
        "es el monto cotizado de reservas ya confirmadas o completadas, aunque el "
        "cobro todavía no se haya cerrado."
    )
    if cmp_:
        p1 += f" Frente al periodo anterior: {cmp_}."
    p2 = ""
    if st and int(st["n"]) >= 2:
        p2 = (
            f"El recorrido va de {_fmt(float(st['min']))} a {_fmt(float(st['max']))} {unit}, "
            f"con promedio de {_fmt(float(st['avg']))} por tramo."
        )
        if int(st["has_half"]) and abs(float(st["half_pct"])) >= 5:
            hp = float(st["half_pct"])
            direction = "al alza" if hp > 0 else "a la baja"
            p2 += f" La segunda mitad del periodo se movió {direction} (~{_fmt(abs(hp))}%)."
    rec = (
        "Este indicador anticipa facturación asegurada, no caja cobrada. "
        "Cruza con comprobantes de pago para detectar confirmadas "
        "sin cobro y prioriza su seguimiento comercial."
    )
    return [p for p in [p1, p2, rec] if p]


def _paras_reservation_status(mod: AnalyticsModule) -> list[str]:
    bd = _breakdown_stats(mod)
    if not bd:
        return [
            f"No hay distribución de estados clara en {_period_clause(mod)}.",
            "Sin volumen no se diagnostica el embudo. Revisa más adelante o amplía el periodo.",
        ]
    top = bd["top"]  # type: ignore[assignment]
    p1 = (
        f"En {_period_clause(mod)} la mayoría de las reservas están en «{top.label}» "
        f"({_fmt(float(bd['top_share']))}% del total de {_fmt(float(bd['total']))})."
    )
    by_key = bd["by_key"]  # type: ignore[assignment]
    risk = 0.0
    for k in ("pending_payment", "payment_received"):
        if k in by_key:
            risk += by_key[k].raw_value  # type: ignore[index]
    p2 = f"Los dos estados líderes concentran {_fmt(float(bd['top2_share']))}% del total."
    if risk > 0 and float(bd["total"]) > 0:
        p2 += (
            f" Hay {_fmt(risk)} reservas aún en cobro o verificación "
            f"({_fmt(risk / float(bd['total']) * 100)}%)."
        )
    rec = (
        "El desglose muestra dónde se atasca el ciclo, no una tasa de conversión. "
        "Atiende primero las que esperan pago o revisión de comprobante "
        "para liberar cupos y mejorar el flujo a confirmadas."
    )
    return [p1, p2, rec]


def _paras_reservation_origins(mod: AnalyticsModule) -> list[str]:
    bd = _breakdown_stats(mod)
    if not bd:
        return [
            f"Todavía no hay orígenes de reserva registrados en {_period_clause(mod)}.",
            "Sin canal no hay priorización de marketing. Asegúrate de capturar el origen al crear cada reserva.",
        ]
    top = bd["top"]  # type: ignore[assignment]
    by_key = bd["by_key"]  # type: ignore[assignment]
    social = sum(
        by_key[k].raw_value  # type: ignore[index]
        for k in ("whatsapp", "facebook", "instagram")
        if k in by_key
    )
    email = by_key["email"].raw_value if "email" in by_key else 0  # type: ignore[index]
    total = float(bd["total"])
    p1 = (
        f"El canal principal es «{top.label}», con {_fmt(top.raw_value)} reservas "
        f"({_fmt(float(bd['top_share']))}% de {_fmt(total)})."
    )
    p2 = (
        f"Las redes (WhatsApp + Facebook + Instagram) suman {_fmt(social)} "
        f"({_fmt(social / total * 100 if total else 0)}%) y el correo {_fmt(email)} "
        f"({_fmt(email / total * 100 if total else 0)}%). "
    )
    hhi = float(bd["hhi"])
    if hhi >= 2500:
        p2 += "La captación está muy concentrada en pocos canales."
    elif hhi >= 1500:
        p2 += "Hay una concentración moderada entre canales."
    else:
        p2 += "La captación está repartida entre varios orígenes."
    weak = [i for i in bd["ordered"] if i.raw_value > 0]  # type: ignore[union-attr]
    weak_label = weak[-1].label if len(weak) >= 2 else None
    rec = f"Conviene doblar apuesta donde ya conviertes («{top.label}»). " + (
        f"Prueba un impulso corto en «{weak_label}» o mejora "
        "el mensaje ahí para no depender de un solo canal."
        if weak_label and weak_label != top.label
        else "Documenta el origen en cada reserva nueva para afinar el mix."
    )
    return [p1, p2, rec]


def _paras_payment_status(mod: AnalyticsModule) -> list[str]:
    bd = _breakdown_stats(mod)
    if not bd:
        return [
            f"No hay comprobantes en {_period_clause(mod)}.",
            "Sin evidencia de pago no se cierra caja. Pide comprobante al confirmar.",
        ]
    by_key = bd["by_key"]  # type: ignore[assignment]
    open_review = sum(
        by_key[k].raw_value
        for k in ("pending", "received")
        if k in by_key  # type: ignore[index]
    )
    verified = by_key["verified"].raw_value if "verified" in by_key else 0  # type: ignore[index]
    total = float(bd["total"])
    p1 = (
        f"Hay {_fmt(total)} comprobantes en {_period_clause(mod)}. "
        f"El estado más frecuente es «{bd['top'].label}» "
        f"({_fmt(float(bd['top_share']))}%)."
    )
    p2 = (
        f"Pendientes de revisión: {_fmt(open_review)}. "
        f"Tasa verificada: {_fmt(verified / total * 100 if total else 0)}% "
        f"({_fmt(verified)} de {_fmt(total)})."
    )
    rec = (
        "Este panel habla de estado documental, no de montos cobrados. "
        "Vacía primero la cola de recibidos/pendientes para no "
        "bloquear confirmaciones ni salidas."
    )
    return [p1, p2, rec]


def _paras_top_experiences(mod: AnalyticsModule) -> list[str]:
    rk = _ranking_stats(mod)
    if not rk:
        return [
            f"No hay experiencias con reservas confirmadas en {_period_clause(mod)}.",
            "Sin demanda no hay ranking. Revisa captación y disponibilidad de cupos.",
        ]
    top = rk["top"]  # type: ignore[assignment]
    share = top.share_percentage
    p1 = (
        f"«{top.label}» lidera con {top.formatted_value}"
        + (f" ({_fmt(share)}% del top)" if share is not None else "")
        + f" en {_period_clause(mod)}."
    )
    p2 = f"El top muestra {rk['n']} experiencias; promedio {_fmt(float(rk['avg']))} {rk['unit']}."
    second = rk["second"]
    if second is not None:
        p2 += f" La brecha con «{second.label}» es de {_fmt(float(rk['gap']))} {rk['unit']}."
    if float(rk["top3_share"]) >= 70 and int(rk["n"]) >= 3:
        p2 += f" El top 3 concentra {_fmt(float(rk['top3_share']))}% de lo mostrado."
    rec = (
        "Pocas experiencias concentran la demanda confirmada. "
        "Protege cupos y equinos de las líderes, y usa las "
        "siguientes del ranking para campañas o empaquetados que redistribuyan carga."
    )
    return [p1, p2, rec]


def _paras_occupancy(mod: AnalyticsModule) -> list[str]:
    rk = _ranking_stats(mod)
    if not rk:
        return [
            "No hay salidas próximas con cupo para medir ocupación.",
            "Sin salidas programadas no hay presión de cupo. Publica próximas fechas si quieres llenar capacidad.",
        ]
    shares = [r.share_percentage for r in mod.ranking if r.share_percentage is not None]
    avg_occ = sum(shares) / len(shares) if shares else 0.0
    low = sum(1 for s in shares if s < 25)
    mid = sum(1 for s in shares if 25 <= s < 75)
    high = sum(1 for s in shares if s >= 75)
    top = rk["top"]  # type: ignore[assignment]
    p1 = (
        f"Hay {rk['n']} salidas próximas en el radar. "
        f"La de mayor ocupación relativa es «{top.label}»"
        + (f" ({_fmt(top.share_percentage)}%)" if top.share_percentage is not None else "")
        + "."
    )
    p2 = (
        f"Ocupación media: {_fmt(avg_occ)}%. "
        f"Umbrales: baja (<25%) = {low}, media = {mid}, alta (≥75%) = {high}."
    )
    rec = (
        "Las salidas con baja ocupación son oportunidad comercial "
        "inmediata; las muy altas necesitan lista de espera o cupo extra. "
        "Empuja promoción a las de <25% y revisa capacidad en las ≥75%."
    )
    return [p1, p2, rec]


def _paras_top_countries(mod: AnalyticsModule) -> list[str]:
    rk = _ranking_stats(mod)
    if not rk:
        return [
            f"No hay países de visitantes registrados en {_period_clause(mod)}.",
            "Sin origen geográfico no se orienta el mensaje. Completa el país en el registro de participantes.",
        ]
    top = rk["top"]  # type: ignore[assignment]
    p1 = (
        f"El país líder es «{top.label}» con {top.formatted_value}"
        + (f" ({_fmt(top.share_percentage)}%)" if top.share_percentage is not None else "")
        + f" en {_period_clause(mod)}."
    )
    p2 = f"El top incluye {rk['n']} países distintos" + (
        f"; el top 3 concentra {_fmt(float(rk['top3_share']))}%." if int(rk["n"]) >= 3 else "."
    )
    rec = (
        "El mix de países marca idioma, moneda percibida y canales. "
        "Adapta comunicación y horarios al país líder, y prueba "
        "un empujón en el segundo mercado del ranking."
    )
    return [p1, p2, rec]


def _paras_participant_readiness(mod: AnalyticsModule) -> list[str]:
    bd = _breakdown_stats(mod)
    by_key = bd["by_key"] if bd else {}  # type: ignore[assignment]
    pending = by_key["pending"].raw_value if "pending" in by_key else 0  # type: ignore[index]
    total = float(bd["total"]) if bd else float(mod.primary_value.raw if mod.primary_value else 0)
    ready = total - pending if total else 0
    p1 = (
        f"En salidas próximas hay {_fmt(total)} participantes esperados. "
        f"Completos: {_fmt(ready)}; pendientes de registro: {_fmt(pending)}"
        + (f" ({_fmt(pending / total * 100)}%)." if total else ".")
    )
    p2 = (
        "Los pendientes suelen bloquear asignaciones equinas y la lista final de salida."
        if pending > 0
        else "Todos los registros aparecen completos: buen margen operativo."
    )
    rec = (
        "La preparación de participantes es un cuello de botella previo a la salida. "
        "Contacta hoy a quienes faltan datos (documento, contacto, "
        "condiciones) empezando por las salidas más cercanas."
        if pending > 0
        else "La base de participantes está lista. Mantén el checklist 48h antes de cada salida."
    )
    return [p1, p2, rec]


def _paras_equine_availability(mod: AnalyticsModule) -> list[str]:
    bd = _breakdown_stats(mod)
    if not bd:
        return [
            "No hay datos de disponibilidad equina en este momento.",
            "Sin inventario operativo no se planifican asignaciones. Revisa el catálogo equino.",
        ]
    by_key = bd["by_key"]  # type: ignore[assignment]
    available = by_key["available"].raw_value if "available" in by_key else 0  # type: ignore[index]
    total = float(bd["total"])
    p1 = (
        f"Del inventario actual ({_fmt(total)}), hay {_fmt(available)} disponibles "
        f"({_fmt(available / total * 100 if total else 0)}%). "
        f"El estado más frecuente es «{bd['top'].label}»."
    )
    p2 = (
        "Estados como descanso, lesión o mantenimiento reducen el cupo asignable "
        "aunque el animal siga en el catálogo."
    )
    rec = (
        "La disponibilidad real define cuántas salidas puedes cubrir. "
        "Si el disponible es bajo, reprograma cargas o pausa "
        "ventas de salidas con alta demanda equina."
        if total and available / total < 0.4
        else "Hay margen operativo en el inventario. Sigue balanceando carga para no vaciar el disponible."
    )
    return [p1, p2, rec]


def _paras_equine_workload(mod: AnalyticsModule) -> list[str]:
    rk = _ranking_stats(mod)
    if not rk:
        return [
            f"No hay carga equina registrada en {_period_clause(mod)}.",
            "Sin asignaciones no hay fatiga medible. Confirma que las salidas estén asignando equinos.",
        ]
    top = rk["top"]  # type: ignore[assignment]
    p1 = (
        f"«{top.label}» concentra la mayor carga ({top.formatted_value})"
        + (
            f", cerca del {_fmt(top.share_percentage)}% del total mostrado"
            if top.share_percentage is not None
            else ""
        )
        + f" en {_period_clause(mod)}."
    )
    p2 = (
        f"Hay {rk['n']} equinos en el ranking; el top 3 suma "
        f"{_fmt(float(rk['top3_share']))}% de la carga."
        if int(rk["n"]) >= 3
        else f"Hay {rk['n']} equinos con carga registrada."
    )
    concentrated = float(rk["top3_share"]) >= 60 and int(rk["n"]) >= 3
    rec = (
        "La carga está muy concentrada en pocos animales. "
        "Redistribuye próximas asignaciones hacia equinos "
        "con menor participación y revisa descansos del líder."
        if concentrated
        else "La carga se ve relativamente repartida. "
        "Mantén el balance y vigila picos puntuales en el líder."
    )
    return [p1, p2, rec]


def _paras_equine_care_alerts(mod: AnalyticsModule) -> list[str]:
    bd = _breakdown_stats(mod)
    total = float(bd["total"]) if bd else float(mod.primary_value.raw if mod.primary_value else 0)
    if total <= 0:
        return [
            "No hay alertas de cuidados abiertas ahora mismo.",
            "El bienestar programado está al día. Revisa de nuevo antes de cada bloque de salidas.",
        ]
    top = bd["ordered"][0] if bd else None  # type: ignore[index]
    p1 = (
        f"Hay {_fmt(total)} alertas de cuidado activas. "
        + (f"La cola principal es «{top.label}» ({_fmt(top.raw_value)})." if top else "")
    ).strip()
    p2 = (
        "Prioriza cuidados vencidos y animales lesionados antes que los próximos "
        "programados: impactan disponibilidad y seguridad de la salida."
    )
    rec = (
        "Cada alerta abierta reduce capacidad real. "
        "Cierra hoy los vencidos y agenda los próximos para "
        "no chocar con las salidas de mayor ocupación."
    )
    return [p1, p2, rec]


def _paras_generic(mod: AnalyticsModule) -> list[str]:
    parts: list[str] = []
    if mod.insight_text:
        parts.append(mod.insight_text.rstrip(".") + ".")
    if mod.primary_value:
        parts.append(
            f"El valor principal en {_period_clause(mod)} es "
            f"{mod.primary_value.formatted} {mod.primary_value.unit}."
        )
    cmp_ = _cmp_phrase(mod)
    if cmp_:
        parts.append(f"Respecto al periodo anterior: {cmp_}.")
    st = _series_stats(mod)
    if st and int(st["n"]) >= 2:
        parts.append(
            f"La serie muestra promedio {_fmt(float(st['avg']))} "
            f"y rango {_fmt(float(st['min']))}–{_fmt(float(st['max']))}."
        )
    bd = _breakdown_stats(mod)
    if bd:
        parts.append(
            f"El líder del desglose es «{bd['top'].label}» con {_fmt(float(bd['top_share']))}%."
        )
    rk = _ranking_stats(mod)
    if rk:
        parts.append(f"En el ranking lidera «{rk['top'].label}» ({rk['top'].formatted_value}).")
    parts.append(
        "Usa este indicador junto con ocupación, pagos y disponibilidad "
        "equina. Define una acción concreta para la próxima semana "
        "a partir del hallazgo principal."
    )
    # Fold into ~3 paragraphs
    if len(parts) <= 3:
        return parts
    return [
        " ".join(parts[:2]),
        " ".join(parts[2:-1]) if len(parts) > 3 else parts[2],
        parts[-1],
    ]


_BUILDERS = {
    "action_center": _paras_action_center,
    "reservation_trend": _paras_reservation_trend,
    "reservation_status": _paras_reservation_status,
    "reservation_origins": _paras_reservation_origins,
    "confirmed_value_trend": _paras_confirmed_value,
    "payment_status": _paras_payment_status,
    "top_experiences": _paras_top_experiences,
    "occupancy": _paras_occupancy,
    "top_countries": _paras_top_countries,
    "participant_readiness": _paras_participant_readiness,
    "equine_availability": _paras_equine_availability,
    "equine_workload": _paras_equine_workload,
    "equine_care_alerts": _paras_equine_care_alerts,
}


def build_rich_analysis(mod: AnalyticsModule) -> list[str]:
    """Return 3–4 conversational paragraphs with findings and recommendations."""
    early = _empty_or_error(mod)
    if early is not None:
        return early

    builder = _BUILDERS.get(mod.id, _paras_generic)
    paragraphs = [p.strip() for p in builder(mod) if p and p.strip()]
    # Cap at 4 paragraphs; merge extras into the last body paragraph.
    if len(paragraphs) > 4:
        head, tail = paragraphs[:3], paragraphs[3:]
        paragraphs = [*head[:-1], f"{head[-1]} {' '.join(tail[:-1])}".strip(), tail[-1]]
    return paragraphs[:4]


def analysis_parameter_rows(mod: AnalyticsModule) -> list[tuple[str, str]]:
    """Key/value snapshot for export and detail sheet — plain language labels."""
    rows: list[tuple[str, str]] = []
    if mod.primary_value:
        rows.append(("Valor", f"{mod.primary_value.formatted} {mod.primary_value.unit}".strip()))
    if mod.comparison and mod.comparison.percentage_delta is not None:
        sign = "+" if mod.comparison.percentage_delta > 0 else ""
        rows.append(
            ("Cambio vs periodo anterior", f"{sign}{_fmt(mod.comparison.percentage_delta)}%")
        )
    if mod.comparison and mod.comparison.absolute_formatted:
        rows.append(("Cambio absoluto", mod.comparison.absolute_formatted))

    if mod.series and mod.series[0].points:
        vals = [p.raw for p in mod.series[0].points]
        rows.append(("Tramos en la serie", str(len(vals))))
        rows.append(("Mínimo / máximo", f"{_fmt(min(vals))} / {_fmt(max(vals))}"))
        avg = sum(vals) / len(vals)
        rows.append(("Promedio", _fmt(avg)))
        if len(vals) >= 3 and avg:
            cv = float(pstdev(vals)) / avg * 100
            rows.append(("Variabilidad", f"{_fmt(cv)}%"))
        if len(vals) >= 4:
            mid = len(vals) // 2
            a1 = sum(vals[:mid]) / mid
            a2 = sum(vals[mid:]) / (len(vals) - mid)
            if a1:
                rows.append(
                    (
                        "2ª mitad vs 1ª",
                        f"{'+' if a2 >= a1 else ''}{_fmt((a2 - a1) / abs(a1) * 100)}%",
                    )
                )

    if mod.breakdown:
        total = sum(i.raw_value for i in mod.breakdown) or 0.0
        rows.append(("Categorías", str(len(mod.breakdown))))
        rows.append(("Total del desglose", _fmt(total)))
        top = max(mod.breakdown, key=lambda i: i.raw_value)
        sh = _share(top.share_percentage, top.raw_value, total)
        rows.append(("Líder", f"{top.label} ({_fmt(sh) if sh is not None else '—'}%)"))
        if total and len(mod.breakdown) >= 2:
            ordered = sorted(mod.breakdown, key=lambda i: i.raw_value, reverse=True)
            top2 = sum(i.raw_value for i in ordered[:2]) / total * 100
            rows.append(("Peso de los 2 líderes", f"{_fmt(top2)}%"))
            shares = [i.raw_value / total for i in mod.breakdown]
            hhi = sum(s * s for s in shares) * 10000
            if hhi >= 2500:
                conc = "alta"
            elif hhi >= 1500:
                conc = "moderada"
            else:
                conc = "dispersa"
            rows.append(("Concentración", conc))

        by_key = {i.key: i for i in mod.breakdown}
        if mod.id == "reservation_origins":
            social = sum(
                by_key[k].raw_value for k in ("whatsapp", "facebook", "instagram") if k in by_key
            )
            if total:
                rows.append(("Redes (WA+FB+IG)", f"{_fmt(social)} ({_fmt(social / total * 100)}%)"))
        elif mod.id == "payment_status":
            open_review = sum(by_key[k].raw_value for k in ("pending", "received") if k in by_key)
            verified = by_key["verified"].raw_value if "verified" in by_key else 0
            rows.append(("Por revisar", _fmt(open_review)))
            if total:
                rows.append(("Tasa verificada", f"{_fmt(verified / total * 100)}%"))
        elif mod.id == "participant_readiness":
            pending = by_key["pending"].raw_value if "pending" in by_key else 0
            rows.append(("Pendientes de registro", _fmt(pending)))
        elif mod.id == "equine_availability":
            available = by_key["available"].raw_value if "available" in by_key else 0
            if total:
                rows.append(
                    ("Disponibles", f"{_fmt(available)} ({_fmt(available / total * 100)}%)")
                )
        elif mod.id in ("action_center", "equine_care_alerts"):
            rows.append(("Ítems abiertos", _fmt(total)))

    if mod.ranking:
        rows.append(("Elementos en el ranking", str(len(mod.ranking))))
        top = mod.ranking[0]
        rows.append(("#1", top.label))
        if top.share_percentage is not None:
            rows.append(("Participación del #1", f"{_fmt(top.share_percentage)}%"))
        if len(mod.ranking) >= 2:
            gap = top.raw_value - mod.ranking[1].raw_value
            rows.append(("Brecha #1 vs #2", _fmt(gap)))
        if len(mod.ranking) >= 3:
            total = sum(i.raw_value for i in mod.ranking) or 0.0
            if total:
                top3 = sum(i.raw_value for i in mod.ranking[:3]) / total * 100
                rows.append(("Peso del top 3", f"{_fmt(top3)}%"))
        if mod.id == "occupancy":
            shares = [r.share_percentage for r in mod.ranking if r.share_percentage is not None]
            if shares:
                rows.append(("Ocupación media", f"{_fmt(sum(shares) / len(shares))}%"))
                rows.append(("Salidas <25%", str(sum(1 for s in shares if s < 25))))
                rows.append(("Salidas ≥75%", str(sum(1 for s in shares if s >= 75))))

    rows.append(("Periodo", mod.period.label if mod.period else "—"))
    return rows
