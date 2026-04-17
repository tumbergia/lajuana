import 'package:flutter/material.dart';
import '../app/widgets/app_button.dart';
import '../app/widgets/app_card.dart';
import '../app/widgets/app_scaffold.dart';
import '../app/widgets/app_text_field.dart';

/// Página de demostración del sistema de widgets Equus Command.
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
    final isDark = theme.brightness == Brightness.dark;

    return AppScaffold(
      eyebrow: 'Operational Module',
      title: 'Widget Demo',
      actions: [
        IconButton(
          tooltip: isDark ? 'Switch to light' : 'Switch to dark',
          icon: AnimatedSwitcher(
            duration: const Duration(milliseconds: 300),
            transitionBuilder: (child, anim) => RotationTransition(
              turns: Tween(begin: 0.75, end: 1.0).animate(anim),
              child: FadeTransition(opacity: anim, child: child),
            ),
            child: Icon(
              isDark ? Icons.light_mode_outlined : Icons.dark_mode_outlined,
              key: ValueKey(isDark),
            ),
          ),
          onPressed: onToggleTheme,
        ),
        const SizedBox(width: 4),
        Padding(
          padding: const EdgeInsets.only(right: 12),
          child: CircleAvatar(
            radius: 16,
            backgroundColor: scheme.surfaceContainerHighest,
            child: Text(
              'JC',
              style: theme.textTheme.labelSmall?.copyWith(
                color: scheme.onSurface,
                fontWeight: FontWeight.w800,
              ),
            ),
          ),
        ),
      ],
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // ── AppButton ──────────────────────────────────────────────────
          _SectionLabel('AppButton — todos en height:52, mismo ancho'),
          const SizedBox(height: 12),

          // Todos expanded:true → mismo ancho. Primary.
          AppButton(
            label: 'Create Reservation',
            icon: Icons.arrow_forward,
            variant: AppButtonVariant.primary,
            expanded: true,
            onPressed: () {},
          ),
          const SizedBox(height: 8),
          // Secondary
          AppButton(
            label: 'Register Participant',
            icon: Icons.person_add_alt_1,
            variant: AppButtonVariant.secondary,
            expanded: true,
            onPressed: () {},
          ),
          const SizedBox(height: 8),
          // Ghost
          AppButton(
            label: 'View All Historical Data',
            variant: AppButtonVariant.ghost,
            expanded: true,
            onPressed: () {},
          ),
          const SizedBox(height: 8),
          // Disabled — no escala al presionar, color muted
          AppButton(
            label: 'Sync Pending',
            icon: Icons.sync_outlined,
            variant: AppButtonVariant.primary,
            expanded: true,
            onPressed: null,
          ),
          const SizedBox(height: 8),
          // Inline (no expanded) — ancho por contenido, altura 52
          Row(
            children: [
              AppButton(
                label: 'Confirm',
                icon: Icons.check_circle_outline,
                variant: AppButtonVariant.primary,
                onPressed: () {},
              ),
              const SizedBox(width: 8),
              AppButton(
                label: 'Cancel',
                variant: AppButtonVariant.secondary,
                onPressed: () {},
              ),
            ],
          ),

          const SizedBox(height: 32),

          // ── AppCard — tonos ────────────────────────────────────────────
          _SectionLabel('AppCard — variantes de tono'),
          const SizedBox(height: 12),

          // High (por defecto) + acento primario
          AppCard(
            accentColor: scheme.primary,
            child: _ReservationContent(scheme: scheme),
          ),
          const SizedBox(height: 8),

          // Low + outlined
          AppCard(
            tone: AppCardTone.low,
            outlined: true,
            onTap: () {},
            child: Row(
              children: [
                Icon(Icons.pending_actions_outlined,
                    color: scheme.onSurfaceVariant),
                const SizedBox(width: 12),
                Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('Pending Records',
                        style: theme.textTheme.titleSmall
                            ?.copyWith(fontWeight: FontWeight.w700)),
                    Text('4 Health Logs awaiting entry',
                        style: theme.textTheme.bodySmall
                            ?.copyWith(color: scheme.onSurfaceVariant)),
                  ],
                ),
              ],
            ),
          ),
          const SizedBox(height: 8),

          // Error — bg rojo errorContainer, como en el mockup de inventory
          AppCard(
            tone: AppCardTone.error,
            accentColor: scheme.error,
            child: Row(
              children: [
                Icon(Icons.inventory_2_outlined, color: scheme.onErrorContainer),
                const SizedBox(width: 12),
                Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'LOW STOCK ALERT',
                      style: theme.textTheme.labelSmall?.copyWith(
                        color: scheme.onErrorContainer,
                        fontWeight: FontWeight.w800,
                        letterSpacing: 1.4,
                      ),
                    ),
                    Text(
                      'Premium Feed: 14kg remaining',
                      style: theme.textTheme.bodySmall?.copyWith(
                        color: scheme.onErrorContainer,
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),

          const SizedBox(height: 32),

          // ── AppCard — flip + redirección ──────────────────────────────
          _SectionLabel('AppCard — flip 3D (toca el card)'),
          const SizedBox(height: 12),

          AppCard(
            accentColor: scheme.primary,
            onTap: () {
              // Aquí iría: Navigator.of(context).push(...)
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(
                  content: Text('→ Navegando a detalle de reserva'),
                  duration: Duration(seconds: 2),
                ),
              );
            },
            backChild: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'DETALLE DE RESERVA',
                    style: theme.textTheme.labelSmall?.copyWith(
                      color: scheme.onSurfaceVariant,
                      letterSpacing: 1.8,
                      fontWeight: FontWeight.w800,
                    ),
                  ),
                  const SizedBox(height: 12),
                  Text(
                    'Alexander Sterling · OCT 24',
                    style: theme.textTheme.titleMedium?.copyWith(
                      fontFamily: 'Manrope',
                      fontWeight: FontWeight.w800,
                      color: scheme.onSurface,
                    ),
                  ),
                  const SizedBox(height: 8),
                  Text(
                    'Toca para ir al detalle completo →',
                    style: theme.textTheme.bodySmall?.copyWith(
                      color: scheme.primary,
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                ],
              ),
            ),
            child: _ReservationContent(scheme: scheme),
          ),

          const SizedBox(height: 32),

          // ── AppTextField ───────────────────────────────────────────────
          _SectionLabel('AppTextField'),
          const SizedBox(height: 12),

          const AppTextField(
            label: 'Search Participants',
            hintText: 'SEARCH PARTICIPANTS...',
            variant: AppTextFieldVariant.underlined,
          ),
          const SizedBox(height: 20),
          const AppTextField(
            label: 'Lead Guide',
            hintText: 'e.g. Marcus Vance',
            variant: AppTextFieldVariant.filled,
          ),
          const SizedBox(height: 20),
          const AppTextField(
            label: 'Observations',
            hintText:
                'Record terrain conditions, horse stamina, and weather anomalies...',
            variant: AppTextFieldVariant.underlined,
            maxLines: 4,
          ),
          const SizedBox(height: 32),
        ],
      ),
    );
  }
}

