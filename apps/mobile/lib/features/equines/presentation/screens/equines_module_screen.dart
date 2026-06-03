import 'dart:convert';
import 'dart:typed_data';

import 'package:flutter/material.dart';
import 'package:material_symbols_icons/material_symbols_icons.dart';

import 'package:mobile_ui/src/widgets/app_badge.dart';
import 'package:mobile_ui/src/widgets/app_button.dart';
import 'package:mobile_ui/src/widgets/app_centered_loader.dart';
import 'package:mobile_ui/src/widgets/app_entity_row_card.dart';
import 'package:mobile_ui/src/widgets/app_metric_card.dart';
import 'package:mobile_ui/src/widgets/app_section_header.dart';
import 'package:mobile_ui/src/widgets/app_segmented_filter.dart';
import 'package:mobile_ui/src/widgets/app_status_banner.dart';
import 'package:mobile_ui/src/widgets/cards/app_image_feature_card.dart';
import 'package:mobile_ui/src/widgets/cards/app_logbook_timeline.dart';
import 'package:mobile_ui/src/widgets/refresh_scope.dart';
import 'package:mobile_domain/src/equines/equine_timeline_entry.dart';
import 'package:mobile_domain/src/equines/equine_repository.dart';
import 'package:mobile/features/equines/infrastructure/mappers/equine_mapper.dart';
import 'package:mobile/features/equines/presentation/controllers/equines_controller.dart';
import 'package:mobile/features/equines/presentation/models/equine_view_models.dart';
import 'package:mobile/features/equines/presentation/widgets/app_equine_profile_card.dart';
import 'package:mobile/features/equines/presentation/widgets/equine_form_sheet.dart';
import 'equine_detail_screen.dart';
import 'equine_timeline_screen.dart';

class EquinesModuleScreen extends StatefulWidget {
  const EquinesModuleScreen({
    super.key,
    required this.repository,
    this.userRole,
  });

  final EquineRepository repository;
  final String? userRole;

  bool get canEdit => userRole == 'admin';

  @override
  State<EquinesModuleScreen> createState() => _EquinesModuleScreenState();
}

enum _ViewMode { grid, list }

