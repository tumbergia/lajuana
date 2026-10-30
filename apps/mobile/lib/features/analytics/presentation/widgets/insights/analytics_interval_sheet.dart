import 'package:flutter/material.dart';
import 'package:mobile_ui/mobile_ui.dart';

/// Bottom sheet de intervalo personalizado — mismo patrón editorial que el resto
/// de sheets de la app (handle, labels uppercase, [AppTextField], [AppButton]).
Future<DateTimeRange?> showAnalyticsIntervalSheet(
  BuildContext context, {
  DateTime? initialFrom,
  DateTime? initialTo,
}) {
  final tokens = Theme.of(context).appTokens;
  final now = DateTime.now();
  final today = DateTime(now.year, now.month, now.day);
  final fallbackStart = today.subtract(const Duration(days: 29));

  return showModalBottomSheet<DateTimeRange>(
    context: context,
    isScrollControlled: true,
    showDragHandle: false,
    shape: RoundedRectangleBorder(
      borderRadius: BorderRadius.vertical(top: tokens.radiusXl.topLeft),
    ),
    builder: (ctx) {
      return _AnalyticsIntervalSheetBody(
        initialFrom: initialFrom ?? fallbackStart,
        initialTo: initialTo ?? today,
        firstDate: DateTime(today.year - 5),
        lastDate: today,
      );
    },
  );
}

class _AnalyticsIntervalSheetBody extends StatefulWidget {
  const _AnalyticsIntervalSheetBody({
    required this.initialFrom,
    required this.initialTo,
    required this.firstDate,
    required this.lastDate,
  });

  final DateTime initialFrom;
  final DateTime initialTo;
  final DateTime firstDate;
  final DateTime lastDate;

  @override
  State<_AnalyticsIntervalSheetBody> createState() =>
      _AnalyticsIntervalSheetBodyState();
}

class _AnalyticsIntervalSheetBodyState
    extends State<_AnalyticsIntervalSheetBody> {
  late DateTime _from;
  late DateTime _to;
  late final TextEditingController _fromController;
  late final TextEditingController _toController;

  @override
  void initState() {
    super.initState();
    _from = _dateOnly(widget.initialFrom);
    _to = _dateOnly(widget.initialTo);
    if (_to.isBefore(_from)) {
      final swap = _from;
      _from = _to;
      _to = swap;
    }
    _fromController = TextEditingController(text: _format(_from));
    _toController = TextEditingController(text: _format(_to));
  }

  @override
  void dispose() {
    _fromController.dispose();
    _toController.dispose();
    super.dispose();
  }

  static DateTime _dateOnly(DateTime d) => DateTime(d.year, d.month, d.day);

  static String _format(DateTime d) =>
      '${d.day.toString().padLeft(2, '0')}/'
      '${d.month.toString().padLeft(2, '0')}/'
      '${d.year}';

  void _syncControllers() {
    _fromController.text = _format(_from);
    _toController.text = _format(_to);
  }

  Future<void> _pick({required bool isFrom}) async {
    final current = isFrom ? _from : _to;
    final picked = await showDatePicker(
      context: context,
      locale: const Locale('es', 'CO'),
      initialDate: current,
      firstDate: widget.firstDate,
      lastDate: widget.lastDate,
      helpText: isFrom ? 'Fecha de inicio' : 'Fecha de fin',
      cancelText: 'Cancelar',
      confirmText: 'Listo',
      fieldLabelText: 'Fecha',
      fieldHintText: 'dd/mm/aaaa',
      errorFormatText: 'Usa el formato dd/mm/aaaa',
      errorInvalidText: 'Fecha fuera de rango',
      builder: (context, child) {
        final theme = Theme.of(context);
        return Localizations.override(
          context: context,
          locale: const Locale('es', 'CO'),
          child: Theme(
            data: theme.copyWith(
              datePickerTheme: DatePickerThemeData(
                backgroundColor: theme.colorScheme.surface,
                headerBackgroundColor: theme.colorScheme.surfaceContainerHigh,
                headerForegroundColor: theme.colorScheme.onSurface,
                dayStyle: theme.textTheme.bodyMedium,
                weekdayStyle: theme.textTheme.labelSmall?.copyWith(
                  fontWeight: FontWeight.w700,
                  letterSpacing: 0.6,
                ),
                yearStyle: theme.textTheme.bodyMedium,
                shape: RoundedRectangleBorder(
                  borderRadius: theme.appTokens.radiusLg,
                ),
              ),
            ),
            child: child!,
          ),
        );
      },
    );
    if (picked == null || !mounted) return;
    final day = _dateOnly(picked);
    setState(() {
      if (isFrom) {
        _from = day;
        if (_to.isBefore(_from)) _to = _from;
      } else {
        _to = day;
        if (_from.isAfter(_to)) _from = _to;
      }
      _syncControllers();
    });
  }

  void _apply() {
    Navigator.of(context).pop(DateTimeRange(start: _from, end: _to));
  }

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final tokens = Theme.of(context).appTokens;
    final bottomInset = MediaQuery.viewPaddingOf(context).bottom;
    final keyboard = MediaQuery.viewInsetsOf(context).bottom;
    final days = _to.difference(_from).inDays + 1;

    return SafeArea(
      child: Padding(
        padding: EdgeInsets.only(bottom: keyboard),
        child: SingleChildScrollView(
          padding: EdgeInsets.fromLTRB(
            tokens.spaceXl,
            tokens.spaceLg,
            tokens.spaceXl,
            tokens.spaceXl + bottomInset,
          ),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Center(
                child: Container(
                  width: 40,
                  height: 4,
                  decoration: BoxDecoration(
                    color: scheme.onSurfaceVariant.withValues(alpha: 0.3),
                    borderRadius: tokens.radiusSm,
                  ),
                ),
              ),
              SizedBox(height: tokens.spaceXl),
              AppSectionHeader(
                eyebrow: 'Periodo',
                title: 'Intervalo',
                subtitle: days == 1
                    ? '1 día seleccionado'
                    : '$days días seleccionados',
                variant: AppSectionHeaderVariant.compact,
              ),
              SizedBox(height: tokens.spaceXl),
              AppTextField(
                label: 'Desde',
                readOnly: true,
                controller: _fromController,
                suffix: Icon(
                  Icons.calendar_today_rounded,
                  size: 18,
                  color: scheme.onSurfaceVariant,
                ),
                onTap: () => _pick(isFrom: true),
              ),
              SizedBox(height: tokens.spaceLg),
              AppTextField(
                label: 'Hasta',
                readOnly: true,
                controller: _toController,
                suffix: Icon(
                  Icons.calendar_today_rounded,
                  size: 18,
                  color: scheme.onSurfaceVariant,
                ),
                onTap: () => _pick(isFrom: false),
              ),
              SizedBox(height: tokens.spaceXl),
              AppButton(
                label: 'Aplicar intervalo',
                icon: Icons.check_rounded,
                expanded: true,
                onPressed: _apply,
              ),
              SizedBox(height: tokens.spaceSm),
              AppButton(
                label: 'Cancelar',
                variant: AppButtonVariant.ghost,
                expanded: true,
                onPressed: () => Navigator.of(context).pop(),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
