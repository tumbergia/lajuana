import 'package:flutter/material.dart';
import 'package:mobile_ui/mobile_ui.dart';

import 'package:mobile/features/analytics/domain/analytics_models.dart';
import 'package:mobile/features/analytics/presentation/controllers/dashboard_controller.dart';
import 'package:mobile/features/analytics/presentation/widgets/insights/analytics_state_views.dart';
import 'package:mobile/features/analytics/presentation/widgets/lead_card.dart';
import 'package:mobile/features/analytics/presentation/widgets/lead_icons.dart';


String analyticsCategoryLabel(String categoryId) {
  switch (categoryId) {
    case 'reservations':
      return 'Reservas';
    case 'money':
      return 'Dinero';
    case 'experiences':
      return 'Experiencias';
    case 'participants':
      return 'Participantes';
    case 'operations':
      return 'Operaciones';
    case 'equines':
      return 'Equinos';
    case 'action':
      return 'Acción';
    default:
      return categoryId;
  }
}

IconData analyticsCategoryIcon(String categoryId) {
  switch (categoryId) {
    case 'reservations':
      return leadIconFor('calendar_today');
    case 'money':
      return leadIconFor('payments');
    case 'experiences':
      return leadIconFor('star');
    case 'participants':
      return leadIconFor('public');
    case 'operations':
      return leadIconFor('percent');
    case 'equines':
      return leadIconFor('pets');
    case 'action':
      return leadIconFor('priority_high');
    default:
      return leadIconFor('bar_chart');
  }
}

IconData analyticsModuleIcon(String moduleId) {
  switch (moduleId) {
    case 'reservation_trend':
      return leadIconFor('trending_up');
    case 'reservation_status':
      return leadIconFor('pie_chart');
    case 'confirmed_value_trend':
      return leadIconFor('monetization_on');
    case 'payment_status':
      return leadIconFor('receipt');
    case 'top_experiences':
      return leadIconFor('emoji_events');
    case 'top_countries':
      return leadIconFor('public');
    case 'occupancy':
      return leadIconFor('percent');
    case 'participant_readiness':
      return leadIconFor('assignment_turned_in');
    case 'equine_availability':
      return leadIconFor('pets');
    case 'equine_workload':
      return leadIconFor('fitness_center');
    default:
      return leadIconFor('bar_chart');
  }
}

/// Configurar hasta 4 módulos — misma UX visual que AllLeadsScreen.
class ConfigureAnalyticsScreen extends StatefulWidget {
  const ConfigureAnalyticsScreen({super.key, required this.controller});

  final DashboardController controller;

  @override
  State<ConfigureAnalyticsScreen> createState() =>
      _ConfigureAnalyticsScreenState();
}

class _ConfigureAnalyticsScreenState extends State<ConfigureAnalyticsScreen> {
  List<String> _draft = [];
  String? _localError;
  bool _saving = false;

  @override
  void initState() {
    super.initState();
    _resetDraftFromController();
    widget.controller.addListener(_onControllerChanged);
  }

  @override
  void dispose() {
    widget.controller.removeListener(_onControllerChanged);
    super.dispose();
  }

  void _resetDraftFromController() {
    _draft = List<String>.from(widget.controller.homeModuleIds);
    _localError = null;
  }

  void _onControllerChanged() {
    if (!mounted) return;
    if (!_isDirty) {
      setState(_resetDraftFromController);
    } else {
      setState(() {});
    }
  }

  bool get _isDirty {
    final saved = widget.controller.homeModuleIds;
    if (_draft.length != saved.length) return true;
    for (var i = 0; i < _draft.length; i++) {
      if (_draft[i] != saved[i]) return true;
    }
    return false;
  }

  bool get _canAdd => _draft.length < AnalyticsPreferences.maxModules;

  List<CatalogModule> get _catalog => widget.controller.catalog
      .where((m) => m.homeConfigurable && !m.blocked)
      .toList(growable: false);

  CatalogModule? _find(String id) {
    for (final c in _catalog) {
      if (c.id == id) return c;
    }
    return null;
  }

