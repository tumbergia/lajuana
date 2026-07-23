import 'dart:typed_data';

import 'package:flutter/material.dart';
import 'package:mobile_core/mobile_core.dart';

import 'package:mobile_ui/src/theme/app_colors.dart';
import 'package:mobile_ui/src/theme/theme_extensions.dart';
import 'package:mobile_ui/src/widgets/app_badge.dart';
import 'package:mobile_ui/src/widgets/app_button.dart';
import 'package:mobile_ui/src/widgets/refresh_scope.dart';
import 'package:mobile/features/reservations/infrastructure/repositories/fallback_repository.dart';
import 'package:mobile/features/reservations/presentation/helpers/reservation_status_labels.dart';
import 'package:mobile_ui/src/widgets/app_centered_loader.dart';
import 'package:mobile_ui/src/widgets/app_metric_card.dart';
import 'package:mobile_ui/src/widgets/app_confirm_dialog.dart';
import 'package:mobile_ui/src/widgets/app_entity_row_card.dart';
import 'package:mobile_ui/src/widgets/app_scaffold.dart';
import 'package:mobile_ui/src/widgets/app_segmented_filter.dart';
import 'package:mobile_ui/src/widgets/app_status_banner.dart';
import 'package:mobile_ui/src/widgets/app_switch_row.dart';
import 'package:mobile_ui/src/widgets/app_text_field.dart';
import 'package:mobile_ui/src/widgets/app_toast.dart';
import 'package:mobile_ui/src/widgets/app_timeline.dart';
import 'package:mobile/features/reservations/presentation/dialogs/reservation_approve_dialog.dart';
import 'package:mobile/features/reservations/presentation/dialogs/reservation_reject_dialog.dart';
import 'package:mobile/features/reservations/presentation/widgets/reservation_client_detail_view.dart';
import 'package:mobile/features/reservations/presentation/widgets/reservation_participant_detail_view.dart';
import 'package:mobile/features/reservations/presentation/widgets/reservation_proof_image_viewer.dart';
import 'package:mobile/features/assignments/assignments_module.dart';
import 'package:mobile/features/assignments/presentation/controllers/assignment_board_controller.dart';
import 'package:mobile/features/assignments/presentation/screens/assignment_board_screen.dart';
import 'package:mobile/features/auth/presentation/auth_controller.dart';
import 'package:mobile/features/catalogs/catalogs_module.dart';
import 'package:mobile_domain/src/reservations/reservation_detail.dart';

import 'package:mobile/features/reservations/domain/models/reservation_status.dart';
import 'package:mobile_domain/src/reservations/reservation_participant_detail.dart';
import 'package:mobile_domain/src/reservations/reservation_payment_proof_detail.dart';
import 'package:mobile_domain/src/reservations/reservation_timeline_entry.dart';
import 'package:mobile_domain/src/reservations/reservation_timeline_photo.dart';
import 'package:mobile_domain/src/reservations/reservations_repository.dart';
import 'package:mobile/features/reservations/infrastructure/mappers/reservation_mapper.dart';
import 'package:mobile/features/reservations/presentation/widgets/reservation_log_note_sheet.dart';
import 'package:mobile/features/reservations/presentation/widgets/reservation_log_photo_preview_row.dart';
import 'package:mobile/features/reservations/presentation/widgets/reservation_log_photo_viewer.dart';
import 'package:mobile/features/reservations/reservations_module.dart';
import 'package:mobile/features/reservations/presentation/widgets/payment_status_card.dart';
import 'package:mobile/features/reservations/presentation/controllers/reservation_detail_controller.dart';
import 'package:mobile/features/reservations/presentation/controllers/reservation_participants_section_controller.dart';
import 'package:mobile/features/reservations/presentation/controllers/reservation_logs_section_controller.dart';
import 'package:mobile/features/reservations/presentation/controllers/reservation_providers_section_controller.dart';
import 'package:mobile/features/reservations/presentation/controllers/reservation_payment_proofs_section_controller.dart';
import 'package:mobile/features/reservations/presentation/widgets/reservation_providers_tab.dart';

enum ReservationDetailSubroute {
  resumen,
  participantes,
  pagos,
  asignaciones,
  bitacora,
  proveedores,
}

/// Detalle de reserva: carga por [reservationId] y renderiza datos reales.
class ReservationDetailShellScreen extends StatefulWidget {
  const ReservationDetailShellScreen({
    super.key,
    required this.reservationId,
    this.reservationsModule,
    this.catalogsModule,
    this.authController,
    this.assignmentsModule,
    this.initialSubroute,
  });

  final String reservationId;
  final ReservationsModule? reservationsModule;
  final CatalogsModule? catalogsModule;
  final AuthController? authController;
  final AssignmentsModule? assignmentsModule;
  final ReservationDetailSubroute? initialSubroute;

  @override
  State<ReservationDetailShellScreen> createState() =>
      _ReservationDetailShellScreenState();
}

