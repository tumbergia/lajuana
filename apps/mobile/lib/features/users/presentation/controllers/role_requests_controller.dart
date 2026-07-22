import 'package:flutter/foundation.dart';

import 'package:mobile/features/users/domain/user_models.dart';
import 'package:mobile/features/users/infrastructure/remote/users_api_client.dart';
import 'package:mobile/features/users/infrastructure/remote/users_api_error.dart';

enum RoleRequestsLoadState { idle, loading, refreshing, success, empty, error }

class RoleRequestsController extends ChangeNotifier {
  RoleRequestsController({required UsersApiClient apiClient}) : _api = apiClient;

  final UsersApiClient _api;
  bool _disposed = false;

  RoleRequestsLoadState state = RoleRequestsLoadState.idle;
  List<RoleRequestRecord> pending = const <RoleRequestRecord>[];
  RoleRequestRecord? myRequest;
  String? errorMessage;
  bool submitting = false;

  int get pendingCount => pending.length;

  Future<void> loadPending() async {
    state = RoleRequestsLoadState.loading;
    errorMessage = null;
    _notify();
    await _fetchPending();
  }

  Future<void> refreshPending() async {
    if (state == RoleRequestsLoadState.loading) return;
    state = RoleRequestsLoadState.refreshing;
    errorMessage = null;
    _notify();
    await _fetchPending();
  }

  Future<void> _fetchPending() async {
    try {
      pending = await _api.listRoleRequests(status: 'pending');
      state = pending.isEmpty
          ? RoleRequestsLoadState.empty
          : RoleRequestsLoadState.success;
      _notify();
    } on UsersApiFailure catch (e) {
      errorMessage = e.message;
      state = RoleRequestsLoadState.error;
      _notify();
    } catch (_) {
      errorMessage = 'No se pudieron cargar las solicitudes.';
      state = RoleRequestsLoadState.error;
      _notify();
    }
  }

  Future<void> loadMyRequest() async {
    errorMessage = null;
    _notify();
    try {
      myRequest = await _api.getMyRoleRequest();
      _notify();
    } on UsersApiFailure catch (e) {
      errorMessage = e.message;
      _notify();
    } catch (_) {
      errorMessage = 'No se pudo consultar tu solicitud.';
      _notify();
    }
  }

  Future<RoleRequestRecord> createMyRequest(String requestedRole) async {
    submitting = true;
    errorMessage = null;
    _notify();
    try {
      myRequest = await _api.createMyRoleRequest(requestedRole);
      return myRequest!;
    } on UsersApiFailure catch (e) {
      errorMessage = e.message;
      rethrow;
    } finally {
      submitting = false;
      _notify();
    }
  }

  Future<RoleRequestRecord> decide({
    required String requestId,
    required String action,
    String? assignedRole,
    String? note,
  }) async {
    submitting = true;
    errorMessage = null;
    _notify();
    try {
      final decided = await _api.decideRoleRequest(
        requestId: requestId,
        action: action,
        assignedRole: assignedRole,
        note: note,
      );
      await refreshPending();
      return decided;
    } on UsersApiFailure catch (e) {
      errorMessage = e.message;
      rethrow;
    } finally {
      submitting = false;
      _notify();
    }
  }

  void _notify() {
    if (!_disposed) notifyListeners();
  }

  @override
  void dispose() {
    _disposed = true;
    super.dispose();
  }
}
