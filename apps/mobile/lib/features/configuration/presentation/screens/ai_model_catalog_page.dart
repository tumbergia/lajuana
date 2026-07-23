import 'package:flutter/material.dart';
import 'package:material_symbols_icons/material_symbols_icons.dart';
import 'package:url_launcher/url_launcher.dart';

import 'package:mobile/features/configuration/configuration_module.dart';
import 'package:mobile/features/configuration/domain/ai_model_catalog.dart';
import 'package:mobile/features/configuration/infrastructure/configuration_api_client.dart';
import 'package:mobile/features/configuration/presentation/utils/ai_cost_estimate.dart';
import 'package:mobile_ui/src/theme/theme_extensions.dart';
import 'package:mobile_ui/src/widgets/app_button.dart';
import 'package:mobile_ui/src/widgets/app_card.dart';
import 'package:mobile_ui/src/widgets/app_centered_loader.dart';
import 'package:mobile_ui/src/widgets/app_entity_row_card.dart';
import 'package:mobile_ui/src/widgets/app_section_header.dart';
import 'package:mobile_ui/src/widgets/app_status_banner.dart';
import 'package:mobile_ui/src/widgets/app_text_field.dart';
import 'package:mobile_ui/src/widgets/app_toast.dart';
import 'package:mobile_ui/src/widgets/refresh_scope.dart';

/// Resultado al elegir un modelo desde el catálogo de precios.
class AiModelSelection {
  const AiModelSelection({required this.modelId, required this.displayName});

  final String modelId;
  final String displayName;
}

class AiModelCatalogPage extends StatefulWidget {
  const AiModelCatalogPage({super.key, required this.module});

  final LaJuanaConfigurationModule module;

  @override
  State<AiModelCatalogPage> createState() => _AiModelCatalogPageState();
}

