// ═════════════════════════════════════════════════════════════════════════════
// Widget Museum — Secret Page
// Shows ALL widgets with ALL possible info: constructors, params, enums, demos
// Route: /dev/widgets (AuthRoutes.widgetMuseum)
// ═════════════════════════════════════════════════════════════════════════════
import 'package:flutter/material.dart';

import '../../lib/app/theme/theme_extensions.dart';
import '../../lib/app/widgets/app_badge.dart';
import '../../lib/app/widgets/app_bottom_nav.dart';
import '../../lib/app/widgets/app_breadcrumb.dart';
import '../../lib/app/widgets/app_button.dart';
import '../../lib/app/widgets/app_card.dart';
import '../../lib/app/widgets/app_centered_loader.dart';
import '../../lib/app/widgets/app_confirm_dialog.dart';
import '../../lib/app/widgets/app_entity_row_card.dart';
import '../../lib/app/widgets/app_metric_card.dart';
import '../../lib/app/widgets/app_scaffold.dart';
import '../../lib/app/widgets/app_section_header.dart';
import '../../lib/app/widgets/app_segmented_filter.dart';
import '../../lib/app/widgets/app_status_banner.dart';
import '../../lib/app/widgets/app_term_help.dart';
import '../../lib/app/widgets/app_text_field.dart';
import '../../lib/app/widgets/app_timeline.dart';
import '../../lib/app/widgets/app_top_bar.dart';
import '../../lib/app/widgets/app_voice_fab.dart';
import '../../lib/app/widgets/cards/app_assignment_card.dart';
import '../../lib/app/widgets/cards/app_centered_badge_card.dart';
import '../../lib/app/widgets/cards/app_experience_card.dart';
import '../../lib/app/widgets/cards/app_image_feature_card.dart';
import '../../lib/app/widgets/cards/app_logbook_timeline.dart';
import '../../lib/app/widgets/cards/app_pricing_tiers_table.dart';
import '../../lib/app/widgets/cards/app_selectable_card.dart';
import '../../lib/app/widgets/cards/app_stats_card.dart';
import '../../lib/features/shared/presentation/widgets/module_subroute_header.dart';

// ─────────────────────────────────────────────────────────────────────────────
// Data model for each widget entry in the museum
// ─────────────────────────────────────────────────────────────────────────────
class _WidgetEntry {
  final String name;
  final String filePath;
  final String description;
  final List<String> enumValues;
  final List<String> constructorParams;
  final Widget Function(BuildContext) demo;
  const _WidgetEntry({
    required this.name,
    required this.filePath,
    required this.description,
    this.enumValues = const [],
    this.constructorParams = const [],
    required this.demo,
  });
}

// ─────────────────────────────────────────────────────────────────────────────
// Main Museum Screen
// ─────────────────────────────────────────────────────────────────────────────
class WidgetMuseumScreen extends StatefulWidget {
  const WidgetMuseumScreen({super.key});

  @override
  State<WidgetMuseumScreen> createState() => _WidgetMuseumScreenState();
}

class _WidgetMuseumScreenState extends State<WidgetMuseumScreen> {
  String _searchQuery = '';
  String _selectedCategory = 'Todas';
  late final List<_WidgetCategory> _categories;

  @override
  void initState() {
    super.initState();
    _categories = _buildCategories();
  }

  List<_WidgetCategory> _buildCategories() {
    return [
      _WidgetCategory(name: 'Botones y Acción', entries: _buttonEntries),
      _WidgetCategory(name: 'Estados y Badges', entries: _badgeEntries),
      _WidgetCategory(name: 'Cards Base', entries: _cardBaseEntries),
      _WidgetCategory(name: 'Cards de Dominio', entries: _cardDomainEntries),
      _WidgetCategory(name: 'Formularios', entries: _formEntries),
      _WidgetCategory(name: 'Navegación', entries: _navEntries),
      _WidgetCategory(name: 'Layout y Scaffold', entries: _layoutEntries),
      _WidgetCategory(name: 'Diálogos', entries: _dialogEntries),
      _WidgetCategory(name: 'Feature Widgets', entries: _featureEntries),
    ];
  }

  List<_WidgetEntry> get _allEntries =>
      _categories.expand((c) => c.entries).toList();

  List<_WidgetEntry> get _filteredEntries {
    final all = _selectedCategory == 'Todas'
        ? _allEntries
        : _categories
            .firstWhere((c) => c.name == _selectedCategory)
            .entries;
    if (_searchQuery.isEmpty) return all;
    final q = _searchQuery.toLowerCase();
    return all.where((e) {
      return e.name.toLowerCase().contains(q) ||
          e.filePath.toLowerCase().contains(q) ||
          e.description.toLowerCase().contains(q);
    }).toList();
  }

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final filtered = _filteredEntries;

