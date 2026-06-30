import 'package:flutter/material.dart';

import 'package:mobile_ui/src/theme/app_colors.dart';
import 'package:mobile_ui/src/theme/theme_extensions.dart';
import 'package:mobile/features/reservations/presentation/controllers/reservations_list_controller.dart';
import 'package:mobile/features/reservations/presentation/models/reservation_view_models.dart';
import 'package:mobile/features/reservations/presentation/widgets/reservation_row_card.dart';

// ── Locale constants ──

const _monthNames = [
  'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
  'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre',
];

const _weekdayLabels = ['LUN', 'MAR', 'MIE', 'JUE', 'VIE', 'SAB', 'DOM'];

/// Normaliza una fecha string al formato ISO `YYYY-MM-DD`.
/// Soporta: `"2024-10-24"`, `"2024-10-24T00:00:00"`, `"2024-10-24 00:00:00"`.
String _normalizeDate(String date) {
  if (date.contains('T')) return date.split('T').first;
  if (date.contains(' ')) return date.split(' ').first;
  return date;
}

String _dateKey(DateTime day) {
  return '${day.year}-${day.month.toString().padLeft(2, '0')}-${day.day.toString().padLeft(2, '0')}';
}

Map<String, List<ReservationRecord>> _groupByDate(
  List<ReservationRecord> items,
) {
  final map = <String, List<ReservationRecord>>{};
  for (final item in items) {
    final raw = item.requestedDate;
    if (raw == null || raw.isEmpty) continue;
    final normalized = _normalizeDate(raw);
    map.putIfAbsent(normalized, () => []);
    map[normalized]!.add(item);
  }
  return map;
}

bool _isSameDay(DateTime a, DateTime b) =>
    a.year == b.year && a.month == b.month && a.day == b.day;

bool _isToday(DateTime day) => _isSameDay(day, DateTime.now());

// ══════════════════════════════════════════════════════════════════════════════
//  ReservationCalendarSheet — full-screen monthly calendar for reservations
// ══════════════════════════════════════════════════════════════════════════════

/// Pantalla modal con calendario mensual.
///
/// Escucha cambios del [controller] para reflejar datos actualizados.
/// Los días con reservas aparecen en verde.
/// Tap en un día muestra las reservas de esa fecha.
class ReservationCalendarSheet extends StatefulWidget {
  final ReservationsListController controller;
  final void Function(String reservationId) onOpenDetail;

  const ReservationCalendarSheet({
    super.key,
    required this.controller,
    required this.onOpenDetail,
  });

  @override
  State<ReservationCalendarSheet> createState() =>
      _ReservationCalendarSheetState();
}

class _ReservationCalendarSheetState extends State<ReservationCalendarSheet> {
  late DateTime _currentMonth;
  DateTime? _selectedDay;

  /// "2024-10-24" → reservas de ese día
  Map<String, List<ReservationRecord>> _reservationsByDate = {};

  @override
  void initState() {
    super.initState();
    final now = DateTime.now();
    _currentMonth = DateTime(now.year, now.month);
    _rebuildData();
    widget.controller.addListener(_onDataChanged);
  }

  @override
  void dispose() {
    widget.controller.removeListener(_onDataChanged);
    super.dispose();
  }

  void _onDataChanged() {
    _rebuildData();
  }

  void _rebuildData() {
    setState(() {
      _reservationsByDate = _groupByDate(widget.controller.allItems);
    });
  }

  bool _hasReservations(DateTime day) =>
      _reservationsByDate.containsKey(_dateKey(day));

  List<ReservationRecord> _reservationsForDay(DateTime day) =>
      _reservationsByDate[_dateKey(day)] ?? [];

  void _goToPreviousMonth() {
    setState(() {
      _currentMonth = DateTime(_currentMonth.year, _currentMonth.month - 1);
      _selectedDay = null;
    });
  }

  void _goToNextMonth() {
    setState(() {
      _currentMonth = DateTime(_currentMonth.year, _currentMonth.month + 1);
      _selectedDay = null;
    });
  }

  void _onDayTap(DateTime day) {
    setState(() {
      if (_selectedDay != null && _isSameDay(_selectedDay!, day)) {
        _selectedDay = null;
      } else {
        _selectedDay = day;
      }
    });
  }

  // ── Build ──

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final scheme = theme.colorScheme;
    final textTheme = theme.textTheme;
    final tokens = theme.appTokens;

