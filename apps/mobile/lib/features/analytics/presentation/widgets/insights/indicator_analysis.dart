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

double _median(List<double> values) {
  final sorted = List<double>.from(values)..sort();
  final mid = sorted.length ~/ 2;
  if (sorted.length.isOdd) return sorted[mid];
  return (sorted[mid - 1] + sorted[mid]) / 2;
}

/// Deterministic multi-parameter analysis mirroring the API export engine.
List<String> buildIndicatorAnalysis(AnalyticsModule module) {
  final lines = <String>[];
  final insight = module.insightText?.trim();
  if (insight != null && insight.isNotEmpty) lines.add(insight);

  final pv = module.primaryValue;
  if (pv != null) {
    lines.add('Valor principal: ${pv.formatted} ${pv.unit}.');
  }

  final cmp = module.comparison;
  if (cmp != null) {
    if (cmp.label != null && cmp.label!.isNotEmpty) {
      lines.add('Comparación: ${cmp.label}.');
    }
    if (cmp.percentageDelta != null) {
      final d = cmp.percentageDelta!;
      final sign = d > 0 ? '+' : '';
      lines.add('Variación porcentual: $sign${_fmt(d)}%.');
    }
    if (cmp.absoluteFormatted != null && cmp.absoluteFormatted!.isNotEmpty) {
      lines.add('Cambio absoluto: ${cmp.absoluteFormatted}.');
    }
    if (cmp.previousFormatted != null && cmp.previousFormatted!.isNotEmpty) {
      lines.add('Periodo anterior: ${cmp.previousFormatted}.');
    }
    if (!cmp.sufficientSample) {
      lines.add(
        'Muestra del periodo anterior limitada: la variación se interpreta con cautela.',
      );
    }
  }

  lines.addAll(_seriesLines(module));
  lines.addAll(_breakdownLines(module));
  lines.addAll(_rankingLines(module));

  lines.add(
    'Periodo analizado: ${module.period.label} '
    '(${module.period.start} → ${module.period.end}).',
  );

  final seen = <String>{};
  return [
    for (final line in lines)
      if (line.trim().isNotEmpty && seen.add(line.trim())) line.trim(),
  ];
}

/// Compact key/value parameters for the detail sheet.
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
    rows.add((key: 'Δ %', value: '$sign${_fmt(d)}%'));
  }
  if (cmp?.absoluteFormatted != null && cmp!.absoluteFormatted!.isNotEmpty) {
    rows.add((key: 'Δ absoluto', value: cmp.absoluteFormatted!));
  }
  if (module.series.isNotEmpty && module.series.first.points.isNotEmpty) {
    final vals = module.series.first.points.map((p) => p.raw).toList();
    rows.add((key: 'Puntos', value: '${vals.length}'));
    rows.add((
      key: 'Mín / Máx',
      value: '${_fmt(vals.reduce(math.min))} / ${_fmt(vals.reduce(math.max))}',
    ));
    rows.add((
      key: 'Promedio',
      value: _fmt(vals.reduce((a, b) => a + b) / vals.length),
    ));
    if (vals.length >= 3) {
      rows.add((key: 'Desvío std', value: _fmt(_pstdev(vals))));
    }
  }
  if (module.breakdown.isNotEmpty) {
    final total =
        module.breakdown.fold<double>(0, (s, i) => s + i.rawValue);
    rows.add((key: 'Categorías', value: '${module.breakdown.length}'));
    rows.add((key: 'Total desglose', value: _fmt(total)));
    final top = module.breakdown.reduce(
      (a, b) => a.rawValue >= b.rawValue ? a : b,
    );
    final sh = _share(top.sharePercentage, top.rawValue, total);
    rows.add((
      key: 'Líder',
      value: '${top.label} (${sh != null ? _fmt(sh) : '—'}%)',
    ));
    if (total > 0 && module.breakdown.length >= 2) {
      final hhi = module.breakdown
              .map((i) => i.rawValue / total)
              .fold<double>(0, (s, p) => s + p * p) *
          10000;
      rows.add((key: 'HHI', value: _fmt(hhi, digits: 0)));
    }
  }
  if (module.ranking.isNotEmpty) {
    rows.add((key: 'Filas ranking', value: '${module.ranking.length}'));
    final top = module.ranking.first;
    rows.add((key: '#1', value: top.label));
    if (top.sharePercentage != null) {
      rows.add((key: '#1 participación', value: '${_fmt(top.sharePercentage!)}%'));
    }
    if (module.ranking.length >= 2) {
      rows.add((
        key: 'Brecha #1-#2',
        value: _fmt(top.rawValue - module.ranking[1].rawValue),
      ));
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
      }
    }
  }
  rows.add((key: 'Periodo', value: module.period.label));
  return rows;
}