class _ReservationDetailShellScreenState
    extends State<ReservationDetailShellScreen>
    with RefreshableState {
  late final ReservationDetailController _controller;
  late final ReservationParticipantsSectionController
  _participantsSectionController;
  late final ReservationPaymentProofsSectionController
  _paymentProofsSectionController;
  late final ReservationLogsSectionController _logsSectionController;
  late final ReservationProvidersSectionController _providersSectionController;
  AssignmentBoardController? _assignmentBoardController;
  ReservationDetailSubroute _subroute = ReservationDetailSubroute.resumen;
  final Map<String, Uint8List> _proofPreviewCache = {};
  final Map<String, Uint8List> _logPhotoCache = {};
  final ScrollController _participantsScrollCtrl = ScrollController();
  String? _highlightedParticipantId;
  final Map<String, GlobalKey> _participantKeys = {};

  bool get _isAdmin => widget.authController?.currentUser?.role == 'admin';

  ReservationsRepository? get _repo => widget.reservationsModule?.repository;

  @override
  Future<void> onRefresh() async {
    if (!mounted) return;
    switch (_subroute) {
      case ReservationDetailSubroute.bitacora:
        await _logsSectionController.load(widget.reservationId);
      case ReservationDetailSubroute.proveedores:
        await _providersSectionController.load(widget.reservationId);
      case ReservationDetailSubroute.asignaciones:
        if (widget.assignmentsModule?.repository != null) {
          _assignmentBoardController ??= _createAssignmentBoardController();
          await _assignmentBoardController!.refresh();
        } else {
          await _controller.loadDetail(widget.reservationId);
        }
      case ReservationDetailSubroute.resumen:
      case ReservationDetailSubroute.participantes:
      case ReservationDetailSubroute.pagos:
        await _controller.loadDetail(widget.reservationId);
    }
  }

  AssignmentBoardController _createAssignmentBoardController() {
    final repo = widget.assignmentsModule!.repository;
    return AssignmentBoardController(
      repository: repo,
      isAdmin: _isAdmin,
      networkStatus: widget.authController?.networkStatus,
      outbox: widget.assignmentsModule?.outbox,
    );
  }

  @override
  void initState() {
    super.initState();
    final initial = widget.initialSubroute ?? ReservationDetailSubroute.resumen;
    _subroute = (!_isAdmin && initial == ReservationDetailSubroute.pagos)
        ? ReservationDetailSubroute.resumen
        : initial;
    _controller =
        widget.reservationsModule?.createDetailController() ??
        ReservationDetailController(
          repository:
              widget.reservationsModule?.repository ?? (_throwNoModule()),
        );
    _participantsSectionController = ReservationParticipantsSectionController();
    _paymentProofsSectionController =
        ReservationPaymentProofsSectionController();
    _logsSectionController = ReservationLogsSectionController(
      repository: widget.reservationsModule?.repository ?? (_throwNoModule()),
    );
    _logsSectionController.addListener(_onLogsStateChanged);
    _providersSectionController = ReservationProvidersSectionController(
      repository: widget.reservationsModule?.repository ?? (_throwNoModule()),
    );
    _providersSectionController.addListener(_onProvidersStateChanged);
    _controller.addListener(_onStateChanged);
    _controller.loadDetail(widget.reservationId);
    if (_subroute == ReservationDetailSubroute.asignaciones &&
        widget.assignmentsModule?.repository != null) {
      WidgetsBinding.instance.addPostFrameCallback((_) {
        if (!mounted) return;
        _assignmentBoardController ??= _createAssignmentBoardController();
        if (_assignmentBoardController!.state == BoardLoadState.initial) {
          _assignmentBoardController!.load(reservationId: widget.reservationId);
        }
      });
    }
  }

  ReservationsRepository _throwNoModule() {
    return FallbackRepository();
  }

  @override
  void dispose() {
    super.dispose();
    _controller.removeListener(_onStateChanged);
    _controller.dispose();
    _participantsSectionController.dispose();
    _paymentProofsSectionController.dispose();
    _logsSectionController.removeListener(_onLogsStateChanged);
    _logsSectionController.dispose();
    _providersSectionController.removeListener(_onProvidersStateChanged);
    _providersSectionController.dispose();
    _assignmentBoardController?.dispose();
    _proofPreviewCache.clear();
    _logPhotoCache.clear();
    _participantsScrollCtrl.dispose();
  }

  void _onStateChanged() {
    final detail = _controller.detail;
    if (detail != null) {
      _participantsSectionController.updateFromDetail(detail);
      _paymentProofsSectionController.updateFromDetail(detail);
    }
    if (mounted) setState(() {});
  }

  void _onLogsStateChanged() {
    if (mounted) setState(() {});
  }

  void _onProvidersStateChanged() {
    if (mounted) setState(() {});
  }

  void _onSubrouteChanged(int index) {
    setState(() {
      _subroute = ReservationDetailSubroute.values[index];
    });
    if (_subroute == ReservationDetailSubroute.bitacora &&
        _logsSectionController.state == ReservationLogsLoadState.initial) {
      _logsSectionController.load(widget.reservationId);
    }
    if (_subroute == ReservationDetailSubroute.proveedores &&
        _providersSectionController.state ==
            ReservationProvidersLoadState.initial) {
      _providersSectionController.load(widget.reservationId);
    }
    if (_subroute == ReservationDetailSubroute.asignaciones &&
        widget.assignmentsModule?.repository != null) {
      _assignmentBoardController ??= _createAssignmentBoardController();
      if (_assignmentBoardController!.state == BoardLoadState.initial) {
        _assignmentBoardController!.load(reservationId: widget.reservationId);
      }
    }
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
              child: RefreshableViewport(child: AppCenteredLoader()),
            )
          else if (state == ReservationDetailLoadState.error)
            Expanded(
              child: RefreshableViewport(
                child: _buildSectionPlaceholder(
                  'Sin reserva',
                  _controller.errorMessage ??
                      'No se pudo cargar el detalle de la reserva.',
                  Icons.error_outline_rounded,
                  action: AppButton(
                    label: 'Reintentar',
                    onPressed: () =>
                        _controller.loadDetail(widget.reservationId),
                  ),
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
              allowDeselect: false,
              onChanged: (index) {
                if (index != null) _onSubrouteChanged(index);
              },
              items: [
                const AppSegmentedFilterItem(label: 'Resumen', value: 0),
                const AppSegmentedFilterItem(label: 'Participantes', value: 1),
                if (_isAdmin)
                  const AppSegmentedFilterItem(label: 'Pagos', value: 2),
                const AppSegmentedFilterItem(label: 'Asignaciones', value: 3),
                const AppSegmentedFilterItem(label: 'Bitacora', value: 4),
                const AppSegmentedFilterItem(label: 'Proveedores', value: 5),
              ],
            ),
            const SizedBox(height: 12),
            Expanded(child: _buildSubrouteContent(detail)),
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
        return _buildAssignmentContent();
      case ReservationDetailSubroute.bitacora:
        return _buildTimelineSection();
      case ReservationDetailSubroute.proveedores:
        return ReservationProvidersTab(
          controller: _providersSectionController,
          isAdmin: _isAdmin,
          emptyState: _buildSectionPlaceholder(
            'Sin proveedores',
            'No hay proveedores asociados a esta reserva.',
            Icons.handshake_outlined,
          ),
        );
    }
  }

  Widget _buildSummary(ReservationDetail detail) {
    final statusLabel = reservationStatusLabel(detail.status);
    final statusTone = reservationStatusToBadgeTone(detail.status);

    return SingleChildScrollView(
      physics: const AlwaysScrollableScrollPhysics(),
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
            title:
                '${detail.participantsCompletedCount} / ${detail.expectedParticipantsCount ?? detail.participantCount}',
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
          if (_isAdmin) ...[
            const SizedBox(height: 16),
            AppSwitchRow(
              title: 'Asistente de IA',
              subtitle: detail.assistantDisabled
                  ? 'Desactivado para esta reserva'
                  : 'Activo para esta reserva',
              value: !detail.assistantDisabled,
              onChanged: _controller.assistantToggleState.isLoading
                  ? null
                  : (enabled) async {
                      await _controller.setAssistantDisabled(
                        disabled: !enabled,
                        isAdmin: true,
                      );
                      if (!mounted) return;
                      if (_controller.assistantToggleState.isError) {
                        showAppToast(
                          context,
                          message:
                              _controller.assistantToggleState.errorMessage ??
                              'No se pudo actualizar el asistente.',
                        );
                      } else {
                        showAppToast(
                          context,
                          message: enabled
                              ? 'Asistente activado para esta reserva.'
                              : 'Asistente desactivado para esta reserva.',
                        );
                      }
                    },
            ),
          ],
          const SizedBox(height: 16),

          // Confirm reservation action (admin only)
          if (_isAdmin &&
              detail.status != ReservationStatus.confirmed &&
              detail.status != ReservationStatus.cancelled &&
              detail.status != ReservationStatus.completed &&
              detail.status != ReservationStatus.expired) ...[
            AppButton(
              label: _controller.confirmationState.isLoading
                  ? 'Confirmando...'
                  : 'Confirmar reserva',
              icon: _controller.confirmationState.isLoading
                  ? null
                  : Icons.check_circle_outline_rounded,
              variant: AppButtonVariant.primary,
              expanded: true,
              onPressed: _controller.confirmationState.isLoading
                  ? null
                  : () => _showConfirmConfirmation(),
            ),
            const SizedBox(height: 8),
          ],
          // Cancel reservation action (admin only)
          if (_isAdmin &&
              detail.status != ReservationStatus.cancelled &&
              detail.status != ReservationStatus.completed &&
              detail.status != ReservationStatus.expired) ...[
            AppButton(
              label: _controller.cancellationState.isLoading
                  ? 'Cancelando...'
                  : 'Cancelar reserva',
              icon: _controller.cancellationState.isLoading
                  ? null
                  : Icons.cancel_outlined,
              variant: AppButtonVariant.danger,
              expanded: true,
              onPressed: _controller.cancellationState.isLoading
                  ? null
                  : () => _showCancelConfirmation(),
            ),
            const SizedBox(height: 8),
          ],
          // Delete reservation action (admin only)
          if (_isAdmin) ...[
            if (detail.deletedAt != null) ...[
              AppButton(
                label: _controller.deleteState.isLoading
                    ? 'Restaurando...'
                    : 'Restaurar reserva',
                icon: Icons.restore_from_trash_rounded,
                variant: AppButtonVariant.secondary,
                expanded: true,
                onPressed: _controller.deleteState.isLoading
                    ? null
                    : () => _showRestoreConfirmation(),
              ),
            ] else ...[
              AppButton(
                label: _controller.deleteState.isLoading
                    ? 'Eliminando...'
                    : 'Eliminar reserva',
                icon: Icons.delete_outline_rounded,
                variant: AppButtonVariant.danger,
                expanded: true,
                onPressed: _controller.deleteState.isLoading
                    ? null
                    : () => _showDeleteConfirmation(),
              ),
            ],
          ],
        ],
      ),
    );
  }

  Widget _buildParticipantsContent(
    ReservationParticipantsSectionController ctrl,
  ) {
    if (ctrl.participants.isEmpty) {
      return RefreshableViewport(
        controller: _participantsScrollCtrl,
        child: _buildSectionPlaceholder(
          'Sin participantes',
          'Aun no hay participantes registrados.',
          Icons.person_outline,
        ),
      );
    }

    final pending = ctrl.totalExpected - ctrl.totalCompleted;

    // Build keys for each participant for scroll targeting.
    _participantKeys.clear();
    for (final p in ctrl.participants) {
      _participantKeys[p.id] = GlobalKey(debugLabel: p.id);
    }

    return SingleChildScrollView(
      controller: _participantsScrollCtrl,
      physics: const AlwaysScrollableScrollPhysics(),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _buildParticipantsMetrics(ctrl.totalCompleted, pending),
          if (ctrl.hasMedicalAlert) ...[
            const SizedBox(height: 8),
            AppStatusBanner(
              title: 'Alerta medica',
              message: 'Toque para localizar al participante.',
              tone: AppStatusBannerTone.danger,
              icon: Icons.medical_services_outlined,
              onTap: () => _highlightAlertParticipant(
                ctrl.participants.where((p) => p.hasMedicalAlert),
              ),
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
                ctrl.participants.where((p) => p.hasFoodRestriction),
              ),
            ),
          ],
          const SizedBox(height: 12),
          ...ctrl.participants.map(
            (p) => Padding(
              key: _participantKeys[p.id],
              padding: const EdgeInsets.only(bottom: 10),
              child: _buildParticipantCard(
                p,
                hasAlertOverride: _highlightedParticipantId == p.id,
                selected: _highlightedParticipantId == p.id,
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildParticipantsMetrics(int totalCompleted, int pending) {
    final registered = AppMetricCard(
      title: 'Registrados',
      value: '$totalCompleted',
      icon: Icons.check_circle_outline,
    );
    final pendingCard = AppMetricCard(
      title: 'Pendientes',
      value: '$pending',
      icon: Icons.pending_outlined,
    );

    // Evita LayoutBuilder dentro del scroll (altura no acotada).
    final contentWidth = MediaQuery.sizeOf(context).width - 48;
    final narrow = contentWidth < 400;
    if (narrow) {
      return Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [registered, const SizedBox(height: 8), pendingCard],
      );
    }
    return Row(
      children: [
        Expanded(child: registered),
        const SizedBox(width: 8),
        Expanded(child: pendingCard),
      ],
    );
  }

  void _highlightAlertParticipant(
    Iterable<ReservationParticipantDetail> matching,
  ) {
    if (matching.isEmpty) return;
    final target = matching.first;
    setState(() => _highlightedParticipantId = target.id);

    WidgetsBinding.instance.addPostFrameCallback((_) {
      final key = _participantKeys[target.id];
      final ctx = key?.currentContext;
      if (ctx != null) {
        Scrollable.ensureVisible(
          ctx,
          alignment: 0.15,
          duration: const Duration(milliseconds: 400),
        );
      }
    });

    Future.delayed(const Duration(seconds: 2), () {
      if (mounted) setState(() => _highlightedParticipantId = null);
    });
  }

  Widget _buildParticipantCard(
    ReservationParticipantDetail p, {
    bool hasAlertOverride = false,
    bool selected = false,
  }) {
    final hasAlert =
        hasAlertOverride || p.hasMedicalAlert || p.hasFoodRestriction;
    final context = this.context;
    final alertRed = appBadgeToneColors(
      context,
      AppBadgeTone.danger,
    ).background;

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
            ? AppBadge(
                label: 'Alerta',
                tone: AppBadgeTone.danger,
                uppercase: false,
              )
            : AppBadge(
                label: p.isCompleted ? 'Completo' : 'Incompleto',
                tone: p.isCompleted
                    ? AppBadgeTone.success
                    : AppBadgeTone.warning,
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

  Widget _buildPaymentContent(ReservationPaymentProofsSectionController ctrl) {
    final actionState = _controller.paymentProofActionState;

    return ListView(
      physics: const AlwaysScrollableScrollPhysics(),
      children: [
        PaymentStatusCard(
          label: paymentStatusLabel(ctrl.paymentStatus),
          backgroundColor: _paymentStatusBgColor(ctrl.paymentStatus),
          foregroundColor: _paymentStatusFgColor(ctrl.paymentStatus),
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
            final proofIsActing = _controller.actingPaymentProofId == proof.id;
            final isApproving =
                proofIsActing && _controller.approveProofState.isLoading;
            final isRejecting =
                proofIsActing && _controller.rejectProofState.isLoading;
            final isUnverifying =
                proofIsActing && _controller.unverifyProofState.isLoading;
            final isUnrejecting =
                proofIsActing && _controller.unrejectProofState.isLoading;
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
                            label: isApproving ? 'Aprobando...' : 'Aprobar',
                            icon: isApproving
                                ? null
                                : Icons.check_circle_outline,
                            variant: AppButtonVariant.primary,
                            onPressed: isApproving || isRejecting
                                ? null
                                : () => showApproveConfirmationDialog(
                                    context,
                                    proof,
                                    _controller,
                                    _isAdmin,
                                  ),
                          ),
                        ),
                        const SizedBox(width: 8),
                        Expanded(
                          child: AppButton(
                            label: isRejecting ? 'Rechazando...' : 'Rechazar',
                            icon: isRejecting ? null : Icons.cancel_outlined,
                            variant: AppButtonVariant.secondary,
                            onPressed: isApproving || isRejecting
                                ? null
                                : () => showRejectDialog(
                                    context,
                                    proof,
                                    _controller,
                                    _isAdmin,
                                  ),
                          ),
                        ),
                      ],
                    ),
                  if (proof.status == 'verified' && _isAdmin)
                    AppButton(
                      label: isUnverifying
                          ? 'Deshaciendo...'
                          : 'Deshacer verificacion',
                      icon: isUnverifying ? null : Icons.undo_rounded,
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
                      icon: isUnrejecting ? null : Icons.undo_rounded,
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
    );
  }

  String _actionErrorTitle(String code) {
    if (code.contains('forbidden') || code.contains('permission')) {
      return 'Permiso denegado';
    }
    if (code.contains('invalid_status_transition') ||
        code == 'common.conflict') {
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
    final notTerminal =
        detail.status != ReservationStatus.confirmed &&
        detail.status != ReservationStatus.cancelled &&
        detail.status != ReservationStatus.completed &&
        detail.status != ReservationStatus.expired;
    final canConfirm = paymentOk && notTerminal;

    if (!canConfirm) {
      AppConfirmDialog.show(
        context: context,
        icon: Icons.error_outline_rounded,
        title: '¡Verifica el pago!',
        message: !paymentOk
            ? 'Antes de confirmar la reserva, tienes que aprobar el comprobante de pago.'
            : 'La reserva ya está en estado terminal.',
        confirmLabel: 'Cerrar',
        style: DialogStyle.warning,
        height: 280,
        onConfirm: () {},
      );
      return;
    }

    final theme = Theme.of(context);
    final tokens = theme.appTokens;
    final scheme = theme.colorScheme;
    TimeOfDay selectedTime = TimeOfDay.now();

    showDialog<void>(
      context: context,
      builder: (ctx) {
        return StatefulBuilder(
          builder: (context, setDialogState) {
            return AlertDialog(
              backgroundColor: scheme.surfaceContainerHigh,
              surfaceTintColor: Colors.transparent,
              shape: RoundedRectangleBorder(borderRadius: tokens.radiusXl),
              insetPadding: const EdgeInsets.symmetric(
                horizontal: 24,
                vertical: 40,
              ),
              contentPadding: EdgeInsets.zero,
              content: Padding(
                padding: EdgeInsets.all(tokens.spaceXl),
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    Icon(
                      Icons.check_circle_outline_rounded,
                      size: 48,
                      color: scheme.primary,
                    ),
                    SizedBox(height: tokens.spaceLg),
                    Text(
                      'Confirmar reserva',
                      textAlign: TextAlign.center,
                      style: theme.textTheme.titleMedium?.copyWith(
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                    SizedBox(height: tokens.spaceSm),
                    Text(
                      'El sistema revalidará disponibilidad y descontará cupos.\n'
                      'Esta acción requiere conexión.',
                      textAlign: TextAlign.center,
                      style: theme.textTheme.bodyMedium?.copyWith(
                        color: scheme.onSurfaceVariant,
                      ),
                    ),
                    SizedBox(height: tokens.spaceLg),
                    Container(
                      decoration: BoxDecoration(
                        color: scheme.surfaceContainerLow,
                        borderRadius: tokens.radiusMd,
                        border: Border.all(color: scheme.outlineVariant),
                      ),
                      padding: const EdgeInsets.symmetric(
                        horizontal: 16,
                        vertical: 4,
                      ),
                      child: InkWell(
                        borderRadius: tokens.radiusMd,
                        onTap: () async {
                          final picked = await showTimePicker(
                            context: context,
                            initialTime: selectedTime,
                            helpText: 'Selecciona la hora de inicio',
                            confirmText: 'Aceptar',
                            cancelText: 'Cancelar',
                            builder: (context, child) {
                              return MediaQuery(
                                data: MediaQuery.of(
                                  context,
                                ).copyWith(alwaysUse24HourFormat: true),
                                child: child!,
                              );
                            },
                          );
                          if (picked != null) {
                            setDialogState(() {
                              selectedTime = picked;
                            });
                          }
                        },
                        child: Padding(
                          padding: const EdgeInsets.symmetric(vertical: 12),
                          child: Row(
                            children: [
                              Icon(
                                Icons.schedule_rounded,
                                size: 20,
                                color: scheme.primary,
                              ),
                              SizedBox(width: tokens.spaceSm),
                              Expanded(
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Text(
                                      'Hora de inicio',
                                      style: theme.textTheme.labelSmall
                                          ?.copyWith(
                                            color: scheme.onSurfaceVariant,
                                          ),
                                    ),
                                    Text(
                                      selectedTime.format(context),
                                      style: theme.textTheme.bodyLarge
                                          ?.copyWith(
                                            fontWeight: FontWeight.w600,
                                          ),
                                    ),
                                  ],
                                ),
                              ),
                              Icon(
                                Icons.edit_calendar_rounded,
                                size: 18,
                                color: scheme.onSurfaceVariant,
                              ),
                            ],
                          ),
                        ),
                      ),
                    ),
                    SizedBox(height: tokens.spaceXl),
                    Row(
                      children: [
                        Expanded(
                          child: AppButton(
                            label: 'Cancelar',
                            variant: AppButtonVariant.secondary,
                            onPressed: () => Navigator.of(ctx).pop(),
                            expanded: true,
                            height: 48,
                          ),
                        ),
                        SizedBox(width: tokens.spaceSm),
                        Expanded(
                          child: AppButton(
                            label: 'Confirmar',
                            variant: AppButtonVariant.primary,
                            onPressed: () {
                              Navigator.of(ctx).pop();
                              final hour = selectedTime.hour.toString().padLeft(
                                2,
                                '0',
                              );
                              final minute = selectedTime.minute
                                  .toString()
                                  .padLeft(2, '0');
                              final startTime = '$hour:$minute';
                              _controller
                                  .confirmReservation(
                                    isAdmin: _isAdmin,
                                    startTime: startTime,
                                  )
                                  .whenComplete(() {
                                    if (!mounted) return;
                                    if (_controller.confirmationErrorCode !=
                                        null) {
                                      showAppToast(
                                        context,
                                        message:
                                            _controller
                                                .confirmationErrorMessage ??
                                            'Error al confirmar reserva',
                                        isError: true,
                                      );
                                    } else if (_controller.detail?.status ==
                                        ReservationStatus.confirmed) {
                                      showAppToast(
                                        context,
                                        message: 'Reserva confirmada',
                                      );
                                    }
                                  });
                            },
                            expanded: true,
                            height: 48,
                          ),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
            );
          },
        );
      },
    );
  }

  void _showCancelConfirmation() {
    final detail = _controller.detail;
    if (detail == null) return;

    final canCancel =
        detail.status != ReservationStatus.cancelled &&
        detail.status != ReservationStatus.completed &&
        detail.status != ReservationStatus.expired;

    AppConfirmDialog.show(
      context: context,
      icon: canCancel ? Icons.cancel_outlined : Icons.error_outline_rounded,
      title: canCancel ? 'Cancelar reserva' : 'No se puede cancelar',
      message: canCancel
          ? 'La reserva será cancelada y el cliente recibirá una notificación por WhatsApp.\n\n'
                'Esta acción requiere conexión.'
          : 'La reserva ya está en estado terminal.',
      confirmLabel: canCancel ? 'Confirmar cancelación' : 'Cerrar',
      cancelLabel: canCancel ? 'Volver' : 'Volver',
      style: canCancel ? DialogStyle.warning : DialogStyle.warning,
      height: 280,
      onConfirm: canCancel
          ? () {
              _controller.cancelReservation(isAdmin: _isAdmin).whenComplete(() {
                if (!mounted) return;
                if (_controller.cancellationErrorCode != null) {
                  showAppToast(
                    context,
                    message:
                        _controller.cancellationErrorMessage ??
                        'Error al cancelar reserva',
                    isError: true,
                  );
                } else if (_controller.detail?.status ==
                    ReservationStatus.cancelled) {
                  showAppToast(context, message: 'Reserva cancelada');
                }
              });
            }
          : () {},
    );
  }

  void _showDeleteConfirmation() {
    final detail = _controller.detail;
    if (detail == null) return;

    AppConfirmDialog.show(
      context: context,
      icon: Icons.delete_outline_rounded,
      title: 'Eliminar reserva',
      message:
          'La reserva "${detail.code}" se ocultará de los listados activos.\n\n'
          'Esta acción es reversible.',
      confirmLabel: 'Eliminar',
      style: DialogStyle.danger,
      height: 280,
      onConfirm: () {
        _controller.deleteReservation(isAdmin: _isAdmin).whenComplete(() {
          if (!mounted) return;
          if (_controller.deleteErrorCode != null) {
            showAppToast(
              context,
              message:
                  _controller.deleteErrorMessage ?? 'Error al eliminar reserva',
              isError: true,
            );
          } else {
            showAppToast(context, message: 'Reserva eliminada');
          }
        });
      },
    );
  }

  void _showRestoreConfirmation() {
    final detail = _controller.detail;
    if (detail == null) return;

    AppConfirmDialog.show(
      context: context,
      icon: Icons.restore_from_trash_rounded,
      title: 'Restaurar reserva',
      message:
          'La reserva "${detail.code}" volverá a aparecer en los listados activos.',
      confirmLabel: 'Restaurar',
      style: DialogStyle.regular,
      height: 240,
      onConfirm: () {
        _controller.restoreReservation(isAdmin: _isAdmin).whenComplete(() {
          if (!mounted) return;
          if (_controller.deleteErrorCode != null) {
            showAppToast(
              context,
              message:
                  _controller.deleteErrorMessage ??
                  'Error al restaurar reserva',
              isError: true,
            );
          } else {
            showAppToast(context, message: 'Reserva restaurada');
          }
        });
      },
    );
  }

  void _showClientDetail(ReservationDetail detail) {
    Navigator.of(context).push(
      MaterialPageRoute(
        builder: (_) => ClientDetailView(
          detail: detail,
          repository: _repo,
          reservationId: widget.reservationId,
        ),
      ),
    );
  }

  Widget _buildAssignmentContent() {
    final repo = widget.assignmentsModule?.repository;
    if (repo == null) {
      return _buildSectionPlaceholder(
        'Asignaciones',
        'Módulo no disponible',
        Icons.shield_moon_outlined,
      );
    }
    _assignmentBoardController ??= _createAssignmentBoardController();
    if (_assignmentBoardController!.state == BoardLoadState.initial) {
      _assignmentBoardController!.load(reservationId: widget.reservationId);
    }
    return AssignmentBoardScreen(
      controller: _assignmentBoardController!,
      reservationId: widget.reservationId,
      isAdmin: _isAdmin,
      isOnline: widget.authController?.networkStatus.hasSomeLink ?? true,
      embedded: true,
      key: ValueKey('assignments_${widget.reservationId}'),
    );
  }

  Widget _buildTimelineSection() {
    final logsState = _logsSectionController.state;
    final entries = _logsSectionController.entries;

    if (logsState == ReservationLogsLoadState.initial ||
        logsState == ReservationLogsLoadState.loading) {
      return const RefreshableViewport(child: AppCenteredLoader());
    }

    if (logsState == ReservationLogsLoadState.error && entries.isEmpty) {
      return RefreshableViewport(
        child: _buildSectionPlaceholder(
          'Bitácora',
          _logsSectionController.errorMessage ??
              'No se pudo cargar la bitácora de esta reserva.',
          Icons.history_rounded,
          action: AppButton(
            label: 'Reintentar',
            onPressed: () => _logsSectionController.load(widget.reservationId),
          ),
        ),
      );
    }

    return SingleChildScrollView(
      physics: const AlwaysScrollableScrollPhysics(),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          AppButton(
            label: 'Agregar nota',
            icon: Icons.add_rounded,
            expanded: true,
            onPressed: logsState == ReservationLogsLoadState.saving
                ? null
                : () => _showNoteSheet(),
          ),
          const SizedBox(height: 16),
          if (entries.isEmpty)
            _buildSectionPlaceholder(
              'Sin eventos',
              'Aún no hay entradas en la bitácora de esta reserva.',
              Icons.history_rounded,
            )
          else
            AppTimeline(
              children: entries.map((entry) {
                final description = _timelineDescription(entry);
                return AppTimelineItem(
                  state: _timelineNodeState(timelineEntryNodeType(entry)),
                  child: AppTimelineEntryCard(
                    date: formatTimelineDate(entry.happenedAt),
                    title: entry.title,
                    description: description,
                    badge: entry.kind == 'note'
                        ? AppBadge(label: 'Manual', tone: AppBadgeTone.primary)
                        : null,
                    highlightedContent: _buildTimelinePhotoPreview(entry),
                    footer: _buildTimelineActions(entry),
                  ),
                );
              }).toList(),
            ),
        ],
      ),
    );
  }

  String? _timelineDescription(ReservationTimelineEntry entry) {
    final parts = <String>[];
    if (entry.description != null && entry.description!.trim().isNotEmpty) {
      parts.add(entry.description!.trim());
    }
    if (entry.actorName != null && entry.actorName!.trim().isNotEmpty) {
      parts.add('Por ${entry.actorName!.trim()}');
    }
    if (parts.isEmpty) return null;
    return parts.join('\n');
  }

  Widget? _buildTimelineActions(ReservationTimelineEntry entry) {
    if (!entry.editable && !entry.deletable) return null;

    final saving =
        _logsSectionController.state == ReservationLogsLoadState.saving;

    return Row(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        if (entry.editable && entry.serviceLogId != null)
          AppButton(
            label: 'Editar',
            icon: Icons.edit_outlined,
            variant: AppButtonVariant.secondary,
            height: 44,
            onPressed: saving
                ? null
                : () => _showNoteSheet(
                    logId: entry.serviceLogId,
                    initialText: entry.description ?? '',
                  ),
          ),
        if (entry.editable && entry.deletable && entry.serviceLogId != null)
          const SizedBox(width: 12),
        if (entry.deletable && entry.serviceLogId != null)
          AppButton(
            label: 'Eliminar',
            icon: Icons.delete_outline_rounded,
            variant: AppButtonVariant.danger,
            height: 44,
            onPressed: saving ? null : () => _confirmDeleteLog(entry),
          ),
      ],
    );
  }

  Widget? _buildTimelinePhotoPreview(ReservationTimelineEntry entry) {
    if (entry.photos.isEmpty || entry.serviceLogId == null) return null;

    return ReservationLogPhotoPreviewRow(
      entry: entry,
      logId: entry.serviceLogId!,
      controller: _logsSectionController,
      cache: _logPhotoCache,
      onPhotoTap: (photo) => _openLogPhoto(entry: entry, photo: photo),
    );
  }

  Future<void> _openLogPhoto({
    required ReservationTimelineEntry entry,
    required ReservationTimelinePhoto photo,
  }) async {
    final repo = _repo;
    final logId = entry.serviceLogId;
    if (repo == null || logId == null) return;

    var photos = entry.photos;
    if (entry.photosTotal > photos.length) {
      final detail = await _logsSectionController.loadNoteForEdit(logId);
      if (detail != null && detail.photos.isNotEmpty) {
        photos = detail.photos;
      }
    }

    if (!mounted || photos.isEmpty) return;

    var initialIndex = photos.indexWhere((item) => item.index == photo.index);
    if (initialIndex < 0) initialIndex = 0;

    Navigator.of(context).push(
      MaterialPageRoute<void>(
        builder: (_) => ReservationLogPhotoViewer(
          logId: logId,
          photos: photos,
          initialIndex: initialIndex,
          repository: repo,
          cache: _logPhotoCache,
          onBytesCached: (key, bytes) => _logPhotoCache[key] = bytes,
        ),
      ),
    );
  }

  Future<void> _showNoteSheet({String? logId, String initialText = ''}) async {
    final isEditing = logId != null;
    var initialPhotos = const <ReservationTimelinePhoto>[];

    if (isEditing) {
      final detail = await _logsSectionController.loadNoteForEdit(logId);
      if (!context.mounted) return;
      if (detail == null) {
        showAppToast(
          context,
          message:
              _logsSectionController.errorMessage ??
              'No se pudo cargar la nota',
          isError: true,
        );
        return;
      }
      initialText = detail.notes;
      initialPhotos = detail.photos;
    }

    final result = await showModalBottomSheet<ReservationLogNoteSheetResult>(
      context: context,
      isScrollControlled: true,
      showDragHandle: true,
      builder: (context) {
        return ReservationLogNoteSheet(
          controller: _logsSectionController,
          isEditing: isEditing,
          initialText: initialText,
          initialPhotos: initialPhotos,
        );
      },
    );

    if (result == null || !context.mounted) return;

    final ok = isEditing
        ? await _logsSectionController.updateNote(
            logId: logId,
            text: result.text,
            photos: result.photos,
          )
        : await _logsSectionController.createNote(
            result.text,
            photos: result.photos,
          );

    if (!context.mounted) return;
    showAppToast(
      context,
      message: ok
          ? (isEditing ? 'Nota actualizada' : 'Nota registrada')
          : (_logsSectionController.errorMessage ??
                'No se pudo guardar la nota'),
      isError: !ok,
    );
  }

  Future<void> _confirmDeleteLog(ReservationTimelineEntry entry) async {
    final logId = entry.serviceLogId;
    if (logId == null) return;

    await AppConfirmDialog.show(
      context: context,
      icon: Icons.delete_outline_rounded,
      title: 'Eliminar entrada',
      message: 'Esta acción quitará la entrada de la bitácora.',
      confirmLabel: 'Eliminar',
      style: DialogStyle.danger,
      onConfirm: () async {
        final ok = await _logsSectionController.deleteEntry(logId);
        if (!mounted) return;
        showAppToast(
          context,
          message: ok
              ? 'Entrada eliminada'
              : (_logsSectionController.errorMessage ??
                    'No se pudo eliminar la entrada'),
          isError: !ok,
        );
      },
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
          Icon(
            icon,
            size: 48,
            color: Theme.of(context).colorScheme.onSurfaceVariant,
          ),
          const SizedBox(height: 16),
          Text(title, style: Theme.of(context).textTheme.titleMedium),
          const SizedBox(height: 8),
          Text(
            message,
            textAlign: TextAlign.center,
            style: Theme.of(context).textTheme.bodySmall?.copyWith(
              color: Theme.of(context).colorScheme.onSurfaceVariant,
            ),
          ),
          if (action != null) ...[const SizedBox(height: 16), action],
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
      MaterialPageRoute(builder: (_) => ParticipantDetailView(participant: p)),
    );
  }
}

typedef ReservationDetailScreen = ReservationDetailShellScreen;
