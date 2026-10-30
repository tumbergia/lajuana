import 'package:flutter/material.dart';

import 'package:mobile_ui/src/widgets/app_badge.dart';
import 'package:mobile_ui/src/widgets/app_entity_row_card.dart';
import 'package:mobile_domain/src/reservations/reservation_provider_item.dart';

import 'package:mobile/features/reservations/presentation/widgets/provider_contact_actions.dart';

class ProviderReservationCard extends StatelessWidget {
  const ProviderReservationCard({super.key, required this.item, this.onTap});

  final ReservationProviderItem item;
  final VoidCallback? onTap;

  AppBadgeTone _statusTone(String status) {
    return switch (status) {
      'confirmed' => AppBadgeTone.success,
      'contacted' => AppBadgeTone.primary,
      'cancelled' => AppBadgeTone.danger,
      _ => AppBadgeTone.neutral,
    };
  }

  @override
  Widget build(BuildContext context) {
    final subtitleParts = <String>[
      'Tipo: ${providerTypeLabel(item.providerType)}',
      if (item.serviceLabel != null && item.serviceLabel!.isNotEmpty)
        'Servicio: ${item.serviceLabel}',
      if (item.locationLabel != null && item.locationLabel!.isNotEmpty)
        'Ubicacion: ${item.locationLabel}',
    ];

    return AppEntityRowCard(
      title: item.providerName,
      subtitle: subtitleParts.join('\n'),
      badge: AppBadge(
        label: reservationProviderStatusLabel(item.status),
        tone: _statusTone(item.status),
        uppercase: false,
      ),
      trailing: const Icon(Icons.chevron_right_rounded, size: 18),
      onTap: onTap,
    );
  }
}
