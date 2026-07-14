import 'dart:math';

import 'package:flutter_test/flutter_test.dart';
import 'package:mobile/features/analytics/presentation/controllers/leads_controller.dart';

LeadItem _lead({
  required String id,
  bool homeEligible = true,
  int homePriority = 1,
}) {
  return LeadItem(
    id: id,
    category: 'test',
    title: id,
    value: '1',
    unit: '',
    description: '',
    icon: 'help',
    order: 0,
    homeEligible: homeEligible,
    homePriority: homePriority,
  );
}

void main() {
  test('pins come first and fill from eligible pool', () {
    final all = [
      _lead(id: 'a'),
      _lead(id: 'b'),
      _lead(id: 'c'),
      _lead(id: 'd'),
      _lead(id: 'e'),
      _lead(id: 'f', homeEligible: false),
    ];
    final home = selectHomeLeads(
      allLeads: all,
      pinnedLeadIds: ['c', 'a'],
      excludedLeadIds: const [],
      random: Random(1),
      limit: 5,
    );
    expect(home.map((l) => l.id).take(2), ['c', 'a']);
    expect(home.length, 5);
    expect(home.map((l) => l.id), isNot(contains('f')));
  });

  test('excluded and blacklisted stay out of fill pool', () {
    final all = [
      _lead(id: 'pin'),
      _lead(id: 'ok1'),
      _lead(id: 'ok2'),
      _lead(id: 'blocked', homeEligible: false),
      _lead(id: 'excluded'),
    ];
    final home = selectHomeLeads(
      allLeads: all,
      pinnedLeadIds: ['pin'],
      excludedLeadIds: ['excluded'],
      random: Random(42),
      limit: 5,
    );
    final ids = home.map((l) => l.id).toSet();
    expect(ids.contains('pin'), isTrue);
    expect(ids.contains('blocked'), isFalse);
    expect(ids.contains('excluded'), isFalse);
    expect(ids.contains('ok1') || ids.contains('ok2'), isTrue);
  });

  test('caps at five pins', () {
    final all = [
      for (final id in ['1', '2', '3', '4', '5', '6']) _lead(id: id),
    ];
    final home = selectHomeLeads(
      allLeads: all,
      pinnedLeadIds: ['1', '2', '3', '4', '5', '6'],
      excludedLeadIds: const [],
      random: Random(0),
      limit: 5,
    );
    expect(home.map((l) => l.id).toList(), ['1', '2', '3', '4', '5']);
  });

  test('missing pin ids are ignored', () {
    final home = selectHomeLeads(
      allLeads: [_lead(id: 'only')],
      pinnedLeadIds: ['gone', 'only'],
      excludedLeadIds: const [],
      random: Random(0),
      limit: 5,
    );
    expect(home.map((l) => l.id).toList(), ['only']);
  });

  test('higher homePriority is preferred in fill', () {
    final all = [
      _lead(id: 'money', homePriority: 100),
      for (var i = 0; i < 20; i++) _lead(id: 'low_$i', homePriority: 1),
    ];
    var moneyHits = 0;
    for (var seed = 0; seed < 40; seed++) {
      final home = selectHomeLeads(
        allLeads: all,
        pinnedLeadIds: const [],
        excludedLeadIds: const [],
        random: Random(seed),
        limit: 1,
      );
      if (home.single.id == 'money') moneyHits++;
    }
    expect(moneyHits, greaterThan(25));
  });
}
