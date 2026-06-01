import 'dart:convert';
import 'dart:typed_data';

import 'package:flutter/material.dart';
import 'package:material_symbols_icons/material_symbols_icons.dart';

import '../../../../app/widgets/app_badge.dart';
import '../../../../app/widgets/app_button.dart';
import '../../../../app/widgets/app_centered_loader.dart';
import '../../../../app/widgets/app_entity_row_card.dart';
import '../../../../app/widgets/app_section_header.dart';
import '../../../../app/widgets/app_status_banner.dart';
import '../../../../app/widgets/cards/app_image_feature_card.dart';
import '../../../../app/widgets/cards/app_logbook_timeline.dart';
import '../../domain/repositories/equine_repository.dart';
import '../controllers/equines_controller.dart';
import '../widgets/app_equine_profile_card.dart';
import '../widgets/equine_form_sheet.dart';
import 'equine_detail_screen.dart';
import 'equine_timeline_screen.dart';
import '../../../shared/presentation/widgets/module_subroute_header.dart';

class EquinesModuleScreen extends StatefulWidget {
  const EquinesModuleScreen({
    super.key,
    required this.repository,
  });

  final EquineRepository repository;

  @override
  State<EquinesModuleScreen> createState() => _EquinesModuleScreenState();
}

class _EquinesModuleScreenState extends State<EquinesModuleScreen> {
  late final EquinesController _controller;

  @override
  void initState() {
    super.initState();
    _controller = EquinesController(repository: widget.repository);
    _controller.addListener(_onChanged);
    _controller.loadEquines();
  }

  void _onChanged() {
    if (mounted) setState(() {});
  }

