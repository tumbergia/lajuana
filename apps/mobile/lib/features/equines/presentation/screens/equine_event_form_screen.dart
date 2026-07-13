import 'package:flutter/material.dart';
import 'package:material_symbols_icons/material_symbols_icons.dart';

import 'package:mobile_ui/src/widgets/app_button.dart';
import 'package:mobile_ui/src/widgets/app_scaffold.dart';
import 'package:mobile_ui/src/widgets/app_section_header.dart';
import 'package:mobile_ui/src/widgets/app_text_field.dart';
import 'package:mobile_ui/src/widgets/app_toast.dart';
import 'package:mobile_domain/src/equines/equine_operational_status.dart';
import 'package:mobile/features/equines/presentation/controllers/equine_events_controller.dart';
import 'package:mobile/features/equines/presentation/equine_event_labels.dart';
import 'package:mobile/features/equines/presentation/equine_labels.dart';

/// Formulario para registrar un evento de cuidado/seguimiento del equino.
class EquineEventFormScreen extends StatefulWidget {
  const EquineEventFormScreen({
    super.key,
    required this.equineId,
    required this.equineName,
    required this.controller,
  });

  final String equineId;
  final String equineName;
  final EquineEventsController controller;

  @override
  State<EquineEventFormScreen> createState() => _EquineEventFormScreenState();
}

class _EquineEventFormScreenState extends State<EquineEventFormScreen> {
  late final TextEditingController _titleController;
  late final TextEditingController _descriptionController;
  late final TextEditingController _weightController;
  late final TextEditingController _performedByController;

  @override
  void initState() {
    super.initState();
    final c = widget.controller;
    _titleController = TextEditingController(text: c.title);
    _descriptionController = TextEditingController(text: c.description);
    _weightController = TextEditingController(text: c.measuredWeightText);
    _performedByController = TextEditingController(text: c.performedBy);
    widget.controller.addListener(_onControllerChanged);
  }

  @override
  void dispose() {
    widget.controller.removeListener(_onControllerChanged);
    _titleController.dispose();
    _descriptionController.dispose();
    _weightController.dispose();
    _performedByController.dispose();
    super.dispose();
  }

  void _onControllerChanged() {
    if (mounted) setState(() {});
  }

  Future<void> _pickHappenedAt() async {
    final now = DateTime.now();
    final date = await showDatePicker(
      context: context,
      initialDate: widget.controller.happenedAt,
      firstDate: DateTime(now.year - 2),
      lastDate: now.add(const Duration(days: 1)),
    );
    if (date == null || !mounted) return;

    final time = await showTimePicker(
      context: context,
      initialTime: TimeOfDay.fromDateTime(widget.controller.happenedAt),
    );
    if (time == null) return;

    widget.controller.setHappenedAt(DateTime(
      date.year,
      date.month,
      date.day,
      time.hour,
      time.minute,
    ));
  }

  Future<void> _pickRestUntil() async {
    final date = await showDatePicker(
      context: context,
      initialDate: widget.controller.restUntil ?? DateTime.now(),
      firstDate: DateTime.now(),
      lastDate: DateTime.now().add(const Duration(days: 365)),
    );
    if (date == null) return;
    widget.controller.setRestUntil(
      DateTime(date.year, date.month, date.day, 23, 59),
    );
  }

  Future<void> _pickNextDueAt() async {
    final date = await showDatePicker(
      context: context,
      initialDate: widget.controller.nextDueAt ?? DateTime.now(),
      firstDate: DateTime.now(),
      lastDate: DateTime.now().add(const Duration(days: 730)),
    );
    if (date == null) return;
    widget.controller.setNextDueAt(
      DateTime(date.year, date.month, date.day, 12, 0),
    );
  }

  Future<void> _save() async {
    final created = await widget.controller.submit(widget.equineId);
    if (!mounted) return;

    if (widget.controller.validationError != null) {
      showAppToast(
        context,
        message: widget.controller.validationError!,
        isError: true,
      );
      return;
    }

    if (created == null) {
      showAppToast(
        context,
        message: widget.controller.saveError ?? 'No se pudo guardar el registro.',
        isError: true,
      );
      return;
    }

    final message = created.syncPending
        ? 'Registro guardado offline. Se sincronizará cuando haya conexión.'
        : 'Registro guardado correctamente.';
    showAppToast(context, message: message);
    Navigator.of(context).pop(true);
  }

