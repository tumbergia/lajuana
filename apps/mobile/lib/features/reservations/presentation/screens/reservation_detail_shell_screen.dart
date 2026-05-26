import 'package:flutter/material.dart';
import 'package:mobile_core/mobile_core.dart';

import '../../../../app/widgets/app_badge.dart';
import '../../../../app/widgets/app_button.dart';
import '../../../../app/widgets/app_centered_loader.dart';
import '../../../../app/widgets/app_entity_row_card.dart';
import '../../../../app/widgets/app_scaffold.dart';
import '../../../../app/widgets/app_segmented_filter.dart';
import '../../../../app/widgets/app_status_banner.dart';
import '../../../../app/widgets/app_timeline.dart';
import '../../../catalogs/catalogs_module.dart';
import '../../domain/models/reservation_detail.dart';
import '../../domain/models/reservation_list_item.dart';
import '../../domain/models/reservation_status.dart';
import '../../domain/repositories/reservations_repository.dart';
import '../../infrastructure/mappers/reservation_mapper.dart';
import '../../reservations_module.dart';
import '../widgets/payment_status_card.dart';
import '../controllers/reservation_detail_controller.dart';

enum ReservationDetailSubroute {
  resumen,
  participantes,
  pagos,
  asignaciones,
  bitacora,
}

/// Detalle de reserva: carga por [reservationId] y renderiza datos reales.
class ReservationDetailShellScreen extends StatefulWidget {
  const ReservationDetailShellScreen({
    super.key,
    required this.reservationId,
    this.reservationsModule,
    this.catalogsModule,
  });

  final String reservationId;
  final ReservationsModule? reservationsModule;
  final CatalogsModule? catalogsModule;

  @override
  State<ReservationDetailShellScreen> createState() =>
      _ReservationDetailShellScreenState();
}

