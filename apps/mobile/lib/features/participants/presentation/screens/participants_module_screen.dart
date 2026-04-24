import 'package:flutter/material.dart';

import '../../../../app/widgets/app_badge.dart';
import '../../../../app/widgets/app_entity_row_card.dart';
import '../../../../app/widgets/app_metric_card.dart';
import '../../../../app/widgets/app_timeline.dart';
import '../../../reservations/presentation/models/reservation_view_models.dart';
import '../controllers/participants_controller.dart';
import '../../../shared/presentation/widgets/module_subroute_header.dart';

class ParticipantsModuleScreen extends StatefulWidget {
  const ParticipantsModuleScreen({super.key});

  @override
  State<ParticipantsModuleScreen> createState() =>
      _ParticipantsModuleScreenState();
}

class _ParticipantsModuleScreenState extends State<ParticipantsModuleScreen> {
  static const List<ReservationParticipantRecord> _participants =
      ReservationPresentationFixtures.participants;

  late final ParticipantsController _controller;

  @override
  void initState() {
    super.initState();
    _controller = ParticipantsController();
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
                eyebrow: 'Participantes',
                title: 'Gestion de participantes',
                subtitle: 'Completitud de datos y validaciones por reserva',
                subrouteLabels: const ['Resumen', 'Listado', 'Historial'],
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
      case ParticipantsSubroute.resumen:
        final pending = _participants
            .where((item) => !item.isComplete)
            .length
            .toString()
            .padLeft(2, '0');
        return Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            AppMetricCard(
              title: 'Participantes incompletos',
              value: pending,
              suffix: 'CASOS',
              tone: AppMetricCardTone.danger,
              icon: Icons.warning_amber_rounded,
            ),
            const SizedBox(height: 12),
            const AppEntityRowCard(
              title: 'Consentimientos',
              subtitle: 'Verifica antes de confirmar reserva',
              badge: AppBadge(
                label: 'Critico',
                tone: AppBadgeTone.warning,
                uppercase: false,
              ),
            ),
          ],
        );
      case ParticipantsSubroute.participantes:
        return ListView.builder(
          shrinkWrap: true,
          physics: const NeverScrollableScrollPhysics(),
          itemCount: _participants.length,
          itemBuilder: (context, i) {
            return Padding(
              padding: EdgeInsets.only(
                bottom: i < _participants.length - 1 ? 10 : 0,
              ),
              child: AppEntityRowCard(
                title: _participants[i].fullName,
                subtitle:
                    'Reserva ${_participants[i].reservationCode} - Completitud ${_participants[i].completionLabel}',
                badge: AppBadge(
                  label: _participants[i].isComplete
                      ? 'Completo'
                      : 'Incompleto',
                  tone: _participants[i].isComplete
                      ? AppBadgeTone.success
                      : AppBadgeTone.warning,
                  uppercase: false,
                ),
              ),
            );
          },
        );
      case ParticipantsSubroute.historial:
        return const AppTimeline(
          children: [
            AppTimelineItem(
              state: AppTimelineNodeState.completed,
              child: AppTimelineEntryCard(
                date: '24 Oct 2026 - 08:45',
                title: 'Consentimiento firmado',
                badge: AppBadge(label: 'OK', tone: AppBadgeTone.success),
                description: 'Reserva RV-1042 consolidada.',
              ),
            ),
            AppTimelineItem(
              state: AppTimelineNodeState.active,
              child: AppTimelineEntryCard(
                date: '24 Oct 2026 - 07:58',
                title: 'Documento pendiente',
                badge: AppBadge(label: 'Pendiente', tone: AppBadgeTone.warning),
                description: 'Falta identificacion de participante.',
              ),
            ),
          ],
        );
    }
  }
}
