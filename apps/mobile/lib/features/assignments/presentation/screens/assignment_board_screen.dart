import 'package:flutter/material.dart';

import 'package:mobile_ui/src/theme/theme_extensions.dart';
import 'package:mobile_ui/src/widgets/app_button.dart';
import 'package:mobile_ui/src/widgets/app_centered_loader.dart';
import 'package:mobile_ui/src/widgets/app_scaffold.dart';
import 'package:mobile_ui/src/widgets/app_section_header.dart';
import 'package:mobile_ui/src/widgets/app_status_banner.dart';
import 'package:mobile_domain/src/assignments/assignment_board.dart';
import 'package:mobile_domain/mobile_domain.dart';
import 'package:mobile/features/assignments/presentation/controllers/assignment_board_controller.dart';
import 'package:mobile/features/assignments/presentation/widgets/board_action_buttons.dart';
import 'package:mobile/features/assignments/presentation/widgets/board_equines_grid.dart';
import 'package:mobile/features/assignments/presentation/widgets/board_participant_tile.dart';
import 'package:mobile/features/assignments/presentation/widgets/board_saddles_grid.dart';
import 'package:mobile/features/assignments/presentation/widgets/board_summary_bar.dart';

/// Pantalla de tablero de asignaciones para una reserva.
///
/// Muestra el resumen de asignaciones, lista de participantes con su
/// estado de asignación, equinos y sillas disponibles.
class AssignmentBoardScreen extends StatefulWidget {
  final AssignmentBoardController controller;
  final String reservationId;
  final bool isAdmin;
  final bool isOnline;

  const AssignmentBoardScreen({
    super.key,
    required this.controller,
    required this.reservationId,
    this.isAdmin = false,
    this.isOnline = true,
  });

  @override
  State<AssignmentBoardScreen> createState() => _AssignmentBoardScreenState();
}

class _AssignmentBoardScreenState extends State<AssignmentBoardScreen> {
  final _observationController = TextEditingController();
  String? _lastActionErrorCode;

  @override
  void initState() {
    super.initState();
    widget.controller.addListener(_onStateChanged);
  }

  @override
  void dispose() {
    widget.controller.removeListener(_onStateChanged);
    _observationController.dispose();
    super.dispose();
  }

  void _onStateChanged() {
    if (!mounted) return;
    final errCode = widget.controller.actionErrorCode;
    if (widget.controller.actionError != null &&
        errCode != _lastActionErrorCode) {
      _lastActionErrorCode = errCode;
      WidgetsBinding.instance.addPostFrameCallback((_) {
        if (!mounted) return;
        final msg = widget.controller.actionError;
        if (msg != null) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text(msg),
              backgroundColor: Theme.of(context).colorScheme.error,
            ),
          );
          widget.controller.clearActionError();
        }
      });
    }
    setState(() {});
  }

  @override
  Widget build(BuildContext context) {
    final ctrl = widget.controller;
    final isLoading = ctrl.state == BoardLoadState.initial || ctrl.state == BoardLoadState.loading;
    return AppScaffold(
      scrollable: !isLoading,
      child: _buildBody(ctrl),
    );
  }

  Widget _buildBody(AssignmentBoardController ctrl) {
    switch (ctrl.state) {
      case BoardLoadState.initial:
      case BoardLoadState.loading:
        return const AppCenteredLoader();
      case BoardLoadState.error:
        return _ErrorState(
          message: ctrl.error ?? 'Error al cargar el tablero',
          onRetry: ctrl.refresh,
        );
      case BoardLoadState.offlineFromCache:
      case BoardLoadState.loaded:
        final board = ctrl.board;
        if (board == null) {
          return const _ErrorState(message: 'No hay datos disponibles');
        }
        return SingleChildScrollView(
          child: Column(
            children: [
              if (ctrl.isOffline)
                AppStatusBanner(
                  title: 'Datos almacenados',
                  message: 'Sin conexión — mostrando última vista guardada.',
                  tone: AppStatusBannerTone.warning,
                  icon: Icons.wifi_off_rounded,
                  badgeLabel: 'Offline',
                ),
              _BoardContent(
                board: board,
                ctrl: ctrl,
                isAdmin: widget.isAdmin,
                isOnline: widget.isOnline,
                observationController: _observationController,
              ),
            ],
          ),
        );
    }
  }
}

// ── Board content ──

class _BoardContent extends StatelessWidget {
  final AssignmentBoard board;
  final AssignmentBoardController ctrl;
  final bool isAdmin;
  final bool isOnline;
  final TextEditingController observationController;

  const _BoardContent({
    required this.board,
    required this.ctrl,
    required this.isAdmin,
    required this.isOnline,
    required this.observationController,
  });

