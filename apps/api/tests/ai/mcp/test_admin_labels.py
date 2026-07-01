from datetime import date

from app.ai.mcp.presenters.admin_labels import (
    format_date_es,
    list_summary_es,
    payment_status_label_es,
    reservation_status_label_es,
)


def test_reservation_status_label_es():
    assert reservation_status_label_es("payment_received") == "Pago recibido"


def test_payment_status_label_es():
    assert payment_status_label_es("verified") == "Verificado"


def test_format_date_es():
    assert format_date_es(date(2026, 7, 5)) == "5 jul 2026"
    assert format_date_es("2026-07-05") == "5 jul 2026"


def test_list_summary_es():
    assert list_summary_es(total=0, singular="reserva", plural="reservas") == (
        "No se encontraron reservas."
    )
    assert list_summary_es(total=1, singular="reserva", plural="reservas") == (
        "1 reserva encontrado."
    )
