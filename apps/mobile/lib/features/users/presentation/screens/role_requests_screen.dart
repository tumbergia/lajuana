import 'package:flutter/material.dart';
import 'package:material_symbols_icons/material_symbols_icons.dart';

import 'package:mobile/features/auth/presentation/user_role_display.dart';
import 'package:mobile/features/users/domain/user_models.dart';
import 'package:mobile/features/users/infrastructure/remote/users_api_error.dart';
import 'package:mobile/features/users/presentation/controllers/role_requests_controller.dart';
import 'package:mobile/features/users/users_module.dart';
import 'package:mobile_ui/src/theme/theme_extensions.dart';
import 'package:mobile_ui/src/widgets/app_badge.dart';
import 'package:mobile_ui/src/widgets/app_button.dart';
import 'package:mobile_ui/src/widgets/app_centered_loader.dart';
import 'package:mobile_ui/src/widgets/app_empty_state.dart';
import 'package:mobile_ui/src/widgets/app_entity_row_card.dart';
import 'package:mobile_ui/src/widgets/app_section_header.dart';
import 'package:mobile_ui/src/widgets/app_toast.dart';
import 'package:mobile_ui/src/widgets/refresh_scope.dart';

class RoleRequestsScreen extends StatefulWidget {
  const RoleRequestsScreen({super.key, required this.module});

  final UsersModule module;

  @override
  State<RoleRequestsScreen> createState() => _RoleRequestsScreenState();
}

