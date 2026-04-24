import 'package:flutter/material.dart';

import '../../../../../app/widgets/app_button.dart';
import '../../../../../app/widgets/app_centered_loader.dart';
import '../../../../../app/widgets/app_entity_row_card.dart';
import '../../../../../app/widgets/app_section_header.dart';
import '../../../../auth/presentation/auth_controller.dart';
import '../../../catalogs_module.dart';
import '../../domain/experience.dart';
import '../widgets/experience_status_badge.dart';
import 'experience_form_page.dart';

class ExperienceDetailPage extends StatefulWidget {
  const ExperienceDetailPage({
    super.key,
    required this.module,
    required this.authController,
    required this.experienceId,
  });

  final CatalogsModule module;
  final AuthController authController;
  final String experienceId;

  @override
  State<ExperienceDetailPage> createState() => _ExperienceDetailPageState();
}

class _ExperienceDetailPageState extends State<ExperienceDetailPage> {
  CatalogExperience? _experience;
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
      _experience = await widget.module.experiences.getById(
        widget.experienceId,
      );
      if (_experience == null) {
        _error = 'La experiencia no existe en el catalogo local.';
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
    if (_experience == null) return;
    await widget.module.experiences.deactivate(_experience!.id);
    await _load();
  }

  @override
  Widget build(BuildContext context) {
    final experience = _experience;
    return Padding(
      padding: const EdgeInsets.fromLTRB(24, 24, 24, 24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          AppSectionHeader(
            eyebrow: 'Catalogos > Experiencias',
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
                      else if (experience != null) ...[
                        AppEntityRowCard(
                          title: experience.name,
                          subtitle: experience.description,
                          badge: experienceStatusBadgeFor(experience),
                          selected: true,
                        ),
                        const SizedBox(height: 10),
                        AppEntityRowCard(
                          title: 'Nivel ${experience.level}',
                          subtitle:
                              'Duracion h:${experience.durationHours ?? '-'} d:${experience.durationDays ?? '-'}',
                        ),
                        const SizedBox(height: 10),
                        AppEntityRowCard(
                          title: 'Capacidad base',
                          subtitle: '${experience.baseCapacity ?? 0}',
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
                                  builder: (_) => ExperienceFormPage(
                                    module: widget.module,
                                    authController: widget.authController,
                                    editing: experience,
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
