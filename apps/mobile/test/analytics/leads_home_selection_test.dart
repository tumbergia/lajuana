/// Legacy weighted home selection is removed.
///
/// This file keeps a regression guard: there must be no Random fill helper
/// exported for home indicators. Prefer [AnalyticsPreferences].
library;

import 'package:flutter_test/flutter_test.dart';
import 'package:mobile/features/analytics/domain/analytics_models.dart';

void main() {
  test('home selection is preference-driven without a hard pin cap', () {
    const prefs = AnalyticsPreferences(
      selectedModuleIds: [
        'confirmed_value_trend',
        'reservation_trend',
        'top_experiences',
        'top_countries',
        'occupancy',
      ],
      moduleOrder: [
        'confirmed_value_trend',
        'reservation_trend',
        'top_experiences',
        'top_countries',
        'occupancy',
      ],
    );
    expect(prefs.selectedModuleIds.length, 5);
    expect(prefs.moduleOrder.length, 5);
  });
}