    return Scaffold(
      backgroundColor: scheme.surface,
      appBar: AppBar(
        title: const Text('WIDGET MUSEUM'),
        backgroundColor: scheme.surfaceContainerHighest,
        actions: [
          Padding(
            padding: const EdgeInsets.only(right: 8),
            child: Text(
              '${_allEntries.length} widgets',
              style: Theme.of(context).textTheme.labelMedium?.copyWith(
                    color: scheme.onSurfaceVariant,
                  ),
            ),
          ),
        ],
      ),
      body: Column(
        children: [
          _buildSearchBar(scheme),
          _buildCategoryFilter(scheme),
          const Divider(height: 1),
          Expanded(
            child: filtered.isEmpty
                ? Center(
                    child: Text(
                      'Ningún widget coincide con "$_searchQuery"',
                      style: Theme.of(context).textTheme.bodyMedium,
                    ),
                  )
                : ListView.builder(
                    padding: const EdgeInsets.only(bottom: 80),
                    itemCount: filtered.length,
                    itemBuilder: (_, i) =>
                        _WidgetMuseumCard(entry: filtered[i]),
                  ),
          ),
        ],
      ),
    );
  }

  Widget _buildSearchBar(ColorScheme scheme) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(16, 12, 16, 8),
      child: TextField(
        decoration: InputDecoration(
          hintText: 'Buscar widget por nombre, ruta o descripción...',
          prefixIcon: const Icon(Icons.search_rounded, size: 20),
          suffixIcon: _searchQuery.isNotEmpty
              ? IconButton(
                  icon: const Icon(Icons.clear_rounded, size: 18),
                  onPressed: () => setState(() => _searchQuery = ''),
                )
              : null,
          isDense: true,
          border: OutlineInputBorder(
            borderRadius: BorderRadius.circular(8),
            borderSide: BorderSide(color: scheme.outlineVariant),
          ),
          filled: true,
          fillColor: scheme.surfaceContainerLow,
        ),
        onChanged: (v) => setState(() => _searchQuery = v),
      ),
    );
  }

  Widget _buildCategoryFilter(ColorScheme scheme) {
    final categories = ['Todas', ..._categories.map((c) => c.name)];
    return SizedBox(
      height: 44,
      child: ListView(
        scrollDirection: Axis.horizontal,
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
        children: categories.map((cat) {
          final selected = cat == _selectedCategory;
          return Padding(
            padding: const EdgeInsets.symmetric(horizontal: 4),
            child: FilterChip(
              label: Text(cat),
              selected: selected,
              onSelected: (_) => setState(() => _selectedCategory = cat),
              visualDensity: VisualDensity.compact,
            ),
          );
        }).toList(),
      ),
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Category model
// ─────────────────────────────────────────────────────────────────────────────
class _WidgetCategory {
  final String name;
  final List<_WidgetEntry> entries;
  const _WidgetCategory({required this.name, required this.entries});
}

// ─────────────────────────────────────────────────────────────────────────────
// Individual Widget Card
// ─────────────────────────────────────────────────────────────────────────────
class _WidgetMuseumCard extends StatefulWidget {
  final _WidgetEntry entry;
  const _WidgetMuseumCard({required this.entry});

  @override
  State<_WidgetMuseumCard> createState() => _WidgetMuseumCardState();
}

class _WidgetMuseumCardState extends State<_WidgetMuseumCard> {
  bool _expanded = false;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final scheme = theme.colorScheme;
    final e = widget.entry;

    return Card(
      margin: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
      color: scheme.surfaceContainerHigh,
      elevation: 0,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(8),
        side: BorderSide(color: scheme.outlineVariant.withValues(alpha: 0.3)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Header (always visible)
          InkWell(
            borderRadius: BorderRadius.circular(8),
            onTap: () => setState(() => _expanded = !_expanded),
            child: Padding(
              padding: const EdgeInsets.all(14),
              child: Row(
                children: [
                  Container(
                    padding:
                        const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                    decoration: BoxDecoration(
                      color: scheme.primary.withValues(alpha: 0.12),
                      borderRadius: BorderRadius.circular(4),
                    ),
                    child: Text(
                      e.name,
                      style: theme.textTheme.labelLarge?.copyWith(
                        fontWeight: FontWeight.w800,
                        color: scheme.primary,
                      ),
                    ),
                  ),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      e.filePath,
                      style: theme.textTheme.labelSmall?.copyWith(
                        color: scheme.onSurfaceVariant,
                        fontFamily: 'monospace',
                        fontSize: 10,
                      ),
                    ),
                  ),
                  Icon(
                    _expanded
                        ? Icons.expand_less_rounded
                        : Icons.expand_more_rounded,
                    size: 20,
                    color: scheme.onSurfaceVariant,
                  ),
                ],
              ),
            ),
          ),

          // Expanded section
          if (_expanded) ...[
            const Divider(height: 1),
            Padding(
              padding: const EdgeInsets.fromLTRB(14, 10, 14, 14),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // Description
                  Text(
                    e.description,
                    style: theme.textTheme.bodySmall?.copyWith(
                      color: scheme.onSurfaceVariant,
                      height: 1.4,
                    ),
                  ),
                  const SizedBox(height: 8),

                  // Constructor params
                  if (e.constructorParams.isNotEmpty) ...[
                    _Label(text: 'CONSTRUCTOR PARAMS', scheme: scheme),
                    const SizedBox(height: 4),
                    Container(
                      width: double.infinity,
                      padding: const EdgeInsets.all(8),
                      decoration: BoxDecoration(
                        color: scheme.surfaceContainerLow,
                        borderRadius: BorderRadius.circular(4),
                      ),
                      child: Text(
                        e.constructorParams.join('\n'),
                        style: TextStyle(
                          fontFamily: 'monospace',
                          fontSize: 10,
                          color: scheme.onSurfaceVariant,
                          height: 1.5,
                        ),
                      ),
                    ),
                    const SizedBox(height: 8),
                  ],

                  // Enum values
                  if (e.enumValues.isNotEmpty) ...[
                    _Label(text: 'ENUMS / VARIANTS', scheme: scheme),
                    const SizedBox(height: 4),
                    Wrap(
                      spacing: 4,
                      runSpacing: 4,
                      children: e.enumValues.map((ev) {
                        return Container(
                          padding: const EdgeInsets.symmetric(
                              horizontal: 6, vertical: 2),
                          decoration: BoxDecoration(
                            color: scheme.tertiary.withValues(alpha: 0.12),
                            borderRadius: BorderRadius.circular(3),
                            border: Border.all(
                              color:
                                  scheme.tertiary.withValues(alpha: 0.25),
                            ),
                          ),
                          child: Text(
                            ev,
                            style: TextStyle(
                              fontFamily: 'monospace',
                              fontSize: 9,
                              fontWeight: FontWeight.w700,
                              color: scheme.tertiary,
                            ),
                          ),
                        );
                      }).toList(),
                    ),
                    const SizedBox(height: 8),
                  ],

                  // Demo section
                  _Label(text: 'DEMO', scheme: scheme),
                  const SizedBox(height: 8),
                  _DemoWrapper(demo: e.demo),
                ],
              ),
            ),
          ],
        ],
      ),
    );
  }
}

class _Label extends StatelessWidget {
  final String text;
  final ColorScheme scheme;
  const _Label({required this.text, required this.scheme});

  @override
  Widget build(BuildContext context) {
    return Text(
      text,
      style: Theme.of(context).textTheme.labelSmall?.copyWith(
            fontWeight: FontWeight.w800,
            color: scheme.onSurfaceVariant,
            letterSpacing: 0.8,
            fontSize: 9,
          ),
    );
  }
}

class _DemoWrapper extends StatelessWidget {
  final Widget Function(BuildContext) demo;
  const _DemoWrapper({required this.demo});

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: Theme.of(context)
            .colorScheme
            .surfaceContainerLow
            .withValues(alpha: 0.4),
        borderRadius: BorderRadius.circular(6),
        border: Border.all(
          color: Theme.of(context)
              .colorScheme
              .outlineVariant
              .withValues(alpha: 0.15),
        ),
      ),
      child: demo(context),
    );
  }
}

// ═════════════════════════════════════════════════════════════════════════════
// WIDGET ENTRIES — every widget in the system cataloged
// ═════════════════════════════════════════════════════════════════════════════

