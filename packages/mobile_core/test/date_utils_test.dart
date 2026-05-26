import 'package:flutter_test/flutter_test.dart';
import 'package:mobile_core/mobile_core.dart';

void main() {
  group('formatDate', () {
    test('formats date-only ISO string', () {
      expect(formatDate('2026-05-30'), '30 de mayo de 2026');
    });

    test('formats ISO datetime string', () {
      expect(
        formatDate('2026-05-20T21:18:30.748000'),
        '20 de mayo de 2026',
      );
    });

    test('returns fallback for null input', () {
      expect(formatDate(null), 'Sin fecha');
    });

    test('returns fallback for empty string', () {
      expect(formatDate(''), 'Sin fecha');
    });

    test('returns fallback for unparseable string', () {
      expect(formatDate('not-a-date'), 'Sin fecha');
    });

    test('returns custom fallback when provided', () {
      expect(formatDate(null, fallback: ''), '');
      expect(formatDate('', fallback: '—'), '—');
    });

    test('handles first day of year', () {
      expect(formatDate('2026-01-01'), '1 de enero de 2026');
    });

    test('handles last day of year', () {
      expect(formatDate('2026-12-31'), '31 de diciembre de 2026');
    });

    test('handles single-digit day', () {
      expect(formatDate('2026-03-05'), '5 de marzo de 2026');
    });

    test('handles all months correctly', () {
      const expected = [
        'enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio',
        'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre',
      ];
      for (int i = 1; i <= 12; i++) {
        final monthStr = i.toString().padLeft(2, '0');
        final result = formatDate('2026-$monthStr-15');
        expect(result, '15 de ${expected[i - 1]} de 2026');
      }
    });
  });
}
