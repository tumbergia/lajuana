import 'package:flutter/material.dart';

import '../../../../app/widgets/app_badge.dart';
import '../../../../app/widgets/app_entity_row_card.dart';
import '../../../../app/widgets/app_timeline.dart';
import '../controllers/equines_controller.dart';
import '../models/equine_demo_record.dart';
import '../../../shared/presentation/widgets/module_subroute_header.dart';

class EquinesModuleScreen extends StatefulWidget {
  const EquinesModuleScreen({super.key});

  @override
  State<EquinesModuleScreen> createState() => _EquinesModuleScreenState();
}

class _EquinesModuleScreenState extends State<EquinesModuleScreen> {
  static const List<EquineDemoRecord> _equines = <EquineDemoRecord>[
    EquineDemoRecord(
      name: 'Cosaco 24',
      summary: 'Disponible hoy 09:00-13:00',
      statusLabel: 'Disponible',
      statusTone: AppBadgeTone.success,
    ),
    EquineDemoRecord(
      name: 'Amanecer',
      summary: 'En servicio 11:30',
      statusLabel: 'Asignado',
      statusTone: AppBadgeTone.primary,
    ),
    EquineDemoRecord(
      name: 'Marte',
      summary: 'Observacion veterinaria activa',
      statusLabel: 'Cuidado',
      statusTone: AppBadgeTone.warning,
    ),
  ];

  late final EquinesController _controller;

  @override
  void initState() {
    super.initState();
    _controller = EquinesController();
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: _controller,
      builder: (context, _) {
        return Padding(
          padding: const EdgeInsets.fromLTRB(24, 24, 24, 24),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              ModuleSubrouteHeader(
                eyebrow: 'Equinos',
                title: 'Gestion de equinos',
                subtitle: 'Disponibilidad, historial y cuidado operativo',
                subrouteLabels: const [
                  'Resumen',
                  'Historial',
                  'Disponibilidad',
                  'Cuidado',
                ],
                currentSubrouteIndex: _controller.subroute.index,
                onSubrouteTap: _controller.selectSubrouteByIndex,
              ),
              const SizedBox(height: 20),
              _buildSubrouteContent(),
            ],
          ),
        );
      },
    );
  }

  Widget _buildSubrouteContent() {
    switch (_controller.subroute) {
      case EquinesSubroute.resumen:
        return ListView.builder(
          shrinkWrap: true,
          physics: const NeverScrollableScrollPhysics(),
          itemCount: _equines.length,
          itemBuilder: (context, i) {
            final e = _equines[i];
            return Padding(
              padding: EdgeInsets.only(
                bottom: i < _equines.length - 1 ? 10 : 0,
              ),
              child: AppEntityRowCard(
                title: e.name,
                subtitle: e.summary,
                badge: AppBadge(
                  label: e.statusLabel,
                  tone: e.statusTone,
                  uppercase: false,
                ),
                trailing: const Icon(Icons.chevron_right_rounded, size: 18),
              ),
            );
          },
        );
      case EquinesSubroute.historial:
        return const AppTimeline(
          children: [
            AppTimelineItem(
              state: AppTimelineNodeState.completed,
              child: AppTimelineEntryCard(
                date: '23 Oct 2026',
                title: 'Cosaco 24 - Servicio finalizado',
                badge: AppBadge(label: 'OK', tone: AppBadgeTone.success),
                description: 'Actividad completada sin novedades.',
              ),
            ),
            AppTimelineItem(
              state: AppTimelineNodeState.neutral,
              child: AppTimelineEntryCard(
                date: '22 Oct 2026',
                title: 'Marte - Revision veterinaria',
                badge: AppBadge(
                  label: 'Observacion',
                  tone: AppBadgeTone.warning,
                ),
                description: 'Control preventivo por fatiga leve.',
              ),
            ),
          ],
        );
      case EquinesSubroute.disponibilidad:
        return Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: const [
            AppEntityRowCard(
              title: 'COSACO 24',
              subtitle: 'Disponible: 09:00 - 13:00',
              badge: AppBadge(
                label: 'Disponible',
                tone: AppBadgeTone.success,
                uppercase: false,
              ),
            ),
            SizedBox(height: 10),
            AppEntityRowCard(
              title: 'AMANECER',
              subtitle: 'Asignado: 11:30 - 14:00',
              badge: AppBadge(
                label: 'Asignado',
                tone: AppBadgeTone.primary,
                uppercase: false,
              ),
            ),
          ],
        );
      case EquinesSubroute.cuidado:
        return Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: const [
            AppEntityRowCard(
              title: 'MARTE',
              subtitle: 'Control veterinario en curso',
              badge: AppBadge(
                label: 'Requiere seguimiento',
                tone: AppBadgeTone.warning,
                uppercase: false,
              ),
            ),
            SizedBox(height: 10),
            AppEntityRowCard(
              title: 'PRADERA',
              subtitle: 'Sin alertas activas',
              badge: AppBadge(
                label: 'Estable',
                tone: AppBadgeTone.success,
                uppercase: false,
              ),
            ),
          ],
        );
    }
  }
}