// ── BOTONES Y ACCIÓN ─────────────────────────────────────────────────────────
final List<_WidgetEntry> _buttonEntries = [
  _WidgetEntry(
    name: 'AppButton',
    filePath: 'app/widgets/app_button.dart',
    description: 'Botón editorial con variantes primary, secondary, ghost, '
        'danger. AnimatedScale al presionar (96%), texto ALLCAPS con '
        'letter-spacing, icono opcional, modo expanded.',
    enumValues: [
      'AppButtonVariant.primary',
      'AppButtonVariant.secondary',
      'AppButtonVariant.ghost',
      'AppButtonVariant.danger',
    ],
    constructorParams: [
      'required String label',
      'required VoidCallback? onPressed',
      'IconData? icon',
      'AppButtonVariant variant = primary',
      'bool expanded = false',
      'double height = 52',
    ],
    demo: _demoAppButton,
  ),
  _WidgetEntry(
    name: 'AppVoiceFab',
    filePath: 'app/widgets/app_voice_fab.dart',
    description: 'Botón FAB redondo para voz. Blanco con elevación, '
        'icono intercambiable (AnimatedSwitcher).',
    constructorParams: [
      'VoidCallback? onTap',
      'double size = 76',
      'bool elevated = true',
      'IconData icon = Icons.mic_rounded',
    ],
    demo: _demoVoiceFab,
  ),
];

// ── ESTADOS Y BADGES ─────────────────────────────────────────────────────────
final List<_WidgetEntry> _badgeEntries = [
  _WidgetEntry(
    name: 'AppBadge',
    filePath: 'app/widgets/app_badge.dart',
    description: 'Badge compacto con 6 tonos funcionales. Soporta icono, '
        'tamaño sm/md, uppercase toggle.',
    enumValues: [
      'AppBadgeTone.neutral',
      'AppBadgeTone.primary',
      'AppBadgeTone.success',
      'AppBadgeTone.danger',
      'AppBadgeTone.warning',
      'AppBadgeTone.ghost',
      'AppBadgeSize.sm',
      'AppBadgeSize.md',
    ],
    constructorParams: [
      'required String label',
      'AppBadgeTone tone = neutral',
      'AppBadgeSize size = sm',
      'IconData? icon',
      'bool uppercase = true',
    ],
    demo: _demoBadge,
  ),
  _WidgetEntry(
    name: 'AppStatusBanner',
    filePath: 'app/widgets/app_status_banner.dart',
    description: 'Banner de estado con icono, título, mensaje, badge '
        'opcional y 4 tonos. Construido sobre AppCard.',
    enumValues: [
      'AppStatusBannerTone.info',
      'AppStatusBannerTone.warning',
      'AppStatusBannerTone.danger',
      'AppStatusBannerTone.success',
    ],
    constructorParams: [
      'required String title',
      'required String message',
      'required AppStatusBannerTone tone',
      'IconData icon = Icons.info_outline_rounded',
      'String? badgeLabel',
      'VoidCallback? onTap',
    ],
    demo: _demoStatusBanner,
  ),
  _WidgetEntry(
    name: 'AppCenteredLoader',
    filePath: 'app/widgets/app_centered_loader.dart',
    description: 'Loader centrado con CircularProgressIndicator. '
        'strokeWidth configurable.',
    constructorParams: ['double strokeWidth = 2.8'],
    demo: _demoLoader,
  ),
];

// ── CARDS BASE ───────────────────────────────────────────────────────────────
final List<_WidgetEntry> _cardBaseEntries = [
  _WidgetEntry(
    name: 'AppCard',
    filePath: 'app/widgets/app_card.dart',
    description: 'Card tonal sin elevación. 4 tonos de superficie. '
        'Soporta flip 3D con backChild, barra de acento, borde outline.',
    enumValues: [
      'AppCardTone.surface',
      'AppCardTone.high',
      'AppCardTone.low',
      'AppCardTone.error',
    ],
    constructorParams: [
      'required Widget child',
      'Widget? backChild',
      'AppCardTone tone = high',
      'EdgeInsetsGeometry? padding',
      'Color? accentColor',
      'bool outlined = false',
      'VoidCallback? onTap',
    ],
    demo: _demoAppCard,
  ),
  _WidgetEntry(
    name: 'AppSelectableCard',
    filePath: 'app/widgets/cards/app_selectable_card.dart',
    description: 'Card seleccionable con barra lateral izquierda al '
        'estar selected. Padding, borderRadius, backgroundColor '
        'configurables. Envuelve cualquier child.',
    constructorParams: [
      'required Widget child',
      'bool selected = false',
      'Color? accentColor',
      'VoidCallback? onTap',
      'EdgeInsetsGeometry? padding',
      'BorderRadius? borderRadius',
      'Color? backgroundColor',
    ],
    demo: _demoSelectableCard,
  ),
  _WidgetEntry(
    name: 'AppEntityRowCard',
    filePath: 'app/widgets/app_entity_row_card.dart',
    description: 'Row card para listas de entidades. Title, subtitle, '
        'badge, selected state, barra de acento, leading/trailing widgets.',
    constructorParams: [
      'required String title',
      'required String subtitle',
      'AppBadge? badge',
      'bool selected = false',
      'VoidCallback? onTap',
      'Color? accentColor',
      'Widget? leading',
      'Widget? trailing',
    ],
    demo: _demoEntityRowCard,
  ),
  _WidgetEntry(
    name: 'AppMetricCard',
    filePath: 'app/widgets/app_metric_card.dart',
    description: 'Card de métrica con valor grande, título, sufijo, '
        'texto de soporte, icono. 3 tonos + compact mode.',
    enumValues: [
      'AppMetricCardTone.defaultTone',
      'AppMetricCardTone.danger',
      'AppMetricCardTone.inverse',
    ],
    constructorParams: [
      'required String title',
      'required String value',
      'String? suffix',
      'String? supportingText',
      'IconData? icon',
      'AppMetricCardTone tone = defaultTone',
      'bool compact = false',
    ],
    demo: _demoMetricCard,
  ),
  _WidgetEntry(
    name: 'AppStatsCard',
    filePath: 'app/widgets/cards/app_stats_card.dart',
    description: 'Card de estadísticas con eyebrow, title, topRight '
        'widget, y children list. Usa AppSelectableCard internamente.',
    constructorParams: [
      'required String eyebrow',
      'required String title',
      'required List<Widget> children',
      'Widget? topRight',
      'bool selected = false',
      'VoidCallback? onTap',
    ],
    demo: _demoStatsCard,
  ),
  _WidgetEntry(
    name: 'AppImageFeatureCard',
    filePath: 'app/widgets/cards/app_image_feature_card.dart',
    description: 'Card con imagen destacada, título, subtítulo, badge '
        'superpuesto. Horizontal scroll. Usa AppSelectableCard.',
    constructorParams: [
      'required String title',
      'required String subtitle',
      'required ImageProvider image',
      'AppBadge? badge',
      'bool selected = false',
      'VoidCallback? onTap',
      'double width = 240',
      'double imageHeight = 160',
    ],
    demo: _demoImageFeatureCard,
  ),
  _WidgetEntry(
    name: 'AppCenteredBadgeCard',
    filePath: 'app/widgets/cards/app_centered_badge_card.dart',
    description: 'Card centrada con kicker, título grande, subtítulo, '
        'y colección de badges. Trailing icon opcional.',
    constructorParams: [
      'required String title',
      'required String subtitle',
      'String? kicker',
      'List<AppBadge> badges = const []',
      'AppBadgeTone tone = neutral',
      'IconData? trailingIcon = Icons.edit_rounded',
      'VoidCallback? onTap',
      'VoidCallback? onTrailingTap',
    ],
    demo: _demoCenteredBadgeCard,
  ),
  _WidgetEntry(
    name: 'AppSectionHeader',
    filePath: 'app/widgets/app_section_header.dart',
    description: 'Cabecera de sección editorial. Variantes hero (display) '
        'y compact (headline). Eyebrow, subtitle, trailing widget.',
    enumValues: [
      'AppSectionHeaderVariant.hero',
      'AppSectionHeaderVariant.compact',
    ],
    constructorParams: [
      'required String title',
      'String? eyebrow',
      'String? subtitle',
      'Widget? trailing',
      'AppSectionHeaderVariant variant = hero',
      'EdgeInsetsGeometry? padding',
    ],
    demo: _demoSectionHeader,
  ),
];