class _ReservationDetailShellScreenState
    extends State<ReservationDetailShellScreen> {
  late final ReservationDetailController _controller;
  ReservationDetailSubroute _subroute = ReservationDetailSubroute.resumen;

  @override
  void initState() {
    super.initState();
    _controller = widget.reservationsModule?.createDetailController() ??
        ReservationDetailController(
          repository: widget.reservationsModule?.repository ??
              (_throwNoModule()),
        );
    _controller.addListener(_onStateChanged);
    _controller.loadDetail(widget.reservationId);
  }

  ReservationsRepository _throwNoModule() {
    return _FallbackRepository();
  }

  @override
  void dispose() {
    _controller.removeListener(_onStateChanged);
    _controller.dispose();
    super.dispose();
  }

  void _onStateChanged() {
    if (mounted) setState(() {});
  }

  @override
  Widget build(BuildContext context) {
    final state = _controller.state;
    final detail = _controller.detail;

    return AppScaffold(
      scrollable: false,
      padding: const EdgeInsets.fromLTRB(24, 24, 24, 24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          AppButton(
            label: 'Volver',
            icon: Icons.arrow_back_rounded,
            variant: AppButtonVariant.ghost,
            onPressed: () => Navigator.of(context).maybePop(),
          ),
          const SizedBox(height: 16),

          if (state == ReservationDetailLoadState.loading)
            const Expanded(
              child: AppCenteredLoader(),
            )
          else if (state == ReservationDetailLoadState.error) ...[
            AppStatusBanner(
              title: 'Error',
              message: _controller.errorMessage ?? 'No se pudo cargar.',
              tone: AppStatusBannerTone.danger,
              icon: Icons.error_outline_rounded,
            ),
            const SizedBox(height: 12),
            AppButton(
              label: 'Reintentar',
              onPressed: () => _controller.loadDetail(widget.reservationId),
            ),
            const Spacer(),
          ] else if (detail != null) ...[
            if (state == ReservationDetailLoadState.offlineFromCache)
              Padding(
                padding: const EdgeInsets.only(bottom: 12),
                child: AppStatusBanner(
                  title: 'Sin conexion',
                  message: 'Mostrando datos almacenados.',
                  tone: AppStatusBannerTone.warning,
                  icon: Icons.wifi_off_rounded,
                  badgeLabel: 'Offline',
                ),
              ),
            AppSegmentedFilter<int>(
              value: _subroute.index,
              onChanged: (index) {
                setState(() {
                  _subroute = ReservationDetailSubroute.values[index];
                });
              },
              items: const [
                AppSegmentedFilterItem(label: 'Resumen', value: 0),
                AppSegmentedFilterItem(label: 'Partic.', value: 1),
                AppSegmentedFilterItem(label: 'Pagos', value: 2),
                AppSegmentedFilterItem(label: 'Asignac.', value: 3),
                AppSegmentedFilterItem(label: 'Bitacora', value: 4),
              ],
            ),
            const SizedBox(height: 12),
            Expanded(
              child: _buildSubrouteContent(detail),
            ),
          ],
        ],
      ),
    );
  }

  Widget _buildSubrouteContent(ReservationDetail detail) {
    switch (_subroute) {
      case ReservationDetailSubroute.resumen:
        return _buildSummary(detail);
      case ReservationDetailSubroute.participantes:
        return _buildSectionPlaceholder(
          'Participantes',
          '${detail.participantsCompletedCount} de ${detail.expectedParticipantsCount ?? detail.participantCount} han llenado el formulario.',
          Icons.group_outlined,
        );
      case ReservationDetailSubroute.pagos:
        return _buildPaymentSection(detail);
      case ReservationDetailSubroute.asignaciones:
        return _buildSectionPlaceholder(
          'Asignaciones',
          'Proximamente',
          Icons.shield_moon_outlined,
        );
      case ReservationDetailSubroute.bitacora:
        return _buildTimelineSection(detail);
    }
  }

  Widget _buildSummary(ReservationDetail detail) {
    final statusLabel = reservationStatusLabel(detail.status);
    final statusTone = reservationStatusToBadgeTone(detail.status);

    return SingleChildScrollView(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          AppEntityRowCard(
            title: detail.holderName ?? detail.holderEmail ?? 'Sin titular',
          subtitle: 'Cliente principal',
          badge: AppBadge(
            label: statusLabel,
            tone: statusTone,
            uppercase: false,
          ),
          selected: true,
        ),
        if (detail.holderEmail != null && detail.holderName != null) ...[
          const SizedBox(height: 10),
          AppEntityRowCard(
            title: detail.holderEmail!,
            subtitle: 'Email',
            leading: const Icon(Icons.email_outlined, size: 18),
          ),
        ],
        const SizedBox(height: 10),
        AppEntityRowCard(
          title: detail.code,
          subtitle: 'Codigo de reserva',
          leading: const Icon(Icons.tag_rounded, size: 18),
        ),
        const SizedBox(height: 10),
        AppEntityRowCard(
          title: detail.currency != null && detail.quotedTotalAmount != null
              ? '${detail.quotedTotalAmount} ${detail.currency}'
              : 'Sin cotizacion',
          subtitle: 'Valor cotizado',
          leading: const Icon(Icons.attach_money_rounded, size: 18),
        ),
        const SizedBox(height: 10),
        AppEntityRowCard(
          title: formatDate(detail.requestedDate),
          subtitle: 'Fecha solicitada',
          leading: const Icon(Icons.calendar_today_rounded, size: 18),
        ),
        const SizedBox(height: 10),
        AppEntityRowCard(
          title: '${detail.participantsCompletedCount} / ${detail.expectedParticipantsCount ?? detail.participantCount}',
          subtitle: 'Participantes completados',
          leading: const Icon(Icons.group_outlined, size: 18),
          badge: detail.participantFormStatus != null
              ? AppBadge(
                  label: _formStatusLabel(detail.participantFormStatus!),
                  tone: _formStatusTone(detail.participantFormStatus!),
                  uppercase: false,
                )
              : null,
        ),
        const SizedBox(height: 10),
        PaymentStatusCard(
          label: _paymentStatusLabel(detail.paymentStatus),
          backgroundColor: _paymentStatusBgColor(detail.paymentStatus),
          foregroundColor: _paymentStatusFgColor(detail.paymentStatus),
        ),
        const SizedBox(height: 16),

        // Blocked action buttons
        AppButton(
          label: 'Confirmar reserva — Proximamente',
          icon: Icons.lock_outline_rounded,
          variant: AppButtonVariant.secondary,
          expanded: true,
          onPressed: null,
        ),
        const SizedBox(height: 8),
        AppButton(
          label: 'Cancelar reserva — Proximamente',
          icon: Icons.lock_outline_rounded,
          variant: AppButtonVariant.secondary,
          expanded: true,
          onPressed: null,
        ),
          ],
        ),
    );
  }

  Widget _buildPaymentSection(ReservationDetail detail) {
    return _buildSectionPlaceholder(
      'Comprobantes de pago',
      detail.paymentStatus != null
          ? 'Estado: ${_paymentStatusLabel(detail.paymentStatus)}'
          : 'Sin informacion de pago.',
      Icons.receipt_long_rounded,
    );
  }

  Widget _buildTimelineSection(ReservationDetail detail) {
    if (detail.timeline.isEmpty) {
      return _buildSectionPlaceholder(
        'Historial',
        'No hay eventos registrados para esta reserva.',
        Icons.history_rounded,
      );
    }

    return SingleChildScrollView(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          AppTimeline(
            children: detail.timeline.map((event) {
              return AppTimelineItem(
                state: _timelineNodeState(event.type),
                child: AppTimelineEntryCard(
                  date: formatDate(event.date, fallback: ''),
                  title: event.title ?? '',
                  description: event.description,
                ),
              );
            }).toList(),
          ),
          const SizedBox(height: 16),
          AppButton(
            label: 'Registrar bitacora — Proximamente',
            icon: Icons.lock_outline_rounded,
            variant: AppButtonVariant.secondary,
            expanded: true,
            onPressed: null,
          ),
        ],
      ),
    );
  }

  Widget _buildSectionPlaceholder(
    String title,
    String message,
    IconData icon,
  ) {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(icon, size: 48,
              color: Theme.of(context).colorScheme.onSurfaceVariant),
          const SizedBox(height: 16),
          Text(
            title,
            style: Theme.of(context).textTheme.titleMedium,
          ),
          const SizedBox(height: 8),
          Text(
            message,
            textAlign: TextAlign.center,
            style: Theme.of(context).textTheme.bodySmall?.copyWith(
              color: Theme.of(context).colorScheme.onSurfaceVariant,
            ),
          ),
        ],
      ),
    );
  }

  AppTimelineNodeState _timelineNodeState(String? type) {
    switch (type) {
      case 'active':
        return AppTimelineNodeState.active;
      case 'completed':
        return AppTimelineNodeState.completed;
      case 'error':
        return AppTimelineNodeState.error;
      default:
        return AppTimelineNodeState.neutral;
    }
  }

  String _formStatusLabel(String status) {
    switch (status.toLowerCase()) {
      case 'not_sent':
        return 'No enviado';
      case 'sent':
        return 'Enviado';
      case 'partial':
        return 'Parcial';
      case 'complete':
        return 'Completo';
      case 'revoked':
        return 'Revocado';
      default:
        return status;
    }
  }

  AppBadgeTone _formStatusTone(String status) {
    switch (status.toLowerCase()) {
      case 'complete':
        return AppBadgeTone.success;
      case 'partial':
        return AppBadgeTone.warning;
      case 'revoked':
        return AppBadgeTone.danger;
      default:
        return AppBadgeTone.neutral;
    }
  }

  String _paymentStatusLabel(String? status) {
    switch (status?.toLowerCase()) {
      case 'pending':
        return 'Pendiente';
      case 'received':
        return 'Recibido';
      case 'verified':
        return 'Verificado';
      case 'rejected':
        return 'Rechazado';
      default:
        return status ?? 'Sin informacion';
    }
  }

  Color _paymentStatusBgColor(String? status) {
    switch (status?.toLowerCase()) {
      case 'pending':
      case 'received':
        return appBadgeToneColors(context, AppBadgeTone.warning).background;
      case 'verified':
        return appBadgeToneColors(context, AppBadgeTone.success).background;
      case 'rejected':
        return appBadgeToneColors(context, AppBadgeTone.danger).background;
      default:
        return Theme.of(context).colorScheme.surfaceContainerLow;
    }
  }

  Color _paymentStatusFgColor(String? status) {
    switch (status?.toLowerCase()) {
      case 'pending':
      case 'received':
        return appBadgeToneColors(context, AppBadgeTone.warning).foreground;
      case 'verified':
        return appBadgeToneColors(context, AppBadgeTone.success).foreground;
      case 'rejected':
        return appBadgeToneColors(context, AppBadgeTone.danger).foreground;
      default:
        return Theme.of(context).colorScheme.onSurface;
    }
  }
}

/// Fallback repository cuando no se inyecta [ReservationsModule].
class _FallbackRepository implements ReservationsRepository {
  @override
  Future<List<ReservationListItem>> listReservations({
    ReservationStatus? status,
    String? query,
  }) async {
    return const <ReservationListItem>[];
  }

  @override
  Future<ReservationDetail> getReservationById(String reservationId) async {
    throw Exception('ReservationsModule no inyectado');
  }

  @override
  Future<List<ReservationListItem>> getCachedReservations() async {
    return const <ReservationListItem>[];
  }

  @override
  Future<ReservationDetail?> getCachedReservationDetail(
    String reservationId,
  ) async {
    return null;
  }
}

typedef ReservationDetailScreen = ReservationDetailShellScreen;
