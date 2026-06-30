"""Seed reproducible con orden estricto y validaciones de coherencia operativa.

Uso:
    cd apps/api
    python -m app.seed_reproducible
"""

from __future__ import annotations

import asyncio
import hashlib
import random
from dataclasses import dataclass
from datetime import UTC, date, datetime
from decimal import Decimal

from beanie import init_beanie
from pymongo import AsyncMongoClient

from app.common.enums import (
    Channel,
    ExperienceLevel,
    PaymentStatus,
    ReservationStatus,
    UserRole,
)
from app.core.config import settings
from app.core.security import hash_password
from app.documents import (
    AppConfigDocument,
    AssignmentDocument,
    EquineDocument,
    ExperienceDocument,
    ParticipantDocument,
    PaymentProofDocument,
    PolicyDocument,
    ProviderDocument,
    ProviderType,
    ReservationDocument,
    ReservationRules,
    SaddleDocument,
    ServiceLogDocument,
    ServiceLogEventType,
    UserDocument,
)

RNG = random.Random(20260422)

COLLECTIONS_TO_DROP = [
    "reservations",
    "participants",
    "payment_proofs",
    "assignments",
    "logs",
    "service_logs",
    "schedules",
    "experiences",
    "equines",
    "saddles",
    "providers",
    "policies",
    "users",
    "config",
    "app_config",
]

RESERVATION_STATUS_COUNTS: dict[ReservationStatus, int] = {
    ReservationStatus.CONTACT: 6,
    ReservationStatus.QUOTED: 5,
    ReservationStatus.PENDING_PAYMENT: 5,
    ReservationStatus.PAYMENT_RECEIVED: 4,
    ReservationStatus.CONFIRMED: 10,
    ReservationStatus.CANCELLED: 5,
}

# La distribucion por estados suma 35; se prioriza esa cobertura de estados.
TOTAL_RESERVATIONS = sum(RESERVATION_STATUS_COUNTS.values())


@dataclass(frozen=True)
class ReservationDateSeed:
    experience_slug: str
    date_iso: str


def _reservation_date_blueprint() -> list[ReservationDateSeed]:
    return [
        ReservationDateSeed("los-chorros", "2026-05-10"),
        ReservationDateSeed("los-chorros", "2026-05-17"),
        ReservationDateSeed("los-chorros", "2026-05-24"),
        ReservationDateSeed("los-chorros", "2026-06-07"),
        ReservationDateSeed("los-chorros", "2026-06-21"),
        ReservationDateSeed("los-chorros", "2026-03-15"),
        ReservationDateSeed("pueblo-dos-mentiras", "2026-05-11"),
        ReservationDateSeed("pueblo-dos-mentiras", "2026-05-18"),
        ReservationDateSeed("pueblo-dos-mentiras", "2026-06-01"),
        ReservationDateSeed("pueblo-dos-mentiras", "2026-06-15"),
        ReservationDateSeed("pueblo-dos-mentiras", "2026-03-22"),
        ReservationDateSeed("montana-cristal", "2026-05-15"),
        ReservationDateSeed("montana-cristal", "2026-05-29"),
        ReservationDateSeed("montana-cristal", "2026-06-12"),
        ReservationDateSeed("montana-cristal", "2026-03-08"),
        ReservationDateSeed("alto-roble", "2026-05-12"),
        ReservationDateSeed("alto-roble", "2026-05-26"),
        ReservationDateSeed("alto-roble", "2026-06-09"),
        ReservationDateSeed("salamina-san-felix-marulanda", "2026-05-20"),
        ReservationDateSeed("salamina-san-felix-marulanda", "2026-06-17"),
        ReservationDateSeed("recorrido-medio-dia", "2026-05-13"),
        ReservationDateSeed("recorrido-medio-dia", "2026-05-27"),
        ReservationDateSeed("recorrido-medio-dia", "2026-06-10"),
        ReservationDateSeed("recorrido-medio-dia", "2026-06-24"),
        ReservationDateSeed("recorrido-medio-dia", "2026-07-08"),
        ReservationDateSeed("los-chorros", "2026-07-22"),
        ReservationDateSeed("pueblo-dos-mentiras", "2026-07-29"),
        ReservationDateSeed("montana-cristal", "2026-08-05"),
        ReservationDateSeed("alto-roble", "2026-08-12"),
        ReservationDateSeed("salamina-san-felix-marulanda", "2026-08-19"),
        ReservationDateSeed("recorrido-medio-dia", "2026-08-26"),
        ReservationDateSeed("los-chorros", "2026-09-02"),
        ReservationDateSeed("pueblo-dos-mentiras", "2026-09-09"),
        ReservationDateSeed("montana-cristal", "2026-09-16"),
        ReservationDateSeed("alto-roble", "2026-09-23"),
        ReservationDateSeed("salamina-san-felix-marulanda", "2026-09-30"),
    ]


