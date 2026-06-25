import 'dart:typed_data';

import 'package:flutter/material.dart';

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
  late int _currentIndex;

  @override
  void initState() {
    super.initState();
    _currentIndex = widget.initialIndex.clamp(0, widget.photos.length - 1);
    _pageController = PageController(initialPage: _currentIndex);
  }

  @override
  void dispose() {
    _pageController.dispose();
    super.dispose();
  }

  ReservationTimelinePhoto get _currentPhoto => widget.photos[_currentIndex];

  String _cacheKey(ReservationTimelinePhoto photo) =>
      '${widget.logId}:${photo.index}';

  Uint8List? get _currentBytes => widget.cache?[_cacheKey(_currentPhoto)];

  Future<void> _saveCurrentToDevice() async {
    final bytes = _currentBytes;
    if (bytes == null) return;

    try {
      await saveFile(bytes, _currentPhoto.filename, _currentPhoto.contentType);
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Descargado: ${_currentPhoto.filename}'),
          duration: const Duration(seconds: 4),
        ),
      );
    } catch (error) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Error al descargar: $error'),
          backgroundColor: Theme.of(context).colorScheme.error,
        ),
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
              onPageChanged: (index) => setState(() => _currentIndex = index),
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
          if (hasMultiple)
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
        child: Center(
          child: Image.memory(
            _bytes!,
            fit: BoxFit.contain,
          ),
        ),
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
