import '../../features/auth/presentation/auth_controller.dart';

/// Punto único para orquestar arranque técnico antes de decidir ruta de entrada.
/// Hoy delega en [AuthController.appStarted]; puede absorber más pasos sin tocar UI.
class StartupOrchestrator {
  const StartupOrchestrator._();

  static Future<void> runBootstrap(AuthController auth) async {
    await auth.appStarted();
  }
}
