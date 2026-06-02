import 'package:flutter/material.dart';

import 'package:mobile_ui/src/widgets/app_badge.dart';
import 'package:mobile_ui/src/widgets/app_button.dart';
import 'package:mobile_ui/src/widgets/app_section_header.dart';
import 'package:mobile_ui/src/widgets/app_text_field.dart';
import 'package:mobile/features/auth/presentation/auth_controller.dart';
import 'package:mobile/features/catalogs/catalogs_module.dart';
import 'package:mobile/features/catalogs/experiences/domain/experience.dart';
import 'package:mobile/features/catalogs/schedules/domain/schedule.dart';
import 'package:mobile/features/catalogs/schedules/domain/schedule_status.dart';
import 'package:mobile/features/catalogs/schedules/presentation/controllers/schedule_form_controller.dart';

class ScheduleFormPage extends StatefulWidget {
  const ScheduleFormPage({
    super.key,
    required this.module,
    required this.authController,
    this.editing,
  });

  final CatalogsModule module;
  final AuthController authController;
  final CatalogSchedule? editing;

  @override
  State<ScheduleFormPage> createState() => _ScheduleFormPageState();
}

class _ScheduleFormPageState extends State<ScheduleFormPage> {
  final ScheduleFormController _controller = ScheduleFormController();

  late final TextEditingController _dateCtrl;
  late final TextEditingController _timeCtrl;
  late final TextEditingController _capacityCtrl;
  late final TextEditingController _reservedCtrl;
  late final TextEditingController _internalCtrl;
  late final TextEditingController _blockedCtrl;
  late final TextEditingController _notesCtrl;

  bool _isSaving = false;
  String? _error;
  List<CatalogExperience> _experiences = const <CatalogExperience>[];

  bool get _isEditing => widget.editing != null;

  @override
  void initState() {
    super.initState();
    final editing = widget.editing;
    if (editing != null) {
      _controller
        ..experienceId = editing.experienceId
        ..dateIso = editing.date
        ..startTime = editing.startTime
        ..isActive = editing.isActive
        ..capacityTotal = editing.capacityTotal
        ..reservedSlots = editing.reservedSlots
        ..internalSlots = editing.internalSlots
        ..blockedSlots = editing.blockedSlots
        ..customRequestOnly = editing.customRequestOnly
        ..notes = editing.notes ?? ''
        ..status = editing.status;
    }
    _dateCtrl = TextEditingController(text: _controller.dateIso);
    _timeCtrl = TextEditingController(text: _controller.startTime);
    _capacityCtrl = TextEditingController(
      text: _controller.capacityTotal.toString(),
    );
    _reservedCtrl = TextEditingController(
      text: _controller.reservedSlots.toString(),
    );
    _internalCtrl = TextEditingController(
      text: _controller.internalSlots.toString(),
    );
    _blockedCtrl = TextEditingController(
      text: _controller.blockedSlots.toString(),
    );
    _notesCtrl = TextEditingController(text: _controller.notes);
    _loadExperiences();
  }

  Future<void> _loadExperiences() async {
    final experiences = await widget.module.experiences.list();
    if (!mounted) return;
    setState(() {
      _experiences = experiences
          .where((item) => item.isActive)
          .toList(growable: false);
      if (_controller.experienceId.isEmpty && _experiences.isNotEmpty) {
        _controller.experienceId = _experiences.first.id;
      }
    });
  }

