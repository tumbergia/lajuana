#!/usr/bin/env python3
"""
Audit completo de tools del asistente AI de La Juana.

Verifica que todas las tools estén correctamente protegidas por canal,
que la validación de argumentos funcione, y que no haya herramientas
sin registrar o con permisos incorrectos.

Uso:
    python scripts/audit_tools.py                          # Ejecuta auditoria y guarda log auto
    python scripts/audit_tools.py --verbose                # Muestra detalles extra
    python scripts/audit_tools.py --report reporte.json    # Guarda reporte en ruta custom
    python scripts/audit_tools.py --log-dir ./logs         # Cambia directorio de logs
    python scripts/audit_tools.py --no-log                 # No guarda log automático
"""

from __future__ import annotations

import argparse
import datetime
import json
import platform
import sys
import time
from pathlib import Path

# Agregar apps/api al path para imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "apps" / "api"))

from app.ai.assistant.policy import ToolPolicyDecision, ToolPolicyEngine  # noqa: E402
from app.schemas.assistant_plan import AssistantAction, AssistantPlan, RiskLevel, ToolArgs  # noqa: E402


class Colors:
    """Códigos ANSI para terminal (duplicado en admin_e2e_test.py — mantener sincronizado)."""

    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RESET = "\033[0m"


class ToolAuditRunner:
    """Ejecuta escenarios de auditoría y reporta resultados."""

    def __init__(self, verbose: bool = False, log_dir: Path | None = None, no_log: bool = False) -> None:
        self.verbose = verbose
        self.no_log = no_log
        self.log_dir = log_dir or Path(__file__).resolve().parent / "audit_logs"
        self.policy = ToolPolicyEngine()
        self.results: list[dict] = []
        self.passed = 0
        self.failed = 0
        self.skipped = 0

    def _color(self, text: str, color: str) -> str:
        return f"{color}{text}{Colors.RESET}"

    def _log(self, message: str) -> None:
        if self.verbose:
            print(message)

    def _save_log(self, report: dict) -> Path | None:
        """Guarda el reporte de auditoría en un archivo JSON con timestamp."""
        if self.no_log:
            return None

        self.log_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = self.log_dir / f"audit_{timestamp}.json"

        log_data = {
            "metadata": {
                "timestamp_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "timestamp_local": datetime.datetime.now().isoformat(),
                "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
                "platform": platform.platform(),
                "hostname": platform.node(),
            },
            "summary": {
                "total": report["total"],
                "passed": report["passed"],
                "failed": report["failed"],
                "elapsed_seconds": report["elapsed_seconds"],
                "success_rate_percent": report["success_rate_percent"],
            },
            "results": report["results"],
        }

        log_file.write_text(json.dumps(log_data, indent=2, ensure_ascii=False), encoding="utf-8")
        return log_file

    def _create_plan(
        self,
        *,
        tool_name: str,
        args: dict | None = None,
        confidence: float = 0.95,
        risk_level: RiskLevel = RiskLevel.LOW,
        needs_human: bool = False,
    ) -> AssistantPlan:
        """Crea un AssistantPlan de prueba."""
        return AssistantPlan(
            action=AssistantAction.TOOL_CALL,
            confidence=confidence,
            tool_name=tool_name,
            arguments=ToolArgs(**(args or {})),
            risk_level=risk_level,
            needs_human=needs_human,
            user_goal=f"Test para {tool_name}",
            audit_summary=f"Auditoría automática de tool {tool_name}",
        )

    def _run_case(self, case: dict) -> dict:
        """Ejecuta un caso de prueba individual."""
        plan = self._create_plan(
            tool_name=case["tool_name"],
            args=case.get("args"),
            confidence=case.get("confidence", 0.95),
            risk_level=case.get("risk_level", RiskLevel.LOW),
            needs_human=case.get("needs_human", False),
        )
        decision = self.policy.validate(plan, channel=case["channel"])

        expected = case["expected_allowed"]
        actual = decision.allowed
        passed = actual == expected

        result = {
            "id": case["id"],
            "tool_name": plan.tool_name,  # puede haber sido autocorregido
            "original_tool": case["tool_name"],
            "channel": case["channel"],
            "description": case["description"],
            "expected": expected,
            "actual": actual,
            "reason": decision.reason,
            "passed": passed,
            "args": case.get("args"),
        }

        if passed:
            self.passed += 1
        else:
            self.failed += 1

        return result

    def _print_case(self, case: dict, result: dict) -> None:
        """Imprime el resultado de un caso."""
        icon = "[OK]" if result["passed"] else "[FAIL]"
        color = Colors.GREEN if result["passed"] else Colors.RED
        tool_display = result["tool_name"]
        if result["original_tool"] != result["tool_name"]:
            tool_display = f"{result['original_tool']}->{result['tool_name']}"

        line = (
            f"{icon} [{case['id']:03d}] "
            f"{result['channel']:12s} | "
            f"{tool_display:45s} | "
            f"{case['description'][:50]:50s}"
        )
        print(self._color(line, color))

        if not result["passed"]:
            print(
                self._color(
                    f"    Esperado: {result['expected']}, "
                    f"Obtenido: {result['actual']}, "
                    f"Razón: {result['reason']}",
                    Colors.YELLOW,
                )
            )

    def run(self, cases: list[dict]) -> dict:
        """Ejecuta todos los casos y retorna reporte."""
        start = time.perf_counter()
        print(self._color("=" * 100, Colors.CYAN))
        print(self._color("  AUDITORIA DE TOOLS - La Juana AI Assistant", Colors.BOLD + Colors.CYAN))
        print(self._color("=" * 100, Colors.CYAN))
        print()

        for case in cases:
            result = self._run_case(case)
            self.results.append(result)
            self._print_case(case, result)

        elapsed = time.perf_counter() - start

        # Reporte final
        total = len(cases)
        pct = (self.passed / total * 100) if total else 0

        print()
        print(self._color("-" * 100, Colors.DIM))
        print(self._color("  RESUMEN", Colors.BOLD))
        print(self._color("-" * 100, Colors.DIM))
        print(f"  Total:     {total:4d}")
        print(self._color(f"  [OK] PASSED: {self.passed:4d}", Colors.GREEN))
        print(self._color(f"  [FAIL] FAILED: {self.failed:4d}", Colors.RED))
        print(f"  Tiempo:    {elapsed:.2f}s")
        print(f"  % Éxito:   {pct:.1f}%")
        print(self._color("-" * 100, Colors.DIM))

        report = {
            "total": total,
            "passed": self.passed,
            "failed": self.failed,
            "elapsed_seconds": round(elapsed, 2),
            "success_rate_percent": round(pct, 2),
            "results": self.results,
        }

        log_path = self._save_log(report)
        if log_path:
            print(f"\nLog guardado en: {log_path.absolute()}")

        return report


