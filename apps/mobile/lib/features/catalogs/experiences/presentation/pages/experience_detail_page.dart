import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:material_symbols_icons/material_symbols_icons.dart';

import 'package:mobile/app/errors/user_facing_error.dart';
import 'package:mobile_ui/src/widgets/app_button.dart';
import 'package:mobile_ui/src/widgets/app_centered_loader.dart';
import 'package:mobile_ui/src/widgets/app_entity_row_card.dart';
import 'package:mobile_ui/src/widgets/app_section_header.dart';
import 'package:mobile_ui/src/widgets/cards/app_pricing_tiers_table.dart';
import 'package:mobile_ui/src/widgets/refresh_scope.dart';
import 'package:mobile/features/auth/presentation/auth_controller.dart';
import 'package:mobile/features/catalogs/catalogs_module.dart';
import 'package:mobile/features/catalogs/experiences/domain/experience.dart';
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

class _ExperienceDetailPageState extends State<ExperienceDetailPage>
    with RefreshableState {
  CatalogExperience? _experience;
  bool _isLoading = true;
  String? _error;

  bool get _isAdmin => widget.authController.currentUser?.role == 'admin';

  @override
  Future<void> onRefresh() async {
    await widget.module.repository.refreshExperiencesFromServer();
    await _load();
  }

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
      _error = userFacingError(
        e,
        fallback: 'No se pudo cargar la experiencia.',
      );
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

  Future<void> _activate() async {
    if (_experience == null) return;
    await widget.module.experiences.activate(_experience!.id);
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
            eyebrow: 'Experiencias',
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
                ? const RefreshableViewport(child: AppCenteredLoader())
                : ListView(
                    physics: const AlwaysScrollableScrollPhysics(),
                    children: [
                      if (_error != null)
                        AppEntityRowCard(
                          title: 'Error',
                          subtitle: _error!,
                          selected: true,
                        )
                      else if (experience != null) ...[
                        _buildImageSection(experience),
                        const SizedBox(height: 10),

                        // ── Nombre + slug ──
                        _infoRow(
                          icon: Icons.description_rounded,
                          title: experience.name,
                          subtitle: experience.description,
                        ),
                        _spacer(),

                        // ── Estado activo/inactivo ──
                        _infoRow(
                          icon: experience.isActive
                              ? Icons.check_circle_rounded
                              : Icons.cancel_rounded,
                          title: experience.isActive
                              ? 'Activa'
                              : 'Inactiva',
                          subtitle: experience.isActive
                              ? 'Disponible para reservas'
                              : 'Desactivada del catalogo',
                        ),
                        _spacer(),

                        // ── Nivel ──
                        if (experience.level.isNotEmpty)
                          _infoRow(
                            icon: Icons.bar_chart_rounded,
                            title: 'Nivel',
                            subtitle: _levelLabel(experience.level),
                          ),
                        _spacer(),

                        // ── Dificultad ──
                        if (experience.difficulty != null &&
                            experience.difficulty!.isNotEmpty)
                          _infoRow(
                            icon: Icons.trending_up_rounded,
                            title: 'Dificultad',
                            subtitle: _difficultyLabel(experience.difficulty!),
                          ),
                        _spacer(),

                        // ── Categoría ──
                        if (experience.category != null &&
                            experience.category!.isNotEmpty)
                          _infoRow(
                            icon: Icons.category_rounded,
                            title: 'Categoria',
                            subtitle: experience.category!,
                          ),
                        _spacer(),

                        // ── Estado operativo ──
                        if (experience.status != null &&
                            experience.status!.isNotEmpty)
                          _infoRow(
                            icon: Icons.info_outline_rounded,
                            title: 'Estado operativo',
                            subtitle: experience.status!,
                          ),
                        _spacer(),

                        // ── Duración ──
                        _buildDurationSection(experience),
                        _spacer(),

                        // ── Ruta ──
                        if (experience.routeDetails != null) ...[
                          _infoRow(
                            icon: Icons.route_rounded,
                            title: 'Terreno',
                            subtitle: experience.routeDetails!.terrain,
                          ),
                          if (experience.routeDetails!.distanceKm != null)
                            _infoRow(
                              icon: Icons.straighten_rounded,
                              title: 'Distancia',
                              subtitle:
                                  '${experience.routeDetails!.distanceKm} km',
                            ),
                          if (experience.routeDetails!.terrainNotes != null &&
                              experience.routeDetails!.terrainNotes!.isNotEmpty)
                            _infoRow(
                              icon: Icons.notes_rounded,
                              title: 'Notas de ruta',
                              subtitle: experience.routeDetails!.terrainNotes!,
                            ),
                          _spacer(),
                        ],

                        // ── Capacidad ──
                        if (experience.standardMaxParticipants != null ||
                            experience.minParticipants != null ||
                            experience.baseCapacity != null) ...[
                          if (experience.standardMaxParticipants != null)
                            _infoRow(
                              icon: Icons.groups_rounded,
                              title: 'Capacidad estandar',
                              subtitle:
                                  '${experience.standardMaxParticipants} personas',
                            ),
                          if (experience.minParticipants != null)
                            _infoRow(
                              icon: Icons.person_outline_rounded,
                              title: 'Minimo de participantes',
                              subtitle:
                                  '${experience.minParticipants} personas',
                            ),
                          if (experience.baseCapacity != null)
                            _infoRow(
                              icon: Icons.inventory_2_rounded,
                              title: 'Capacidad base',
                              subtitle:
                                  '${experience.baseCapacity}',
                            ),
                          _spacer(),
                        ],

                        // ── Tarifas ──
                        if (experience.pricing != null &&
                            experience.pricing!.tiers.isNotEmpty) ...[
                          _infoRow(
                            icon: Icons.attach_money_rounded,
                            title: 'Moneda',
                            subtitle: experience.pricing!.currency,
                          ),
                          if (experience.pricing!.pricingNotes != null &&
                              experience.pricing!.pricingNotes!.isNotEmpty)
                            _infoRow(
                              icon: Icons.receipt_rounded,
                              title: 'Notas de tarifa',
                              subtitle: experience.pricing!.pricingNotes!,
                            ),
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
                          _spacer(),
                        ],

                        // ── Incluye ──
                        if (experience.inclusions != null &&
                            experience.inclusions!.items.isNotEmpty) ...[
                          _infoRow(
                            icon: Icons.checklist_rounded,
                            title: 'Incluye',
                            subtitle:
                                experience.inclusions!.items.join(', '),
                          ),
                          if (experience.inclusions!.displayText != null &&
                              experience.inclusions!.displayText!.isNotEmpty)
                            _infoRow(
                              icon: Icons.text_fields_rounded,
                              title: 'Texto visible',
                              subtitle: experience.inclusions!.displayText!,
                            ),
                          _spacer(),
                        ],

                        // ── Tags ──
                        if (experience.tags.isNotEmpty)
                          _infoRow(
                            icon: Icons.sell_rounded,
                            title: 'Tags',
                            subtitle: experience.tags.join(', '),
                          ),
                        _spacer(),

                        // ── Acciones admin ──
                        if (_isAdmin) ...[
                          const SizedBox(height: 8),
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
                          if (experience.isActive)
                            AppButton(
                              label: 'Desactivar',
                              icon: Icons.block_rounded,
                              variant: AppButtonVariant.secondary,
                              expanded: true,
                              onPressed: _deactivate,
                            )
                          else
                            AppButton(
                              label: 'Reactivar',
                              icon: Icons.restart_alt_rounded,
                              variant: AppButtonVariant.secondary,
                              expanded: true,
                              onPressed: _activate,
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

  // ── Helpers ──

  Widget _infoRow({
    required IconData icon,
    required String title,
    required String subtitle,
  }) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 6),
      child: AppEntityRowCard(
        title: title,
        subtitle: subtitle,
        leading: Icon(icon, size: 20),
      ),
    );
  }

  Widget _spacer() => const SizedBox(height: 2);

  void _spacerIf(bool condition) {
    // no-op, spacer added inline
  }

  Widget _buildDurationSection(CatalogExperience e) {
    final parts = <String>[];
    if (e.duration != null) {
      parts.add('Actividad ${e.duration!.activityMinutes} min');
      parts.add('Recorrido ${e.duration!.routeMinutes} min');
    }
    if (e.durationHours != null) {
      parts.add('${e.durationHours}h');
    }
    if (e.durationDays != null) {
      parts.add('${e.durationDays} dia(s)');
    }
    if (parts.isEmpty && e.duration?.displayText == null) {
      return const SizedBox.shrink();
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        _infoRow(
          icon: Icons.schedule_rounded,
          title: 'Duraciones',
          subtitle: parts.isNotEmpty ? parts.join(' | ') : '',
        ),
        if (e.duration?.displayText != null &&
            e.duration!.displayText!.isNotEmpty)
          _infoRow(
            icon: Icons.text_fields_rounded,
            title: 'Texto visible',
            subtitle: e.duration!.displayText!,
          ),
      ],
    );
  }

  Widget _buildImageSection(CatalogExperience experience) {
    Widget imageWidget;
    if (experience.imageBase64 != null && experience.imageBase64!.isNotEmpty) {
      try {
        final bytes = base64Decode(experience.imageBase64!);
        imageWidget = Image.memory(
          bytes,
          width: double.infinity,
          fit: BoxFit.cover,
          errorBuilder: (_, _, _) => const SizedBox.shrink(),
        );
      } catch (_) {
        imageWidget = const SizedBox.shrink();
      }
    } else if (experience.imageUrl != null && experience.imageUrl!.isNotEmpty) {
      imageWidget = Image.network(
        experience.imageUrl!,
        width: double.infinity,
        fit: BoxFit.cover,
        errorBuilder: (_, _, _) => const SizedBox.shrink(),
      );
    } else {
      return const SizedBox.shrink();
    }

    return ClipRRect(
      borderRadius: BorderRadius.circular(8),
      child: AspectRatio(
        aspectRatio: 16 / 9,
        child: imageWidget,
      ),
    );
  }

  String _levelLabel(String level) {
    switch (level) {
      case 'basic':
        return 'Basico';
      case 'intermediate':
        return 'Intermedio';
      case 'advanced':
        return 'Avanzado';
      default:
        return level;
    }
  }

  String _difficultyLabel(String difficulty) {
    switch (difficulty) {
      case 'basic':
        return 'Basica';
      case 'intermediate':
        return 'Intermedia';
      case 'advanced':
        return 'Avanzada';
      default:
        return 'Sin dificultad';
    }
  }
}