    return Scaffold(
      appBar: AppBar(
        title: Text(
          'Calendario de reservas',
          style: textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w700),
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.close_rounded),
            onPressed: () => Navigator.of(context).pop(),
          ),
        ],
      ),
      body: _reservationsByDate.isEmpty
          ? _buildEmptyData(scheme, textTheme)
          : Column(
              children: [
                // ── Monthly calendar ──
                Padding(
                  padding: EdgeInsets.fromLTRB(
                    tokens.spaceLg, tokens.spaceSm, tokens.spaceLg, 0,
                  ),
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      _buildMonthSelector(textTheme, scheme),
                      SizedBox(height: tokens.spaceMd),
                      _buildWeekdayHeaders(textTheme, scheme),
                      SizedBox(height: tokens.spaceSm),
                      _buildCalendarGrid(scheme, textTheme, tokens),
                      SizedBox(height: tokens.spaceLg),
                    ],
                  ),
                ),

                // ── Separator ──
                Padding(
                  padding: EdgeInsets.symmetric(horizontal: tokens.spaceLg),
                  child: Divider(height: 1, color: scheme.outlineVariant),
                ),

                // ── Reservations for selected day ──
                Expanded(
                  child: _buildDayReservations(textTheme, scheme, tokens),
                ),
              ],
            ),
    );
  }

  Widget _buildEmptyData(ColorScheme scheme, TextTheme textTheme) {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(
            Icons.event_note_rounded,
            size: 48,
            color: scheme.onSurfaceVariant.withValues(alpha: 0.5),
          ),
          const SizedBox(height: 16),
          Text(
            'Cargando reservas...',
            style: textTheme.bodyMedium?.copyWith(
              color: scheme.onSurfaceVariant,
            ),
          ),
        ],
      ),
    );
  }

  // ── Month selector ──

  Widget _buildMonthSelector(TextTheme textTheme, ColorScheme scheme) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        IconButton(
          icon: const Icon(Icons.chevron_left_rounded),
          onPressed: _goToPreviousMonth,
          color: scheme.onSurface,
        ),
        Text(
          '${_monthNames[_currentMonth.month - 1]} ${_currentMonth.year}',
          style: textTheme.titleLarge?.copyWith(
            fontWeight: FontWeight.w800,
            letterSpacing: 0.5,
          ),
        ),
        IconButton(
          icon: const Icon(Icons.chevron_right_rounded),
          onPressed: _goToNextMonth,
          color: scheme.onSurface,
        ),
      ],
    );
  }

  // ── Weekday headers ──

  Widget _buildWeekdayHeaders(TextTheme textTheme, ColorScheme scheme) {
    return Row(
      children: List.generate(7, (i) {
        return Expanded(
          child: Center(
            child: Text(
              _weekdayLabels[i],
              style: textTheme.labelSmall?.copyWith(
                color: scheme.onSurfaceVariant,
                letterSpacing: 1.0,
              ),
            ),
          ),
        );
      }),
    );
  }

  // ── Calendar grid ──

  Widget _buildCalendarGrid(
    ColorScheme scheme,
    TextTheme textTheme,
    AppThemeTokens tokens,
  ) {
    final firstWeekday =
        DateTime(_currentMonth.year, _currentMonth.month, 1).weekday;
    final offset = firstWeekday - 1; // 0 = Mon
    final daysInMonth =
        DateTime(_currentMonth.year, _currentMonth.month + 1, 0).day;
    final totalCells = offset + daysInMonth;
    final weeks = (totalCells / 7).ceil();

    return LayoutBuilder(
      builder: (context, constraints) {
        final cellSize = (constraints.maxWidth / 7).floorToDouble();

        return Column(
          mainAxisSize: MainAxisSize.min,
          children: List.generate(weeks, (weekIndex) {
            return SizedBox(
              height: cellSize,
              child: Row(
                children: List.generate(7, (dayIndex) {
                  final cellIndex = weekIndex * 7 + dayIndex;
                  final day = cellIndex - offset + 1;

                  if (day < 1 || day > daysInMonth) {
                    return const Expanded(child: SizedBox.shrink());
                  }

                  final date = DateTime(
                    _currentMonth.year, _currentMonth.month, day,
                  );
                  final hasRes = _hasReservations(date);
                  final isSelected =
                      _selectedDay != null && _isSameDay(_selectedDay!, date);
                  final today = _isToday(date);

                  return Expanded(
                    child: _DayCell(
                      day: day,
                      hasReservations: hasRes,
                      isSelected: isSelected,
                      isToday: today,
                      onTap: () => _onDayTap(date),
                    ),
                  );
                }),
              ),
            );
          }),
        );
      },
    );
  }

  // ── Reservations list for selected day ──

  Widget _buildDayReservations(
    TextTheme textTheme,
    ColorScheme scheme,
    AppThemeTokens tokens,
  ) {
    if (_selectedDay == null) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              Icons.touch_app_rounded,
              size: 48,
              color: scheme.onSurfaceVariant.withValues(alpha: 0.5),
            ),
            SizedBox(height: tokens.spaceMd),
            Text(
              'Selecciona un día con reservas',
              style: textTheme.bodyMedium?.copyWith(
                color: scheme.onSurfaceVariant,
              ),
            ),
          ],
        ),
      );
    }

    final dayReservations = _reservationsForDay(_selectedDay!);

    if (dayReservations.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              Icons.event_busy_rounded,
              size: 48,
              color: scheme.onSurfaceVariant.withValues(alpha: 0.5),
            ),
            SizedBox(height: tokens.spaceMd),
            Text(
              'No hay reservas para esta fecha',
              style: textTheme.bodyMedium?.copyWith(
                color: scheme.onSurfaceVariant,
              ),
            ),
          ],
        ),
      );
    }

    final dayStr =
        '${_selectedDay!.day.toString().padLeft(2, '0')}/${_selectedDay!.month.toString().padLeft(2, '0')}/${_selectedDay!.year}';

    return ListView(
      padding: EdgeInsets.fromLTRB(
        tokens.spaceLg, tokens.spaceSm, tokens.spaceLg, tokens.spaceXl,
      ),
      children: [
        Padding(
          padding: EdgeInsets.only(bottom: tokens.spaceMd),
          child: Text(
            'Reservas del $dayStr',
            style: textTheme.titleSmall?.copyWith(
              fontWeight: FontWeight.w700,
              color: scheme.onSurface,
            ),
          ),
        ),
        ...dayReservations.map((reservation) {
          return Padding(
            padding: EdgeInsets.only(bottom: tokens.spaceSm),
            child: ReservationRowCard(
              reservation: reservation,
              subtitle: reservation.experienceName ?? '',
              highlightIfPending: reservation.status == 'pendientes',
              openDetailsOnTap: true,
              onOpenDetail: () =>
                  widget.onOpenDetail(reservation.id ?? reservation.code),
            ),
          );
        }),
      ],
    );
  }
}

