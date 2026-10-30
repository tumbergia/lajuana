import 'dart:typed_data';

import 'package:flutter/material.dart';

import 'package:mobile_ui/src/widgets/app_toast.dart';

import 'package:mobile/app/utils/file_saver.dart';
import 'package:mobile_domain/src/reservations/reservation_timeline_photo.dart';
import 'package:mobile_domain/src/reservations/reservations_repository.dart';
import 'package:mobile_ui/src/widgets/app_button.dart';

/// Visor de fotos de bitácora con carrusel y descarga al dispositivo.
class ReservationLogPhotoViewer extends StatefulWidget {
  const ReservationLogPhotoViewer({
    super.key,
    required this.logId,
    required this.photos,
    required this.initialIndex,
    required this.repository,
    this.cache,
    this.onBytesCached,
  });

  final String logId;
  final List<ReservationTimelinePhoto> photos;
  final int initialIndex;
  final ReservationsRepository repository;
  final Map<String, Uint8List>? cache;
  final void Function(String cacheKey, Uint8List bytes)? onBytesCached;

  @override
  State<ReservationLogPhotoViewer> createState() =>
      _ReservationLogPhotoViewerState();
}

class _ReservationLogPhotoViewerState extends State<ReservationLogPhotoViewer> {
  late final PageController _pageController;
  late final ScrollController _thumbScrollController;
  late int _currentIndex;

  static const double _thumbSize = 64;
  static const double _thumbGap = 8;

