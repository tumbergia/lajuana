import 'package:flutter/material.dart';
import 'package:material_symbols_icons/material_symbols_icons.dart';

import 'package:mobile_ui/src/widgets/app_button.dart';
import 'package:mobile_ui/src/widgets/app_centered_loader.dart';
import 'package:mobile_ui/src/widgets/app_search_field.dart';
import 'package:mobile_ui/src/widgets/app_section_header.dart';
import 'package:mobile_ui/src/widgets/app_segmented_filter.dart';
import 'package:mobile_ui/src/widgets/app_status_banner.dart';
import 'package:mobile_ui/src/widgets/refresh_scope.dart';
import 'package:mobile_ui/src/widgets/app_toast.dart';
import 'package:mobile_domain/src/providers/providers_repository.dart';
import 'package:mobile/features/providers/infrastructure/mappers/provider_mapper.dart';
import 'package:mobile/features/providers/infrastructure/repositories/fallback_providers_repository.dart';
import 'package:mobile/features/providers/providers_module.dart';
import 'package:mobile/features/providers/presentation/controllers/providers_list_controller.dart';
import 'package:mobile/features/providers/presentation/models/provider_view_models.dart';
import 'package:mobile/features/providers/presentation/widgets/provider_detail_sheet.dart';
import 'package:mobile/features/providers/presentation/widgets/provider_form_sheet.dart';
import 'package:mobile/features/providers/presentation/widgets/provider_row_card.dart';

class ProvidersModuleScreen extends StatefulWidget {
  const ProvidersModuleScreen({
    super.key,
    this.showHeader = true,
    this.providersModule,
    this.canManage = true,
  });

  final bool showHeader;
  final ProvidersModule? providersModule;

  /// When false (e.g. guide), hide create/edit/deactivate actions.
  final bool canManage;

  @override
  State<ProvidersModuleScreen> createState() => _ProvidersModuleScreenState();
}