// ── CARDS DE DOMINIO ─────────────────────────────────────────────────────────
final List<_WidgetEntry> _cardDomainEntries = [
  _WidgetEntry(
    name: 'AppExperienceCard',
    filePath: 'app/widgets/cards/app_experience_card.dart',
    description: 'Card de experiencia/producto. 3 variantes: commercial '
        '(imagen + precio), compact, operational (horario + cupos). '
        'Incluye badges, metadata, botón CTA.',
    enumValues: [
      'AppExperienceCardVariant.commercial',
      'AppExperienceCardVariant.compact',
      'AppExperienceCardVariant.operational',
    ],
    constructorParams: [
      'required AppExperienceCardData data',
      'AppExperienceCardVariant variant = commercial',
      'String? primaryActionLabel',
      'VoidCallback? onTap',
      'VoidCallback? onPrimaryAction',
      'bool enabled = true',
      'bool selected = false',
    ],
    demo: _demoExperienceCard,
  ),
  _WidgetEntry(
    name: 'AppPricingTiersTable',
    filePath: 'app/widgets/cards/app_pricing_tiers_table.dart',
    description: 'Tabla de tarifas por rango de participantes. '
        'Currency configurable, notas, indicador de netas.',
    constructorParams: [
      'required List<AppPricingTierData> tiers',
      'String currency = COP',
      'bool pricesAreNet = true',
      'String? notes',
    ],
    demo: _demoPricingTable,
  ),
  _WidgetEntry(
    name: 'AppAssignmentCard',
    filePath: 'app/widgets/cards/app_assignment_card.dart',
    description: 'Card de asignación participante + equino. Muestra '
        'carga, silla, validación con 3 estados: ok, warning, error. '
        'Botones de cambio.',
    enumValues: [
      'AppAssignmentCardState.ok',
      'AppAssignmentCardState.warning',
      'AppAssignmentCardState.error',
    ],
    constructorParams: [
      'required String startTimeLabel',
      'required AppAssignmentParticipantData participant',
      'required AppAssignmentEquineData equine',
      'required String saddleLabel',
      'required double loadRatio',
      'String? reservationLabel',
      'String? validationMessage',
      'AppAssignmentCardState state = ok',
      'VoidCallback? onTap',
      'VoidCallback? onChangeEquine',
      'VoidCallback? onChangeSaddle',
    ],
    demo: _demoAssignmentCard,
  ),
  _WidgetEntry(
    name: 'AppTimeline',
    filePath: 'app/widgets/app_timeline.dart',
    description: 'Timeline vertical con nodos de estado: active, '
        'completed, cancelled, error, neutral. Usa AppTimelineItem '
        'y AppTimelineEntryCard. Contenido destacable opcional.',
    enumValues: [
      'AppTimelineNodeState.active',
      'AppTimelineNodeState.completed',
      'AppTimelineNodeState.cancelled',
      'AppTimelineNodeState.error',
      'AppTimelineNodeState.neutral',
    ],
    constructorParams: [
      'required List<Widget> children',
      'double lineLeft = 12',
      'EdgeInsetsGeometry? padding',
    ],
    demo: _demoTimeline,
  ),
  _WidgetEntry(
    name: 'AppLogbookTimeline',
    filePath: 'app/widgets/cards/app_logbook_timeline.dart',
    description: 'Timeline de bitácora con entradas enriquecidas: '
        'reserva, guía, duración, observaciones, fotos, edit.',
    enumValues: [
      'AppLogbookEntryState.active',
      'AppLogbookEntryState.completed',
      'AppLogbookEntryState.neutral',
      'AppLogbookEntryState.warning',
      'AppLogbookEntryState.error',
    ],
    constructorParams: [
      'required List<AppLogbookTimelineEntry> entries',
      'double lineLeft = 12',
      'double itemSpacing = 24',
    ],
    demo: _demoLogbookTimeline,
  ),
];

