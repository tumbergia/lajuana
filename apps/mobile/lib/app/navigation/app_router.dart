import '../../features/auth/presentation/auth_routes.dart';
import 'route_names.dart';

/// Rutas de alto nivel; la app sigue en MaterialApp 1.0 con [onGenerateRoute].
/// Centraliza constantes para futura migración a Navigator 2 / router declarativo.
class AppRouter {
  const AppRouter._();

  static String get initialRoute => AuthRoutes.sessionGate;

  static Map<String, String> get debugNameByPath => {
    RouteNames.startupGate: 'StartupGate',
    RouteNames.login: 'Login',
    RouteNames.register: 'Register',
    RouteNames.authenticatedShell: 'AuthenticatedShell',
    RouteNames.sessionView: 'SessionView',
    RouteNames.changePassword: 'ChangePassword',
  };
}
