import 'package:flutter/material.dart';
import 'package:material_symbols_icons/material_symbols_icons.dart';

import 'package:mobile_ui/src/widgets/app_button.dart';
import 'package:mobile_ui/src/widgets/app_centered_loader.dart';
import 'package:mobile_ui/src/widgets/app_scaffold.dart';
import 'package:mobile_ui/src/widgets/app_segmented_filter.dart';
import 'package:mobile_ui/src/widgets/refresh_scope.dart';
import 'package:mobile_ui/src/widgets/cards/app_logbook_timeline.dart';
import 'package:mobile_domain/src/equines/equine_event_repository.dart';
import 'package:mobile_domain/src/equines/equine_repository.dart';
import 'package:mobile_domain/src/equines/equine_timeline_entry.dart';
import 'package:mobile/features/equines/infrastructure/mappers/equine_mapper.dart';
import 'package:mobile/features/equines/presentation/controllers/equine_events_controller.dart';
import 'package:mobile/features/equines/presentation/screens/equine_event_form_screen.dart';

/// Pantalla completa del timeline de un equino.
///
/// Muestra el historial cronológico de servicios, eventos y observaciones
/// obtenido desde el backend mediante [EquineRepository.getEquineTimeline].
class EquineTimelineScreen extends StatefulWidget {
  final String equineId;
  final String equineName;
  final EquineRepository repository;
  final EquineEventRepository eventRepository;

  const EquineTimelineScreen({
    super.key,
    required this.equineId,
    required this.equineName,
    required this.repository,
    required this.eventRepository,
  });

  @override
  State<EquineTimelineScreen> createState() => _EquineTimelineScreenState();
}

class _EquineTimelineScreenState extends State<EquineTimelineScreen>
    with RefreshableState {
  bool _isLoading = false;
  List<EquineTimelineEntry> _domainEntries = [];
  String? _category;
  bool _hasError = false;

  // Categorías para filtrar la bitácora. Agrupan los tipos de evento en cubos
  // navegables sin saturar la barra de filtros.
  static const _healthTypes = <String>{
    'health_check', 'injury', 'treatment', 'medication', 'vaccination',
    'farrier', 'hoof_care', 'dentistry', 'lab_test',
  };
  static const _availabilityTypes = <String>{
    'rest', 'availability_change',
  };

  String _categoryOf(EquineTimelineEntry e) {
    if (e.source != 'equine_event') return 'servicio';
    if (e.affectsAvailability || _availabilityTypes.contains(e.eventType)) {
      return 'disponibilidad';
    }
    if (_healthTypes.contains(e.eventType)) return 'salud';
    return 'manejo';
  }

  List<EquineTimelineEntry> get _filteredDomain {
    if (_category == null) return _domainEntries;
    return _domainEntries
        .where((e) => _categoryOf(e) == _category)
        .toList(growable: false);
  }

  @override
  Future<void> onRefresh() => _loadTimeline();

  @override
  void initState() {
    super.initState();
    _loadTimeline();
  }

  Future<void> _loadTimeline() async {
    setState(() {
      _isLoading = true;
      _hasError = false;
    });

    try {
      await widget.eventRepository.flushPendingEvents(
        equineId: widget.equineId,
      );
      final domainEntries = await widget.repository.getEquineTimeline(
        widget.equineId,
      );
      final pending = await widget.eventRepository.listPendingEvents(
        widget.equineId,
      );
      final merged = <EquineTimelineEntry>[
        ...domainEntries,
        ...pending.map(EquineMapper.eventToTimelineEntry),
      ]..sort((a, b) => b.happenedAt.compareTo(a.happenedAt));

      if (!mounted) return;
      setState(() {
        _domainEntries = merged;
        _isLoading = false;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _hasError = true;
        _isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;

    return AppScaffold(
      scrollable: _domainEntries.isNotEmpty,
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
      return const RefreshableViewport(child: AppCenteredLoader());
    }

    if (_hasError) {
      return RefreshableViewport(
        child: Center(
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
                onPressed: _loadTimeline,
              ),
            ],
          ),
        ),
      );
    }

    if (_domainEntries.isEmpty) {
      return RefreshableViewport(child: _buildEmptyState());
    }

    final filtered = _filteredDomain;
    final entries = filtered
        .map((e) => EquineMapper.timelineEntryToLogbookEntry(e))
        .toList(growable: false);

    return SingleChildScrollView(
      physics: const AlwaysScrollableScrollPhysics(),
      child: Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // Filtro por categoría de la bitácora.
        Padding(
          padding: const EdgeInsets.only(bottom: 16),
          child: _buildCategoryFilter(),
        ),

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
                  '${entries.length}',
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

        // Timeline entries (o aviso si el filtro no tiene registros).
        if (entries.isEmpty)
          Padding(
            padding: const EdgeInsets.symmetric(vertical: 48),
            child: Center(
              child: Text(
                'Sin registros en esta categoría',
                style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                      color: scheme.onSurfaceVariant,
                    ),
              ),
            ),
          )
        else
          AppLogbookTimeline(entries: entries),

        const SizedBox(height: 80), // Space for FAB
      ],
    ),
    );
  }

  Widget _buildCategoryFilter() {
    return AppSegmentedFilter<String?>(
      value: _category,
      onChanged: (value) => setState(() => _category = value),
      items: const [
        AppSegmentedFilterItem(label: 'TODOS', value: null),
        AppSegmentedFilterItem(label: 'SALUD', value: 'salud'),
        AppSegmentedFilterItem(label: 'DISPONIBILIDAD', value: 'disponibilidad'),
        AppSegmentedFilterItem(label: 'MANEJO', value: 'manejo'),
        AppSegmentedFilterItem(label: 'SERVICIO', value: 'servicio'),
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

  Future<void> _onAddEntry() async {
    final controller = EquineEventsController(
      repository: widget.eventRepository,
    );
    final saved = await Navigator.of(context).push<bool>(
      MaterialPageRoute<bool>(
        builder: (_) => EquineEventFormScreen(
          equineId: widget.equineId,
          equineName: widget.equineName,
          controller: controller,
        ),
      ),
    );
    if (saved == true) {
      await _loadTimeline();
    }
  }
}
