import 'package:flutter_test/flutter_test.dart';
import 'package:mobile/features/dashboard/presentation/controllers/dashboard_controller.dart';

void main() {
  late DashboardController controller;

  setUp(() {
    controller = DashboardController();
  });

  tearDown(() {
    controller.dispose();
  });

  group('initial state', () {
    test('starts at resumen subroute', () {
      expect(controller.subroute, DashboardSubroute.resumen);
    });
  });

  group('selectSubrouteByIndex', () {
    test('changes to pendientes', () {
      controller.selectSubrouteByIndex(1);
      expect(controller.subroute, DashboardSubroute.pendientes);
    });

    test('changes to salidas', () {
      controller.selectSubrouteByIndex(2);
      expect(controller.subroute, DashboardSubroute.salidas);
    });

    test('changes to sync', () {
      controller.selectSubrouteByIndex(3);
      expect(controller.subroute, DashboardSubroute.sync);
    });

    test('does nothing if already on the same subroute', () {
      controller.selectSubrouteByIndex(2);
      expect(controller.subroute, DashboardSubroute.salidas);

      // Same index — should not notify
      controller.selectSubrouteByIndex(2);
      expect(controller.subroute, DashboardSubroute.salidas);
    });

    test('out of bounds index throws RangeError', () {
      expect(() => controller.selectSubrouteByIndex(-1), throwsRangeError);
      expect(() => controller.selectSubrouteByIndex(99), throwsRangeError);
    });
  });

  group('reset', () {
    test('goes back to resumen', () {
      controller.selectSubrouteByIndex(2);
      expect(controller.subroute, DashboardSubroute.salidas);

      controller.reset();
      expect(controller.subroute, DashboardSubroute.resumen);
    });

    test('does nothing if already at resumen', () {
      controller.reset();
      expect(controller.subroute, DashboardSubroute.resumen);
    });
  });
}
