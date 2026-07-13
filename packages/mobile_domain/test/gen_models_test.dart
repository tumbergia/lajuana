import 'package:flutter_test/flutter_test.dart';
import 'package:mobile_domain/src/gen/gen.dart';

void main() {
  group('Generated enums roundtrip via String', () {
    test('EquineSex', () {
      expect('female'.toEquineSex(), EquineSex.FEMALE);
      expect(EquineSex.MALE.toJson(), 'male');
    });

    test('ReservationStatus', () {
      expect('confirmed'.toReservationStatus(), ReservationStatus.CONFIRMED);
      expect(ReservationStatus.PENDING_PAYMENT.toJson(), 'pending_payment');
    });

    test('AssignmentStatus', () {
      expect('draft'.toAssignmentStatus(), AssignmentStatus.DRAFT);
      expect(AssignmentStatus.FINAL.toJson(), 'final');
    });

    test('EquineSpecies', () {
      expect('horse'.toEquineSpecies(), EquineSpecies.HORSE);
      expect(EquineSpecies.MULE.toJson(), 'mule');
    });

    test('Channel', () {
      expect('whatsapp'.toChannel(), Channel.WHATSAPP);
      expect(Channel.FACEBOOK.toJson(), 'facebook');
    });
  });

  group('Generated models fromJson', () {
    test('User.fromJson basic fields', () {
      final json = <String, dynamic>{
        'id': 'u1',
        'email': 'test@test.com',
        'full_name': 'Test User',
        'role': 'admin',
        'is_active': true,
        'version': 1,
        'created_at': '2024-01-01T00:00:00Z',
        'updated_at': '2024-06-01T00:00:00Z',
      };
      final user = User.fromJson(json);
      expect(user.email, 'test@test.com');
      expect(user.id, 'u1');
      expect(user.isActive, true);
    });

    test('SaddleListItem.fromJson simple', () {
      final json = <String, dynamic>{
        'id': 's1',
        'code': 'S-001',
        'version': 1,
        'created_at': '2024-01-01T00:00:00Z',
        'updated_at': '2024-06-01T00:00:00Z',
      };
      final item = SaddleListItem.fromJson(json);
      expect(item.id, 's1');
      expect(item.code, 'S-001');
    });

    test('InAppNotification.fromJson nullable reservation', () {
      final json = <String, dynamic>{
        'id': 'n1',
        'user_id': 'u1',
        'reservation_id': null,
        'title': 'Atención',
        'body': 'Cliente pide ayuda',
        'read': false,
        'event_type': 'human_review_requested',
        'version': 1,
        'created_at': '2024-01-01T00:00:00Z',
        'updated_at': '2024-06-01T00:00:00Z',
      };
      final item = InAppNotification.fromJson(json);
      expect(item.id, 'n1');
      expect(item.reservationId, isNull);
      expect(item.read, isFalse);
    });

    test('NotificationPreferences.fromJson map', () {
      final json = <String, dynamic>{
        'preferences': {
          'reservation_created': true,
          'configuration_changed': false,
        },
      };
      final prefs = NotificationPreferences.fromJson(json);
      expect(prefs.preferences?['reservation_created'], isTrue);
      expect(prefs.preferences?['configuration_changed'], isFalse);
    });

    test('InAppUnreadCount.fromJson', () {
      final count = InAppUnreadCount.fromJson({'unread_count': 3});
      expect(count.unreadCount, 3);
    });
  });
}
