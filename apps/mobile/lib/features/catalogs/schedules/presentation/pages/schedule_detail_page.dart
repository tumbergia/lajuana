import 'package:flutter/material.dart';

import 'package:mobile_ui/src/widgets/app_button.dart';
import 'package:mobile_ui/src/widgets/app_centered_loader.dart';
import 'package:mobile_ui/src/widgets/app_entity_row_card.dart';
import 'package:mobile_ui/src/widgets/app_section_header.dart';
import 'package:mobile/features/auth/presentation/auth_controller.dart';
import 'package:mobile/features/catalogs/catalogs_module.dart';
import 'package:mobile/features/catalogs/schedules/domain/schedule.dart';
import 'package:mobile/features/catalogs/schedules/presentation/widgets/schedule_capacity_summary.dart';
import 'package:mobile/features/catalogs/schedules/presentation/widgets/schedule_status_badge.dart';
import 'schedule_form_page.dart';

class ScheduleDetailPage extends StatefulWidget {
  const ScheduleDetailPage({
    super.key,
    required this.module,
    required this.authController,
    required this.scheduleId,
  });

  final CatalogsModule module;
  final AuthController authController;
  final String scheduleId;

  @override
  State<ScheduleDetailPage> createState() => _ScheduleDetailPageState();
}

class _ScheduleDetailPageState extends State<ScheduleDetailPage> {
  CatalogSchedule? _schedule;
  bool _isLoading = true;
  String? _error;

  bool get _isAdmin => widget.authController.currentUser?.role == 'admin';

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() {
      _isLoading = true;
      _error = null;
    });
    try {
      _schedule = await widget.module.schedules.getById(widget.scheduleId);
      if (_schedule == null) {
        _error = 'La fecha operativa no existe en el catalogo local.';
      }
    } catch (e) {
      _error = e.toString();
    } finally {
      if (mounted) {
        setState(() {
          _isLoading = false;
        });
      }
    }
  }

  Future<void> _deactivate() async {
    if (_schedule == null) return;
    await widget.module.schedules.deactivate(_schedule!.id);
    await _load();
  }

  @override
  Widget build(BuildContext context) {
    final schedule = _schedule;
    return Padding(
      padding: const EdgeInsets.fromLTRB(24, 24, 24, 24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          AppSectionHeader(
            eyebrow: 'Catalogos > Fechas operativas',
            title: 'Detalle',
            trailing: AppButton(
              label: 'Volver',
              icon: Icons.arrow_back_rounded,
              variant: AppButtonVariant.ghost,
              onPressed: () => Navigator.of(context).pop(),
            ),
          ),
          const SizedBox(height: 14),
          Expanded(
            child: _isLoading
                ? const AppCenteredLoader()
                : ListView(
                    children: [
                      if (_error != null)
                        AppEntityRowCard(
                          title: 'Error',
                          subtitle: _error!,
                          selected: true,
                        )
                      else if (schedule != null) ...[
                        AppEntityRowCard(
                          title: '${schedule.date} ${schedule.startTime}',
                          subtitle: 'Experiencia ${schedule.experienceId}',
                          badge: scheduleStatusBadgeFor(schedule),
                          selected: true,
                        ),
                        const SizedBox(height: 10),
                        ScheduleCapacitySummary(schedule: schedule),
                        const SizedBox(height: 10),
                        AppEntityRowCard(
                          title:
                              'Cupos R:${schedule.reservedSlots} I:${schedule.internalSlots} B:${schedule.blockedSlots}',
                          subtitle: schedule.notes ?? 'Sin observaciones',
                        ),
                        if (_isAdmin) ...[
                          const SizedBox(height: 16),
                          AppButton(
                            label: 'Editar',
                            icon: Icons.edit_rounded,
                            expanded: true,
                            onPressed: () async {
                              await Navigator.of(context).push(
                                MaterialPageRoute<void>(
                                  builder: (_) => ScheduleFormPage(
                                    module: widget.module,
                                    authController: widget.authController,
                                    editing: schedule,
                                  ),
                                ),
                              );
                              await _load();
                            },
                          ),
                          const SizedBox(height: 8),
                          AppButton(
                            label: 'Desactivar',
                            icon: Icons.block_rounded,
                            variant: AppButtonVariant.secondary,
                            expanded: true,
                            onPressed: _deactivate,
                          ),
                        ],
                      ],
                    ],
                  ),
          ),
        ],
      ),
    );
  }
}
