import 'dart:convert';

import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:image_cropper/image_cropper.dart';
import 'package:image_picker/image_picker.dart';
import 'package:material_symbols_icons/material_symbols_icons.dart';

import '../../../../app/widgets/app_button.dart';
import '../../../../app/widgets/app_section_header.dart';
import '../../../../app/widgets/app_text_field.dart';
import '../../../../app/theme/app_radii.dart';
import '../../domain/models/equine_operational_status.dart';
import '../equine_labels.dart';
import '../models/equine_view_models.dart';

/// Modal bottom sheet para crear o editar un equino (V1 simplificada).
///
/// [existing] = null → modo creación, no-null → modo edición.
class EquineFormSheet extends StatefulWidget {
  final EquineDetailRecord? existing;

  const EquineFormSheet({super.key, this.existing});

  @override
  State<EquineFormSheet> createState() => _EquineFormSheetState();
}

class _EquineFormSheetState extends State<EquineFormSheet> {
  // ── Text controllers ────────────────────────────────────────────────────
  final _nameController = TextEditingController();
  final _inventoryNumberController = TextEditingController();
  final _breedController = TextEditingController();
  final _coatColorController = TextEditingController();
  final _gaitController = TextEditingController();
  final _weightController = TextEditingController();
  final _heightController = TextEditingController();
  final _maxRiderWeightController = TextEditingController();
  final _notesController = TextEditingController();

  // ── Dropdown / switch state ─────────────────────────────────────────────
  String _species = 'mule';
  String _sex = 'male';
  EquineOperationalStatus _status = EquineOperationalStatus.available;
  bool _isAvailable = true;

  // ── Image state ─────────────────────────────────────────────────────────
  String? _imageBase64;
  // ignore: unused_field
  XFile? _selectedImage;

  bool get _isEditing => widget.existing != null;

  @override
  void initState() {
    super.initState();
    if (_isEditing) {
      final e = widget.existing!;
      _nameController.text = e.name;
      _inventoryNumberController.text = e.inventoryNumber?.toString() ?? '';
      _breedController.text = e.breed ?? '';
      _coatColorController.text = e.coatColor ?? '';
      _gaitController.text = e.gait ?? '';
      _weightController.text = e.weightKg?.toString() ?? '';
      _heightController.text = e.heightM?.toString() ?? '';
      _maxRiderWeightController.text = e.maxRiderWeightKg?.toString() ?? '';
      _notesController.text = e.availabilityNotes ?? '';
      _species = e.species;
      _sex = e.sex;
      _status = e.operationalStatus;
      _isAvailable = e.isAvailable;
      _imageBase64 = e.imageBase64;
    }
  }