  @override
  void initState() {
    super.initState();
    _currentIndex = widget.initialIndex.clamp(0, widget.photos.length - 1);
    _pageController = PageController(initialPage: _currentIndex);
    _thumbScrollController = ScrollController();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _scrollThumbIntoView(_currentIndex, animate: false);
    });
  }

  @override
  void dispose() {
    _pageController.dispose();
    _thumbScrollController.dispose();
    super.dispose();
  }

  ReservationTimelinePhoto get _currentPhoto => widget.photos[_currentIndex];

  String _cacheKey(ReservationTimelinePhoto photo) =>
      '${widget.logId}:${photo.index}';

  Uint8List? get _currentBytes => widget.cache?[_cacheKey(_currentPhoto)];

  void _goToPage(int index) {
    if (index == _currentIndex) return;
    _pageController.animateToPage(
      index,
      duration: const Duration(milliseconds: 240),
      curve: Curves.easeOutCubic,
    );
  }

  void _onPageChanged(int index) {
    setState(() => _currentIndex = index);
    _scrollThumbIntoView(index);
  }

  void _scrollThumbIntoView(int index, {bool animate = true}) {
    if (!_thumbScrollController.hasClients) return;
    final offset = index * (_thumbSize + _thumbGap);
    final viewport = _thumbScrollController.position.viewportDimension;
    final maxScroll = _thumbScrollController.position.maxScrollExtent;
    final target = (offset - (viewport - _thumbSize) / 2).clamp(0.0, maxScroll);

    if (animate) {
      _thumbScrollController.animateTo(
        target,
        duration: const Duration(milliseconds: 240),
        curve: Curves.easeOutCubic,
      );
    } else {
      _thumbScrollController.jumpTo(target);
    }
  }

  Future<void> _saveCurrentToDevice() async {
    final bytes = _currentBytes;
    if (bytes == null) return;

    try {
      await saveFile(bytes, _currentPhoto.filename, _currentPhoto.contentType);
      if (!mounted) return;
      showAppToast(context, message: 'Descargado: ${_currentPhoto.filename}');
    } catch (error) {
      if (!mounted) return;
      showAppToast(
        context,
        message: 'Error al descargar: $error',
        isError: true,
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final photos = widget.photos;
    final hasMultiple = photos.length > 1;

    return Scaffold(
      appBar: AppBar(
        title: Text(
          hasMultiple
              ? '${_currentIndex + 1} / ${photos.length}'
              : _currentPhoto.filename,
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.download_rounded),
            tooltip: 'Descargar',
            onPressed: _currentBytes != null ? _saveCurrentToDevice : null,
          ),
        ],
      ),
      body: Column(
        children: [
          Expanded(
            child: PageView.builder(
              controller: _pageController,
              itemCount: photos.length,
              onPageChanged: _onPageChanged,
              itemBuilder: (context, index) {
                return _LogPhotoPage(
                  key: ValueKey('log-photo-${photos[index].index}'),
                  logId: widget.logId,
                  photo: photos[index],
                  repository: widget.repository,
                  cache: widget.cache,
                  onBytesCached: widget.onBytesCached,
                  onBytesLoaded: () {
                    if (index == _currentIndex && mounted) setState(() {});
                  },
                );
              },
            ),
          ),
          if (hasMultiple) _buildBottomCarousel(context),
          Padding(
            padding: const EdgeInsets.fromLTRB(24, 8, 24, 16),
            child: Text(
              _currentPhoto.filename,
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
              textAlign: TextAlign.center,
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                color: Theme.of(context).colorScheme.onSurfaceVariant,
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildBottomCarousel(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final photos = widget.photos;

    return Container(
      width: double.infinity,
      padding: const EdgeInsets.fromLTRB(16, 12, 16, 4),
      decoration: BoxDecoration(
        color: scheme.surfaceContainerHighest,
        border: Border(
          top: BorderSide(color: scheme.outlineVariant.withValues(alpha: 0.5)),
        ),
      ),
      child: SizedBox(
        height: _thumbSize,
        child: ListView.separated(
          controller: _thumbScrollController,
          scrollDirection: Axis.horizontal,
          itemCount: photos.length,
          separatorBuilder: (_, __) => SizedBox(width: _thumbGap),
          itemBuilder: (context, index) {
            final selected = index == _currentIndex;
            final photo = photos[index];
            final cacheKey = _cacheKey(photo);

            return GestureDetector(
              onTap: () => _goToPage(index),
              child: AnimatedContainer(
                duration: const Duration(milliseconds: 180),
                width: _thumbSize,
                height: _thumbSize,
                decoration: BoxDecoration(
                  borderRadius: BorderRadius.circular(6),
                  border: Border.all(
                    color: selected ? scheme.primary : scheme.outlineVariant,
                    width: selected ? 2 : 1,
                  ),
                ),
                clipBehavior: Clip.antiAlias,
                child: _ViewerStripThumbnail(
                  logId: widget.logId,
                  photo: photo,
                  repository: widget.repository,
                  cache: widget.cache,
                  onBytesCached: widget.onBytesCached,
                  cacheKey: cacheKey,
                ),
              ),
            );
          },
        ),
      ),
    );
  }
}

class _ViewerStripThumbnail extends StatefulWidget {
  const _ViewerStripThumbnail({
    required this.logId,
    required this.photo,
    required this.repository,
    required this.cacheKey,
    this.cache,
    this.onBytesCached,
  });

  final String logId;
  final ReservationTimelinePhoto photo;
  final ReservationsRepository repository;
  final String cacheKey;
  final Map<String, Uint8List>? cache;
  final void Function(String cacheKey, Uint8List bytes)? onBytesCached;

  @override
  State<_ViewerStripThumbnail> createState() => _ViewerStripThumbnailState();
}

class _ViewerStripThumbnailState extends State<_ViewerStripThumbnail> {
  Uint8List? _bytes;
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    final cached = widget.cache?[widget.cacheKey];
    if (cached != null) {
      setState(() {
        _bytes = cached;
        _loading = false;
      });
      return;
    }

    try {
      final bytes = await widget.repository.downloadReservationLogPhoto(
        logId: widget.logId,
        photoIndex: widget.photo.index,
      );
      widget.cache?[widget.cacheKey] = bytes;
      widget.onBytesCached?.call(widget.cacheKey, bytes);
      if (!mounted) return;
      setState(() {
        _bytes = bytes;
        _loading = false;
      });
    } catch (_) {
      if (!mounted) return;
      setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;

    if (_loading) {
      return ColoredBox(
        color: scheme.surfaceContainerHigh,
        child: Center(
          child: SizedBox(
            width: 18,
            height: 18,
            child: CircularProgressIndicator(strokeWidth: 2),
          ),
        ),
      );
    }

    if (_bytes != null) {
      return Image.memory(_bytes!, fit: BoxFit.cover);
    }

    return ColoredBox(
      color: scheme.surfaceContainerHigh,
      child: Icon(
        Icons.broken_image_outlined,
        size: 24,
        color: scheme.onSurfaceVariant,
      ),
    );
  }
}

class _LogPhotoPage extends StatefulWidget {
  const _LogPhotoPage({
    super.key,
    required this.logId,
    required this.photo,
    required this.repository,
    this.cache,
    this.onBytesCached,
    this.onBytesLoaded,
  });

  final String logId;
  final ReservationTimelinePhoto photo;
  final ReservationsRepository repository;
  final Map<String, Uint8List>? cache;
  final void Function(String cacheKey, Uint8List bytes)? onBytesCached;
  final VoidCallback? onBytesLoaded;

  @override
  State<_LogPhotoPage> createState() => _LogPhotoPageState();
}

class _LogPhotoPageState extends State<_LogPhotoPage> {
  Uint8List? _bytes;
  String? _error;
  bool _loading = true;

  String get _cacheKey => '${widget.logId}:${widget.photo.index}';

  bool get _isImage {
    final contentType = widget.photo.contentType.toLowerCase();
    return contentType.contains('image/');
  }

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
      widget.onBytesLoaded?.call();
      return;
    }

    try {
      final bytes = await widget.repository.downloadReservationLogPhoto(
        logId: widget.logId,
        photoIndex: widget.photo.index,
      );
      widget.cache?[_cacheKey] = bytes;
      widget.onBytesCached?.call(_cacheKey, bytes);
      if (!mounted) return;
      setState(() {
        _bytes = bytes;
        _loading = false;
      });
      widget.onBytesLoaded?.call();
    } catch (error) {
      if (!mounted) return;
      setState(() {
        _error = 'Error al descargar: $error';
        _loading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    if (_loading) {
      return const Center(child: CircularProgressIndicator());
    }

    if (_error != null) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(
                Icons.error_outline_rounded,
                size: 48,
                color: theme.colorScheme.error,
              ),
              const SizedBox(height: 16),
              Text(_error!, textAlign: TextAlign.center),
              const SizedBox(height: 16),
              AppButton(
                label: 'Reintentar',
                onPressed: () {
                  setState(() {
                    _loading = true;
                    _error = null;
                  });
                  _load();
                },
              ),
            ],
          ),
        ),
      );
    }

    if (_isImage && _bytes != null) {
      return InteractiveViewer(
        minScale: 0.5,
        maxScale: 5,
        child: Center(child: Image.memory(_bytes!, fit: BoxFit.contain)),
      );
    }

    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Text(
          'Vista previa no disponible para ${widget.photo.contentType}.',
          textAlign: TextAlign.center,
        ),
      ),
    );
  }
}
