import 'package:flutter/material.dart';
import 'package:material_symbols_icons/material_symbols_icons.dart';

import '../../../../app/widgets/app_badge.dart';
import '../../../../app/widgets/app_entity_row_card.dart';
import '../models/saddle_view_models.dart';

class SaddleRowCard extends StatelessWidget {
  const SaddleRowCard({
    super.key,
    required this.saddle,
    required this.onTap,
  });

  final SaddleRecord saddle;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    return AppEntityRowCard(
      title: saddle.code,
      subtitle: saddle.name,
      trailing: AppBadge(
        label: saddle.statusLabel,
        tone: saddle.statusTone,
        uppercase: false,
      ),
      leading: Container(
        width: 48,
        height: 48,
        decoration: BoxDecoration(
          color: Theme.of(context).colorScheme.surfaceContainerHighest,
          borderRadius: BorderRadius.circular(4),
        ),
        child: Icon(
          Symbols.airline_seat_legroom_extra,
          size: 24,
          color: Theme.of(context).colorScheme.onSurfaceVariant,
        ),
      ),
      onTap: onTap,
    );
  }
}