  @override
  void dispose() {
    _nameController.dispose();
    _inventoryNumberController.dispose();
    _breedController.dispose();
    _coatColorController.dispose();
    _gaitController.dispose();
    _weightController.dispose();
    _heightController.dispose();
    _maxRiderWeightController.dispose();
    _notesController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;

    return Padding(
      padding: EdgeInsets.only(
        left: 24,
        right: 24,
        top: 24,
        bottom: MediaQuery.of(context).viewInsets.bottom + 24,
      ),
      child: SingleChildScrollView(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // ── Header ───────────────────────────────────────────────────
            Center(
              child: Container(
                width: 40,
                height: 4,
                decoration: BoxDecoration(
                  color: scheme.onSurfaceVariant.withValues(alpha: 0.3),
                  borderRadius: BorderRadius.circular(2),
                ),
              ),
            ),
            const SizedBox(height: 20),
            AppSectionHeader(
              title: _isEditing ? 'Editar equino' : 'Nuevo equino',
              subtitle: _isEditing
                  ? 'Actualiza los datos de ${widget.existing!.name}'
                  : 'Registra un nuevo equino en el sistema',
            ),
            const SizedBox(height: 24),

            // ── Image picker ──────────────────────────────────────────────
            Container(
              width: double.infinity,
              margin: const EdgeInsets.only(bottom: 16),
              decoration: BoxDecoration(
                color: scheme.surfaceContainerHighest,
                borderRadius: BorderRadius.circular(8),
              ),
              child: InkWell(
                borderRadius: BorderRadius.circular(8),
                onTap: _pickImage,
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    children: [
                      if (_imageBase64 != null)
                        Center(
                          child: FractionallySizedBox(
                            widthFactor: 0.4,
                            child: ClipRRect(
                              borderRadius: BorderRadius.circular(4),
                              child: AspectRatio(
                                aspectRatio: 1.0,
                                child: Image.memory(
                                  base64Decode(_imageBase64!),
                                  width: double.infinity,
                                  fit: BoxFit.cover,
                                ),
                              ),
                            ),
                          ),
                        )
                      else
                        Icon(Symbols.add_photo_alternate,
                            size: 48, color: scheme.onSurfaceVariant),
                      const SizedBox(height: 8),
                      Text(
                        _imageBase64 != null
                            ? 'Tocar para cambiar foto'
                            : 'Tocar para agregar foto',
                        style: Theme.of(context)
                            .textTheme
                            .bodySmall
                            ?.copyWith(color: scheme.onSurfaceVariant),
                      ),
                    ],
                  ),
                ),
              ),
            ),
            const SizedBox(height: 16),

            // ── Identificación ──────────────────────────────────────────
            _sectionHeader('Identificación'),
            const SizedBox(height: 12),
            AppTextField(
              label: 'Nombre *',
              hintText: 'Ej: Relámpago',
              controller: _nameController,
              prefixIcon: Padding(
                padding: const EdgeInsets.all(12),
                child: Icon(Symbols.badge_rounded, size: 18, color: scheme.onSurfaceVariant),
              ),
            ),
            const SizedBox(height: 12),
            AppTextField(
              label: 'Número de inventario',
              hintText: 'Ej: 1234',
              controller: _inventoryNumberController,
              keyboardType: TextInputType.number,
              prefixIcon: Padding(
                padding: const EdgeInsets.all(12),
                child: Icon(Symbols.tag_rounded, size: 18, color: scheme.onSurfaceVariant),
              ),
            ),
            const SizedBox(height: 20),

            // ── Ficha técnica ───────────────────────────────────────────
            _sectionHeader('Ficha técnica'),
            const SizedBox(height: 12),
            _dropdownField(
              label: 'Especie',
              value: _species,
              items: const [
                DropdownMenuItem(value: 'mule', child: Text('Mula')),
                DropdownMenuItem(value: 'donkey', child: Text('Asno')),
                DropdownMenuItem(value: 'horse', child: Text('Caballo')),
              ],
              onChanged: (v) {
                if (v != null) setState(() => _species = v);
              },
              prefixIcon: Symbols.pets_rounded,
            ),
            const SizedBox(height: 12),
            AppTextField(
              label: 'Raza',
              hintText: 'Ej: Criollo',
              controller: _breedController,
              prefixIcon: Padding(
                padding: const EdgeInsets.all(12),
                child: Icon(Symbols.category_rounded, size: 18, color: scheme.onSurfaceVariant),
              ),
            ),
            const SizedBox(height: 12),
            _dropdownField(
              label: 'Sexo',
              value: _sex,
              items: const [
                DropdownMenuItem(value: 'male', child: Text('Macho')),
                DropdownMenuItem(value: 'female', child: Text('Hembra')),
              ],
              onChanged: (v) {
                if (v != null) setState(() => _sex = v);
              },
              prefixIcon: Symbols.wc_rounded,
            ),
            const SizedBox(height: 12),
            AppTextField(
              label: 'Color de capa',
              hintText: 'Ej: Zaino',
              controller: _coatColorController,
              prefixIcon: Padding(
                padding: const EdgeInsets.all(12),
                child: Icon(Symbols.palette_rounded, size: 18, color: scheme.onSurfaceVariant),
              ),
            ),
            const SizedBox(height: 12),
            AppTextField(
              label: 'Paso / Marcha',
              hintText: 'Ej: Picadero',
              controller: _gaitController,
              prefixIcon: Padding(
                padding: const EdgeInsets.all(12),
                child: Icon(Symbols.directions_walk_rounded, size: 18, color: scheme.onSurfaceVariant),
              ),
            ),
            const SizedBox(height: 20),

            // ── Medidas ─────────────────────────────────────────────────
            _sectionHeader('Medidas'),
            const SizedBox(height: 12),
            AppTextField(
              label: 'Peso (kg)',
              hintText: 'Ej: 450',
              controller: _weightController,
              keyboardType: TextInputType.number,
              prefixIcon: Padding(
                padding: const EdgeInsets.all(12),
                child: Icon(Symbols.weight_rounded, size: 18, color: scheme.onSurfaceVariant),
              ),
            ),
            const SizedBox(height: 12),
            AppTextField(
              label: 'Alzada (m)',
              hintText: 'Ej: 1.55',
              controller: _heightController,
              keyboardType:
                  const TextInputType.numberWithOptions(decimal: true),
              prefixIcon: Padding(
                padding: const EdgeInsets.all(12),
                child: Icon(Symbols.height_rounded, size: 18, color: scheme.onSurfaceVariant),
              ),
            ),
            const SizedBox(height: 12),
            AppTextField(
              label: 'Carga máxima jinete (kg)',
              hintText: 'Ej: 90',
              controller: _maxRiderWeightController,
              keyboardType: TextInputType.number,
              prefixIcon: Padding(
                padding: const EdgeInsets.all(12),
                child: Icon(Symbols.fitness_center_rounded, size: 18, color: scheme.onSurfaceVariant),
              ),
            ),
            const SizedBox(height: 20),

            // ── Estado ──────────────────────────────────────────────────
            _sectionHeader('Estado'),
            const SizedBox(height: 12),
            _dropdownField(
              label: 'Estado operativo',
              value: _status,
              items: EquineOperationalStatus.values
                  .map((s) => DropdownMenuItem(
                        value: s,
                        child: Text(equineStatusLabel(s)),
                      ))
                  .toList(),
              onChanged: (v) {
                if (v != null) setState(() => _status = v);
              },
              prefixIcon: Symbols.radio_button_checked_rounded,
            ),
            const SizedBox(height: 12),
            Row(
              children: [
                Icon(Symbols.check_circle_rounded, size: 14, color: scheme.onSurfaceVariant),
                const SizedBox(width: 6),
                Text(
                  'DISPONIBLE',
                  style: Theme.of(context).textTheme.labelSmall?.copyWith(
                        color: scheme.onSurfaceVariant,
                        fontWeight: FontWeight.w800,
                        letterSpacing: 1.8,
                      ),
                ),
                const Spacer(),
                Switch(
                  value: _isAvailable,
                  onChanged: (v) => setState(() => _isAvailable = v),
                ),
              ],
            ),
            const SizedBox(height: 12),
            AppTextField(
              label: 'Notas',
              hintText: 'Observaciones adicionales...',
              controller: _notesController,
              maxLines: 3,
              prefixIcon: Padding(
                padding: const EdgeInsets.all(12),
                child: Icon(Symbols.notes_rounded, size: 18, color: scheme.onSurfaceVariant),
              ),
            ),
            const SizedBox(height: 24),

            // ── Actions ─────────────────────────────────────────────────
            Row(
              children: [
                Expanded(
                  child: AppButton(
                    label: 'Cancelar',
                    variant: AppButtonVariant.secondary,
                    onPressed: () => Navigator.of(context).pop(),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: AppButton(
                    label: 'Guardar',
                    onPressed: _onSave,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 8),
          ],
        ),
      ),
    );
  }

