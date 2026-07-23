import 'dart:math' as math;

import 'package:mobile/features/analytics/domain/analytics_models.dart';

String _fmt(num n, {int digits = 1}) {
  if ((n - n.round()).abs() < 1e-9) return '${n.round()}';
  return n.toStringAsFixed(digits);
}

double? _share(double? share, double raw, double total) {
  if (share != null) return share;
  if (total > 0) return (raw / total * 100 * 10).roundToDouble() / 10;
  return null;
}

double _pstdev(List<double> values) {
  if (values.length < 2) return 0;
  final mean = values.reduce((a, b) => a + b) / values.length;
  final sumSq = values.fold<double>(0, (s, v) => s + (v - mean) * (v - mean));
  return math.sqrt(sumSq / values.length);
}

/// Prefer server paragraphs; fall back to a short local narrative for cache.
List<String> buildIndicatorAnalysis(AnalyticsModule module) {
  if (module.analysis.isNotEmpty) {
    return List<String>.from(module.analysis);
  }

  final lines = <String>[];
  final insight = module.insightText?.trim();
  if (insight != null && insight.isNotEmpty) lines.add(insight);

  final pv = module.primaryValue;
  if (pv != null) {
    lines.add(
      'El valor principal en ${module.period.label} es ${pv.formatted} ${pv.unit}.',
    );
  }

  final cmp = module.comparison;
  if (cmp?.label != null && cmp!.label!.isNotEmpty) {
    lines.add('Respecto al periodo anterior: ${cmp.label}.');
  } else if (cmp?.percentageDelta != null) {
    final d = cmp!.percentageDelta!;
    final sign = d > 0 ? '+' : '';
    lines.add(
      'Respecto al periodo anterior: variación de $sign${_fmt(d)}%.',
    );
  }

  lines.add(
    'Usa este indicador junto con ocupación, pagos y disponibilidad. '
    'Define una acción concreta a partir del hallazgo principal.',
  );

  final seen = <String>{};
  return [
    for (final line in lines)
      if (line.trim().isNotEmpty && seen.add(line.trim())) line.trim(),
  ];
}

