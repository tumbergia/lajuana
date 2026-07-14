"""Server-side XLSX export for analytics dashboard (business-facing sheets)."""

from __future__ import annotations

from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import Any

from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.table import Table, TableStyleInfo

from app.core.time import APP_TIMEZONE_NAME, now_colombia
from app.schemas.analytics_v2 import ANALYTICS_SCHEMA_VERSION, DashboardResponse

# Forbidden technical terms on visible sheets (regression guard).
FORBIDDEN_VISIBLE_TERMS = (
    "module_id",
    "series_id",
    "schema_version",
    "query_key",
    "trace_id",
    "payload",
    "cache_age_seconds",
    "enum",
)

_HEADER_FILL = PatternFill(start_color="1A1C1C", end_color="1A1C1C", fill_type="solid")
_HEADER_FONT = Font(bold=True, color="FFFFFF")
_MAX_COL_WIDTH = 48


def _logo_candidates() -> list[Path]:
    root = Path(__file__).resolve().parents[4]  # repo root from apps/api/app/services
    return [
        root / "apps" / "mobile" / "assets" / "branding" / "lajuana.svg",
        root / "apps" / "mobile" / "assets" / "branding" / "splash_logo.png",
        root / "apps" / "mobile" / "assets" / "branding" / "lajuana-banner.svg",
    ]


def _set_widths(ws: Any, widths: list[float]) -> None:
    for idx, width in enumerate(widths, start=1):
        ws.column_dimensions[get_column_letter(idx)].width = min(width, _MAX_COL_WIDTH)


def _style_header(ws: Any, row: int = 1) -> None:
    for cell in ws[row]:
        cell.font = _HEADER_FONT
        cell.fill = _HEADER_FILL
        cell.alignment = Alignment(vertical="center")


def _try_table(ws: Any, name: str, ref: str) -> None:
    try:
        table = Table(displayName=name, ref=ref)
        table.tableStyleInfo = TableStyleInfo(
            name="TableStyleMedium2",
            showFirstColumn=False,
            showLastColumn=False,
            showRowStripes=True,
            showColumnStripes=False,
        )
        ws.add_table(table)
    except Exception:
        # Tables are enhancement; never fail export.
        pass


