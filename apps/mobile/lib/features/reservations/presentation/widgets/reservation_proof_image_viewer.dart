import 'dart:typed_data';

import 'package:flutter/material.dart';
import 'package:pdfrx/pdfrx.dart';

import 'package:mobile_ui/src/widgets/app_toast.dart';

import 'package:mobile/app/errors/user_facing_error.dart';
import 'package:mobile/app/utils/file_saver.dart';
import 'package:mobile_ui/src/widgets/app_badge.dart';
import 'package:mobile_ui/src/widgets/app_button.dart';
import 'package:mobile_domain/src/reservations/reservation_payment_proof_detail.dart';
import 'package:mobile_domain/src/reservations/reservations_repository.dart';
import 'package:mobile/features/reservations/presentation/helpers/reservation_status_labels.dart';

/// Full-screen payment proof viewer.
///
/// Downloads the file via streaming (or uses cached bytes) and renders it:
/// - images (PNG/JPEG): zoomable + pannable via [InteractiveViewer]
/// - PDFs: in-app preview via [PdfViewer]
/// - other types: shows a message
/// - errors: shows retry button
class ProofImageViewer extends StatefulWidget {
  const ProofImageViewer({
    super.key,
    required this.proof,
    this.repository,
    this.cache,
    this.onBytesCached,
  });

  final ReservationPaymentProofDetail proof;
  final ReservationsRepository? repository;
  final Map<String, Uint8List>? cache;
  final void Function(String id, Uint8List bytes)? onBytesCached;

  @override
  State<ProofImageViewer> createState() => _ProofImageViewerState();
}

class _ProofImageViewerState extends State<ProofImageViewer> {
  Uint8List? _bytes;
  String? _error;
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    // Try cache first
    if (widget.cache != null) {
      final cached = widget.cache![widget.proof.id];
      if (cached != null) {
        setState(() {
          _bytes = cached;
          _loading = false;
        });
        return;
      }
    }

    final repo = widget.repository;
    if (repo == null) {
      setState(() {
        _error = 'Repositorio no disponible.';
        _loading = false;
      });
      return;
    }

    try {
      final bytes = await repo.downloadPaymentProofFile(widget.proof.id);
      widget.cache?[widget.proof.id] = bytes;
      widget.onBytesCached?.call(widget.proof.id, bytes);
      setState(() {
        _bytes = bytes;
        _loading = false;
      });
    } catch (e) {
      setState(() {
        _error = userFacingError(
          e,
          fallback: 'No se pudo descargar el comprobante.',
        );
        _loading = false;
      });
    }
  }

  bool get _isImage {
    final ct = widget.proof.contentType?.toLowerCase() ?? '';
    return ct.contains('image/png') ||
        ct.contains('image/jpeg') ||
        ct.contains('image/jpg');
  }

  bool get _isPdf {
    final ct = widget.proof.contentType?.toLowerCase() ?? '';
    if (ct.contains('application/pdf') || ct.contains('pdf')) return true;
    final name = widget.proof.filename?.toLowerCase() ?? '';
    return name.endsWith('.pdf');
  }

  Future<void> _saveToDevice(Uint8List bytes) async {
    final filename = widget.proof.filename ?? 'comprobante-${widget.proof.id}';
    final contentType = widget.proof.contentType ?? 'application/octet-stream';
    try {
      await saveFile(bytes, filename, contentType);
      if (!mounted) return;
      showAppToast(context, message: 'Descargado: $filename');
    } catch (e) {
      if (!mounted) return;
      showAppToast(
        context,
        message: userFacingError(
          e,
          fallback: 'No se pudo guardar el archivo.',
        ),
        isError: true,
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(
        title: Text(widget.proof.filename ?? 'Comprobante'),
        actions: [
          IconButton(
            icon: const Icon(Icons.download_rounded),
            tooltip: 'Descargar',
            onPressed: _bytes != null ? () => _saveToDevice(_bytes!) : null,
          ),
          Center(
            child: Padding(
              padding: const EdgeInsets.only(right: 12),
              child: AppBadge(
                label: paymentProofStatusLabel(widget.proof.status),
                tone: paymentProofStatusTone(widget.proof.status),
                uppercase: false,
              ),
            ),
          ),
        ],
      ),
      body: _buildBody(theme),
    );
  }

  Widget _buildBody(ThemeData theme) {
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
        maxScale: 5.0,
        child: Center(
          child: Image.memory(
            _bytes!,
            fit: BoxFit.contain,
            errorBuilder: (_, __, ___) => Padding(
              padding: const EdgeInsets.all(24),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Icon(
                    Icons.broken_image_outlined,
                    size: 48,
                    color: theme.colorScheme.onSurfaceVariant,
                  ),
                  const SizedBox(height: 16),
                  const Text('No se pudo renderizar la imagen.'),
                ],
              ),
            ),
          ),
        ),
      );
    }

    if (_isPdf && _bytes != null) {
      return PdfViewer.data(
        _bytes!,
        sourceName: widget.proof.filename ?? 'proof-${widget.proof.id}.pdf',
        params: const PdfViewerParams(margin: 8),
      );
    }

    // Non-previewable types
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(
              Icons.description_outlined,
              size: 48,
              color: theme.colorScheme.onSurfaceVariant,
            ),
            const SizedBox(height: 16),
            Text(
              'Vista previa no disponible para ${widget.proof.contentType ?? 'este tipo de archivo'}.',
              textAlign: TextAlign.center,
            ),
          ],
        ),
      ),
    );
  }
}
