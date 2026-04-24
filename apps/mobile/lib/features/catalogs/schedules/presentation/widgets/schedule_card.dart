import 'package:flutter/material.dart';

import '../../../../../app/widgets/app_entity_row_card.dart';
import '../../domain/schedule.dart';
import 'schedule_status_badge.dart';

class ScheduleCard extends StatelessWidget {
  const ScheduleCard({super.key, required this.schedule, this.onTap});

  final CatalogSchedule schedule;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    final subtitle = '${schedule.date} - ${schedule.startTime}';
    return AppEntityRowCard(
      title: 'Experiencia ${schedule.experienceId}',
      subtitle: subtitle,
      badge: scheduleStatusBadgeFor(schedule),
      onTap: onTap,
    );
  }
}
