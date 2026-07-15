"""Deterministic multi-parameter analysis for analytics modules.

Used by XLSX export (and mirrored on mobile for the detail sheet).
Each visualization / module id contributes extra quantitative parameters
beyond the single-line insight_text.
"""

from __future__ import annotations

from statistics import median, pstdev

from app.schemas.analytics_v2 import AnalyticsModule, VisualizationType


def _fmt(n: float, *, digits: int = 1) -> str:
    if abs(n - round(n)) < 1e-9:
        return str(int(round(n)))
    return f"{n:.{digits}f}"


def _unit_of(mod: AnalyticsModule, fallback: str = "") -> str:
    if mod.primary_value and mod.primary_value.unit:
        return mod.primary_value.unit
    if mod.series and mod.series[0].unit:
        return mod.series[0].unit
    return fallback


def _dedupe(lines: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for line in lines:
        text = (line or "").strip()
        if not text or text in seen:
            continue
        seen.add(text)
        out.append(text)
    return out


def _comparison_lines(mod: AnalyticsModule) -> list[str]:
    lines: list[str] = []
    cmp_ = mod.comparison
    if not cmp_:
        return lines
    if cmp_.label:
        lines.append(f"Comparación: {cmp_.label}.")
    if cmp_.percentage_delta is not None:
        sign = "+" if cmp_.percentage_delta > 0 else ""
        lines.append(
            f"Variación porcentual: {sign}{_fmt(cmp_.percentage_delta)}%."
        )
    if cmp_.absolute_formatted:
        lines.append(f"Cambio absoluto: {cmp_.absolute_formatted}.")
    if cmp_.previous_formatted or cmp_.previous_raw is not None:
        prev = cmp_.previous_formatted or _fmt(cmp_.previous_raw or 0)
        lines.append(f"Periodo anterior: {prev}.")
    if not cmp_.sufficient_sample:
        lines.append(
            "Muestra del periodo anterior limitada: la variación se interpreta con cautela."
        )
    return lines


def _series_lines(mod: AnalyticsModule) -> list[str]:
    lines: list[str] = []
    for series in mod.series:
        if not series.points:
            continue
        values = [p.raw for p in series.points]
        n = len(values)
        total = sum(values)
        mn, mx = min(values), max(values)
        avg = total / n
        med = float(median(values))
        unit = series.unit or _unit_of(mod)
        u = f" {unit}" if unit else ""
        peak = max(series.points, key=lambda p: p.raw)
        trough = min(series.points, key=lambda p: p.raw)

        lines.append(
            f"{series.label}: n={n} periodos, suma={_fmt(total)}{u}, "
            f"promedio={_fmt(avg)}{u}, mediana={_fmt(med)}{u}."
        )
        lines.append(
            f"Rango: mínimo {_fmt(mn)}{u} ({trough.label}) → "
            f"máximo {_fmt(mx)}{u} ({peak.label}); amplitud {_fmt(mx - mn)}{u}."
        )
        if n >= 3:
            sd = float(pstdev(values))
            cv = (sd / avg * 100) if avg else 0.0
            lines.append(
                f"Dispersión: desvío estándar {_fmt(sd)}{u} "
                f"(coef. variación {_fmt(cv)}%)."
            )

        zeros = sum(1 for v in values if v == 0)
        if zeros:
            lines.append(f"Periodos en cero: {zeros} de {n} ({round(zeros / n * 100)}%).")

        first, last = values[0], values[-1]
        if first != 0:
            delta_pct = (last - first) / abs(first) * 100
            sign = "+" if delta_pct > 0 else ""
            lines.append(
                f"Inicio→fin: {_fmt(first)} → {_fmt(last)}{u} "
                f"({sign}{_fmt(delta_pct)}%)."
            )
        else:
            lines.append(f"Inicio→fin: {_fmt(first)} → {_fmt(last)}{u}.")

        # Simple trend: compare first half avg vs second half avg
        if n >= 4:
            mid = n // 2
            a1 = sum(values[:mid]) / mid
            a2 = sum(values[mid:]) / (n - mid)
            if a1 == 0 and a2 == 0:
                lines.append("Tendencia: estable en cero.")
            elif a1 == 0:
                lines.append("Tendencia: aceleración desde periodos iniciales en cero.")
            else:
                half_pct = (a2 - a1) / abs(a1) * 100
                if abs(half_pct) < 5:
                    lines.append("Tendencia: relativamente estable entre mitades del periodo.")
                elif half_pct > 0:
                    lines.append(
                        f"Tendencia alcista: segunda mitad {_fmt(half_pct)}% por encima de la primera."
                    )
                else:
                    lines.append(
                        f"Tendencia bajista: segunda mitad {_fmt(abs(half_pct))}% por debajo de la primera."
                    )

        # Longest run of non-decreasing
        if n >= 3:
            best_up = best_down = cur_up = cur_down = 1
            for i in range(1, n):
                if values[i] >= values[i - 1]:
                    cur_up += 1
                    best_up = max(best_up, cur_up)
                else:
                    cur_up = 1
                if values[i] <= values[i - 1]:
                    cur_down += 1
                    best_down = max(best_down, cur_down)
                else:
                    cur_down = 1
            if best_up >= 3:
                lines.append(f"Racha alcista más larga: {best_up} periodos consecutivos.")
            if best_down >= 3:
                lines.append(f"Racha bajista más larga: {best_down} periodos consecutivos.")

        if mod.id == "confirmed_value_trend" and total > 0:
            lines.append(
                f"Ingresos comprometidos acumulados en el periodo: {_fmt(total)}{u}."
            )
        if mod.id == "reservation_trend" and total > 0:
            lines.append(
                f"Reservas nuevas acumuladas: {_fmt(total)}{u} "
                f"(~{_fmt(avg)} por periodo)."
            )
    return lines


def _share(item_share: float | None, raw: float, total: float) -> float | None:
    if item_share is not None:
        return item_share
    if total > 0:
        return round(raw / total * 100, 1)
    return None


def _breakdown_lines(mod: AnalyticsModule) -> list[str]:
    items = list(mod.breakdown)
    if not items:
        return []
    lines: list[str] = []
    total = sum(i.raw_value for i in items) or 0.0
    n = len(items)
    unit = items[0].unit or _unit_of(mod, "reservas")
    ordered = sorted(items, key=lambda i: -i.raw_value)
    top = ordered[0]
    bottom = ordered[-1]
    top_share = _share(top.share_percentage, top.raw_value, total)
    bot_share = _share(bottom.share_percentage, bottom.raw_value, total)

    lines.append(f"Categorías: {n}; total={_fmt(total)} {unit}.")
    if top_share is not None:
        lines.append(
            f"Líder: {top.label} = {_fmt(top.raw_value)} {unit} ({_fmt(top_share)}%)."
        )
    if n >= 2 and bot_share is not None and bottom.key != top.key:
        lines.append(
            f"Menor: {bottom.label} = {_fmt(bottom.raw_value)} {unit} ({_fmt(bot_share)}%)."
        )

    if n >= 2 and total:
        top2 = sum(i.raw_value for i in ordered[:2])
        conc = round(top2 / total * 100, 1)
        lines.append(f"Concentración top-2: {_fmt(conc)}% del total.")
        # Herfindahl-Hirschman (0-10000 scale on percentage shares)
        shares = [(i.raw_value / total) for i in items if total]
        hhi = sum(s * s for s in shares) * 10000
        if hhi >= 2500:
            lines.append(f"Índice de concentración (HHI) {_fmt(hhi, digits=0)}: mercado concentrado.")
        elif hhi >= 1500:
            lines.append(f"Índice de concentración (HHI) {_fmt(hhi, digits=0)}: concentración moderada.")
        else:
            lines.append(f"Índice de concentración (HHI) {_fmt(hhi, digits=0)}: distribución dispersa.")

        if top_share is not None and top_share < 40:
            lines.append("Ninguna categoría supera el 40%: mix relativamente equilibrado.")

    # Module-specific
    keys = {i.key: i for i in items}
    if mod.id == "reservation_origins":
        social = sum(
            keys[k].raw_value
            for k in ("whatsapp", "facebook", "instagram")
            if k in keys
        )
        email = keys["email"].raw_value if "email" in keys else 0.0
        if total:
            lines.append(
                f"Redes sociales (WA+FB+IG): {_fmt(social)} ({_fmt(social / total * 100)}%); "
                f"correo: {_fmt(email)} ({_fmt(email / total * 100)}%)."
            )
        for channel in ("whatsapp", "instagram", "facebook", "email"):
            if channel in keys and keys[channel].raw_value > 0:
                it = keys[channel]
                sh = _share(it.share_percentage, it.raw_value, total)
                if sh is not None:
                    lines.append(f"  · {it.label}: {_fmt(it.raw_value)} ({_fmt(sh)}%).")

    elif mod.id == "reservation_status":
        active = sum(
            keys[k].raw_value
            for k in (
                "contact",
                "quoted",
                "pending_payment",
                "payment_received",
                "confirmed",
                "pre_reserved",
            )
            if k in keys
        )
        closed = sum(
            keys[k].raw_value
            for k in ("cancelled", "expired", "completed")
            if k in keys
        )
        if total:
            lines.append(
                f"Pipeline activo: {_fmt(active)} ({_fmt(active / total * 100)}%); "
                f"cerradas/completadas: {_fmt(closed)} ({_fmt(closed / total * 100)}%)."
            )
        risk = sum(
            keys[k].raw_value
            for k in ("pending_payment", "payment_received")
            if k in keys
        )
        if risk and total:
            lines.append(
                f"Pendientes de cobro/verificación: {_fmt(risk)} ({_fmt(risk / total * 100)}%)."
            )

    elif mod.id == "payment_status":
        pending = keys.get("pending") or keys.get("received")
        verified = keys.get("verified")
        rejected = keys.get("rejected")
        if verified and total:
            lines.append(
                f"Tasa verificada: {_fmt(verified.raw_value / total * 100)}% "
                f"({_fmt(verified.raw_value)} de {_fmt(total)})."
            )
        if rejected and total:
            lines.append(
                f"Rechazados: {_fmt(rejected.raw_value)} ({_fmt(rejected.raw_value / total * 100)}%)."
            )
        open_review = sum(
            keys[k].raw_value for k in ("pending", "received") if k in keys
        )
        if open_review:
            lines.append(f"Comprobantes por revisar: {_fmt(open_review)}.")

    elif mod.id == "participant_readiness":
        pending = keys.get("pending")
        completed = keys.get("completed")
        if pending and total:
            lines.append(
                f"Pendientes de registro: {_fmt(pending.raw_value)} "
                f"({_fmt(pending.raw_value / total * 100)}%)."
            )
        if completed and total:
            lines.append(
                f"Listos: {_fmt(completed.raw_value)} "
                f"({_fmt(completed.raw_value / total * 100)}%)."
            )

    elif mod.id == "equine_availability":
        available = keys.get("available")
        blocked = sum(
            keys[k].raw_value
            for k in ("injured", "retired", "unavailable", "restricted", "resting")
            if k in keys
        )
        if available and total:
            lines.append(
                f"Disponibles: {_fmt(available.raw_value)} "
                f"({_fmt(available.raw_value / total * 100)}%)."
            )
        if blocked and total:
            lines.append(
                f"No asignables ahora: {_fmt(blocked)} "
                f"({_fmt(blocked / total * 100)}%)."
            )

    elif mod.id in ("action_center", "equine_care_alerts"):
        open_total = total
        lines.append(f"Ítems abiertos: {_fmt(open_total)}.")
        if ordered:
            lines.append(
                f"Cola principal: {ordered[0].label} ({_fmt(ordered[0].raw_value)})."
            )
        if n >= 2:
            lines.append(
                f"Segunda cola: {ordered[1].label} ({_fmt(ordered[1].raw_value)})."
            )

    return lines


def _ranking_lines(mod: AnalyticsModule) -> list[str]:
    items = list(mod.ranking)
    if not items:
        return []
    lines: list[str] = []
    n = len(items)
    values = [i.raw_value for i in items]
    total = sum(values) or 0.0
    avg = total / n if n else 0.0
    unit = items[0].unit or _unit_of(mod)
    top = items[0]

    lines.append(f"Elementos en ranking: {n}; promedio={_fmt(avg)} {unit}.")
    share = top.share_percentage
    if share is not None:
        lines.append(
            f"Líder: {top.label} = {top.formatted_value}"
            f"{(' ' + unit) if unit and unit not in top.formatted_value else ''} "
            f"({_fmt(share)}%)."
        )
    else:
        lines.append(f"Líder: {top.label} = {top.formatted_value}.")

    if n >= 2:
        second = items[1]
        gap = top.raw_value - second.raw_value
        gap_pct = (gap / top.raw_value * 100) if top.raw_value else 0.0
        lines.append(
            f"Brecha #1 vs #2: {_fmt(gap)} {unit} "
            f"({_fmt(gap_pct)}% del líder) — {second.label}."
        )

    if n >= 3:
        top3 = sum(i.raw_value for i in items[:3])
        if total:
            lines.append(f"Top 3 concentran {_fmt(top3 / total * 100)}% del total mostrado.")
        shares = [i.share_percentage for i in items[:3] if i.share_percentage is not None]
        if shares:
            lines.append(f"Suma de participación top 3: {_fmt(sum(shares))}%.")

    if mod.id == "occupancy":
        shares = [i.share_percentage for i in items if i.share_percentage is not None]
        if shares:
            avg_occ = sum(shares) / len(shares)
            lines.append(f"Ocupación media de salidas: {_fmt(avg_occ)}%.")
            low = [r for r in items if (r.share_percentage or 0) < 25]
            mid = [r for r in items if 25 <= (r.share_percentage or 0) < 75]
            high = [r for r in items if (r.share_percentage or 0) >= 75]
            lines.append(
                f"Umbrales: baja(<25%)={len(low)}, media={len(mid)}, alta(≥75%)={len(high)}."
            )
            if low:
                lines.append(
                    "Salidas bajas: "
                    + ", ".join(r.label for r in low[:4])
                    + ("…" if len(low) > 4 else "")
                    + "."
                )
            if high:
                lines.append(
                    "Casi llenas: "
                    + ", ".join(r.label for r in high[:4])
                    + ("…" if len(high) > 4 else "")
                    + "."
                )

    elif mod.id == "top_countries":
        lines.append(f"Países distintos en el top: {n}.")
        if top.country_code:
            lines.append(f"Código ISO del líder: {top.country_code}.")
        if n >= 2 and total:
            lines.append(
                f"Diversidad: el líder pesa {_fmt((top.share_percentage or top.raw_value / total * 100))}%; "
                f"resto {_fmt(100 - (top.share_percentage or top.raw_value / total * 100))}%."
            )

    elif mod.id == "top_experiences":
        if total:
            lines.append(
                f"Reservas confirmadas en el top: {_fmt(total)} {unit}."
            )
        if n >= 2 and top.raw_value:
            lines.append(
                f"{top.label} supera a {items[1].label} por "
                f"{_fmt(top.raw_value - items[1].raw_value)} {unit}."
            )

    elif mod.id == "equine_workload":
        if total:
            lines.append(f"Carga total asignada: {_fmt(total)} {unit}.")
        if n >= 3 and total:
            top3 = sum(i.raw_value for i in items[:3])
            lines.append(
                f"Concentración en 3 equinos: {_fmt(top3 / total * 100)}%."
            )
        overloaded = [i for i in items if i.share_percentage and i.share_percentage >= 20]
        if overloaded:
            lines.append(
                f"Equinos con ≥20% de la carga: {len(overloaded)} "
                f"({', '.join(i.label for i in overloaded[:3])})."
            )

    return lines


def build_rich_analysis(mod: AnalyticsModule) -> list[str]:
    """Return multi-line deterministic analysis with extra parameters per metric."""
    lines: list[str] = []
    if mod.insight_text:
        lines.append(mod.insight_text)

    if mod.primary_value:
        lines.append(
            f"Valor principal: {mod.primary_value.formatted} {mod.primary_value.unit}."
        )

    lines.extend(_comparison_lines(mod))

    viz = mod.visualization
    if mod.series and viz in (
        VisualizationType.LINE,
        VisualizationType.SPARKLINE,
        VisualizationType.KPI,
    ):
        lines.extend(_series_lines(mod))
    elif mod.series and not mod.breakdown and not mod.ranking:
        lines.extend(_series_lines(mod))

    if mod.breakdown:
        lines.extend(_breakdown_lines(mod))

    if mod.ranking:
        lines.extend(_ranking_lines(mod))

    if mod.status and mod.status.value != "ok":
        lines.append(f"Estado del indicador: {mod.status.value}.")
    if mod.empty_message and mod.status and mod.status.value == "empty":
        lines.append(mod.empty_message)

    # Period context
    if mod.period:
        lines.append(
            f"Periodo analizado: {mod.period.label} "
            f"({mod.period.start.isoformat()} → {mod.period.end.isoformat()})."
        )

    return _dedupe(lines)


def analysis_parameter_rows(mod: AnalyticsModule) -> list[tuple[str, str]]:
    """Optional key/value parameter table for export sheets."""
    rows: list[tuple[str, str]] = []
    if mod.primary_value:
        rows.append(("Valor", f"{mod.primary_value.formatted} {mod.primary_value.unit}".strip()))
    if mod.comparison and mod.comparison.percentage_delta is not None:
        sign = "+" if mod.comparison.percentage_delta > 0 else ""
        rows.append(("Δ %", f"{sign}{_fmt(mod.comparison.percentage_delta)}%"))
    if mod.comparison and mod.comparison.absolute_formatted:
        rows.append(("Δ absoluto", mod.comparison.absolute_formatted))
    if mod.series and mod.series[0].points:
        vals = [p.raw for p in mod.series[0].points]
        rows.append(("Puntos", str(len(vals))))
        rows.append(("Mín / Máx", f"{_fmt(min(vals))} / {_fmt(max(vals))}"))
        rows.append(("Promedio", _fmt(sum(vals) / len(vals))))
        if len(vals) >= 3:
            rows.append(("Desvío std", _fmt(float(pstdev(vals)))))
    if mod.breakdown:
        total = sum(i.raw_value for i in mod.breakdown) or 0.0
        rows.append(("Categorías", str(len(mod.breakdown))))
        rows.append(("Total desglose", _fmt(total)))
        top = max(mod.breakdown, key=lambda i: i.raw_value)
        sh = _share(top.share_percentage, top.raw_value, total)
        rows.append(("Líder", f"{top.label} ({_fmt(sh) if sh is not None else '—'}%)"))
        if total and len(mod.breakdown) >= 2:
            shares = [(i.raw_value / total) for i in mod.breakdown]
            hhi = sum(s * s for s in shares) * 10000
            rows.append(("HHI", _fmt(hhi, digits=0)))
    if mod.ranking:
        rows.append(("Filas ranking", str(len(mod.ranking))))
        top = mod.ranking[0]
        rows.append(("#1", top.label))
        if top.share_percentage is not None:
            rows.append(("#1 participación", f"{_fmt(top.share_percentage)}%"))
        if len(mod.ranking) >= 2:
            gap = top.raw_value - mod.ranking[1].raw_value
            rows.append(("Brecha #1-#2", _fmt(gap)))
        if mod.id == "occupancy":
            shares = [r.share_percentage for r in mod.ranking if r.share_percentage is not None]
            if shares:
                rows.append(("Ocupación media", f"{_fmt(sum(shares) / len(shares))}%"))
    rows.append(("Periodo", mod.period.label if mod.period else "—"))
    return rows
