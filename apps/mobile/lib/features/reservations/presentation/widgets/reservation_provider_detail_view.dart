import 'package:flutter/material.dart';

import 'package:mobile_ui/src/widgets/app_badge.dart';
import 'package:mobile_ui/src/widgets/refresh_scope.dart';
import 'package:mobile_domain/src/reservations/reservation_provider_item.dart';

import 'package:mobile/features/reservations/presentation/widgets/provider_contact_actions.dart';

class ReservationProviderDetailView extends StatefulWidget {
  const ReservationProviderDetailView({
    super.key,
    required this.item,
    required this.isAdmin,
    this.onEdit,
    this.onRemove,
  });

  final ReservationProviderItem item;
  final bool isAdmin;
  final VoidCallback? onEdit;
  final VoidCallback? onRemove;

  @override
  State<ReservationProviderDetailView> createState() =>
      _ReservationProviderDetailViewState();
}

class _ReservationProviderDetailViewState
    extends State<ReservationProviderDetailView>
    with RefreshableState {
  @override
  Future<void> onRefresh() async {}

  AppBadgeTone _statusTone(String status) {
    return switch (status) {
      'confirmed' => AppBadgeTone.success,
      'contacted' => AppBadgeTone.primary,
      'cancelled' => AppBadgeTone.danger,
      _ => AppBadgeTone.neutral,
    };
  }

  String _formatDate(DateTime? date) {
    if (date == null) return 'Por definir';
    final local = date.toLocal();
    final day = local.day.toString().padLeft(2, '0');
    final month = local.month.toString().padLeft(2, '0');
    return '$day/$month/${local.year}';
  }

  @override
  Widget build(BuildContext context) {
    final item = widget.item;
    return Scaffold(
      appBar: AppBar(
        title: Text(item.providerName),
        actions: [
          Center(
            child: Padding(
              padding: const EdgeInsets.only(right: 12),
              child: AppBadge(
                label: reservationProviderStatusLabel(item.status),
                tone: _statusTone(item.status),
                uppercase: false,
              ),
            ),
          ),
        ],
      ),
      body: RefreshableViewport(
        padding: const EdgeInsets.fromLTRB(16, 8, 16, 32),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            _sectionHeader(context, 'ASOCIACION A LA RESERVA'),
            _fieldRow(context, 'Reserva', item.reservationCode),
            _fieldRow(context, 'Experiencia', item.experienceName),
            _fieldRow(context, 'Fecha', _formatDate(item.scheduledDate)),
            _fieldRow(context, 'Participantes', '${item.participantsCount}'),
            _fieldRow(context, 'Servicio requerido', item.serviceLabel),
            _fieldRow(
              context,
              'Estado',
              reservationProviderStatusLabel(item.status),
            ),
            _fieldRow(context, 'Notas de coordinacion', item.notes),
            const SizedBox(height: 16),
            _sectionHeader(context, 'PROVEEDOR'),
            _fieldRow(context, 'Tipo', providerTypeLabel(item.providerType)),
            _fieldRow(context, 'Ubicacion', item.locationLabel),
            _fieldRow(context, 'Contacto', item.contactName),
            _fieldRow(context, 'Correo', item.email),
            _fieldRow(context, 'Telefono / WhatsApp', item.whatsappPhone),
            const SizedBox(height: 16),
            _sectionHeader(context, 'NOTAS DEL CATALOGO'),
            _fieldRow(context, 'Tarifa', item.tariffNotes),
            _fieldRow(context, 'Capacidad', item.capacityNotes),
            _fieldRow(context, 'Operativas', item.operationalNotes),
            const SizedBox(height: 24),
            _sectionHeader(context, 'ACCIONES'),
            const SizedBox(height: 8),
            ProviderDetailActionsBar(
              item: item,
              isAdmin: widget.isAdmin,
              onEdit: widget.onEdit,
              onRemove: widget.onRemove,
            ),
          ],
        ),
      ),
    );
  }

  Widget _sectionHeader(BuildContext context, String title) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: Text(
        title,
        style: Theme.of(context).textTheme.labelLarge?.copyWith(
          fontWeight: FontWeight.w800,
          letterSpacing: 0.8,
          color: Theme.of(context).colorScheme.primary,
        ),
      ),
    );
  }

  Widget _fieldRow(BuildContext context, String label, String? value) {
    final theme = Theme.of(context);
    final scheme = theme.colorScheme;
    final display = (value != null && value.trim().isNotEmpty) ? value : '—';

    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 6),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 132,
            child: Text(
              label,
              style: theme.textTheme.bodySmall?.copyWith(
                fontWeight: FontWeight.w600,
                color: scheme.onSurfaceVariant,
              ),
            ),
          ),
          Expanded(
            child: Text(
              display,
              style: theme.textTheme.bodyMedium?.copyWith(
                color: display == '—'
                    ? scheme.onSurfaceVariant
                    : scheme.onSurface,
              ),
            ),
          ),
        ],
      ),
    );
  }
}
