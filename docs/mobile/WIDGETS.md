# Widget System

All reusable UI widgets live in the **`mobile_ui` package** (`packages/mobile_ui/`). The app itself (`apps/mobile/lib/app/widgets/` and `apps/mobile/lib/app/theme/`) contains only thin delegation files that re-export from the package.

## Package Structure

```
packages/mobile_ui/lib/src/
├── theme/
│   ├── app_colors.dart         # ColorScheme definitions (light + dark)
│   ├── app_text_theme.dart     # Manrope + Inter Typography
│   ├── app_radii.dart          # Radius constants
│   ├── app_theme.dart          # ThemeData factory (light/dark)
│   ├── app_theme_notifier.dart # InheritedWidget for theme toggle
│   └── theme_extensions.dart   # AppThemeTokens (spacing, radii)
└── widgets/
    ├── app_badge.dart          # Status badge
    ├── app_bottom_nav.dart     # Bottom navigation bar
    ├── app_breadcrumb.dart     # Breadcrumb trail
    ├── app_button.dart         # Button (primary, secondary, ghost)
    ├── app_card.dart           # Card (front + back, flip)
    ├── app_centered_loader.dart  # Centered spinner
    ├── app_confirm_dialog.dart   # Confirmation dialog
    ├── app_entity_row_card.dart  # Entity row card
    ├── app_metric_card.dart      # Metric/stat display
    ├── app_scaffold.dart         # Screen scaffold
    ├── app_section_header.dart   # Section header
    ├── app_segmented_filter.dart # Segmented control filter
    ├── app_status_banner.dart    # Status/info banner
    ├── app_term_help.dart        # Help terms & definitions
    ├── app_text_field.dart       # Text input
    ├── app_timeline.dart         # Timeline widget
    ├── app_top_bar.dart          # Top app bar
    ├── app_voice_fab.dart        # Voice FAB
    ├── dashed_border_painter.dart  # Dashed border
    ├── refresh_scope.dart        # Pull-to-refresh scope
    └── cards/
        ├── app_assignment_card.dart
        ├── app_assignment_list_item.dart
        ├── app_centered_badge_card.dart
        ├── app_experience_card.dart
        ├── app_image_feature_card.dart
        ├── app_logbook_timeline.dart
        ├── app_pricing_tiers_table.dart
        ├── app_selectable_card.dart
        └── app_stats_card.dart
```

## Design Tokens

### `AppColors` (`theme/app_colors.dart`)

Two complete `ColorScheme` definitions (Material 3):

- **`darkColorScheme`** — Dark theme, surface at `#131313`, primary white
- **`lightColorScheme`** — Light theme, surface at `#F7F7F7`, primary `#1A1C1C`

Standalone semantic colors:
- `success` — `#2E7D32`
- `warning` — `#F9A825`
- `danger` — `#B3261E`

### `AppTextThemes` (`theme/app_text_theme.dart`)

Two font families:
- **Manrope** — Display and headline styles (weight 600-700)
- **Inter** — Title, body, label styles (weight 400-600)

Full `TextTheme` with all 15 styles: `displayLarge` through `labelSmall`. Each style includes `fontFamily`, `fontSize`, `fontWeight`, `height`, and `color`.

### `AppRadii` (`theme/app_radii.dart`)

| Token | Radius value |
|-------|-------------|
| `defaultRadius` | `2` |
| `lg` | `4` |
| `xl` | `8` |
| `full` | `12` |

## Theme Extensions

`AppThemeTokens` (`theme/theme_extensions.dart`) extends `ThemeExtension<AppThemeTokens>`, providing custom tokens beyond Material 3:

```
radiusSm  → defaultRadius (2)
radiusMd  → lg (4)
radiusLg  → xl (8)
radiusXl  → full (12)
spaceXs   → 4
spaceSm   → 8
spaceMd   → 12
spaceLg   → 16
spaceXl   → 24
```

**Access in widgets:**
```dart
final tokens = Theme.of(context).appTokens;
// tokens.spaceMd, tokens.radiusLg, etc.
```

