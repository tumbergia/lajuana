import 'dart:typed_data';

import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';

import 'package:mobile/app/errors/user_facing_error.dart';
import 'package:mobile_domain/src/reservations/reservation_log_photo_input.dart';
import 'package:mobile_domain/src/reservations/reservation_timeline_photo.dart';
import 'package:mobile_ui/src/widgets/app_button.dart';
import 'package:mobile_ui/src/widgets/app_text_field.dart';
import 'package:mobile/features/reservations/presentation/controllers/reservation_logs_section_controller.dart';

const _maxPhotosPerNote = 10;

class _PendingPhoto {
  _PendingPhoto.existing({required this.input, this.previewBytes})
    : localFile = null;

  _PendingPhoto.local({required this.localFile, required this.previewBytes})
    : input = null;

  final ReservationLogPhotoInput? input;
  final XFile? localFile;
  final Uint8List? previewBytes;
  bool uploading = false;
}

/// Bottom sheet para crear o editar una nota con fotos adjuntas.
class ReservationLogNoteSheet extends StatefulWidget {
  const ReservationLogNoteSheet({
    super.key,
    required this.controller,
    required this.isEditing,
    this.initialText = '',
    this.initialPhotos = const [],
  });

  final ReservationLogsSectionController controller;
  final bool isEditing;
  final String initialText;
  final List<ReservationTimelinePhoto> initialPhotos;

  @override
  State<ReservationLogNoteSheet> createState() =>
      _ReservationLogNoteSheetState();
}

