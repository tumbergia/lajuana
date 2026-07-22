import 'package:flutter/foundation.dart';

import 'package:mobile/features/users/domain/user_models.dart';
import 'package:mobile/features/users/infrastructure/remote/users_api_client.dart';
import 'package:mobile/features/users/infrastructure/remote/users_api_error.dart';

enum UsersLoadState { idle, loading, refreshing, success, empty, error }

class UsersListController extends ChangeNotifier {
  UsersListController({required UsersApiClient apiClient}) : _api = apiClient;

  final UsersApiClient _api;
  bool _disposed = false;

  UsersLoadState state = UsersLoadState.idle;
  List<UserRecord> items = const <UserRecord>[];
  String searchQuery = '';
  String? errorMessage;

  List<UserRecord> _allItems = const <UserRecord>[];

  Future<void> loadInitial() async {
    state = UsersLoadState.loading;
    errorMessage = null;
    _notify();
    await _fetch();
  }

  Future<void> refresh() async {
    if (state == UsersLoadState.loading) return;
    state = UsersLoadState.refreshing;
    errorMessage = null;
    _notify();
    await _fetch();
  }

  Future<void> _fetch() async {
    try {
      final users = await _api.listUsers();
      _allItems = users;
      _applyFilters();
      state = _allItems.isEmpty ? UsersLoadState.empty : UsersLoadState.success;
      _notify();
    } on UsersApiFailure catch (e) {
      errorMessage = e.message;
      state = UsersLoadState.error;
      _notify();
    } catch (_) {
      errorMessage = 'No se pudieron cargar los usuarios.';
      state = UsersLoadState.error;
      _notify();
    }
  }

  void setSearchQuery(String query) {
    searchQuery = query;
    _applyFilters();
    _notify();
  }

  void _applyFilters() {
    final q = searchQuery.trim().toLowerCase();
    if (q.isEmpty) {
      items = _allItems;
      return;
    }
    items = _allItems
        .where(
          (u) =>
              u.fullName.toLowerCase().contains(q) ||
              u.email.toLowerCase().contains(q) ||
              u.role.toLowerCase().contains(q),
        )
        .toList(growable: false);
  }

  Future<UserRecord> createUser({
    required String email,
    required String fullName,
    required String password,
    required String role,
  }) async {
    final created = await _api.createUser(
      email: email,
      fullName: fullName,
      password: password,
      role: role,
    );
    await refresh();
    return created;
  }

  Future<UserRecord> updateUser(
    String userId, {
    String? fullName,
    String? role,
    bool? isActive,
  }) async {
    final updated = await _api.updateUser(
      userId,
      fullName: fullName,
      role: role,
      isActive: isActive,
    );
    await refresh();
    return updated;
  }

  Future<void> deactivateUser(String userId) async {
    await _api.deactivateUser(userId);
    await refresh();
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