The `ThemeDataX` extension on `ThemeData` adds the `.appTokens` getter.

### `AppTheme` (`theme/app_theme.dart`)

Factory class with `light()` and `dark()` static methods that produce `ThemeData` with:
- Material 3 enabled
- Full `ColorScheme` from `AppColors`
- Scaffold background color
- Custom text theme
- `AppThemeTokens.base()` extension
- Styled `AppBarTheme`, `CardTheme`, `InputDecorationTheme`, `ElevatedButtonTheme`, `OutlinedButtonTheme`, `TextButtonTheme`, `ChipTheme`, `DividerTheme`, `BottomSheetTheme`

### `AppThemeNotifier` (`theme/app_theme_notifier.dart`)

Minimal `InheritedWidget` that exposes a `VoidCallback onToggle` for theme switching. Used by screens that need a theme toggle button.

## Key Widgets Reference

| Widget | Purpose |
|--------|---------|
| `AppBadge` | Status label pill (`neutral`, `primary`, `success`, `danger`, `warning`, `ghost`) |
| `AppBottomNav` | 5-tab bottom navigation with `AppNavItem` enum |
| `AppButton` | Primary/secondary/ghost action button with icon |
| `AppCard` | Container with optional flip animation |
| `AppScaffold` | Standard screen layout (top bar, bottom nav, padding) |
| `AppSectionHeader` | Eyebrow + title heading |
| `AppStatusBanner` | Contextual info/warning/danger banner |
| `AppTextField` | Styled input with variants (default/underlined) |
| `AppSegmentedFilter` | Segmented control filter |
| `AppMetricCard` | Stat display card |
| `AppEntityRowCard` | Entity list item with badge |
| `AppTopBar` | Top bar with logo and title |
| `AppVoiceFab` | Floating action button for voice |
| `AppAssignmentCard` | Complex card showing participant+equine+saddle assignment |
| `AppExperienceCard` | Experience listing card (commercial/compact/operational) |
| `AppTimeline` | Vertical timeline with nodes |
| `AppLogbookTimeline` | Logbook entry timeline with photos and highlights |
| `AppCenteredLoader` | Centered loading spinner |
| `RefreshScope` | Pull-to-refresh wrapper |

## How to Add a Widget

1. **Determine location**: If the widget is reusable across features, add it to `packages/mobile_ui/lib/src/widgets/`. If it's feature-specific, add it to `lib/features/<feature>/presentation/widgets/`.

2. **Create widget file** in the appropriate `widgets/` directory. Use `app_` prefix for shared widgets.

3. **Export** from `packages/mobile_ui/lib/mobile_ui.dart` if the widget is in the shared package.

4. **Design tokens**: Use `Theme.of(context).appTokens` for spacing/radii, `Theme.of(context).colorScheme` for colors, and `Theme.of(context).textTheme` for typography. Never hardcode values that have token equivalents.

5. **Widget catalog**: Add an example to `DevWidgetCatalogScreen` (`app/bootstrap/dev_loader_screen.dart`) so the widget is visible in the design system explorer.

6. **No business logic**: Shared widgets must not import from `mobile/features/`. They receive data via constructor parameters and callbacks.

7. **Single icon family**: Use `material_symbols_icons` for all icons. Verify icon exists in the chosen weight before committing.

8. **State handling**: Widgets should handle loading, error, empty, and success visual states where applicable.

## Voice UI (`packages/mobile_ui/lib/src/voice/`)

Subsistema de interacción por voz (prototipo, release-guarded):

| Archivo | Propósito |
|---------|-----------|
| `voice_context.dart` | `VoiceContext` — estado global de voz (escuchando, procesando, idle) |
| `voice_route.dart` | `VoiceRoute` — ruta navegable desde comando de voz |
| `voice_screen.dart` | Pantalla full-screen para interacción por voz |
| `voice_visualizer.dart` | `VoiceVisualizer` — widget animado de ondas de sonido |

Activado vía `AppVoiceFab` en pantallas operativas. Reconocimiento local (sin cloud).
