import 'package:flutter/material.dart';
import 'package:material_symbols_icons/material_symbols_icons.dart';

import '../../../../app/widgets/app_badge.dart';
import '../../../../app/widgets/app_centered_loader.dart';
import '../../../../app/widgets/app_entity_row_card.dart';
import '../../../../app/widgets/app_status_banner.dart';
import '../../domain/repositories/equine_repository.dart';
import '../controllers/equines_controller.dart';
import '../models/equine_view_models.dart';
import 'equine_detail_screen.dart';
import '../../../shared/presentation/widgets/module_subroute_header.dart';

class EquinesModuleScreen extends StatefulWidget {
  const EquinesModuleScreen({
    super.key,
    required this.repository,
  });

  final EquineRepository repository;

  @override
  State<EquinesModuleScreen> createState() => _EquinesModuleScreenState();
}

class _EquinesModuleScreenState extends State<EquinesModuleScreen> {
  late final EquinesController _controller;

  @override
  void initState() {
    super.initState();
    _controller = EquinesController(repository: widget.repository);
    _controller.addListener(_onChanged);
    _controller.loadEquines();
  }

  void _onChanged() {
    if (mounted) setState(() {});
  }

  @override
  void dispose() {
    _controller.removeListener(_onChanged);
    _controller.dispose();
    super.dispose();
  }

  Future<void> _onRefresh() => _controller.loadEquines();

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(24, 24, 24, 24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          ModuleSubrouteHeader(
            eyebrow: 'Equinos',
            title: 'Gestión de equinos',
            subtitle: 'Disponibilidad, historial y cuidado operativo',
            subrouteLabels: const [
              'Resumen',
              'Historial',
              'Disponibilidad',
              'Cuidado',
            ],
            currentSubrouteIndex: _controller.subroute.index,
            onSubrouteTap: (i) {
              _controller.selectSubrouteByIndex(i);
            },
          ),
          const SizedBox(height: 20),
          _buildSubrouteContent(),
        ],
      ),
    );
  }

  Widget _buildSubrouteContent() {
    switch (_controller.loadState) {
      case EquinesLoadState.idle:
      case EquinesLoadState.loading:
        return _buildLoading();
      case EquinesLoadState.error:
        return _buildError();
      case EquinesLoadState.empty:
        return _buildEmpty();
      case EquinesLoadState.success:
        return _buildList();
    }
  }

  Widget _buildLoading() {
    return ListView.builder(
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      itemCount: 5,
      itemBuilder: (_, __) => Padding(
        padding: const EdgeInsets.only(bottom: 10),
        child: AppEntityRowCard(
          title: 'Cargando...',
          subtitle: '···',
          badge: AppBadge(
            label: '···',
            tone: AppBadgeTone.neutral,
            uppercase: false,
          ),
        ),
      ),
    );
  }

  Widget _buildError() {
    return Center(
      child: AppStatusBanner(
        title: 'Error al cargar equinos',
        message: _controller.errorMessage,
        tone: AppStatusBannerTone.danger,
        onTap: _controller.loadEquines,
      ),
    );
  }

  Widget _buildEmpty() {
    return Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(
                Symbols.chess_knight,
                size: 56,
            color: Theme.of(context).colorScheme.onSurfaceVariant,
          ),
          const SizedBox(height: 16),
          Text(
            'No hay equinos sincronizados',
            style: Theme.of(context).textTheme.titleMedium?.copyWith(
                  color: Theme.of(context).colorScheme.onSurfaceVariant,
                ),
          ),
          const SizedBox(height: 8),
          Text(
            'Conectate al backend o verifica la conexion',
            style: Theme.of(context).textTheme.bodySmall?.copyWith(
                  color: Theme.of(context).colorScheme.onSurfaceVariant,
                ),
          ),
          const SizedBox(height: 24),
          FilledButton.icon(
            onPressed: _controller.loadEquines,
            icon: const Icon(Icons.refresh_rounded),
            label: const Text('Reintentar'),
          ),
        ],
      ),
    );
  }

  Widget _buildList() {
    final records = _controller.records;
    if (records.isEmpty) {
      return Center(
        child: Text(
          _emptyMessage(),
          style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                color: Theme.of(context).colorScheme.onSurfaceVariant,
              ),
        ),
      );
    }
    return ListView.builder(
        shrinkWrap: true,
        physics: const NeverScrollableScrollPhysics(),
        itemCount: records.length,
        itemBuilder: (context, i) {
          final e = records[i];
          return Padding(
            padding: EdgeInsets.only(
              bottom: i < records.length - 1 ? 10 : 0,
            ),
            child: AppEntityRowCard(
              title: e.name,
              subtitle: e.subtitle ?? e.summary,
              leading: _speciesIcon(e.species),
              badge: AppBadge(
                label: e.statusLabel,
                tone: e.statusTone,
                uppercase: false,
              ),
              trailing: const Icon(Icons.chevron_right_rounded, size: 18),
              onTap: () {
                Navigator.of(context).push(
                  MaterialPageRoute<void>(
                    builder: (_) => EquineDetailScreen(
                      equineId: e.id,
                      repository: widget.repository,
                    ),
                  ),
                );
              },
            ),
          );
        },
      );
  }

  Widget _speciesIcon(String species) {
    return Container(
      width: 40,
      height: 40,
      decoration: BoxDecoration(
        color: Theme.of(context).colorScheme.primaryContainer,
        borderRadius: BorderRadius.circular(8),
      ),
      child: Icon(
        Symbols.chess_knight,
        size: 22,
        color: Theme.of(context).colorScheme.onPrimaryContainer,
      ),
    );
  }

  String _emptyMessage() {
    switch (_controller.subroute) {
      case EquinesSubroute.resumen:
        return 'No hay equinos registrados';
      case EquinesSubroute.historial:
        return 'Sin historial disponible';
      case EquinesSubroute.disponibilidad:
        return 'No hay equinos disponibles';
      case EquinesSubroute.cuidado:
        return 'No hay equinos en cuidado';
    }
  }
}
