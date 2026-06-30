import 'package:flutter/material.dart';

import 'package:mobile_ui/src/widgets/app_button.dart';
import 'package:mobile_ui/src/widgets/app_section_header.dart';
import 'package:mobile_ui/src/widgets/app_text_field.dart';
import 'package:mobile/features/providers/presentation/models/provider_view_models.dart';
import 'package:mobile/features/providers/presentation/widgets/provider_phone_field.dart';

class ProviderFormSheet extends StatefulWidget {
  const ProviderFormSheet({super.key, this.existing});

  final ProviderRecord? existing;

  bool get isEditing => existing != null;

  @override
  State<ProviderFormSheet> createState() => _ProviderFormSheetState();
}

class _ProviderFormSheetState extends State<ProviderFormSheet> {
  final GlobalKey<ProviderPhoneFieldState> _phoneKey =
      GlobalKey<ProviderPhoneFieldState>();
  late final TextEditingController _nameCtrl;
  late final TextEditingController _locationCtrl;
  late final TextEditingController _contactCtrl;
  late final TextEditingController _emailCtrl;
  late final TextEditingController _categoriesCtrl;
  late final TextEditingController _tariffCtrl;
  late final TextEditingController _sourceCtrl;
  late final TextEditingController _capacityCtrl;
  late final TextEditingController _operationalCtrl;
  late String _type;
  late String _status;

  @override
  void initState() {
    super.initState();
    final existing = widget.existing;
    _nameCtrl = TextEditingController(text: existing?.name ?? '');
    _locationCtrl = TextEditingController(text: existing?.locationLabel ?? '');
    _contactCtrl = TextEditingController(text: existing?.contactName ?? '');
    _emailCtrl = TextEditingController(text: existing?.email ?? '');
    _categoriesCtrl = TextEditingController(
      text: existing?.serviceCategories.join(', ') ?? '',
    );
    _tariffCtrl = TextEditingController(text: existing?.tariffNotes ?? '');
    _sourceCtrl = TextEditingController(text: existing?.sourceNotes ?? '');
    _capacityCtrl = TextEditingController(text: existing?.capacityNotes ?? '');
    _operationalCtrl =
        TextEditingController(text: existing?.operationalNotes ?? '');
    _type = existing?.type ?? 'other';
    _status = existing?.status ?? 'active';
  }

  @override
  void dispose() {
    _nameCtrl.dispose();
    _locationCtrl.dispose();
    _contactCtrl.dispose();
    _emailCtrl.dispose();
    _categoriesCtrl.dispose();
    _tariffCtrl.dispose();
    _sourceCtrl.dispose();
    _capacityCtrl.dispose();
    _operationalCtrl.dispose();
    super.dispose();
  }

  bool get _canSubmit => _nameCtrl.text.trim().isNotEmpty;

  List<String> _parseCategories(String raw) {
    if (raw.trim().isEmpty) return const [];
    return raw
        .split(',')
        .map((part) => part.trim())
        .where((part) => part.isNotEmpty)
        .toList(growable: false);
  }

  void _submit() {
    if (!_canSubmit) return;
    Navigator.of(context).pop({
      'name': _nameCtrl.text.trim(),
      'type': _type,
      'status': _status,
      'location_label': _nullableText(_locationCtrl.text),
      'contact_name': _nullableText(_contactCtrl.text),
      'email': _nullableText(_emailCtrl.text),
      'whatsapp_phone': _phoneKey.currentState?.e164Phone,
      'service_categories': _parseCategories(_categoriesCtrl.text),
      'tariff_notes': _nullableText(_tariffCtrl.text),
      'source_notes': _nullableText(_sourceCtrl.text),
      'capacity_notes': _nullableText(_capacityCtrl.text),
      'operational_notes': _nullableText(_operationalCtrl.text),
    });
  }

  String? _nullableText(String value) {
    final trimmed = value.trim();
    return trimmed.isEmpty ? null : trimmed;
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
      child: SingleChildScrollView(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
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
              eyebrow: widget.isEditing ? 'Editar proveedor' : 'Nuevo proveedor',
              title: widget.isEditing ? 'Actualizar datos' : 'Registrar proveedor',
              variant: AppSectionHeaderVariant.compact,
            ),
            const SizedBox(height: 20),
            AppTextField(
              controller: _nameCtrl,
              label: 'Nombre *',
              hintText: 'Ej: Hotel Los Andes',
              onChanged: (_) => setState(() {}),
            ),
            const SizedBox(height: 12),
            DropdownButtonFormField<String>(
              value: _type,
              decoration: const InputDecoration(
                labelText: 'Tipo',
                border: OutlineInputBorder(),
              ),
              items: providerTypeOptions.entries
                  .map(
                    (entry) => DropdownMenuItem(
                      value: entry.key,
                      child: Text(entry.value),
                    ),
                  )
                  .toList(growable: false),
              onChanged: (value) {
                if (value == null) return;
                setState(() => _type = value);
              },
            ),
            const SizedBox(height: 12),
            DropdownButtonFormField<String>(
              value: _status,
              decoration: const InputDecoration(
                labelText: 'Estado',
                border: OutlineInputBorder(),
              ),
              items: providerStatusOptions.entries
                  .map(
                    (entry) => DropdownMenuItem(
                      value: entry.key,
                      child: Text(entry.value),
                    ),
                  )
                  .toList(growable: false),
              onChanged: (value) {
                if (value == null) return;
                setState(() => _status = value);
              },
            ),
            const SizedBox(height: 12),
            AppTextField(
              controller: _locationCtrl,
              label: 'Ubicacion',
              hintText: 'Ej: Barichara, Santander',
            ),
            const SizedBox(height: 12),
            AppTextField(
              controller: _contactCtrl,
              label: 'Contacto',
              hintText: 'Nombre del contacto',
            ),
            const SizedBox(height: 12),
            AppTextField(
              controller: _emailCtrl,
              label: 'Correo',
              hintText: 'contacto@ejemplo.com',
              keyboardType: TextInputType.emailAddress,
            ),
            const SizedBox(height: 12),
            ProviderPhoneField(
              key: _phoneKey,
              initialPhone: widget.existing?.whatsappPhone,
            ),
            const SizedBox(height: 12),
            AppTextField(
              controller: _categoriesCtrl,
              label: 'Categorias de servicio',
              hintText: 'alojamiento, desayuno',
            ),
            const SizedBox(height: 12),
            AppTextField(
              controller: _tariffCtrl,
              label: 'Notas de tarifa',
              maxLines: 2,
            ),
            const SizedBox(height: 12),
            AppTextField(
              controller: _capacityCtrl,
              label: 'Notas de capacidad',
              maxLines: 2,
            ),
            const SizedBox(height: 12),
            AppTextField(
              controller: _operationalCtrl,
              label: 'Notas operativas',
              maxLines: 2,
            ),
            const SizedBox(height: 12),
            AppTextField(
              controller: _sourceCtrl,
              label: 'Notas de origen',
              maxLines: 2,
            ),
            const SizedBox(height: 20),
            AppButton(
              label: widget.isEditing ? 'Guardar cambios' : 'Registrar proveedor',
              icon: widget.isEditing ? Icons.save_rounded : Icons.add,
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
      ),
    );
  }
}
