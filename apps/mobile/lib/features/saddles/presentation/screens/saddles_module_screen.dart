import 'package:flutter/material.dart';
import 'package:material_symbols_icons/material_symbols_icons.dart';

import 'package:mobile_ui/src/widgets/app_badge.dart';
import 'package:mobile_ui/src/widgets/app_button.dart';
import 'package:mobile_ui/src/widgets/app_centered_loader.dart';
import 'package:mobile_ui/src/widgets/app_section_header.dart';
import 'package:mobile_ui/src/widgets/app_segmented_filter.dart';
import 'package:mobile_ui/src/widgets/app_status_banner.dart';
import 'package:mobile_ui/src/widgets/app_text_field.dart';
import 'package:mobile_ui/src/widgets/refresh_scope.dart';
import 'package:mobile_domain/src/saddles/saddles_repository.dart';
import 'package:mobile/features/saddles/infrastructure/repositories/fallback_saddles_repository.dart';
import 'package:mobile/features/saddles/saddles_module.dart';
import 'package:mobile/features/saddles/presentation/controllers/saddles_list_controller.dart';
import 'package:mobile/features/saddles/presentation/models/saddle_view_models.dart';
import 'package:mobile/features/saddles/presentation/widgets/saddle_form_sheet.dart';
import 'package:mobile/features/saddles/presentation/widgets/saddle_row_card.dart';

class SaddlesModuleScreen extends StatefulWidget {
  const SaddlesModuleScreen({
    super.key,
    this.showHeader = true,
    this.saddlesModule,
  });

  final bool showHeader;
  final SaddlesModule? saddlesModule;

  @override
  State<SaddlesModuleScreen> createState() => _SaddlesModuleScreenState();
}

