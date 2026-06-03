# How to add a reusable widget

## Paso a paso

### 1. Crear el widget

En `packages/mobile_ui/lib/src/widgets/`:

```dart
import 'package:flutter/material.dart';

class AppMiWidget extends StatelessWidget {
  const AppMiWidget({
    required this.label,
    this.onPressed,
    this.variant = AppMiWidgetVariant.primary,
    super.key,
  });

  final String label;
  final VoidCallback? onPressed;
  final AppMiWidgetVariant variant;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    // Usar theme.colors, no Colors.* directamente
    return ...
  }
}

enum AppMiWidgetVariant { primary, secondary, ghost }
```

Reglas:
- Usar `Theme.of(context)` para colores/tipografía
- `const` constructor siempre que sea posible
- Sin importaciones de `mobile_domain` (sin lógica de negocio)
- Sin dependencias de features de la app

### 2. Exportar del barrel

En `packages/mobile_ui/lib/mobile_ui.dart`:

```dart
export 'src/widgets/app_mi_widget.dart';
```

### 3. Si tiene variantes: agregar al DevWidgetCatalogScreen

En `apps/mobile/lib/app/bootstrap/dev_loader_screen.dart`:

Agregar una sección de demostración del nuevo widget con variantes.

### 4. Usar desde la app

```dart
import 'package:mobile_ui/mobile_ui.dart';

// En cualquier screen:
AppMiWidget(
  label: 'Acción',
  onPressed: () {},
  variant: AppMiWidgetVariant.primary,
)
```

## ¿Cuándo crear un widget reusable?

- El mismo patrón UI aparece en ≥3 lugares
- El widget no tiene dependencias de negocio
- La interfaz es estable (no va a cambiar la semana que viene)

## ¿Cuándo NO crearlo?

- Es específico de una sola feature → queda en `lib/features/*/presentation/widgets/`
- Tiene lógica de negocio → separar UI en widget, lógica en controller
- Es experimental → queda en `dev/playground/`
