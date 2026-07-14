import 'package:flutter/material.dart';
import 'package:mobile_ui/mobile_ui.dart';

import 'package:mobile/features/analytics/presentation/controllers/leads_controller.dart';
import 'package:mobile/features/analytics/presentation/widgets/lead_card.dart';
import 'package:mobile/features/analytics/presentation/widgets/lead_category_section.dart';
import 'package:mobile/features/analytics/presentation/widgets/lead_detail_sheet.dart';

/// Hub único: ver indicadores por sección, exportar y configurar (pin/ocultar).
class AllLeadsScreen extends StatefulWidget {
  const AllLeadsScreen({
    super.key,
    required this.controller,
  });

  final LeadsController controller;

  @override
  State<AllLeadsScreen> createState() => _AllLeadsScreenState();
}

class _AllLeadsScreenState extends State<AllLeadsScreen> {
  // Non-late so hot reload / rebuild before initState cannot throw.
  List<String> _draftPinned = [];
  List<String> _draftExcluded = [];
  String? _localError;

  @override
  void initState() {
    super.initState();
    _resetDraftFromController();
    widget.controller.addListener(_onChanged);
  }

  @override
  void dispose() {
    widget.controller.removeListener(_onChanged);
    super.dispose();
  }

  void _resetDraftFromController() {
    final prefs = widget.controller.preferences;
    _draftPinned = List<String>.from(prefs.pinnedLeadIds);
    _draftExcluded = List<String>.from(prefs.excludedLeadIds);
    _localError = null;
  }

  void _onChanged() {
    if (!mounted) return;
    if (!_isDirty) {
      setState(_resetDraftFromController);
    } else {
      setState(() {});
    }
  }

  LeadsController get controller => widget.controller;

  bool get _isDirty {
    final prefs = controller.preferences;
    if (_draftPinned.length != prefs.pinnedLeadIds.length ||
        _draftExcluded.length != prefs.excludedLeadIds.length) {
      return true;
    }
    for (var i = 0; i < _draftPinned.length; i++) {
      if (_draftPinned[i] != prefs.pinnedLeadIds[i]) return true;
    }
    final savedExcl = prefs.excludedLeadIds.toSet();
    final draftExcl = _draftExcluded.toSet();
    return savedExcl.length != draftExcl.length ||
        !savedExcl.containsAll(draftExcl);
  }

  void _togglePin(String leadId) {
    setState(() {
      _localError = null;
      if (_draftPinned.contains(leadId)) {
        _draftPinned.remove(leadId);
      } else {
        if (_draftPinned.length >= 5) {
          _localError = 'Solo puedes fijar hasta 5 indicadores.';
          return;
        }
        _draftPinned.add(leadId);
        _draftExcluded.remove(leadId);
      }
    });
  }

  void _toggleExcluded(String leadId) {
    setState(() {
      _localError = null;
      if (_draftExcluded.contains(leadId)) {
        _draftExcluded.remove(leadId);
      } else {
        _draftPinned.remove(leadId);
        _draftExcluded.add(leadId);
      }
    });
  }

  void _movePinned(int oldIndex, int newIndex) {
    setState(() {
      if (newIndex > oldIndex) newIndex -= 1;
      final item = _draftPinned.removeAt(oldIndex);
      _draftPinned.insert(newIndex, item);
    });
  }

  Future<void> _save() async {
    final ok = await controller.savePreferences(
      LeadsPreferences(
        pinnedLeadIds: List<String>.from(_draftPinned),
        excludedLeadIds: List<String>.from(_draftExcluded),
      ),
    );
    if (!mounted) return;
    if (ok) {
      setState(_resetDraftFromController);
      showAppToast(context, message: 'Preferencias guardadas');
    } else {
      final msg = controller.error ?? 'Error al guardar preferencias.';
      setState(() => _localError = msg);
      showAppToast(context, message: msg, isError: true);
    }
  }

  void _discard() => setState(_resetDraftFromController);