  @override
  Widget build(BuildContext context) {
    final tokens = Theme.of(context).appTokens;
    final availableEquines = board.availableEquines
        .where((e) => e.isAvailable)
        .toList();
    final unavailableEquines = board.availableEquines
        .where((e) => !e.isAvailable)
        .toList();
    final availableSaddles = board.availableSaddles
        .where((s) => s.isAvailable)
        .toList();
    final unavailableSaddles = board.availableSaddles
        .where((s) => !s.isAvailable)
        .toList();

    final hasConfirmedAssignments = board.participants.any(
      (p) => p.assignment?.status == AssignmentStatus.confirmed,
    ) || ctrl.hasPendingChanges;
    final hasFinalizedAssignments = board.participants.any(
      (p) => p.assignment?.status == AssignmentStatus.final_,
    );

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        BoardSummaryBar(summary: board.summary),
        const SizedBox(height: 24),

        if (board.participants.isEmpty)
          _EmptyState(message: 'No hay participantes registrados')
        else
          ...board.participants.map(
            (p) => Padding(
              padding: EdgeInsets.only(bottom: tokens.spaceMd),
              child: BoardParticipantTile(
                participant: p,
                availableEquines: board.availableEquines,
                availableSaddles: board.availableSaddles,
                isAdmin: isAdmin,
                isOnline: isOnline,
                ctrl: ctrl,
              ),
            ),
          ),

        if (isOnline) ...[
          const SizedBox(height: 16),
          TextField(
            controller: observationController,
            decoration: const InputDecoration(
              hintText: 'Agregar observación...',
              border: OutlineInputBorder(),
            ),
            maxLines: 3,
          ),
          const SizedBox(height: 12),
        ],

        if (isAdmin && isOnline) ...[
          if (hasConfirmedAssignments)
            Padding(
              padding: const EdgeInsets.only(bottom: 8),
              child: AppButton(
                label: 'Finalizar asignaciones',
                icon: ctrl.isFinalizing ? null : Icons.check_circle_outline_rounded,
                variant: AppButtonVariant.primary,
                expanded: true,
                onPressed: ctrl.isFinalizing
                    ? null
                    : () => showFinalizeAllConfirm(
                          context,
                          ctrl,
                          observationController,
                        ),
              ),
            ),
          if (hasFinalizedAssignments)
            AppButton(
              label: 'Revertir finalizaciones',
              icon: ctrl.isRevertingFinalize ? null : Icons.undo_rounded,
              variant: AppButtonVariant.ghost,
              expanded: true,
              onPressed: ctrl.isRevertingFinalize
                  ? null
                  : () => showUnfinalizeAllConfirm(
                        context,
                        ctrl,
                        observationController,
                      ),
            ),
          const SizedBox(height: 12),
        ],

        const SizedBox(height: 24),
        AppSectionHeader(
          title: 'Equinos disponibles',
          subtitle: '${availableEquines.length} disponibles',
          variant: AppSectionHeaderVariant.compact,
        ),
        const SizedBox(height: 12),
        BoardEquinesGrid(equines: availableEquines),

        const SizedBox(height: 24),
        AppSectionHeader(
          title: 'Sillas disponibles',
          subtitle: '${availableSaddles.length} disponibles',
          variant: AppSectionHeaderVariant.compact,
        ),
        const SizedBox(height: 12),
        BoardSaddlesGrid(saddles: availableSaddles),

        if (unavailableEquines.isNotEmpty) ...[
          const SizedBox(height: 24),
          AppSectionHeader(
            title: 'Equinos no disponibles',
            subtitle: '${unavailableEquines.length} bloqueados',
            variant: AppSectionHeaderVariant.compact,
          ),
          const SizedBox(height: 12),
          BoardEquinesGrid(equines: unavailableEquines),
        ],

        if (unavailableSaddles.isNotEmpty) ...[
          const SizedBox(height: 24),
          AppSectionHeader(
            title: 'Sillas no disponibles',
            subtitle: '${unavailableSaddles.length} bloqueadas',
            variant: AppSectionHeaderVariant.compact,
          ),
          const SizedBox(height: 12),
          BoardSaddlesGrid(saddles: unavailableSaddles),
        ],
      ],
    );
  }
}

// ── Empty state ──

class _EmptyState extends StatelessWidget {
  final String message;
  const _EmptyState({required this.message});

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;

    return Container(
      width: double.infinity,
      padding: const EdgeInsets.symmetric(vertical: 32, horizontal: 16),
      decoration: BoxDecoration(
        color: scheme.surfaceContainerLow,
        borderRadius: BorderRadius.circular(4),
      ),
      child: Column(
        children: [
          Icon(
            Icons.inbox_outlined,
            size: 40,
            color: scheme.onSurfaceVariant.withValues(alpha: 0.5),
          ),
          const SizedBox(height: 12),
          Text(
            message,
            style: Theme.of(context)
                .textTheme
                .bodyMedium
                ?.copyWith(color: scheme.onSurfaceVariant),
          ),
        ],
      ),
    );
  }
}

// ── Error state ──

class _ErrorState extends StatelessWidget {
  final String message;
  final VoidCallback? onRetry;

  const _ErrorState({required this.message, this.onRetry});

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;

    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(Icons.error_outline_rounded, size: 48, color: scheme.error),
            const SizedBox(height: 16),
            Text(
              message,
              textAlign: TextAlign.center,
              style: Theme.of(context)
                  .textTheme
                  .bodyLarge
                  ?.copyWith(color: scheme.onSurfaceVariant),
            ),
            if (onRetry != null) ...[
              const SizedBox(height: 16),
              AppButton(
                label: 'Reintentar',
                icon: Icons.refresh_rounded,
                onPressed: onRetry,
              ),
            ],
          ],
        ),
      ),
    );
  }
}
