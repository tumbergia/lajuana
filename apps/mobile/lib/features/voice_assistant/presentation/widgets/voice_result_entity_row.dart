import 'package:flutter/material.dart';
import 'package:mobile_ui/src/widgets/app_badge.dart';
import 'package:mobile_ui/src/widgets/app_entity_row_card.dart';

/// Fila normalizada para resultados estructurados del asistente de voz.
class VoiceResultEntityRow extends StatelessWidget {
  const VoiceResultEntityRow({
    super.key,
    required this.title,
    required this.subtitle,
    this.statusLabel,
    this.statusTone = AppBadgeTone.neutral,
    this.onTap,
    this.leading,
  });

  final String title;
  final String subtitle;
  final String? statusLabel;
  final AppBadgeTone statusTone;
  final VoidCallback? onTap;
  final Widget? leading;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Padding(
      padding: const EdgeInsets.only(top: 8),
      child: AppEntityRowCard(
        title: title,
        subtitle: subtitle,
        leading: leading,
        badge: statusLabel == null
            ? null
            : AppBadge(
                label: statusLabel!,
                tone: statusTone,
                uppercase: false,
              ),
        onTap: onTap,
        trailing: onTap == null
            ? null
            : Icon(
                Icons.chevron_right_rounded,
                color: scheme.onSurfaceVariant,
              ),
      ),
    );
  }
}
