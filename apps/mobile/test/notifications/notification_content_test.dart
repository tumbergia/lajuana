import 'package:flutter_test/flutter_test.dart';
import 'package:mobile/features/notifications/presentation/notification_content.dart';
import 'package:mobile/features/notifications/presentation/notification_visuals.dart';

void main() {
  group('NotificationContent.from', () {
    test('parses reservation_created', () {
      final content = NotificationContent.from(
        eventType: 'reservation_created',
        title: 'Nueva reserva',
        body: 'Ana Pérez — RES-TEST (4 participantes)',
      );

      expect(content.headline, 'Ana Pérez · 4 participantes');
      expect(content.compactFacts, 'RES-TEST');
      expect(
        content.keyFacts.map((f) => '${f.label}:${f.value}'),
        [
          'Titular:Ana Pérez',
          'Código:RES-TEST',
          'Participantes:4 participantes',
        ],
      );
    });

    test('parses reservation_confirmed template body', () {
      final content = NotificationContent.from(
        eventType: 'reservation_confirmed',
        title: 'Nueva reserva confirmada',
        body: 'Reserva RES-42 confirmada - 3 participantes.',
      );

      expect(content.headline, 'Confirmada · 3 participantes');
      expect(content.keyFacts.map((f) => f.value), [
        'RES-42',
        '3 participantes',
      ]);
    });

    test('translates reservation_status_changed tokens', () {
      final content = NotificationContent.from(
        eventType: 'reservation_status_changed',
        title: 'Estado de reserva actualizado',
        body: 'Ana Pérez — RES-TEST: quoted → payment_received',
      );

      expect(content.headline, 'Cotizado → Pago recibido');
      expect(content.keyFacts.map((f) => '${f.label}:${f.value}'), [
        'Titular:Ana Pérez',
        'Código:RES-TEST',
        'Cambio:Cotizado → Pago recibido',
      ]);
    });

    test('parses cancellation with translated previous status', () {
      final content = NotificationContent.from(
        eventType: 'reservation_status_changed',
        title: 'Reserva cancelada',
        body: 'Ana Pérez — RES-TEST (antes: confirmed)',
      );

      expect(content.headline, 'Ana Pérez · cancelada');
      expect(content.keyFacts.map((f) => '${f.label}:${f.value}'), [
        'Titular:Ana Pérez',
        'Código:RES-TEST',
        'Estado anterior:Confirmada',
      ]);
    });

    test('humanizes reservation_updated field tokens', () {
      final content = NotificationContent.from(
        eventType: 'reservation_updated',
        title: 'Reserva actualizada',
        body: 'Ana Pérez — RES-TEST: holder_name, participant_count',
      );

      expect(content.headline, 'Se actualizó: Titular, Participantes');
      expect(content.compactFacts, contains('RES-TEST'));
      expect(content.compactFacts, contains('Ana Pérez'));
    });

    test('parses payment_proof_registered with proof id', () {
      final content = NotificationContent.from(
        eventType: 'payment_proof_registered',
        title: 'Nuevo comprobante de pago',
        body: 'Ana Pérez — RES-TEST: comprobante.pdf|507f1f77bcf86cd799439011',
      );

      expect(content.headline, 'Comprobante de Ana Pérez');
      expect(content.paymentProofId, '507f1f77bcf86cd799439011');
      expect(
        content.keyFacts.any((f) => f.label == 'Archivo'),
        isFalse,
      );
      expect(content.compactFacts, contains('RES-TEST'));
    });

    test('parses payment_proof_registered legacy without proof id', () {
      final content = NotificationContent.from(
        eventType: 'payment_proof_registered',
        title: 'Nuevo comprobante de pago',
        body: 'Ana Pérez — RES-TEST: comprobante.pdf',
      );

      expect(content.headline, 'Comprobante de Ana Pérez');
      expect(content.paymentProofId, isNull);
    });

    test('parses participant_form_completed with phone', () {
      final content = NotificationContent.from(
        eventType: 'participant_form_completed',
        title: 'Participante completó formulario',
        body: 'Luis Gómez — reserva RES-TEST',
        contactPhone: '+573001112233',
      );

      expect(content.headline, 'Luis Gómez completó el formulario');
      expect(content.keyFacts.map((f) => '${f.label}:${f.value}'), [
        'Participante:Luis Gómez',
        'Código:RES-TEST',
        'Teléfono:+573001112233',
      ]);
    });

    test('parses whatsapp_message_unattended', () {
      final content = NotificationContent.from(
        eventType: 'whatsapp_message_unattended',
        title: 'WhatsApp sin asistente',
        body: '+573001112233: Hola, ¿sigue disponible el sábado?',
      );

      expect(content.headline, 'Hola, ¿sigue disponible el sábado?');
      expect(content.isQuotedMessage, isTrue);
      expect(content.keyFacts.single.value, '+573001112233');
    });

    test('parses human_review_requested', () {
      final content = NotificationContent.from(
        eventType: 'human_review_requested',
        title: 'Cliente solicita atención humana',
        body: '+573001112233: Quiere cambiar la fecha del paseo',
        contactPhone: '+573001112233',
      );

      expect(content.headline, 'Quiere cambiar la fecha del paseo');
      expect(content.isQuotedMessage, isTrue);
    });

    test('parses whatsapp_delivery_failed', () {
      final content = NotificationContent.from(
        eventType: 'whatsapp_delivery_failed',
        title: 'Fallo envío WhatsApp',
        body: 'No se pudo enviar a +573001112233: Cancelación. boom',
      );

      expect(content.headline, 'Cancelación');
      expect(content.isQuotedMessage, isTrue);
      expect(
        content.keyFacts.map((f) => '${f.label}:${f.value}'),
        ['Teléfono:+573001112233', 'Error:boom'],
      );
    });

    test('parses configuration_changed', () {
      final content = NotificationContent.from(
        eventType: 'configuration_changed',
        title: 'Configuración actualizada',
        body: 'Camilo actualizó: Reglas de reserva',
      );

      expect(content.headline, 'Camilo actualizó Reglas de reserva');
      expect(content.compactFacts, isEmpty);
    });

    test('parses assignment_changed with holder', () {
      final content = NotificationContent.from(
        eventType: 'assignment_changed',
        title: 'Asignaciones actualizadas',
        body: 'Asignación creada — Ana Pérez · reserva RES-TEST',
        contactPhone: '+573001112233',
      );

      expect(content.headline, 'Asignación creada · Ana Pérez');
      expect(content.keyFacts.map((f) => '${f.label}:${f.value}'), [
        'Acción:creada',
        'Titular:Ana Pérez',
        'Código:RES-TEST',
        'Teléfono:+573001112233',
      ]);
    });

    test('parses legacy assignment_changed', () {
      final content = NotificationContent.from(
        eventType: 'assignment_changed',
        title: 'Asignaciones actualizadas',
        body: 'Asignación creada — reserva RES-TEST',
      );

      expect(content.headline, 'Asignación creada · RES-TEST');
      expect(content.keyFacts.map((f) => '${f.label}:${f.value}'), [
        'Acción:creada',
        'Código:RES-TEST',
      ]);
    });

    test('parses tomorrow_services_summary multiline', () {
      final content = NotificationContent.from(
        eventType: 'tomorrow_services_summary',
        title: 'Reservas de mañana (2)',
        body:
            '• RES-TEST|507f1f77bcf86cd799439011: Ana Pérez (4)\n• RES-DEMO|507f1f77bcf86cd799439012: Carlos Ruiz (2)',
      );

      expect(content.headline, '2 reservas mañana');
      expect(content.detailLines, [
        'RES-TEST|507f1f77bcf86cd799439011: Ana Pérez (4)',
        'RES-DEMO|507f1f77bcf86cd799439012: Carlos Ruiz (2)',
      ]);
      final first = parseTomorrowReservationLine(content.detailLines.first);
      expect(first?.code, 'RES-TEST');
      expect(first?.reservationId, '507f1f77bcf86cd799439011');
      expect(first?.subtitle, 'Ana Pérez · 4 participantes');
      expect(content.compactFacts, contains('Ana Pérez'));
    });

    test('falls back to body for unknown event types', () {
      final content = NotificationContent.from(
        eventType: 'something_new',
        title: 'Título',
        body: 'Cuerpo libre',
      );

      expect(content.headline, 'Cuerpo libre');
      expect(content.keyFacts, isEmpty);
    });

    test('falls back to title when body is empty', () {
      final content = NotificationContent.from(
        eventType: 'something_new',
        title: 'Solo título',
        body: '  ',
      );

      expect(content.headline, 'Solo título');
    });

    test('notificationStatusLabel maps known tokens', () {
      expect(notificationStatusLabel('quoted'), 'Cotizado');
      expect(notificationStatusLabel('payment_received'), 'Pago recibido');
      expect(notificationStatusLabel('pending_payment'), 'Pago pendiente');
    });
  });

  group('formatRelativeTime', () {
    final now = DateTime.utc(2026, 7, 13, 23, 0, 0);

    test('treats naive timestamps as UTC so west timezones are correct', () {
      // 2 hours earlier in UTC, stored without Z (common API serialization).
      final created = DateTime(2026, 7, 13, 21, 0, 0);
      expect(
        formatRelativeTime(created, now: now),
        'Hace 2 h',
      );
    });

    test('formats minutes for recent UTC timestamps', () {
      final created = DateTime.utc(2026, 7, 13, 22, 40, 0);
      expect(
        formatRelativeTime(created, now: now),
        'Hace 20 min',
      );
    });

    test('shows moment ago only under one minute', () {
      final created = DateTime.utc(2026, 7, 13, 22, 59, 30);
      expect(
        formatRelativeTime(created, now: now),
        'Hace un momento',
      );
    });
  });
}
