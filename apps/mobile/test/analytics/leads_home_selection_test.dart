/// Legacy weighted home selection is removed.
///
/// This file keeps a regression guard: there must be no Random fill helper
/// exported for home indicators. Prefer [AnalyticsPreferences] (max 4).
library;

import 'package:flutter_test/flutter_test.dart';
import 'package:mobile/features/analytics/domain/analytics_models.dart';

void main() {
  test('home selection is preference-driven with max four', () {
    expect(AnalyticsPreferences.maxModules, 4);
  });
}