async def reset_db(client: AsyncMongoClient) -> None:
    db = client[settings.mongodb_db_name]
    for collection_name in COLLECTIONS_TO_DROP:
        await db[collection_name].delete_many({})


async def seed_users() -> UserDocument:
    admin = UserDocument(
        email="admin@lajuana.com",
        full_name="Admin La Juana",
        password_hash=hash_password("Admin123!"),
        role=UserRole.ADMIN,
    )
    await admin.insert()
    return admin


async def seed_config() -> AppConfigDocument:
    config = AppConfigDocument(
        key="reservation_rules",
        reservation_rules=ReservationRules(
            min_days_in_advance=7,
            require_payment_proof_for_confirmation=True,
        ),
    )
    await config.insert()
    return config


async def seed_experiences() -> dict[str, ExperienceDocument]:
    payloads = [
        {
            "name": "Los Chorros",
            "slug": "los-chorros",
            "description": "Ruta de un dia por senderos y cascadas.",
            "level": ExperienceLevel.INTERMEDIATE,
            "duration_hours": 8,
            "base_capacity": 8,
            "is_active": True,
            "aliases": [
                "chorros",
                "los chorros",
                "recorrido los chorros",
                "ruta los chorros",
                "un día",
                "día completo",
                "paseo de un día",
            ],
            "tags": ["café", "cafe", "naturaleza", "cascada"],
        },
        {
            "name": "El Pueblo de las Dos Mentiras",
            "slug": "pueblo-dos-mentiras",
            "description": "Recorrido cultural y de montana de un dia.",
            "level": ExperienceLevel.INTERMEDIATE,
            "duration_hours": 8,
            "base_capacity": 8,
            "is_active": True,
            "aliases": ["pueblo dos mentiras", "pueblo mentiras", "dos mentiras"],
        },
        {
            "name": "La Montana de Cristal",
            "slug": "montana-cristal",
            "description": "Ruta tecnica de ascenso de un dia.",
            "level": ExperienceLevel.ADVANCED,
            "duration_hours": 10,
            "base_capacity": 6,
            "is_active": True,
            "aliases": ["montaña cristal", "cristal"],
        },
        {
            "name": "Salamina - San Felix - Marulanda",
            "slug": "salamina-san-felix-marulanda",
            "description": "Travesia de varios dias por zonas altas.",
            "level": ExperienceLevel.ADVANCED,
            "duration_days": 3,
            "base_capacity": 6,
            "is_active": True,
            "aliases": ["salamina", "san felix", "marulanda", "travesía"],
        },
        {
            "name": "Cruce del Alto del Roble",
            "slug": "alto-roble",
            "description": "Ruta corta de baja exigencia.",
            "level": ExperienceLevel.BASIC,
            "duration_hours": 5,
            "base_capacity": 10,
            "is_active": True,
            "aliases": ["alto del roble", "cruce alto roble", "ruta corta"],
        },
        {
            "name": "Recorrido de medio día",
            "slug": "recorrido-medio-dia",
            "description": "Experiencia corta ideal para quienes tienen poco tiempo. Incluye paseo en mula por senderos.",  # noqa: E501
            "level": ExperienceLevel.BASIC,
            "duration_hours": 4,
            "base_capacity": 10,
            "is_active": True,
            "aliases": [
                "medio día",
                "medio dia",
                "recorrido medio día",
                "recorrido medio dia",
                "recorrido de medio día",
                "experiencia corta",
                "plan corto",
                "paseo corto",
                "paseo café",
                "cafe",
                "café",
            ],
            "tags": ["café", "cafe", "senderismo"],
        },
    ]
    inserted: dict[str, ExperienceDocument] = {}
    for payload in payloads:
        doc = ExperienceDocument(**payload)
        await doc.insert()
        inserted[doc.slug] = doc
    return inserted


