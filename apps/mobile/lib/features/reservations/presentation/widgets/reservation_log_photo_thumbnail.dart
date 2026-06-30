import 'dart:typed_data';

import 'package:flutter/material.dart';

import 'package:mobile_domain/src/reservations/reservation_timeline_photo.dart';
import 'package:mobile/features/reservations/presentation/controllers/reservation_logs_section_controller.dart';

/// Miniatura async de una foto de bitácora (cuadrito pequeño).
class ReservationLogPhotoThumbnail extends StatefulWidget {
  const ReservationLogPhotoThumbnail({
    super.key,
    required this.logId,
    required this.photo,
    required this.controller,
    this.cache,
    this.onTap,
    this.size = 40,
    this.moreCount = 0,
  });

  final String logId;
  final ReservationTimelinePhoto photo;
  final ReservationLogsSectionController controller;
  final Map<String, Uint8List>? cache;
  final VoidCallback? onTap;
  final double size;
  final int moreCount;

  @override
  State<ReservationLogPhotoThumbnail> createState() =>
      _ReservationLogPhotoThumbnailState();
}

class _ReservationLogPhotoThumbnailState
    extends State<ReservationLogPhotoThumbnail> {
  Uint8List? _bytes;
  bool _loading = true;

  String get _cacheKey => '${widget.logId}:${widget.photo.index}';

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    final cached = widget.cache?[_cacheKey];
    if (cached != null) {
      setState(() {
        _bytes = cached;
        _loading = false;
      });
      return;
    }

    final bytes = await widget.controller.downloadPhoto(
      logId: widget.logId,
      photoIndex: widget.photo.index,
    );
    if (!mounted) return;
    if (bytes != null) {
      widget.cache?[_cacheKey] = bytes;
    }
    setState(() {
      _bytes = bytes;
      _loading = false;
    });
  }

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;

    Widget content = Container(
      width: widget.size,
      height: widget.size,
      decoration: BoxDecoration(
        color: scheme.surfaceContainerHigh,
        borderRadius: BorderRadius.circular(4),
        border: Border.all(color: scheme.outlineVariant),
      ),
      clipBehavior: Clip.antiAlias,
      child: _loading
          ? Center(
              child: SizedBox(
                width: widget.size * 0.4,
                height: widget.size * 0.4,
                child: CircularProgressIndicator(strokeWidth: 2),
              ),
            )
          : _bytes != null
              ? Image.memory(_bytes!, fit: BoxFit.cover)
              : Icon(
                  Icons.broken_image_outlined,
                  size: widget.size * 0.5,
                  color: scheme.onSurfaceVariant,
                ),
    );

    if (widget.moreCount > 0) {
      content = Stack(
        children: [
          content,
          Positioned.fill(
            child: Material(
              color: Colors.black.withValues(alpha: 0.45),
              child: Center(
                child: Text(
                  '+${widget.moreCount}',
                  style: Theme.of(context).textTheme.labelSmall?.copyWith(
                        color: Colors.white,
                        fontWeight: FontWeight.w800,
                      ),
                ),
              ),
            ),
          ),
        ],
      );
    }

    return GestureDetector(onTap: widget.onTap, child: content);
  }
}