// ══════════════════════════════════════════════════════════════════════════════
//  _DayCell — individual day inside the calendar grid
// ══════════════════════════════════════════════════════════════════════════════

class _DayCell extends StatelessWidget {
  final int day;
  final bool hasReservations;
  final bool isSelected;
  final bool isToday;
  final VoidCallback onTap;

  const _DayCell({
    required this.day,
    required this.hasReservations,
    required this.isSelected,
    required this.isToday,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final textTheme = Theme.of(context).textTheme;

    // ── Decide background & text color ──
    // Priority: isSelected > hasReservations > normal

    Color textColor = scheme.onSurface;
    FontWeight fontWeight = FontWeight.w400;
    BoxDecoration? decoration;

    if (isSelected) {
      textColor = AppColors.success;
      fontWeight = FontWeight.w700;
      decoration = BoxDecoration(
        color: AppColors.success.withValues(alpha: 0.25),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: AppColors.success, width: 1.5),
      );
    } else if (hasReservations) {
      textColor = AppColors.success;
      fontWeight = FontWeight.w600;
      decoration = BoxDecoration(
        color: AppColors.success.withValues(alpha: 0.12),
        borderRadius: BorderRadius.circular(8),
      );
    }

    // Today: subtle underline / bold, but DON'T override green
    // We add a small dot indicator below the number instead
    return Padding(
      padding: const EdgeInsets.all(2),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(8),
        child: Container(
          decoration: decoration,
          alignment: Alignment.center,
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Text(
                '$day',
                style: textTheme.bodyMedium?.copyWith(
                  color: textColor,
                  fontWeight: isToday ? FontWeight.w700 : fontWeight,
                ),
              ),
              if (isToday)
                Container(
                  width: 4,
                  height: 4,
                  margin: const EdgeInsets.only(top: 2),
                  decoration: BoxDecoration(
                    color: isSelected || hasReservations
                        ? AppColors.success
                        : scheme.primary,
                    shape: BoxShape.circle,
                  ),
                ),
            ],
          ),
        ),
      ),
    );
  }
}