async def seed_equines() -> dict[str, EquineDocument]:
    mule_names = [
        "Juana",
        "Redentor",
        "Chula",
        "Cachirula",
        "Sonadora",
        "Lucerito",
        "Napoleon",
        "Carbonero",
        "Gitana",
        "Linda",
        "Almendra",
        "Suzana",
        "Julia",
        "Calandria",
    ]
    inserted: dict[str, EquineDocument] = {}
    for name in mule_names:
        restricted = name == "Napoleon"
        doc = EquineDocument(
            name=name,
            sex="male" if name in {"Redentor", "Napoleon", "Carbonero"} else "female",
            breed="mule",
            gait="service_mule",
            is_available=not restricted,
            availability_notes="status=restricted" if restricted else "status=active",
        )
        await doc.insert()
        inserted[name] = doc

    cosaco = EquineDocument(
        name="Cosaco 24",
        sex="male",
        breed="donkey",
        gait="breeding",
        is_available=False,
        availability_notes="is_assignable=false",
    )
    await cosaco.insert()
    inserted[cosaco.name] = cosaco

    mimosa = EquineDocument(
        name="Mimosa",
        sex="female",
        breed="horse",
        gait="mare",
        is_available=False,
        availability_notes="is_assignable=false",
    )
    picasso = EquineDocument(
        name="Picasso",
        sex="male",
        breed="horse",
        gait="horse",
        is_available=False,
        availability_notes="is_assignable=false",
    )
    await mimosa.insert()
    await picasso.insert()
    inserted[mimosa.name] = mimosa
    inserted[picasso.name] = picasso
    return inserted


async def seed_saddles() -> dict[str, SaddleDocument]:
    inserted: dict[str, SaddleDocument] = {}
    for idx in range(1, 13):
        code = f"S{idx}"
        doc = SaddleDocument(code=code, name=f"Silla {code}", is_available=True)
        await doc.insert()
        inserted[code] = doc
    return inserted


def _provider_type_for(category: str) -> ProviderType:
    mapping = {
        "lodging": ProviderType.LODGING,
        "food": ProviderType.FOOD,
        "logistics": ProviderType.MULE_TRANSPORT,
        "transport": ProviderType.MULE_TRANSPORT,
        "insurance": ProviderType.OTHER,
        "partner": ProviderType.OTHER,
    }
    return mapping[category]


async def seed_providers() -> list[ProviderDocument]:
    payloads = [
        ("Safe Trips", "insurance"),
        ("Tominejo Ecolodge", "lodging"),
        ("Castillo de Cascadas", "lodging"),
        ("Casa Tucan", "lodging"),
        ("Hotel Termales del Ruiz", "lodging"),
        ("Hacienda Guayabal", "lodging"),
        ("Neira York Coffee", "food"),
        ("Los Turpiales", "food"),
        ("Melva Pineda", "food"),
        ("Nohra Pueblo Hondo", "food"),
        ("Juan Jose Hidalgo", "logistics"),
        ("Andres Mejia", "logistics"),
        ("Guillermo Alvarez", "logistics"),
        ("Jeep Willys", "transport"),
        ("DE UNA COLOMBIA", "partner"),
        ("KIUBO COLOMBIA", "partner"),
    ]
    docs: list[ProviderDocument] = []
    for name, category in payloads:
        doc = ProviderDocument(
            name=name,
            provider_type=_provider_type_for(category),
            contact_name=name,
            is_active=True,
        )
        await doc.insert()
        docs.append(doc)
    return docs


def _reservation_people_by_status() -> dict[ReservationStatus, list[int]]:
    return {
        ReservationStatus.CONTACT: [2, 2, 2, 8, 2, 2],
        ReservationStatus.QUOTED: [1, 2, 2, 2, 2],
        ReservationStatus.PENDING_PAYMENT: [2, 2, 9, 2, 2],
        ReservationStatus.PAYMENT_RECEIVED: [2, 2, 2, 2],
        ReservationStatus.CONFIRMED: [4, 3, 2, 5, 4, 3, 2, 1, 1, 1],
        ReservationStatus.CANCELLED: [2, 2, 2, 2, 2],
    }


