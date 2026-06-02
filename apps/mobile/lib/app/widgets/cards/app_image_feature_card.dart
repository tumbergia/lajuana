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
  final double? imageAspectRatio;

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
    this.imageAspectRatio,
  });

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;

    const radius = Radius.circular(8);

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
                  topLeft: radius,
                  topRight: radius,
                ),
                child: imageAspectRatio != null
                    ? AspectRatio(
                        aspectRatio: imageAspectRatio!,
                        child: Image(
                          image: image,
                          width: width,
                          height: imageHeight,
                          fit: BoxFit.cover,
                          errorBuilder: (_, _, _) => Container(
                            color: scheme.surfaceContainerHigh,
                            alignment: Alignment.center,
                            child: Icon(
                              Icons.image_not_supported_outlined,
                              color: scheme.onSurfaceVariant,
                            ),
                          ),
                        ),
                      )
                    : Image(
                        image: image,
                        width: width,
                        height: imageHeight,
                        fit: BoxFit.cover,
                        errorBuilder: (_, _, _) => Container(
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
              if (badge != null) Positioned(top: 12, left: 12, child: badge!),
            ],
          ),
          Expanded(
            child: Padding(
              padding: const EdgeInsets.fromLTRB(16, 14, 16, 8),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    title.toUpperCase(),
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                    style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                      fontWeight: FontWeight.w800,
                      color: scheme.onSurface,
                    ),
                  ),
                  const SizedBox(height: 2),
                  Text(
                    subtitle.toUpperCase(),
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: Theme.of(context).textTheme.labelLarge?.copyWith(
                      color: scheme.onSurfaceVariant,
                      letterSpacing: 1.0,
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );

    return SizedBox(width: width, child: card);
  }
}
