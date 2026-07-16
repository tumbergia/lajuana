import 'dart:async' show unawaited;

import 'package:flutter/material.dart';
import 'package:material_symbols_icons/material_symbols_icons.dart';
import 'package:mobile_domain/src/gen/in_app_notification.dart';
import 'package:mobile_domain/src/reservations/reservation_payment_proof_detail.dart';
import 'package:mobile/features/assignments/assignments_module.dart';
import 'package:mobile/features/auth/presentation/auth_controller.dart';
import 'package:mobile/features/catalogs/catalogs_module.dart';
import 'package:mobile/features/notifications/presentation/controllers/notifications_controller.dart';
import 'package:mobile/features/notifications/presentation/notification_content.dart';
import 'package:mobile/features/notifications/presentation/notification_visuals.dart';
import 'package:mobile/features/reservations/presentation/screens/reservation_detail_shell_screen.dart';
import 'package:mobile/features/reservations/presentation/widgets/reservation_proof_image_viewer.dart';
import 'package:mobile/features/reservations/reservations_module.dart';
import 'package:mobile_ui/src/widgets/app_badge.dart';
import 'package:mobile_ui/src/widgets/app_button.dart';
import 'package:mobile_ui/src/widgets/app_centered_loader.dart';
import 'package:mobile_ui/src/widgets/app_confirm_dialog.dart';
import 'package:mobile_ui/src/widgets/app_page_app_bar.dart';
import 'package:mobile_ui/src/widgets/app_status_banner.dart';
import 'package:mobile_ui/src/widgets/app_text_field.dart';
import 'package:mobile_ui/src/widgets/app_toast.dart';
import 'package:mobile_ui/src/widgets/refresh_scope.dart';
import 'package:url_launcher/url_launcher.dart';

ReservationDetailSubroute? reservationSubrouteForEvent(String eventType) {
  return switch (eventType) {
    'payment_proof_registered' => ReservationDetailSubroute.pagos,
    'participant_form_completed' => ReservationDetailSubroute.participantes,
    'assignment_changed' => ReservationDetailSubroute.asignaciones,
    'reservation_created' ||
    'reservation_confirmed' ||
    'reservation_status_changed' ||
    'reservation_updated' ||
    'reservation_cancelled' =>
      ReservationDetailSubroute.resumen,
    _ => null,
  };
}

Future<void> openWhatsAppChat(String? phone, {String? message}) async {
  final digits = whatsappDigits(phone);
  if (digits.isEmpty) return;
  final uri = message == null || message.trim().isEmpty
      ? Uri.parse('https://wa.me/$digits')
      : Uri.parse(
          'https://wa.me/$digits?text=${Uri.encodeComponent(message.trim())}',
        );
  if (!await canLaunchUrl(uri)) return;
  await launchUrl(uri, mode: LaunchMode.externalApplication);
}

class NotificationsScreen extends StatefulWidget {
  const NotificationsScreen({
    super.key,
    required this.controller,
    this.reservationsModule,
    this.catalogsModule,
    this.authController,
    this.assignmentsModule,
    this.initialOpenNotificationId,
  });

  final NotificationsController controller;
  final ReservationsModule? reservationsModule;
  final CatalogsModule? catalogsModule;
  final AuthController? authController;
  final AssignmentsModule? assignmentsModule;
  final String? initialOpenNotificationId;

  @override
  State<NotificationsScreen> createState() => _NotificationsScreenState();
}

