# Catalogo de widgets mobile (frontend)

Fecha de corte: 2026-04-22

## Alcance

- Repositorio analizado: `apps/mobile/lib`
- Estado actual de `packages/mobile_ui`: sin widgets implementados aun
- Se listan widgets publicos (no clases privadas con prefijo `_`)

## Widgets de shell y app

### `LaJuanaApp`
Archivo: `apps/mobile/lib/app/app.dart`

```dart
const LaJuanaApp({super.key});
```

```dart
runApp(const LaJuanaApp());
```

### `AppThemeNotifier`
Archivo: `apps/mobile/lib/app/theme/app_theme_notifier.dart`

```dart
const AppThemeNotifier({
  super.key,
  required this.onToggle,
  required super.child,
});
```

```dart
AppThemeNotifier(
  onToggle: _toggleTheme,
  child: const SizedBox.shrink(),
)
```

### `HomePage`
Archivo: `apps/mobile/lib/home/home_page.dart`

```dart
const HomePage({super.key});
```

```dart
const HomePage()
```

### `DesignSystemPlayground`
Archivo: `apps/mobile/lib/playground/design_system_playground.dart`

```dart
const DesignSystemPlayground({super.key});
```

```dart
const DesignSystemPlayground()
```

## Widgets de voz

### `VoiceScreen`
Archivo: `apps/mobile/lib/app/voice/voice_screen.dart`

```dart
const VoiceScreen({
  super.key,
  required this.voiceContext,
});
```

```dart
VoiceScreen(voiceContext: VoiceContext.reservas)
```

### `VoiceVisualizer`
Archivo: `apps/mobile/lib/app/voice/voice_visualizer.dart`

```dart
const VoiceVisualizer({
  super.key,
  this.barCount = 6,
  this.color = Colors.white,
  this.barWidth = 6,
  this.minHeight = 12,
  this.maxHeight = 48,
  this.gap = 6,
  this.isActive = true,
});
```

```dart
const VoiceVisualizer(isActive: true)
```

## Widgets UI reutilizables (`app/widgets`)

### `AppScaffold`
Archivo: `apps/mobile/lib/app/widgets/app_scaffold.dart`

```dart
const AppScaffold({
  super.key,
  required this.child,
  this.appBar,
  this.bottomNavigationBar,
  this.floatingActionButton,
  this.scrollable = true,
  this.padding,
  this.backgroundColor,
});
```

```dart
AppScaffold(
  appBar: const AppTopBar(logoAssetPath: 'assets/branding/lajuana.svg'),
  child: const SizedBox.shrink(),
)
```

### `AppTopBar`
Archivo: `apps/mobile/lib/app/widgets/app_top_bar.dart`

```dart
const AppTopBar({
  super.key,
  required this.logoAssetPath,
  this.title = 'LA JUANA',
  this.onNotificationsTap,
  this.onThemeToggleTap,
  this.showNotificationDot = false,
});
```

```dart
const AppTopBar(logoAssetPath: 'assets/branding/lajuana.svg')
```

### `AppBottomNav`
Archivo: `apps/mobile/lib/app/widgets/app_bottom_nav.dart`

```dart
const AppBottomNav({
  super.key,
  required this.current,
  this.onTap,
});
```

```dart
AppBottomNav(
  current: AppNavItem.inicio,
  onTap: (item) {},
)
```

### `AppButton`
Archivo: `apps/mobile/lib/app/widgets/app_button.dart`

```dart
const AppButton({
  super.key,
  required this.label,
  required this.onPressed,
  this.icon,
  this.variant = AppButtonVariant.primary,
  this.expanded = false,
  this.height = 52,
});
```

```dart
AppButton(
  label: 'Crear',
  icon: Icons.add,
  onPressed: () {},
)
```

### `AppBadge`
Archivo: `apps/mobile/lib/app/widgets/app_badge.dart`

```dart
const AppBadge({
  super.key,
  required this.label,
  this.tone = AppBadgeTone.neutral,
  this.size = AppBadgeSize.sm,
  this.icon,
  this.uppercase = true,
});
```

```dart
const AppBadge(label: 'Pendiente', tone: AppBadgeTone.neutral)
```

### `AppCard`
Archivo: `apps/mobile/lib/app/widgets/app_card.dart`

```dart
const AppCard({
  super.key,
  required this.child,
  this.backChild,
  this.tone = AppCardTone.high,
  this.padding,
  this.accentColor,
  this.outlined = false,
  this.onTap,
});
```

```dart
AppCard(
  tone: AppCardTone.high,
  onTap: () {},
  child: const Text('Contenido'),
)
```