List<String> _seriesLines(AnalyticsModule module) {
  final lines = <String>[];
  final viz = module.visualization;
  final useSeries = module.series.isNotEmpty &&
      (viz == 'line' ||
          viz == 'sparkline' ||
          viz == 'kpi' ||
          (module.breakdown.isEmpty && module.ranking.isEmpty));
  if (!useSeries) return lines;

  for (final series in module.series) {
    if (series.points.isEmpty) continue;
    final values = series.points.map((p) => p.raw).toList();
    final n = values.length;
    final total = values.reduce((a, b) => a + b);
    final mn = values.reduce(math.min);
    final mx = values.reduce(math.max);
    final avg = total / n;
    final med = _median(values);
    final unit = series.unit.isNotEmpty
        ? series.unit
        : (module.primaryValue?.unit ?? '');
    final u = unit.isNotEmpty ? ' $unit' : '';
    final peak = series.points.reduce((a, b) => a.raw >= b.raw ? a : b);
    final trough = series.points.reduce((a, b) => a.raw <= b.raw ? a : b);

    lines.add(
      '${series.label}: n=$n periodos, suma=${_fmt(total)}$u, '
      'promedio=${_fmt(avg)}$u, mediana=${_fmt(med)}$u.',
    );
    lines.add(
      'Rango: mínimo ${_fmt(mn)}$u (${trough.label}) → '
      'máximo ${_fmt(mx)}$u (${peak.label}); amplitud ${_fmt(mx - mn)}$u.',
    );
    if (n >= 3) {
      final sd = _pstdev(values);
      final cv = avg != 0 ? sd / avg * 100 : 0.0;
      lines.add(
        'Dispersión: desvío estándar ${_fmt(sd)}$u '
        '(coef. variación ${_fmt(cv)}%).',
      );
    }
    final zeros = values.where((v) => v == 0).length;
    if (zeros > 0) {
      lines.add('Periodos en cero: $zeros de $n (${(zeros / n * 100).round()}%).');
    }
    final first = values.first;
    final last = values.last;
    if (first != 0) {
      final deltaPct = (last - first) / first.abs() * 100;
      final sign = deltaPct > 0 ? '+' : '';
      lines.add(
        'Inicio→fin: ${_fmt(first)} → ${_fmt(last)}$u ($sign${_fmt(deltaPct)}%).',
      );
    } else {
      lines.add('Inicio→fin: ${_fmt(first)} → ${_fmt(last)}$u.');
    }
    if (n >= 4) {
      final mid = n ~/ 2;
      final a1 = values.sublist(0, mid).reduce((a, b) => a + b) / mid;
      final a2 = values.sublist(mid).reduce((a, b) => a + b) / (n - mid);
      if (a1 == 0 && a2 == 0) {
        lines.add('Tendencia: estable en cero.');
      } else if (a1 == 0) {
        lines.add('Tendencia: aceleración desde periodos iniciales en cero.');
      } else {
        final halfPct = (a2 - a1) / a1.abs() * 100;
        if (halfPct.abs() < 5) {
          lines.add('Tendencia: relativamente estable entre mitades del periodo.');
        } else if (halfPct > 0) {
          lines.add(
            'Tendencia alcista: segunda mitad ${_fmt(halfPct)}% por encima de la primera.',
          );
        } else {
          lines.add(
            'Tendencia bajista: segunda mitad ${_fmt(halfPct.abs())}% por debajo de la primera.',
          );
        }
      }
    }
  }
  return lines;
}