  // ── Helpers ──────────────────────────────────────────────────────────────

  Widget _sectionHeader(String title, {IconData? icon}) {
    return Row(
      children: [
        if (icon != null) ...[
          Icon(icon, size: 18, color: Theme.of(context).colorScheme.onSurfaceVariant),
          const SizedBox(width: 8),
        ],
        Expanded(
          child: AppSectionHeader(
            title: title,
            variant: AppSectionHeaderVariant.compact,
          ),
        ),
      ],
    );
  }

  Widget _dropdownField<T>({
    required String label,
    required T value,
    required List<DropdownMenuItem<T>> items,
    required ValueChanged<T?> onChanged,
    IconData? prefixIcon,
  }) {
    final scheme = Theme.of(context).colorScheme;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      mainAxisSize: MainAxisSize.min,
      children: [
        Row(
          children: [
            if (prefixIcon != null) ...[
              Icon(prefixIcon, size: 14, color: scheme.onSurfaceVariant),
              const SizedBox(width: 6),
            ],
            Text(
              label.toUpperCase(),
              style: Theme.of(context).textTheme.labelSmall?.copyWith(
                    color: scheme.onSurfaceVariant,
                    fontWeight: FontWeight.w800,
                    letterSpacing: 1.8,
                  ),
            ),
          ],
        ),
        const SizedBox(height: 6),
        Container(
          width: double.infinity,
          padding: const EdgeInsets.symmetric(horizontal: 14),
          decoration: BoxDecoration(
            color: scheme.surfaceContainerLow,
            borderRadius: AppRadii.radiusLg,
            border: Border.all(color: scheme.outlineVariant),
          ),
          child: DropdownButtonHideUnderline(
            child: DropdownButton<T>(
              value: value,
              isExpanded: true,
              items: items,
              onChanged: onChanged,
              style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                    color: scheme.onSurface,
                  ),
              dropdownColor: scheme.surfaceContainerLow,
            ),
          ),
        ),
      ],
    );
  }

  Future<void> _pickImage() async {
    final messenger = ScaffoldMessenger.of(context);

    try {
      final picker = ImagePicker();
      final image = await picker.pickImage(
        source: ImageSource.gallery,
        maxWidth: 1024,
        maxHeight: 1024,
        imageQuality: 80,
      );
      if (image == null) return;

      final supportsNativeCropping = !kIsWeb &&
          (defaultTargetPlatform == TargetPlatform.android ||
              defaultTargetPlatform == TargetPlatform.iOS);
      final bytes = supportsNativeCropping
          ? await _cropAndRead(image)
          : await image.readAsBytes();
      setState(() {
        _selectedImage = image;
        _imageBase64 = base64Encode(bytes);
      });
    } catch (e) {
      debugPrint('Error picking image: $e');
      if (mounted) {
        messenger.showSnackBar(
          SnackBar(content: Text('Error al seleccionar foto: $e')),
        );
      }
    }
  }

  Future<Uint8List> _cropAndRead(XFile image) async {
    final cropped = await ImageCropper().cropImage(
      sourcePath: image.path,
      aspectRatio: const CropAspectRatio(ratioX: 1, ratioY: 1),
      uiSettings: [
        AndroidUiSettings(
          toolbarTitle: 'Ajustar recorte',
          toolbarColor: Theme.of(context).colorScheme.surface,
          toolbarWidgetColor: Theme.of(context).colorScheme.onSurface,
          backgroundColor: Theme.of(context).colorScheme.surface,
          activeControlsWidgetColor: Theme.of(context).colorScheme.primary,
        ),
        IOSUiSettings(
          title: 'Ajustar recorte',
          aspectRatioLockEnabled: true,
          resetButtonHidden: true,
        ),
      ],
    );
    return cropped != null
        ? await cropped.readAsBytes()
        : await image.readAsBytes();
  }

  void _onSave() {
    final name = _nameController.text.trim();
    if (name.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('El nombre es obligatorio')),
      );
      return;
    }

    // Por ahora solo cerramos el sheet — la persistencia se conecta
    // cuando el backend exponga el endpoint de creación/edición.
    Navigator.of(context).pop(<String, dynamic>{
      'name': name,
      'inventory_number': int.tryParse(_inventoryNumberController.text),
      'species': _species,
      'breed': _breedController.text.trim().nullIfEmpty,
      'sex': _sex,
      'coat_color': _coatColorController.text.trim().nullIfEmpty,
      'gait': _gaitController.text.trim().nullIfEmpty,
      'weight_kg': double.tryParse(_weightController.text),
      'height_m': double.tryParse(_heightController.text),
      'max_rider_weight_kg': double.tryParse(_maxRiderWeightController.text),
      'operational_status': _status == EquineOperationalStatus.inService
          ? 'in_service'
          : _status.name,
      'is_available': _isAvailable,
      'availability_notes': _notesController.text.trim().nullIfEmpty,
      'image_base64': _imageBase64,
    });
  }
}

extension _StringExt on String {
  String? get nullIfEmpty => isEmpty ? null : this;
}
