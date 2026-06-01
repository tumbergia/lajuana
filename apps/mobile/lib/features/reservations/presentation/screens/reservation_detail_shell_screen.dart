import 'dart:typed_data';

import 'package:flutter/material.dart';
import 'package:mobile_core/mobile_core.dart';

import '../../../../app/theme/app_colors.dart';
import '../../../../app/widgets/app_badge.dart';
import '../../../../app/widgets/app_button.dart';
import '../../infrastructure/repositories/fallback_repository.dart';
import '../helpers/reservation_status_labels.dart';
import '../../../../app/widgets/app_centered_loader.dart';
import '../../../../app/widgets/app_confirm_dialog.dart';
import '../../../../app/widgets/app_entity_row_card.dart';
import '../../../../app/widgets/app_scaffold.dart';
import '../../../../app/widgets/app_segmented_filter.dart';
import '../../../../app/widgets/app_status_banner.dart';
import '../../../../app/widgets/app_timeline.dart';
import '../dialogs/reservation_approve_dialog.dart';
import '../dialogs/reservation_reject_dialog.dart';
import '../widgets/reservation_client_detail_view.dart';
import '../widgets/reservation_participant_detail_view.dart';
import '../widgets/reservation_proof_image_viewer.dart';
import '../../../auth/presentation/auth_controller.dart';
import '../../../catalogs/catalogs_module.dart';
import '../../domain/models/reservation_detail.dart';

import '../../domain/models/reservation_status.dart';
import '../../domain/models/reservation_participant_detail.dart';
import '../../domain/models/reservation_payment_proof_detail.dart';
import '../../domain/repositories/reservations_repository.dart';
import '../../infrastructure/mappers/reservation_mapper.dart';
import '../../reservations_module.dart';
import '../widgets/payment_status_card.dart';
import '../controllers/reservation_detail_controller.dart';
import '../controllers/reservation_participants_section_controller.dart';
import '../controllers/reservation_payment_proofs_section_controller.dart';

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
    this.authController,
  });

  final String reservationId;
  final ReservationsModule? reservationsModule;
  final CatalogsModule? catalogsModule;
  final AuthController? authController;

  @override
  State<ReservationDetailShellScreen> createState() =>
      _ReservationDetailShellScreenState();
}