class _SaddlesModuleScreenState extends State<SaddlesModuleScreen>
    with RefreshableState {
  late final SaddlesListController _listController;
  late final bool _ownsListController;
  late final SaddlesRepository _repository;
  final TextEditingController _searchController = TextEditingController();

  @override
  Future<void> onRefresh() => _listController.refresh();

  @override
  void initState() {
    super.initState();
    _repository = widget.saddlesModule?.repository ?? FallbackSaddlesRepository();
    if (widget.saddlesModule != null) {
      _listController = widget.saddlesModule!.listController;
      _ownsListController = false;
    } else {
      _listController = SaddlesListController(repository: _repository);
      _ownsListController = true;
    }
    _listController.addListener(_onListChanged);
    if (_listController.state == SaddlesLoadState.idle) {
      _listController.loadInitial();
    }

    _searchController.addListener(() {
      _listController.setSearchQuery(_searchController.text);
    });
  }

  @override
  void dispose() {
    _listController.removeListener(_onListChanged);
    if (_ownsListController) {
      _listController.dispose();
    }
    _searchController.dispose();
    super.dispose();
  }

  void _onListChanged() {
    if (mounted) setState(() {});
  }

  Future<void> _openCreateSheet() async {
    final result = await showModalBottomSheet<Map<String, dynamic>>(
      context: context,
      isScrollControlled: true,
      backgroundColor: Theme.of(context).colorScheme.surface,
      builder: (_) => const SaddleFormSheet(),
    );
    if (result != null && mounted) {
      try {
        await _repository.createSaddle(
          code: result['code'] as String,
          name: result['name'] as String?,
          isAvailable: result['is_available'] as bool? ?? true,
          notes: result['notes'] as String?,
        );
        await _listController.refresh();
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('Silla registrada correctamente')),
          );
        }
      } catch (e) {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('Error al registrar la silla')),
          );
        }
      }
    }
  }

  Future<void> _openEditSheet(SaddleRecord saddle) async {
    final result = await showModalBottomSheet<Map<String, dynamic>>(
      context: context,
      isScrollControlled: true,
      backgroundColor: Theme.of(context).colorScheme.surface,
      builder: (_) => SaddleFormSheet(existing: saddle),
    );
    if (result != null && mounted) {
      try {
        await _repository.updateSaddle(
          saddleId: saddle.id,
          code: result['code'] as String?,
          name: result['name'] as String?,
          isAvailable: result['is_available'] as bool?,
          notes: result['notes'] as String?,
        );
        await _listController.refresh();
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('Silla actualizada correctamente')),
          );
        }
      } catch (e) {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('Error al actualizar la silla')),
          );
        }
      }
    }
  }

  Future<void> _confirmDeleteSaddle(SaddleRecord saddle) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Eliminar silla'),
        content: Text(
          '¿Estás seguro de eliminar "${saddle.code}"? '
          'La silla quedará oculta de los listados activos.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(ctx).pop(false),
            child: const Text('Cancelar'),
          ),
          TextButton(
            onPressed: () => Navigator.of(ctx).pop(true),
            child: const Text('Eliminar'),
          ),
        ],
      ),
    );
    if (confirmed == true && mounted) {
      try {
        await _repository.deleteSaddle(saddle.id);
        await _listController.refresh();
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('Silla eliminada')),
          );
        }
      } catch (e) {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('Error al eliminar la silla')),
          );
        }
      }
    }
  }

  Future<void> _confirmRestoreSaddle(SaddleRecord saddle) async {
    try {
      await _repository.restoreSaddle(saddle.id);
      await _listController.refresh();
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Silla restaurada')),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Error al restaurar la silla')),
        );
      }
    }
  }

  void _showSaddleActions(SaddleRecord saddle) {
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
              Icon(
                Symbols.airline_seat_legroom_extra,
                size: 40,
                color: scheme.primary,
              ),
              const SizedBox(height: 12),
              Text(
                saddle.code,
                style: Theme.of(context).textTheme.titleLarge?.copyWith(
                      fontWeight: FontWeight.w800,
                    ),
              ),
              const SizedBox(height: 4),
              Text(
                saddle.name,
                style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                      color: scheme.onSurfaceVariant,
                    ),
              ),
              const SizedBox(height: 8),
              AppBadge(
                label: saddle.statusLabel,
                tone: saddle.statusTone,
                uppercase: false,
              ),
              if (saddle.notes != null && saddle.notes!.isNotEmpty) ...[
                const SizedBox(height: 12),
                Text(
                  saddle.notes!,
                  style: Theme.of(context).textTheme.bodySmall?.copyWith(
                        color: scheme.onSurfaceVariant,
                      ),
                  textAlign: TextAlign.center,
                ),
              ],
              const SizedBox(height: 24),
              SizedBox(
                width: double.infinity,
                child: AppButton(
                  label: 'Editar',
                  icon: Icons.edit_rounded,
                  onPressed: () {
                    Navigator.of(ctx).pop();
                    _openEditSheet(saddle);
                  },
                ),
              ),
              const SizedBox(height: 10),
              if (saddle.isDeleted)
                SizedBox(
                  width: double.infinity,
                  child: AppButton(
                    label: 'Restaurar',
                    icon: Icons.restore_rounded,
                    variant: AppButtonVariant.secondary,
                    onPressed: () {
                      Navigator.of(ctx).pop();
                      _confirmRestoreSaddle(saddle);
                    },
                  ),
                )
              else
                SizedBox(
                  width: double.infinity,
                  child: AppButton(
                    label: 'Eliminar',
                    icon: Icons.delete_outline_rounded,
                    variant: AppButtonVariant.secondary,
                    onPressed: () {
                      Navigator.of(ctx).pop();
                      _confirmDeleteSaddle(saddle);
                    },
                  ),
                ),
              const SizedBox(height: 10),
              SizedBox(
                width: double.infinity,
                child: AppButton(
                  label: 'Cerrar',
                  icon: Icons.close_rounded,
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

  @override
  Widget build(BuildContext context) {
    final state = _listController.state;
    final body = _buildContent(state);

    if (widget.showHeader) {
      return Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          AppSectionHeader(
            eyebrow: 'Gestion',
            title: 'Sillas',
          ),
          const SizedBox(height: 20),
          Expanded(child: body),
        ],
      );
    }

    return body;
  }

  Widget _buildContent(SaddlesLoadState state) {
    switch (state) {
      case SaddlesLoadState.idle:
      case SaddlesLoadState.loading:
        return const RefreshableViewport(child: AppCenteredLoader());

      case SaddlesLoadState.refreshing:
        if (_listController.items.isEmpty) {
          return const RefreshableViewport(child: AppCenteredLoader());
        }
        return _buildListContent();

      case SaddlesLoadState.success:
      case SaddlesLoadState.offlineFromCache:
        return _buildListContent();

      case SaddlesLoadState.empty:
        return RefreshableViewport(child: _buildEmptyState());

      case SaddlesLoadState.error:
        return RefreshableViewport(child: _buildErrorState());
    }
  }

  Widget _buildListContent() {
    final items = _listController.items;
    final hasItems = _listController.hasAnyRecords;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // Search
        AppTextField(
          controller: _searchController,
          hintText: 'Buscar por código o nombre...',
          variant: AppTextFieldVariant.filled,
          suffix: const Icon(Icons.search_rounded, size: 20),
        ),
        const SizedBox(height: 12),

        // Availability filter
        AppSegmentedFilter<String?>(
          value: _availabilityFilterValue,
          initialValue: 'active',
          onChanged: (value) {
            if (value == null || value == 'active') {
              _listController.setIncludeDeleted(false);
              _listController.setShowOnlyAvailable(null);
            } else if (value == 'available') {
              _listController.setIncludeDeleted(false);
              _listController.setShowOnlyAvailable(true);
            } else if (value == 'unavailable') {
              _listController.setIncludeDeleted(false);
              _listController.setShowOnlyAvailable(false);
            } else if (value == 'deleted') {
              _listController.setIncludeDeleted(true);
              _listController.setShowOnlyAvailable(null);
            }
          },
          items: const [
            AppSegmentedFilterItem(label: 'Activas', value: 'active'),
            AppSegmentedFilterItem(label: 'Disponibles', value: 'available'),
            AppSegmentedFilterItem(
              label: 'No disponibles',
              value: 'unavailable',
            ),
            AppSegmentedFilterItem(label: 'Eliminadas', value: 'deleted'),
          ],
        ),
        const SizedBox(height: 12),

        // Add button
        AppButton(
          label: 'Registrar silla',
          icon: Icons.add,
          expanded: true,
          onPressed: _openCreateSheet,
        ),
        const SizedBox(height: 16),

        // Error banner
        if (_listController.state == SaddlesLoadState.offlineFromCache) ...[
          AppStatusBanner(
            title: 'Sin conexion',
            message: 'Mostrando datos almacenados localmente.',
            tone: AppStatusBannerTone.warning,
            icon: Icons.wifi_off_rounded,
            badgeLabel: 'Offline',
          ),
          const SizedBox(height: 12),
        ],

        // List or empty filter message
        if (items.isEmpty && hasItems)
          _buildEmptyFilterMessage()
        else if (items.isEmpty)
          _buildEmptyInventory()
        else
          _buildSaddleListView(items),
      ],
    );
  }

  Widget _buildEmptyFilterMessage() {
    return Expanded(
      child: Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(Icons.search_off_rounded,
                size: 40,
                color: Theme.of(context).colorScheme.onSurfaceVariant),
            const SizedBox(height: 8),
            Text(
              'No hay sillas con ese filtro',
              style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                    color: Theme.of(context).colorScheme.onSurfaceVariant,
                  ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildEmptyInventory() {
    return Expanded(
      child: Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(Symbols.airline_seat_legroom_extra,
                size: 48,
                color: Theme.of(context).colorScheme.onSurfaceVariant),
            const SizedBox(height: 12),
            Text('No hay sillas registradas',
                style: Theme.of(context).textTheme.titleMedium),
            const SizedBox(height: 4),
            Text(
              'Registra la primera silla usando el boton de arriba',
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                    color: Theme.of(context).colorScheme.onSurfaceVariant,
                  ),
              textAlign: TextAlign.center,
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildSaddleListView(List<SaddleRecord> items) {
    return Expanded(
      child: ListView.separated(
        physics: const AlwaysScrollableScrollPhysics(),
        itemCount: items.length,
        separatorBuilder: (_, __) => const SizedBox(height: 10),
        itemBuilder: (context, i) {
          return SaddleRowCard(
            saddle: items[i],
            onTap: () => _showSaddleActions(items[i]),
          );
        },
      ),
    );
  }

  String? get _availabilityFilterValue {
    if (_listController.includeDeleted) return 'deleted';
    final v = _listController.showOnlyAvailable;
    if (v == null) return 'active';
    if (v) return 'available';
    return 'unavailable';
  }

  Widget _buildEmptyState() {
    return Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(
            Symbols.airline_seat_legroom_extra,
            size: 56,
            color: Theme.of(context).colorScheme.onSurfaceVariant,
          ),
          const SizedBox(height: 16),
          Text(
            'No hay sillas',
            style: Theme.of(context).textTheme.titleMedium?.copyWith(
                  color: Theme.of(context).colorScheme.onSurfaceVariant,
                ),
          ),
          const SizedBox(height: 8),
          Text(
            'Registra una nueva silla usando el boton de abajo',
            style: Theme.of(context).textTheme.bodySmall?.copyWith(
                  color: Theme.of(context).colorScheme.onSurfaceVariant,
                ),
          ),
          const SizedBox(height: 24),
          AppButton(
            label: 'Registrar silla',
            icon: Icons.add,
            onPressed: _openCreateSheet,
          ),
        ],
      ),
    );
  }

  Widget _buildErrorState() {
    return Center(
      child: AppStatusBanner(
        title: 'Error al cargar sillas',
        message: _listController.errorMessage ?? 'Error desconocido',
        tone: AppStatusBannerTone.danger,
        onTap: _listController.loadInitial,
      ),
    );
  }
}