class _NotificationsScreenState extends State<NotificationsScreen>
    with RefreshableState {
  String? _pendingOpenId;
  bool _openedInitial = false;

  @override
  void initState() {
    super.initState();
    _pendingOpenId = widget.initialOpenNotificationId;
    widget.controller.addListener(_onChanged);
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!mounted) return;
      widget.controller.setListVisible(true);
      unawaited(widget.controller.loadInitial().then((_) {
        if (!mounted) return;
        _tryOpenPending();
      }));
    });
  }

  @override
  void dispose() {
    widget.controller.setListVisible(false);
    widget.controller.removeListener(_onChanged);
    super.dispose();
  }

  void _onChanged() {
    if (mounted) setState(() {});
    _tryOpenPending();
  }

  void _tryOpenPending() {
    if (_openedInitial || _pendingOpenId == null) return;
    final id = _pendingOpenId!;
    InAppNotification? match;
    for (final item in widget.controller.items) {
      if (item.id == id) {
        match = item;
        break;
      }
    }
    if (match == null) return;
    _openedInitial = true;
    _pendingOpenId = null;
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!mounted) return;
      unawaited(_openItem(match!));
    });
  }

  @override
  Future<void> onRefresh() => widget.controller.loadInitial();

  Future<void> _openItem(InAppNotification item) async {
    if (!item.read) {
      await widget.controller.markRead(item.id);
    }
    if (!mounted) return;
    final phone = resolveNotificationPhone(
      contactPhone: item.contactPhone,
      body: item.body,
    );
    await showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      showDragHandle: true,
      builder: (sheetContext) {
        return _NotificationDetailSheet(
          item: item,
          contactPhone: phone,
          onOpenReservation: (subroute) {
            final reservationId = item.reservationId;
            Navigator.of(sheetContext).pop();
            // Wait for the sheet to finish dismissing before pushing,
            // otherwise the route push is swallowed.
            WidgetsBinding.instance.addPostFrameCallback((_) {
              if (!mounted) return;
              unawaited(_openReservation(reservationId, subroute));
            });
          },
          onOpenReservationTarget: ({String? reservationId, String? code}) {
            Navigator.of(sheetContext).pop();
            WidgetsBinding.instance.addPostFrameCallback((_) {
              if (!mounted) return;
              unawaited(
                _openReservationTarget(
                  reservationId: reservationId,
                  code: code,
                ),
              );
            });
          },
          onOpenPaymentProof: () {
            Navigator.of(sheetContext).pop();
            WidgetsBinding.instance.addPostFrameCallback((_) {
              if (!mounted) return;
              unawaited(_openPaymentProof(item));
            });
          },
          onWhatsAppReply: (message) async {
            Navigator.of(sheetContext).pop();
            WidgetsBinding.instance.addPostFrameCallback((_) {
              if (!mounted) return;
              unawaited(openWhatsAppChat(phone, message: message));
            });
          },
          onSendDirectly: (message) async {
            return widget.controller.sendWhatsAppMessage(
              phone: phone ?? '',
              message: message,
            );
          },
          onDelete: () async {
            Navigator.of(sheetContext).pop();
            await widget.controller.deleteOne(item.id);
          },
        );
      },
    );
  }

  Future<void> _openReservation(
    String? reservationId,
    ReservationDetailSubroute subroute,
  ) async {
    final module = widget.reservationsModule;
    if (reservationId == null || reservationId.isEmpty) {
      if (!mounted) return;
      showAppToast(
        context,
        message: 'Esta notificación no tiene una reserva asociada.',
        isError: true,
      );
      return;
    }
    if (module == null) {
      if (!mounted) return;
      showAppToast(
        context,
        message: 'No se pudo abrir la reserva ahora.',
        isError: true,
      );
      return;
    }
    if (!mounted) return;
    await Navigator.of(context).push(
      MaterialPageRoute<void>(
        builder: (_) => ReservationDetailShellScreen(
          reservationId: reservationId,
          reservationsModule: module,
          catalogsModule: widget.catalogsModule,
          authController: widget.authController,
          assignmentsModule: widget.assignmentsModule,
          initialSubroute: subroute,
        ),
      ),
    );
  }

  Future<void> _openReservationTarget({
    String? reservationId,
    String? code,
  }) async {
    final module = widget.reservationsModule;
    if (module == null) {
      if (!mounted) return;
      showAppToast(
        context,
        message: 'No se pudo abrir la reserva ahora.',
        isError: true,
      );
      return;
    }

    var resolvedId = reservationId?.trim();
    if (resolvedId == null || resolvedId.isEmpty) {
      final needle = code?.trim();
      if (needle == null || needle.isEmpty) {
        if (!mounted) return;
        showAppToast(
          context,
          message: 'No se encontró la reserva.',
          isError: true,
        );
        return;
      }
      try {
        final items = await module.repository.listReservations();
        for (final item in items) {
          if (item.code == needle) {
            resolvedId = item.id;
            break;
          }
        }
      } catch (_) {
        if (!mounted) return;
        showAppToast(
          context,
          message: 'No se pudo buscar la reserva.',
          isError: true,
        );
        return;
      }
    }

    if (resolvedId == null || resolvedId.isEmpty) {
      if (!mounted) return;
      showAppToast(
        context,
        message: 'No se encontró la reserva $code.',
        isError: true,
      );
      return;
    }

    await _openReservation(resolvedId, ReservationDetailSubroute.resumen);
  }

  Future<void> _openPaymentProof(InAppNotification item) async {
    final module = widget.reservationsModule;
    final reservationId = item.reservationId;
    if (module == null || reservationId == null || reservationId.isEmpty) {
      if (!mounted) return;
      showAppToast(
        context,
        message: 'No se pudo abrir el comprobante.',
        isError: true,
      );
      return;
    }

    final content = NotificationContent.from(
      eventType: item.eventType,
      title: item.title,
      body: item.body,
      contactPhone: item.contactPhone,
    );

    try {
      final detail =
          await module.repository.getReservationById(reservationId);
      ReservationPaymentProofDetail? proof;
      final proofId = content.paymentProofId;
      if (proofId != null && proofId.isNotEmpty) {
        for (final candidate in detail.paymentProofs) {
          if (candidate.id == proofId) {
            proof = candidate;
            break;
          }
        }
      }
      proof ??= detail.paymentProofs.isNotEmpty
          ? detail.paymentProofs.last
          : null;

      // Legacy notifications without proof id: try matching filename from body.
      if (proof == null ||
          (content.paymentProofId == null && detail.paymentProofs.length > 1)) {
        final filenameMatch = RegExp(r':\s*([^|]+?)(?:\||$)')
            .firstMatch(item.body.trim());
        final filename = filenameMatch?.group(1)?.trim();
        if (filename != null && filename.isNotEmpty) {
          for (final candidate in detail.paymentProofs) {
            if (candidate.filename == filename) {
              proof = candidate;
              break;
            }
          }
        }
      }

      if (!mounted) return;
      if (proof == null) {
        await _openReservation(
          reservationId,
          ReservationDetailSubroute.pagos,
        );
        return;
      }

      await Navigator.of(context).push(
        MaterialPageRoute<void>(
          builder: (_) => ProofImageViewer(
            proof: proof!,
            repository: module.repository,
          ),
        ),
      );
    } catch (_) {
      if (!mounted) return;
      showAppToast(
        context,
        message: 'No se pudo cargar el comprobante.',
        isError: true,
      );
    }
  }

  Future<void> _confirmClear({required bool readOnly}) async {
    await AppConfirmDialog.show(
      context: context,
      icon: Icons.delete_outline_rounded,
      title: readOnly ? 'Limpiar leídas' : 'Limpiar todas',
      message: readOnly
          ? 'Se eliminarán las notificaciones ya leídas del inbox.'
          : 'Se eliminarán todas las notificaciones del inbox.',
      confirmLabel: 'Limpiar',
      style: readOnly ? DialogStyle.warning : DialogStyle.danger,
      onConfirm: () async {
        try {
          await widget.controller.clearInbox(readOnly: readOnly);
        } catch (_) {
          if (!mounted) return;
          showAppToast(
            context,
            message: 'No se pudieron limpiar las notificaciones.',
            isError: true,
          );
        }
      },
    );
  }

  Future<void> _openClearActions() async {
    final hasRead = widget.controller.items.any((item) => item.read);
    await showModalBottomSheet<void>(
      context: context,
      showDragHandle: true,
      builder: (sheetContext) {
        return SafeArea(
          child: Padding(
            padding: const EdgeInsets.fromLTRB(24, 0, 24, 24),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                Text(
                  'Limpiar inbox',
                  style: Theme.of(context).textTheme.titleMedium,
                ),
                const SizedBox(height: 16),
                AppButton(
                  label: 'Limpiar leídas',
                  variant: AppButtonVariant.secondary,
                  onPressed: hasRead
                      ? () {
                          Navigator.of(sheetContext).pop();
                          unawaited(_confirmClear(readOnly: true));
                        }
                      : null,
                ),
                const SizedBox(height: 8),
                AppButton(
                  label: 'Limpiar todas',
                  variant: AppButtonVariant.danger,
                  onPressed: () {
                    Navigator.of(sheetContext).pop();
                    unawaited(_confirmClear(readOnly: false));
                  },
                ),
                const SizedBox(height: 8),
                AppButton(
                  label: 'Cancelar',
                  variant: AppButtonVariant.ghost,
                  onPressed: () => Navigator.of(sheetContext).pop(),
                ),
              ],
            ),
          ),
        );
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    final controller = widget.controller;
    final hasItems = controller.items.isNotEmpty;

    return Scaffold(
      appBar: AppPageAppBar(
        title: 'Notificaciones',
        actions: [
          if (controller.unreadCount > 0)
            IconButton(
              tooltip: 'Marcar todas',
              onPressed: controller.markAllRead,
              icon: const Icon(Icons.done_all_rounded),
            ),
          if (hasItems)
            IconButton(
              tooltip: 'Limpiar',
              onPressed: _openClearActions,
              icon: const Icon(Icons.delete_sweep_rounded),
            ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: onRefresh,
        child: _buildBody(controller),
      ),
    );
  }

  Widget _buildBody(NotificationsController controller) {
    switch (controller.loadState) {
      case NotificationsLoadState.idle:
      case NotificationsLoadState.loading:
        if (controller.items.isEmpty) {
          return const RefreshableViewport(child: AppCenteredLoader());
        }
        return _buildList(controller);
      case NotificationsLoadState.error:
        if (controller.items.isEmpty) {
          return RefreshableViewport(child: _buildErrorState(controller));
        }
        return _buildList(controller);
      case NotificationsLoadState.success:
        if (controller.items.isEmpty) {
          return const RefreshableViewport(child: _NotificationsEmptyState());
        }
        return _buildList(controller);
    }
  }

  Widget _buildList(NotificationsController controller) {
    final showErrorBanner =
        controller.loadState == NotificationsLoadState.error;
    final count = controller.items.length + (showErrorBanner ? 1 : 0);

    return ListView.separated(
      physics: const AlwaysScrollableScrollPhysics(),
      padding: const EdgeInsets.fromLTRB(24, 16, 24, 32),
      itemCount: count,
      separatorBuilder: (_, _) => const SizedBox(height: 12),
      itemBuilder: (context, index) {
        if (showErrorBanner && index == 0) {
          return AppStatusBanner(
            title: 'Error de sincronizacion',
            message: controller.errorMessage ?? 'No se pudieron actualizar.',
            tone: AppStatusBannerTone.danger,
            icon: Icons.error_outline_rounded,
            badgeLabel: 'Error',
            onTap: controller.loadInitial,
          );
        }
        final item = controller.items[showErrorBanner ? index - 1 : index];
        return _NotificationRowCard(
          item: item,
          onTap: () => _openItem(item),
        );
      },
    );
  }

  Widget _buildErrorState(NotificationsController controller) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 24),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            AppStatusBanner(
              title: 'Error al cargar',
              message: controller.errorMessage ??
                  'No se pudieron cargar las notificaciones.',
              tone: AppStatusBannerTone.danger,
              icon: Icons.error_outline_rounded,
              badgeLabel: 'Error',
            ),
            const SizedBox(height: 16),
            AppButton(
              label: 'Reintentar',
              onPressed: controller.loadInitial,
            ),
          ],
        ),
      ),
    );
  }
}

