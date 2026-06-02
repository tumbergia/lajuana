import 'package:flutter_test/flutter_test.dart';
import 'package:mobile/features/participants/presentation/controllers/participants_controller.dart';

void main() {
  late ParticipantsController controller;

  setUp(() {
    controller = ParticipantsController();
  });

  tearDown(() {
    controller.dispose();
  });

  group('initial state', () {
    test('starts at resumen subroute', () {
      expect(controller.subroute, ParticipantsSubroute.resumen);
    });
  });

  group('selectSubrouteByIndex', () {
    test('changes to participantes', () {
      controller.selectSubrouteByIndex(1);
      expect(controller.subroute, ParticipantsSubroute.participantes);
    });

    test('changes to historial', () {
      controller.selectSubrouteByIndex(2);
      expect(controller.subroute, ParticipantsSubroute.historial);
    });

    test('does nothing if already on the same subroute', () {
      controller.selectSubrouteByIndex(1);
      expect(controller.subroute, ParticipantsSubroute.participantes);

      controller.selectSubrouteByIndex(1);
      expect(controller.subroute, ParticipantsSubroute.participantes);
    });
  });

  group('reset', () {
    test('goes back to resumen', () {
      controller.selectSubrouteByIndex(2);
      expect(controller.subroute, ParticipantsSubroute.historial);

      controller.reset();
      expect(controller.subroute, ParticipantsSubroute.resumen);
    });

    test('does nothing if already at resumen', () {
      controller.reset();
      expect(controller.subroute, ParticipantsSubroute.resumen);
    });
  });
}