class _ReservationDetailShellScreenState
    extends State<ReservationDetailShellScreen> {
  late final ReservationDetailController _controller;
  late final ReservationParticipantsSectionController
      _participantsSectionController;
  late final ReservationPaymentProofsSectionController
      _paymentProofsSectionController;
  ReservationDetailSubroute _subroute = ReservationDetailSubroute.resumen;
  final Map<String, Uint8List> _proofPreviewCache = {};
  final ScrollController _participantsScrollCtrl = ScrollController();
  String? _highlightedParticipantId;
  final Map<String, GlobalKey> _participantKeys = {};

  bool get _isAdmin =>
      widget.authController?.currentUser?.role == 'admin';

  ReservationsRepository? get _repo => widget.reservationsModule?.repository;

  @override
  void initState() {
    super.initState();
    _controller = widget.reservationsModule?.createDetailController() ??
        ReservationDetailController(
          repository: widget.reservationsModule?.repository ??
              (_throwNoModule()),
        );
    _participantsSectionController = ReservationParticipantsSectionController();
    _paymentProofsSectionController =
        ReservationPaymentProofsSectionController();
    _controller.addListener(_onStateChanged);
    _controller.loadDetail(widget.reservationId);
  }

  ReservationsRepository _throwNoModule() {
    return FallbackRepository();
  }

  @override
  void dispose() {
    _controller.removeListener(_onStateChanged);
    _controller.dispose();
    _participantsSectionController.dispose();
    _paymentProofsSectionController.dispose();
    _proofPreviewCache.clear();
    _participantsScrollCtrl.dispose();
    super.dispose();
  }

  void _onStateChanged() {
    final detail = _controller.detail;
    if (detail != null) {
      _participantsSectionController.updateFromDetail(detail);
      _paymentProofsSectionController.updateFromDetail(detail);
    }
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
          else if (state == ReservationDetailLoadState.error)
            Expanded(
              child: _buildSectionPlaceholder(
                'Sin reserva',
                _controller.errorMessage ?? 'No se pudo cargar el detalle de la reserva.',
                Icons.error_outline_rounded,
                action: AppButton(
                  label: 'Reintentar',
                  onPressed: () => _controller.loadDetail(widget.reservationId),
                ),
              ),
            )
          else if (detail != null) ...[
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
        return _buildParticipantsContent(_participantsSectionController);
      case ReservationDetailSubroute.pagos:
        return _buildPaymentContent(_paymentProofsSectionController);
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
          onTap: () => _showClientDetail(detail),
        ),
        if (detail.holderEmail != null) ...[
          const SizedBox(height: 10),
          AppEntityRowCard(
            title: detail.holderEmail!,
            subtitle: 'Email',
            leading: const Icon(Icons.email_outlined, size: 18),
            onTap: () => _showClientDetail(detail),
          ),
        ],
        if (detail.holderPhone != null) ...[
          const SizedBox(height: 10),
          AppEntityRowCard(
            title: detail.holderPhone!,
            subtitle: 'Telefono',
            leading: const Icon(Icons.phone_outlined, size: 18),
            onTap: () => _showClientDetail(detail),
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
          title: detail.quotedTotalAmount != null
              ? formatColombianPrice(detail.quotedTotalAmount!)
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
                  label: formStatusLabel(detail.participantFormStatus!),
                  tone: formStatusTone(detail.participantFormStatus!),
                  uppercase: false,
                )
              : null,
        ),
        const SizedBox(height: 10),
        PaymentStatusCard(
          label: paymentStatusLabel(detail.paymentStatus),
          backgroundColor: _paymentStatusBgColor(detail.paymentStatus),
          foregroundColor: _paymentStatusFgColor(detail.paymentStatus),
        ),
        const SizedBox(height: 16),

        // Confirm reservation action (admin only)
        if (_isAdmin &&
            detail.status != ReservationStatus.confirmed &&
            detail.status != ReservationStatus.cancelled &&
            detail.status != ReservationStatus.completed &&
            detail.status != ReservationStatus.expired) ...[
          AppButton(
            label: _controller.confirmationState ==
                    ReservationActionState.confirming
                ? 'Confirmando...'
                : 'Confirmar reserva',
            icon: _controller.confirmationState ==
                    ReservationActionState.confirming
                ? null
                : Icons.check_circle_outline_rounded,
            variant: AppButtonVariant.primary,
            expanded: true,
            onPressed: _controller.confirmationState ==
                    ReservationActionState.confirming
                ? null
                : () => _showConfirmConfirmation(),
          ),
          const SizedBox(height: 8),
        ],
        // Cancel reservation (separate microplan — stays disabled)
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

  Widget _buildParticipantsContent(
      ReservationParticipantsSectionController ctrl) {
    final pending = ctrl.totalExpected - ctrl.totalCompleted;

    // Build keys for each participant for scroll targeting.
    _participantKeys.clear();
    for (final p in ctrl.participants) {
      _participantKeys[p.id] = GlobalKey(debugLabel: p.id);
    }

    return SingleChildScrollView(
      controller: _participantsScrollCtrl,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Summary metrics row.
          Row(
            children: [
              Expanded(
                child: _metricSmall(
                  'Registrados',
                  '${ctrl.totalCompleted}',
                  Icons.check_circle_outline,
                ),
              ),
              const SizedBox(width: 8),
              Expanded(
                child: _metricSmall(
                  'Pendientes',
                  '$pending',
                  Icons.pending_outlined,
                ),
              ),
            ],
          ),
          if (ctrl.hasMedicalAlert) ...[
            const SizedBox(height: 8),
            AppStatusBanner(
              title: 'Alerta medica',
              message: 'Toque para localizar al participante.',
              tone: AppStatusBannerTone.danger,
              icon: Icons.medical_services_outlined,
              onTap: () => _highlightAlertParticipant(
                  ctrl.participants.where((p) => p.hasMedicalAlert)),
            ),
          ],
          if (ctrl.hasFoodRestriction) ...[
            const SizedBox(height: 8),
            AppStatusBanner(
              title: 'Restriccion alimentaria',
              message: 'Toque para localizar al participante.',
              tone: AppStatusBannerTone.danger,
              icon: Icons.restaurant_outlined,
              onTap: () => _highlightAlertParticipant(
                  ctrl.participants.where((p) => p.hasFoodRestriction)),
            ),
          ],
          const SizedBox(height: 12),
          if (ctrl.participants.isEmpty)
            _buildSectionPlaceholder(
              'Sin participantes',
              'Aun no hay participantes registrados.',
              Icons.person_outline,
            )
          else
            ...ctrl.participants.map((p) => Padding(
                  key: _participantKeys[p.id],
                  padding: const EdgeInsets.only(bottom: 10),
                  child: _buildParticipantCard(p,
                      hasAlertOverride: _highlightedParticipantId == p.id,
                      selected: _highlightedParticipantId == p.id),
                )),
        ],
      ),
    );
  }

  void _highlightAlertParticipant(Iterable<ReservationParticipantDetail> matching) {
    if (matching.isEmpty) return;
    final target = matching.first;
    setState(() => _highlightedParticipantId = target.id);

    WidgetsBinding.instance.addPostFrameCallback((_) {
      final key = _participantKeys[target.id];
      final ctx = key?.currentContext;
      if (ctx != null) {
        Scrollable.ensureVisible(ctx, alignment: 0.15, duration: const Duration(milliseconds: 400));
      }
    });

    Future.delayed(const Duration(seconds: 2), () {
      if (mounted) setState(() => _highlightedParticipantId = null);
    });
  }

  Widget _buildParticipantCard(ReservationParticipantDetail p,
      {bool hasAlertOverride = false, bool selected = false}) {
    final hasAlert = hasAlertOverride || p.hasMedicalAlert || p.hasFoodRestriction;
    final context = this.context;
    final alertRed = appBadgeToneColors(context, AppBadgeTone.danger).background;

    final info = <String>[];
    if (p.heightCm != null) info.add('Altura: ${p.heightCm} cm');
    if (p.weightKg != null) info.add('Peso: ${p.weightKg} kg');
    if (p.ageYears != null) info.add('Edad: ${p.ageYears} años');
    if (p.experienceLevel != null) {
      info.add(_experienceLevelLabel(p.experienceLevel!));
    }

    return Padding(
      padding: const EdgeInsets.only(bottom: 10),
      child: AppEntityRowCard(
        title: p.fullName,
        subtitle: info.isNotEmpty ? info.join(' · ') : '',
        selected: selected,
        accentColor: hasAlert ? alertRed : null,
        badge: hasAlert
            ? AppBadge(label: 'Alerta', tone: AppBadgeTone.danger, uppercase: false)
            : AppBadge(
                label: p.isCompleted ? 'Completo' : 'Incompleto',
                tone: p.isCompleted ? AppBadgeTone.success : AppBadgeTone.warning,
                uppercase: false,
              ),
        leading: Icon(
          hasAlert ? Icons.warning_amber_rounded : Icons.person_outline,
          size: 18,
          color: hasAlert ? alertRed : null,
        ),
        onTap: () => _previewParticipant(p),
      ),
    );
  }

  Widget _metricSmall(String label, String value, IconData icon) {
    final theme = Theme.of(context);
    final scheme = theme.colorScheme;
    return Container(
      padding: const EdgeInsets.all(24),
      decoration: BoxDecoration(
        color: scheme.surfaceContainerHighest,
        borderRadius: BorderRadius.circular(8),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            label.toUpperCase(),
            style: theme.textTheme.labelLarge?.copyWith(
              color: scheme.onSurfaceVariant,
              fontWeight: FontWeight.w700,
              letterSpacing: 0.8,
            ),
          ),
          const SizedBox(height: 12),
          Row(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              Expanded(
                child: Text(
                  value,
                  style: theme.textTheme.displayLarge?.copyWith(
                    color: scheme.onSurface,
                    fontWeight: FontWeight.w800,
                    fontSize: 64,
                    height: 0.95,
                  ),
                ),
              ),
              const SizedBox(width: 8),
              Icon(icon, color: scheme.onSurfaceVariant, size: 28),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildPaymentContent(
      ReservationPaymentProofsSectionController ctrl) {
    final actionState = _controller.paymentProofActionState;

    return RefreshIndicator(
      onRefresh: () => _controller.loadDetail(widget.reservationId),
      child: ListView(
        physics: const AlwaysScrollableScrollPhysics(),
        children: [
            PaymentStatusCard(
              label: paymentStatusLabel(ctrl.paymentStatus),
              backgroundColor:
                  _paymentStatusBgColor(ctrl.paymentStatus),
              foregroundColor:
                  _paymentStatusFgColor(ctrl.paymentStatus),
            ),
          const SizedBox(height: 16),

          // Action feedback (error / success)
          if (_controller.actionErrorCode != null) ...[
            AppStatusBanner(
              title: _actionErrorTitle(_controller.actionErrorCode!),
              message: _controller.actionErrorMessage ?? '',
              tone: AppStatusBannerTone.danger,
              icon: Icons.error_outline_rounded,
            ),
            const SizedBox(height: 12),
          ],

          // Non-admin: hide proofs and actions
          if (!_isAdmin)
            _buildSectionPlaceholder(
              'Comprobantes no disponibles',
              'Seccion no disponible para tu rol.',
              Icons.lock_outline_rounded,
            )
          else if (ctrl.paymentProofs.isEmpty)
            _buildSectionPlaceholder(
              'Sin comprobantes',
              ctrl.paymentStatus != null
                  ? 'Estado: ${paymentStatusLabel(ctrl.paymentStatus)}'
                  : 'No se han cargado comprobantes.',
              Icons.receipt_long_rounded,
            )
          else
            ...ctrl.paymentProofs.map((proof) {
              final statusLabel = paymentProofStatusLabel(proof.status);
              final tone = paymentProofStatusTone(proof.status);
              final proofIsActing =
                  _controller.actingPaymentProofId == proof.id;
              final isApproving = proofIsActing &&
                  actionState == PaymentProofActionState.approving;
              final isRejecting = proofIsActing &&
                  actionState == PaymentProofActionState.rejecting;
              final isUnverifying = proofIsActing &&
                  actionState == PaymentProofActionState.unverifying;
              final isUnrejecting = proofIsActing &&
                  actionState == PaymentProofActionState.unrejecting;
              return Padding(
                padding: const EdgeInsets.only(bottom: 10),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    AppEntityRowCard(
                      title: proof.filename ?? 'Comprobante',
                      subtitle: _buildProofSubtitle(proof),
                      badge: AppBadge(
                        label: statusLabel,
                        tone: tone,
                        uppercase: false,
                      ),
                      leading: const Icon(Icons.receipt_long_rounded, size: 18),
                      onTap: () => _previewProof(proof),
                    ),
                    const SizedBox(height: 8),
                    if (proof.status == 'received')
                      Row(
                        children: [
                          Expanded(
                            child: AppButton(
                              label: isApproving
                                  ? 'Aprobando...'
                                  : 'Aprobar',
                              icon: isApproving
                                  ? null
                                  : Icons.check_circle_outline,
                              variant: AppButtonVariant.primary,
                              onPressed: isApproving || isRejecting
              ? null
                  : () => showApproveConfirmationDialog(
                      context, proof, _controller, _isAdmin),
                            ),
                          ),
                          const SizedBox(width: 8),
                          Expanded(
                            child: AppButton(
                              label: isRejecting
                                  ? 'Rechazando...'
                                  : 'Rechazar',
                              icon: isRejecting
                                  ? null
                                  : Icons.cancel_outlined,
                              variant: AppButtonVariant.secondary,
                              onPressed: isApproving || isRejecting
                  ? null
                  : () => showRejectDialog(context, proof, _controller, _isAdmin),
                            ),
                          ),
                        ],
                      ),
                    if (proof.status == 'verified' && _isAdmin)
                      AppButton(
                        label: isUnverifying
                            ? 'Deshaciendo...'
                            : 'Deshacer verificacion',
                        icon: isUnverifying
                            ? null
                            : Icons.undo_rounded,
                        variant: AppButtonVariant.secondary,
                        expanded: true,
                        onPressed: isUnverifying
                            ? null
                            : () => _showUnverifyConfirm(proof),
                      ),
                    if (proof.status == 'rejected' && _isAdmin)
                      AppButton(
                        label: isUnrejecting
                            ? 'Deshaciendo...'
                            : 'Deshacer rechazo',
                        icon: isUnrejecting
                            ? null
                            : Icons.undo_rounded,
                        variant: AppButtonVariant.secondary,
                        expanded: true,
                        onPressed: isUnrejecting
                            ? null
                            : () => _showUnrejectConfirm(proof),
                      ),
                  ],
                ),
              );
            }),
        ],
      ),
    );
  }

  String _actionErrorTitle(String code) {
    if (code.contains('forbidden') || code.contains('permission')) {
      return 'Permiso denegado';
    }
    if (code.contains('invalid_status_transition') || code == 'common.conflict') {
      return 'Conflicto de estado';
    }
    if (code.contains('network') || code.contains('timeout')) {
      return 'Error de conexion';
    }
    return 'Error al procesar comprobante';
  }

  void _showUnverifyConfirm(ReservationPaymentProofDetail proof) {
    AppConfirmDialog.show(
      context: context,
      icon: Icons.undo_rounded,
      title: 'Deshacer verificacion',
      message:
          'El pago volvera a estado "recibido" y la reserva a '
          '"pendiente de pago".',
      confirmLabel: 'Deshacer',
      style: DialogStyle.danger,
      height: 280,
      onConfirm: () {
        _controller.unverifyPaymentProof(
          paymentProofId: proof.id,
          isAdmin: _isAdmin,
        );
      },
    );
  }

  void _showUnrejectConfirm(ReservationPaymentProofDetail proof) {
    AppConfirmDialog.show(
      context: context,
      icon: Icons.undo_rounded,
      title: 'Deshacer rechazo',
      message:
          'El comprobante volvera a estado "recibido". '
          'La reserva mantiene su estado actual.',
      confirmLabel: 'Deshacer',
      style: DialogStyle.danger,
      height: 280,
      onConfirm: () {
        _controller.unrejectPaymentProof(
          paymentProofId: proof.id,
          isAdmin: _isAdmin,
        );
      },
    );
  }

  void _showConfirmConfirmation() {
    final detail = _controller.detail;
    if (detail == null) return;

    final paymentOk = detail.paymentStatus == 'verified';
    final notTerminal = detail.status != ReservationStatus.confirmed &&
        detail.status != ReservationStatus.cancelled &&
        detail.status != ReservationStatus.completed &&
        detail.status != ReservationStatus.expired;
    final canConfirm = paymentOk && notTerminal;

    AppConfirmDialog.show(
      context: context,
      icon: canConfirm
          ? Icons.check_circle_outline_rounded
          : Icons.error_outline_rounded,
      title: canConfirm ? 'Confirmar reserva' : '¡Verifica el pago!',
      message: canConfirm
          ? 'El sistema revalidará disponibilidad y descontará cupos.\n\n'
              'Esta acción requiere conexión.'
          : !paymentOk
              ? 'Antes de confirmar la reserva, tienes que aprobar el comprobante de pago.'
              : 'La reserva ya está en estado terminal.',
      confirmLabel: canConfirm ? 'Confirmar' : 'Cerrar',
      style: canConfirm ? DialogStyle.regular : DialogStyle.warning,
      height: 280,
      onConfirm: canConfirm
          ? () {
              _controller.confirmReservation(isAdmin: _isAdmin).whenComplete(() {
                if (!mounted) return;
                if (_controller.confirmationErrorCode != null) {
                  ScaffoldMessenger.of(context).showSnackBar(
                    SnackBar(
                      content: Text(
                        _controller.confirmationErrorMessage ??
                            'Error al confirmar reserva',
                        style: const TextStyle(color: Colors.white),
                      ),
                      backgroundColor: AppColors.danger,
                    ),
                  );
                } else if (_controller.detail?.status ==
                    ReservationStatus.confirmed) {
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(
                      content: Text(
                        'Reserva confirmada',
                        style: TextStyle(color: Colors.white),
                      ),
                      backgroundColor: Colors.green,
                    ),
                  );
                }
              });
            }
          : () {},
    );
  }

  void _showClientDetail(ReservationDetail detail) {
    Navigator.of(context).push(
      MaterialPageRoute(
        builder: (_) => ClientDetailView(detail: detail),
      ),
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
    IconData icon, {
    Widget? action,
  }) {
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
          if (action != null) ...[
            const SizedBox(height: 16),
            action,
          ],
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

  String _experienceLevelLabel(String level) {
    switch (level.toLowerCase()) {
      case 'basic':
        return 'Basico';
      case 'intermediate':
        return 'Intermedio';
      case 'advanced':
        return 'Avanzado';
      default:
        return level;
    }
  }

  String _buildProofSubtitle(ReservationPaymentProofDetail proof) {
    final parts = <String>[];
    if (proof.contentType != null) parts.add(proof.contentType!);
    if (proof.sizeBytes != null) {
      parts.add('${(proof.sizeBytes! / 1024).toStringAsFixed(0)} KB');
    }
    if (proof.uploadedAt != null) {
      parts.add(formatDate(proof.uploadedAt!.toIso8601String(), fallback: ''));
    }
    return parts.join(' · ');
  }

  void _previewProof(ReservationPaymentProofDetail proof) {
    Navigator.of(context).push(
      MaterialPageRoute(
        builder: (_) => ProofImageViewer(
          proof: proof,
          repository: _repo,
          cache: _proofPreviewCache,
          onBytesCached: (id, bytes) => _proofPreviewCache[id] = bytes,
        ),
      ),
    );
  }

  void _previewParticipant(ReservationParticipantDetail p) {
    Navigator.of(context).push(
      MaterialPageRoute(
        builder: (_) => ParticipantDetailView(participant: p),
      ),
    );
  }
}

typedef ReservationDetailScreen = ReservationDetailShellScreen;