// ── FORMULARIOS ──────────────────────────────────────────────────────────────
final List<_WidgetEntry> _formEntries = [
  _WidgetEntry(
    name: 'AppTextField',
    filePath: 'app/widgets/app_text_field.dart',
    description: 'Campo de texto editorial. Variantes filled y underlined. '
        'Label externo en mayúsculas, hint, suffix, focus color primary.',
    enumValues: [
      'AppTextFieldVariant.filled',
      'AppTextFieldVariant.underlined',
    ],
    constructorParams: [
      'TextEditingController? controller',
      'String? label',
      'String? hintText',
      'Widget? suffix',
      'int? maxLines = 1',
      'AppTextFieldVariant variant = filled',
      'TextInputType? keyboardType',
      'ValueChanged<String>? onChanged',
      'FocusNode? focusNode',
      'bool autofocus = false',
      'bool readOnly = false',
      'VoidCallback? onTap',
      'bool obscureText = false',
    ],
    demo: _demoTextField,
  ),
  _WidgetEntry(
    name: 'AppSegmentedFilter',
    filePath: 'app/widgets/app_segmented_filter.dart',
    description: 'Control segmentado tipo filter bar. Genérico T. '
        'Soporta expanded mode. Usa auto_size_text.',
    constructorParams: [
      'required List<AppSegmentedFilterItem<T>> items',
      'required T value',
      'required ValueChanged<T> onChanged',
      'bool expanded = true',
    ],
    demo: _demoSegmentedFilter,
  ),
  _WidgetEntry(
    name: 'AppTermHelp',
    filePath: 'app/widgets/app_term_help.dart',
    description: 'Botón de ayuda circular con ? que muestra AlertDialog '
        'con título y mensaje explicativo.',
    constructorParams: [
      'required String title',
      'required String message',
    ],
    demo: _demoTermHelp,
  ),
];

// ── NAVEGACIÓN ───────────────────────────────────────────────────────────────
final List<_WidgetEntry> _navEntries = [
  _WidgetEntry(
    name: 'AppBottomNav',
    filePath: 'app/widgets/app_bottom_nav.dart',
    description: 'Barra de navegación inferior con 5 tabs: Inicio, '
        'Reservas, Equinos, Clientes, Más. Long-press para voz. '
        'Animaciones de selección y voz.',
    enumValues: ['AppNavItem.inicio', 'AppNavItem.reservas', 'AppNavItem.equinos', 'AppNavItem.clientes', 'AppNavItem.mas'],
    constructorParams: [
      'required AppNavItem current',
      'ValueChanged<AppNavItem>? onTap',
    ],
    demo: _demoBottomNav,
  ),
  _WidgetEntry(
    name: 'AppBreadcrumb',
    filePath: 'app/widgets/app_breadcrumb.dart',
    description: 'Migas de pan con items, separador configurable, '
        'currentIndex, onItemTap, uppercase toggle.',
    constructorParams: [
      'required List<String> items',
      'String separator = >',
      'int? currentIndex',
      'ValueChanged<int>? onItemTap',
      'bool uppercase = true',
    ],
    demo: _demoBreadcrumb,
  ),
  _WidgetEntry(
    name: 'AppTopBar',
    filePath: 'app/widgets/app_top_bar.dart',
    description: 'Barra superior con logo SVG, título, theme toggle, '
        'notificaciones con dot. 64px de altura.',
    constructorParams: [
      'required String logoAssetPath',
      'String title = LA JUANA',
      'VoidCallback? onNotificationsTap',
      'VoidCallback? onThemeToggleTap',
      'bool showNotificationDot = false',
    ],
    demo: _demoTopBar,
  ),
];

// ── LAYOUT Y SCAFFOLD ────────────────────────────────────────────────────────
final List<_WidgetEntry> _layoutEntries = [
  _WidgetEntry(
    name: 'AppScaffold',
    filePath: 'app/widgets/app_scaffold.dart',
    description: 'Wrapper de Scaffold + SafeArea + scroll opcional + '
        'padding. Controla resizeToAvoidBottomInset.',
    constructorParams: [
      'required Widget child',
      'PreferredSizeWidget? appBar',
      'Widget? bottomNavigationBar',
      'FloatingActionButton? floatingActionButton',
      'bool scrollable = true',
      'EdgeInsetsGeometry? padding',
      'Color? backgroundColor',
      'bool resizeToAvoidBottomInset = true',
    ],
    demo: _demoScaffold,
  ),
  _WidgetEntry(
    name: 'AppThemeTokens',
    filePath: 'app/theme/theme_extensions.dart',
    description: 'ThemeExtension con radius tokens (sm, md, lg, xl) '
        'y spacing tokens (xs, sm, md, lg, xl). Acceso vía '
        'Theme.of(context).appTokens.',
    constructorParams: [
      'required BorderRadius radiusSm',
      'required BorderRadius radiusMd',
      'required BorderRadius radiusLg',
      'required BorderRadius radiusXl',
      'required double spaceXs = 4',
      'required double spaceSm = 8',
      'required double spaceMd = 12',
      'required double spaceLg = 16',
      'required double spaceXl = 24',
    ],
    demo: _demoTokens,
  ),
];

// ── DIÁLOGOS ─────────────────────────────────────────────────────────────────
final List<_WidgetEntry> _dialogEntries = [
  _WidgetEntry(
    name: 'AppConfirmDialog',
    filePath: 'app/widgets/app_confirm_dialog.dart',
    description: 'Diálogo de confirmación reutilizable con icono, título, '
        'mensaje, botones cancel/confirm. 3 estilos: regular, warning, '
        'danger. Método estático show().',
    enumValues: [
      'DialogStyle.regular',
      'DialogStyle.warning',
      'DialogStyle.danger',
    ],
    constructorParams: [
      'required IconData icon',
      'required String title',
      'required String message',
      'required String confirmLabel',
      'required VoidCallback onConfirm',
      'String cancelLabel = Cancelar',
      'VoidCallback? onCancel',
      'DialogStyle style = regular',
      'double? height',
    ],
    demo: _demoConfirmDialog,
  ),
];

// ── FEATURE WIDGETS ──────────────────────────────────────────────────────────
final List<_WidgetEntry> _featureEntries = [
  _WidgetEntry(
    name: 'ModuleSubrouteHeader',
    filePath: 'features/shared/presentation/widgets/module_subroute_header.dart',
    description: 'Cabecera de módulo con AppSectionHeader + '
        'AppSegmentedFilter para subrutas (sin breadcrumb falso).',
    constructorParams: [
      'required String eyebrow',
      'required String title',
      'required List<String> subrouteLabels',
      'required int currentSubrouteIndex',
      'required ValueChanged<int> onSubrouteTap',
      'String? subtitle',
      'Widget? trailing',
    ],
    demo: _demoModuleSubroute,
  ),
];

// ═════════════════════════════════════════════════════════════════════════════
// DEMO BUILDERS — each builds a live interactive widget preview
// ═════════════════════════════════════════════════════════════════════════════

