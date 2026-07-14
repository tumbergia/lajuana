#!/usr/bin/env python3
"""Dispara una in-app de cada tipo de preferencia para probar la UI.

Autentica contra Mongo (sin depender del servidor HTTP), encola cada
NotificationEventType de NOTIFICATION_PREFERENCE_KEYS vía
NotificationService y espera 3 segundos entre cada una.

Usa reservas/comprobantes reales de Mongo cuando existen, para que la app
pueda abrir detalle, foto de pago y filas de reservas de mañana.

Uso:

    cd apps/api
    uv run python scripts/test_in_app_notifications.py

Opciones:

    uv run python scripts/test_in_app_notifications.py \\
        --email camilo@lajuana.com \\
        --password camilo123 \\
        --delay 3
"""

from __future__ import annotations

import argparse
import asyncio
import sys
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import uuid4

from app.common.enums import (
    NOTIFICATION_PREFERENCE_KEYS,
    NotificationChannel,
    NotificationEventType,
    UserRole,
)
from app.core.db import close_db, init_db
from app.core.security import verify_password
from app.documents import UserDocument
from app.documents.in_app_notification_document import InAppNotificationDocument
from app.documents.payment_proof_document import PaymentProofDocument
from app.documents.reservation_document import ReservationDocument
from app.services.notification_service import NotificationService


@dataclass(frozen=True)
class SamplePayload:
    title: str
    body: str
    reservation_id: str | None = None
    contact_phone: str | None = None


@dataclass
class FixtureData:
    reservations: list[ReservationDocument]
    payment_proof: PaymentProofDocument | None

    @property
    def primary(self) -> ReservationDocument | None:
        return self.reservations[0] if self.reservations else None

    @property
    def secondary(self) -> ReservationDocument | None:
        if len(self.reservations) > 1:
            return self.reservations[1]
        return self.primary


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--email", default="camilo@lajuana.com")
    parser.add_argument("--password", default="camilo123")
    parser.add_argument(
        "--delay",
        type=float,
        default=3.0,
        help="Segundos de espera entre cada notificación",
    )
    return parser.parse_args()


async def _authenticate(email: str, password: str) -> UserDocument:
    user = await UserDocument.find_one({"email": email})
    if user is None:
        raise SystemExit(f"Usuario {email} no existe en Mongo")
    if not user.is_active:
        raise SystemExit(f"Usuario {email} está inactivo")
    if not verify_password(password, user.password_hash):
        raise SystemExit(f"Password inválido para {email}")
    return user


async def _load_fixtures() -> FixtureData:
    reservations = (
        await ReservationDocument.find({"deleted_at": None})
        .sort("-updated_at")
        .limit(5)
        .to_list()
    )
    payment_proof: PaymentProofDocument | None = None
    if reservations:
        payment_proof = await PaymentProofDocument.find_one(
            {"reservation_id": reservations[0].id},
        )
        if payment_proof is None:
            payment_proof = await PaymentProofDocument.find_one({})
    return FixtureData(reservations=reservations, payment_proof=payment_proof)


def _holder(reservation: ReservationDocument | None, fallback: str = "Ana Pérez") -> str:
    if reservation is None:
        return fallback
    return reservation.holder_name or fallback


def _code(reservation: ReservationDocument | None, fallback: str = "RES-TEST") -> str:
    if reservation is None:
        return fallback
    return reservation.code or str(reservation.id)


def _phone(reservation: ReservationDocument | None, fallback: str = "+573001112233") -> str:
    if reservation is None:
        return fallback
    return reservation.holder_phone or fallback


def _rid(reservation: ReservationDocument | None) -> str | None:
    return str(reservation.id) if reservation is not None else None


def _participants(reservation: ReservationDocument | None, fallback: int = 4) -> int:
    if reservation is None:
        return fallback
    return int(reservation.participant_count or fallback)