class _NotificationDetailSheet extends StatefulWidget {
  const _NotificationDetailSheet({
    required this.item,
    required this.contactPhone,
    required this.onOpenReservation,
    required this.onOpenReservationTarget,
    required this.onOpenPaymentProof,
    required this.onWhatsAppReply,
    required this.onSendDirectly,
    required this.onDelete,
  });

  final InAppNotification item;
  final String? contactPhone;
  final void Function(ReservationDetailSubroute subroute) onOpenReservation;
  final void Function({String? reservationId, String? code})
      onOpenReservationTarget;
  final VoidCallback onOpenPaymentProof;
  final Future<void> Function(String message) onWhatsAppReply;
  final Future<bool> Function(String message) onSendDirectly;
  final VoidCallback onDelete;

  @override
  State<_NotificationDetailSheet> createState() =>
      _NotificationDetailSheetState();
}

class _NotificationDetailSheetState extends State<_NotificationDetailSheet> {
  late final TextEditingController _replyController;
  late bool _composingReply;
  bool _sending = false;

  @override
  void initState() {
    super.initState();
    _replyController = TextEditingController();
    final hasPhone = whatsappDigits(widget.contactPhone).isNotEmpty;
    _composingReply =
        hasPhone && isWhatsAppPrimaryEvent(widget.item.eventType);
  }

