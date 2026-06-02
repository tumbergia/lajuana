import 'package:flutter/material.dart';

import 'package:mobile_ui/src/widgets/app_metric_card.dart';
import 'package:mobile/features/catalogs/schedules/domain/schedule.dart';

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
