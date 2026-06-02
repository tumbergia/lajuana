import 'package:flutter/material.dart';
import 'package:material_symbols_icons/material_symbols_icons.dart';

import 'package:mobile_ui/src/widgets/app_button.dart';
import 'package:mobile_ui/src/widgets/app_section_header.dart';
import 'package:mobile_ui/src/widgets/app_text_field.dart';
import 'package:mobile/features/saddles/presentation/models/saddle_view_models.dart';

class SaddleFormSheet extends StatefulWidget {
  const SaddleFormSheet({super.key, this.existing});

  final SaddleRecord? existing;

  bool get isEditing => existing != null;

  @override
  State<SaddleFormSheet> createState() => _SaddleFormSheetState();
}

class _SaddleFormSheetState extends State<SaddleFormSheet> {
  late final TextEditingController _codeCtrl;
  late final TextEditingController _nameCtrl;
  late final TextEditingController _notesCtrl;
  bool _isAvailable = true;

  @override
  void initState() {
    super.initState();
    final existing = widget.existing;
    _codeCtrl = TextEditingController(text: existing?.code ?? '');
    _nameCtrl = TextEditingController(text: existing?.name ?? '');
    _notesCtrl = TextEditingController(text: existing?.notes ?? '');
    _isAvailable = existing?.isAvailable ?? true;
  }

  @override
  void dispose() {
    _codeCtrl.dispose();
    _nameCtrl.dispose();
    _notesCtrl.dispose();
    super.dispose();
  }

  bool get _canSubmit =>
      _codeCtrl.text.trim().isNotEmpty;

  void _submit() {
    if (!_canSubmit) return;
    Navigator.of(context).pop({
      'code': _codeCtrl.text.trim(),
      'name': _nameCtrl.text.trim().isEmpty ? null : _nameCtrl.text.trim(),
      'is_available': _isAvailable,
      'notes': _notesCtrl.text.trim().isEmpty ? null : _notesCtrl.text.trim(),
    });
  }

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;

    return Padding(
      padding: EdgeInsets.only(
        left: 24,
        right: 24,
        top: 20,
        bottom: MediaQuery.of(context).viewInsets.bottom + 24,
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Handle
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
          const SizedBox(height: 16),
          AppSectionHeader(
            eyebrow: widget.isEditing ? 'Editar silla' : 'Nueva silla',
            title: widget.isEditing ? 'Actualizar datos' : 'Registrar silla',
            variant: AppSectionHeaderVariant.compact,
          ),
          const SizedBox(height: 20),
          AppTextField(
            controller: _codeCtrl,
            label: 'Código *',
            hintText: 'Ej: SILLA-001',
            onChanged: (_) => setState(() {}),
          ),
          const SizedBox(height: 12),
          AppTextField(
            controller: _nameCtrl,
            label: 'Nombre',
            hintText: 'Ej: Silla Australiana',
          ),
          const SizedBox(height: 12),
          // Availability toggle
          Row(
            children: [
              Text(
                'Disponible',
                style: Theme.of(context).textTheme.bodyMedium,
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
            controller: _notesCtrl,
            label: 'Notas',
            hintText: 'Observaciones adicionales...',
            maxLines: 3,
          ),
          const SizedBox(height: 20),
          AppButton(
            label: widget.isEditing ? 'Guardar cambios' : 'Registrar silla',
            icon: widget.isEditing
                ? Icons.save_rounded
                : Icons.add,
            expanded: true,
            onPressed: _canSubmit ? _submit : null,
          ),
          const SizedBox(height: 10),
          AppButton(
            label: 'Cancelar',
            icon: Icons.close_rounded,
            variant: AppButtonVariant.secondary,
            expanded: true,
            onPressed: () => Navigator.of(context).pop(),
          ),
        ],
      ),
    );
  }
}
