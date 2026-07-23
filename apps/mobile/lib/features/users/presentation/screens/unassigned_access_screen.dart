import 'package:flutter/material.dart';
import 'package:material_symbols_icons/material_symbols_icons.dart';

import 'package:mobile/features/auth/presentation/auth_controller.dart';
import 'package:mobile/features/auth/presentation/auth_routes.dart';
import 'package:mobile/features/auth/presentation/user_role_display.dart';
import 'package:mobile/features/users/presentation/screens/request_role_screen.dart';
import 'package:mobile/features/users/users_module.dart';
import 'package:mobile_ui/src/theme/theme_extensions.dart';
import 'package:mobile_ui/src/widgets/app_button.dart';
import 'package:mobile_ui/src/widgets/app_centered_loader.dart';
import 'package:mobile_ui/src/widgets/app_empty_state.dart';

/// Full-shell screen for users without an assigned role.
class UnassignedAccessScreen extends StatefulWidget {
  const UnassignedAccessScreen({
    super.key,
    required this.usersModule,
    required this.authController,
  });

  final UsersModule usersModule;
  final AuthController authController;

  @override
  State<UnassignedAccessScreen> createState() => _UnassignedAccessScreenState();
}

class _UnassignedAccessScreenState extends State<UnassignedAccessScreen> {
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    widget.usersModule.roleRequestsController.addListener(_onChanged);
    _load();
  }

  @override
  void dispose() {
    widget.usersModule.roleRequestsController.removeListener(_onChanged);
    super.dispose();
  }

  void _onChanged() {
    if (mounted) setState(() {});
  }

  Future<void> _load() async {
    setState(() => _loading = true);
    await widget.usersModule.roleRequestsController.loadMyRequest();
    if (!mounted) return;
    setState(() => _loading = false);
  }

  Future<void> _openRequestFlow() async {
    await Navigator.of(context).push(
      MaterialPageRoute<void>(
        builder: (_) => RequestRoleScreen(
          module: widget.usersModule,
          authController: widget.authController,
        ),
      ),
    );
    if (!mounted) return;
    await _load();
    await widget.authController.profileRefreshRequested();
  }

  Future<void> _onLogoutPressed() async {
    await widget.authController.logoutRequested();
    if (!mounted) return;
    await Navigator.of(
      context,
      rootNavigator: true,
    ).pushNamedAndRemoveUntil(AuthRoutes.login, (_) => false);
  }

  @override
  Widget build(BuildContext context) {
    if (_loading) {
      return const AppCenteredLoader();
    }

    final tokens = Theme.of(context).appTokens;
    final request = widget.usersModule.roleRequestsController.myRequest;
    final pending = request?.status == 'pending';
    final approved = request?.status == 'approved';
    final rejected = request?.status == 'rejected';

    final Widget body;
    if (pending) {
      body = AppEmptyState(
        icon: Symbols.hourglass_top,
        title: 'Solicitud en revisión',
        message:
            'Pediste el rol de ${displayUserRoleLabel(request!.requestedRole)}. '
            'Un administrador la confirmará pronto.',
      );
    } else if (approved) {
      body = AppEmptyState(
        icon: Symbols.verified_user,
        title: 'Rol aprobado',
        message:
            'Te asignaron el rol de ${displayUserRoleLabel(request!.decidedRole)}. '
            'Actualizando tu acceso…',
      );
    } else if (rejected) {
      body = AppEmptyState(
        icon: Symbols.person_off,
        title: 'Solicitud rechazada',
        message: request?.note?.trim().isNotEmpty == true
            ? request!.note!
            : 'Puedes volver a solicitar un rol si lo necesitas.',
        actionLabel: 'Solicitar rol',
        actionIcon: Symbols.badge,
        onAction: _openRequestFlow,
      );
    } else {
      body = AppEmptyState(
        icon: Symbols.badge,
        title: 'Sin acceso todavía',
        message:
            'Tu cuenta aún no tiene un rol asignado. Solicita acceso de Guía '
            'o Administrador para usar la app.',
        actionLabel: 'Solicitar rol',
        actionIcon: Symbols.badge,
        onAction: _openRequestFlow,
      );
    }

    return Column(
      children: [
        Expanded(child: body),
        SafeArea(
          top: false,
          child: Padding(
            padding: EdgeInsets.fromLTRB(
              tokens.spaceXl,
              0,
              tokens.spaceXl,
              tokens.spaceLg,
            ),
            child: AppButton(
              label: 'Cerrar sesión',
              variant: AppButtonVariant.secondary,
              expanded: true,
              onPressed: _onLogoutPressed,
            ),
          ),
        ),
      ],
    );
  }
}