  void _togglePin(String id) {
    setState(() {
      _localError = null;
      if (_draft.contains(id)) {
        _draft.remove(id);
      } else {
        if (!_canAdd) {
          _localError =
              'Solo puedes fijar hasta ${AnalyticsPreferences.maxModules} indicadores.';
          return;
        }
        _draft.add(id);
      }
    });
  }

  void _movePinned(int oldIndex, int newIndex) {
    setState(() {
      if (newIndex > oldIndex) newIndex -= 1;
      final item = _draft.removeAt(oldIndex);
      _draft.insert(newIndex, item);
    });
  }

  void _discard() => setState(_resetDraftFromController);

  Future<void> _save() async {
    setState(() => _saving = true);
    try {
      await widget.controller.savePreferences(
        AnalyticsPreferences(
          selectedModuleIds: List.unmodifiable(_draft),
          moduleOrder: List.unmodifiable(_draft),
          defaultRange: widget.controller.range,
        ),
      );
      if (!mounted) return;
      setState(() {
        _saving = false;
        _resetDraftFromController();
      });
      showAppToast(context, message: 'Preferencias guardadas');
      Navigator.of(context).pop();
    } catch (_) {
      if (!mounted) return;
      setState(() {
        _saving = false;
        _localError = 'No pudimos guardar la configuración.';
      });
      showAppToast(context, message: _localError!, isError: true);
    }
  }

  Future<void> _restoreDefaults() async {
    await widget.controller.restoreDefaults();
    if (!mounted) return;
    setState(_resetDraftFromController);
    showAppToast(context, message: 'Valores sugeridos restaurados');
  }

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final tokens = Theme.of(context).appTokens;
    final dirty = _isDirty;

