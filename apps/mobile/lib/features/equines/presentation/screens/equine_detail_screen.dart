import 'package:flutter/material.dart';
import 'package:material_symbols_icons/material_symbols_icons.dart';

import 'package:mobile_ui/src/theme/app_radii.dart';
import 'package:mobile_ui/src/widgets/app_badge.dart';
import 'package:mobile_ui/src/widgets/app_centered_loader.dart';
import 'package:mobile_ui/src/widgets/app_confirm_dialog.dart';
import 'package:mobile_ui/src/widgets/app_metric_card.dart';
import 'package:mobile_ui/src/widgets/app_scaffold.dart';
import 'package:mobile_ui/src/widgets/app_section_header.dart';
import 'package:mobile_ui/src/widgets/app_status_banner.dart';
import 'package:mobile_ui/src/widgets/app_button.dart';
import 'package:mobile_ui/src/widgets/dashed_border_painter.dart';
import 'package:mobile_ui/src/widgets/refresh_scope.dart';
import 'package:mobile_domain/src/equines/equine_repository.dart';
import 'package:mobile/features/equines/infrastructure/mappers/equine_mapper.dart';
import 'package:mobile/features/equines/presentation/equine_labels.dart';
import 'package:mobile/features/equines/presentation/models/equine_view_models.dart';
import 'package:mobile/features/equines/presentation/widgets/equine_image_provider.dart';

class EquineDetailScreen extends StatefulWidget {
  const EquineDetailScreen({
    super.key,
    required this.equineId,
    required this.repository,
    this.initialDetail,
    this.userRole,
  });

  final String equineId;
  final EquineRepository repository;

  /// Datos precargados del detalle. Si se provee, se evita un request HTTP.
  final EquineDetailRecord? initialDetail;
  final String? userRole;

  bool get canEdit => userRole == 'admin';

  @override
  State<EquineDetailScreen> createState() => _EquineDetailScreenState();
}

