import 'package:flutter/material.dart';

import 'package:mobile/features/auth/domain/auth_enums.dart';
import 'package:mobile/features/auth/presentation/auth_controller.dart';
import 'package:mobile/features/auth/presentation/auth_routes.dart';
import 'package:mobile/features/auth/presentation/widgets/session_loading_view.dart';
import 'package:mobile_ui/src/widgets/app_scaffold.dart';
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

        return const AppScaffold(scrollable: false, child: SessionLoadingView());
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