  @override
  void dispose() {
    _replyController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final item = widget.item;
    final scheme = Theme.of(context).colorScheme;
    final visuals = notificationVisuals(item.eventType, body: item.body);
    final iconColors = notificationIconColors(context, visuals.tone);
    final content = NotificationContent.from(
      eventType: item.eventType,
      title: item.title,
      body: item.body,
      contactPhone: widget.contactPhone,
    );
    final reservationId = item.reservationId;
    final hasReservation =
        reservationId != null && reservationId.isNotEmpty;
    final primarySubroute = reservationSubrouteForEvent(item.eventType) ??
        (hasReservation ? ReservationDetailSubroute.resumen : null);
    final hasWhatsApp = whatsappDigits(widget.contactPhone).isNotEmpty;
    final whatsappPrimary = isWhatsAppPrimaryEvent(item.eventType);
    final showBitacora = hasReservation &&
        primarySubroute != ReservationDetailSubroute.bitacora;
    final bottomInset = MediaQuery.viewInsetsOf(context).bottom;

    final detailCards = <Widget>[];
    var detailSectionTitle = 'Detalle';
    if (content.isQuotedMessage && content.headline.trim().isNotEmpty) {
      detailCards.add(
        _DetailInfoCard(
          label: 'Mensaje',
          value: content.headline,
          quoted: true,
        ),
      );
    } else if (content.detailLines.isNotEmpty) {
      detailSectionTitle = 'Reservas';
      for (final line in content.detailLines) {
        final parsed = parseTomorrowReservationLine(line);
        if (parsed != null) {
          final canOpen = parsed.code != 'Más';
          detailCards.add(
            _DetailInfoCard(
              label: parsed.code,
              value: parsed.subtitle,
              onTap: canOpen
                  ? () => widget.onOpenReservationTarget(
                        reservationId: parsed.reservationId,
                        code: parsed.code,
                      )
                  : null,
            ),
          );
        } else {
          detailCards.add(
            _DetailInfoCard(
              label: 'Reserva',
              value: line,
            ),
          );
        }
      }
    }

    final isPaymentProof = item.eventType == 'payment_proof_registered';
    final contextFacts = content.keyFacts.where((fact) {
      if (fact.value.trim().isEmpty) return false;
      if (fact.label == 'Reserva' && content.detailLines.isNotEmpty) {
        return false;
      }
      if (fact.label == 'Servicio' && content.detailLines.isNotEmpty) {
        return false;
      }
      if (fact.label == 'Archivo') return false;
      return true;
    }).toList(growable: false);

    return SafeArea(
      child: Padding(
        padding: EdgeInsets.fromLTRB(24, 8, 24, 24 + bottomInset),
        child: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Container(
                    width: 48,
                    height: 48,
                    decoration: BoxDecoration(
                      color: iconColors.background,
                      borderRadius: BorderRadius.circular(4),
                    ),
                    child: Icon(
                      visuals.icon,
                      size: 24,
                      color: iconColors.foreground,
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          item.title,
                          style:
                              Theme.of(context).textTheme.titleLarge?.copyWith(
                                    fontWeight: FontWeight.w800,
                                  ),
                        ),
                        const SizedBox(height: 4),
                        Text(
                          '${visuals.label} · ${formatRelativeTime(item.createdAt)}',
                          style:
                              Theme.of(context).textTheme.bodyMedium?.copyWith(
                                    color: scheme.onSurfaceVariant,
                                  ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
              if (detailCards.isNotEmpty) ...[
                const SizedBox(height: 20),
                _DetailSection(
                  title: detailSectionTitle,
                  children: detailCards,
                ),
              ],
              if (contextFacts.isNotEmpty) ...[
                const SizedBox(height: 12),
                _DetailSection(
                  title: 'Contexto',
                  children: [
                    for (final fact in contextFacts)
                      _DetailInfoCard(label: fact.label, value: fact.value),
                  ],
                ),
              ],
              const SizedBox(height: 20),
              if (hasWhatsApp && _composingReply) ...[
                AppTextField(
                  controller: _replyController,
                  label: 'Respuesta',
                  hintText: 'Escribe tu mensaje…',
                  maxLines: 4,
                ),
                const SizedBox(height: 12),
                Row(
                  children: [
                    Expanded(
                      child: AppButton(
                        label: 'Abrir WhatsApp',
                        icon: Symbols.chat,
                        onPressed: () =>
                            widget.onWhatsAppReply(_replyController.text),
                      ),
                    ),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Theme(
                        data: Theme.of(context).copyWith(
                          colorScheme: Theme.of(context).colorScheme.copyWith(
                            primary: const Color(0xFF25D366),
                            onPrimary: Colors.white,
                          ),
                        ),
                        child: AppButton(
                          label: _sending ? 'Enviando…' : 'Enviar mensaje',
                          variant: AppButtonVariant.primary,
                          icon: Symbols.send,
                          onPressed: _sending
                              ? null
                              : () async {
                                  final msg = _replyController.text.trim();
                                  if (msg.isEmpty) return;
                                  setState(() => _sending = true);
                                  final ok =
                                      await widget.onSendDirectly(msg);
                                  setState(() => _sending = false);
                                  if (ok && mounted) {
                                    Navigator.of(context).pop();
                                    showAppToast(
                                      context,
                                      message: 'Mensaje enviado.',
                                    );
                                  } else if (!ok && mounted) {
                                    showAppToast(
                                      context,
                                      message: 'Error al enviar mensaje.',
                                      isError: true,
                                    );
                                  }
                                },
                        ),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 8),
              ] else if (hasWhatsApp) ...[
                AppButton(
                  label: 'Responder',
                  icon: Symbols.chat,
                  onPressed: () => setState(() => _composingReply = true),
                ),
                const SizedBox(height: 8),
              ],
              if (isPaymentProof && hasReservation) ...[
                AppButton(
                  label: 'Ver comprobante',
                  icon: Symbols.image,
                  onPressed: widget.onOpenPaymentProof,
                ),
                const SizedBox(height: 8),
                AppButton(
                  label: 'Ver pagos',
                  variant: AppButtonVariant.secondary,
                  onPressed: () => widget
                      .onOpenReservation(ReservationDetailSubroute.pagos),
                ),
                const SizedBox(height: 8),
              ] else if (primarySubroute != null && hasReservation) ...[
                AppButton(
                  label: _primaryActionLabel(primarySubroute),
                  variant: hasWhatsApp && whatsappPrimary
                      ? AppButtonVariant.secondary
                      : AppButtonVariant.primary,
                  onPressed: () => widget.onOpenReservation(primarySubroute),
                ),
                const SizedBox(height: 8),
              ],
              if (showBitacora) ...[
                AppButton(
                  label: 'Ver bitácora',
                  variant: AppButtonVariant.secondary,
                  icon: Symbols.menu_book,
                  onPressed: () => widget
                      .onOpenReservation(ReservationDetailSubroute.bitacora),
                ),
                const SizedBox(height: 8),
              ],
              AppButton(
                label: 'Eliminar',
                variant: AppButtonVariant.ghost,
                icon: Symbols.delete,
                onPressed: widget.onDelete,
              ),
            ],
          ),
        ),
      ),
    );
  }

  String _primaryActionLabel(ReservationDetailSubroute subroute) {
    return switch (subroute) {
      ReservationDetailSubroute.pagos => 'Ver pagos',
      ReservationDetailSubroute.participantes => 'Ver participantes',
      ReservationDetailSubroute.asignaciones => 'Ver asignaciones',
      ReservationDetailSubroute.bitacora => 'Ver bitácora',
      ReservationDetailSubroute.proveedores => 'Ver proveedores',
      ReservationDetailSubroute.resumen => 'Ir a la reserva',
    };
  }
}

class _DetailSection extends StatelessWidget {
  const _DetailSection({
    required this.title,
    required this.children,
  });

  final String title;
  final List<Widget> children;

  @override
  Widget build(BuildContext context) {
    if (children.isEmpty) return const SizedBox.shrink();

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          title.toUpperCase(),
          style: Theme.of(context).textTheme.labelSmall?.copyWith(
                letterSpacing: 1.2,
                color: Theme.of(context).colorScheme.onSurfaceVariant,
              ),
        ),
        const SizedBox(height: 8),
        for (var i = 0; i < children.length; i++) ...[
          if (i > 0) const SizedBox(height: 10),
          children[i],
        ],
      ],
    );
  }
}