  Future<void> _exportAll() async {
    try {
      await controller.exportAll();
      if (!mounted) return;
      showAppToast(context, message: 'Exportación lista');
    } catch (_) {
      if (!mounted) return;
      showAppToast(
        context,
        message: controller.error ?? 'Error al exportar',
        isError: true,
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final tokens = Theme.of(context).appTokens;
    final dirty = _isDirty;

    return Scaffold(
      appBar: AppPageAppBar(
        title: 'Indicadores',
        actions: [
          IconButton(
            icon: const Icon(Icons.download_rounded),
            tooltip: 'Exportar todos',
            onPressed: controller.isLoading ? null : _exportAll,
          ),
          IconButton(
            icon: const Icon(Icons.refresh_rounded),
            tooltip: 'Actualizar',
            onPressed: controller.isLoading
                ? null
                : () async {
                    await controller.refresh();
                    if (!mounted) return;
                    final err = controller.error;
                    if (err != null) {
                      showAppToast(this.context, message: err, isError: true);
                    }
                  },
          ),
        ],
      ),
      body: Column(
        children: [
          if (dirty)
            Material(
              color: scheme.primaryContainer,
              child: SafeArea(
                bottom: false,
                child: Padding(
                  padding: EdgeInsets.symmetric(
                    horizontal: tokens.spaceMd,
                    vertical: tokens.spaceSm,
                  ),
                  child: Row(
                    children: [
                      Icon(
                        Icons.edit_note_rounded,
                        color: scheme.onPrimaryContainer,
                      ),
                      SizedBox(width: tokens.spaceSm),
                      Expanded(
                        child: Text(
                          'CAMBIOS SIN GUARDAR',
                          style:
                              Theme.of(context).textTheme.labelLarge?.copyWith(
                                    color: scheme.onPrimaryContainer,
                                    fontWeight: FontWeight.w700,
                                    letterSpacing: 0.6,
                                  ),
                        ),
                      ),
                      Material(
                        color: const Color(0xFF1A1A1A),
                        borderRadius: tokens.radiusMd,
                        child: InkWell(
                          borderRadius: tokens.radiusMd,
                          onTap: controller.preferencesSaving ? null : _discard,
                          child: SizedBox(
                            height: 40,
                            child: Padding(
                              padding: EdgeInsets.symmetric(
                                horizontal: tokens.spaceLg,
                              ),
                              child: Center(
                                child: Text(
                                  'DESCARTAR',
                                  style: Theme.of(context)
                                      .textTheme
                                      .labelLarge
                                      ?.copyWith(
                                        color: Colors.white,
                                        fontWeight: FontWeight.w800,
                                        letterSpacing: 1.2,
                                        fontSize: 12,
                                      ),
                                ),
                              ),
                            ),
                          ),
                        ),
                      ),
                      SizedBox(width: tokens.spaceXs),
                      Material(
                        color: scheme.primary,
                        borderRadius: tokens.radiusMd,
                        child: InkWell(
                          borderRadius: tokens.radiusMd,
                          onTap: controller.preferencesSaving ? null : _save,
                          child: SizedBox(
                            height: 40,
                            child: Padding(
                              padding: EdgeInsets.symmetric(
                                horizontal: tokens.spaceLg,
                              ),
                              child: Center(
                                child: controller.preferencesSaving
                                    ? SizedBox(
                                        width: 18,
                                        height: 18,
                                        child: CircularProgressIndicator(
                                          strokeWidth: 2,
                                          color: scheme.onPrimary,
                                        ),
                                      )
                                    : Text(
                                        'GUARDAR',
                                        style: Theme.of(context)
                                            .textTheme
                                            .labelLarge
                                            ?.copyWith(
                                              color: scheme.onPrimary,
                                              fontWeight: FontWeight.w800,
                                              letterSpacing: 1.2,
                                              fontSize: 12,
                                            ),
                                      ),
                              ),
                            ),
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ),
          Expanded(child: _buildBody(context)),
        ],
      ),
    );
  }

  Widget _buildBody(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final tokens = Theme.of(context).appTokens;

    if (controller.isLoading && controller.categories.isEmpty) {
      return const AppCenteredLoader();
    }

    if (controller.error != null && controller.categories.isEmpty) {
      return Center(
        child: Padding(
          padding: EdgeInsets.all(tokens.spaceXl),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(Icons.error_outline_rounded, size: 48, color: scheme.error),
              SizedBox(height: tokens.spaceMd),
              Text(
                'No se pudieron cargar',
                style: Theme.of(context).textTheme.titleMedium?.copyWith(
                      fontWeight: FontWeight.w700,
                    ),
              ),
              SizedBox(height: tokens.spaceSm),
              Text(
                controller.error!,
                style: Theme.of(context).textTheme.bodySmall?.copyWith(
                      color: scheme.onSurfaceVariant,
                    ),
                textAlign: TextAlign.center,
              ),
              SizedBox(height: tokens.spaceLg),
              AppButton(
                label: 'REINTENTAR',
                icon: Icons.refresh_rounded,
                onPressed: () => controller.loadLeads(forceRefresh: true),
              ),
            ],
          ),
        ),
      );
    }

    if (controller.categories.isEmpty) {
      return Center(
        child: Text(
          'No hay indicadores disponibles.',
          style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                color: scheme.onSurfaceVariant,
              ),
        ),
      );
    }

    final pinnedSet = _draftPinned.toSet();
    final excludedSet = _draftExcluded.toSet();
    final errorText = _localError;

    return ListView(
      padding: EdgeInsets.fromLTRB(
        tokens.spaceXl,
        tokens.spaceMd,
        tokens.spaceXl,
        tokens.spaceXl * 1.5,
      ),
      children: [
        Text(
          'Explora por sección, exporta y fija u oculta indicadores. '
          'Guarda cuando termines de ajustar.',
          style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                color: scheme.onSurfaceVariant,
              ),
        ),
        SizedBox(height: tokens.spaceSm),
        Text(
          'FIJADOS: ${_draftPinned.length} / 5',
          style: Theme.of(context).textTheme.labelLarge?.copyWith(
                fontWeight: FontWeight.w700,
                letterSpacing: 0.6,
              ),
        ),
        if (errorText != null) ...[
          SizedBox(height: tokens.spaceSm),
          AppStatusBanner(
            title: 'Atención',
            message: errorText,
            tone: AppStatusBannerTone.warning,
            icon: Icons.info_outline_rounded,
          ),
        ],
        if (_draftPinned.isNotEmpty) ...[
          SizedBox(height: tokens.spaceLg),
          Text(
            'ORDEN EN INICIO',
            style: Theme.of(context).textTheme.labelLarge?.copyWith(
                  fontWeight: FontWeight.w700,
                  letterSpacing: 0.6,
                ),
          ),
          SizedBox(height: tokens.spaceSm),
          ReorderableListView.builder(
            shrinkWrap: true,
            physics: const NeverScrollableScrollPhysics(),
            buildDefaultDragHandles: false,
            itemCount: _draftPinned.length,
            onReorder: _movePinned,
            proxyDecorator: (child, index, animation) {
              return AnimatedBuilder(
                animation: animation,
                builder: (context, child) {
                  final t = Curves.easeInOut.transform(animation.value);
                  return Material(
                    elevation: 2 + 4 * t,
                    borderRadius: tokens.radiusLg,
                    color: scheme.surfaceContainerHighest,
                    child: child,
                  );
                },
                child: child,
              );
            },
            itemBuilder: (context, index) {
              final id = _draftPinned[index];
              LeadItem? lead;
              for (final item in controller.allLeads) {
                if (item.id == id) {
                  lead = item;
                  break;
                }
              }
              return Padding(
                key: ValueKey(id),
                padding: EdgeInsets.only(bottom: tokens.spaceSm),
                child: AppEntityRowCard(
                  title: lead?.title ?? id,
                  subtitle: 'Posición ${index + 1} · Arrastra el asa',
                  leading: ReorderableDragStartListener(
                    index: index,
                    child: Padding(
                      padding: const EdgeInsets.all(4),
                      child: Icon(
                        Icons.drag_handle_rounded,
                        size: 28,
                        color: scheme.onSurface,
                      ),
                    ),
                  ),
                  trailing: LeadActionIcon(
                    icon: Icons.push_pin_rounded,
                    color: scheme.primary,
                    tooltip: 'Quitar fijado',
                    onPressed: () => _togglePin(id),
                  ),
                ),
              );
            },
          ),
        ],
        SizedBox(height: tokens.spaceLg),
        for (var i = 0; i < controller.categories.length; i++)
          LeadCategorySection(
            category: controller.categories[i],
            initiallyExpanded: i == 0,
            pinnedIds: pinnedSet,
            excludedIds: excludedSet,
            onTogglePin: _togglePin,
            onToggleExcluded: _toggleExcluded,
            onLeadTap: (lead) => showLeadDetailSheet(
              context,
              lead: lead,
              pinned: pinnedSet.contains(lead.id),
              onExport: () => controller.exportSingle(lead.id),
            ),
          ),
      ],
    );
  }
}
