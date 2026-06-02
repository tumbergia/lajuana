import 'package:flutter/material.dart';

import 'package:mobile_ui/src/theme/theme_extensions.dart';

class AppPricingTierData {
  const AppPricingTierData({
    required this.minParticipants,
    required this.maxParticipants,
    required this.pricePerPerson,
  });

  final int minParticipants;
  final int maxParticipants;
  final int pricePerPerson;
}

class AppPricingTiersTable extends StatelessWidget {
  const AppPricingTiersTable({
    super.key,
    required this.tiers,
    this.currency = 'COP',
    this.pricesAreNet = true,
    this.notes,
  });

  final List<AppPricingTierData> tiers;
  final String currency;
  final bool pricesAreNet;
  final String? notes;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final scheme = theme.colorScheme;
    final tokens = theme.appTokens;

    return Container(
      decoration: BoxDecoration(
        color: scheme.surfaceContainerHigh,
        borderRadius: tokens.radiusMd,
        border: Border.all(color: scheme.outlineVariant.withValues(alpha: 0.3)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(14, 12, 14, 10),
            child: Row(
              children: [
                Expanded(
                  child: Text(
                    'TARIFAS POR PARTICIPANTES',
                    style: theme.textTheme.labelMedium?.copyWith(
                      fontWeight: FontWeight.w900,
                      color: scheme.onSurface,
                      letterSpacing: 0.6,
                    ),
                  ),
                ),
                Text(
                  currency.toUpperCase(),
                  style: theme.textTheme.labelSmall?.copyWith(
                    fontWeight: FontWeight.w800,
                    color: scheme.onSurfaceVariant,
                    letterSpacing: 0.8,
                  ),
                ),
              ],
            ),
          ),
          const Divider(height: 1),
          for (final tier in tiers)
            _TierRow(
              tier: tier,
              currency: currency,
              isLast: tier == tiers.last,
            ),
          if (pricesAreNet || notes != null) ...[
            const Divider(height: 1),
            Padding(
              padding: const EdgeInsets.fromLTRB(14, 10, 14, 12),
              child: Text(
                [
                  if (pricesAreNet) 'Tarifas netas',
                  if (notes != null && notes!.trim().isNotEmpty) notes!.trim(),
                ].join(' - '),
                style: theme.textTheme.labelSmall?.copyWith(
                  color: scheme.onSurfaceVariant,
                  fontWeight: FontWeight.w700,
                ),
              ),
            ),
          ],
        ],
      ),
    );
  }
}

class _TierRow extends StatelessWidget {
  const _TierRow({
    required this.tier,
    required this.currency,
    required this.isLast,
  });

  final AppPricingTierData tier;
  final String currency;
  final bool isLast;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final scheme = theme.colorScheme;
    final participantsLabel = tier.minParticipants == tier.maxParticipants
        ? '${tier.minParticipants}'
        : '${tier.minParticipants}-${tier.maxParticipants}';
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 11),
      decoration: BoxDecoration(
        border: isLast
            ? null
            : Border(
                bottom: BorderSide(
                  color: scheme.outlineVariant.withValues(alpha: 0.22),
                ),
              ),
      ),
      child: Row(
        children: [
          Expanded(
            child: Text(
              '$participantsLabel participante(s)',
              style: theme.textTheme.labelLarge?.copyWith(
                color: scheme.onSurface,
                fontWeight: FontWeight.w700,
              ),
            ),
          ),
          Text(
            '${_formatMoney(tier.pricePerPerson)} $currency',
            style: theme.textTheme.labelLarge?.copyWith(
              color: scheme.onSurface,
              fontWeight: FontWeight.w900,
            ),
          ),
        ],
      ),
    );
  }

  String _formatMoney(int value) {
    final raw = value.toString();
    final reversed = raw.split('').reversed.join();
    final chunks = <String>[];
    for (var i = 0; i < reversed.length; i += 3) {
      final end = (i + 3 < reversed.length) ? i + 3 : reversed.length;
      chunks.add(reversed.substring(i, end));
    }
    return chunks.join('.').split('').reversed.join();
  }
}
