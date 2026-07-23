import 'package:flutter_test/flutter_test.dart';
import 'package:mobile/features/reservations/infrastructure/remote/reservation_dtos.dart';

void main() {
  group('ReservationDetailDto.fromJson', () {
    final sampleParticipant = {
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
      'emergency_contact': {
        'name': 'Contacto 1',
        'phone': '3200000001',
        'relationship': 'familiar',
      },
      'accepted_data_processing': true,
      'accepted_media_usage': true,
      'accepted_risk_release': true,
      'is_completed': true,
    };

    final sampleProof = {
      'id': 'proof1',
      'reservation_id': 'r1',
      'storage_key': 'seed/RES-SEED-001.pdf',
      'filename': 'RES-SEED-001.pdf',
      'content_type': 'application/pdf',
      'size_bytes': 2048,
      'sha256': 'abc123',
      'status': 'verified',
      'uploaded_at': '2026-05-25T12:00:00Z',
    };

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
      'participants_completed_count': 1,
      'participant_form_status': 'partial',
      'form_url': 'https://example.test/form',
      'confirmed_at': null,
      'cancelled_at': null,
      'completed_at': null,
      'version': 3,
      'created_at': '2026-05-25T12:00:00Z',
      'updated_at': '2026-05-25T12:00:00Z',
      'deleted_at': null,
    };

    test('parses participants and payment_proofs from JSON', () {
      final json = Map<String, dynamic>.from(baseJson);
      json['participants'] = [sampleParticipant];
      json['payment_proofs'] = [sampleProof];

      final dto = ReservationDetailDto.fromJson(json);

      expect(dto.participants, hasLength(1));
      expect(dto.participants[0].id, 'p1');
      expect(dto.participants[0].fullName, 'Carlos Mejia');
      expect(dto.participants[0].experienceLevel, 'intermediate');
      expect(dto.participants[0].emergencyContact.name, 'Contacto 1');
      expect(dto.participants[0].isCompleted, true);

      expect(dto.paymentProofs, hasLength(1));
      expect(dto.paymentProofs[0].id, 'proof1');
      expect(dto.paymentProofs[0].status, 'verified');
      expect(dto.paymentProofs[0].filename, 'RES-SEED-001.pdf');
      expect(dto.paymentProofs[0].uploadedAt, isNotNull);
    });

    test('handles empty participants array', () {
      final json = Map<String, dynamic>.from(baseJson);
      json['participants'] = [];
      json['payment_proofs'] = [];

      final dto = ReservationDetailDto.fromJson(json);

      expect(dto.participants, isEmpty);
      expect(dto.paymentProofs, isEmpty);
    });

    test('handles null participants/payment_proofs keys (backward compat)', () {
      final json = Map<String, dynamic>.from(baseJson);
      // Do NOT add participants or payment_proofs keys

      final dto = ReservationDetailDto.fromJson(json);

      expect(dto.participants, isEmpty);
      expect(dto.paymentProofs, isEmpty);
    });

    test('payment proof unknown status does not crash', () {
      final json = Map<String, dynamic>.from(baseJson);
      final proofWithUnknownStatus = Map<String, dynamic>.from(sampleProof);
      proofWithUnknownStatus['status'] = 'unknown_status_123';
      json['payment_proofs'] = [proofWithUnknownStatus];

      final dto = ReservationDetailDto.fromJson(json);

      expect(dto.paymentProofs, hasLength(1));
      expect(dto.paymentProofs[0].status, 'unknown_status_123');
    });

    test('participant with missing optional fields still parses', () {
      final minimalParticipant = {
        'id': 'p2',
        'reservation_id': 'r1',
        'first_name': 'Ana',
        'last_name': 'Lopez',
        'birth_date': null,
        'document_type': null,
        'document_number': null,
        'phone': null,
        'country': null,
        'city': null,
        'height_cm': null,
        'weight_kg': null,
        'experience_level': null,
        'dietary_restrictions': null,
        'blood_type': null,
        'eps_or_travel_insurance': null,
        'health_conditions': null,
        'sensory_disabilities': null,
        'emergency_contact': null,
        'accepted_data_processing': false,
        'accepted_media_usage': null,
        'accepted_risk_release': null,
        'is_completed': false,
      };
      final json = Map<String, dynamic>.from(baseJson);
      json['participants'] = [minimalParticipant];

      final dto = ReservationDetailDto.fromJson(json);

      expect(dto.participants, hasLength(1));
      expect(dto.participants[0].fullName, 'Ana Lopez');
      expect(dto.participants[0].emergencyContact.name, '');
      expect(dto.participants[0].experienceLevel, isNull);
      expect(dto.participants[0].isCompleted, false);
    });
  });
}