### `AppSectionHeader`
Archivo: `apps/mobile/lib/app/widgets/app_section_header.dart`

```dart
const AppSectionHeader({
  super.key,
  required this.title,
  this.eyebrow,
  this.subtitle,
  this.trailing,
  this.variant = AppSectionHeaderVariant.hero,
  this.padding,
});
```

```dart
const AppSectionHeader(
  eyebrow: 'Inicio',
  title: 'Supervision operacional',
)
```

### `AppMetricCard`
Archivo: `apps/mobile/lib/app/widgets/app_metric_card.dart`

```dart
const AppMetricCard({
  super.key,
  required this.title,
  required this.value,
  this.suffix,
  this.supportingText,
  this.icon,
  this.tone = AppMetricCardTone.defaultTone,
  this.compact = false,
});
```

```dart
const AppMetricCard(title: 'Total', value: '124', suffix: 'ITEMS')
```

### `AppEntityRowCard`
Archivo: `apps/mobile/lib/app/widgets/app_entity_row_card.dart`

```dart
const AppEntityRowCard({
  super.key,
  required this.title,
  required this.subtitle,
  this.badge,
  this.selected = false,
  this.onTap,
  this.accentColor,
  this.leading,
  this.trailing,
});
```

```dart
const AppEntityRowCard(
  title: 'Elena Rodriguez',
  subtitle: 'EXP: INTERMEDIO',
)
```

### `AppBreadcrumb`
Archivo: `apps/mobile/lib/app/widgets/app_breadcrumb.dart`

```dart
const AppBreadcrumb({
  super.key,
  required this.items,
  this.separator = '>',
});
```

```dart
const AppBreadcrumb(items: ['Gestion', 'Experiencias'])
```

### `AppSegmentedFilter<T>`
Archivo: `apps/mobile/lib/app/widgets/app_segmented_filter.dart`

```dart
const AppSegmentedFilter({
  super.key,
  required this.items,
  required this.value,
  required this.onChanged,
  this.expanded = true,
});
```

```dart
AppSegmentedFilter<String>(
  value: 'pendientes',
  onChanged: (value) {},
  items: const [
    AppSegmentedFilterItem(label: 'Pendientes', value: 'pendientes'),
    AppSegmentedFilterItem(label: 'Confirmadas', value: 'confirmadas'),
  ],
)
```

### `AppTextField`
Archivo: `apps/mobile/lib/app/widgets/app_text_field.dart`

```dart
const AppTextField({
  super.key,
  this.controller,
  this.label,
  this.hintText,
  this.suffix,
  this.maxLines = 1,
  this.variant = AppTextFieldVariant.filled,
  this.keyboardType,
  this.onChanged,
  this.focusNode,
  this.autofocus = false,
  this.readOnly = false,
  this.onTap,
});
```

```dart
AppTextField(
  label: 'Buscar',
  hintText: 'Nombre de cliente',
  onChanged: (value) {},
)
```

### `AppTimeline`
Archivo: `apps/mobile/lib/app/widgets/app_timeline.dart`

```dart
const AppTimeline({
  super.key,
  required this.children,
  this.lineLeft = 12,
  this.padding,
});
```

```dart
const AppTimeline(
  children: [
    AppTimelineItem(
      state: AppTimelineNodeState.active,
      child: AppTimelineEntryCard(date: '2026-10-24', title: 'Monta controlada'),
    ),
  ],
)
```

### `AppTimelineItem`
Archivo: `apps/mobile/lib/app/widgets/app_timeline.dart`

```dart
const AppTimelineItem({
  super.key,
  required this.state,
  required this.child,
  this.lineLeft = 12,
  this.nodeSize = 20,
  this.margin,
});
```

```dart
const AppTimelineItem(
  state: AppTimelineNodeState.completed,
  child: AppTimelineEntryCard(date: '2026-09-15', title: 'Vacunacion anual'),
)
```

### `AppTimelineEntryCard`
Archivo: `apps/mobile/lib/app/widgets/app_timeline.dart`

```dart
const AppTimelineEntryCard({
  super.key,
  required this.date,
  required this.title,
  this.description,
  this.badge,
  this.highlightedContent,
  this.footer,
});
```

```dart
const AppTimelineEntryCard(
  date: '2026-10-24',
  title: 'Monta controlada',
  description: 'Detalle del evento',
)
```

### `AppTimelineMetrics`
Archivo: `apps/mobile/lib/app/widgets/app_timeline.dart`

```dart
const AppTimelineMetrics({
  super.key,
  required this.items,
});
```

