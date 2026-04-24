import 'package:flutter/material.dart';

import '../../../reservations/presentation/models/reservation_view_models.dart';
import '../../../reservations/presentation/widgets/reservation_row_card.dart';

class DashboardPendingBlock extends StatelessWidget {
  const DashboardPendingBlock({
    super.key,
    required this.reservations,
    required this.onOpenReservationDetail,
  });

  final List<ReservationRecord> reservations;
  final ValueChanged<ReservationRecord> onOpenReservationDetail;

  @override
  Widget build(BuildContext context) {
    final pending = reservations
        .where((item) => item.status == 'pendientes')
        .toList(growable: false);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        for (int i = 0; i < pending.length; i++) ...[
          ReservationRowCard(
            reservation: pending[i],
            subtitle: '${pending[i].equineName} - ${pending[i].slotLabel}',
            highlightIfPending: true,
            openDetailsOnTap: true,
            onOpenDetail: () => onOpenReservationDetail(pending[i]),
          ),
          if (i != pending.length - 1) const SizedBox(height: 10),
        ],
      ],
    );
  }
}