class AnalyticsExportService:
    def export_dashboard(
        self,
        dashboard: DashboardResponse,
        *,
        generated_by: str,
        include_logo: bool = True,
    ) -> tuple[bytes, str]:
        wb = Workbook()

        self._write_resumen(wb, dashboard, generated_by=generated_by, include_logo=include_logo)
        self._write_indicadores(wb, dashboard)
        self._write_tendencias(wb, dashboard)
        self._write_desgloses(wb, dashboard)
        self._write_hidden_meta(wb, dashboard, generated_by=generated_by)

        # Document properties (technical metadata, not visible sheet)
        try:
            wb.properties.title = "Reporte de analítica — La Juana"
            wb.properties.creator = generated_by
            wb.properties.description = (
                f"schema={ANALYTICS_SCHEMA_VERSION};"
                f"period={dashboard.period.start.isoformat()}..{dashboard.period.end.isoformat()}"
            )
        except Exception:
            pass

        buf = BytesIO()
        wb.save(buf)
        buf.seek(0)
        data = buf.getvalue()

        stamp = now_colombia().strftime("%Y%m%d_%H%M")
        filename = (
            f"analitica_{dashboard.period.start.isoformat()}_"
            f"{dashboard.period.end.isoformat()}_{stamp}.xlsx"
        )
        return data, filename

    def _write_resumen(
        self,
        wb: Workbook,
        dashboard: DashboardResponse,
        *,
        generated_by: str,
        include_logo: bool,
    ) -> None:
        ws = wb.active
        ws.title = "Resumen"
        ws.append(["Reporte de analítica — La Juana"])
        ws.append(["Periodo", dashboard.period.label])
        ws.append(
            [
                "Desde",
                dashboard.period.start.isoformat(),
                "Hasta",
                dashboard.period.end.isoformat(),
            ]
        )
        local_now = now_colombia()
        ws.append(
            [
                "Elaborado",
                local_now.strftime("%d/%m/%Y %H:%M"),
                "Zona",
                APP_TIMEZONE_NAME.replace("_", " "),
            ]
        )
        ws.append(["Elaborado por", generated_by])
        ws.append([])
        ws.append(["Principales cifras"])
        for mod in dashboard.modules[:8]:
            if mod.primary_value is None:
                continue
            ws.append(
                [
                    mod.title,
                    mod.primary_value.formatted,
                    mod.primary_value.unit,
                    mod.insight_text or "",
                ]
            )
        ws.append([])
        ws.append(["Conclusiones"])
        for mod in dashboard.modules:
            if mod.insight_text:
                ws.append([mod.title, mod.insight_text])

        if include_logo:
            for candidate in _logo_candidates():
                if not candidate.exists():
                    continue
                if candidate.suffix.lower() == ".svg":
                    # openpyxl does not embed SVG reliably; skip, try png
                    continue
                try:
                    from openpyxl.drawing.image import Image as XLImage

                    img = XLImage(str(candidate))
                    img.width = 120
                    img.height = 40
                    ws.add_image(img, "F1")
                    break
                except Exception:
                    continue

        _set_widths(ws, [36, 24, 18, 64])

    def _write_indicadores(self, wb: Workbook, dashboard: DashboardResponse) -> None:
        ws = wb.create_sheet("Indicadores")
        headers = [
            "Categoría",
            "Indicador",
            "Periodo",
            "Valor",
            "Unidad",
            "Comparación",
            "Variación",
        ]
        ws.append(headers)
        _style_header(ws)
        for mod in dashboard.modules:
            pv = mod.primary_value
            cmp_label = mod.comparison.label if mod.comparison else ""
            variation = ""
            if mod.comparison and mod.comparison.percentage_delta is not None:
                variation = f"{mod.comparison.percentage_delta} %"
            elif mod.comparison and mod.comparison.absolute_formatted:
                variation = mod.comparison.absolute_formatted
            ws.append(
                [
                    mod.category.value if hasattr(mod.category, "value") else str(mod.category),
                    mod.title,
                    mod.period.label,
                    pv.raw if pv else None,
                    pv.unit if pv else "",
                    cmp_label,
                    variation,
                ]
            )
        # Format category as business label (map raw enum values to Spanish)
        cat_labels = {
            "action": "Atención",
            "reservations": "Reservas",
            "money": "Dinero",
            "experiences": "Experiencias",
            "participants": "Participantes",
            "equines": "Equinos",
            "operations": "Operación",
        }
        for row in ws.iter_rows(min_row=2, min_col=1, max_col=1):
            cell = row[0]
            cell.value = cat_labels.get(str(cell.value), cell.value)

        last = max(ws.max_row, 2)
        _try_table(ws, "IndicadoresTabla", f"A1:G{last}")
        ws.auto_filter.ref = f"A1:G{last}"
        ws.freeze_panes = "A2"
        _set_widths(ws, [16, 32, 22, 14, 14, 40, 16])

    def _write_tendencias(self, wb: Workbook, dashboard: DashboardResponse) -> None:
        ws = wb.create_sheet("Tendencias")
        headers = ["Indicador", "Fecha o periodo", "Valor", "Unidad"]
        ws.append(headers)
        _style_header(ws)
        for mod in dashboard.modules:
            for series in mod.series:
                for point in series.points:
                    ws.append(
                        [
                            mod.title,
                            point.label,
                            point.raw,
                            point.unit or series.unit,
                        ]
                    )
        last = max(ws.max_row, 2)
        _try_table(ws, "TendenciasTabla", f"A1:D{last}")
        ws.auto_filter.ref = f"A1:D{last}"
        ws.freeze_panes = "A2"
        _set_widths(ws, [32, 22, 14, 14])

    def _write_desgloses(self, wb: Workbook, dashboard: DashboardResponse) -> None:
        ws = wb.create_sheet("Desgloses")
        headers = [
            "Indicador",
            "Categoría",
            "Nombre",
            "Cantidad",
            "Participación",
            "Posición",
        ]
        ws.append(headers)
        _style_header(ws)
        for mod in dashboard.modules:
            for item in mod.breakdown:
                ws.append(
                    [
                        mod.title,
                        item.dimension,
                        item.label,
                        item.raw_value,
                        item.share_percentage,
                        item.rank,
                    ]
                )
            for item in mod.ranking:
                ws.append(
                    [
                        mod.title,
                        "ranking",
                        item.label,
                        item.raw_value,
                        item.share_percentage,
                        item.rank,
                    ]
                )
        # Soften technical dimension keys on visible sheet
        dim_labels = {
            "status": "Estado",
            "payment_status": "Estado del comprobante",
            "operational_status": "Estado operacional",
            "attention": "Atención",
            "readiness": "Preparación",
            "care": "Cuidado",
            "ranking": "Posición",
        }
        for row in ws.iter_rows(min_row=2, min_col=2, max_col=2):
            cell = row[0]
            cell.value = dim_labels.get(str(cell.value), cell.value)

        last = max(ws.max_row, 2)
        _try_table(ws, "DesglosesTabla", f"A1:F{last}")
        ws.auto_filter.ref = f"A1:F{last}"
        ws.freeze_panes = "A2"
        _set_widths(ws, [32, 22, 28, 12, 14, 10])

    def _write_hidden_meta(
        self,
        wb: Workbook,
        dashboard: DashboardResponse,
        *,
        generated_by: str,
    ) -> None:
        ws = wb.create_sheet("_sistema")
        ws.sheet_state = "hidden"
        ws.append(["clave", "valor"])
        ws.append(["schema_version", ANALYTICS_SCHEMA_VERSION])
        ws.append(["report_version", 1])
        ws.append(["generated_at", dashboard.generated_at.isoformat()])
        ws.append(["timezone", APP_TIMEZONE_NAME])
        ws.append(["generated_by", generated_by])
        ws.append(
            [
                "filters",
                (
                    f"range={dashboard.period.preset};"
                    f"from={dashboard.period.start};to={dashboard.period.end}"
                ),
            ]
        )
        for mod in dashboard.modules:
            ws.append([f"module:{mod.id}", mod.status.value])

    @staticmethod
    def visible_sheet_names(data: bytes) -> list[str]:
        wb = load_workbook(BytesIO(data))
        return [name for name in wb.sheetnames if not name.startswith("_")]

    @staticmethod
    def assert_no_forbidden_terms_in_visible(data: bytes) -> list[str]:
        """Return list of forbidden hits found in visible sheets (empty = ok)."""
        wb = load_workbook(BytesIO(data), data_only=False)
        hits: list[str] = []
        for name in wb.sheetnames:
            ws = wb[name]
            if getattr(ws, "sheet_state", "visible") == "hidden" or name.startswith("_"):
                continue
            for row in ws.iter_rows(values_only=True):
                for cell in row:
                    if cell is None:
                        continue
                    text = str(cell)
                    for term in FORBIDDEN_VISIBLE_TERMS:
                        if term in text:
                            hits.append(f"{name}:{term}")
        return hits
