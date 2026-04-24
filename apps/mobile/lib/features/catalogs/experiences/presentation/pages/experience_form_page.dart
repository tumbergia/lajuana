import 'package:flutter/material.dart';

import '../../../../../app/widgets/app_badge.dart';
import '../../../../../app/widgets/app_button.dart';
import '../../../../../app/widgets/app_section_header.dart';
import '../../../../../app/widgets/app_text_field.dart';
import '../../../../auth/presentation/auth_controller.dart';
import '../../../catalogs_module.dart';
import '../../domain/experience.dart';
import '../controllers/experience_form_controller.dart';

class ExperienceFormPage extends StatefulWidget {
  const ExperienceFormPage({
    super.key,
    required this.module,
    required this.authController,
    this.editing,
  });

  final CatalogsModule module;
  final AuthController authController;
  final CatalogExperience? editing;

  @override
  State<ExperienceFormPage> createState() => _ExperienceFormPageState();
}

class _ExperienceFormPageState extends State<ExperienceFormPage> {
  final ExperienceFormController _controller = ExperienceFormController();

  late final TextEditingController _nameCtrl;
  late final TextEditingController _slugCtrl;
  late final TextEditingController _descriptionCtrl;
  late final TextEditingController _durationHoursCtrl;
  late final TextEditingController _durationDaysCtrl;
  late final TextEditingController _capacityCtrl;

  String? _error;
  bool _isSaving = false;

  bool get _isEditing => widget.editing != null;

  @override
  void initState() {
    super.initState();
    final editing = widget.editing;
    if (editing != null) {
      _controller
        ..name = editing.name
        ..slug = editing.slug
        ..description = editing.description
        ..level = editing.level
        ..durationHours = editing.durationHours
        ..durationDays = editing.durationDays
        ..baseCapacity = editing.baseCapacity
        ..isActive = editing.isActive;
    }
    _nameCtrl = TextEditingController(text: _controller.name);
    _slugCtrl = TextEditingController(text: _controller.slug);
    _descriptionCtrl = TextEditingController(text: _controller.description);
    _durationHoursCtrl = TextEditingController(
      text: _controller.durationHours?.toString() ?? '',
    );
    _durationDaysCtrl = TextEditingController(
      text: _controller.durationDays?.toString() ?? '',
    );
    _capacityCtrl = TextEditingController(
      text: _controller.baseCapacity?.toString() ?? '',
    );
  }

  @override
  void dispose() {
    _nameCtrl.dispose();
    _slugCtrl.dispose();
    _descriptionCtrl.dispose();
    _durationHoursCtrl.dispose();
    _durationDaysCtrl.dispose();
    _capacityCtrl.dispose();
    _controller.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    setState(() {
      _error = _controller.validate();
    });
    if (_error != null) return;

    setState(() {
      _isSaving = true;
    });
    try {
      if (_isEditing) {
        await widget.module.experiences.update(
          id: widget.editing!.id,
          name: _controller.name.trim(),
          description: _controller.description.trim(),
          level: _controller.level,
          isActive: _controller.isActive,
          durationHours: _controller.durationHours,
          durationDays: _controller.durationDays,
          baseCapacity: _controller.baseCapacity,
        );
      } else {
        await widget.module.experiences.create(
          name: _controller.name.trim(),
          slug: _controller.slug.trim(),
          description: _controller.description.trim(),
          level: _controller.level,
          durationHours: _controller.durationHours,
          durationDays: _controller.durationDays,
          baseCapacity: _controller.baseCapacity,
          isActive: _controller.isActive,
        );
      }
      if (!mounted) return;
      Navigator.of(context).pop();
    } catch (e) {
      setState(() {
        _error = e.toString();
      });
    } finally {
      if (mounted) {
        setState(() {
          _isSaving = false;
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(24, 24, 24, 24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          AppSectionHeader(
            eyebrow: 'Catalogos > Experiencias',
            title: _isEditing ? 'Editar experiencia' : 'Crear experiencia',
            trailing: AppButton(
              label: 'Volver',
              icon: Icons.arrow_back_rounded,
              variant: AppButtonVariant.ghost,
              onPressed: () => Navigator.of(context).pop(),
            ),
          ),
          const SizedBox(height: 14),
          AppTextField(
            controller: _nameCtrl,
            label: 'Nombre',
            onChanged: _controller.updateName,
          ),
          const SizedBox(height: 10),
          AppTextField(
            controller: _slugCtrl,
            label: 'Slug',
            onChanged: _controller.updateSlug,
          ),
          const SizedBox(height: 10),
          AppTextField(
            controller: _descriptionCtrl,
            label: 'Descripcion',
            maxLines: 3,
            onChanged: _controller.updateDescription,
          ),
          const SizedBox(height: 10),
          AppTextField(
            controller: _durationHoursCtrl,
            label: 'Duracion horas',
            keyboardType: TextInputType.number,
            onChanged: (value) =>
                _controller.updateDurationHours(int.tryParse(value.trim())),
          ),
          const SizedBox(height: 10),
          AppTextField(
            controller: _durationDaysCtrl,
            label: 'Duracion dias',
            keyboardType: TextInputType.number,
            onChanged: (value) =>
                _controller.updateDurationDays(int.tryParse(value.trim())),
          ),
          const SizedBox(height: 10),
          AppTextField(
            controller: _capacityCtrl,
            label: 'Capacidad base',
            keyboardType: TextInputType.number,
            onChanged: (value) =>
                _controller.updateBaseCapacity(int.tryParse(value.trim())),
          ),
          const SizedBox(height: 10),
          DropdownButtonFormField<String>(
            initialValue: _controller.level,
            decoration: const InputDecoration(labelText: 'Nivel recomendado'),
            items: const [
              DropdownMenuItem(value: 'basic', child: Text('Basic')),
              DropdownMenuItem(
                value: 'intermediate',
                child: Text('Intermediate'),
              ),
              DropdownMenuItem(value: 'advanced', child: Text('Advanced')),
            ],
            onChanged: (value) {
              if (value == null) return;
              setState(() {
                _controller.updateLevel(value);
              });
            },
          ),
          const SizedBox(height: 8),
          SwitchListTile(
            contentPadding: EdgeInsets.zero,
            title: const Text('Experiencia activa'),
            value: _controller.isActive,
            onChanged: (value) {
              setState(() {
                _controller.updateIsActive(value);
              });
            },
          ),
          if (_error != null) ...[
            const SizedBox(height: 8),
            AppBadge(
              label: _error!,
              tone: AppBadgeTone.danger,
              uppercase: false,
            ),
          ],
          const SizedBox(height: 12),
          AppButton(
            label: _isSaving ? 'Guardando...' : 'Guardar',
            expanded: true,
            onPressed: _isSaving ? null : _submit,
          ),
        ],
      ),
    );
  }
}