/// Card-style fact row (like the old detail rows) without forcing UPPERCASE values.
class _DetailInfoCard extends StatelessWidget {
  const _DetailInfoCard({
    required this.label,
    required this.value,
    this.quoted = false,
    this.onTap,
  });

  final String label;
  final String value;
  final bool quoted;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final card = ClipRRect(
      borderRadius: BorderRadius.circular(4),
      child: ColoredBox(
        color: scheme.surfaceContainerLow,
        child: Container(
          width: double.infinity,
          padding: const EdgeInsets.fromLTRB(16, 14, 12, 14),
          decoration: quoted
              ? BoxDecoration(
                  border: Border(
                    left: BorderSide(color: scheme.primary, width: 3),
                  ),
                )
              : null,
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.center,
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      label.toUpperCase(),
                      style: Theme.of(context).textTheme.labelSmall?.copyWith(
                            color: scheme.onSurfaceVariant,
                            fontWeight: FontWeight.w700,
                            letterSpacing: 0.8,
                          ),
                    ),
                    const SizedBox(height: 6),
                    Text(
                      value,
                      style: Theme.of(context).textTheme.titleMedium?.copyWith(
                            fontWeight: FontWeight.w700,
                            height: 1.3,
                            color: scheme.onSurface,
                          ),
                    ),
                  ],
                ),
              ),
              if (onTap != null)
                Icon(
                  Icons.chevron_right_rounded,
                  size: 20,
                  color: scheme.onSurfaceVariant,
                ),
            ],
          ),
        ),
      ),
    );

    if (onTap == null) return card;
    return Material(
      color: Colors.transparent,
      child: InkWell(
        borderRadius: BorderRadius.circular(4),
        onTap: onTap,
        child: card,
      ),
    );
  }
}