class _ProvidersModuleScreenState extends State<ProvidersModuleScreen>
    with RefreshableState {
  late final ProvidersListController _listController;
  late final bool _ownsListController;
  late final ProvidersRepository _repository;
  final TextEditingController _searchController = TextEditingController();

  @override
  Future<void> onRefresh() => _listController.refresh();

  @override
  void initState() {
    super.initState();
    _repository =
        widget.providersModule?.repository ?? FallbackProvidersRepository();
    if (widget.providersModule != null) {
      _listController = widget.providersModule!.listController;
      _ownsListController = false;
    } else {
      _listController = ProvidersListController(repository: _repository);
      _ownsListController = true;
    }
    _listController.addListener(_onListChanged);
    if (_listController.state == ProvidersLoadState.idle) {
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
      builder: (_) => const ProviderFormSheet(),
    );
    if (result != null && mounted) {
      try {
        await _repository.createProvider(
          name: result['name'] as String,
          type: result['type'] as String,
          status: result['status'] as String? ?? 'active',
          serviceCategories:
              result['service_categories'] as List<String>? ?? const [],
          contactName: result['contact_name'] as String?,
          email: result['email'] as String?,
          whatsappPhone: result['whatsapp_phone'] as String?,
          locationLabel: result['location_label'] as String?,
          capacityNotes: result['capacity_notes'] as String?,
          operationalNotes: result['operational_notes'] as String?,
          tariffNotes: result['tariff_notes'] as String?,
          sourceNotes: result['source_notes'] as String?,
        );
        await _listController.refresh();
        if (mounted) {
          showAppToast(context, message: 'Proveedor registrado correctamente');
        }
      } catch (e) {
        if (mounted) {
          showAppToast(
            context,
            message: 'Error al registrar el proveedor',
            isError: true,
          );
        }
      }
    }
  }

  Future<void> _openEditSheet(ProviderRecord provider) async {
    ProviderRecord editable = provider;
    try {
      final full = await _repository.getProviderById(provider.id);
      editable = listItemToRecord(full);
    } catch (_) {
      // Usa datos del listado si falla la carga detallada.
    }

    if (!mounted) return;

    final result = await showModalBottomSheet<Map<String, dynamic>>(
      context: context,
      isScrollControlled: true,
      backgroundColor: Theme.of(context).colorScheme.surface,
      builder: (_) => ProviderFormSheet(existing: editable),
    );
    if (result != null && mounted) {
      try {
        await _repository.updateProvider(
          providerId: provider.id,
          name: result['name'] as String?,
          type: result['type'] as String?,
          status: result['status'] as String?,
          serviceCategories: result['service_categories'] as List<String>?,
          contactName: result['contact_name'] as String?,
          email: result['email'] as String?,
          whatsappPhone: result['whatsapp_phone'] as String?,
          locationLabel: result['location_label'] as String?,
          capacityNotes: result['capacity_notes'] as String?,
          operationalNotes: result['operational_notes'] as String?,
          tariffNotes: result['tariff_notes'] as String?,
          sourceNotes: result['source_notes'] as String?,
        );
        await _listController.refresh();
        if (mounted) {
          showAppToast(context, message: 'Proveedor actualizado correctamente');
        }
      } catch (e) {
        if (mounted) {
          showAppToast(
            context,
            message: 'Error al actualizar el proveedor',
            isError: true,
          );
        }
      }
    }
  }

  Future<void> _confirmDeactivateProvider(ProviderRecord provider) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Desactivar proveedor'),
        content: Text(
          '¿Desactivar "${provider.name}"? '
          'Quedara oculto de los listados activos.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(ctx).pop(false),
            child: const Text('Cancelar'),
          ),
          TextButton(
            onPressed: () => Navigator.of(ctx).pop(true),
            child: const Text('Desactivar'),
          ),
        ],
      ),
    );
    if (confirmed == true && mounted) {
      try {
        await _repository.deactivateProvider(provider.id);
        await _listController.refresh();
        if (mounted) {
          showAppToast(context, message: 'Proveedor desactivado');
        }
      } catch (e) {
        if (mounted) {
          showAppToast(
            context,
            message: 'Error al desactivar el proveedor',
            isError: true,
          );
        }
      }
    }
  }

  Future<void> _confirmReactivateProvider(ProviderRecord provider) async {
    try {
      await _repository.reactivateProvider(provider.id);
      await _listController.refresh();
      if (mounted) {
        showAppToast(context, message: 'Proveedor reactivado');
      }
    } catch (e) {
      if (mounted) {
        showAppToast(
          context,
          message: 'Error al reactivar el proveedor',
          isError: true,
        );
      }
    }
  }

  void _showProviderDetail(ProviderRecord provider) {
    showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      backgroundColor: Theme.of(context).colorScheme.surface,
      builder: (_) => ProviderDetailSheet(
        provider: provider,
        loadDetails: () async {
          final full = await _repository.getProviderById(provider.id);
          return listItemToRecord(full);
        },
        onEdit: widget.canManage ? () => _openEditSheet(provider) : null,
        onDeactivate: widget.canManage
            ? () => _confirmDeactivateProvider(provider)
            : null,
        onReactivate: widget.canManage
            ? () => _confirmReactivateProvider(provider)
            : null,
      ),
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
          const AppSectionHeader(eyebrow: 'Gestion', title: 'Proveedores'),
          const SizedBox(height: 20),
          Expanded(child: body),
        ],
      );
    }

    return body;
  }

  Widget _buildContent(ProvidersLoadState state) {
    switch (state) {
      case ProvidersLoadState.idle:
      case ProvidersLoadState.loading:
        return const RefreshableViewport(child: AppCenteredLoader());

      case ProvidersLoadState.refreshing:
        if (_listController.items.isEmpty) {
          return const RefreshableViewport(child: AppCenteredLoader());
        }
        return _buildListContent();

      case ProvidersLoadState.success:
      case ProvidersLoadState.offlineFromCache:
        return _buildListContent();

      case ProvidersLoadState.empty:
        return RefreshableViewport(child: _buildEmptyState());

      case ProvidersLoadState.error:
        return RefreshableViewport(child: _buildErrorState());
    }
  }

  Widget _buildListContent() {
    final items = _listController.items;
    final hasItems = _listController.hasAnyRecords;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        AppSearchField(
          controller: _searchController,
          hintText: 'Buscar por nombre o ubicacion...',
        ),
        const SizedBox(height: 12),
        AppSegmentedFilter<String>(
          value: _listController.includeInactive ? 'inactive' : 'active',
          initialValue: 'active',
          onChanged: (value) {
            _listController.setIncludeInactive(value == 'inactive');
          },
          items: const [
            AppSegmentedFilterItem(label: 'Activos', value: 'active'),
            AppSegmentedFilterItem(label: 'Inactivos', value: 'inactive'),
          ],
        ),
        if (widget.canManage) ...[
          const SizedBox(height: 12),
          AppButton(
            label: 'Registrar proveedor',
            icon: Icons.add,
            expanded: true,
            onPressed: _openCreateSheet,
          ),
        ],
        const SizedBox(height: 16),
        if (_listController.state == ProvidersLoadState.offlineFromCache) ...[
          AppStatusBanner(
            title: 'Sin conexion',
            message: 'Mostrando datos almacenados localmente.',
            tone: AppStatusBannerTone.warning,
            icon: Icons.wifi_off_rounded,
            badgeLabel: 'Offline',
          ),
          const SizedBox(height: 12),
        ],
        if (items.isEmpty && hasItems)
          _buildEmptyFilterMessage()
        else if (items.isEmpty)
          _buildEmptyInventory()
        else
          _buildProviderListView(items),
      ],
    );
  }

  Widget _buildEmptyFilterMessage() {
    return Expanded(
      child: Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(
              Icons.search_off_rounded,
              size: 40,
              color: Theme.of(context).colorScheme.onSurfaceVariant,
            ),
            const SizedBox(height: 8),
            Text(
              'No hay proveedores con ese filtro',
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
            Icon(
              Symbols.handshake,
              size: 48,
              color: Theme.of(context).colorScheme.onSurfaceVariant,
            ),
            const SizedBox(height: 12),
            Text(
              'No hay proveedores registrados',
              style: Theme.of(context).textTheme.titleMedium,
            ),
            const SizedBox(height: 4),
            Text(
              widget.canManage
                  ? 'Registra el primer proveedor usando el boton de arriba'
                  : 'Aun no hay proveedores en el catalogo',
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

  Widget _buildProviderListView(List<ProviderRecord> items) {
    return Expanded(
      child: ListView.separated(
        physics: const AlwaysScrollableScrollPhysics(),
        itemCount: items.length,
        separatorBuilder: (_, __) => const SizedBox(height: 10),
        itemBuilder: (context, i) {
          return ProviderRowCard(
            provider: items[i],
            onTap: () => _showProviderDetail(items[i]),
          );
        },
      ),
    );
  }

  Widget _buildEmptyState() {
    final content = Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        Icon(
          Symbols.handshake,
          size: 56,
          color: Theme.of(context).colorScheme.onSurfaceVariant,
        ),
        const SizedBox(height: 16),
        Text(
          'No hay proveedores',
          style: Theme.of(context).textTheme.titleMedium?.copyWith(
            color: Theme.of(context).colorScheme.onSurfaceVariant,
          ),
        ),
        const SizedBox(height: 8),
        Text(
          widget.canManage
              ? 'Registra un nuevo proveedor usando el boton de abajo'
              : 'Aun no hay proveedores en el catalogo',
          style: Theme.of(context).textTheme.bodySmall?.copyWith(
            color: Theme.of(context).colorScheme.onSurfaceVariant,
          ),
          textAlign: TextAlign.center,
        ),
        if (widget.canManage) ...[
          const SizedBox(height: 24),
          AppButton(
            label: 'Registrar proveedor',
            icon: Icons.add,
            onPressed: _openCreateSheet,
          ),
        ],
      ],
    );

    return Center(child: content);
  }

  Widget _buildErrorState() {
    return Center(
      child: AppStatusBanner(
        title: 'Error al cargar proveedores',
        message: _listController.errorMessage ?? 'Error desconocido',
        tone: AppStatusBannerTone.danger,
        onTap: _listController.loadInitial,
      ),
    );
  }
}
