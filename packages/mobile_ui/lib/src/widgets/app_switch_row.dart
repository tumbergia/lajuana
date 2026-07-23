import 'package:flutter/material.dart';
import 'package:mobile_ui/src/widgets/app_entity_row_card.dart';
import 'package:mobile_ui/src/widgets/app_switch.dart';

/// Settings switch row: [AppEntityRowCard] chrome + square [AppSwitch].
class AppSwitchRow extends StatelessWidget {
  const AppSwitchRow({
    super.key,
    required this.title,
    required this.value,
    required this.onChanged,
    this.subtitle,
  });

  final String title;
  final String? subtitle;
  final bool value;
  final ValueChanged<bool>? onChanged;

  bool get _enabled => onChanged != null;

  void _toggle() {
    final callback = onChanged;
    if (callback == null) return;
    callback(!value);
  }

  @override
  Widget build(BuildContext context) {
    return Semantics(
      button: true,
      toggled: value,
      enabled: _enabled,
      label: title,
      child: AppEntityRowCard(
        title: title,
        subtitle: subtitle ?? '',
        selected: value,
        wrapTitle: true,
        onTap: _enabled ? _toggle : null,
        trailing: ExcludeSemantics(
          child: IgnorePointer(
            child: AppSwitch(value: value, onChanged: onChanged),
          ),
        ),
      ),
    );
  }
}
