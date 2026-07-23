import 'package:flutter/material.dart';

const _monthAbbreviations = [
  'ENE',
  'FEB',
  'MAR',
  'ABR',
  'MAY',
  'JUN',
  'JUL',
  'AGO',
  'SEP',
  'OCT',
  'NOV',
  'DIC',
];

String _normalizeDate(String date) {
  if (date.contains('T')) return date.split('T').first;
  if (date.contains(' ')) return date.split(' ').first;
  return date;
}

class ReservationDateLeading extends StatelessWidget {
  const ReservationDateLeading({super.key, required this.requestedDate});

  final String? requestedDate;

  @override
  Widget build(BuildContext context) {
    final raw = requestedDate;
    if (raw == null || raw.isEmpty) {
      return const SizedBox.shrink();
    }

    final date = DateTime.tryParse(_normalizeDate(raw));
    if (date == null) {
      return const SizedBox.shrink();
    }

    final scheme = Theme.of(context).colorScheme;
    final textTheme = Theme.of(context).textTheme;

    return Container(
      width: 48,
      height: 48,
      decoration: BoxDecoration(
        color: scheme.surfaceContainerHighest,
        borderRadius: BorderRadius.circular(4),
      ),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Text(
            '${date.day}',
            style: textTheme.titleMedium?.copyWith(
              fontWeight: FontWeight.w800,
              color: scheme.onSurface,
              height: 1,
            ),
          ),
          Text(
            _monthAbbreviations[date.month - 1],
            style: textTheme.labelSmall?.copyWith(
              fontWeight: FontWeight.w700,
              color: scheme.onSurfaceVariant,
              height: 1.2,
            ),
          ),
        ],
      ),
    );
  }
}
