import 'package:flutter_test/flutter_test.dart';
import 'package:mobile/features/catalogs/schedules/presentation/controllers/schedule_form_controller.dart';

void main() {
  late ScheduleFormController controller;

  setUp(() {
    controller = ScheduleFormController();
  });

  group('initial state', () {
    test('starts with reasonable defaults', () {
      expect(controller.experienceId, '');
      expect(controller.dateIso, '');
      expect(controller.startTime, '08:00:00');
      expect(controller.isActive, true);
      expect(controller.capacityTotal, 1);
      expect(controller.reservedSlots, 0);
      expect(controller.internalSlots, 0);
      expect(controller.blockedSlots, 0);
      expect(controller.customRequestOnly, false);
      expect(controller.notes, '');
    });
  });

  group('availableSlots', () {
    test('returns total minus reserved, internal, and blocked', () {
      controller.capacityTotal = 10;
      controller.reservedSlots = 3;
      controller.internalSlots = 1;
      controller.blockedSlots = 2;

      expect(controller.availableSlots, 4);
    });

    test('returns full capacity when no slots used', () {
      controller.capacityTotal = 20;
      expect(controller.availableSlots, 20);
    });
  });

  group('validate', () {
    test('fails when experienceId is empty', () {
      controller.experienceId = '';
      final error = controller.validate();
      expect(error, contains('experiencia'));
    });

    test('fails when date is empty', () {
      controller.experienceId = 'exp-1';
      controller.dateIso = '';
      final error = controller.validate();
      expect(error, contains('fecha'));
    });

    test('fails when capacity is zero or negative', () {
      controller.experienceId = 'exp-1';
      controller.dateIso = '2026-06-15';
      controller.capacityTotal = 0;
      var error = controller.validate();
      expect(error, contains('capacidad'));

      controller.capacityTotal = -5;
      error = controller.validate();
      expect(error, contains('capacidad'));
    });

    test('fails when reservedSlots exceeds capacity', () {
      controller.experienceId = 'exp-1';
      controller.dateIso = '2026-06-15';
      controller.capacityTotal = 5;
      controller.reservedSlots = 10;
      final error = controller.validate();
      expect(error, contains('cupo'));
    });

    test('fails when internalSlots exceeds capacity', () {
      controller.experienceId = 'exp-1';
      controller.dateIso = '2026-06-15';
      controller.capacityTotal = 5;
      controller.internalSlots = 10;
      final error = controller.validate();
      expect(error, contains('cupo'));
    });

    test('fails when blockedSlots exceeds capacity', () {
      controller.experienceId = 'exp-1';
      controller.dateIso = '2026-06-15';
      controller.capacityTotal = 5;
      controller.blockedSlots = 10;
      final error = controller.validate();
      expect(error, contains('cupo'));
    });

    test('fails when slots are negative', () {
      controller.experienceId = 'exp-1';
      controller.dateIso = '2026-06-15';
      controller.capacityTotal = 5;
      controller.reservedSlots = -1;
      final error = controller.validate();
      expect(error, contains('negativos'));
    });

    test('fails when available slots become negative', () {
      controller.experienceId = 'exp-1';
      controller.dateIso = '2026-06-15';
      controller.capacityTotal = 5;
      controller.reservedSlots = 3;
      controller.internalSlots = 2;
      controller.blockedSlots = 2; // 5 - 3 - 2 - 2 = -2
      final error = controller.validate();
      expect(error, contains('negativa'));
    });

    test('passes with valid fields', () {
      controller.experienceId = 'exp-1';
      controller.dateIso = '2026-06-15';
      controller.capacityTotal = 10;
      controller.reservedSlots = 3;
      controller.internalSlots = 1;
      controller.blockedSlots = 1;

      final error = controller.validate();
      expect(error, isNull);
    });

    test('passes with minimal valid fields', () {
      controller.experienceId = 'exp-1';
      controller.dateIso = '2026-06-15';
      controller.capacityTotal = 1;

      final error = controller.validate();
      expect(error, isNull);
    });
  });
}