def _build_samples(fixtures: FixtureData) -> dict[str, SamplePayload]:
    primary = fixtures.primary
    secondary = fixtures.secondary
    proof = fixtures.payment_proof

    holder = _holder(primary)
    code = _code(primary)
    phone = _phone(primary)
    count = _participants(primary)
    rid = _rid(primary)

    holder_b = _holder(secondary, "Carlos Ruiz")
    code_b = _code(secondary, "RES-DEMO")
    count_b = _participants(secondary, 2)
    rid_b = _rid(secondary) or "000000000000000000000002"

    proof_name = (proof.filename if proof is not None else None) or "comprobante.pdf"
    proof_id = str(proof.id) if proof is not None else "507f1f77bcf86cd799439011"
    proof_reservation_id = (
        str(proof.reservation_id) if proof is not None and proof.reservation_id else rid
    )

    fake_primary_id = rid or "507f1f77bcf86cd799439001"
    fake_secondary_id = rid_b if rid_b != rid else "507f1f77bcf86cd799439002"

    return {
        NotificationEventType.RESERVATION_CREATED.value: SamplePayload(
            title="Nueva reserva",
            body=f"{holder} — {code} ({count} participantes)",
            reservation_id=rid,
            contact_phone=phone,
        ),
        NotificationEventType.RESERVATION_CONFIRMED.value: SamplePayload(
            title="Nueva reserva confirmada",
            body=f"Reserva {code} confirmada - {count} participantes.",
            reservation_id=rid,
            contact_phone=phone,
        ),
        NotificationEventType.RESERVATION_STATUS_CHANGED.value: SamplePayload(
            title="Estado de reserva actualizado",
            body=f"{holder} — {code}: quoted → payment_received",
            reservation_id=rid,
            contact_phone=phone,
        ),
        NotificationEventType.RESERVATION_UPDATED.value: SamplePayload(
            title="Reserva actualizada",
            body=f"{holder} — {code}: holder_name, participant_count, requested_date",
            reservation_id=rid,
            contact_phone=phone,
        ),
        NotificationEventType.RESERVATION_CANCELLED.value: SamplePayload(
            title="Reserva cancelada",
            body=f"{holder} — {code} (antes: confirmed)",
            reservation_id=rid,
            contact_phone=phone,
        ),
        NotificationEventType.PAYMENT_PROOF_REGISTERED.value: SamplePayload(
            title="Nuevo comprobante de pago",
            body=f"{holder} — {code}: {proof_name}|{proof_id}",
            reservation_id=proof_reservation_id,
            contact_phone=phone,
        ),
        NotificationEventType.PARTICIPANT_FORM_COMPLETED.value: SamplePayload(
            title="Participante completó formulario",
            body=f"Luis Gómez — reserva {code}",
            reservation_id=rid,
            contact_phone=phone,
        ),
        NotificationEventType.HUMAN_REVIEW_REQUESTED.value: SamplePayload(
            title="Cliente solicita atención humana",
            body=f"{phone}: Quiere cambiar la fecha del paseo y pregunta por disponibilidad",
            contact_phone=phone,
        ),
        NotificationEventType.WHATSAPP_MESSAGE_UNATTENDED.value: SamplePayload(
            title="WhatsApp sin asistente",
            body=f"{phone}: Hola, ¿sigue disponible el sábado para {count} personas?",
            contact_phone=phone,
        ),
        NotificationEventType.CONFIGURATION_CHANGED.value: SamplePayload(
            title="Configuración actualizada",
            body="Camilo actualizó: Reglas de reserva",
        ),
        NotificationEventType.ASSIGNMENT_CHANGED.value: SamplePayload(
            title="Asignaciones actualizadas",
            body=f"Asignación creada — {holder} · reserva {code}",
            reservation_id=rid,
            contact_phone=phone,
        ),
        NotificationEventType.TOMORROW_SERVICES_SUMMARY.value: SamplePayload(
            title="Reservas de mañana (2)",
            body=(
                f"• {code}|{fake_primary_id}: {holder} ({count})\n"
                f"• {code_b}|{fake_secondary_id}: {holder_b} ({count_b})"
            ),
        ),
        NotificationEventType.WHATSAPP_DELIVERY_FAILED.value: SamplePayload(
            title="Fallo envío WhatsApp",
            body=(
                f"No se pudo enviar a {phone}: Recordatorio de mañana. "
                "WhatsApp API timeout"
            ),
            reservation_id=rid,
            contact_phone=phone,
        ),
    }