class _RoleRequestsScreenState extends State<RoleRequestsScreen>
    with RefreshableState {
  late final RoleRequestsController _controller;

  @override
  Future<void> onRefresh() => _controller.refreshPending();

  @override
  void initState() {
    super.initState();
    _controller = widget.module.roleRequestsController;
    _controller.addListener(_onChanged);
    if (_controller.state == RoleRequestsLoadState.idle) {
      _controller.loadPending();
    }
  }

  @override
  void dispose() {
    _controller.removeListener(_onChanged);
    super.dispose();
  }

  void _onChanged() {
    if (mounted) setState(() {});
  }

  Future<void> _openDecision(RoleRequestRecord request) async {
    final result = await showModalBottomSheet<_DecisionResult>(
      context: context,
      isScrollControlled: true,
      backgroundColor: Theme.of(context).colorScheme.surface,
      builder: (_) => _RoleDecisionSheet(request: request),
    );
    if (result == null || !mounted) return;
    try {
      await _controller.decide(
        requestId: request.id,
        action: result.action,
        assignedRole: result.assignedRole,
      );
      if (!mounted) return;
      showAppToast(
        context,
        message: result.action == 'approve'
            ? 'Solicitud aprobada.'
            : 'Solicitud rechazada.',
      );
    } on UsersApiFailure catch (e) {
      if (!mounted) return;
      showAppToast(context, message: e.message, isError: true);
    } catch (_) {
      if (!mounted) return;
      showAppToast(
        context,
        message: 'No se pudo resolver la solicitud',
        isError: true,
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final tokens = Theme.of(context).appTokens;
    return Scaffold(
      body: SafeArea(
        child: Padding(
          padding: EdgeInsets.all(tokens.spaceXl),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              AppSectionHeader(
                title: 'Solicitudes de rol',
                subtitle: 'Acepta el rol pedido o asigna otro',
                trailing: AppButton(
                  label: 'Volver',
                  icon: Icons.arrow_back_rounded,
                  variant: AppButtonVariant.ghost,
                  onPressed: () => Navigator.pop(context),
                ),
              ),
              SizedBox(height: tokens.spaceMd),
              Expanded(child: _buildBody()),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildBody() {
    switch (_controller.state) {
      case RoleRequestsLoadState.idle:
      case RoleRequestsLoadState.loading:
        return const RefreshableViewport(child: AppCenteredLoader());
      case RoleRequestsLoadState.error:
        return RefreshableViewport(
          child: AppEntityRowCard(
            title: 'No se pudieron cargar las solicitudes',
            subtitle: _controller.errorMessage ?? 'Revisa la conexión',
            badge: const AppBadge(label: 'Error', tone: AppBadgeTone.danger),
            onTap: _controller.loadPending,
          ),
        );
      case RoleRequestsLoadState.empty:
        return const RefreshableViewport(
          child: AppEmptyState(
            icon: Symbols.inbox,
            title: 'Sin solicitudes pendientes',
            message: 'Cuando alguien sin rol pida acceso, aparecerá aquí.',
          ),
        );
      case RoleRequestsLoadState.refreshing:
      case RoleRequestsLoadState.success:
        return ListView.separated(
          physics: const AlwaysScrollableScrollPhysics(),
          itemCount: _controller.pending.length,
          separatorBuilder: (_, _) => const SizedBox(height: 10),
          itemBuilder: (context, index) {
            final item = _controller.pending[index];
            return AppEntityRowCard(
              title: item.userFullName,
              subtitle:
                  '${item.userEmail}\nPide: ${displayUserRoleLabel(item.requestedRole)}',
              leading: const Icon(Symbols.person_alert, size: 22),
              badge: const AppBadge(
                label: 'Pendiente',
                tone: AppBadgeTone.warning,
                uppercase: false,
              ),
              trailing: const Icon(Icons.chevron_right_rounded, size: 18),
              onTap: () => _openDecision(item),
            );
          },
        );
    }
  }
}

class _DecisionResult {
  const _DecisionResult({required this.action, this.assignedRole});

  final String action;
  final String? assignedRole;
}

class _RoleDecisionSheet extends StatefulWidget {
  const _RoleDecisionSheet({required this.request});

  final RoleRequestRecord request;

  @override
  State<_RoleDecisionSheet> createState() => _RoleDecisionSheetState();
}

class _RoleDecisionSheetState extends State<_RoleDecisionSheet> {
  late String _assignedRole;

  @override
  void initState() {
    super.initState();
    _assignedRole = widget.request.requestedRole == 'admin' ? 'admin' : 'guide';
  }

  @override
  Widget build(BuildContext context) {
    final tokens = Theme.of(context).appTokens;
    final bottom = MediaQuery.viewInsetsOf(context).bottom;
    final request = widget.request;
    return Padding(
      padding: EdgeInsets.fromLTRB(24, 24, 24, 24 + bottom),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          const AppSectionHeader(
            eyebrow: 'Solicitud',
            title: 'Resolver solicitud',
          ),
          SizedBox(height: tokens.spaceMd),
          AppEntityRowCard(
            title: request.userFullName,
            subtitle: request.userEmail,
            badge: AppBadge(
              label: 'Pide ${displayUserRoleLabel(request.requestedRole)}',
              tone: AppBadgeTone.primary,
              uppercase: false,
            ),
            selected: true,
          ),
          SizedBox(height: tokens.spaceMd),
          Text(
            'Rol a asignar si apruebas',
            style: Theme.of(context).textTheme.labelLarge,
          ),
          SizedBox(height: tokens.spaceSm),
          AppEntityRowCard(
            title: 'Guía',
            subtitle: 'Reservas, equinos y operación diaria',
            selected: _assignedRole == 'guide',
            onTap: () => setState(() => _assignedRole = 'guide'),
          ),
          SizedBox(height: tokens.spaceSm),
          AppEntityRowCard(
            title: 'Administrador',
            subtitle: 'Acceso completo, usuarios y configuración',
            selected: _assignedRole == 'admin',
            onTap: () => setState(() => _assignedRole = 'admin'),
          ),
          SizedBox(height: tokens.spaceLg),
          AppButton(
            label: 'Aceptar rol',
            expanded: true,
            onPressed: () {
              Navigator.pop(
                context,
                _DecisionResult(action: 'approve', assignedRole: _assignedRole),
              );
            },
          ),
          SizedBox(height: tokens.spaceSm),
          AppButton(
            label: 'Rechazar',
            variant: AppButtonVariant.secondary,
            expanded: true,
            onPressed: () {
              Navigator.pop(context, const _DecisionResult(action: 'reject'));
            },
          ),
        ],
      ),
    );
  }
}