class _EquinesModuleScreenState extends State<EquinesModuleScreen>
    with RefreshableState {
  late final EquinesController _controller;

  _ViewMode _viewMode = _ViewMode.grid;
  late final TextEditingController _searchController;
  String _searchQuery = '';

  List<EquineRecord> get _filteredRecords {
    final q = _searchQuery;
    if (q.isEmpty) return _controller.records;
    final lower = q.toLowerCase();
    return _controller.records.where((r) {
      return r.name.toLowerCase().contains(lower) ||
          (r.inventoryNumber?.toString() ?? '').contains(lower) ||
          (r.subtitle?.toLowerCase() ?? '').contains(lower);
    }).toList();
  }

  @override
  Future<void> onRefresh() => _controller.loadEquines();

  @override
  void initState() {
    super.initState();
    _searchController = TextEditingController();
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
    _searchController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(24, 24, 24, 24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          AppSectionHeader(
            eyebrow: 'GESTIÓN',
            title: 'EQUINOS',
            variant: AppSectionHeaderVariant.hero,
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
        return const Expanded(
          child: AppCenteredLoader(),
        );
      case EquinesLoadState.error:
        return _buildError();
      case EquinesLoadState.empty:
        return _buildEmpty();
      case EquinesLoadState.success:
        return _buildSuccessContent();
    }
  }

  Widget _buildError() {
    return Center(
      child: Padding(
        padding: const EdgeInsets.symmetric(vertical: 80),
        child: AppStatusBanner(
          title: 'Error al cargar equinos',
          message: _controller.errorMessage,
          tone: AppStatusBannerTone.danger,
          onTap: _controller.loadEquines,
        ),
      ),
    );
  }

  Widget _buildEmpty() {
    return Center(
      child: Padding(
        padding: const EdgeInsets.symmetric(vertical: 80),
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
      ),
    );
  }

  Widget _buildSearchRow() {
    return Row(
      children: [
        Expanded(
          child: TextField(
            controller: _searchController,
            onChanged: (v) => setState(() => _searchQuery = v),
            decoration: InputDecoration(
              hintText: 'Buscar equino…',
              prefixIcon: Icon(Symbols.search_rounded, size: 20),
              suffixIcon: _searchQuery.isNotEmpty
                  ? IconButton(
                      icon: Icon(Symbols.close_rounded, size: 18),
                      onPressed: () {
                        _searchController.clear();
                        setState(() => _searchQuery = '');
                      },
                    )
                  : null,
              isDense: true,
              filled: true,
              fillColor: Theme.of(context).colorScheme.surfaceContainerLow,
              border: OutlineInputBorder(
                borderRadius: BorderRadius.circular(8),
                borderSide: BorderSide(
                  color: Theme.of(context).colorScheme.outlineVariant,
                ),
              ),
              contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
            ),
          ),
        ),
        const SizedBox(width: 8),
        Material(
          color: Theme.of(context).colorScheme.surfaceContainerLow,
          borderRadius: BorderRadius.circular(8),
          child: InkWell(
            borderRadius: BorderRadius.circular(8),
            onTap: () => setState(() {
              _viewMode = _viewMode == _ViewMode.grid
                  ? _ViewMode.list
                  : _ViewMode.grid;
            }),
            child: Padding(
              padding: const EdgeInsets.all(10),
              child: Icon(
                _viewMode == _ViewMode.grid
                    ? Symbols.grid_view_rounded
                    : Symbols.format_list_bulleted_rounded,
                size: 22,
                color: Theme.of(context).colorScheme.onSurfaceVariant,
              ),
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildRegisterButton() {
    if (!widget.canEdit) return const SizedBox.shrink();
    return AppButton(
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
    );
  }

  Widget _buildSuccessContent() {
    final records = _controller.records;
    final hasEquines = _controller.hasAnyRecords;
    final filteredEmpty = records.isEmpty;

    // ── Empty filter: llenar viewport + centrar mensaje ────────────
    if (filteredEmpty && hasEquines) {
      final vh = (Scrollable.maybeOf(context)?.position.viewportDimension)
          ?? MediaQuery.of(context).size.height;
      return SizedBox(
        height: vh,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _buildMetricsRow(),
            const SizedBox(height: 8),
            _buildStatusFilter(),
            const SizedBox(height: 12),
            _buildSearchRow(),
            const SizedBox(height: 12),
            _buildRegisterButton(),
            const SizedBox(height: 16),
            Expanded(
              child: Center(
                child: _buildEmptyFilterMessage(),
              ),
            ),
          ],
        ),
      );
    }

    // ── Con contenido (grid o lista) ────────────────────────────────
    return Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          if (hasEquines) _buildMetricsRow(),
          if (hasEquines) const SizedBox(height: 8),

          // ── Status filter ────────────────────────────────────────────
          _buildStatusFilter(),
          const SizedBox(height: 12),

          // ── Search + view toggle ─────────────────────────────────────
          _buildSearchRow(),
          const SizedBox(height: 12),

          // ── Botón Registrar equino ────────────────────────────────────
          _buildRegisterButton(),
          const SizedBox(height: 16),

          if (!filteredEmpty) ...[
            if (_viewMode == _ViewMode.grid) ...[
              // ── Carrusel horizontal de equinos ──────────────────────
              // Altura = image (240w × aspectRatio 1.0) + texto (~66) + tolerance
              SizedBox(
                height: 310,
                child: ListView.separated(
                  scrollDirection: Axis.horizontal,
                  itemCount: _filteredRecords.length,
                  separatorBuilder: (_, __) => const SizedBox(width: 12),
                  itemBuilder: (context, i) {
                    final e = _filteredRecords[i];
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
                      imageAspectRatio: 1.0,
                    );
                  },
                ),
              ),
              const SizedBox(height: 12),

              // ── Acciones: Ver info · Editar ─────────────────────────
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
                                    initialDetail: _controller.selectedDetail,
                                    userRole: widget.userRole,
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
                      onPressed: _controller.selectedEquineId != null && widget.canEdit
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

              // ── Ficha del equino seleccionado ───────────────────────
              _buildSelectedEquineSection(),
              const SizedBox(height: 16),

              // ── Timeline ────────────────────────────────────────────
              _buildTimelineSection(),
              const SizedBox(height: 32),
            ] else ...[
              // ── Vista lista ─────────────────────────────────────────
              _buildListView(),
            ],
          ],

        ],
    );
  }

  void _showEquineActions(BuildContext context, EquineRecord equine) {
    final scheme = Theme.of(context).colorScheme;
    showModalBottomSheet(
      context: context,
      backgroundColor: scheme.surface,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(12)),
      ),
      builder: (ctx) {
        return Padding(
          padding: const EdgeInsets.fromLTRB(24, 20, 24, 24),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Container(
                width: 40,
                height: 4,
                decoration: BoxDecoration(
                  color: scheme.onSurfaceVariant.withValues(alpha: 0.3),
                  borderRadius: BorderRadius.circular(2),
                ),
              ),
              const SizedBox(height: 16),
              Text(
                equine.name,
                style: Theme.of(context).textTheme.titleLarge?.copyWith(
                  fontWeight: FontWeight.w800,
                ),
              ),
              const SizedBox(height: 4),
              Text(
                equine.summary,
                style: Theme.of(context).textTheme.bodySmall?.copyWith(
                  color: scheme.onSurfaceVariant,
                ),
              ),
              const SizedBox(height: 24),
              SizedBox(
                width: double.infinity,
                child: AppButton(
                  label: 'Ver detalles',
                  icon: Icons.info_outline_rounded,
                  onPressed: () {
                    Navigator.of(ctx).pop();
                    Navigator.of(context).push(
                      MaterialPageRoute<void>(
                        builder: (_) => EquineDetailScreen(
                          equineId: equine.id,
                          repository: widget.repository,
                          userRole: widget.userRole,
                        ),
                      ),
                    );
                  },
                ),
              ),
              if (widget.canEdit) ...[
                const SizedBox(height: 10),
                SizedBox(
                  width: double.infinity,
                  child: AppButton(
                    label: 'Editar',
                    icon: Symbols.edit_rounded,
                    variant: AppButtonVariant.secondary,
                    onPressed: () {
                      final messenger = ScaffoldMessenger.of(context);
                      Navigator.of(ctx).pop();
                      _controller.selectEquine(equine.id);
                      final detail = _controller.selectedDetail;
                      if (detail == null) return;
                      showModalBottomSheet<Map<String, dynamic>>(
                        context: context,
                        isScrollControlled: true,
                        backgroundColor: scheme.surface,
                        builder: (_) => EquineFormSheet(existing: detail),
                      ).then((result) async {
                        if (result != null && mounted) {
                          final success = await _controller.updateEquine(equine.id, result);
                          if (success && mounted) {
                            messenger.showSnackBar(
                              const SnackBar(content: Text('Equino actualizado correctamente')),
                            );
                          }
                        }
                      });
                    },
                  ),
                ),
              ],
              const SizedBox(height: 10),
              SizedBox(
                width: double.infinity,
                child: AppButton(
                  label: 'Cerrar',
                  icon: Symbols.close_rounded,
                  variant: AppButtonVariant.secondary,
                  onPressed: () => Navigator.of(ctx).pop(),
                ),
              ),
            ],
          ),
        );
      },
    );
  }

  Widget _buildMetricsRow() {
    final m = _controller.metrics;
    if (m.total == 0) return const SizedBox.shrink();
    return Row(
      children: [
        Expanded(
          child: AppMetricCard(
            title: 'Disponibles',
            value: m.available.toString(),
            compact: true,
            tone: m.available > 0
                ? AppMetricCardTone.defaultTone
                : AppMetricCardTone.danger,
          ),
        ),
        const SizedBox(width: 8),
        Expanded(
          child: AppMetricCard(
            title: 'Bloqueados',
            value: m.blocked.toString(),
            compact: true,
            tone: m.blocked > 0
                ? AppMetricCardTone.danger
                : AppMetricCardTone.defaultTone,
          ),
        ),
      ],
    );
  }

  Widget _buildStatusFilter() {
    // Construir opciones base: TODOS + estados operativos + ELIMINADOS.
    final items = <AppSegmentedFilterItem<String?>>[
      const AppSegmentedFilterItem(label: 'TODOS', value: null),
      const AppSegmentedFilterItem(
        label: 'DISPONIBLES',
        value: 'available',
      ),
      const AppSegmentedFilterItem(
        label: 'NO DISP.',
        value: 'unavailable',
      ),
      const AppSegmentedFilterItem(
        label: 'DESCANSO',
        value: 'resting',
      ),
      const AppSegmentedFilterItem(
        label: 'EN SERVICIO',
        value: 'in_service',
      ),
      if (widget.canEdit)
        const AppSegmentedFilterItem(
          label: 'ELIMINADOS',
          value: 'deleted',
        ),
    ];

    // Elegir valor actual: _filterMode mapea directamente a los values string.
    return AppSegmentedFilter<String?>(
      value: _controller.filterMode,
      onChanged: (v) => _controller.setFilterMode(v),
      items: items,
    );
  }

  Widget _buildListView() {
    final filtered = _filteredRecords;
    if (filtered.isEmpty) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.symmetric(vertical: 48),
          child: Text(
            'Sin resultados',
            style: Theme.of(context).textTheme.bodyMedium?.copyWith(
              color: Theme.of(context).colorScheme.onSurfaceVariant,
            ),
          ),
        ),
      );
    }

    return ListView.separated(
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      itemCount: filtered.length,
      separatorBuilder: (_, __) => const SizedBox(height: 6),
      itemBuilder: (context, i) {
        final e = filtered[i];
        return AppEntityRowCard(
          title: e.name,
          subtitle: e.summary,
          badge: AppBadge(
            label: e.statusLabel,
            tone: e.statusTone,
            uppercase: false,
          ),
          leading: e.imageBase64 != null && e.imageBase64!.isNotEmpty
              ? ClipRRect(
                  borderRadius: BorderRadius.circular(4),
                  child: Image.memory(
                    base64Decode(e.imageBase64!),
                    width: 48,
                    height: 48,
                    fit: BoxFit.cover,
                    errorBuilder: (_, __, ___) => _listPlaceholder(),
                  ),
                )
              : _listPlaceholder(),
          onTap: () => _showEquineActions(context, e),
        );
      },
    );
  }

  Widget _listPlaceholder() {
    return Container(
      width: 48,
      height: 48,
      decoration: BoxDecoration(
        color: Theme.of(context).colorScheme.surfaceContainerHighest,
        borderRadius: BorderRadius.circular(4),
      ),
      child: Icon(
        Symbols.chess_knight,
        size: 24,
        color: Theme.of(context).colorScheme.onSurfaceVariant,
      ),
    );
  }

  Widget _buildSelectedEquineSection() {
    final detail = _controller.selectedDetail;
    if (detail == null) {
      return const SizedBox.shrink();
    }
    return AppEquineProfileCard(detail: detail);
  }

  Widget _buildEmptyFilterMessage() {
    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        Icon(Symbols.search_off_rounded, size: 40,
          color: Theme.of(context).colorScheme.onSurfaceVariant),
        const SizedBox(height: 8),
        Text(
          'No hay equinos con ese estado',
          style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                color: Theme.of(context).colorScheme.onSurfaceVariant,
              ),
        ),
      ],
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

  /// Timeline del equino seleccionado.
  Widget _buildTimelineSection() {
    final records = _controller.records;
    if (records.isEmpty) {
      return const SizedBox.shrink();
    }

    final firstRecord = records.first;
    final equineId = _controller.selectedEquineId ?? firstRecord.id;
    final equineName = records.firstWhere(
      (r) => r.id == equineId,
      orElse: () => firstRecord,
    ).name;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        AppSectionHeader(
          title: 'Historial reciente',
          variant: AppSectionHeaderVariant.compact,
        ),
        const SizedBox(height: 16),
        // Cargar timeline real desde el repo, con fallback a datos vacíos.
        FutureBuilder<List<EquineTimelineEntry>>(
          future: widget.repository.getEquineTimeline(equineId),
          builder: (context, snapshot) {
            if (snapshot.connectionState == ConnectionState.waiting) {
              return const Padding(
                padding: EdgeInsets.symmetric(vertical: 24),
                child: AppCenteredLoader(fill: false),
              );
            }
            if (snapshot.hasError || !snapshot.hasData || snapshot.data!.isEmpty) {
              return Center(
                child: Padding(
                  padding: const EdgeInsets.symmetric(vertical: 24),
                  child: Text(
                    'Sin historial disponible',
                    style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                      color: Theme.of(context).colorScheme.onSurfaceVariant,
                    ),
                  ),
                ),
              );
            }
            final entries = snapshot.data!
                .take(5)
                .map((e) => EquineMapper.timelineEntryToLogbookEntry(e))
                .toList();
            return AppLogbookTimeline(entries: entries);
          },
        ),
        const SizedBox(height: 20),
        AppButton(
          label: 'Ver timeline completo',
          icon: Icons.history_rounded,
          variant: AppButtonVariant.secondary,
          expanded: true,
          onPressed: () {
            Navigator.of(context).push(
              MaterialPageRoute(
                builder: (_) => EquineTimelineScreen(
                  equineId: equineId,
                  equineName: equineName,
                  repository: widget.repository,
                ),
              ),
            );
          },
        ),
      ],
    );
  }

}