class _ReservationLogNoteSheetState extends State<ReservationLogNoteSheet> {
  late final TextEditingController _textController;
  final List<_PendingPhoto> _photos = [];
  bool _saving = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    _textController = TextEditingController(text: widget.initialText);
    for (final photo in widget.initialPhotos) {
      _photos.add(
        _PendingPhoto.existing(
          input: ReservationLogPhotoInput(
            storageKey: photo.storageKey,
            filename: photo.filename,
            contentType: photo.contentType,
            sizeBytes: photo.sizeBytes,
          ),
        ),
      );
    }
  }

  @override
  void dispose() {
    _textController.dispose();
    super.dispose();
  }

  Future<void> _pickPhotos() async {
    if (_photos.length >= _maxPhotosPerNote) {
      setState(() {
        _error = 'Máximo $_maxPhotosPerNote fotos por nota.';
      });
      return;
    }

    try {
      final picker = ImagePicker();
      final images = await picker.pickMultiImage(
        maxWidth: 1600,
        maxHeight: 1600,
        imageQuality: 85,
      );
      if (images.isEmpty) return;

      final remaining = _maxPhotosPerNote - _photos.length;
      final selected = images.take(remaining).toList(growable: false);

      for (final image in selected) {
        final bytes = await image.readAsBytes();
        _photos.add(_PendingPhoto.local(localFile: image, previewBytes: bytes));
      }
      setState(() => _error = null);
    } catch (error) {
      setState(() => _error = 'Error al seleccionar fotos: $error');
    }
  }

  void _removePhoto(int index) {
    setState(() => _photos.removeAt(index));
  }

  Future<List<ReservationLogPhotoInput>> _resolvePhotoInputs() async {
    final inputs = <ReservationLogPhotoInput>[];

    for (final photo in _photos) {
      if (photo.input != null && photo.input!.storageKey.isNotEmpty) {
        inputs.add(photo.input!);
        continue;
      }

      final file = photo.localFile;
      if (file == null) continue;

      final bytes = photo.previewBytes ?? await file.readAsBytes();
      final filename = file.name.isNotEmpty ? file.name : 'foto.jpg';
      final contentType = _guessContentType(filename);

      final uploaded = await widget.controller.uploadPhoto(
        bytes: bytes,
        filename: filename,
        contentType: contentType,
      );
      if (uploaded == null) {
        throw Exception(
          widget.controller.errorMessage ?? 'No se pudo subir una foto.',
        );
      }

      inputs.add(
        ReservationLogPhotoInput(
          storageKey: uploaded.storageKey,
          filename: uploaded.filename,
          contentType: uploaded.contentType,
          sizeBytes: uploaded.sizeBytes,
        ),
      );
    }

    return inputs;
  }

  String _guessContentType(String filename) {
    final lower = filename.toLowerCase();
    if (lower.endsWith('.png')) return 'image/png';
    if (lower.endsWith('.webp')) return 'image/webp';
    return 'image/jpeg';
  }

  Future<void> _save() async {
    final text = _textController.text.trim();
    if (text.isEmpty) {
      setState(() => _error = 'La nota no puede estar vacía.');
      return;
    }

    setState(() {
      _saving = true;
      _error = null;
    });

    try {
      final photos = await _resolvePhotoInputs();
      if (!mounted) return;
      Navigator.of(
        context,
      ).pop(ReservationLogNoteSheetResult(text: text, photos: photos));
    } catch (error) {
      setState(() {
        _saving = false;
        _error = userFacingError(
          error,
          fallback: 'No se pudo preparar la nota.',
        );
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: EdgeInsets.fromLTRB(
        24,
        8,
        24,
        24 + MediaQuery.viewInsetsOf(context).bottom,
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Text(
            widget.isEditing ? 'Editar nota' : 'Agregar nota',
            style: Theme.of(
              context,
            ).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w800),
          ),
          const SizedBox(height: 16),
          AppTextField(
            controller: _textController,
            label: 'Nota',
            hintText: 'Escribe una observación operativa...',
            maxLines: 5,
          ),
          const SizedBox(height: 12),
          Row(
            children: [
              Expanded(
                child: Text(
                  'Fotos (${_photos.length}/$_maxPhotosPerNote)',
                  style: Theme.of(context).textTheme.labelLarge,
                ),
              ),
              AppButton(
                label: 'Agregar fotos',
                variant: AppButtonVariant.ghost,
                icon: Icons.add_photo_alternate_outlined,
                onPressed: _saving || _photos.length >= _maxPhotosPerNote
                    ? null
                    : _pickPhotos,
              ),
            ],
          ),
          if (_photos.isNotEmpty) ...[
            const SizedBox(height: 8),
            SizedBox(
              height: 56,
              child: ListView.separated(
                scrollDirection: Axis.horizontal,
                itemCount: _photos.length,
                separatorBuilder: (_, __) => const SizedBox(width: 8),
                itemBuilder: (context, index) {
                  final photo = _photos[index];
                  return Stack(
                    clipBehavior: Clip.none,
                    children: [
                      Container(
                        width: 56,
                        height: 56,
                        decoration: BoxDecoration(
                          borderRadius: BorderRadius.circular(4),
                          border: Border.all(
                            color: Theme.of(context).colorScheme.outlineVariant,
                          ),
                        ),
                        clipBehavior: Clip.antiAlias,
                        child: photo.previewBytes != null
                            ? Image.memory(
                                photo.previewBytes!,
                                fit: BoxFit.cover,
                              )
                            : Icon(
                                Icons.image_outlined,
                                color: Theme.of(
                                  context,
                                ).colorScheme.onSurfaceVariant,
                              ),
                      ),
                      Positioned(
                        top: -6,
                        right: -6,
                        child: IconButton(
                          visualDensity: VisualDensity.compact,
                          padding: EdgeInsets.zero,
                          constraints: const BoxConstraints(
                            minWidth: 24,
                            minHeight: 24,
                          ),
                          icon: const Icon(Icons.close, size: 16),
                          onPressed: _saving ? null : () => _removePhoto(index),
                        ),
                      ),
                    ],
                  );
                },
              ),
            ),
          ],
          if (_error != null) ...[
            const SizedBox(height: 8),
            Text(
              _error!,
              style: TextStyle(
                color: Theme.of(context).colorScheme.error,
                fontSize: 13,
              ),
            ),
          ],
          const SizedBox(height: 16),
          AppButton(
            label: widget.isEditing ? 'Guardar cambios' : 'Guardar nota',
            expanded: true,
            onPressed: _saving ? null : _save,
          ),
          if (_saving)
            const Padding(
              padding: EdgeInsets.only(top: 12),
              child: Center(child: CircularProgressIndicator()),
            ),
        ],
      ),
    );
  }
}

class ReservationLogNoteSheetResult {
  const ReservationLogNoteSheetResult({
    required this.text,
    this.photos = const [],
  });

  final String text;
  final List<ReservationLogPhotoInput> photos;
}