```dart
const AppTimelineMetrics(
  items: [
    AppTimelineMetricItem(value: '12', label: 'Activas'),
    AppTimelineMetricItem(value: '03', label: 'Pendientes'),
  ],
)
```

### `AppVoiceFab`
Archivo: `apps/mobile/lib/app/widgets/app_voice_fab.dart`

```dart
const AppVoiceFab({
  super.key,
  this.onTap,
  this.size = 76,
  this.elevated = true,
  this.icon = Icons.mic_rounded,
});
```

```dart
AppVoiceFab(onTap: () {}, icon: Icons.mic_rounded)
```

## Widgets UI reutilizables (`app/widgets/cards`)

### `AppSelectableCard`
Archivo: `apps/mobile/lib/app/widgets/cards/app_selectable_card.dart`

```dart
const AppSelectableCard({
  super.key,
  required this.child,
  this.selected = false,
  this.accentColor,
  this.onTap,
  this.padding,
  this.borderRadius,
  this.backgroundColor,
});
```

```dart
AppSelectableCard(
  selected: true,
  onTap: () {},
  child: const Text('Cosaco 24'),
)
```

### `AppImageFeatureCard`
Archivo: `apps/mobile/lib/app/widgets/cards/app_image_feature_card.dart`

```dart
const AppImageFeatureCard({
  super.key,
  required this.title,
  required this.subtitle,
  required this.image,
  this.badge,
  this.selected = false,
  this.onTap,
  this.width = 240,
  this.imageHeight = 160,
});
```

```dart
AppImageFeatureCard(
  title: 'Cosaco 24',
  subtitle: 'Criollo',
  image: const AssetImage('assets/images/equino.jpg'),
)
```

### `AppStatsCard`
Archivo: `apps/mobile/lib/app/widgets/cards/app_stats_card.dart`

```dart
const AppStatsCard({
  super.key,
  required this.eyebrow,
  required this.title,
  required this.children,
  this.topRight,
  this.selected = false,
  this.onTap,
});
```

```dart
AppStatsCard(
  eyebrow: 'Resumen',
  title: 'Rendimiento',
  children: const [Text('Metricas')],
)
```

### `AppExperienceCard`
Archivo: `apps/mobile/lib/app/widgets/cards/app_experience_card.dart`

```dart
const AppExperienceCard({
  super.key,
  required this.data,
  this.variant = AppExperienceCardVariant.commercial,
  this.primaryActionLabel,
  this.onTap,
  this.onPrimaryAction,
  this.enabled = true,
  this.selected = false,
});
```

### `AppPricingTiersTable`
Archivo: `apps/mobile/lib/app/widgets/cards/app_pricing_tiers_table.dart`

```dart
const AppPricingTiersTable({
  super.key,
  required this.tiers,
  this.currency = 'COP',
  this.pricesAreNet = true,
  this.notes,
});
```

## Tipos de apoyo usados por los widgets

```dart
enum AppBadgeTone { neutral, primary, success, danger, warning, ghost }
enum AppBadgeSize { sm, md }
enum AppButtonVariant { primary, secondary, ghost }
enum AppCardTone { surface, high, low, error }
enum AppMetricCardTone { defaultTone, danger, inverse }
enum AppExperienceCardVariant { compact, commercial, operational }
enum AppSectionHeaderVariant { hero, compact }
enum AppTextFieldVariant { filled, underlined }
enum AppTimelineNodeState { active, completed, cancelled, error, neutral }
enum AppNavItem { none, inicio, reservas, equinos, clientes, mas }
enum VoiceContext { inicio, reservas, equinos, clientes, mas }
enum VoiceRecordState { listening, paused, ready }

class AppSegmentedFilterItem<T> {
  final String label;
  final T value;
  const AppSegmentedFilterItem({required this.label, required this.value});
}

class AppTimelineMetricItem {
  final String value;
  final String label;
  const AppTimelineMetricItem({required this.value, required this.label});
}

class AppOperationalBadgeData {
  final String label;
  final IconData? icon;
  final AppBadgeTone tone;
}

class AppExperienceCardData {
  final String title;
  final String description;
  final ImageProvider? image;
  final String? priceLabel;
  final String? priceCaption;
  final String activityDurationLabel;
  final String routeDurationLabel;
  final String? distanceLabel;
  final String? terrainLabel;
  final String difficultyLabel;
  final String? capacityLabel;
  final List<String> inclusions;
  final List<AppOperationalBadgeData> badges;
}

class AppPricingTierData {
  final int minParticipants;
  final int maxParticipants;
  final int pricePerPerson;
}
```