// ── Helpers ─────────────────────────────────────────────────────────────────

class _SectionLabel extends StatelessWidget {
  final String text;
  const _SectionLabel(this.text);

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Text(
      text.toUpperCase(),
      style: theme.textTheme.labelSmall?.copyWith(
        color: theme.colorScheme.onSurfaceVariant,
        letterSpacing: 1.8,
        fontWeight: FontWeight.w800,
      ),
    );
  }
}

class _ReservationContent extends StatelessWidget {
  final ColorScheme scheme;
  const _ReservationContent({required this.scheme});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Alexander Sterling',
                  style: theme.textTheme.titleMedium?.copyWith(
                    fontFamily: 'Manrope',
                    fontWeight: FontWeight.w800,
                    color: scheme.onSurface,
                  ),
                ),
                const SizedBox(height: 2),
                Text(
                  'sterling.a@lexus-group.com',
                  style: theme.textTheme.bodySmall
                      ?.copyWith(color: scheme.onSurfaceVariant),
                ),
              ],
            ),
            Container(
              padding:
                  const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
              color: scheme.surfaceContainerLow,
              child: Text(
                'QUOTED',
                style: theme.textTheme.labelSmall?.copyWith(
                  color: scheme.onSurface,
                  fontWeight: FontWeight.w800,
                  letterSpacing: 1.4,
                ),
              ),
            ),
          ],
        ),
        const SizedBox(height: 12),
        Container(
          padding:
              const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
          decoration: BoxDecoration(
            color: scheme.surfaceContainerLow,
            borderRadius: BorderRadius.circular(4),
          ),
          child: Row(
            children: [
              _Stat('DATE', 'OCT 24', scheme, theme),
              _Stat('TOTAL', r'$1,240', scheme, theme),
              _Stat('PAID', r'$620', scheme, theme),
            ],
          ),
        ),
      ],
    );
  }
}

class _Stat extends StatelessWidget {
  final String label;
  final String value;
  final ColorScheme scheme;
  final ThemeData theme;
  const _Stat(this.label, this.value, this.scheme, this.theme);

  @override
  Widget build(BuildContext context) {
    return Expanded(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(label,
              style: theme.textTheme.labelSmall?.copyWith(
                color: scheme.onSurfaceVariant,
                letterSpacing: 1.2,
                fontWeight: FontWeight.w700,
              )),
          const SizedBox(height: 2),
          Text(value,
              style: theme.textTheme.labelMedium?.copyWith(
                color: scheme.onSurface,
                fontWeight: FontWeight.w700,
              )),
        ],
      ),
    );
  }
}
