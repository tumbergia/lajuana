import 'dart:typed_data';

import 'package:flutter/material.dart';

import 'package:mobile_domain/src/reservations/reservation_timeline_entry.dart';
import 'package:mobile_domain/src/reservations/reservation_timeline_photo.dart';
import 'package:mobile/features/reservations/presentation/controllers/reservation_logs_section_controller.dart';
import 'package:mobile/features/reservations/presentation/widgets/reservation_log_photo_thumbnail.dart';

/// Preview de fotos en timeline: una fila de cuadritos que llena el ancho.
class ReservationLogPhotoPreviewRow extends StatelessWidget {
  const ReservationLogPhotoPreviewRow({
    super.key,
    required this.entry,
    required this.logId,
    required this.controller,
    required this.cache,
    required this.onPhotoTap,
    this.thumbSize = 40,
    this.gap = 6,
  });

  final ReservationTimelineEntry entry;
  final String logId;
  final ReservationLogsSectionController controller;
  final Map<String, Uint8List> cache;
  final void Function(ReservationTimelinePhoto photo) onPhotoTap;
  final double thumbSize;
  final double gap;

  @override
  Widget build(BuildContext context) {
    final photos = entry.photos;
    if (photos.isEmpty) return const SizedBox.shrink();

    return LayoutBuilder(
      builder: (context, constraints) {
        final maxSlots = _maxSlotsForWidth(constraints.maxWidth);
        final totalPhotos = entry.photosTotal > 0
            ? entry.photosTotal
            : photos.length;
        final visibleCount = totalPhotos < maxSlots ? totalPhotos : maxSlots;
        final hiddenCount = totalPhotos - visibleCount;
        final previewPhotos = photos.take(visibleCount).toList(growable: false);

        return Row(
          children: [
            for (var i = 0; i < previewPhotos.length; i++) ...[
              if (i > 0) SizedBox(width: gap),
              ReservationLogPhotoThumbnail(
                logId: logId,
                photo: previewPhotos[i],
                controller: controller,
                cache: cache,
                size: thumbSize,
                moreCount: i == previewPhotos.length - 1 ? hiddenCount : 0,
                onTap: () => onPhotoTap(previewPhotos[i]),
              ),
            ],
          ],
        );
      },
    );
  }

  int _maxSlotsForWidth(double width) {
    if (width <= 0) return 1;
    return ((width + gap) / (thumbSize + gap)).floor().clamp(1, 12);
  }
}
