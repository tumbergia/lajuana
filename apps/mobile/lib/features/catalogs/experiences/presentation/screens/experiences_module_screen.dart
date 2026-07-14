import 'dart:convert';
import 'dart:typed_data';

import 'package:flutter/material.dart';
import 'package:material_symbols_icons/material_symbols_icons.dart';

import 'package:mobile_ui/mobile_ui.dart';
import 'package:mobile/features/auth/presentation/auth_controller.dart';
import 'package:mobile/features/catalogs/catalogs_module.dart';
import 'package:mobile/features/catalogs/experiences/domain/experience.dart';
import 'package:mobile/features/catalogs/experiences/presentation/controllers/experiences_tab_controller.dart';
import 'package:mobile/features/catalogs/experiences/presentation/pages/experience_detail_page.dart';
import 'package:mobile/features/catalogs/experiences/presentation/pages/experience_form_page.dart';

class ExperiencesModuleScreen extends StatefulWidget {
  const ExperiencesModuleScreen({
    super.key,
    this.catalogsModule,
    required this.authController,
    this.showHeader = true,
  });

  final CatalogsModule? catalogsModule;
  final AuthController authController;
  final bool showHeader;

  bool get canEdit =>
      authController.currentUser?.role == 'admin';

  @override
  State<ExperiencesModuleScreen> createState() => _ExperiencesModuleScreenState();
}

