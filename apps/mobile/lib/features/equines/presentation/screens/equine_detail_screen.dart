import 'package:flutter/material.dart';

import '../../../../app/theme/app_radii.dart';
import '../../../../app/widgets/app_badge.dart';
import '../../../../app/widgets/app_centered_loader.dart';
import '../../../../app/widgets/app_metric_card.dart';
import '../../../../app/widgets/app_scaffold.dart';
import '../../../../app/widgets/app_section_header.dart';
import '../../../../app/widgets/app_status_banner.dart';
import '../../domain/repositories/equine_repository.dart';
import '../../infrastructure/mappers/equine_mapper.dart';
import '../equine_labels.dart';
import '../models/equine_view_models.dart';
import '../widgets/equine_image_provider.dart';

class EquineDetailScreen extends StatefulWidget {
  const EquineDetailScreen({
    super.key,
    required this.equineId,
    required this.repository,
  });

  final String equineId;
  final EquineRepository repository;

  @override
  State<EquineDetailScreen> createState() => _EquineDetailScreenState();
}

class _EquineDetailScreenState extends State<EquineDetailScreen> {
  EquineDetailRecord? _detail;
  bool _isLoading = true;
  String? _error;

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

  @override
  Widget build(BuildContext context) {
    return AppScaffold(
      scrollable: true,
      appBar: AppBar(
        title: Text(_detail?.name ?? 'Detalle de equino'),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_rounded),
          onPressed: () => Navigator.of(context).pop(),
        ),
      ),
      child: _buildBody(),
    );
  }

  Widget _buildBody() {
    if (_isLoading) {
      return const AppCenteredLoader();
    }
    if (_error != null) {
      return AppStatusBanner(
        title: 'Error al cargar',
        message: _error!,
        tone: AppStatusBannerTone.danger,
        onTap: _load,
      );
    }
    final d = _detail!;
    final scheme = Theme.of(context).colorScheme;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // Encabezado
        Padding(
          padding: const EdgeInsets.only(bottom: 16),
          child: Row(
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      d.name,
                      style: Theme.of(context).textTheme.headlineSmall,
                    ),
                    const SizedBox(height: 4),
                    Text(
                      [
                        if (d.inventoryNumber != null)
                          '#${d.inventoryNumber}',
                        if (d.species != 'unknown')
                          equineSpeciesLabel(d.species),
                        if (d.breed != null) d.breed!,
                      ].where((e) => e.isNotEmpty).join(' · '),
                      style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                            color: scheme.onSurfaceVariant,
                          ),
                    ),
                  ],
                ),
              ),
              AppBadge(
                label: d.statusLabel,
                tone: d.statusTone,
                uppercase: false,
              ),
            ],
          ),
        ),
        // Imagen del equino
        if (d.imageBase64 != null && d.imageBase64!.isNotEmpty)
          Padding(
            padding: const EdgeInsets.only(bottom: 16),
            child: ClipRRect(
              borderRadius: AppRadii.radiusLg,
              child: EquineImageProvider(
                imageBase64: d.imageBase64,
                height: 200,
              ),
            ),
          ),
        // Métricas
        _buildMetricsSection(d),
        const SizedBox(height: 16),
        // Ficha técnica
        _buildSection('Ficha técnica', [
          _row('Especie', equineSpeciesLabel(d.species)),
          _row('Raza', d.breed),
          _row('Sexo', equineSexLabel(d.sex)),
          _row('Color', d.coatColor),
          _row('Paso', d.gait),
          _row('Ubicación', equineLocationLabel(d.locationStatus)),
          if (d.locationNotes != null) _row('Notas ubicación', d.locationNotes),
        ]),
        const SizedBox(height: 12),
        // Identificación
        _buildSection('Identificación', [
          if (d.registryNumber != null)
            _row('# Registro', d.registryNumber),
          if (d.microchip != null) _row('Microchip', d.microchip),
        ]),
        const SizedBox(height: 12),
        // Nacimiento
        _buildSection('Nacimiento', [
          if (d.approximateBirthDate != null)
            _row('Fecha', d.approximateBirthDate!),
          if (d.birthDateRaw != null) _row('Texto original', d.birthDateRaw),
          if (d.approximateAgeYears != null)
            _row('Edad aprox.', '${d.approximateAgeYears} años'),
          if (d.birthPlace != null) _row('Lugar', d.birthPlace),
        ]),
        const SizedBox(height: 12),
        // Genealogía
        _buildSection('Genealogía', [
          if (d.sireName != null) _row('Padre', d.sireName!),
          if (d.damName != null) _row('Madre', d.damName!),
        ]),
        const SizedBox(height: 12),
        // Medidas
        _buildSection('Medidas', [
          if (d.weightKg != null) _row('Peso', '${d.weightKg!.toStringAsFixed(0)} kg'),
          if (d.heightM != null) _row('Alzada', '${d.heightM!.toStringAsFixed(2)} m'),
          if (d.maxRiderWeightKg != null)
            _row('Carga jinete', '${d.maxRiderWeightKg!.toStringAsFixed(0)} kg'),
          if (d.lastWeightAt != null) _row('Último peso', d.lastWeightAt!),
          if (d.lastHeightAt != null) _row('Última alzada', d.lastHeightAt!),
        ]),
        const SizedBox(height: 12),
        // Operación
        _buildSection('Operación', [
          _row('Estado', d.statusLabel),
          _row('Disponible', d.isAvailable ? 'Sí' : 'No'),
          _row('Activo', d.isActive ? 'Sí' : 'No'),
          if (d.experienceFit != null)
            _row('Experiencia', equineExperienceLabel(d.experienceFit)),
          if (d.workloadLast7Days > 0)
            _row('Carga semanal', '${d.workloadLast7Days} servicios'),
          if (d.lastServiceAt != null)
            _row('Último servicio', _formatDate(d.lastServiceAt!)),
        ]),
        if (d.availabilityReasons != null &&
            d.availabilityReasons!.isNotEmpty) ...[
          const SizedBox(height: 12),
          AppStatusBanner(
            title: 'Motivo',
            message: d.availabilityReasons!,
            tone: _bannerToneFromBadge(d.statusTone),
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

  Widget _row(String label, String? value) {
    if (value == null || value.isEmpty) return const SizedBox.shrink();
    final scheme = Theme.of(context).colorScheme;
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 3),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 120,
            child: Text(
              label,
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                    color: scheme.onSurfaceVariant,
                  ),
            ),
          ),
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
