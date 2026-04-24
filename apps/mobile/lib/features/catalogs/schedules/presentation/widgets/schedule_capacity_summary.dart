import 'package:flutter/material.dart';

import '../../../../../app/widgets/app_metric_card.dart';
import '../../domain/schedule.dart';

class ScheduleCapacitySummary extends StatelessWidget {
  const ScheduleCapacitySummary({super.key, required this.schedule});

  final CatalogSchedule schedule;

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Expanded(
          child: AppMetricCard(
            title: 'Disponibles',
            value: '${schedule.availableSlots}',
            compact: true,
          ),
        ),
        const SizedBox(width: 8),
        Expanded(
          child: AppMetricCard(
            title: 'Total',
            value: '${schedule.capacityTotal}',
            compact: true,
          ),
        ),
      ],
    );
  }
}
