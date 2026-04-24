import 'package:flutter/material.dart';

import '../../../../app/widgets/app_section_header.dart';
import '../../../../app/widgets/app_segmented_filter.dart';

/// Cabecera de módulo: [AppSectionHeader] + selector de secciones (peers, sin jerarquía falsa con `>`).
class ModuleSubrouteHeader extends StatelessWidget {
  const ModuleSubrouteHeader({
    super.key,
    required this.eyebrow,
    required this.title,
    required this.subrouteLabels,
    required this.currentSubrouteIndex,
    required this.onSubrouteTap,
    this.subtitle,
    this.trailing,
  });

  final String eyebrow;
  final String title;
  final String? subtitle;
  final List<String> subrouteLabels;
  final int currentSubrouteIndex;
  final ValueChanged<int> onSubrouteTap;
  final Widget? trailing;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        AppSectionHeader(
          eyebrow: eyebrow,
          title: title,
          subtitle: subtitle,
          trailing: trailing,
        ),
        const SizedBox(height: 12),
        AppSegmentedFilter<int>(
          value: currentSubrouteIndex,
          onChanged: onSubrouteTap,
          items: [
            for (int i = 0; i < subrouteLabels.length; i++)
              AppSegmentedFilterItem<int>(label: subrouteLabels[i], value: i),
          ],
        ),
      ],
    );
  }
}
