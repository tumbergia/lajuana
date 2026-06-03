#!/usr/bin/env python3
"""
Admin E2E Test - Prueba end-to-end de tools admin via HTTP /admin/ask.

Envia mensajes reales al endpoint admin, verifica que el asistente seleccione
la tool correcta, y guarda un log con el mensaje entrante, tool llamada,
respuesta y tokens consumidos por peticion.

Uso:
    python scripts/admin_e2e_test.py --base-url http://localhost:8000 --email admin@test.com --password 123456
    python scripts/admin_e2e_test.py --token JWT_AQUI --verbose
    python scripts/admin_e2e_test.py --log-dir ./e2e_logs
"""

from __future__ import annotations

import argparse
import datetime
import json
import platform
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import requests


class Colors:
    """Códigos ANSI para terminal (duplicado en audit_tools.py — mantener sincronizado)."""

    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RESET = "\033[0m"


@dataclass
class TestScenario:
    """Escenario de prueba E2E."""

    message: str
    expected_tool: str
    description: str


@dataclass
class TestResult:
    """Resultado de una prueba individual."""

    scenario: TestScenario
    actual_tool: str | None
    action: str | None
    response: str
    token_usage: dict[str, int] | None
    passed: bool
    error: str | None = None
    http_status: int = 0
    latency_ms: int = 0