def _build_channels() -> list[Channel]:
    channels = [Channel.WHATSAPP] * 25
    channels.extend([Channel.INSTAGRAM] * 4)
    channels.extend([Channel.FACEBOOK] * 3)
    channels.extend([Channel.EMAIL] * 3)
    return channels


async def seed_reservations(
    experiences_by_slug: dict[str, ExperienceDocument],
) -> list[ReservationDocument]:
    date_cycle = _reservation_date_blueprint()
    channels = _build_channels()
    people_map = _reservation_people_by_status()
    confirmed_dates: set[str] = set()

    holder_first_names = [
        "Carlos",
        "Ana",
        "Laura",
        "Daniel",
        "Marta",
        "Sofia",
        "Pedro",
        "Miguel",
        "Valentina",
        "Andres",
        "Camila",
        "Jhon",
        "Felipe",
        "Paula",
        "Monica",
        "Julian",
        "Natalia",
        "Diana",
        "Ricardo",
        "Elena",
    ]
    holder_last_names = [
        "Mejia",
        "Lopez",
        "Gomez",
        "Torres",
        "Ramirez",
        "Hernandez",
        "Diaz",
        "Vargas",
        "Ruiz",
        "Morales",
    ]

    reservations: list[ReservationDocument] = []
    sequence = 1
    channel_idx = 0
    for status, count in RESERVATION_STATUS_COUNTS.items():
        people_values = people_map[status]
        for idx in range(count):
            first = holder_first_names[(sequence - 1) % len(holder_first_names)]
            last = holder_last_names[(sequence - 1) % len(holder_last_names)]
            date_seed = date_cycle[(sequence - 1) % len(date_cycle)]
            exp = experiences_by_slug[date_seed.experience_slug]
            requested = date.fromisoformat(date_seed.date_iso)
            if status == ReservationStatus.CONFIRMED:
                if requested.isoformat() in confirmed_dates:
                    raise ValueError(
                        f"Fecha duplicada para reserva confirmada: {requested.isoformat()}"
                    )
                confirmed_dates.add(requested.isoformat())
            payment_status = PaymentStatus.PENDING
            if status in {ReservationStatus.PAYMENT_RECEIVED, ReservationStatus.CONFIRMED}:
                payment_status = PaymentStatus.RECEIVED
            doc = ReservationDocument(
                code=f"RES-SEED-{sequence:03d}",
                experience_id=exp.id,
                channel=channels[channel_idx],
                status=status,
                holder_name=f"{first} {last}",
                holder_email=f"{first.lower()}.{last.lower()}{sequence}@mail.com",
                holder_phone=f"300000{sequence:04d}",
                requested_date=requested,
                participant_count=people_values[idx],
                quoted_total_amount=None,
                currency="COP",
                payment_status=payment_status,
                blocks_day=status == ReservationStatus.CONFIRMED,
                availability_lock_key=requested.isoformat()
                if status == ReservationStatus.CONFIRMED
                else None,
            )
            await doc.insert()
            reservations.append(doc)
            sequence += 1
            channel_idx += 1
    if len(reservations) != TOTAL_RESERVATIONS:
        raise ValueError("Cantidad de reservas distinta a la esperada.")
    return reservations


def _make_placeholder_png() -> bytes:
    """Return a minimal valid 1x1 white pixel PNG (~68 bytes)."""
    import struct, zlib  # noqa: PLC0415 — inline for clarity

    sig = b'\x89PNG\r\n\x1a\n'
    # IHDR: 1x1 pixel, 8-bit RGB
    ihdr_data = struct.pack('>IIBBBBB', 1, 1, 8, 2, 0, 0, 0)
    ihdr_crc = zlib.crc32(b'IHDR' + ihdr_data) & 0xffffffff
    ihdr = struct.pack('>I', 13) + b'IHDR' + ihdr_data + struct.pack('>I', ihdr_crc)
    # IDAT: filter byte (0) + white pixel (255,255,255)
    raw = zlib.compress(b'\x00\xff\xff\xff')
    idat_crc = zlib.crc32(b'IDAT' + raw) & 0xffffffff
    idat = struct.pack('>I', len(raw)) + b'IDAT' + raw + struct.pack('>I', idat_crc)
    # IEND
    iend_crc = zlib.crc32(b'IEND') & 0xffffffff
    iend = struct.pack('>I', 0) + b'IEND' + struct.pack('>I', iend_crc)
    return sig + ihdr + idat + iend


