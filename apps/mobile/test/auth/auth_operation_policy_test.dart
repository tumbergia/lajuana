import 'package:flutter_test/flutter_test.dart';
import 'package:mobile/features/auth/application/auth_operation_policy.dart';

void main() {
  test('AuthOperationPolicy: operaciones criticas requieren backend', () {
    const policy = AuthOperationPolicy();
    expect(policy.signIn, OperationMode.requiresBackend);
    expect(policy.register, OperationMode.requiresBackend);
    expect(policy.changePassword, OperationMode.requiresBackend);
    expect(policy.logout, OperationMode.canFallbackToLocal);
    expect(policy.modeForBootstrap(false), OperationMode.requiresBackend);
    expect(policy.modeForBootstrap(true), OperationMode.canFallbackToLocal);
  });
}
