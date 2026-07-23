import 'package:flutter_test/flutter_test.dart';
import 'package:mobile_domain/src/reservations/reservation_detail.dart';
import 'package:mobile_domain/src/reservations/reservation_participant_detail.dart';
import 'package:mobile_domain/src/reservations/reservation_payment_proof_detail.dart';
import 'package:mobile_domain/src/reservations/reservation_timeline_entry.dart';
import 'package:mobile/features/reservations/domain/models/reservation_status.dart';
import 'package:mobile/features/reservations/infrastructure/mappers/reservation_mapper.dart';
import 'package:mobile/features/reservations/infrastructure/remote/reservation_dtos.dart';

void main() {
  group('dtoToDetail', () {
    ReservationDetailDto _makeDto({
      List<Map<String, dynamic>> participants = const [],
      List<Map<String, dynamic>> paymentProofs = const [],
    }) {
      final baseJson = {
        'id': 'r1',
        'code': 'RES-001',
        'experience_id': 'e1',
        'channel': 'whatsapp',
        'status': 'confirmed',
        'participant_count': 2,
        'payment_status': 'verified',
        'holder_name': 'Carlos Mejia',
        'holder_email': 'carlos@mail.com',
        'holder_phone': '3000000001',
        'requested_date': '2026-05-10',
        'quoted_total_amount': '180000',
        'currency': 'COP',
        'expected_participants_count': 2,
        'participants_completed_count': 2,
        'participant_form_status': 'complete',
        'form_url': null,
        'confirmed_at': '2026-05-25T12:00:00Z',
        'cancelled_at': null,
        'completed_at': null,
        'version': 3,
        'created_at': '2026-05-25T12:00:00Z',
        'updated_at': '2026-05-25T12:00:00Z',
        'deleted_at': null,
        'participants': participants,
        'payment_proofs': paymentProofs,
      };
      return ReservationDetailDto.fromJson(baseJson);
    }

    test('maps participants correctly', () {
      final dto = _makeDto(
        participants: [
          {
            'id': 'p1',
            'reservation_id': 'r1',
            'first_name': 'Carlos',
            'last_name': 'Mejia',
            'birth_date': '1990-05-15',
            'document_type': 'cc',
            'document_number': '80000001',
            'phone': '3110000001',
            'country': 'Colombia',
            'city': 'Manizales',
            'height_cm': '175.0',
            'weight_kg': '70.0',
            'experience_level': 'intermediate',
            'dietary_restrictions': null,
            'blood_type': null,
            'eps_or_travel_insurance': null,
            'health_conditions': null,
            'sensory_disabilities': null,
            'emergency_contact': {'name': 'Contacto', 'phone': '3200000001'},
            'accepted_data_processing': true,
            'accepted_media_usage': true,
            'accepted_risk_release': true,
            'is_completed': true,
          },
        ],
      );

      final detail = dtoToDetail(dto);

      expect(detail.participants, hasLength(1));
      expect(detail.participants[0].fullName, 'Carlos Mejia');
      expect(detail.participants[0].isCompleted, true);
      expect(detail.participants[0].hasMedicalAlert, false);
      expect(detail.participants[0].hasFoodRestriction, false);
      expect(detail.participants[0].photoVideoConsent, true);
      expect(detail.participants[0].experienceLevel, 'intermediate');
      expect(detail.participants[0].heightCm, '175.0');
      expect(detail.participants[0].weightKg, '70.0');
    });

    test('maps medical alerts from health_conditions', () {
      final dto = _makeDto(
        participants: [
          {
            'id': 'p1',
            'reservation_id': 'r1',
            'first_name': 'Maria',
            'last_name': 'Lopez',
            'birth_date': '1985-03-10',
            'document_type': 'cc',
            'document_number': '80000002',
            'phone': '3110000002',
            'country': 'Colombia',
            'city': 'Manizales',
            'height_cm': '160.0',
            'weight_kg': '60.0',
            'experience_level': 'basic',
            'dietary_restrictions': 'Sin gluten',
            'health_conditions': 'Asma',
            'sensory_disabilities': null,
            'emergency_contact': {'name': 'Contacto', 'phone': '3200000002'},
            'accepted_data_processing': true,
            'accepted_media_usage': false,
            'accepted_risk_release': true,
            'is_completed': true,
          },
        ],
      );

      final detail = dtoToDetail(dto);

      expect(detail.participants[0].hasMedicalAlert, true);
      expect(detail.participants[0].hasFoodRestriction, true);
      expect(detail.participants[0].photoVideoConsent, false);
    });

    test('maps payment proofs', () {
      final dto = _makeDto(
        paymentProofs: [
          {
            'id': 'proof1',
            'reservation_id': 'r1',
            'storage_key': 'seed/RES-001.pdf',
            'filename': 'RES-001.pdf',
            'content_type': 'application/pdf',
            'size_bytes': 2048,
            'sha256': 'abc123',
            'status': 'verified',
            'uploaded_at': '2026-05-25T12:00:00Z',
          },
        ],
      );

      final detail = dtoToDetail(dto);

      expect(detail.paymentProofs, hasLength(1));
      expect(detail.paymentProofs[0].status, 'verified');
      expect(detail.paymentProofs[0].filename, 'RES-001.pdf');
      expect(detail.paymentProofs[0].contentType, 'application/pdf');
      expect(detail.paymentProofs[0].uploadedAt, isNotNull);
    });

    test('produces empty lists for empty DTO arrays', () {
      final dto = _makeDto(participants: [], paymentProofs: []);

      final detail = dtoToDetail(dto);

      expect(detail.participants, isEmpty);
      expect(detail.paymentProofs, isEmpty);
    });

    test('produces empty lists for null DTO arrays (backward compat)', () {
      final dto = _makeDto(); // no participants/payment_proofs keys

      final detail = dtoToDetail(dto);

      expect(detail.participants, isEmpty);
      expect(detail.paymentProofs, isEmpty);
    });

    test('deriveFallbackTimeline still works with new fields', () {
      final dto = _makeDto(
        participants: [
          {
            'id': 'p1',
            'reservation_id': 'r1',
            'first_name': 'Juan',
            'last_name': 'Perez',
            'birth_date': '2000-01-01',
            'document_type': 'cc',
            'document_number': '80000003',
            'phone': '3110000003',
            'country': 'Colombia',
            'city': 'Manizales',
            'height_cm': '170.0',
            'weight_kg': '65.0',
            'experience_level': 'advanced',
            'dietary_restrictions': null,
            'health_conditions': null,
            'sensory_disabilities': null,
            'emergency_contact': {'name': 'Contacto', 'phone': '3200000003'},
            'accepted_data_processing': true,
            'accepted_media_usage': null,
            'accepted_risk_release': true,
            'is_completed': true,
          },
        ],
      );

      final detail = dtoToDetail(dto);

      // Fallback timeline should still derive from state fields
      expect(detail.timeline, isNotEmpty);
      expect(detail.timeline.any((e) => e.title == 'Fecha solicitada'), isTrue);
      expect(
        detail.timeline.any((e) => e.title == 'Reserva confirmada'),
        isTrue,
      );
    });

    test('timelineEntryNodeType maps kinds', () {
      final note = ReservationTimelineEntry(
        id: '1',
        source: 'service_log',
        kind: 'note',
        happenedAt: DateTime(2026, 1, 1),
        title: 'Nota',
      );
      final rejected = ReservationTimelineEntry(
        id: '2',
        source: 'audit_log',
        kind: 'payment_proof.rejected',
        happenedAt: DateTime(2026, 1, 1),
        title: 'Rechazado',
      );

      expect(timelineEntryNodeType(note), 'active');
      expect(timelineEntryNodeType(rejected), 'error');
    });

    test('payment summary gets proof count', () {
      final dto = _makeDto(
        paymentProofs: [
          {
            'id': 'p1',
            'reservation_id': 'r1',
            'filename': 'proof.pdf',
            'content_type': 'application/pdf',
            'size_bytes': 1000,
            'sha256': 'abc',
            'status': 'received',
            'uploaded_at': '2026-05-25T12:00:00Z',
          },
          {
            'id': 'p2',
            'reservation_id': 'r1',
            'filename': 'proof2.pdf',
            'content_type': 'application/pdf',
            'size_bytes': 2000,
            'sha256': 'def',
            'status': 'verified',
            'uploaded_at': '2026-05-26T12:00:00Z',
          },
        ],
      );

      final detail = dtoToDetail(dto);

      expect(detail.paymentSummary?.proofCount, 2);
    });

    test('payment proof unknown status maps without crash', () {
      final dto = _makeDto(
        paymentProofs: [
          {
            'id': 'p1',
            'reservation_id': 'r1',
            'filename': 'proof.pdf',
            'content_type': 'image/png',
            'size_bytes': 500,
            'sha256': 'xyz',
            'status': 'bogus_status_42',
            'uploaded_at': '2026-05-25T12:00:00Z',
          },
        ],
      );

      final detail = dtoToDetail(dto);

      expect(detail.paymentProofs[0].status, 'bogus_status_42');
    });
  });
}