class _EquineDetailScreenState extends State<EquineDetailScreen>
    with RefreshableState {
  EquineDetailRecord? _detail;
  bool _isLoading = true;
  bool _isDeleting = false;
  String? _error;

  @override
  Future<void> onRefresh() => _load();

  @override
  void initState() {
    super.initState();
    if (widget.initialDetail != null) {
      _detail = widget.initialDetail;
      _isLoading = false;
    } else {
      _load();
    }
  }

  Future<void> _load() async {
    setState(() {
      _isLoading = true;
      _error = null;
    });
    try {
      final equine = await widget.repository.getEquineById(widget.equineId);
      if (!mounted) return;
      setState(() {
        _detail = EquineMapper.domainToDetailRecord(equine);
        _isLoading = false;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _error = e.toString();
        _isLoading = false;
      });
    }
  }

  bool get _isDeleted => _detail == null ? false : !_detail!.isActive;

  void _confirmDelete() {
    AppConfirmDialog.show(
      context: context,
      icon: Icons.delete_outline_rounded,
      title: 'Eliminar equino',
      message: 'El equino "${_detail?.name}" se desactivará y '
          'quedará oculto de los listados activos.\n\n'
          'Esta acción es reversible.',
      confirmLabel: 'Eliminar',
      style: DialogStyle.danger,
      height: 280,
      onConfirm: () {
        _doDelete();
      },
    );
  }

  Future<void> _doDelete() async {
    setState(() => _isDeleting = true);
    try {
      await widget.repository.deleteEquine(widget.equineId);
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Equino eliminado correctamente')),
      );
      Navigator.of(context).pop(true);
    } catch (e) {
      if (!mounted) return;
      setState(() => _isDeleting = false);
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Error al eliminar: $e')),
      );
    }
  }

  Future<void> _confirmRestore() async {
    setState(() => _isDeleting = true);
    try {
      await widget.repository.restoreEquine(widget.equineId);
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Equino restaurado correctamente')),
      );
      _load();
    } catch (e) {
      if (!mounted) return;
      setState(() => _isDeleting = false);
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Error al restaurar: $e')),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return AppScaffold(
      scrollable: !_isLoading,
      appBar: AppBar(
        title: Text(_detail?.name ?? 'Detalle de equino'),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_rounded),
          onPressed: () => Navigator.of(context).pop(),
        ),
        actions: [
          if (widget.canEdit && !_isDeleted)
            IconButton(
              icon: _isDeleting
                  ? const SizedBox(
                      width: 20,
                      height: 20,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    )
                  : const Icon(Icons.delete_outline_rounded),
              onPressed: _isDeleting ? null : _confirmDelete,
              tooltip: 'Eliminar equino',
            ),
        ],
      ),
      child: _buildBody(),
    );
  }

  Widget _buildBody() {
    if (_isLoading) {
      return const RefreshableViewport(child: AppCenteredLoader());
    }
    if (_error != null) {
      return RefreshableViewport(
        child: AppStatusBanner(
          title: 'Error al cargar',
          message: _error!,
          tone: AppStatusBannerTone.danger,
          onTap: _load,
        ),
      );
    }
    final d = _detail!;
    final scheme = Theme.of(context).colorScheme;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // Deleted banner
        if (_isDeleted)
          Padding(
            padding: const EdgeInsets.only(bottom: 16),
            child: AppStatusBanner(
              title: 'Equino eliminado',
              message: 'Está oculto de los listados activos. Toque para restaurar.',
              tone: AppStatusBannerTone.danger,
              icon: Icons.delete_outline_rounded,
              badgeLabel: 'Eliminado',
              onTap: widget.canEdit ? () => _confirmRestore() : null,
            ),
          ),
        // Foto + info header
        Padding(
          padding: const EdgeInsets.only(bottom: 24),
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              ClipRRect(
                borderRadius: AppRadii.radiusLg,
                child: SizedBox(
                  width: 140,
                  height: 140,
                  child: Stack(
                    children: [
                      Padding(
                        padding: const EdgeInsets.all(3),
                        child: EquineImageProvider(imageBase64: d.imageBase64),
                      ),
                      Positioned(
                        top: 6,
                        right: 6,
                        child: AppBadge(
                          label: d.statusLabel,
                          tone: d.statusTone,
                          uppercase: false,
                        ),
                      ),
                      Positioned.fill(
                        child: IgnorePointer(
                          child: CustomPaint(
                            painter: DashedBorderPainter(
                              color: scheme.outlineVariant,
                            ),
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          d.name,
                          style: Theme.of(context).textTheme.headlineMedium,
                        ),
                        const SizedBox(height: 2),
                        if (d.inventoryNumber != null)
                          Padding(
                            padding: const EdgeInsets.only(bottom: 2),
                            child: Text(
                              '#${d.inventoryNumber}',
                              style: Theme.of(context)
                                  .textTheme
                                  .labelSmall
                                  ?.copyWith(
                                    color: scheme.onSurfaceVariant,
                                    letterSpacing: 1.5,
                                  ),
                            ),
                          ),
                        if (d.species != 'unknown')
                          Padding(
                            padding: const EdgeInsets.only(bottom: 1),
                            child: Text(
                              equineSpeciesLabel(d.species),
                              style:
                                  Theme.of(context).textTheme.bodyMedium,
                            ),
                          ),
                        if (d.breed != null && d.breed!.isNotEmpty)
                          Text(
                            d.breed!,
                            style: Theme.of(context)
                                .textTheme
                                .bodySmall
                                ?.copyWith(
                                    color: scheme.onSurfaceVariant),
                          ),
                      ],
                    ),
                  ],
                ),
              ),
              ],
            ),
          ),
        // Métricas
        _buildMetricsSection(d),
        const SizedBox(height: 16),
        // Ficha técnica
        _buildSection('Ficha técnica', [
          _row('Especie', equineSpeciesLabel(d.species), icon: Symbols.pets_rounded),
          _row('Raza', d.breed, icon: Symbols.category_rounded),
          _row('Sexo', equineSexLabel(d.sex), icon: Symbols.wc_rounded),
          _row('Color', d.coatColor, icon: Symbols.palette_rounded),
          _row('Paso', d.gait, icon: Symbols.directions_walk_rounded),
          _row('Ubicación', equineLocationLabel(d.locationStatus), icon: Symbols.location_on_rounded),
          if (d.locationNotes != null)
            _row('Notas ubicación', d.locationNotes, icon: Symbols.notes_rounded),
        ]),
        const SizedBox(height: 12),
        // Identificación
        _buildSection('Identificación', [
          if (d.registryNumber != null)
            _row('# Registro', d.registryNumber, icon: Symbols.tag_rounded),
          if (d.microchip != null) _row('Microchip', d.microchip, icon: Symbols.memory_rounded),
        ]),
        const SizedBox(height: 12),
        // Nacimiento
        _buildSection('Nacimiento', [
          if (d.approximateBirthDate != null)
            _row('Fecha', d.approximateBirthDate!, icon: Symbols.calendar_month_rounded),
          if (d.birthDateRaw != null) _row('Texto original', d.birthDateRaw, icon: Symbols.description_rounded),
          if (d.approximateAgeYears != null)
            _row('Edad aprox.', '${d.approximateAgeYears} años', icon: Symbols.schedule_rounded),
          if (d.birthPlace != null) _row('Lugar', d.birthPlace, icon: Symbols.place_rounded),
        ]),
        const SizedBox(height: 12),
        // Genealogía
        _buildSection('Genealogía', [
          if (d.sireName != null) _row('Padre', d.sireName!, icon: Symbols.male_rounded),
          if (d.damName != null) _row('Madre', d.damName!, icon: Symbols.female_rounded),
        ]),
        const SizedBox(height: 12),
        // Medidas
        _buildSection('Medidas', [
          if (d.weightKg != null)
            _row('Peso', '${d.weightKg!.toStringAsFixed(0)} kg', icon: Symbols.scale_rounded),
          if (d.heightM != null)
            _row('Alzada', '${d.heightM!.toStringAsFixed(2)} m', icon: Symbols.height_rounded),
          if (d.maxRiderWeightKg != null)
            _row('Carga jinete', '${d.maxRiderWeightKg!.toStringAsFixed(0)} kg', icon: Symbols.fitness_center_rounded),
          if (d.lastWeightAt != null) _row('Último peso', d.lastWeightAt!, icon: Symbols.scale_rounded),
          if (d.lastHeightAt != null) _row('Última alzada', d.lastHeightAt!, icon: Symbols.height_rounded),
        ]),
        const SizedBox(height: 12),
        // Operación
        _buildSection('Operación', [
          _row('Estado', d.statusLabel, icon: Symbols.radio_button_checked_rounded),
          _row('Disponible', d.isAvailable ? 'Sí' : 'No', icon: Symbols.check_circle_rounded),
          _row('Activo', d.isActive ? 'Sí' : 'No', icon: Symbols.offline_bolt_rounded),
          if (d.experienceFit != null)
            _row('Experiencia', equineExperienceLabel(d.experienceFit), icon: Symbols.stars_rounded),
          if (d.workloadLast7Days > 0)
            _row('Carga semanal', '${d.workloadLast7Days} servicios', icon: Symbols.date_range_rounded),
          if (d.lastServiceAt != null)
            _row('Último servicio', _formatDate(d.lastServiceAt!), icon: Symbols.history_rounded),
        ]),
        if (d.availabilityReasons != null &&
            d.availabilityReasons!.isNotEmpty) ...[
          const SizedBox(height: 12),
          AppStatusBanner(
            title: 'Motivo',
            message: normalizeReason(d.availabilityReasons!),
            tone: _bannerToneFromBadge(d.statusTone),
          ),
        ],
        if (widget.canEdit) ...[
          const SizedBox(height: 24),
          const Divider(),
          const SizedBox(height: 12),
          if (_isDeleted)
            AppButton(
              label: _isDeleting ? 'Restaurando...' : 'Restaurar equino',
              icon: Icons.restore_from_trash_rounded,
              variant: AppButtonVariant.secondary,
              expanded: true,
              onPressed: _isDeleting ? null : _confirmRestore,
            )
          else
            AppButton(
              label: _isDeleting ? 'Eliminando...' : 'Eliminar equino',
              icon: Icons.delete_outline_rounded,
              variant: AppButtonVariant.danger,
              expanded: true,
              onPressed: _isDeleting ? null : _confirmDelete,
            ),
        ],
      ],
    );
  }

  Widget _buildMetricsSection(EquineDetailRecord d) {
    final metricPanels = <Widget>[];
    if (d.approximateAgeYears != null) {
      metricPanels.add(
        AppMetricCard(
          title: 'Edad',
          value: '${d.approximateAgeYears}',
          supportingText: d.birthDateIsApproximate ? 'aproximada' : null,
        ),
      );
    }
    if (d.weightKg != null) {
      metricPanels.add(
        AppMetricCard(
          title: 'Peso',
          value: '${d.weightKg!.toStringAsFixed(0)} kg',
          icon: Symbols.weight_rounded,
          iconSize: 56,
        ),
      );
    }
    if (d.maxRiderWeightKg != null) {
      metricPanels.add(
        AppMetricCard(
          title: 'Carga máx.',
          value: '${d.maxRiderWeightKg!.toStringAsFixed(0)} kg',
          supportingText: 'jinete',
        ),
      );
    }
    if (metricPanels.isEmpty) return const SizedBox.shrink();
    return Row(
      children: [
        for (int i = 0; i < metricPanels.length; i++)
          Expanded(
            child: Padding(
              padding: EdgeInsets.only(
                left: i == 0 ? 0 : 8,
                right: i == metricPanels.length - 1 ? 0 : 8,
              ),
              child: metricPanels[i],
            ),
          ),
      ],
    );
  }

  Widget _buildSection(String title, List<Widget> rows) {
    final nonNullRows = rows.where((w) {
      final text = w.toString();
      return !text.contains('null') && !text.contains('· ');
    }).toList();
    if (nonNullRows.isEmpty) return const SizedBox.shrink();
    final scheme = Theme.of(context).colorScheme;
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: scheme.surfaceContainerHighest,
        borderRadius: AppRadii.radiusLg,
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          AppSectionHeader(title: title, variant: AppSectionHeaderVariant.compact),
          const SizedBox(height: 8),
          ...nonNullRows,
        ],
      ),
    );
  }

  Widget _row(String label, String? value, {required IconData icon}) {
    if (value == null || value.isEmpty) return const SizedBox.shrink();
    final scheme = Theme.of(context).colorScheme;
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 3),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(icon, size: 16, color: scheme.onSurfaceVariant),
          const SizedBox(width: 8),
          SizedBox(
            width: 100,
            child: Text(
              label,
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                    color: scheme.onSurfaceVariant,
                  ),
            ),
          ),
          const SizedBox(width: 8),
          Expanded(
            child: Text(value, style: Theme.of(context).textTheme.bodyMedium),
          ),
        ],
      ),
    );
  }

  AppStatusBannerTone _bannerToneFromBadge(AppBadgeTone tone) {
    switch (tone) {
      case AppBadgeTone.success:
        return AppStatusBannerTone.success;
      case AppBadgeTone.warning:
        return AppStatusBannerTone.warning;
      case AppBadgeTone.danger:
        return AppStatusBannerTone.danger;
      default:
        return AppStatusBannerTone.info;
    }
  }

  String _formatDate(DateTime dt) {
    return '${dt.day.toString().padLeft(2, "0")}/${dt.month.toString().padLeft(2, "0")}/${dt.year}';
  }
}
