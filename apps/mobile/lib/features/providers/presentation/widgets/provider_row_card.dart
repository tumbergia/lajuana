import 'package:flutter/material.dart';
import 'package:material_symbols_icons/material_symbols_icons.dart';

import 'package:mobile_ui/src/widgets/app_badge.dart';
import 'package:mobile_ui/src/widgets/app_entity_row_card.dart';
import 'package:mobile/features/providers/presentation/models/provider_view_models.dart';

class ProviderRowCard extends StatelessWidget {
  const ProviderRowCard({
    super.key,
    required this.provider,
    required this.onTap,
  });

  final ProviderRecord provider;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    return AppEntityRowCard(
      title: provider.name,
      subtitle: provider.subtitle,
      trailing: AppBadge(
        label: provider.statusLabel,
        tone: provider.statusTone,
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
          Symbols.handshake,
          size: 24,
          color: Theme.of(context).colorScheme.onSurfaceVariant,
        ),
      ),
      onTap: onTap,
    );
  }
}
