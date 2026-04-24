import 'package:flutter/material.dart';

import '../../features/auth/domain/auth_enums.dart';
import '../../features/auth/infrastructure/connectivity/network_models.dart';
import '../../features/auth/presentation/auth_controller.dart';
import '../../features/auth/presentation/auth_routes.dart';
import '../widgets/app_badge.dart';
import '../widgets/app_scaffold.dart';
import '../../features/auth/presentation/auth_ui_helpers.dart';
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
                Text(
                  'LA JUANA',
                  style: Theme.of(context).textTheme.displaySmall?.copyWith(
                    fontWeight: FontWeight.w800,
                    letterSpacing: 1.4,
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
