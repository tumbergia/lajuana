enum OperationMode { requiresBackend, canFallbackToLocal }

class AuthOperationPolicy {
  const AuthOperationPolicy();

  OperationMode modeForBootstrap(bool hasLocalSession) {
    return hasLocalSession
        ? OperationMode.canFallbackToLocal
        : OperationMode.requiresBackend;
  }

  OperationMode modeForRefresh(bool hasLocalSession) {
    return hasLocalSession
        ? OperationMode.canFallbackToLocal
        : OperationMode.requiresBackend;
  }

  OperationMode get signIn => OperationMode.requiresBackend;

  OperationMode get register => OperationMode.requiresBackend;

  OperationMode get changePassword => OperationMode.requiresBackend;

  OperationMode get logout => OperationMode.canFallbackToLocal;
}