  @override
  Widget build(BuildContext context) {
    final c = widget.controller;
    final scheme = Theme.of(context).colorScheme;
    final isSaving = c.saveState == EquineEventSaveState.saving;

    return AppScaffold(
      scrollable: true,
      appBar: AppBar(
        title: Text(
          'Nuevo registro',
          style: Theme.of(context).textTheme.titleLarge?.copyWith(
                fontWeight: FontWeight.w800,
              ),
        ),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_rounded),
          onPressed: isSaving ? null : () => Navigator.of(context).pop(),
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Text(
            widget.equineName,
            style: Theme.of(context).textTheme.titleMedium?.copyWith(
                  color: scheme.onSurfaceVariant,
                ),
          ),
          const SizedBox(height: 20),
          AppSectionHeader(
            title: 'Evento',
            variant: AppSectionHeaderVariant.compact,
          ),
          const SizedBox(height: 8),
          DropdownButtonFormField<String>(
            value: c.eventType,
            decoration: const InputDecoration(
              labelText: 'Tipo de evento',
              border: OutlineInputBorder(),
            ),
            items: equineEventTypeOptions.entries
                .map(
                  (e) => DropdownMenuItem(
                    value: e.key,
                    child: Text(e.value),
                  ),
                )
                .toList(growable: false),
            onChanged: isSaving
                ? null
                : (value) {
                    if (value != null) c.setEventType(value);
                  },
          ),
          const SizedBox(height: 12),
          ListTile(
            contentPadding: EdgeInsets.zero,
            title: const Text('Fecha y hora'),
            subtitle: Text(_formatDateTime(c.happenedAt)),
            trailing: IconButton(
              icon: const Icon(Symbols.calendar_month_rounded),
              onPressed: isSaving ? null : _pickHappenedAt,
            ),
          ),
          const SizedBox(height: 8),
          AppTextField(
            controller: _titleController,
            label: 'Título',
            readOnly: isSaving,
            onChanged: c.setTitle,
          ),
          const SizedBox(height: 12),
          AppTextField(
            controller: _descriptionController,
            label: 'Descripción / motivo',
            readOnly: isSaving,
            maxLines: 3,
            onChanged: c.setDescription,
          ),
          const SizedBox(height: 12),
          DropdownButtonFormField<String>(
            value: c.severity,
            decoration: const InputDecoration(
              labelText: 'Severidad (opcional)',
              border: OutlineInputBorder(),
            ),
            items: [
              const DropdownMenuItem<String>(
                child: Text('Sin severidad'),
              ),
              ...equineEventSeverityOptions.entries.map(
                (e) => DropdownMenuItem(
                  value: e.key,
                  child: Text(e.value),
                ),
              ),
            ],
            onChanged: isSaving
                ? null
                : (value) => c.setSeverity(value),
          ),
          if (c.showWeightField) ...[
            const SizedBox(height: 20),
            AppSectionHeader(
              title: 'Medición',
              variant: AppSectionHeaderVariant.compact,
            ),
            const SizedBox(height: 8),
            AppTextField(
              controller: _weightController,
              label: 'Peso medido (kg)',
              inputKind: AppTextInputKind.decimal,
              readOnly: isSaving,
              onChanged: c.setMeasuredWeightText,
            ),
          ],
          if (c.showNextDueField) ...[
            const SizedBox(height: 12),
            ListTile(
              contentPadding: EdgeInsets.zero,
              title: const Text('Próximo control / dosis'),
              subtitle: Text(
                c.nextDueAt != null
                    ? _formatDateTime(c.nextDueAt!)
                    : 'Sin fecha programada',
              ),
              trailing: IconButton(
                icon: const Icon(Symbols.event_rounded),
                onPressed: isSaving ? null : _pickNextDueAt,
              ),
            ),
          ],
          const SizedBox(height: 20),
          AppSectionHeader(
            title: 'Responsable',
            variant: AppSectionHeaderVariant.compact,
          ),
          const SizedBox(height: 8),
          AppTextField(
            controller: _performedByController,
            label: 'Veterinario / herrador / responsable',
            readOnly: isSaving,
            onChanged: c.setPerformedBy,
          ),
          if (c.showAvailabilityFields) ...[
            const SizedBox(height: 20),
            AppSectionHeader(
              title: 'Disponibilidad',
              variant: AppSectionHeaderVariant.compact,
            ),
            const SizedBox(height: 8),
            SwitchListTile(
              contentPadding: EdgeInsets.zero,
              title: const Text('Afecta disponibilidad'),
              subtitle: const Text('El equino no podrá asignarse mientras aplique'),
              value: c.affectsAvailability,
              onChanged: isSaving ? null : c.setAffectsAvailability,
            ),
            if (c.affectsAvailability) ...[
              DropdownButtonFormField<EquineOperationalStatus>(
                value: c.resultingOperationalStatus,
                decoration: const InputDecoration(
                  labelText: 'Nuevo estado operativo',
                  border: OutlineInputBorder(),
                ),
                items: EquineOperationalStatus.values
                    .map(
                      (status) => DropdownMenuItem(
                        value: status,
                        child: Text(equineStatusLabel(status)),
                      ),
                    )
                    .toList(growable: false),
                onChanged: isSaving
                    ? null
                    : (value) {
                        if (value != null) {
                          c.setResultingOperationalStatus(value);
                        }
                      },
              ),
              const SizedBox(height: 12),
              ListTile(
                contentPadding: EdgeInsets.zero,
                title: const Text('Descanso hasta'),
                subtitle: Text(
                  c.restUntil != null
                      ? _formatDateTime(c.restUntil!)
                      : 'Sin fecha de fin',
                ),
                trailing: IconButton(
                  icon: const Icon(Symbols.event_busy_rounded),
                  onPressed: isSaving ? null : _pickRestUntil,
                ),
              ),
            ],
          ],
          const SizedBox(height: 32),
          AppButton(
            label: isSaving ? 'Guardando...' : 'Guardar registro',
            icon: Symbols.save_rounded,
            onPressed: isSaving ? null : _save,
          ),
          const SizedBox(height: 24),
        ],
      ),
    );
  }

  String _formatDateTime(DateTime dt) {
    final local = dt.toLocal();
    final d = '${local.day.toString().padLeft(2, '0')}/'
        '${local.month.toString().padLeft(2, '0')}/'
        '${local.year}';
    final t = '${local.hour.toString().padLeft(2, '0')}:'
        '${local.minute.toString().padLeft(2, '0')}';
    return '$d $t';
  }
}
