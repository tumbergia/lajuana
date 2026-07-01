import 'package:flutter/material.dart';

import 'package:mobile_ui/src/widgets/refresh_scope.dart';
import 'package:mobile_domain/src/reservations/reservation_detail.dart';
import 'package:mobile_domain/src/reservations/reservations_repository.dart';
import 'package:mobile/features/reservations/presentation/helpers/reservation_status_labels.dart';

/// Full-screen client/holder detail view.
class ClientDetailView extends StatefulWidget {
  const ClientDetailView({
    super.key,
    required this.detail,
    this.repository,
    this.reservationId,
  });

  final ReservationDetail detail;
  final ReservationsRepository? repository;
  final String? reservationId;

  @override
  State<ClientDetailView> createState() => _ClientDetailViewState();
}

class _ClientDetailViewState extends State<ClientDetailView>
    with RefreshableState {
  late ReservationDetail _detail;
  bool _isRefreshing = false;

  @override
  void initState() {
    super.initState();
    _detail = widget.detail;
  }

  @override
  Future<void> onRefresh() async {
    final repo = widget.repository;
    final id = widget.reservationId ?? _detail.id;
    if (repo == null || id == null) return;

    setState(() => _isRefreshing = true);
    try {
      final refreshed = await repo.getReservationById(id);
      if (!mounted) return;
      setState(() {
        _detail = refreshed;
        _isRefreshing = false;
      });
    } catch (_) {
      if (mounted) setState(() => _isRefreshing = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final scheme = theme.colorScheme;
    final detail = _detail;

    final rows = <Widget>[];
    void addRow(String label, String? value) {
      rows.add(Padding(
        padding: const EdgeInsets.symmetric(vertical: 6),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            SizedBox(
              width: 120,
              child: Text(label,
                  style: theme.textTheme.bodySmall?.copyWith(
                      fontWeight: FontWeight.w600,
                      color: scheme.onSurfaceVariant)),
            ),
            Expanded(
              child: Text(
                (value != null && value.isNotEmpty) ? value : '\u2014',
                style: theme.textTheme.bodyMedium?.copyWith(
                  color: (value != null && value.isNotEmpty)
                      ? scheme.onSurface
                      : scheme.onSurfaceVariant,
                ),
              ),
            ),
          ],
        ),
      ));
    }

    addRow('Nombre', detail.holderName);
    addRow('Email', detail.holderEmail);
    addRow('Telefono', detail.holderPhone);
    addRow('Codigo reserva', detail.code);
    addRow('Valor cotizado', detail.quotedTotalAmount != null
        ? '\$${detail.quotedTotalAmount!}'
        : null);
    addRow('Fecha solicitada', detail.requestedDate);
    addRow('Estado de pago', paymentStatusLabel(detail.paymentStatus));
    addRow('Participantes',
        '${detail.participantsCompletedCount} / ${detail.expectedParticipantsCount ?? detail.participantCount}');
    if (detail.participantFormStatus != null) {
      addRow('Estado formulario', formStatusLabel(detail.participantFormStatus!));
    }

    return Scaffold(
      appBar: AppBar(
        title: Text(detail.holderName ?? 'Cliente'),
      ),
      body: RefreshableViewport(
        padding: const EdgeInsets.fromLTRB(16, 8, 16, 32),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            if (_isRefreshing) ...[
              const LinearProgressIndicator(minHeight: 2),
              const SizedBox(height: 8),
            ],
            _sectionHeader(context, 'INFORMACION DEL CLIENTE'),
            ...rows,
          ],
        ),
      ),
    );
  }

  Widget _sectionHeader(BuildContext context, String title) {
    final theme = Theme.of(context);
    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: Text(
        title,
        style: theme.textTheme.labelLarge?.copyWith(
          fontWeight: FontWeight.w800,
          letterSpacing: 0.8,
          color: theme.colorScheme.primary,
        ),
      ),
    );
  }
}