  @override
  void dispose() {
    _dateCtrl.dispose();
    _timeCtrl.dispose();
    _capacityCtrl.dispose();
    _reservedCtrl.dispose();
    _internalCtrl.dispose();
    _blockedCtrl.dispose();
    _notesCtrl.dispose();
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
        await widget.module.schedules.update(
          id: widget.editing!.id,
          isActive: _controller.isActive,
          capacityTotal: _controller.capacityTotal,
          reservedSlots: _controller.reservedSlots,
          internalSlots: _controller.internalSlots,
          blockedSlots: _controller.blockedSlots,
          status: _controller.status,
          customRequestOnly: _controller.customRequestOnly,
          notes: _controller.notes.trim().isEmpty
              ? null
              : _controller.notes.trim(),
        );
      } else {
        await widget.module.schedules.create(
          experienceId: _controller.experienceId,
          dateIso: _controller.dateIso,
          startTime: _controller.startTime,
          isActive: _controller.isActive,
          capacityTotal: _controller.capacityTotal,
          reservedSlots: _controller.reservedSlots,
          internalSlots: _controller.internalSlots,
          blockedSlots: _controller.blockedSlots,
          customRequestOnly: _controller.customRequestOnly,
          notes: _controller.notes.trim().isEmpty
              ? null
              : _controller.notes.trim(),
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
            eyebrow: 'Catalogos > Fechas operativas',
            title: _isEditing ? 'Editar fecha' : 'Crear fecha',
            trailing: AppButton(
              label: 'Volver',
              icon: Icons.arrow_back_rounded,
              variant: AppButtonVariant.ghost,
              onPressed: () => Navigator.of(context).pop(),
            ),
          ),
          const SizedBox(height: 14),
          DropdownButtonFormField<String>(
            initialValue: _controller.experienceId.isEmpty
                ? null
                : _controller.experienceId,
            decoration: const InputDecoration(labelText: 'Experiencia'),
            items: [
              for (final item in _experiences)
                DropdownMenuItem<String>(
                  value: item.id,
                  child: Text(item.name),
                ),
            ],
            onChanged: (value) {
              if (value == null) return;
              setState(() {
                _controller.experienceId = value;
              });
            },
          ),
          const SizedBox(height: 10),
          AppTextField(
            controller: _dateCtrl,
            label: 'Fecha (YYYY-MM-DD)',
            onChanged: (value) => _controller.dateIso = value.trim(),
          ),
          const SizedBox(height: 10),
          AppTextField(
            controller: _timeCtrl,
            label: 'Hora (HH:MM:SS)',
            onChanged: (value) => _controller.startTime = value.trim(),
          ),
          const SizedBox(height: 10),
          AppTextField(
            controller: _capacityCtrl,
            label: 'Capacidad total',
            keyboardType: TextInputType.number,
            onChanged: (value) =>
                _controller.capacityTotal = int.tryParse(value) ?? 0,
          ),
          const SizedBox(height: 10),
          AppTextField(
            controller: _reservedCtrl,
            label: 'Cupos reservados',
            keyboardType: TextInputType.number,
            onChanged: (value) =>
                _controller.reservedSlots = int.tryParse(value) ?? 0,
          ),
          const SizedBox(height: 10),
          AppTextField(
            controller: _internalCtrl,
            label: 'Cupos internos',
            keyboardType: TextInputType.number,
            onChanged: (value) =>
                _controller.internalSlots = int.tryParse(value) ?? 0,
          ),
          const SizedBox(height: 10),
          AppTextField(
            controller: _blockedCtrl,
            label: 'Cupos bloqueados',
            keyboardType: TextInputType.number,
            onChanged: (value) =>
                _controller.blockedSlots = int.tryParse(value) ?? 0,
          ),
          const SizedBox(height: 10),
          AppTextField(
            controller: _notesCtrl,
            label: 'Observaciones',
            maxLines: 3,
            onChanged: (value) => _controller.notes = value,
          ),
          const SizedBox(height: 8),
          SwitchListTile(
            contentPadding: EdgeInsets.zero,
            title: const Text('Fecha activa'),
            value: _controller.isActive,
            onChanged: (value) {
              setState(() {
                _controller.isActive = value;
              });
            },
          ),
          const SizedBox(height: 4),
          DropdownButtonFormField<CatalogScheduleStatus>(
            initialValue: _controller.status,
            decoration: const InputDecoration(labelText: 'Estado'),
            items: const [
              DropdownMenuItem(
                value: CatalogScheduleStatus.open,
                child: Text('Open'),
              ),
              DropdownMenuItem(
                value: CatalogScheduleStatus.closed,
                child: Text('Closed'),
              ),
              DropdownMenuItem(
                value: CatalogScheduleStatus.full,
                child: Text('Full'),
              ),
            ],
            onChanged: (value) {
              if (value == null) return;
              setState(() {
                _controller.status = value;
              });
            },
          ),
          const SizedBox(height: 8),
          SwitchListTile(
            contentPadding: EdgeInsets.zero,
            title: const Text('Solo solicitud personalizada'),
            value: _controller.customRequestOnly,
            onChanged: (value) {
              setState(() {
                _controller.customRequestOnly = value;
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
