import 'package:flutter/material.dart';

import '../../../../app/widgets/app_badge.dart';
import '../../../../app/widgets/app_button.dart';
import '../../../../app/widgets/app_entity_row_card.dart';
import '../../../../app/widgets/app_scaffold.dart';
import '../../../../app/widgets/app_section_header.dart';
import '../../../../app/widgets/app_top_bar.dart';
import '../../domain/auth_enums.dart';
import '../auth_controller.dart';
import '../auth_routes.dart';
import '../auth_ui_helpers.dart';
import '../user_role_display.dart';

class SessionViewScreen extends StatelessWidget {
  const SessionViewScreen({super.key, required this.controller});

  final AuthController controller;

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: controller,
      builder: (context, _) {
        final user = controller.currentUser;
        final lastStateText = switch (controller.authState) {
          LocalAuthState.signedInVerified => 'Verificada',
          LocalAuthState.signedInLocalUnverified => 'Local',
          LocalAuthState.refreshRequired => 'Expirada',
          LocalAuthState.invalid => 'Inválida',
          LocalAuthState.signedOut => 'Sin sesión',
        };

        return AppScaffold(
          appBar: const AppTopBar(
            logoAssetPath: 'assets/branding/lajuana.svg',
            title: 'Sesión',
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const AppSectionHeader(
                title: 'Sesión',
                subtitle: 'Vista técnica',
              ),
              const SizedBox(height: 12),
              authStateBadge(controller.authState),
              const SizedBox(height: 12),
              if (controller.hasPendingSync)
                const AppBadge(
                  label: 'Cambios pendientes de sincronización',
                  tone: AppBadgeTone.warning,
                  uppercase: false,
                ),
              const SizedBox(height: 12),
              AppEntityRowCard(
                title: user?.fullName ?? 'Sin usuario',
                subtitle:
                    'EMAIL: ${user?.email ?? '-'} • ROL: ${user?.role == null ? '-' : displayUserRoleLabel(user!.role)}',
                selected: true,
                badge: AppBadge(
                  label: lastStateText,
                  tone: controller.authState == LocalAuthState.signedInVerified
                      ? AppBadgeTone.success
                      : AppBadgeTone.warning,
                  uppercase: false,
                ),
              ),
              const SizedBox(height: 16),
              AppButton(
                label: 'Cambiar contraseña',
                expanded: true,
                onPressed: () {
                  Navigator.of(context).pushNamed(AuthRoutes.changePassword);
                },
              ),
              const SizedBox(height: 8),
              AppButton(
                label: 'Cerrar sesión',
                variant: AppButtonVariant.secondary,
                expanded: true,
                onPressed: () async {
                  await controller.logoutRequested();
                  if (!context.mounted) return;
                  Navigator.of(
                    context,
                  ).pushNamedAndRemoveUntil(AuthRoutes.login, (_) => false);
                },
              ),
            ],
          ),
        );
      },
    );
  }
}