List<String> _breakdownLines(AnalyticsModule module) {
  final items = module.breakdown;
  if (items.isEmpty) return [];
  final lines = <String>[];
  final total = items.fold<double>(0, (s, i) => s + i.rawValue);
  final n = items.length;
  final unit = items.first.unit.isNotEmpty
      ? items.first.unit
      : (module.primaryValue?.unit ?? 'reservas');
  final ordered = List<BreakdownItem>.from(items)
    ..sort((a, b) => b.rawValue.compareTo(a.rawValue));
  final top = ordered.first;
  final bottom = ordered.last;
  final topShare = _share(top.sharePercentage, top.rawValue, total);
  final botShare = _share(bottom.sharePercentage, bottom.rawValue, total);

  lines.add('Categorías: $n; total=${_fmt(total)} $unit.');
  if (topShare != null) {
    lines.add(
      'Líder: ${top.label} = ${_fmt(top.rawValue)} $unit (${_fmt(topShare)}%).',
    );
  }
  if (n >= 2 && botShare != null && bottom.key != top.key) {
    lines.add(
      'Menor: ${bottom.label} = ${_fmt(bottom.rawValue)} $unit (${_fmt(botShare)}%).',
    );
  }
  if (n >= 2 && total > 0) {
    final top2 = ordered.take(2).fold<double>(0, (s, i) => s + i.rawValue);
    lines.add('Concentración top-2: ${_fmt(top2 / total * 100)}% del total.');
    final hhi = items
            .map((i) => i.rawValue / total)
            .fold<double>(0, (s, p) => s + p * p) *
        10000;
    if (hhi >= 2500) {
      lines.add(
        'Índice de concentración (HHI) ${_fmt(hhi, digits: 0)}: mercado concentrado.',
      );
    } else if (hhi >= 1500) {
      lines.add(
        'Índice de concentración (HHI) ${_fmt(hhi, digits: 0)}: concentración moderada.',
      );
    } else {
      lines.add(
        'Índice de concentración (HHI) ${_fmt(hhi, digits: 0)}: distribución dispersa.',
      );
    }
  }

  final keys = {for (final i in items) i.key: i};
  if (module.id == 'reservation_origins') {
    final social = ['whatsapp', 'facebook', 'instagram']
        .where(keys.containsKey)
        .fold<double>(0, (s, k) => s + keys[k]!.rawValue);
    final email = keys['email']?.rawValue ?? 0;
    if (total > 0) {
      lines.add(
        'Redes sociales (WA+FB+IG): ${_fmt(social)} (${_fmt(social / total * 100)}%); '
        'correo: ${_fmt(email)} (${_fmt(email / total * 100)}%).',
      );
    }
  } else if (module.id == 'reservation_status') {
    final risk = ['pending_payment', 'payment_received']
        .where(keys.containsKey)
        .fold<double>(0, (s, k) => s + keys[k]!.rawValue);
    if (risk > 0 && total > 0) {
      lines.add(
        'Pendientes de cobro/verificación: ${_fmt(risk)} (${_fmt(risk / total * 100)}%).',
      );
    }
  } else if (module.id == 'payment_status') {
    final openReview = ['pending', 'received']
        .where(keys.containsKey)
        .fold<double>(0, (s, k) => s + keys[k]!.rawValue);
    if (openReview > 0) {
      lines.add('Comprobantes por revisar: ${_fmt(openReview)}.');
    }
    final verified = keys['verified'];
    if (verified != null && total > 0) {
      lines.add(
        'Tasa verificada: ${_fmt(verified.rawValue / total * 100)}% '
        '(${_fmt(verified.rawValue)} de ${_fmt(total)}).',
      );
    }
  } else if (module.id == 'participant_readiness') {
    final pending = keys['pending'];
    if (pending != null && total > 0) {
      lines.add(
        'Pendientes de registro: ${_fmt(pending.rawValue)} '
        '(${_fmt(pending.rawValue / total * 100)}%).',
      );
    }
  } else if (module.id == 'equine_availability') {
    final available = keys['available'];
    if (available != null && total > 0) {
      lines.add(
        'Disponibles: ${_fmt(available.rawValue)} '
        '(${_fmt(available.rawValue / total * 100)}%).',
      );
    }
  } else if (module.id == 'action_center' || module.id == 'equine_care_alerts') {
    lines.add('Ítems abiertos: ${_fmt(total)}.');
    if (ordered.isNotEmpty) {
      lines.add(
        'Cola principal: ${ordered.first.label} (${_fmt(ordered.first.rawValue)}).',
      );
    }
  }
  return lines;
}

List<String> _rankingLines(AnalyticsModule module) {
  final items = module.ranking;
  if (items.isEmpty) return [];
  final lines = <String>[];
  final n = items.length;
  final total = items.fold<double>(0, (s, i) => s + i.rawValue);
  final avg = n > 0 ? total / n : 0.0;
  final unit = items.first.unit.isNotEmpty
      ? items.first.unit
      : (module.primaryValue?.unit ?? '');
  final top = items.first;

  lines.add('Elementos en ranking: $n; promedio=${_fmt(avg)} $unit.');
  if (top.sharePercentage != null) {
    lines.add(
      'Líder: ${top.label} = ${top.formattedValue} (${_fmt(top.sharePercentage!)}%).',
    );
  } else {
    lines.add('Líder: ${top.label} = ${top.formattedValue}.');
  }
  if (n >= 2) {
    final second = items[1];
    final gap = top.rawValue - second.rawValue;
    final gapPct = top.rawValue != 0 ? gap / top.rawValue * 100 : 0.0;
    lines.add(
      'Brecha #1 vs #2: ${_fmt(gap)} $unit '
      '(${_fmt(gapPct)}% del líder) — ${second.label}.',
    );
  }
  if (n >= 3 && total > 0) {
    final top3 = items.take(3).fold<double>(0, (s, i) => s + i.rawValue);
    lines.add('Top 3 concentran ${_fmt(top3 / total * 100)}% del total mostrado.');
  }

  if (module.id == 'occupancy') {
    final shares =
        items.map((i) => i.sharePercentage).whereType<double>().toList();
    if (shares.isNotEmpty) {
      final avgOcc = shares.reduce((a, b) => a + b) / shares.length;
      lines.add('Ocupación media de salidas: ${_fmt(avgOcc)}%.');
      final low = items.where((r) => (r.sharePercentage ?? 0) < 25).length;
      final mid = items
          .where((r) {
            final s = r.sharePercentage ?? 0;
            return s >= 25 && s < 75;
          })
          .length;
      final high = items.where((r) => (r.sharePercentage ?? 0) >= 75).length;
      lines.add('Umbrales: baja(<25%)=$low, media=$mid, alta(≥75%)=$high.');
    }
  } else if (module.id == 'top_countries') {
    lines.add('Países distintos en el top: $n.');
  } else if (module.id == 'equine_workload' && total > 0 && n >= 3) {
    final top3 = items.take(3).fold<double>(0, (s, i) => s + i.rawValue);
    lines.add('Concentración en 3 equinos: ${_fmt(top3 / total * 100)}%.');
  }
  return lines;
}
