import 'package:flutter/material.dart';

import '../../../app/widgets/app_badge.dart';
import '../../../app/widgets/app_scaffold.dart';
import '../../domain/auth_enums.dart';
import '../auth_controller.dart';
import '../auth_routes.dart';
import '../auth_ui_helpers.dart';

class SessionGateScreen extends StatefulWidget {
  const SessionGateScreen({super.key, required this.controller});

  final AuthController controller;

  @override
  State<SessionGateScreen> createState() => _SessionGateScreenState();
}

class _SessionGateScreenState extends State<SessionGateScreen> {
  bool _navigated = false;

  @override
  void initState() {
    super.initState();
    widget.controller.appStarted();
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
            widget.controller.connectivityState == ConnectivityState.offline
            ? const AppBadge(
                label: 'Sin conexión',
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