    return Scaffold(
      appBar: const AppPageAppBar(title: 'Configurar indicadores'),
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
                        color: scheme.inverseSurface,
                        borderRadius: tokens.radiusMd,
                        child: InkWell(
                          borderRadius: tokens.radiusMd,
                          onTap: _saving ? null : _discard,
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
                                        color: scheme.onInverseSurface,
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
                          onTap: _saving ? null : _save,
                          child: SizedBox(
                            height: 40,
                            child: Padding(
                              padding: EdgeInsets.symmetric(
                                horizontal: tokens.spaceLg,
                              ),
                              child: Center(
                                child: _saving
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
    final catalog = _catalog;

    if (catalog.isEmpty) {
      return AnalyticsEmptyView(
        title: 'Sin indicadores disponibles',
        message:
            'No hay módulos configurables para tu rol en este momento.',
        icon: Icons.tune_rounded,
      );
    }

    final byCategory = <String, List<CatalogModule>>{};
    for (final m in catalog) {
      byCategory.putIfAbsent(m.category, () => []).add(m);
    }
    const categoryOrder = [
      'reservations',
      'money',
      'experiences',
      'participants',
      'operations',
      'equines',
      'action',
    ];
    final sortedCats = [
      ...categoryOrder.where(byCategory.containsKey),
      ...byCategory.keys.where((k) => !categoryOrder.contains(k)),
    ];
    final pinnedSet = _draft.toSet();

    return ListView(
      padding: EdgeInsets.fromLTRB(
        tokens.spaceXl,
        tokens.spaceMd,
        tokens.spaceXl,
        tokens.spaceXl * 1.5,
      ),
      children: [
        AppSectionHeader(
          eyebrow: 'Preferencias',
          title: 'Indicadores en Inicio',
          subtitle:
              'Fija hasta ${AnalyticsPreferences.maxModules} indicadores. '
              'Guarda cuando termines de ajustar.',
          variant: AppSectionHeaderVariant.compact,
        ),
        SizedBox(height: tokens.spaceLg),
        Text(
          'FIJADOS: ${_draft.length} / ${AnalyticsPreferences.maxModules}',
          style: Theme.of(context).textTheme.labelLarge?.copyWith(
                fontWeight: FontWeight.w700,
                letterSpacing: 0.6,
              ),
        ),
        if (_localError != null) ...[
          SizedBox(height: tokens.spaceSm),
          AppStatusBanner(
            title: 'Atención',
            message: _localError!,
            tone: AppStatusBannerTone.warning,
            icon: Icons.info_outline_rounded,
          ),
        ],
        if (_draft.isNotEmpty) ...[
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
            itemCount: _draft.length,
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
              final id = _draft[index];
              final mod = _find(id);
              final chip = analyticsDomainChipColors(
                context,
                mod?.category ?? '',
              );
              return Padding(
                key: ValueKey(id),
                padding: EdgeInsets.only(bottom: tokens.spaceSm),
                child: AppEntityRowCard(
                  title: mod?.title ?? id,
                  subtitle: 'Posición ${index + 1} · Arrastra el asa',
                  accentColor: chip.background,
                  badge: const AppBadge(
                    label: 'FIJO',
                    tone: AppBadgeTone.primary,
                    size: AppBadgeSize.sm,
                  ),
                  leading: ReorderableDragStartListener(
                    index: index,
                    child: Container(
                      width: 40,
                      height: 40,
                      decoration: BoxDecoration(
                        color: chip.background,
                        borderRadius: tokens.radiusMd,
                      ),
                      child: Icon(
                        Icons.drag_handle_rounded,
                        size: 22,
                        color: chip.foreground,
                      ),
                    ),
                  ),
                  trailing: LeadActionIcon(
                    icon: Icons.push_pin_rounded,
                    color: chip.background,
                    tooltip: 'Quitar fijado',
                    onPressed: () => _togglePin(id),
                  ),
                ),
              );
            },
          ),
        ],
        SizedBox(height: tokens.spaceLg),
        for (var i = 0; i < sortedCats.length; i++)
          _ConfigureCategorySection(
            categoryId: sortedCats[i],
            modules: byCategory[sortedCats[i]]!,
            pinnedIds: pinnedSet,
            canAdd: _canAdd,
            initiallyExpanded: i == 0,
            onTogglePin: _togglePin,
          ),
        SizedBox(height: tokens.spaceLg),
        AppButton(
          label: 'Restaurar valores sugeridos',
          variant: AppButtonVariant.ghost,
          onPressed: _saving ? null : _restoreDefaults,
          expanded: true,
        ),
      ],
    );
  }
}

/// Expandable colored section — mirrors [LeadCategorySection].
class _ConfigureCategorySection extends StatefulWidget {
  const _ConfigureCategorySection({
    required this.categoryId,
    required this.modules,
    required this.pinnedIds,
    required this.canAdd,
    required this.onTogglePin,
    this.initiallyExpanded = false,
  });

  final String categoryId;
  final List<CatalogModule> modules;
  final Set<String> pinnedIds;
  final bool canAdd;
  final void Function(String id) onTogglePin;
  final bool initiallyExpanded;

  @override
  State<_ConfigureCategorySection> createState() =>
      _ConfigureCategorySectionState();
}

class _ConfigureCategorySectionState extends State<_ConfigureCategorySection> {
  late bool _expanded = widget.initiallyExpanded;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final tokens = Theme.of(context).appTokens;
    final chip = analyticsDomainChipColors(context, widget.categoryId);
    final accent = chip.background;
    final radius = tokens.radiusLg;

    return Padding(
      padding: EdgeInsets.only(bottom: tokens.spaceMd),
      child: DecoratedBox(
        decoration: BoxDecoration(
          color: scheme.surfaceContainerLow,
          borderRadius: radius,
          border: Border.all(
            color: scheme.outlineVariant.withValues(alpha: 0.4),
          ),
        ),
        child: ClipRRect(
          borderRadius: radius,
          child: Stack(
            children: [
              Positioned(
                left: 0,
                top: 0,
                bottom: 0,
                width: 4,
                child: ColoredBox(color: accent),
              ),
              Padding(
                padding: const EdgeInsets.only(left: 4),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Material(
                      color: scheme.surfaceContainer,
                      child: InkWell(
                        onTap: () => setState(() => _expanded = !_expanded),
                        child: Padding(
                          padding: EdgeInsets.symmetric(
                            vertical: tokens.spaceMd,
                            horizontal: tokens.spaceLg,
                          ),
                          child: Row(
                            children: [
                              Container(
                                width: 40,
                                height: 40,
                                decoration: BoxDecoration(
                                  color: accent,
                                  borderRadius: tokens.radiusMd,
                                ),
                                child: Icon(
                                  analyticsCategoryIcon(widget.categoryId),
                                  size: 20,
                                  color: chip.foreground,
                                ),
                              ),
                              SizedBox(width: tokens.spaceMd),
                              Expanded(
                                child: Text(
                                  analyticsCategoryLabel(widget.categoryId)
                                      .toUpperCase(),
                                  style: Theme.of(context)
                                      .textTheme
                                      .titleSmall
                                      ?.copyWith(
                                        fontWeight: FontWeight.w800,
                                        letterSpacing: 0.6,
                                        color: scheme.onSurface,
                                      ),
                                ),
                              ),
                              AppBadge(
                                label: '${widget.modules.length}',
                                tone: AppBadgeTone.neutral,
                                size: AppBadgeSize.sm,
                                uppercase: false,
                              ),
                              SizedBox(width: tokens.spaceSm),
                              AnimatedRotation(
                                turns: _expanded ? 0.5 : 0,
                                duration: const Duration(milliseconds: 160),
                                curve: Curves.easeOutCubic,
                                child: Icon(
                                  Icons.keyboard_arrow_down_rounded,
                                  size: 22,
                                  color: scheme.onSurfaceVariant,
                                ),
                              ),
                            ],
                          ),
                        ),
                      ),
                    ),
                    if (_expanded)
                      Padding(
                        padding: EdgeInsets.fromLTRB(
                          tokens.spaceMd,
                          tokens.spaceSm,
                          tokens.spaceMd,
                          tokens.spaceMd,
                        ),
                        child: Column(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            for (final mod in widget.modules)
                              Padding(
                                padding:
                                    EdgeInsets.only(bottom: tokens.spaceSm),
                                child: _ModuleConfigRow(
                                  module: mod,
                                  accent: accent,
                                  pinned: widget.pinnedIds.contains(mod.id),
                                  canPin: widget.canAdd ||
                                      widget.pinnedIds.contains(mod.id),
                                  onTogglePin: () =>
                                      widget.onTogglePin(mod.id),
                                ),
                              ),
                          ],
                        ),
                      ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

/// Row styled like [LeadCard]: colored chip, title, pin action.
class _ModuleConfigRow extends StatelessWidget {
  const _ModuleConfigRow({
    required this.module,
    required this.accent,
    required this.pinned,
    required this.canPin,
    required this.onTogglePin,
  });

  final CatalogModule module;
  final Color accent;
  final bool pinned;
  final bool canPin;
  final VoidCallback onTogglePin;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final tokens = Theme.of(context).appTokens;
    final iconFg = analyticsAccentForeground(accent);

    return AppEntityRowCard(
      title: module.title,
      subtitle: module.description,
      wrapTitle: true,
      accentColor: pinned ? accent : null,
      badge: pinned
          ? const AppBadge(
              label: 'FIJO',
              tone: AppBadgeTone.primary,
              size: AppBadgeSize.sm,
            )
          : null,
      leading: Container(
        width: 40,
        height: 40,
        decoration: BoxDecoration(
          color: accent,
          borderRadius: tokens.radiusMd,
        ),
        child: Icon(
          analyticsModuleIcon(module.id),
          size: 22,
          color: iconFg,
        ),
      ),
      trailing: LeadActionIcon(
        icon: pinned ? Icons.push_pin_rounded : Icons.push_pin_outlined,
        color: pinned
            ? accent
            : (canPin ? scheme.onSurfaceVariant : scheme.outline),
        tooltip: pinned ? 'Quitar fijado' : 'Fijar en Inicio',
        onPressed: canPin ? onTogglePin : () {},
      ),
    );
  }
}
