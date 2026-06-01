import 'package:flutter/material.dart';
import 'package:material_symbols_icons/material_symbols_icons.dart';

import '../../../../app/widgets/app_badge.dart';
import '../../../../app/widgets/app_button.dart';
import '../../../../app/widgets/app_centered_loader.dart';
import '../../../../app/widgets/app_scaffold.dart';
import '../../../../app/widgets/cards/app_logbook_timeline.dart';

/// Pantalla completa del timeline de un equino.
///
/// Muestra el historial cronológico de servicios, eventos y observaciones.
/// Por ahora usa datos mock — se conectará al backend cuando el endpoint
/// esté disponible.
class EquineTimelineScreen extends StatefulWidget {
  final String equineId;
  final String equineName;

  const EquineTimelineScreen({
    super.key,
    required this.equineId,
    required this.equineName,
  });

  @override
  State<EquineTimelineScreen> createState() => _EquineTimelineScreenState();
}

class _EquineTimelineScreenState extends State<EquineTimelineScreen> {
  // TODO: Reemplazar con llamada real al backend.
  bool _isLoading = false;
  List<AppLogbookTimelineEntry> _entries = [];
  bool _hasError = false;

  @override
  void initState() {
    super.initState();
    _loadMockEntries();
  }

  void _loadMockEntries() {
    setState(() {
      _isLoading = true;
      _hasError = false;
    });

    // Simula carga async.
    Future<void>.delayed(const Duration(milliseconds: 300), () {
      if (!mounted) return;
      setState(() {
        _entries = _buildMockEntries();
        _isLoading = false;
      });
    });
  }

  List<AppLogbookTimelineEntry> _buildMockEntries() {
    return [
      AppLogbookTimelineEntry(
        title: 'Servicio de monta',
        dateLabel: '15/03/2026',
        reservationLabel: 'RES-001',
        guideLabel: 'Carlos',
        durationLabel: '2h',
        state: AppLogbookEntryState.completed,
        badge: AppBadge(
          label: 'Completado',
          tone: AppBadgeTone.success,
          uppercase: false,
        ),
        observations:
            'Equino en buen estado general. Se comportó de manera tranquila durante todo el recorrido.',
        onTap: () {},
      ),
      AppLogbookTimelineEntry(
        title: 'Control veterinario',
        dateLabel: '10/03/2026',
        reservationLabel: 'VET-023',
        guideLabel: 'Dra. Martínez',
        durationLabel: '45min',
        state: AppLogbookEntryState.completed,
        badge: AppBadge(
          label: 'Revisión',
          tone: AppBadgeTone.neutral,
          uppercase: false,
        ),
        observations: 'Vacunación antirrábica al día. Desparasitación interna aplicada. Sin novedades.',
      ),
      AppLogbookTimelineEntry(
        title: 'Servicio de cabalgata',
        dateLabel: '08/03/2026',
        reservationLabel: 'RES-089',
        guideLabel: 'María',
        durationLabel: '3h',
        state: AppLogbookEntryState.completed,
        badge: AppBadge(
          label: 'Completado',
          tone: AppBadgeTone.success,
          uppercase: false,
        ),
        observations: 'Recorrido medialuna. Clima favorable. Equino respondedó bien al trote.',
      ),
      AppLogbookTimelineEntry(
        title: 'Mantenimiento de herraje',
        dateLabel: '01/03/2026',
        reservationLabel: 'HER-005',
        guideLabel: 'Pedro',
        durationLabel: '1h',
        state: AppLogbookEntryState.completed,
        badge: AppBadge(
          label: 'Rutina',
          tone: AppBadgeTone.neutral,
          uppercase: false,
        ),
        observations: 'Cambio de herraduras traseras. Cascos en buen estado.',
      ),
      AppLogbookTimelineEntry(
        title: 'Servicio de monta',
        dateLabel: '28/02/2026',
        reservationLabel: 'RES-076',
        guideLabel: 'Carlos',
        durationLabel: '2h',
        state: AppLogbookEntryState.active,
        badge: AppBadge(
          label: 'En curso',
          tone: AppBadgeTone.primary,
          uppercase: false,
        ),
      ),
      AppLogbookTimelineEntry(
        title: 'Observación',
        dateLabel: '25/02/2026',
        reservationLabel: 'OBS-012',
        guideLabel: 'Admin',
        durationLabel: '—',
        state: AppLogbookEntryState.warning,
        badge: AppBadge(
          label: 'Pendiente',
          tone: AppBadgeTone.warning,
          uppercase: false,
        ),
        observations:
            'Se observa leve cojera en miembro anterior derecho. Programar revisión veterinaria.',
      ),
    ];
  }

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;