Widget _demoAppButton(BuildContext context) {
  return Column(
    children: [
      Wrap(
        spacing: 8,
        runSpacing: 8,
        children: [
          AppButton(label: 'Primary', onPressed: () {}),
          AppButton(
              label: 'Secondary',
              onPressed: () {},
              variant: AppButtonVariant.secondary),
          AppButton(
              label: 'Ghost',
              onPressed: () {},
              variant: AppButtonVariant.ghost),
          AppButton(
              label: 'Danger',
              onPressed: () {},
              variant: AppButtonVariant.danger),
        ],
      ),
      const SizedBox(height: 8),
      AppButton(
        label: 'Con icono',
        onPressed: () {},
        icon: Icons.check,
        expanded: true,
      ),
    ],
  );
}

Widget _demoVoiceFab(BuildContext context) {
  return const Row(
    children: [
      AppVoiceFab(onTap: null),
      SizedBox(width: 12),
      AppVoiceFab(onTap: null, size: 56, elevated: false),
      SizedBox(width: 12),
      AppVoiceFab(onTap: null, size: 44, icon: Icons.play_arrow_rounded),
    ],
  );
}

Widget _demoBadge(BuildContext context) {
  final scheme = Theme.of(context).colorScheme;
  return Column(
    crossAxisAlignment: CrossAxisAlignment.start,
    children: [
      Wrap(
        spacing: 6,
        runSpacing: 6,
        children: [
          const AppBadge(label: 'Neutral', tone: AppBadgeTone.neutral),
          const AppBadge(label: 'Primary', tone: AppBadgeTone.primary),
          const AppBadge(label: 'Success', tone: AppBadgeTone.success),
          const AppBadge(label: 'Danger', tone: AppBadgeTone.danger),
          const AppBadge(label: 'Warning', tone: AppBadgeTone.warning),
          const AppBadge(label: 'Ghost', tone: AppBadgeTone.ghost),
        ],
      ),
      const SizedBox(height: 8),
      Row(
        children: [
          const AppBadge(
            label: 'Con icono',
            tone: AppBadgeTone.primary,
            icon: Icons.star_rounded,
          ),
          const SizedBox(width: 8),
          AppBadge(
            label: 'Size md',
            tone: AppBadgeTone.success,
            size: AppBadgeSize.md,
          ),
          const SizedBox(width: 8),
          AppBadge(
            label: 'no uppercase',
            tone: AppBadgeTone.ghost,
            uppercase: false,
          ),
        ],
      ),
      const SizedBox(height: 8),
      Text(
        'appBadgeToneColors() / appBadgeToneTint() disponibles como helpers.',
        style: Theme.of(context).textTheme.labelSmall?.copyWith(
              color: scheme.onSurfaceVariant,
            ),
      ),
    ],
  );
}

Widget _demoStatusBanner(BuildContext context) {
  return Column(
    children: const [
      AppStatusBanner(
        title: 'Sincronización',
        message: 'Datos enviados correctamente.',
        tone: AppStatusBannerTone.success,
        badgeLabel: 'OK',
      ),
      SizedBox(height: 8),
      AppStatusBanner(
        title: 'Sin conexión',
        message: 'Cambios se enviarán cuando haya conexión.',
        tone: AppStatusBannerTone.warning,
        badgeLabel: 'Pendiente',
      ),
      SizedBox(height: 8),
      AppStatusBanner(
        title: 'Error crítico',
        message: 'No se pudo conectar con el servidor.',
        tone: AppStatusBannerTone.danger,
        icon: Icons.error_outline_rounded,
        badgeLabel: 'Error',
      ),
    ],
  );
}

Widget _demoLoader(BuildContext context) {
  return const SizedBox(height: 80, child: AppCenteredLoader());
}

Widget _demoAppCard(BuildContext context) {
  final scheme = Theme.of(context).colorScheme;
  return Column(
    children: [
      AppCard(
        tone: AppCardTone.high,
        outlined: true,
        accentColor: scheme.primary,
        child: const Text('AppCard high + outlined + accent'),
      ),
      const SizedBox(height: 8),
      AppCard(
        tone: AppCardTone.surface,
        child: const Text('AppCard surface (sin borde)'),
      ),
      const SizedBox(height: 8),
      AppCard(
        tone: AppCardTone.error,
        child: Text('AppCard error tone',
            style: TextStyle(color: scheme.onErrorContainer)),
      ),
    ],
  );
}

Widget _demoSelectableCard(BuildContext context) {
  return Column(
    children: [
      AppSelectableCard(
        selected: true,
        onTap: () {},
        child: const Text('AppSelectableCard selected=true'),
      ),
      const SizedBox(height: 8),
      AppSelectableCard(
        selected: false,
        onTap: () {},
        child: const Text('AppSelectableCard selected=false'),
      ),
    ],
  );
}

Widget _demoEntityRowCard(BuildContext context) {
  return const Column(
    children: [
      AppEntityRowCard(
        title: 'Elena Rodriguez',
        subtitle: 'EXP: INTERMEDIO - 68KG',
        selected: true,
        badge: AppBadge(label: 'Alto riesgo', tone: AppBadgeTone.danger),
      ),
      SizedBox(height: 8),
      AppEntityRowCard(
        title: 'Marcus Thorne',
        subtitle: 'EXP: AVANZADO - 82KG',
        badge: AppBadge(label: 'Perfecto', tone: AppBadgeTone.success),
      ),
    ],
  );
}

Widget _demoMetricCard(BuildContext context) {
  return Column(
    children: [
      const AppMetricCard(
        title: 'Reservas activas',
        value: '124',
        suffix: 'ITEMS',
      ),
      const SizedBox(height: 8),
      const AppMetricCard(
        title: 'Stock crítico',
        value: '08',
        supportingText: 'SE RECOMIENDA COMPRAR',
        tone: AppMetricCardTone.danger,
        icon: Icons.warning_amber_rounded,
      ),
      const SizedBox(height: 8),
      const AppMetricCard(
        title: 'Compact mode',
        value: '42',
        suffix: 'UNITS',
        compact: true,
      ),
    ],
  );
}

Widget _demoStatsCard(BuildContext context) {
  return AppStatsCard(
    eyebrow: 'Estadísticas',
    title: 'Cosaco 24',
    selected: true,
    topRight: const AppBadge(label: 'Disponible', tone: AppBadgeTone.success),
    children: const [
      Row(
        children: [
          Expanded(
            child: Text('Edad: 11 años',
                style: TextStyle(fontWeight: FontWeight.w700)),
          ),
          Expanded(
            child: Text('Peso: 300 kg',
                style: TextStyle(fontWeight: FontWeight.w700)),
          ),
        ],
      ),
    ],
  );
}