async def seed_payment_proofs(
    reservations: list[ReservationDocument],
) -> dict[str, PaymentProofDocument]:
    proof_by_reservation_id: dict[str, PaymentProofDocument] = {}
    cancelled_with_proof = 0
    for reservation in reservations:
        should_create = reservation.status in {
            ReservationStatus.PAYMENT_RECEIVED,
            ReservationStatus.CONFIRMED,
        }
        if reservation.status == ReservationStatus.CANCELLED and cancelled_with_proof < 2:
            should_create = True
            cancelled_with_proof += 1
        if not should_create:
            continue

        # Generate a minimal placeholder PNG for synthetic proofs
        placeholder_png = _make_placeholder_png()
        digest = hashlib.sha256(placeholder_png).hexdigest()
        proof = PaymentProofDocument(
            reservation_id=reservation.id,
            storage_key=f"seed/{reservation.code}.png",
            filename=f"{reservation.code}.png",
            content_type="image/png",
            size_bytes=len(placeholder_png),
            sha256=digest,
            status=PaymentStatus.VERIFIED,
            file_data=placeholder_png,
        )
        await proof.insert()
        reservation.payment_proof_ids.append(proof.id)
        if reservation.status in {ReservationStatus.PAYMENT_RECEIVED, ReservationStatus.CONFIRMED}:
            reservation.payment_status = PaymentStatus.VERIFIED
        await reservation.save()
        proof_by_reservation_id[str(reservation.id)] = proof
    return proof_by_reservation_id


def _participant_name_pool() -> list[tuple[str, str]]:
    first_names = [
        "Carlos",
        "Ana",
        "Tom",
        "Laura",
        "Daniel",
        "Mateo",
        "Sofia",
        "Sara",
        "Juan",
        "Maria",
        "Nicolas",
        "Emma",
        "Diego",
        "Lina",
        "Pedro",
        "Mia",
        "Felipe",
        "Rosa",
        "Camilo",
        "Elisa",
    ]
    last_names = [
        "Mejia",
        "Lopez",
        "Wilson",
        "Gomez",
        "Torres",
        "Ruiz",
        "Diaz",
        "Miller",
        "Vargas",
        "Perez",
    ]
    names: list[tuple[str, str]] = []
    for i in range(120):
        names.append((first_names[i % len(first_names)], last_names[i % len(last_names)]))
    return names


async def seed_participants(reservations: list[ReservationDocument]) -> list[ParticipantDocument]:
    names = _participant_name_pool()
    countries = ["Colombia", "USA", "Canada", "Mexico", "Chile"]
    levels = [ExperienceLevel.BASIC, ExperienceLevel.INTERMEDIATE, ExperienceLevel.ADVANCED]
    participants: list[ParticipantDocument] = []
    name_idx = 0
    doc_seq = 1
    for reservation in reservations:
        for slot in range(reservation.participant_count):
            first_name, last_name = names[name_idx]
            birth_year = RNG.randint(1970, 2008)
            birth_month = RNG.randint(1, 12)
            birth_day = RNG.randint(1, 28)
            participant = ParticipantDocument(
                reservation_id=reservation.id,
                first_name=first_name,
                last_name=last_name,
                email=f"{first_name.lower()}.{last_name.lower()}.{doc_seq}@mail.com",
                birth_date=date(birth_year, birth_month, birth_day),
                document_type="cc",
                document_number=f"{80000000 + doc_seq}",
                phone=f"311000{doc_seq:04d}",
                country=countries[name_idx % len(countries)],
                city="Manizales",
                height_cm=Decimal(str(150 + (slot % 25))),
                weight_kg=Decimal(str(50 + (slot % 40))),
                experience_level=levels[name_idx % len(levels)],
                emergency_contact={
                    "name": f"Contacto {doc_seq}",
                    "phone": f"320000{doc_seq:04d}",
                    "relationship": "familiar",
                },
                accepted_data_processing=True,
                accepted_media_usage=True,
                is_completed=True,
            )
            await participant.insert()
            reservation.participant_ids.append(participant.id)
            participants.append(participant)
            doc_seq += 1
            name_idx += 1
        await reservation.save()
    return participants