def generate_test_cases() -> list[dict]:
    """Genera todos los casos de prueba para auditoría."""
    cases: list[dict] = []
    case_id = 0

    def add(tool_name: str, channel: str, expected: bool, description: str, args: dict | None = None, **kwargs) -> None:
        nonlocal case_id
        case_id += 1
        cases.append({
            "id": case_id,
            "tool_name": tool_name,
            "channel": channel,
            "expected_allowed": expected,
            "description": description,
            "args": args,
            **kwargs,
        })

    engine = ToolPolicyEngine()

    # Argumentos mínimos para que las tools pasen validación de argumentos
    # en los tests genéricos de channel access.
    _MINIMAL_ARGS: dict[str, dict] = {
        # Client tools con validación
        "check_experience_availability": {"requested_date": "2026-06-15", "participant_count": 4},
        "quote_experience": {"experience_id": "exp_123", "participant_count": 4},
        # Admin tools con validación de ID
        "admin_update_experience": {"experience_id": "test-id"},
        "admin_deactivate_experience": {"experience_id": "test-id"},
        "admin_update_schedule": {"schedule_id": "test-id"},
        "admin_deactivate_schedule": {"schedule_id": "test-id"},
        "admin_update_user": {"user_id": "test-id"},
        "admin_deactivate_user": {"user_id": "test-id"},
        "admin_update_equine": {"equine_id": "test-id"},
        "admin_deactivate_equine": {"equine_id": "test-id"},
        "admin_get_equine": {"equine_id": "test-id"},
        "admin_add_equine_health_event": {"equine_id": "test-id"},
        "admin_update_equine_availability": {"equine_id": "test-id"},
        "admin_get_participant": {"participant_id": "test-id"},
        "admin_update_participant": {"participant_id": "test-id"},
        "admin_get_reservation_detail": {"reservation_id": "test-id"},
        "admin_confirm_reservation": {"reservation_id": "test-id"},
        "admin_cancel_reservation": {"reservation_id": "test-id"},
        "admin_close_service_execution": {"reservation_id": "test-id"},
        "admin_get_payment_proof": {"payment_proof_id": "test-id"},
        "admin_approve_payment": {"payment_proof_id": "test-id"},
        "admin_reject_payment_proof": {"payment_proof_id": "test-id"},
        "admin_unverify_payment_proof": {"payment_proof_id": "test-id"},
        "admin_unreject_payment_proof": {"payment_proof_id": "test-id"},
        # Admin tools con validación de creación
        "admin_create_experience": {"name": "Test", "slug": "test"},
        "admin_create_user": {"email": "test@test.com", "password": "123456"},
        "admin_create_schedule": {"experience_id": "test-id", "date": "2026-06-15"},
        "admin_create_equine": {"name": "Tornado"},
        "admin_update_reservation_rules": {"min_days_in_advance": 3},
    }

    # -----------------------------------------------
    # 1. TOOLS CLIENTE (canal whatsapp)
    # -----------------------------------------------
    for tool in sorted(engine.CLIENT_TOOLS):
        add(tool, "whatsapp", True, f"Tool cliente permitida en whatsapp", _MINIMAL_ARGS.get(tool))

    # -----------------------------------------------
    # 2. TOOLS GUIA (canal mobile_api)
    # -----------------------------------------------
    for tool in sorted(engine.GUIDE_TOOLS):
        add(tool, "mobile_api", True, f"Tool guia permitida en mobile_api", _MINIMAL_ARGS.get(tool))
        add(tool, "whatsapp", False, f"Tool guia bloqueada en whatsapp")

    # -----------------------------------------------
    # 3. TOOLS ADMIN (canal admin_api)
    # -----------------------------------------------
    for tool in sorted(engine.ADMIN_TOOLS):
        add(tool, "admin_api", True, f"Tool admin permitida en admin_api", _MINIMAL_ARGS.get(tool))
        add(tool, "whatsapp", False, f"Tool admin bloqueada en whatsapp")

    # -----------------------------------------------
    # 4. CRITICAL TOOLS (bloqueadas en TODOS los canales)
    # -----------------------------------------------
    for tool in sorted(engine.CRITICAL_TOOLS):
        add(tool, "whatsapp", False, f"CRITICAL tool bloqueada en whatsapp")
        add(tool, "admin_api", False, f"CRITICAL tool bloqueada en admin_api")
        add(tool, "mobile_api", False, f"CRITICAL tool bloqueada en mobile_api")

    # -----------------------------------------------
    # 5. VALIDACIÓN DE ARGUMENTOS - Tools client
    # -----------------------------------------------
    # check_experience_availability sin fecha
    add(
        "check_experience_availability",
        "whatsapp",
        False,
        "Availability sin fecha -> bloqueado",
        {"participant_count": 4},
    )
    # check_experience_availability sin participantes
    add(
        "check_experience_availability",
        "whatsapp",
        False,
        "Availability sin participantes -> bloqueado",
        {"requested_date": "2026-06-15"},
    )
    # check_experience_availability completo
    add(
        "check_experience_availability",
        "whatsapp",
        True,
        "Availability con fecha y participantes -> permitido",
        {"requested_date": "2026-06-15", "participant_count": 4},
    )

    # quote_experience sin experiencia
    add(
        "quote_experience",
        "whatsapp",
        False,
        "Quote sin experiencia -> bloqueado",
        {"participant_count": 4},
    )
    # quote_experience sin participantes
    add(
        "quote_experience",
        "whatsapp",
        False,
        "Quote sin participantes -> bloqueado",
        {"experience_id": "exp_123"},
    )
    # quote_experience completo
    add(
        "quote_experience",
        "whatsapp",
        True,
        "Quote completo -> permitido",
        {"experience_id": "exp_123", "participant_count": 4},
    )

    # -----------------------------------------------
    # 6. VALIDACIÓN DE ARGUMENTOS - Tools admin
    # -----------------------------------------------
    # admin_create_experience sin name
    add(
        "admin_create_experience",
        "admin_api",
        False,
        "Crear experiencia sin name -> bloqueado",
        {"slug": "cabalgata"},
    )
    # admin_create_experience completo
    add(
        "admin_create_experience",
        "admin_api",
        True,
        "Crear experiencia con name y slug -> permitido",
        {"name": "Cabalgata", "slug": "cabalgata"},
    )

    # admin_create_user sin email
    add(
        "admin_create_user",
        "admin_api",
        False,
        "Crear usuario sin email -> bloqueado",
        {"password": "123456"},
    )
    # admin_create_user completo
    add(
        "admin_create_user",
        "admin_api",
        True,
        "Crear usuario con email y password -> permitido",
        {"email": "test@lajuana.com", "password": "123456"},
    )

    # admin_create_schedule sin experience_id
    add(
        "admin_create_schedule",
        "admin_api",
        False,
        "Crear schedule sin experience_id -> bloqueado",
        {"date": "2026-06-15"},
    )
    # admin_create_schedule completo
    add(
        "admin_create_schedule",
        "admin_api",
        True,
        "Crear schedule completo -> permitido",
        {"experience_id": "exp_123", "date": "2026-06-15"},
    )

    # admin_create_equine sin name
    add(
        "admin_create_equine",
        "admin_api",
        False,
        "Crear equino sin name -> bloqueado",
        {"breed": "Criollo"},
    )
    # admin_create_equine completo
    add(
        "admin_create_equine",
        "admin_api",
        True,
        "Crear equino con name -> permitido",
        {"name": "Tornado"},
    )

    # admin_update_reservation_rules sin campos
    add(
        "admin_update_reservation_rules",
        "admin_api",
        False,
        "Update rules sin campos -> bloqueado",
        {},
    )
    # admin_update_reservation_rules completo
    add(
        "admin_update_reservation_rules",
        "admin_api",
        True,
        "Update rules con min_days -> permitido",
        {"min_days_in_advance": 3},
    )

    # Tools que requieren ID específico
    id_required_tests = [
        ("admin_update_experience", "experience_id"),
        ("admin_deactivate_experience", "experience_id"),
        ("admin_update_schedule", "schedule_id"),
        ("admin_deactivate_schedule", "schedule_id"),
        ("admin_update_user", "user_id"),
        ("admin_deactivate_user", "user_id"),
        ("admin_update_equine", "equine_id"),
        ("admin_deactivate_equine", "equine_id"),
        ("admin_get_equine", "equine_id"),
        ("admin_add_equine_health_event", "equine_id"),
        ("admin_update_equine_availability", "equine_id"),
        ("admin_get_participant", "participant_id"),
        ("admin_update_participant", "participant_id"),
        ("admin_get_reservation_detail", "reservation_id"),
        ("admin_confirm_reservation", "reservation_id"),
        ("admin_cancel_reservation", "reservation_id"),
        ("admin_close_service_execution", "reservation_id"),
        ("admin_get_payment_proof", "payment_proof_id"),
        ("admin_approve_payment", "payment_proof_id"),
        ("admin_reject_payment_proof", "payment_proof_id"),
        ("admin_unverify_payment_proof", "payment_proof_id"),
        ("admin_unreject_payment_proof", "payment_proof_id"),
    ]

    for tool, field in id_required_tests:
        # Sin ID
        add(tool, "admin_api", False, f"{tool} sin {field} -> bloqueado", {})
        # Con ID
        add(tool, "admin_api", True, f"{tool} con {field} -> permitido", {field: "test-id-123"})

    # -----------------------------------------------
    # 7. EDGE CASES
    # -----------------------------------------------
    # Tool desconocida
    add("unknown_tool_xyz", "admin_api", False, "Tool desconocida -> bloqueada")
    add("unknown_tool_xyz", "whatsapp", False, "Tool desconocida en whatsapp -> bloqueada")

    # Confianza baja
    add(
        "list_experiences",
        "whatsapp",
        False,
        "Confianza baja -> bloqueado",
        confidence=0.3,
    )

    # Nivel de riesgo alto
    add(
        "list_experiences",
        "whatsapp",
        False,
        "Riesgo alto -> bloqueado",
        risk_level=RiskLevel.HIGH,
    )

    # Necesita humano
    add(
        "list_experiences",
        "whatsapp",
        False,
        "Necesita humano -> bloqueado",
        needs_human=True,
    )

    # Canal no mapeado -> client por defecto
    add("list_experiences", "random_channel", True, "Canal no mapeado -> rol client por defecto")
    add("admin_list_users", "random_channel", False, "Tool admin en canal no mapeado -> bloqueado")

    # Autocorrección de typo
    add("admin_list_equins", "admin_api", True, "Typo autocorregido -> permitido")
    add("admin_upate_user", "admin_api", True, "Typo autocorregido -> permitido", {"user_id": "test-id"})

    # No autocorregir tool conocida que está en CRITICAL
    add("confirm_reservation", "admin_api", False, "CRITICAL no se autocorrige -> bloqueado")

    return cases


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Auditoría completa de tools del asistente La Juana",
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Mostrar detalles extra")
    parser.add_argument("--report", "-r", type=str, help="Guardar reporte JSON en archivo (ruta custom)")
    parser.add_argument("--log-dir", type=str, help="Directorio para guardar logs (default: scripts/audit_logs/)")
    parser.add_argument("--no-log", action="store_true", help="No guardar log automático")
    parser.add_argument("--failed-only", action="store_true", help="Solo mostrar fallos")
    args = parser.parse_args()

    log_dir = Path(args.log_dir) if args.log_dir else None
    cases = generate_test_cases()
    runner = ToolAuditRunner(verbose=args.verbose, log_dir=log_dir, no_log=args.no_log)
    report = runner.run(cases)

    if args.report:
        report_path = Path(args.report)
        report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False))
        print(f"\nReporte guardado en: {report_path.absolute()}")

    return 0 if report["failed"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