  @override
  void dispose() {
    _controller.removeListener(_onChanged);
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(24, 24, 24, 24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          ModuleSubrouteHeader(
            eyebrow: 'Equinos',
            title: 'Gestión de equinos',
            subtitle: 'Disponibilidad, historial y cuidado operativo',
            subrouteLabels: const [
              'Resumen',
              'Historial',
              'Disponibilidad',
              'Cuidado',
            ],
            currentSubrouteIndex: _controller.subroute.index,
            onSubrouteTap: (i) {
              _controller.selectSubrouteByIndex(i);
            },
          ),
          const SizedBox(height: 20),
          _buildSubrouteContent(),
        ],
      ),
    );
  }

  Widget _buildSubrouteContent() {
    switch (_controller.loadState) {
      case EquinesLoadState.idle:
      case EquinesLoadState.loading:
        return _buildLoading();
      case EquinesLoadState.error:
        return _buildError();
      case EquinesLoadState.empty:
        return _buildEmpty();
      case EquinesLoadState.success:
        if (_controller.subroute == EquinesSubroute.historial) {
          return _buildTimelineSection();
        }
        return _buildSuccessContent();
    }
  }

  Widget _buildLoading() {
    return ListView.builder(
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      itemCount: 5,
      itemBuilder: (_, __) => Padding(
        padding: const EdgeInsets.only(bottom: 10),
        child: AppEntityRowCard(
          title: 'Cargando...',
          subtitle: '···',
          badge: AppBadge(
            label: '···',
            tone: AppBadgeTone.neutral,
            uppercase: false,
          ),
        ),
      ),
    );
  }

  Widget _buildError() {
    return Center(
      child: AppStatusBanner(
        title: 'Error al cargar equinos',
        message: _controller.errorMessage,
        tone: AppStatusBannerTone.danger,
        onTap: _controller.loadEquines,
      ),
    );
  }

  Widget _buildEmpty() {
    return Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(
                Symbols.chess_knight,
                size: 56,
            color: Theme.of(context).colorScheme.onSurfaceVariant,
          ),
          const SizedBox(height: 16),
          Text(
            'No hay equinos sincronizados',
            style: Theme.of(context).textTheme.titleMedium?.copyWith(
                  color: Theme.of(context).colorScheme.onSurfaceVariant,
                ),
          ),
          const SizedBox(height: 8),
          Text(
            'Conectate al backend o verifica la conexion',
            style: Theme.of(context).textTheme.bodySmall?.copyWith(
                  color: Theme.of(context).colorScheme.onSurfaceVariant,
                ),
          ),
          const SizedBox(height: 24),
          FilledButton.icon(
            onPressed: _controller.loadEquines,
            icon: const Icon(Icons.refresh_rounded),
            label: const Text('Reintentar'),
          ),
        ],
      ),
    );
  }

  Widget _buildSuccessContent() {
    final records = _controller.records;
    if (records.isEmpty) {
      return _buildEmptyMessage();
    }

    return Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Botón Registrar equino
          AppButton(
            label: 'Registrar equino',
            icon: Icons.add,
            expanded: true,
            onPressed: () async {
              final result = await showModalBottomSheet<Map<String, dynamic>>(
                context: context,
                isScrollControlled: true,
                backgroundColor: Theme.of(context).colorScheme.surface,
                builder: (_) => const EquineFormSheet(),
              );
              if (result != null && mounted) {
                final success = await _controller.createEquine(result);
                if (success && mounted) {
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(content: Text('Equino creado correctamente')),
                  );
                }
              }
            },
          ),
          const SizedBox(height: 16),

          // Carrusel horizontal de equinos
          SizedBox(
            height: 260,
            child: ListView.separated(
              scrollDirection: Axis.horizontal,
              itemCount: records.length,
              separatorBuilder: (_, __) => const SizedBox(width: 12),
              itemBuilder: (context, i) {
                final e = records[i];
                final isSelected = e.id == _controller.selectedEquineId;
                return AppImageFeatureCard(
                  title: e.name,
                  subtitle: e.subtitle ?? e.summary,
                  image: _equineImage(e.imageBase64),
                  badge: AppBadge(
                    label: e.statusLabel,
                    tone: e.statusTone,
                    uppercase: false,
                  ),
                  selected: isSelected,
                  onTap: () => _controller.selectEquine(e.id),
                );
              },
            ),
          ),
          const SizedBox(height: 12),

          // Acciones: Ver info · Editar
          Row(
            children: [
              Expanded(
                child: AppButton(
                  label: 'Ver info',
                  icon: Icons.info_outline_rounded,
                  variant: AppButtonVariant.secondary,
                  onPressed: _controller.selectedEquineId != null
                      ? () {
                          Navigator.of(context).push(
                            MaterialPageRoute<void>(
                              builder: (_) => EquineDetailScreen(
                                equineId: _controller.selectedEquineId!,
                                repository: widget.repository,
                              ),
                            ),
                          );
                        }
                      : null,
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: AppButton(
                  label: 'Editar',
                  icon: Icons.edit_rounded,
                  onPressed: _controller.selectedEquineId != null
                      ? () async {
                          final detail = _controller.selectedDetail;
                          final result = await showModalBottomSheet<Map<String, dynamic>>(
                            context: context,
                            isScrollControlled: true,
                            backgroundColor: Theme.of(context).colorScheme.surface,
                            builder: (_) => EquineFormSheet(existing: detail),
                          );
                          if (result != null && mounted) {
                            final success = await _controller.updateEquine(
                              _controller.selectedEquineId!,
                              result,
                            );
                            if (success && mounted) {
                              ScaffoldMessenger.of(context).showSnackBar(
                                const SnackBar(content: Text('Equino actualizado correctamente')),
                              );
                            }
                          }
                        }
                      : null,
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),

          // Ficha del equino seleccionado
          _buildSelectedEquineSection(),
          const SizedBox(height: 16),

          // Timeline
          _buildTimelineSection(),
          const SizedBox(height: 32),
        ],
    );
  }

  Widget _buildSelectedEquineSection() {
    final detail = _controller.selectedDetail;
    final state = _controller.detailLoadState;

    debugPrint('EquineDetailSection: state=$state detail=${detail?.id}');

    if (state == EquinesLoadState.loading) {
      return const AppCenteredLoader();
    }
    if (state == EquinesLoadState.error) {
      return Padding(
        padding: const EdgeInsets.only(top: 8),
        child: AppStatusBanner(
          title: 'Error al cargar detalle',
          message: _controller.detailErrorMessage,
          tone: AppStatusBannerTone.danger,
        ),
      );
    }
    if (detail == null) {
      return const SizedBox.shrink();
    }
    return AppEquineProfileCard(detail: detail);
  }

  Widget _buildEmptyMessage() {
    return Center(
      child: Text(
        _emptyMessage(),
        style: Theme.of(context).textTheme.bodyMedium?.copyWith(
              color: Theme.of(context).colorScheme.onSurfaceVariant,
            ),
      ),
    );
  }

  ImageProvider _equineImage(String? base64) {
    if (base64 == null || base64.isEmpty) {
      return MemoryImage(Uint8List(0));
    }
    try {
      return MemoryImage(base64Decode(base64));
    } catch (_) {
      return MemoryImage(Uint8List(0));
    }
  }

  /// Sección de historial reciente para la subruta "Historial".
  /// Muestra entradas mock del timeline + botón para ver el completo.
  Widget _buildTimelineSection() {
    final records = _controller.records;
    if (records.isEmpty) {
      return Center(
        child: Text(
          'Sin historial disponible',
          style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                color: Theme.of(context).colorScheme.onSurfaceVariant,
              ),
        ),
      );
    }

    final firstRecord = records.first;
    final mockEntries = [
      AppLogbookTimelineEntry(
        title: 'Servicio de monta',
        dateLabel: '15/03/2026',
        reservationLabel: 'RES-001',
        guideLabel: 'Carlos',
        durationLabel: '2h',
        state: AppLogbookEntryState.completed,
      ),
      AppLogbookTimelineEntry(
        title: 'Control veterinario',
        dateLabel: '10/03/2026',
        reservationLabel: 'VET-023',
        guideLabel: 'Dra. Martínez',
        durationLabel: '45min',
        state: AppLogbookEntryState.completed,
      ),
      AppLogbookTimelineEntry(
        title: 'Servicio de cabalgata',
        dateLabel: '08/03/2026',
        reservationLabel: 'RES-089',
        guideLabel: 'María',
        durationLabel: '3h',
        state: AppLogbookEntryState.completed,
      ),
    ];

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        AppSectionHeader(
          title: 'Historial reciente',
          variant: AppSectionHeaderVariant.compact,
        ),
        const SizedBox(height: 16),
        AppLogbookTimeline(entries: mockEntries),
        const SizedBox(height: 20),
        AppButton(
          label: 'Ver timeline completo',
          icon: Icons.history_rounded,
          variant: AppButtonVariant.secondary,
          expanded: true,
          onPressed: () {
            final id = _controller.selectedEquineId ?? firstRecord.id;
            final record =
                records.firstWhere((r) => r.id == id, orElse: () => firstRecord);
            Navigator.of(context).push(
              MaterialPageRoute(
                builder: (_) => EquineTimelineScreen(
                  equineId: record.id,
                  equineName: record.name,
                ),
              ),
            );
          },
        ),
      ],
    );
  }

  String _emptyMessage() {
    switch (_controller.subroute) {
      case EquinesSubroute.resumen:
        return 'No hay equinos registrados';
      case EquinesSubroute.historial:
        return 'Sin historial disponible';
      case EquinesSubroute.disponibilidad:
        return 'No hay equinos disponibles';
      case EquinesSubroute.cuidado:
        return 'No hay equinos en cuidado';
    }
  }
}
