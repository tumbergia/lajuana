import 'package:flutter_test/flutter_test.dart';
import 'package:mobile/app/errors/user_facing_error.dart';
import 'package:mobile/features/assignments/infrastructure/remote/assignments_api_client.dart';
import 'package:mobile/features/users/infrastructure/remote/users_api_error.dart';

void main() {
  const fallback = 'No se pudo completar la acción.';

  test('uses clean Spanish API message', () {
    final error = UsersApiFailure(
      code: 'role_request.not_pending',
      message: 'La solicitud ya fue resuelta.',
    );
    expect(
      userFacingError(error, fallback: fallback),
      'La solicitud ya fue resuelta.',
    );
  });

  test('prefers clean message over code mapping', () {
    final error = UsersApiFailure(
      code: 'user.not_found',
      message: 'Usuario no encontrado.',
    );
    expect(userFacingError(error, fallback: fallback), 'Usuario no encontrado.');
  });

  test('maps common codes when message is technical', () {
    final error = AssignmentsApiFailure(
      code: 'auth.forbidden',
      message: 'AssignmentsApiFailure(auth.forbidden): denied',
    );
    expect(
      userFacingError(error, fallback: fallback),
      'No tienes permiso para esta acción.',
    );
  });

  test('falls back for Exception.toString style errors', () {
    expect(
      userFacingError(Exception('network boom'), fallback: fallback),
      fallback,
    );
  });

  test('falls back for SocketException-like text in message', () {
    final error = UsersApiFailure(
      code: 'common.error',
      message: 'SocketException: Failed host lookup',
    );
    expect(userFacingError(error, fallback: fallback), fallback);
  });

  test('falls back for bare error codes as message', () {
    final error = UsersApiFailure(
      code: 'x',
      message: 'role_request.not_pending',
    );
    expect(userFacingError(error, fallback: fallback), fallback);
  });

  test('uses clean AssignmentsApiFailure message', () {
    final error = AssignmentsApiFailure(
      code: 'assignments.weird',
      message: 'No se pudo confirmar la asignación.',
    );
    expect(
      userFacingError(error, fallback: fallback),
      'No se pudo confirmar la asignación.',
    );
  });

  test('maps not_found codes when message empty', () {
    final error = UsersApiFailure(code: 'user.not_found', message: '');
    expect(
      userFacingError(error, fallback: fallback),
      'No encontramos lo que buscabas.',
    );
  });
}
