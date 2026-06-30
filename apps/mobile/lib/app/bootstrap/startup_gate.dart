import 'package:flutter/material.dart';
import 'package:flutter_svg/flutter_svg.dart';

import 'package:mobile/features/auth/domain/auth_enums.dart';
import 'package:mobile/features/auth/infrastructure/connectivity/network_models.dart';
import 'package:mobile/features/auth/presentation/auth_controller.dart';
import 'package:mobile/features/auth/presentation/auth_routes.dart';
import 'package:mobile_ui/src/widgets/app_badge.dart';
import 'package:mobile_ui/src/widgets/app_scaffold.dart';
import 'package:mobile/features/auth/presentation/auth_ui_helpers.dart';
import 'startup_orchestrator.dart';

/// Puerta de entrada técnica: bootstrap + decisión login vs área autenticada.
/// No renderiza negocio de módulos.
class StartupGate extends StatefulWidget {
  const StartupGate({super.key, required this.controller});

  final AuthController controller;

  @override
  State<StartupGate> createState() => _StartupGateState();
}

class _StartupGateState extends State<StartupGate> {
  bool _navigated = false;

  @override
  void initState() {
    super.initState();
    StartupOrchestrator.runBootstrap(widget.controller);
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: widget.controller,
      builder: (context, _) {
        if (!widget.controller.isBootstrapping && !_navigated) {
          final route = _resolveTargetRoute(widget.controller.authState);
          _navigated = true;
          WidgetsBinding.instance.addPostFrameCallback((_) {
            if (!mounted) return;
            Navigator.of(context).pushReplacementNamed(route);
          });
        }

        final statusBadge =
            widget.controller.networkStatus.linkType == LinkType.offline
            ? const AppBadge(
                label: 'Sin enlace de red',
                tone: AppBadgeTone.danger,
                uppercase: false,
              )
            : authStateBadge(widget.controller.authState);

        return AppScaffold(
          scrollable: false,
          child: Center(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                SizedBox(
                  width: 220,
                  height: 220 / (1600 / 567),
                  child: SvgPicture.asset(
                    'assets/branding/lajuana-banner.svg',
                    fit: BoxFit.contain,
                    colorFilter: ColorFilter.mode(
                      Theme.of(context).colorScheme.onSurface,
                      BlendMode.srcIn,
                    ),
                  ),
                ),
                const SizedBox(height: 16),
                const SizedBox(
                  height: 28,
                  width: 28,
                  child: CircularProgressIndicator(strokeWidth: 2.5),
                ),
                const SizedBox(height: 16),
                statusBadge,
              ],
            ),
          ),
        );
      },
    );
  }

  String _resolveTargetRoute(LocalAuthState state) {
    switch (state) {
      case LocalAuthState.signedInVerified:
      case LocalAuthState.signedInLocalUnverified:
        return AuthRoutes.home;
      case LocalAuthState.signedOut:
      case LocalAuthState.refreshRequired:
      case LocalAuthState.invalid:
        return AuthRoutes.login;
    }
  }
}