class _AiModelCatalogPageState extends State<AiModelCatalogPage>
    with RefreshableState {
  AiModelCatalog? _catalog;
  bool _loading = true;
  String? _loadError;

  /// true = COP mensual; false = USD por millón.
  bool _showCop = true;
  AiLoadConfig _load = AiLoadConfig.defaults;

  late final TextEditingController _peopleCtrl;
  late final TextEditingController _msgsPerDayCtrl;
  late final TextEditingController _daysCtrl;

  static const _providerLabels = {
    'google': 'Google',
    'anthropic': 'Anthropic',
    'openai': 'OpenAI',
    'groq': 'Groq',
    'openrouter': 'OpenRouter',
  };

  @override
  Future<void> onRefresh() => _loadCatalog();

  @override
  void initState() {
    super.initState();
    _peopleCtrl = TextEditingController(text: '${_load.people}');
    _msgsPerDayCtrl = TextEditingController(
      text: '${_load.messagesPerPersonPerDay}',
    );
    _daysCtrl = TextEditingController(text: '${_load.daysPerMonth}');
    _loadCatalog();
  }

  @override
  void dispose() {
    _peopleCtrl.dispose();
    _msgsPerDayCtrl.dispose();
    _daysCtrl.dispose();
    super.dispose();
  }

  void _applyPreset(AiLoadPreset preset) {
    final next = AiLoadConfig.fromPreset(preset);
    setState(() {
      _load = next;
      _peopleCtrl.text = '${next.people}';
      _msgsPerDayCtrl.text = '${next.messagesPerPersonPerDay}';
      _daysCtrl.text = '${next.daysPerMonth}';
    });
  }

  void _syncLoadFromFields() {
    final people = int.tryParse(_peopleCtrl.text.trim()) ?? _load.people;
    final msgs =
        int.tryParse(_msgsPerDayCtrl.text.trim()) ??
        _load.messagesPerPersonPerDay;
    final days = int.tryParse(_daysCtrl.text.trim()) ?? _load.daysPerMonth;
    setState(() {
      _load = AiLoadConfig(
        people: people.clamp(1, 100000),
        messagesPerPersonPerDay: msgs.clamp(1, 1000),
        daysPerMonth: days.clamp(1, 366),
      );
    });
  }

  Future<void> _loadCatalog() async {
    setState(() {
      _loadError = null;
      if (_catalog == null) _loading = true;
    });
    try {
      final catalog = await widget.module.api.getModelCatalog();
      if (!mounted) return;
      setState(() {
        _catalog = catalog;
        _loading = false;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _loadError = e is ConfigurationApiFailure
            ? e.message
            : 'No se pudo cargar el catálogo de modelos.';
        _loading = false;
      });
    }
  }

  Future<void> _openBuyKey(String url) async {
    final uri = Uri.tryParse(url);
    if (uri == null) {
      showAppToast(context, message: 'Enlace no válido.');
      return;
    }
    final ok = await launchUrl(uri, mode: LaunchMode.externalApplication);
    if (!ok && mounted) {
      showAppToast(context, message: 'No se pudo abrir el enlace.');
    }
  }

  void _selectModel(AiModelItem item) {
    Navigator.of(context).pop(
      AiModelSelection(modelId: item.modelId, displayName: item.displayName),
    );
  }

  Color _brandOf(AiModelItem item) => item.brandColorValue;

  Color _brandForProvider(String provider) {
    final catalog = _catalog;
    if (catalog != null) return catalog.brandColorFor(provider);
    return const Color(0xFF5B5B5B);
  }

  Widget _sectionTitle(BuildContext context, String text, {Color? accent}) {
    final theme = Theme.of(context);
    return Row(
      children: [
        if (accent != null) ...[
          Container(
            width: 8,
            height: 8,
            decoration: BoxDecoration(
              color: accent,
              borderRadius: BorderRadius.circular(2),
            ),
          ),
          const SizedBox(width: 8),
        ],
        Expanded(
          child: Text(
            text.toUpperCase(),
            style: theme.textTheme.labelLarge?.copyWith(
              color: theme.colorScheme.onSurfaceVariant,
              fontWeight: FontWeight.w800,
              letterSpacing: 1.4,
            ),
          ),
        ),
      ],
    );
  }

  Widget _sectionHint(BuildContext context, String text) {
    return Text(
      text,
      style: Theme.of(context).textTheme.bodySmall?.copyWith(
        color: Theme.of(context).colorScheme.onSurfaceVariant,
      ),
    );
  }

  Widget _leadingIcon(IconData icon, {Color? brand}) {
    final scheme = Theme.of(context).colorScheme;
    final fill = brand?.withValues(alpha: 0.14) ?? scheme.surfaceContainerHighest;
    final iconColor = brand ?? scheme.onSurfaceVariant;
    return Container(
      width: 40,
      height: 40,
      alignment: Alignment.center,
      decoration: BoxDecoration(
        color: fill,
        borderRadius: BorderRadius.circular(4),
        border: brand == null
            ? null
            : Border.all(color: brand.withValues(alpha: 0.35)),
      ),
      child: Icon(icon, size: 22, color: iconColor),
    );
  }

  Widget _sectionCard(List<Widget> children, {Color? brand}) {
    return AppCard(
      tone: AppCardTone.surface,
      outlined: true,
      padding: const EdgeInsets.fromLTRB(14, 14, 14, 14),
      child: DecoratedBox(
        decoration: brand == null
            ? const BoxDecoration()
            : BoxDecoration(
                border: Border(
                  left: BorderSide(color: brand, width: 3),
                ),
              ),
        child: Padding(
          padding: brand == null
              ? EdgeInsets.zero
              : const EdgeInsets.only(left: 18),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: children,
          ),
        ),
      ),
    );
  }

  Widget _brandBadge(BuildContext context, String label, Color brand) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
      decoration: BoxDecoration(
        color: brand.withValues(alpha: 0.14),
        borderRadius: BorderRadius.circular(2),
        border: Border.all(color: brand.withValues(alpha: 0.4)),
      ),
      child: Text(
        label.toUpperCase(),
        style: Theme.of(context).textTheme.labelSmall?.copyWith(
          color: brand,
          fontWeight: FontWeight.w800,
          letterSpacing: 0.6,
        ),
      ),
    );
  }

  Widget _recommendedBadge(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
      decoration: BoxDecoration(
        color: scheme.primary,
        borderRadius: BorderRadius.circular(2),
      ),
      child: Text(
        'RECOMENDADO',
        style: Theme.of(context).textTheme.labelSmall?.copyWith(
          color: scheme.onPrimary,
          fontWeight: FontWeight.w800,
          letterSpacing: 0.6,
        ),
      ),
    );
  }

  Widget _starRow(BuildContext context, int level, {required Color color}) {
    final scheme = Theme.of(context).colorScheme;
    final clamped = level.clamp(1, 5);
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: List.generate(5, (i) {
        final filled = i < clamped;
        return Padding(
          padding: EdgeInsets.only(right: i < 4 ? 1 : 0),
          child: Icon(
            filled ? Icons.star_rounded : Icons.star_outline_rounded,
            size: 14,
            color: filled
                ? color
                : scheme.outlineVariant.withValues(alpha: 0.7),
          ),
        );
      }),
    );
  }

  Widget _ratingLine(
    BuildContext context, {
    required String label,
    required int level,
    required Color color,
  }) {
    final scheme = Theme.of(context).colorScheme;
    return Row(
      children: [
        SizedBox(
          width: 92,
          child: Text(
            label.toUpperCase(),
            style: Theme.of(context).textTheme.labelSmall?.copyWith(
              color: scheme.onSurfaceVariant,
              fontWeight: FontWeight.w700,
              letterSpacing: 0.6,
            ),
          ),
        ),
        _starRow(context, level, color: color),
      ],
    );
  }

  String _priceSubtitle(AiModelItem item) {
    if (_showCop) {
      final monthly = AiCostEstimate.monthlyCop(item, _load);
      if (monthly == null) return 'Precio no disponible';
      return '${AiCostEstimate.formatCop(monthly)} / mes · ${_load.summaryLabel}';
    }
    final input = AiCostEstimate.formatUsdPerMillion(item.inputUsdPerMillion);
    final output = AiCostEstimate.formatUsdPerMillion(item.outputUsdPerMillion);
    final combined = AiCostEstimate.formatUsdPerMillion(
      item.combinedUsdPerMillion,
    );
    return 'In $input · Out $output · Comb $combined / 1M';
  }

  Widget _controlsSection(BuildContext context) {
    final tokens = Theme.of(context).appTokens;
    final scheme = Theme.of(context).colorScheme;
    final matched = _load.matchingPreset();
    return _sectionCard([
      _sectionTitle(context, 'Visualización'),
      SizedBox(height: tokens.spaceSm),
      _sectionHint(
        context,
        _showCop
            ? 'Estimado mensual en COP: personas × msgs/día × días '
                '(~${AiCostEstimate.tokensPerMessage} tokens/mensaje). '
                'Tasa ~${AiCostEstimate.usdToCop.toStringAsFixed(0)} COP/USD. '
                'Informativo; valida siempre contra el proveedor.'
            : 'USD por millón de tokens. Combinado = 1M entrada + 1M salida. '
                'Pueden diferir de los reales; valida siempre contra el proveedor.',
      ),
      SizedBox(height: tokens.spaceMd),
      Row(
        children: [
          Expanded(
            child: AppEntityRowCard(
              title: 'USD',
              subtitle: 'Por millón de tokens',
              leading: _leadingIcon(Symbols.attach_money),
              selected: !_showCop,
              trailing: Icon(
                !_showCop ? Icons.check_circle_rounded : Icons.circle_outlined,
                size: 22,
                color: !_showCop ? scheme.primary : scheme.outlineVariant,
              ),
              onTap: () => setState(() => _showCop = false),
            ),
          ),
          SizedBox(width: tokens.spaceSm),
          Expanded(
            child: AppEntityRowCard(
              title: 'COP',
              subtitle: 'Estimado mensual',
              leading: _leadingIcon(Symbols.payments),
              selected: _showCop,
              trailing: Icon(
                _showCop ? Icons.check_circle_rounded : Icons.circle_outlined,
                size: 22,
                color: _showCop ? scheme.primary : scheme.outlineVariant,
              ),
              onTap: () => setState(() => _showCop = true),
            ),
          ),
        ],
      ),
      if (_showCop) ...[
        SizedBox(height: tokens.spaceXl),
        _sectionTitle(context, 'Carga'),
        SizedBox(height: tokens.spaceSm),
        _sectionHint(
          context,
          'Atajos o valores a medida. Total: ${_load.messagesPerMonth} msgs/mes.',
        ),
        SizedBox(height: tokens.spaceMd),
        for (final preset in AiLoadPreset.values) ...[
          AppEntityRowCard(
            title: preset.label,
            subtitle:
                '${preset.people} personas · ${preset.messagesPerPersonPerDay} msgs/día',
            leading: _leadingIcon(
              preset == AiLoadPreset.max
                  ? Symbols.groups
                  : preset == AiLoadPreset.high
                  ? Symbols.group
                  : Symbols.person,
            ),
            selected: matched == preset,
            trailing: Icon(
              matched == preset
                  ? Icons.check_circle_rounded
                  : Icons.circle_outlined,
              size: 22,
              color: matched == preset
                  ? scheme.primary
                  : scheme.outlineVariant,
            ),
            onTap: () => _applyPreset(preset),
          ),
          if (preset != AiLoadPreset.values.last)
            SizedBox(height: tokens.spaceSm),
        ],
        SizedBox(height: tokens.spaceXl),
        _sectionTitle(context, 'Personalizar'),
        SizedBox(height: tokens.spaceSm),
        AppTextField(
          controller: _peopleCtrl,
          label: 'Personas / clientes',
          inputKind: AppTextInputKind.integer,
          onChanged: (_) => _syncLoadFromFields(),
        ),
        SizedBox(height: tokens.spaceSm),
        AppTextField(
          controller: _msgsPerDayCtrl,
          label: 'Mensajes por día (por cliente)',
          inputKind: AppTextInputKind.integer,
          onChanged: (_) => _syncLoadFromFields(),
        ),
        SizedBox(height: tokens.spaceSm),
        AppTextField(
          controller: _daysCtrl,
          label: 'Días del mes',
          inputKind: AppTextInputKind.integer,
          onChanged: (_) => _syncLoadFromFields(),
        ),
        SizedBox(height: tokens.spaceSm),
        AppEntityRowCard(
          title: 'Resumen',
          subtitle: _load.summaryLabel,
          leading: _leadingIcon(Symbols.calculate),
        ),
      ],
    ]);
  }

  Widget _providerKeysSection(BuildContext context, AiModelCatalog catalog) {
    final tokens = Theme.of(context).appTokens;
    final urls = Map<String, String>.from(catalog.providerBuyUrls);
    final openRouterUrl =
        urls['openrouter'] ?? 'https://openrouter.ai/keys';

    // OpenRouter primero; luego providers nativos.
    final nativeOrder = ['google', 'anthropic', 'openai', 'groq'];
    final nativeEntries = <MapEntry<String, String>>[];
    for (final key in nativeOrder) {
      final url = urls[key];
      if (url != null && url.isNotEmpty) {
        nativeEntries.add(MapEntry(key, url));
      }
    }

    return _sectionCard([
      _sectionTitle(context, 'API keys'),
      SizedBox(height: tokens.spaceSm),
      _sectionHint(
        context,
        'Para usar un modelo de esta lista necesitas una API key. '
        'Lo más simple es OpenRouter: una sola key sirve para todos. '
        'También puedes usar la API key directa de cada marca si lo prefieres.',
      ),
      SizedBox(height: tokens.spaceMd),
      _sectionTitle(context, 'Opción simple · todos los modelos'),
      SizedBox(height: tokens.spaceSm),
      AppEntityRowCard(
        title: 'OpenRouter',
        subtitle: 'Una API key para Gemini, Claude, GPT y Groq',
        leading: _leadingIcon(
          Symbols.verified,
          brand: _brandForProvider('openrouter'),
        ),
        trailing: const Icon(Icons.open_in_new_rounded, size: 18),
        onTap: () => _openBuyKey(openRouterUrl),
      ),
      SizedBox(height: tokens.spaceSm),
      AppButton(
        label: 'Obtener API key de OpenRouter',
        icon: Icons.open_in_new_rounded,
        expanded: true,
        onPressed: () => _openBuyKey(openRouterUrl),
      ),
      if (nativeEntries.isNotEmpty) ...[
        SizedBox(height: tokens.spaceXl),
        _sectionTitle(context, 'Opción por marca'),
        SizedBox(height: tokens.spaceSm),
        _sectionHint(
          context,
          'Si ya tienes API key de Google, OpenAI u otra marca, '
          'puedes usarla en “Modelos personalizados”. '
          'Claude solo funciona con OpenRouter en esta app.',
        ),
        SizedBox(height: tokens.spaceMd),
        for (var i = 0; i < nativeEntries.length; i++) ...[
          AppEntityRowCard(
            title: _providerLabels[nativeEntries[i].key] ??
                nativeEntries[i].key,
            subtitle: 'API key directa de la marca',
            leading: _leadingIcon(
              Symbols.storefront,
              brand: _brandForProvider(nativeEntries[i].key),
            ),
            trailing: const Icon(Icons.open_in_new_rounded, size: 18),
            onTap: () => _openBuyKey(nativeEntries[i].value),
          ),
          if (i < nativeEntries.length - 1)
            SizedBox(height: tokens.spaceSm),
        ],
      ],
    ]);
  }

  Widget _modelCard(
    BuildContext context,
    AiModelItem item, {
    required String openRouterUrl,
  }) {
    final tokens = Theme.of(context).appTokens;
    final scheme = Theme.of(context).colorScheme;
    final brand = _brandOf(item);
    final providerLabel =
        _providerLabels[item.provider] ?? item.provider.toUpperCase();
    final providerKeyUrl = item.buyKeyUrl.trim();

    return _sectionCard([
      Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _leadingIcon(Symbols.psychology, brand: brand),
          SizedBox(width: tokens.spaceMd),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  item.displayName.toUpperCase(),
                  style: Theme.of(context).textTheme.titleSmall?.copyWith(
                    fontWeight: FontWeight.w800,
                    letterSpacing: 0.4,
                  ),
                ),
                SizedBox(height: tokens.spaceXs),
                Wrap(
                  spacing: 6,
                  runSpacing: 6,
                  crossAxisAlignment: WrapCrossAlignment.center,
                  children: [
                    _brandBadge(context, providerLabel, brand),
                    if (item.recommended) _recommendedBadge(context),
                  ],
                ),
              ],
            ),
          ),
        ],
      ),
      if (item.valueNote.isNotEmpty) ...[
        SizedBox(height: tokens.spaceSm),
        Text(
          item.valueNote,
          style: Theme.of(context).textTheme.bodySmall?.copyWith(
            color: scheme.onSurfaceVariant,
          ),
        ),
      ],
      SizedBox(height: tokens.spaceMd),
      _ratingLine(
        context,
        label: 'Inteligencia',
        level: item.intelligence,
        color: brand,
      ),
      SizedBox(height: tokens.spaceXs),
      _ratingLine(
        context,
        label: 'Velocidad',
        level: item.speed,
        color: brand,
      ),
      SizedBox(height: tokens.spaceMd),
      AppEntityRowCard(
        title: _showCop ? 'Costo estimado' : 'Precio',
        subtitle: _priceSubtitle(item),
        leading: _leadingIcon(
          _showCop ? Symbols.payments : Symbols.attach_money,
          brand: brand,
        ),
      ),
      SizedBox(height: tokens.spaceMd),
      AppButton(
        label: 'Usar este modelo',
        icon: Icons.check_rounded,
        expanded: true,
        onPressed: () => _selectModel(item),
      ),
      SizedBox(height: tokens.spaceSm),
      AppButton(
        label: 'API key OpenRouter',
        icon: Icons.open_in_new_rounded,
        expanded: true,
        variant: AppButtonVariant.secondary,
        onPressed: () => _openBuyKey(openRouterUrl),
      ),
      if (providerKeyUrl.isNotEmpty) ...[
        SizedBox(height: tokens.spaceSm),
        AppButton(
          label: 'API key $providerLabel',
          icon: Icons.open_in_new_rounded,
          expanded: true,
          variant: AppButtonVariant.ghost,
          onPressed: () => _openBuyKey(providerKeyUrl),
        ),
      ],
    ], brand: brand);
  }

  List<Widget> _buildModelSections(
    BuildContext context,
    AiModelCatalog catalog,
  ) {
    final tokens = Theme.of(context).appTokens;
    final openRouterUrl =
        catalog.providerBuyUrls['openrouter'] ?? 'https://openrouter.ai/keys';
    final recommended = catalog.items.where((i) => i.recommended).toList()
      ..sort((a, b) => a.sortOrder.compareTo(b.sortOrder));
    final rest = catalog.items.where((i) => !i.recommended).toList()
      ..sort((a, b) => a.sortOrder.compareTo(b.sortOrder));

    final children = <Widget>[];

    if (recommended.isNotEmpty) {
      children.add(_sectionTitle(context, 'Recomendados'));
      children.add(SizedBox(height: tokens.spaceSm));
      children.add(
        _sectionHint(
          context,
          'Llama 3.1 8B: máxima economía. '
          'Gemini 3.1 Flash-Lite: mejor calidad/precio. '
          'Claude Haiku 4.5: velocidad y calidad, precio más alto.',
        ),
      );
      children.add(SizedBox(height: tokens.spaceLg));
      for (final item in recommended) {
        children.add(
          _modelCard(context, item, openRouterUrl: openRouterUrl),
        );
        children.add(SizedBox(height: tokens.spaceLg));
      }
      children.add(SizedBox(height: tokens.spaceMd));
    }

    if (rest.isNotEmpty) {
      children.add(_sectionTitle(context, 'Todos · por precio'));
      children.add(SizedBox(height: tokens.spaceSm));
      children.add(
        _sectionHint(
          context,
          'Ordenados por costo combinado (1M entrada + 1M salida), de menor a mayor. '
          'El color identifica la marca.',
        ),
      );
      children.add(SizedBox(height: tokens.spaceLg));
      for (final item in rest) {
        children.add(
          _modelCard(context, item, openRouterUrl: openRouterUrl),
        );
        children.add(SizedBox(height: tokens.spaceLg));
      }
    }

    return children;
  }

  @override
  Widget build(BuildContext context) {
    final catalog = _catalog;
    return Padding(
      padding: const EdgeInsets.fromLTRB(24, 24, 24, 24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          AppSectionHeader(
            eyebrow: 'Configuración de IA',
            title: 'Precios y modelos',
            subtitle:
                'Compara qué tan inteligente, rápido y costoso es cada modelo. '
                'Al elegir uno, lo activas con una API key de OpenRouter.',
            trailing: AppButton(
              label: 'Volver',
              icon: Icons.arrow_back_rounded,
              variant: AppButtonVariant.ghost,
              onPressed: () => Navigator.pop(context),
            ),
          ),
          const SizedBox(height: 12),
          Expanded(
            child: _loading
                ? const RefreshableViewport(child: AppCenteredLoader())
                : ListView(
                    physics: const AlwaysScrollableScrollPhysics(),
                    children: [
                      if (_loadError != null) ...[
                        AppStatusBanner(
                          title: 'No se pudo cargar',
                          message: _loadError!,
                          tone: AppStatusBannerTone.danger,
                          icon: Icons.error_outline_rounded,
                        ),
                        const SizedBox(height: 12),
                        AppButton(
                          label: 'Reintentar',
                          expanded: true,
                          onPressed: _loadCatalog,
                        ),
                      ] else if (catalog != null) ...[
                        if (catalog.stale || catalog.warnings.isNotEmpty) ...[
                          AppStatusBanner(
                            title: catalog.stale
                                ? 'Precios desactualizados'
                                : 'Aviso',
                            message: catalog.warnings.isNotEmpty
                                ? catalog.warnings.first
                                : 'Se muestran datos en caché.',
                            tone: AppStatusBannerTone.warning,
                            icon: Icons.info_outline_rounded,
                          ),
                          const SizedBox(height: 12),
                        ],
                        _controlsSection(context),
                        const SizedBox(height: 28),
                        _providerKeysSection(context, catalog),
                        const SizedBox(height: 28),
                        ..._buildModelSections(context, catalog),
                      ],
                    ],
                  ),
          ),
        ],
      ),
    );
  }
}