class _ExperiencesModuleScreenState extends State<ExperiencesModuleScreen>
    with RefreshableState {
  late final ExperiencesTabController _controller;
  late final TextEditingController _searchController;
  String _searchQuery = '';
  bool _missingModule = false;

  @override
  Future<void> onRefresh() =>
      _missingModule ? Future.value() : _controller.refreshFromServer();

  @override
  void initState() {
    super.initState();
    _searchController = TextEditingController();
    final module = widget.catalogsModule;
    if (module == null) {
      _missingModule = true;
      return;
    }
    _controller = ExperiencesTabController(
      repository: module.experiences,
      catalogsRepository: module.repository,
    );
    _controller.addListener(_onChanged);
    _controller.loadLocalThenRefresh();
  }

  void _onChanged() {
    if (mounted) setState(() {});
  }

  @override
  void dispose() {
    if (!_missingModule) {
      _controller.removeListener(_onChanged);
      _controller.dispose();
    }
    _searchController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    if (!widget.showHeader) {
      return _buildBodyContent();
    }
    return Padding(
      padding: const EdgeInsets.fromLTRB(24, 24, 24, 24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          AppSectionHeader(
            eyebrow: 'GESTIÓN',
            title: 'EXPERIENCIAS',
            variant: AppSectionHeaderVariant.hero,
          ),
          const SizedBox(height: 20),
          Expanded(child: _buildBodyContent()),
        ],
      ),
    );
  }

  Widget _buildBodyContent() {
    if (_missingModule) {
      return RefreshableViewport(
        child: Center(
          child: Padding(
            padding: const EdgeInsets.symmetric(vertical: 80),
            child: AppStatusBanner(
              title: 'Modulo no disponible',
              message: 'El modulo de catalogos no esta inicializado.',
              tone: AppStatusBannerTone.danger,
              badgeLabel: 'ERROR',
            ),
          ),
        ),
      );
    }
    switch (_controller.loadState) {
      case ExperiencesTabLoadState.idle:
      case ExperiencesTabLoadState.loading:
        return const RefreshableViewport(child: AppCenteredLoader());
      case ExperiencesTabLoadState.syncing:
        return RefreshableViewport(child: _buildSyncing());
      case ExperiencesTabLoadState.error:
        return RefreshableViewport(child: _buildError());
      case ExperiencesTabLoadState.empty:
        return RefreshableViewport(child: _buildEmpty());
      case ExperiencesTabLoadState.success:
      case ExperiencesTabLoadState.offlineFromCache:
        return _buildSuccessContent();
    }
  }

  Widget _buildSyncing() {
    return Center(
      child: Padding(
        padding: const EdgeInsets.symmetric(vertical: 80),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const AppCenteredLoader(),
            const SizedBox(height: 16),
            Text(
              'Cargando experiencias…',
              style: Theme.of(context).textTheme.titleMedium?.copyWith(
                color: Theme.of(context).colorScheme.onSurfaceVariant,
              ),
            ),
            const SizedBox(height: 8),
            Text(
              'Un momento',
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                color: Theme.of(context).colorScheme.onSurfaceVariant,
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildError() {
    return Center(
      child: Padding(
        padding: const EdgeInsets.symmetric(vertical: 80),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            AppStatusBanner(
              title: 'Error al cargar experiencias',
              message: _controller.errorMessage,
              tone: AppStatusBannerTone.danger,
              badgeLabel: 'ERROR',
            ),
            const SizedBox(height: 24),
            FilledButton.icon(
              onPressed: () => _controller.loadLocalThenRefresh(),
              icon: const Icon(Icons.refresh_rounded),
              label: const Text('Reintentar'),
            ),
          ],
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
              Symbols.explore,
              size: 56,
              color: Theme.of(context).colorScheme.onSurfaceVariant,
            ),
            const SizedBox(height: 16),
            Text(
              'No hay experiencias',
              style: Theme.of(context).textTheme.titleMedium?.copyWith(
                color: Theme.of(context).colorScheme.onSurfaceVariant,
              ),
            ),
            const SizedBox(height: 8),
            Text(
              'Desliza para actualizar o verifica tu conexión',
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                color: Theme.of(context).colorScheme.onSurfaceVariant,
              ),
            ),
            const SizedBox(height: 24),
            FilledButton.icon(
              onPressed: () => _controller.refreshFromServer(),
              icon: const Icon(Icons.refresh_rounded),
              label: const Text('Actualizar'),
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
            onChanged: (v) {
              _searchQuery = v;
              _controller.setSearchQuery(v);
            },
            decoration: InputDecoration(
              hintText: 'Buscar experiencia…',
              prefixIcon: Icon(Symbols.search_rounded, size: 20),
              suffixIcon: _searchQuery.isNotEmpty
                  ? IconButton(
                      icon: Icon(Symbols.close_rounded, size: 18),
                      onPressed: () {
                        _searchController.clear();
                        _searchQuery = '';
                        _controller.setSearchQuery('');
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
              contentPadding: const EdgeInsets.symmetric(
                horizontal: 12,
                vertical: 10,
              ),
            ),
          ),
        ),
        if (_controller.isRefreshing) ...[
          const SizedBox(width: 8),
          const SizedBox(
            width: 20,
            height: 20,
            child: CircularProgressIndicator(strokeWidth: 2),
          ),
        ],
      ],
    );
  }

  Widget _buildCreateButton() {
    if (!widget.canEdit) return const SizedBox.shrink();
    return AppButton(
      label: 'Crear experiencia',
      icon: Icons.add,
      expanded: true,
      onPressed: () async {
        await Navigator.of(context).push(
          MaterialPageRoute<void>(
            builder: (_) => ExperienceFormPage(
              module: widget.catalogsModule!,
              authController: widget.authController,
            ),
          ),
        );
        if (mounted) {
          await _controller.loadLocalThenRefresh(refreshServer: true);
        }
      },
    );
  }

  Widget _buildSuccessContent() {
    final items = _controller.items;
    final hasData = _controller.allItems.isNotEmpty;
    final filteredEmpty = items.isEmpty;

    if (filteredEmpty && hasData) {
      final offlineBanner = _buildOfflineBanner();
      return Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          if (offlineBanner != null) ...[
            offlineBanner,
            const SizedBox(height: 16),
          ],
          _buildSearchRow(),
          const SizedBox(height: 12),
          _buildCreateButton(),
          const SizedBox(height: 16),
          Expanded(child: Center(child: _buildEmptyFilterMessage())),
        ],
      );
    }

    return SingleChildScrollView(
      physics: const AlwaysScrollableScrollPhysics(),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          if (_controller.loadState ==
              ExperiencesTabLoadState.offlineFromCache) ...[
            _buildOfflineBanner()!,
            const SizedBox(height: 16),
          ],
          _buildSearchRow(),
          const SizedBox(height: 12),
          _buildCreateButton(),
          const SizedBox(height: 16),
          if (!filteredEmpty) _buildListView(),
        ],
      ),
    );
  }

  Widget? _buildOfflineBanner() {
    if (_controller.loadState != ExperiencesTabLoadState.offlineFromCache) {
      return null;
    }
    return AppStatusBanner(
      title: 'Sin conexion',
      message: _controller.errorMessage.isNotEmpty
          ? _controller.errorMessage
          : 'Mostrando datos almacenados localmente.',
      tone: AppStatusBannerTone.warning,
      icon: Icons.wifi_off_rounded,
      badgeLabel: 'Offline',
    );
  }

  Widget _buildListView() {
    final items = _controller.items;
    return ListView.separated(
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      itemCount: items.length,
      separatorBuilder: (_, __) => const SizedBox(height: 6),
      itemBuilder: (context, i) {
        final e = items[i];
        return AppEntityRowCard(
          title: e.name,
          subtitle: '',
          leading: _buildLeadingImage(e),
          trailing: const Icon(Icons.chevron_right_rounded, size: 18),
          onTap: () => _showExperienceActions(context, e),
        );
      },
    );
  }

  Widget _buildLeadingImage(CatalogExperience e) {
    // Prefer base64 local image, fallback to network image, else placeholder
    if (e.imageBase64 != null && e.imageBase64!.isNotEmpty) {
      return ClipRRect(
        borderRadius: BorderRadius.circular(4),
        child: Image.memory(
          base64Decode(e.imageBase64!),
          width: 48,
          height: 48,
          fit: BoxFit.cover,
          errorBuilder: (_, __, ___) => _listPlaceholder(),
        ),
      );
    }
    if (e.imageUrl != null && e.imageUrl!.isNotEmpty) {
      return ClipRRect(
        borderRadius: BorderRadius.circular(4),
        child: Image.network(
          e.imageUrl!,
          width: 48,
          height: 48,
          fit: BoxFit.cover,
          errorBuilder: (_, __, ___) => _listPlaceholder(),
        ),
      );
    }
    return _listPlaceholder();
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
        Symbols.explore,
        size: 24,
        color: Theme.of(context).colorScheme.onSurfaceVariant,
      ),
    );
  }

  Widget _buildEmptyFilterMessage() {
    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        Icon(
          Symbols.search_off_rounded,
          size: 40,
          color: Theme.of(context).colorScheme.onSurfaceVariant,
        ),
        const SizedBox(height: 8),
        Text(
          'No hay experiencias con ese filtro',
          style: Theme.of(context).textTheme.bodyMedium?.copyWith(
            color: Theme.of(context).colorScheme.onSurfaceVariant,
          ),
        ),
      ],
    );
  }

  void _confirmDeleteExperience(CatalogExperience experience) {
    AppConfirmDialog.show(
      context: context,
      icon: Icons.delete_outline_rounded,
      title: 'Eliminar experiencia',
      message:
          'La experiencia "${experience.name}" se desactivara del catalogo. '
          'Esta accion es reversible editando su estado.',
      confirmLabel: 'Eliminar',
      style: DialogStyle.danger,
      height: 280,
      onConfirm: () => _deleteExperience(experience),
    );
  }

  Future<void> _deleteExperience(CatalogExperience experience) async {
    try {
      await widget.catalogsModule!.experiences.deactivate(experience.id);
      if (!mounted) return;
      showAppToast(context, message: 'Experiencia eliminada correctamente');
      await _controller.loadLocalThenRefresh(refreshServer: true);
    } catch (_) {
      if (!mounted) return;
      showAppToast(
        context,
        message: 'No se pudo eliminar la experiencia. Intenta de nuevo.',
        isError: true,
      );
    }
  }

  void _showExperienceActions(BuildContext context, CatalogExperience experience) {
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
                experience.name,
                style: Theme.of(context)
                    .textTheme
                    .titleLarge
                    ?.copyWith(fontWeight: FontWeight.w800),
              ),
              const SizedBox(height: 4),
              Text(
                experience.description,
                maxLines: 2,
                overflow: TextOverflow.ellipsis,
                style: Theme.of(context)
                    .textTheme
                    .bodySmall
                    ?.copyWith(color: scheme.onSurfaceVariant),
              ),
              const SizedBox(height: 24),
              SizedBox(
                width: double.infinity,
                child: AppButton(
                  label: 'Ver detalle',
                  icon: Icons.info_outline_rounded,
                  onPressed: () async {
                    Navigator.of(ctx).pop();
                    await Navigator.of(context).push(
                      MaterialPageRoute<void>(
                        builder: (_) => ExperienceDetailPage(
                          module: widget.catalogsModule!,
                          authController: widget.authController,
                          experienceId: experience.id,
                        ),
                      ),
                    );
                    if (mounted) {
                      _controller.loadLocalThenRefresh(refreshServer: true);
                    }
                  },
                ),
              ),
              if (widget.canEdit) ...[
                const SizedBox(height: 10),
                SizedBox(
                  width: double.infinity,
                  child: AppButton(
                    label: 'Editar',
                    icon: Icons.edit_rounded,
                    variant: AppButtonVariant.secondary,
                    onPressed: () async {
                      Navigator.of(ctx).pop();
                      await Navigator.of(context).push(
                        MaterialPageRoute<void>(
                          builder: (_) => ExperienceFormPage(
                            module: widget.catalogsModule!,
                            authController: widget.authController,
                            editing: experience,
                          ),
                        ),
                      );
                      if (mounted) {
                        _controller.loadLocalThenRefresh(refreshServer: true);
                      }
                    },
                  ),
                ),
                if (experience.isActive) ...[
                  const SizedBox(height: 10),
                  SizedBox(
                    width: double.infinity,
                    child: AppButton(
                      label: 'Eliminar',
                      icon: Icons.delete_outline_rounded,
                      variant: AppButtonVariant.danger,
                      onPressed: () {
                        Navigator.of(ctx).pop();
                        _confirmDeleteExperience(experience);
                      },
                    ),
                  ),
                ],
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
}