class _NotificationsEmptyState extends StatelessWidget {
  const _NotificationsEmptyState();

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(
            Symbols.notifications,
            size: 48,
            color: scheme.onSurfaceVariant,
          ),
          const SizedBox(height: 16),
          Text(
            'Sin notificaciones',
            style: Theme.of(context).textTheme.titleMedium,
          ),
          const SizedBox(height: 8),
          Text(
            'Cuando haya actividad operativa aparecera aqui.',
            textAlign: TextAlign.center,
            style: Theme.of(context).textTheme.bodySmall?.copyWith(
                  color: scheme.onSurfaceVariant,
                ),
          ),
        ],
      ),
    );
  }
}

class _NotificationRowCard extends StatelessWidget {
  const _NotificationRowCard({
    required this.item,
    required this.onTap,
  });

  final InAppNotification item;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final unread = !item.read;
    final visuals = notificationVisuals(item.eventType, body: item.body);
    final toneColors = appBadgeToneColors(context, visuals.tone);
    final iconColors = notificationIconColors(context, visuals.tone);
    final scheme = Theme.of(context).colorScheme;
    final content = NotificationContent.from(
      eventType: item.eventType,
      title: item.title,
      body: item.body,
      contactPhone: item.contactPhone,
    );
    final accent = unread
        ? toneColors.background
        : appBadgeToneTint(context, visuals.tone, alpha: 0.55);
    final background =
        unread ? scheme.surfaceContainerHighest : scheme.surfaceContainerLow;
    final compact = content.compactFacts;