async def seed_assignments(
    reservations: list[ReservationDocument],
    participants: list[ParticipantDocument],
    equines_by_name: dict[str, EquineDocument],
    saddles_by_code: dict[str, SaddleDocument],
) -> list[AssignmentDocument]:
    participants_by_reservation: dict[str, list[ParticipantDocument]] = {}
    for p in participants:
        participants_by_reservation.setdefault(str(p.reservation_id), []).append(p)

    assignable_mules = [
        equines_by_name[name]
        for name in (
            "Juana",
            "Redentor",
            "Chula",
            "Cachirula",
            "Sonadora",
            "Lucerito",
            "Carbonero",
            "Gitana",
            "Linda",
            "Almendra",
            "Suzana",
            "Julia",
            "Calandria",
        )
    ]
    saddle_codes = [f"S{i}" for i in range(1, 13)]
    assignments: list[AssignmentDocument] = []
    mule_idx = 0
    saddle_idx = 0
    for reservation in reservations:
        if reservation.status != ReservationStatus.CONFIRMED:
            continue
        reservation_participants = participants_by_reservation.get(str(reservation.id), [])
        for participant in reservation_participants:
            assignment = AssignmentDocument(
                reservation_id=reservation.id,
                participant_id=participant.id,
                equine_id=assignable_mules[mule_idx % len(assignable_mules)].id,
                saddle_id=saddles_by_code[saddle_codes[saddle_idx % len(saddle_codes)]].id,
                notes="Asignacion seed operativa",
            )
            await assignment.insert()
            assignments.append(assignment)
            mule_idx += 1
            saddle_idx += 1
    return assignments


async def seed_logs(
    reservations: list[ReservationDocument],
    participants: list[ParticipantDocument],
    assignments: list[AssignmentDocument],
) -> list[ServiceLogDocument]:
    confirmed = [r for r in reservations if r.status == ReservationStatus.CONFIRMED]
    participant_by_id = {str(p.id): p for p in participants}
    assignment_by_reservation: dict[str, list[AssignmentDocument]] = {}
    for assignment in assignments:
        assignment_by_reservation.setdefault(str(assignment.reservation_id), []).append(assignment)

    logs: list[ServiceLogDocument] = []
    for idx in range(13):
        reservation = confirmed[idx % len(confirmed)]
        related_assignments = assignment_by_reservation.get(str(reservation.id), [])
        related_participant_id = None
        related_equine_id = None
        if related_assignments:
            selected = related_assignments[idx % len(related_assignments)]
            related_participant_id = selected.participant_id
            related_equine_id = selected.equine_id
            _ = participant_by_id.get(str(selected.participant_id))
        if idx % 3 == 0:
            event_type = ServiceLogEventType.ARRIVAL
            checkpoint = None
        elif idx % 3 == 1:
            event_type = ServiceLogEventType.CHECKPOINT
            checkpoint = f"Punto {idx + 1}"
        else:
            event_type = ServiceLogEventType.DEPARTURE
            checkpoint = None
        log = ServiceLogDocument(
            reservation_id=reservation.id,
            event_type=event_type,
            happened_at=datetime(2026, 5, 10, 8, 0, tzinfo=UTC),
            checkpoint_name=checkpoint,
            notes="Log seed operativo",
            related_participant_id=related_participant_id,
            related_equine_id=related_equine_id,
        )
        # Mantiene timestamps crecientes sin dependencia externa.
        log.happened_at = datetime(2026, 5, 10, 8 + (idx % 6), (idx * 7) % 60, tzinfo=UTC)
        await log.insert()
        logs.append(log)
    return logs


