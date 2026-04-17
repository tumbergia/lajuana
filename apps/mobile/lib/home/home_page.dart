import 'package:flutter/material.dart';
import '../app/theme/theme_extensions.dart';

class HomePage extends StatelessWidget {
  final VoidCallback onToggleTheme;
  final ThemeMode themeMode;

  const HomePage({
    super.key,
    required this.onToggleTheme,
    required this.themeMode,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final scheme = theme.colorScheme;
    final tokens = theme.appTokens;

    final isDark = theme.brightness == Brightness.dark;

    return Scaffold(
      appBar: AppBar(
        title: const Text('La Juana'),
        actions: [
          IconButton(
            tooltip: isDark ? 'Cambiar a claro' : 'Cambiar a oscuro',
            icon: AnimatedSwitcher(
              duration: const Duration(milliseconds: 250),
              transitionBuilder: (child, animation) => RotationTransition(
                turns: animation,
                child: FadeTransition(opacity: animation, child: child),
              ),
              child: Icon(
                isDark ? Icons.light_mode_outlined : Icons.dark_mode_outlined,
                key: ValueKey(isDark),
              ),
            ),
            onPressed: onToggleTheme,
          ),
          const SizedBox(width: 4),
        ],
      ),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: ListView(
          children: [
            Text(
              'Sistema base',
              style: theme.textTheme.headlineMedium,
            ),
            const SizedBox(height: 8),
            Text(
              'El tema debe resolverse globalmente, no con condicionales por widget.',
              style: theme.textTheme.bodyLarge,
            ),
            const SizedBox(height: 16),
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('Reserva', style: theme.textTheme.titleLarge),
                    const SizedBox(height: 8),
                    Text(
                      'Estado: borrador local',
                      style: theme.textTheme.bodyMedium?.copyWith(
                        color: scheme.onSurfaceVariant,
                      ),
                    ),
                    const SizedBox(height: 16),
                    const Wrap(
                      spacing: 8,
                      runSpacing: 8,
                      children: [
                        Chip(label: Text('Offline')),
                        Chip(label: Text('Pendiente sync')),
                        Chip(label: Text('Participantes 4')),
                      ],
                    ),
                    const SizedBox(height: 16),
                    Row(
                      children: [
                        Expanded(
                          child: ElevatedButton(
                            onPressed: () {},
                            child: const Text('Continuar'),
                          ),
                        ),
                        const SizedBox(width: 12),
                        Expanded(
                          child: OutlinedButton(
                            onPressed: () {},
                            child: const Text('Cancelar'),
                          ),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 16),
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: scheme.surfaceContainerHigh,
                borderRadius: tokens.radiusLg,
                border: Border.all(color: scheme.outlineVariant),
              ),
              child: const TextField(
                decoration: InputDecoration(
                  labelText: 'Buscar',
                  hintText: 'Reserva, cliente, fecha...',
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
