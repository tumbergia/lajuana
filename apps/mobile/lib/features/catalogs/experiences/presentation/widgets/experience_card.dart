import 'package:flutter/material.dart';

import '../../../../../app/widgets/app_entity_row_card.dart';
import '../../domain/experience.dart';
import 'experience_status_badge.dart';

class ExperienceCard extends StatelessWidget {
  const ExperienceCard({super.key, required this.experience, this.onTap});

  final CatalogExperience experience;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    final duration = experience.durationHours != null
        ? '${experience.durationHours}h'
        : experience.durationDays != null
        ? '${experience.durationDays}d'
        : 'sin duracion';
    return AppEntityRowCard(
      title: experience.name,
      subtitle: '${experience.level} - $duration',
      badge: experienceStatusBadgeFor(experience),
      onTap: onTap,
    );
  }
}
