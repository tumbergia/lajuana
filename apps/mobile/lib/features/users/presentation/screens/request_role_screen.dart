import 'package:flutter/material.dart';

import 'package:mobile/app/errors/user_facing_error.dart';
import 'package:mobile/features/auth/presentation/auth_controller.dart';
import 'package:mobile/features/auth/presentation/user_role_display.dart';
import 'package:mobile/features/users/infrastructure/remote/users_api_error.dart';
import 'package:mobile/features/users/presentation/controllers/role_requests_controller.dart';
import 'package:mobile/features/users/users_module.dart';
import 'package:mobile_ui/src/theme/theme_extensions.dart';
import 'package:mobile_ui/src/widgets/app_badge.dart';
import 'package:mobile_ui/src/widgets/app_button.dart';
import 'package:mobile_ui/src/widgets/app_centered_loader.dart';
import 'package:mobile_ui/src/widgets/app_entity_row_card.dart';
import 'package:mobile_ui/src/widgets/app_section_header.dart';
import 'package:mobile_ui/src/widgets/app_toast.dart';

class RequestRoleScreen extends StatefulWidget {
  const RequestRoleScreen({
    super.key,
    required this.module,
    required this.authController,
  });

  final UsersModule module;
  final AuthController authController;

  @override
  State<RequestRoleScreen> createState() => _RequestRoleScreenState();
}

class _RequestRoleScreenState extends State<RequestRoleScreen> {
  late final RoleRequestsController _controller;
  String _requestedRole = 'guide';
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _controller = widget.module.roleRequestsController;
    _controller.addListener(_onChanged);
    _load();
  }

  @override
  void dispose() {
    _controller.removeListener(_onChanged);
    super.dispose();
  }

  void _onChanged() {
    if (mounted) setState(() {});
  }

  Future<void> _load() async {
    setState(() => _loading = true);
    await _controller.loadMyRequest();
    if (!mounted) return;
    setState(() => _loading = false);
  }

  Future<void> _submit() async {
    try {
      await _controller.createMyRequest(_requestedRole);
      if (!mounted) return;
      showAppToast(
        context,
        message: 'Solicitud enviada. Un administrador la revisará.',
      );
      await widget.authController.profileRefreshRequested();
    } on UsersApiFailure catch (e) {
      if (!mounted) return;
      showAppToast(
        context,
        message: userFacingError(
          e,
          fallback: 'No se pudo enviar la solicitud',
        ),
        isError: true,
      );
    } catch (e) {
      if (!mounted) return;
      showAppToast(
        context,
        message: userFacingError(
          e,
          fallback: 'No se pudo enviar la solicitud',
        ),
        isError: true,
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final tokens = Theme.of(context).appTokens;
    final request = _controller.myRequest;

    return Scaffold(
      body: SafeArea(
        child: _loading
            ? const AppCenteredLoader()
            : LayoutBuilder(
                builder: (context, constraints) {
                  return SingleChildScrollView(
                    padding: EdgeInsets.all(tokens.spaceXl),
                    child: ConstrainedBox(
                      constraints: BoxConstraints(
                        minHeight: constraints.maxHeight - (tokens.spaceXl * 2),
                      ),
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        crossAxisAlignment: CrossAxisAlignment.stretch,
                        children: [
                          AppSectionHeader(
                            title: 'Solicitar rol',
                            subtitle:
                                'Elige el rol que necesitas. Un administrador lo confirmará.',
                            trailing: AppButton(
                              label: 'Volver',
                              icon: Icons.arrow_back_rounded,
                              variant: AppButtonVariant.ghost,
                              onPressed: () => Navigator.pop(context),
                            ),
                          ),
                          SizedBox(height: tokens.spaceLg),
                          if (request != null && request.status == 'pending')
                            AppEntityRowCard(
                              title: 'Solicitud pendiente',
                              subtitle:
                                  'Pediste: ${displayUserRoleLabel(request.requestedRole)}',
                              badge: const AppBadge(
                                label: 'En revisión',
                                tone: AppBadgeTone.warning,
                                uppercase: false,
                              ),
                              selected: true,
                            )
                          else if (request != null &&
                              request.status != 'pending') ...[
                            AppEntityRowCard(
                              title: request.status == 'approved'
                                  ? 'Solicitud aprobada'
                                  : 'Solicitud rechazada',
                              subtitle: request.status == 'approved'
                                  ? 'Rol asignado: ${displayUserRoleLabel(request.decidedRole)}'
                                  : (request.note ??
                                      'Puedes volver a solicitar si lo necesitas.'),
                              badge: AppBadge(
                                label: request.status == 'approved'
                                    ? 'Aprobada'
                                    : 'Rechazada',
                                tone: request.status == 'approved'
                                    ? AppBadgeTone.success
                                    : AppBadgeTone.danger,
                                uppercase: false,
                              ),
                              selected: true,
                            ),
                            if (request.status == 'rejected') ...[
                              SizedBox(height: tokens.spaceLg),
                              ..._buildRolePicker(tokens),
                            ],
                          ] else ...[
                            ..._buildRolePicker(tokens),
                          ],
                        ],
                      ),
                    ),
                  );
                },
              ),
      ),
    );
  }

  List<Widget> _buildRolePicker(AppThemeTokens tokens) {
    return [
      AppEntityRowCard(
        title: 'Guía',
        subtitle: 'Reservas, equinos y operación diaria',
        selected: _requestedRole == 'guide',
        onTap: () => setState(() => _requestedRole = 'guide'),
      ),
      SizedBox(height: tokens.spaceSm),
      AppEntityRowCard(
        title: 'Administrador',
        subtitle: 'Acceso completo, usuarios y configuración',
        selected: _requestedRole == 'admin',
        onTap: () => setState(() => _requestedRole = 'admin'),
      ),
      SizedBox(height: tokens.spaceLg),
      AppButton(
        label: _controller.submitting ? 'Enviando...' : 'Enviar solicitud',
        expanded: true,
        onPressed: _controller.submitting ? null : _submit,
      ),
    ];
  }
}
