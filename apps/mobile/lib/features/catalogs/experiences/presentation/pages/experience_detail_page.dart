import 'package:flutter/material.dart';

import 'package:mobile_ui/src/widgets/app_button.dart';
import 'package:mobile_ui/src/widgets/app_centered_loader.dart';
import 'package:mobile_ui/src/widgets/app_entity_row_card.dart';
import 'package:mobile_ui/src/widgets/app_section_header.dart';
import 'package:mobile_ui/src/widgets/cards/app_pricing_tiers_table.dart';
import 'package:mobile/features/auth/presentation/auth_controller.dart';
import 'package:mobile/features/catalogs/catalogs_module.dart';
import 'package:mobile/features/catalogs/experiences/domain/experience.dart';
import 'package:mobile/features/catalogs/experiences/presentation/widgets/experience_status_badge.dart';
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
            title: 'Detalle de experiencia',
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
                        if ((experience.subtitle ?? '').isNotEmpty) ...[
                          const SizedBox(height: 10),
                          AppEntityRowCard(
                            title: 'Subtitulo',
                            subtitle: experience.subtitle!,
                          ),
                        ],
                        const SizedBox(height: 10),
                        AppEntityRowCard(
                          title: 'Identificador URL',
                          subtitle: experience.slug,
                        ),
                        if (experience.standardMaxParticipants != null) ...[
                          const SizedBox(height: 10),
                          AppEntityRowCard(
                            title: 'Capacidad estandar',
                            subtitle: '${experience.standardMaxParticipants}',
                          ),
                        ],
                        if (experience.duration != null) ...[
                          const SizedBox(height: 10),
                          AppEntityRowCard(
                            title: 'Duraciones',
                            subtitle:
                                'Experiencia ${experience.duration!.activityMinutes} min | Recorrido ${experience.duration!.routeMinutes} min',
                          ),
                        ],
                        if (experience.routeDetails != null) ...[
                          const SizedBox(height: 10),
                          AppEntityRowCard(
                            title: 'Ruta',
                            subtitle:
                                '${experience.routeDetails!.terrain} | ${experience.routeDetails!.distanceKm ?? '-'} km',
                          ),
                        ],
                        if (experience.pricing != null &&
                            experience.pricing!.tiers.isNotEmpty) ...[
                          const SizedBox(height: 10),
                          AppPricingTiersTable(
                            currency: experience.pricing!.currency,
                            pricesAreNet: experience.pricing!.pricesAreNet,
                            notes: experience.pricing!.pricingNotes,
                            tiers: experience.pricing!.tiers
                                .map(
                                  (tier) => AppPricingTierData(
                                    minParticipants: tier.minParticipants,
                                    maxParticipants: tier.maxParticipants,
                                    pricePerPerson: tier.pricePerPerson,
                                  ),
                                )
                                .toList(growable: false),
                          ),
                        ],
                        if (experience.inclusions != null &&
                            experience.inclusions!.items.isNotEmpty) ...[
                          const SizedBox(height: 10),
                          AppEntityRowCard(
                            title: 'Incluye',
                            subtitle: experience.inclusions!.items.join(', '),
                          ),
                        ],
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
