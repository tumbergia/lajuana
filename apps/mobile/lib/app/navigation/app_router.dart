import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';

import '../../features/auth/domain/auth_enums.dart';
import '../../features/auth/presentation/auth_routes.dart';
import '../../features/auth/presentation/screens/change_password_screen.dart';
import '../../features/auth/presentation/screens/login_screen.dart';
import '../../features/auth/presentation/screens/register_screen.dart';
import '../../features/auth/presentation/screens/session_view_screen.dart';
import '../bootstrap/dev_loader_screen.dart';
import '../bootstrap/dev/widget_museum_placeholder.dart';
import '../bootstrap/startup_gate.dart';
import '../dependency_injection.dart';
import '../shell/authenticated_shell.dart';

/// Route generator for La Juana app.
///
/// Extracted from _LaJuanaAppState._buildRoute to separate routing
/// from widget lifecycle (W3.1 del plan de mejora).
class AppRouter {
  AppRouter(this.dependencies);

  final AppDependencies dependencies;

  bool _isAuthenticated() {
    final state = dependencies.authController.authState;
    return state == LocalAuthState.signedInVerified ||
        state == LocalAuthState.signedInLocalUnverified;
  }

  /// Resolves dev/playground screens — only in non-release builds.
  Widget? _devScreen(String routeName) {
    if (kReleaseMode) return null;
    switch (routeName) {
      case AuthRoutes.devLoader:
        return const DevWidgetCatalogScreen();
      case AuthRoutes.widgetMuseum:
        return const WidgetMuseumPlaceholder();
      default:
        return null;
    }
  }

  Route<dynamic> onGenerateRoute(RouteSettings settings) {
    final routeName = settings.name ?? AuthRoutes.sessionGate;
    final canAccessAuthenticated = _isAuthenticated();
    final deps = dependencies;
    late final Widget screen;

    switch (routeName) {
      case AuthRoutes.devLoader:
      case AuthRoutes.widgetMuseum:
        screen = _devScreen(routeName) ??
            StartupGate(controller: deps.authController);
        break;
      case AuthRoutes.sessionGate:
        screen = StartupGate(controller: deps.authController);
        break;
      case AuthRoutes.login:
        screen = LoginScreen(controller: deps.authController);
        break;
      case AuthRoutes.register:
        screen = RegisterScreen(controller: deps.authController);
        break;
      case AuthRoutes.home:
        screen = canAccessAuthenticated
            ? AuthenticatedShell(
                authController: deps.authController,
                contactsApiClient: deps.apiClient,
                catalogsModule: deps.catalogsModule,
                reservationsModule: deps.reservationsModule,
                saddlesModule: deps.saddlesModule,
                assignmentsModule: deps.assignmentsModule,
                equineRepository: deps.equineRepository,
              )
            : LoginScreen(controller: deps.authController);
        break;
      case AuthRoutes.sessionView:
        screen = canAccessAuthenticated
            ? SessionViewScreen(controller: deps.authController)
            : LoginScreen(controller: deps.authController);
        break;
      case AuthRoutes.changePassword:
        screen = canAccessAuthenticated
            ? ChangePasswordScreen(controller: deps.authController)
            : LoginScreen(controller: deps.authController);
        break;
      default:
        screen = StartupGate(controller: deps.authController);
    }

    return MaterialPageRoute<void>(builder: (_) => screen, settings: settings);
  }
}