    return AppScaffold(
      appBar: AppBar(
        title: Text(
          widget.equineName,
          style: Theme.of(context).textTheme.titleLarge?.copyWith(
                fontWeight: FontWeight.w800,
              ),
        ),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_rounded),
          onPressed: () => Navigator.of(context).pop(),
        ),
      ),
      floatingActionButton: FloatingActionButton.small(
        onPressed: _onAddEntry,
        backgroundColor: scheme.primary,
        foregroundColor: scheme.onPrimary,
        child: const Icon(Icons.add_rounded),
      ),
      child: _buildBody(),
    );
  }

  Widget _buildBody() {
    final scheme = Theme.of(context).colorScheme;

    if (_isLoading) {
      return const AppCenteredLoader();
    }

    if (_hasError) {
      return Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(
              Symbols.error_rounded,
              size: 48,
              color: Theme.of(context).colorScheme.error,
            ),
            const SizedBox(height: 16),
            Text(
              'Error al cargar el historial',
              style: Theme.of(context).textTheme.titleMedium,
            ),
            const SizedBox(height: 16),
            AppButton(
              label: 'Reintentar',
              variant: AppButtonVariant.secondary,
              onPressed: _loadMockEntries,
            ),
          ],
        ),
      );
    }

    if (_entries.isEmpty) {
      return _buildEmptyState();
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // Timeline header
        Padding(
          padding: const EdgeInsets.only(bottom: 16),
          child: Row(
            children: [
              Text(
                'HISTORIAL COMPLETO',
                style: Theme.of(context).textTheme.titleMedium?.copyWith(
                      fontWeight: FontWeight.w800,
                      letterSpacing: 0.5,
                    ),
              ),
              const SizedBox(width: 8),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                decoration: BoxDecoration(
                  color: scheme.secondaryContainer,
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Text(
                  '${_entries.length}',
                  style: Theme.of(context).textTheme.labelSmall?.copyWith(
                        fontWeight: FontWeight.w800,
                      ),
                ),
              ),
              const Spacer(),
              Text(
                'Últimos 30 días',
                style: Theme.of(context).textTheme.bodySmall?.copyWith(
                      color: scheme.onSurfaceVariant,
                    ),
              ),
            ],
          ),
        ),

        // Timeline entries
        AppLogbookTimeline(
          entries: _entries,
        ),

        const SizedBox(height: 80), // Space for FAB
      ],
    );
  }

  Widget _buildEmptyState() {
    return Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(
            Symbols.history_rounded,
            size: 56,
            color: Theme.of(context).colorScheme.onSurfaceVariant,
          ),
          const SizedBox(height: 16),
          Text(
            'No hay registros en el timeline',
            style: Theme.of(context).textTheme.titleMedium?.copyWith(
                  color: Theme.of(context).colorScheme.onSurfaceVariant,
                ),
          ),
          const SizedBox(height: 8),
          Text(
            'Agregá el primer registro de actividad',
            style: Theme.of(context).textTheme.bodySmall?.copyWith(
                  color: Theme.of(context).colorScheme.onSurfaceVariant,
                ),
          ),
          const SizedBox(height: 24),
          AppButton(
            label: 'Agregar registro',
            icon: Icons.add_rounded,
            onPressed: _onAddEntry,
          ),
        ],
      ),
    );
  }

  void _onAddEntry() {
    // TODO: Abrir formulario de nuevo registro para el timeline.
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        content: Text('Nuevo registro — funcionalidad próximamente'),
      ),
    );
  }
}