async def _unread_count(user_id: object) -> int:
    return await InAppNotificationDocument.find(
        {"user_id": user_id, "read": False}
    ).count()


async def main() -> None:
    args = _parse_args()
    run_id = uuid4().hex[:8]
    started = datetime.now(UTC).isoformat()

    print("==> Conectando a Mongo / Beanie")
    await init_db()
    try:
        print(f"==> Auth DB {args.email}")
        user = await _authenticate(args.email, args.password)
        print(
            f"    OK user_id={user.id} role={user.role.value} "
            f"active={user.is_active}"
        )

        fixtures = await _load_fixtures()
        print(
            f"==> Fixtures: reservas={len(fixtures.reservations)} "
            f"comprobante={'sí' if fixtures.payment_proof else 'no (ids fake)'}"
        )
        if fixtures.primary is not None:
            print(
                f"    primary={_code(fixtures.primary)} "
                f"id={fixtures.primary.id} "
                f"holder={_holder(fixtures.primary)}"
            )

        samples = _build_samples(fixtures)
        service = NotificationService()
        total = len(NOTIFICATION_PREFERENCE_KEYS)
        print(
            f"==> Enviando {total} notificaciones "
            f"(delay={args.delay}s, run={run_id}, started={started})"
        )

        for index, event_key in enumerate(NOTIFICATION_PREFERENCE_KEYS, start=1):
            event = NotificationEventType(event_key)
            sample = samples.get(event_key)
            if sample is None:
                sample = SamplePayload(
                    title=event_key.replace("_", " ").title(),
                    body=f"Prueba completa {event_key} #{index}",
                )

            dedup = f"script:{run_id}:{index}:{event_key}"
            extras = []
            if sample.reservation_id:
                extras.append(f"reservation={sample.reservation_id}")
            if sample.contact_phone:
                extras.append(f"phone={sample.contact_phone}")
            extra = f" ({', '.join(extras)})" if extras else ""

            print(f"[{index}/{total}] {event_key} — {sample.title}{extra}")
            print(f"    body={sample.body!r}")

            entries = await service.enqueue_admin_in_app(
                event_type=event,
                title=sample.title,
                body=sample.body,
                reservation_id=sample.reservation_id,
                actor_user_id=None,
                dedup_suffix=dedup,
                contact_phone=sample.contact_phone,
            )

            # Garantiza que el usuario de prueba también la reciba
            # (p. ej. si no es ADMIN, el fan-out no lo incluye).
            recipient_ids = {e.recipient_identifier for e in entries}
            if str(user.id) not in recipient_ids:
                if user.role != UserRole.ADMIN:
                    print(
                        f"    aviso: {args.email} no es ADMIN "
                        f"(role={user.role.value}); envío directo"
                    )
                entry = await service.enqueue(
                    event_type=event,
                    reservation_id=sample.reservation_id,
                    channel=NotificationChannel.IN_APP,
                    recipient_type="internal",
                    recipient_identifier=str(user.id),
                    subject=sample.title,
                    body=sample.body,
                    skip_template=True,
                    dedup_suffix=f"{dedup}:direct",
                    contact_phone=sample.contact_phone,
                )
                await service.send_from_outbox(entry)
                entries = [*entries, entry]

            unread = await _unread_count(user.id)
            print(f"    enqueued={len(entries)} unread={unread}")

            if index < total:
                await asyncio.sleep(args.delay)

        final_unread = await _unread_count(user.id)
        print(f"==> Listo. unread final={final_unread}")
        print("    Abre la campana en la app para revisar cada tipo.")
        if fixtures.payment_proof is None:
            print(
                "    Nota: no había comprobante real; "
                "'Ver comprobante' puede caer a la pestaña Pagos."
            )
    finally:
        await close_db()


if __name__ == "__main__":
    sys.stdout.reconfigure(line_buffering=True)  # type: ignore[attr-defined]
    t0 = time.perf_counter()
    asyncio.run(main())
    print(f"==> Duración {time.perf_counter() - t0:.1f}s")