    return Material(
      color: Colors.transparent,
      child: InkWell(
        borderRadius: BorderRadius.circular(4),
        onTap: onTap,
        child: ClipRRect(
          borderRadius: BorderRadius.circular(4),
          child: ColoredBox(
            color: background,
            child: Stack(
              children: [
                Padding(
                  padding: const EdgeInsets.fromLTRB(16, 14, 12, 14),
                  child: Row(
                    crossAxisAlignment: CrossAxisAlignment.center,
                    children: [
                      Container(
                        width: 44,
                        height: 44,
                        decoration: BoxDecoration(
                          color: iconColors.background,
                          borderRadius: BorderRadius.circular(4),
                        ),
                        child: Icon(
                          visuals.icon,
                          size: 22,
                          color: iconColors.foreground,
                        ),
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              '${visuals.label} · ${formatRelativeTime(item.createdAt)}',
                              style: Theme.of(context)
                                  .textTheme
                                  .labelSmall
                                  ?.copyWith(
                                    color: scheme.onSurfaceVariant,
                                    fontWeight: FontWeight.w600,
                                  ),
                            ),
                            const SizedBox(height: 4),
                            Text(
                              content.previewLine.isNotEmpty
                                  ? content.previewLine
                                  : item.title,
                              maxLines: 2,
                              overflow: TextOverflow.ellipsis,
                              style: Theme.of(context)
                                  .textTheme
                                  .titleMedium
                                  ?.copyWith(
                                    fontWeight: FontWeight.w700,
                                    height: 1.25,
                                    color: scheme.onSurface,
                                  ),
                            ),
                            if (compact.isNotEmpty) ...[
                              const SizedBox(height: 4),
                              Text(
                                compact,
                                maxLines: 1,
                                overflow: TextOverflow.ellipsis,
                                style: Theme.of(context)
                                    .textTheme
                                    .bodySmall
                                    ?.copyWith(
                                      color: scheme.onSurfaceVariant,
                                      fontWeight: FontWeight.w500,
                                      height: 1.25,
                                    ),
                              ),
                            ],
                          ],
                        ),
                      ),
                      const SizedBox(width: 4),
                      Icon(
                        Icons.chevron_right_rounded,
                        size: 18,
                        color: scheme.onSurfaceVariant,
                      ),
                    ],
                  ),
                ),
                Positioned(
                  left: 0,
                  top: 0,
                  bottom: 0,
                  child: ColoredBox(
                    color: accent,
                    child: const SizedBox(width: 4),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