Widget _demoImageFeatureCard(BuildContext context) {
  return SizedBox(
    height: 220,
    child: ListView(
      scrollDirection: Axis.horizontal,
      children: const [
        AppImageFeatureCard(
          title: 'Cosaco 24',
          subtitle: 'Criollo - 11 años',
          selected: true,
          badge: AppBadge(label: 'Paso fino', tone: AppBadgeTone.primary),
          image: NetworkImage('https://picsum.photos/seed/equino1/360/220'),
        ),
        SizedBox(width: 8),
        AppImageFeatureCard(
          title: 'Juana',
          subtitle: 'Criolla - 6 años',
          image: NetworkImage('https://picsum.photos/seed/equino2/360/220'),
        ),
      ],
    ),
  );
}

Widget _demoCenteredBadgeCard(BuildContext context) {
  return AppCenteredBadgeCard(
    kicker: 'Reserva principal',
    title: 'Elena + Cosaco',
    subtitle: 'Asignación preparada para salida de las 09:15 AM',
    tone: AppBadgeTone.primary,
    badges: const [
      AppBadge(label: 'Confirmada', tone: AppBadgeTone.success),
      AppBadge(label: 'Pago parcial', tone: AppBadgeTone.warning),
      AppBadge(label: '2 extras', tone: AppBadgeTone.ghost),
    ],
    onTap: () {},
    onTrailingTap: () {},
  );
}

Widget _demoSectionHeader(BuildContext context) {
  return Column(
    children: [
      const AppSectionHeader(eyebrow: 'Sección', title: 'Hero Variant'),
      const SizedBox(height: 16),
      const AppSectionHeader(
        eyebrow: 'Compacta',
        title: 'Compact Variant',
        variant: AppSectionHeaderVariant.compact,
        subtitle: 'Con subtítulo opcional',
      ),
      const SizedBox(height: 16),
      AppSectionHeader(
        eyebrow: 'Con acción',
        title: 'Con trailing',
        variant: AppSectionHeaderVariant.compact,
        trailing: AppButton(
          label: 'Crear',
          icon: Icons.add,
          onPressed: () {},
          variant: AppButtonVariant.secondary,
          height: 40,
        ),
      ),
    ],
  );
}

Widget _demoExperienceCard(BuildContext context) {
  return Column(
    children: [
      const AppExperienceCard(
        variant: AppExperienceCardVariant.compact,
        data: AppExperienceCardData(
          title: 'Cabalgata de atardecer',
          description: 'Sesión corta para principiantes.',
          activityDurationLabel: '1h 20m',
          routeDurationLabel: '55m',
          difficultyLabel: 'Básico',
          badges: [
            AppOperationalBadgeData(
              label: 'Últimos cupos',
              tone: AppBadgeTone.warning,
            ),
          ],
        ),
        onPrimaryAction: null,
      ),
      const SizedBox(height: 8),
      const AppPricingTiersTable(
        currency: 'COP',
        pricesAreNet: true,
        notes: 'Netas en pesos colombianos (COP)',
        tiers: [
          AppPricingTierData(
              minParticipants: 1, maxParticipants: 1, pricePerPerson: 875000),
          AppPricingTierData(
              minParticipants: 2, maxParticipants: 2, pricePerPerson: 530000),
          AppPricingTierData(
              minParticipants: 3, maxParticipants: 3, pricePerPerson: 450000),
          AppPricingTierData(
              minParticipants: 4, maxParticipants: 8, pricePerPerson: 420000),
        ],
      ),
    ],
  );
}

Widget _demoPricingTable(BuildContext context) {
  return const AppPricingTiersTable(
    currency: 'COP',
    pricesAreNet: true,
    notes: 'Netas en pesos colombianos (COP)',
    tiers: [
      AppPricingTierData(
          minParticipants: 1, maxParticipants: 1, pricePerPerson: 875000),
      AppPricingTierData(
          minParticipants: 2, maxParticipants: 2, pricePerPerson: 530000),
      AppPricingTierData(
          minParticipants: 3, maxParticipants: 3, pricePerPerson: 450000),
      AppPricingTierData(
          minParticipants: 4, maxParticipants: 8, pricePerPerson: 420000),
    ],
  );
}

Widget _demoAssignmentCard(BuildContext context) {
  return Column(
    children: [
      AppAssignmentCard(
        startTimeLabel: '09:15 AM',
        reservationLabel: 'RES-2419',
        participant: const AppAssignmentParticipantData(
          name: 'Elena Rodriguez',
          weightLabel: '68 kg',
          experienceLabel: 'Intermedia',
          ageLabel: '29 años',
        ),
        equine: const AppAssignmentEquineData(
          name: 'Cosaco 24',
          capacityLabel: 'Carga max 90 kg',
          statusLabel: 'Paso fino',
        ),
        saddleLabel: 'Silla trail media',
        loadRatio: 0.72,
        state: AppAssignmentCardState.warning,
        validationMessage: 'Cerca del límite de carga.',
        onChangeEquine: () {},
        onChangeSaddle: () {},
      ),
      const SizedBox(height: 12),
      AppAssignmentCard(
        startTimeLabel: '11:30 AM',
        reservationLabel: 'RES-2427',
        participant: const AppAssignmentParticipantData(
          name: 'Marcus Thorne',
          weightLabel: '82 kg',
          experienceLabel: 'Avanzado',
        ),
        equine: const AppAssignmentEquineData(
          name: 'Juana',
          capacityLabel: 'Carga max 80 kg',
          statusLabel: 'En revisión',
        ),
        saddleLabel: 'Silla endurance #3',
        loadRatio: 1.04,
        state: AppAssignmentCardState.error,
        validationMessage: 'Excede capacidad recomendada.',
        onChangeEquine: () {},
      ),
    ],
  );
}

Widget _demoTimeline(BuildContext context) {
  return AppTimeline(
    children: const [
      AppTimelineItem(
        state: AppTimelineNodeState.active,
        child: AppTimelineEntryCard(
          date: 'Oct 24, 2026 - 09:00 AM',
          title: 'Monta controlada',
          badge: AppBadge(label: 'Pendiente', tone: AppBadgeTone.ghost),
          description: 'Monta natural con yegua en condiciones controladas.',
        ),
      ),
      AppTimelineItem(
        state: AppTimelineNodeState.completed,
        child: AppTimelineEntryCard(
          date: 'Sep 15, 2026',
          title: 'Vacunación anual',
          badge: AppBadge(label: 'Completado', tone: AppBadgeTone.ghost),
          description: 'Vacuna contra influenza y tétanos.',
        ),
      ),
      AppTimelineItem(
        state: AppTimelineNodeState.cancelled,
        child: AppTimelineEntryCard(
          date: 'Ago 28, 2026',
          title: 'Monta controlada',
          badge: AppBadge(label: 'Cancelado', tone: AppBadgeTone.danger),
          description: 'Reprogramada.',
        ),
      ),
    ],
  );
}