class AdminE2ETestRunner:
    """Ejecuta pruebas E2E contra el endpoint /admin/ask."""

    def __init__(
        self,
        *,
        base_url: str,
        token: str | None = None,
        email: str | None = None,
        password: str | None = None,
        log_dir: Path | None = None,
        no_log: bool = False,
        verbose: bool = False,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.email = email
        self.password = password
        self.log_dir = log_dir or Path(__file__).resolve().parent / "e2e_logs"
        self.no_log = no_log
        self.verbose = verbose
        self.results: list[TestResult] = []
        self.passed = 0
        self.failed = 0
        self.total_tokens = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}

    def _color(self, text: str, color: str) -> str:
        return f"{color}{text}{Colors.RESET}"

    def _vprint(self, message: str) -> None:
        if self.verbose:
            print(message)

    def _authenticate(self) -> str:
        """Obtiene token JWT via login."""
        if self.token:
            self._vprint(f"Usando token proporcionado: {self.token[:20]}...")
            return self.token

        if not self.email or not self.password:
            raise ValueError("Se requiere --token o --email + --password")

        login_url = f"{self.base_url}/api/v1/auth/login"
        self._vprint(f"Autenticando en {login_url} con {self.email}")

        resp = requests.post(
            login_url,
            json={"email": self.email, "password": self.password},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        token = data["access_token"]
        self._vprint(f"Token obtenido: {token[:20]}...")
        return token

    def _send_message(self, message: str, token: str) -> tuple[dict, int, int]:
        """Envia mensaje a /admin/ask y retorna (respuesta_json, status_code, latency_ms)."""
        url = f"{self.base_url}/api/v1/admin/ask"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        payload = {"message": message}

        started = time.perf_counter()
        resp = requests.post(url, json=payload, headers=headers, timeout=30)
        latency_ms = int((time.perf_counter() - started) * 1000)

        if resp.status_code != 200:
            return {"error": f"HTTP {resp.status_code}", "text": resp.text}, resp.status_code, latency_ms

        return resp.json(), resp.status_code, latency_ms

    def _run_scenario(self, scenario: TestScenario, token: str) -> TestResult:
        """Ejecuta un escenario de prueba."""
        try:
            data, status, latency = self._send_message(scenario.message, token)

            if status != 200:
                return TestResult(
                    scenario=scenario,
                    actual_tool=None,
                    action=None,
                    response=data.get("text", ""),
                    token_usage=None,
                    passed=False,
                    error=f"HTTP {status}: {data.get('error', 'Unknown')}",
                    http_status=status,
                    latency_ms=latency,
                )

            actual_tool = data.get("tool_name")
            action = data.get("action")
            response = data.get("response", "")
            token_usage = data.get("token_usage")
            passed = actual_tool == scenario.expected_tool

            if token_usage:
                for k in self.total_tokens:
                    self.total_tokens[k] += token_usage.get(k, 0)

            return TestResult(
                scenario=scenario,
                actual_tool=actual_tool,
                action=action,
                response=response,
                token_usage=token_usage,
                passed=passed,
                http_status=status,
                latency_ms=latency,
            )

        except Exception as exc:
            return TestResult(
                scenario=scenario,
                actual_tool=None,
                action=None,
                response="",
                token_usage=None,
                passed=False,
                error=str(exc),
                http_status=0,
                latency_ms=0,
            )

    def _print_result(self, result: TestResult) -> None:
        """Imprime resultado en terminal."""
        icon = "[OK]" if result.passed else "[FAIL]"
        color = Colors.GREEN if result.passed else Colors.RED

        line = (
            f"{icon} | "
            f"{result.scenario.description[:45]:45s} | "
            f"tool={result.actual_tool or 'N/A':35s} | "
            f"{result.latency_ms}ms"
        )
        print(self._color(line, color))

        if not result.passed:
            detail = f"    Esperado: {result.scenario.expected_tool}, Obtenido: {result.actual_tool or 'N/A'}"
            if result.error:
                detail += f" | Error: {result.error}"
            print(self._color(detail, Colors.YELLOW))

        if self.verbose and result.token_usage:
            print(
                self._color(
                    f"    Tokens: prompt={result.token_usage.get('prompt_tokens', 0)} "
                    f"completion={result.token_usage.get('completion_tokens', 0)} "
                    f"total={result.token_usage.get('total_tokens', 0)}",
                    Colors.DIM,
                )
            )

    def run(self, scenarios: list[TestScenario]) -> dict[str, Any]:
        """Ejecuta todos los escenarios y retorna reporte."""
        start = time.perf_counter()

        print(self._color("=" * 100, Colors.CYAN))
        print(self._color("  ADMIN E2E TEST - La Juana AI Assistant", Colors.BOLD + Colors.CYAN))
        print(self._color("=" * 100, Colors.CYAN))
        print()

        token = self._authenticate()
        print(f"Base URL: {self.base_url}")
        print(f"Escenarios: {len(scenarios)}")
        print()

        for scenario in scenarios:
            result = self._run_scenario(scenario, token)
            self.results.append(result)
            if result.passed:
                self.passed += 1
            else:
                self.failed += 1
            self._print_result(result)

        elapsed = time.perf_counter() - start
        total = len(scenarios)
        pct = (self.passed / total * 100) if total else 0

        print()
        print(self._color("-" * 100, Colors.DIM))
        print(self._color("  RESUMEN", Colors.BOLD))
        print(self._color("-" * 100, Colors.DIM))
        print(f"  Total:            {total:4d}")
        print(self._color(f"  [OK]  PASADO:     {self.passed:4d}", Colors.GREEN))
        print(self._color(f"  [FAIL] FALLADO:   {self.failed:4d}", Colors.RED))
        print(f"  Tiempo total:     {elapsed:.1f}s")
        print(f"  Tiempo promedio:  {elapsed/total*1000:.0f}ms/petición" if total else "")
        print(f"  Tokens prompt:    {self.total_tokens['prompt_tokens']:,}")
        print(f"  Tokens completion:{self.total_tokens['completion_tokens']:,}")
        print(f"  Tokens total:     {self.total_tokens['total_tokens']:,}")
        print(f"  % Exito:          {pct:.1f}%")
        print(self._color("-" * 100, Colors.DIM))

        report = {
            "metadata": {
                "timestamp_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "timestamp_local": datetime.datetime.now().isoformat(),
                "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
                "platform": platform.platform(),
                "hostname": platform.node(),
                "base_url": self.base_url,
            },
            "summary": {
                "total": total,
                "passed": self.passed,
                "failed": self.failed,
                "elapsed_seconds": round(elapsed, 2),
                "success_rate_percent": round(pct, 2),
                "tokens": self.total_tokens,
            },
            "results": [
                {
                    "message": r.scenario.message,
                    "expected_tool": r.scenario.expected_tool,
                    "description": r.scenario.description,
                    "actual_tool": r.actual_tool,
                    "action": r.action,
                    "response": r.response,
                    "token_usage": r.token_usage,
                    "passed": r.passed,
                    "error": r.error,
                    "http_status": r.http_status,
                    "latency_ms": r.latency_ms,
                }
                for r in self.results
            ],
        }

        if not self.no_log:
            self.log_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            log_file = self.log_dir / f"admin_e2e_{timestamp}.json"
            log_file.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
            print(f"\nLog guardado en: {log_file.absolute()}")

        return report


def generate_scenarios() -> list[TestScenario]:
    """Genera escenarios de prueba para todas las tools admin."""
    return [
        # --- READ tools (seguras, sin efectos secundarios) ---
        TestScenario("Listar todos los usuarios del sistema", "admin_list_users", "Listar usuarios"),
        TestScenario("Mostrar todas las experiencias disponibles", "admin_list_experiences_admin", "Listar experiencias"),
        TestScenario("Ver todos los horarios registrados", "admin_list_schedules_admin", "Listar schedules"),
        TestScenario("Mostrar la lista de equinos", "admin_list_equines", "Listar equinos"),
        TestScenario("Ver todas las reservas", "admin_list_reservations", "Listar reservas"),
        TestScenario("Mostrar el resumen de ventas", "admin_get_sales_summary", "Reporte ventas"),
        TestScenario("Ver el embudo de conversion de reservas", "admin_get_reservation_funnel", "Embudo conversion"),
        TestScenario("Mostrar rendimiento por canal", "admin_get_channel_performance", "Rendimiento canal"),
        TestScenario("Ver reporte de ocupacion", "admin_get_occupancy_report", "Ocupacion"),
        TestScenario("Mostrar carga de trabajo de equinos", "admin_get_equine_workload_report", "Carga equina"),
        TestScenario("Ver el checklist logistico", "admin_get_logistics_checklist", "Checklist logistico"),
        TestScenario("Mostrar configuracion del sistema", "admin_get_system_config", "Config sistema"),
        TestScenario("Ver instrucciones de pago", "admin_get_payment_instructions", "Instrucciones pago"),
        TestScenario("Listar solicitudes de revision humana", "admin_list_human_review_requests", "Revisiones humanas"),
        TestScenario("Ver detalle del equino ID-test-123", "admin_get_equine", "Detalle equino"),
        TestScenario("Ver detalle de la reserva RES-test-001", "admin_get_reservation_detail", "Detalle reserva"),
        TestScenario("Ver comprobante de pago ID-proof-001", "admin_get_payment_proof", "Ver comprobante"),
        TestScenario("Mostrar detalle del participante ID-part-001", "admin_get_participant", "Detalle participante"),
        TestScenario("Ver carga de trabajo del equino ID-test-123", "admin_get_equine_workload", "Carga equino"),

        # --- WRITE tools (pueden pedir confirmacion) ---
        TestScenario("Crear un nuevo usuario con email test@lajuana.com y clave 123456", "admin_create_user", "Crear usuario"),
        TestScenario("Actualizar los datos del usuario ID-user-001", "admin_update_user", "Actualizar usuario"),
        TestScenario("Desactivar el usuario ID-user-001", "admin_deactivate_user", "Desactivar usuario"),
        TestScenario("Crear una nueva experiencia de cabalgata", "admin_create_experience", "Crear experiencia"),
        TestScenario("Actualizar la experiencia ID-exp-001", "admin_update_experience", "Actualizar experiencia"),
        TestScenario("Desactivar la experiencia ID-exp-001", "admin_deactivate_experience", "Desactivar experiencia"),
        TestScenario("Agregar un nuevo horario para la experiencia ID-exp-001", "admin_create_schedule", "Crear schedule"),
        TestScenario("Actualizar el horario ID-sched-001", "admin_update_schedule", "Actualizar schedule"),
        TestScenario("Eliminar el horario ID-sched-001", "admin_deactivate_schedule", "Desactivar schedule"),
        TestScenario("Crear un nuevo equino llamado Relampago", "admin_create_equine", "Crear equino"),
        TestScenario("Actualizar los datos del equino ID-eq-001", "admin_update_equine", "Actualizar equino"),
        TestScenario("Desactivar el equino ID-eq-001", "admin_deactivate_equine", "Desactivar equino"),
        TestScenario("Registrar evento de salud para el equino ID-eq-001", "admin_add_equine_health_event", "Evento salud equino"),
        TestScenario("Cambiar disponibilidad del equino ID-eq-001", "admin_update_equine_availability", "Disponibilidad equino"),
        TestScenario("Cerrar la ejecucion del servicio RES-001", "admin_close_service_execution", "Cerrar servicio"),
        TestScenario("Actualizar reglas de reserva con 3 dias de anticipacion", "admin_update_reservation_rules", "Reglas reserva"),
        TestScenario("Confirmar la reserva RES-001", "admin_confirm_reservation", "Confirmar reserva"),
        TestScenario("Cancelar la reserva RES-001", "admin_cancel_reservation", "Cancelar reserva"),
        TestScenario("Actualizar datos del participante ID-part-001", "admin_update_participant", "Actualizar participante"),
        TestScenario("Aprobar el pago ID-pay-001", "admin_approve_payment", "Aprobar pago"),
        TestScenario("Rechazar el comprobante de pago ID-proof-001", "admin_reject_payment_proof", "Rechazar comprobante"),
        TestScenario("Des-verificar el comprobante ID-proof-001", "admin_unverify_payment_proof", "Des-verificar"),
        TestScenario("Revertir rechazo del comprobante ID-proof-001", "admin_unreject_payment_proof", "Des-rechazar"),
        TestScenario("Programar automatizacion de cumpleanos", "schedule_birthday_automation", "Cumpleanos"),
        TestScenario("Programar automatizacion de aniversario de visita", "schedule_visit_anniversary_automation", "Aniversario"),
    ]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Pruebas E2E de tools admin via HTTP /admin/ask",
    )
    parser.add_argument("--base-url", type=str, default="http://localhost:8000", help="URL base de la API")
    parser.add_argument("--email", type=str, help="Email de admin para login")
    parser.add_argument("--password", type=str, help="Password de admin")
    parser.add_argument("--token", type=str, help="JWT token (alternativa a email/password)")
    parser.add_argument("--log-dir", type=str, help="Directorio para guardar logs")
    parser.add_argument("--no-log", action="store_true", help="No guardar log automatico")
    parser.add_argument("--verbose", "-v", action="store_true", help="Mostrar detalles extra")
    parser.add_argument("--failed-only", action="store_true", help="Solo mostrar fallos")
    args = parser.parse_args()

    log_dir = Path(args.log_dir) if args.log_dir else None
    runner = AdminE2ETestRunner(
        base_url=args.base_url,
        token=args.token,
        email=args.email,
        password=args.password,
        log_dir=log_dir,
        no_log=args.no_log,
        verbose=args.verbose,
    )

    scenarios = generate_scenarios()
    report = runner.run(scenarios)

    return 0 if report["summary"]["failed"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
