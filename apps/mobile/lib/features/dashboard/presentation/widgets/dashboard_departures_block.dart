import 'package:flutter/material.dart';

import 'package:mobile_ui/src/widgets/app_entity_row_card.dart';
import 'package:mobile/features/reservations/presentation/models/reservation_view_models.dart';
import 'package:mobile/features/reservations/presentation/widgets/reservation_row_card.dart';

class DashboardDeparturesBlock extends StatelessWidget {
  const DashboardDeparturesBlock({super.key, required this.reservations});

  final List<ReservationRecord> reservations;

  @override
  Widget build(BuildContext context) {
    final ordered = reservations
        .where((item) => item.status != 'finalizadas')
        .take(4)
        .toList(growable: false);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        for (int i = 0; i < ordered.length; i++) ...[
          AppEntityRowCard(
            title: ordered[i].slotLabel,
            subtitle: '${ordered[i].clientName} - ${ordered[i].equineName}',
            badge: ReservationRowCard.statusBadgeForLegacy(ordered[i].status),
            leading: const Icon(Icons.schedule_rounded, size: 18),
          ),
          if (i != ordered.length - 1) const SizedBox(height: 10),
        ],
      ],
    );
  }
}
