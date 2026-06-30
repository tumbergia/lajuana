import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';

import 'package:mobile/features/auth/domain/auth_enums.dart';
import 'package:mobile/features/auth/presentation/auth_routes.dart';
import 'package:mobile/features/auth/presentation/screens/change_password_screen.dart';
import 'package:mobile/features/auth/presentation/screens/login_screen.dart';
import 'package:mobile/features/auth/presentation/screens/register_screen.dart';
import 'package:mobile/features/auth/presentation/screens/session_view_screen.dart';
import 'package:mobile/app/bootstrap/dev_loader_screen.dart' deferred as dev;
import 'package:mobile/app/bootstrap/dev/widget_museum_placeholder.dart'
    deferred as dev_ph;
import 'package:mobile/app/bootstrap/startup_gate.dart';
import 'package:mobile/app/dependency_injection.dart';
import 'package:mobile/app/shell/authenticated_shell.dart';

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
  ///
  /// Uses [deferred] imports so the dev code is tree-shaken in release.
  /// Note: Flutter AOT (iOS/Android) does not support true lazy loading,
  /// so [loadLibrary] is called as a no-op for web compat.  The real
  /// exclusion is the [kReleaseMode] guard (W3.8 del plan de mejora).
  Widget? _devScreen(String routeName) {
    if (kReleaseMode) return null;
    dev.loadLibrary();
    dev_ph.loadLibrary();
    switch (routeName) {
      case AuthRoutes.devLoader:
        return dev.DevWidgetCatalogScreen();
      case AuthRoutes.widgetMuseum:
        return dev_ph.WidgetMuseumPlaceholder();
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
                providersModule: deps.providersModule,
                assignmentsModule: deps.assignmentsModule,
                equineRepository: deps.equineRepository,
                equineEventRepository: deps.equineEventRepository,
                voiceAssistantModule: deps.voiceAssistantModule,
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