/// Compact key/value parameters for the detail sheet — plain language.
List<({String key, String value})> indicatorParameterRows(
  AnalyticsModule module,
) {
  final rows = <({String key, String value})>[];
  final pv = module.primaryValue;
  if (pv != null) {
    rows.add((key: 'Valor', value: '${pv.formatted} ${pv.unit}'.trim()));
  }
  final cmp = module.comparison;
  if (cmp?.percentageDelta != null) {
    final d = cmp!.percentageDelta!;
    final sign = d > 0 ? '+' : '';
    rows.add((key: 'Cambio vs periodo anterior', value: '$sign${_fmt(d)}%'));
  }
  if (cmp?.absoluteFormatted != null && cmp!.absoluteFormatted!.isNotEmpty) {
    rows.add((key: 'Cambio absoluto', value: cmp.absoluteFormatted!));
  }

  if (module.series.isNotEmpty && module.series.first.points.isNotEmpty) {
    final vals = module.series.first.points.map((p) => p.raw).toList();
    rows.add((key: 'Tramos en la serie', value: '${vals.length}'));
    rows.add((
      key: 'Mínimo / máximo',
      value: '${_fmt(vals.reduce(math.min))} / ${_fmt(vals.reduce(math.max))}',
    ));
    final avg = vals.reduce((a, b) => a + b) / vals.length;
    rows.add((key: 'Promedio', value: _fmt(avg)));
    if (vals.length >= 3 && avg != 0) {
      rows.add((
        key: 'Variabilidad',
        value: '${_fmt(_pstdev(vals) / avg * 100)}%',
      ));
    }
    if (vals.length >= 4) {
      final mid = vals.length ~/ 2;
      final a1 = vals.sublist(0, mid).reduce((a, b) => a + b) / mid;
      final a2 =
          vals.sublist(mid).reduce((a, b) => a + b) / (vals.length - mid);
      if (a1 != 0) {
        final half = (a2 - a1) / a1.abs() * 100;
        final sign = half >= 0 ? '+' : '';
        rows.add((key: '2ª mitad vs 1ª', value: '$sign${_fmt(half)}%'));
      }
    }
  }

  if (module.breakdown.isNotEmpty) {
    final total =
        module.breakdown.fold<double>(0, (s, i) => s + i.rawValue);
    rows.add((key: 'Categorías', value: '${module.breakdown.length}'));
    rows.add((key: 'Total del desglose', value: _fmt(total)));
    final top = module.breakdown.reduce(
      (a, b) => a.rawValue >= b.rawValue ? a : b,
    );
    final sh = _share(top.sharePercentage, top.rawValue, total);
    rows.add((
      key: 'Líder',
      value: '${top.label} (${sh != null ? _fmt(sh) : '—'}%)',
    ));
    if (total > 0 && module.breakdown.length >= 2) {
      final ordered = List<BreakdownItem>.from(module.breakdown)
        ..sort((a, b) => b.rawValue.compareTo(a.rawValue));
      final top2 =
          ordered.take(2).fold<double>(0, (s, i) => s + i.rawValue) /
              total *
              100;
      rows.add((key: 'Peso de los 2 líderes', value: '${_fmt(top2)}%'));
      final hhi = module.breakdown
              .map((i) => i.rawValue / total)
              .fold<double>(0, (s, p) => s + p * p) *
          10000;
      final conc = hhi >= 2500
          ? 'alta'
          : hhi >= 1500
              ? 'moderada'
              : 'dispersa';
      rows.add((key: 'Concentración', value: conc));
    }

    final keys = {for (final i in module.breakdown) i.key: i};
    if (module.id == 'reservation_origins' && total > 0) {
      final social = ['whatsapp', 'facebook', 'instagram']
          .where(keys.containsKey)
          .fold<double>(0, (s, k) => s + keys[k]!.rawValue);
      rows.add((
        key: 'Redes (WA+FB+IG)',
        value: '${_fmt(social)} (${_fmt(social / total * 100)}%)',
      ));
    } else if (module.id == 'payment_status') {
      final openReview = ['pending', 'received']
          .where(keys.containsKey)
          .fold<double>(0, (s, k) => s + keys[k]!.rawValue);
      rows.add((key: 'Por revisar', value: _fmt(openReview)));
      final verified = keys['verified'];
      if (verified != null && total > 0) {
        rows.add((
          key: 'Tasa verificada',
          value: '${_fmt(verified.rawValue / total * 100)}%',
        ));
      }
    } else if (module.id == 'participant_readiness') {
      final pending = keys['pending'];
      if (pending != null) {
        rows.add((
          key: 'Pendientes de registro',
          value: _fmt(pending.rawValue),
        ));
      }
    } else if (module.id == 'equine_availability') {
      final available = keys['available'];
      if (available != null && total > 0) {
        rows.add((
          key: 'Disponibles',
          value:
              '${_fmt(available.rawValue)} (${_fmt(available.rawValue / total * 100)}%)',
        ));
      }
    } else if (module.id == 'action_center' ||
        module.id == 'equine_care_alerts') {
      rows.add((key: 'Ítems abiertos', value: _fmt(total)));
    }
  }

  if (module.ranking.isNotEmpty) {
    rows.add((
      key: 'Elementos en el ranking',
      value: '${module.ranking.length}',
    ));
    final top = module.ranking.first;
    rows.add((key: '#1', value: top.label));
    if (top.sharePercentage != null) {
      rows.add((
        key: 'Participación del #1',
        value: '${_fmt(top.sharePercentage!)}%',
      ));
    }
    if (module.ranking.length >= 2) {
      rows.add((
        key: 'Brecha #1 vs #2',
        value: _fmt(top.rawValue - module.ranking[1].rawValue),
      ));
    }
    if (module.ranking.length >= 3) {
      final total =
          module.ranking.fold<double>(0, (s, i) => s + i.rawValue);
      if (total > 0) {
        final top3 = module.ranking
                .take(3)
                .fold<double>(0, (s, i) => s + i.rawValue) /
            total *
            100;
        rows.add((key: 'Peso del top 3', value: '${_fmt(top3)}%'));
      }
    }
    if (module.id == 'occupancy') {
      final shares = module.ranking
          .map((r) => r.sharePercentage)
          .whereType<double>()
          .toList();
      if (shares.isNotEmpty) {
        rows.add((
          key: 'Ocupación media',
          value:
              '${_fmt(shares.reduce((a, b) => a + b) / shares.length)}%',
        ));
        rows.add((
          key: 'Salidas <25%',
          value: '${shares.where((s) => s < 25).length}',
        ));
        rows.add((
          key: 'Salidas ≥75%',
          value: '${shares.where((s) => s >= 75).length}',
        ));
      }
    }
  }

  rows.add((key: 'Periodo', value: module.period.label));
  return rows;
}