Widget _demoLogbookTimeline(BuildContext context) {
  return AppLogbookTimeline(
    entries: [
      AppLogbookTimelineEntry(
        state: AppLogbookEntryState.active,
        title: 'Monta guiada',
        dateLabel: '24 Oct 2026 - 09:00 AM',
        reservationLabel: 'RES-2419',
        guideLabel: 'Juan P.',
        durationLabel: '2h 30m',
        badge: const AppBadge(
            label: 'En curso', tone: AppBadgeTone.primary),
        observations: 'Terreno seco, respuesta estable del equino.',
      ),
      AppLogbookTimelineEntry(
        state: AppLogbookEntryState.completed,
        title: 'Checklist pre salida',
        dateLabel: '24 Oct 2026 - 08:20 AM',
        reservationLabel: 'RES-2419',
        guideLabel: 'Laura V.',
        durationLabel: '12m',
        badge: const AppBadge(
            label: 'Completado', tone: AppBadgeTone.ghost),
      ),
    ],
  );
}

Widget _demoTextField(BuildContext context) {
  return const Column(
    children: [
      AppTextField(
        label: 'Búsqueda',
        hintText: 'Buscar reserva',
        suffix: Icon(Icons.search),
      ),
      SizedBox(height: 12),
      AppTextField(
        label: 'Notas',
        hintText: 'Escribe observaciones',
        maxLines: 3,
        variant: AppTextFieldVariant.underlined,
      ),
    ],
  );
}

Widget _demoSegmentedFilter(BuildContext context) {
  return AppSegmentedFilter<String>(
    value: 'opcion1',
    onChanged: (_) {},
    items: const [
      AppSegmentedFilterItem(label: 'Opción 1', value: 'opcion1'),
      AppSegmentedFilterItem(label: 'Opción 2', value: 'opcion2'),
      AppSegmentedFilterItem(label: 'Opción 3', value: 'opcion3'),
    ],
  );
}

Widget _demoTermHelp(BuildContext context) {
  return const AppTermHelp(title: 'Ayuda', message: 'Mensaje de ayuda.');
}

Widget _demoBottomNav(BuildContext context) {
  return const SizedBox(
    height: 65,
    child: AppBottomNav(current: AppNavItem.inicio),
  );
}

Widget _demoBreadcrumb(BuildContext context) {
  return const AppBreadcrumb(items: ['Gestión', 'Experiencias', 'Detalle']);
}

Widget _demoTopBar(BuildContext context) {
  return const AppTopBar(
    logoAssetPath: 'assets/branding/lajuana.svg',
    title: 'LA JUANA',
  );
}

Widget _demoScaffold(BuildContext context) {
  return const AppScaffold(
    scrollable: false,
    padding: EdgeInsets.all(16),
    child: Text('AppScaffold wrapper content.'),
  );
}

Widget _demoTokens(BuildContext context) {
  final tokens = Theme.of(context).appTokens;
  final scheme = Theme.of(context).colorScheme;
  return Column(
    crossAxisAlignment: CrossAxisAlignment.start,
    children: [
      Text('Radius: sm=${_br(tokens.radiusSm)} md=${_br(tokens.radiusMd)} '
          'lg=${_br(tokens.radiusLg)} xl=${_br(tokens.radiusXl)}',
          style: Theme.of(context).textTheme.labelSmall),
      const SizedBox(height: 4),
      Text('Spacing: xs=${_d(tokens.spaceXs)} sm=${_d(tokens.spaceSm)} '
          'md=${_d(tokens.spaceMd)} lg=${_d(tokens.spaceLg)} xl=${_d(tokens.spaceXl)}',
          style: Theme.of(context).textTheme.labelSmall),
      const SizedBox(height: 8),
      Row(
        children: [
          _Swatch(color: scheme.primary, label: 'Primary'),
          _Swatch(color: scheme.secondary, label: 'Secondary'),
          _Swatch(color: scheme.tertiary, label: 'Tertiary'),
          _Swatch(color: scheme.error, label: 'Error'),
          _Swatch(color: scheme.surface, label: 'Surface'),
          _Swatch(color: scheme.surfaceContainerHighest, label: 'Container'),
        ],
      ),
    ],
  );
}

String _br(BorderRadius br) {
  final r = br.resolve(TextDirection.ltr);
  return '${r.topLeft.x.round()}px';
}

String _d(double d) => '${d.round()}px';

class _Swatch extends StatelessWidget {
  final Color color;
  final String label;
  const _Swatch({required this.color, required this.label});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(right: 8),
      child: Column(
        children: [
          Container(
            width: 20,
            height: 20,
            decoration: BoxDecoration(
              color: color,
              borderRadius: BorderRadius.circular(3),
              border: Border.all(color: Colors.white24),
            ),
          ),
          const SizedBox(height: 2),
          Text(label,
              style: Theme.of(context).textTheme.labelSmall?.copyWith(
                    fontSize: 7,
                  )),
        ],
      ),
    );
  }
}

Widget _demoConfirmDialog(BuildContext context) {
  return Row(
    children: [
      AppButton(
        label: 'Regular',
        onPressed: () => AppConfirmDialog.show(
          context: context,
          icon: Icons.check_circle_outline,
          title: 'Confirmar acción',
          message: '¿Estás seguro de realizar esta acción?',
          confirmLabel: 'Confirmar',
          onConfirm: () {},
        ),
        variant: AppButtonVariant.secondary,
        height: 40,
      ),
      const SizedBox(width: 8),
      AppButton(
        label: 'Danger',
        onPressed: () => AppConfirmDialog.show(
          context: context,
          icon: Icons.warning_rounded,
          title: 'Eliminar',
          message: 'Esta acción no se puede deshacer.',
          confirmLabel: 'Eliminar',
          onConfirm: () {},
          style: DialogStyle.danger,
        ),
        variant: AppButtonVariant.danger,
        height: 40,
      ),
    ],
  );
}

Widget _demoModuleSubroute(BuildContext context) {
  return ModuleSubrouteHeader(
    eyebrow: 'Experiencias',
    title: 'Catálogo',
    subrouteLabels: ['Todas', 'Activas', 'Inactivas'],
    currentSubrouteIndex: 0,
    onSubrouteTap: (_) {},
  );
}
