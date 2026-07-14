import 'package:flutter/material.dart';

import 'package:mobile_ui/src/widgets/app_badge.dart';
import 'package:mobile_ui/src/widgets/app_button.dart';
import 'package:mobile_ui/src/widgets/app_entity_row_card.dart';
import 'package:mobile_ui/src/widgets/app_scaffold.dart';
import 'package:mobile_ui/src/widgets/app_section_header.dart';
import 'package:mobile_ui/src/widgets/app_top_bar.dart';
import 'package:mobile/features/auth/domain/auth_enums.dart';
import 'package:mobile/features/auth/presentation/auth_controller.dart';
import 'package:mobile/features/auth/presentation/auth_routes.dart';
import 'package:mobile/features/auth/presentation/auth_ui_helpers.dart';
import 'package:mobile/features/auth/presentation/user_role_display.dart';

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
            logoAssetPath: 'assets/branding/lajuana-banner.svg',
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
