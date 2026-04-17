import 'package:flutter/material.dart';

import '../app_badge.dart';
import 'app_selectable_card.dart';

class AppImageFeatureCard extends StatelessWidget {
  final String title;
  final String subtitle;
  final ImageProvider image;
  final AppBadge? badge;
  final bool selected;
  final VoidCallback? onTap;
  final double width;
  final double imageHeight;

  const AppImageFeatureCard({
    super.key,
    required this.title,
    required this.subtitle,
    required this.image,
    this.badge,
    this.selected = false,
    this.onTap,
    this.width = 240,
    this.imageHeight = 160,
  });

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;

    final card = AppSelectableCard(
      selected: selected,
      onTap: onTap,
      padding: EdgeInsets.zero,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Stack(
            children: [
              ClipRRect(
                borderRadius: const BorderRadius.only(
                  topLeft: Radius.circular(8),
                  topRight: Radius.circular(8),
                ),
                child: Image(
                  image: image,
                  width: width,
                  height: imageHeight,
                  fit: BoxFit.cover,
                  errorBuilder: (_, __, ___) => Container(
                    width: width,
                    height: imageHeight,
                    color: scheme.surfaceContainerHigh,
                    alignment: Alignment.center,
                    child: Icon(
                      Icons.image_not_supported_outlined,
                      color: scheme.onSurfaceVariant,
                    ),
                  ),
                ),
              ),
              if (badge != null)
                Positioned(top: 12, left: 12, child: badge!),
            ],
          ),
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 14, 16, 16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  title.toUpperCase(),
                  style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                    fontWeight: FontWeight.w800,
                    color: scheme.onSurface,
                  ),
                ),
                const SizedBox(height: 2),
                Text(
                  subtitle.toUpperCase(),
                  style: Theme.of(context).textTheme.labelLarge?.copyWith(
                    color: scheme.onSurfaceVariant,
                    letterSpacing: 1.0,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );

    return SizedBox(width: width, child: card);
  }
}