async def validate_seed(
    reservations: list[ReservationDocument],
    participants: list[ParticipantDocument],
    assignments: list[AssignmentDocument],
    logs: list[ServiceLogDocument],
    equines_by_name: dict[str, EquineDocument],
) -> None:
    reservation_by_id = {str(r.id): r for r in reservations}
    participant_by_id = {str(p.id): p for p in participants}

    confirmed = [r for r in reservations if r.status == ReservationStatus.CONFIRMED]
    for reservation in confirmed:
        if not reservation.payment_proof_ids:
            raise ValueError(f"Reserva confirmada sin comprobante: {reservation.code}")

    for assignment in assignments:
        if str(assignment.participant_id) not in participant_by_id:
            raise ValueError("Asignacion con participante inexistente.")
        participant = participant_by_id[str(assignment.participant_id)]
        if str(participant.reservation_id) != str(assignment.reservation_id):
            raise ValueError("Asignacion con participante fuera de su reserva.")

    for participant in participants:
        if str(participant.reservation_id) not in reservation_by_id:
            raise ValueError("Participante sin reserva valida.")

    for log in logs:
        if str(log.reservation_id) not in reservation_by_id:
            raise ValueError("Log sin reserva valida.")

    forbidden_equines = {"Cosaco 24", "Mimosa", "Picasso"}
    equine_ids_forbidden = {str(equines_by_name[name].id) for name in forbidden_equines}
    napoleon_id = str(equines_by_name["Napoleon"].id)
    napoleon_assignments = 0
    for assignment in assignments:
        if str(assignment.equine_id) in equine_ids_forbidden:
            raise ValueError("Se detecto asignacion de equino no asignable.")
        if str(assignment.equine_id) == napoleon_id:
            napoleon_assignments += 1
    if napoleon_assignments > 1:
        raise ValueError("Napoleon fue usado en exceso.")

    confirmed_dates: set[str] = set()
    for reservation in confirmed:
        if reservation.requested_date is None:
            raise ValueError(f"Reserva confirmada sin fecha: {reservation.code}")
        date_key = reservation.requested_date.isoformat()
        if date_key in confirmed_dates:
            raise ValueError(f"Fecha duplicada entre reservas confirmadas: {date_key}")
        confirmed_dates.add(date_key)
        if not reservation.blocks_day or reservation.availability_lock_key != date_key:
            raise ValueError(f"Day-lock invalido para reserva confirmada: {reservation.code}")

    experiences_count = await ExperienceDocument.find({"is_active": True}).count()
    if experiences_count != 6:
        raise ValueError("Cobertura invalida de experiencias activas.")
    equines_count = await EquineDocument.find_all().count()
    if equines_count != 17:
        raise ValueError("Cobertura invalida de equinos.")
    active_assignable = await EquineDocument.find({"is_available": True}).count()
    if active_assignable != 13:
        raise ValueError("Cantidad de equinos asignables invalida.")

    for status, expected in RESERVATION_STATUS_COUNTS.items():
        count = sum(1 for r in reservations if r.status == status)
        if count != expected:
            raise ValueError(f"Cobertura invalida para estado {status}.")

    past_reservation_dates = sum(
        1 for r in reservations if r.requested_date and r.requested_date < date(2026, 4, 22)
    )
    if past_reservation_dates != 3:
        raise ValueError("Cobertura invalida de reservas con fechas pasadas.")


async def run_seed() -> None:
    client = AsyncMongoClient(settings.mongodb_uri)
    database = client[settings.mongodb_db_name]
    await init_beanie(
        database=database,
        document_models=[
            UserDocument,
            ExperienceDocument,
            ReservationDocument,
            ParticipantDocument,
            PaymentProofDocument,
            AppConfigDocument,
            EquineDocument,
            SaddleDocument,
            AssignmentDocument,
            ServiceLogDocument,
            ProviderDocument,
            PolicyDocument,
        ],
    )

    reservations: list[ReservationDocument] = []
    participants: list[ParticipantDocument] = []
    assignments: list[AssignmentDocument] = []
    logs: list[ServiceLogDocument] = []

    try:
        await reset_db(client)
        await seed_users()
        await seed_config()
        experiences_by_slug = await seed_experiences()
        equines_by_name = await seed_equines()
        saddles_by_code = await seed_saddles()
        await seed_providers()
        reservations = await seed_reservations(experiences_by_slug)
        await seed_payment_proofs(reservations)
        participants = await seed_participants(reservations)
        assignments = await seed_assignments(
            reservations,
            participants,
            equines_by_name,
            saddles_by_code,
        )
        logs = await seed_logs(reservations, participants, assignments)
        await validate_seed(
            reservations=reservations,
            participants=participants,
            assignments=assignments,
            logs=logs,
            equines_by_name=equines_by_name,
        )
    finally:
        await client.close()

    print("Seed reproducible completado.")
    print(f"- reservas: {len(reservations)}")
    print(f"- participantes: {len(participants)}")
    print(f"- asignaciones: {len(assignments)}")
    print(f"- logs: {len(logs)}")


if __name__ == "__main__":
    asyncio.run(run_seed())
