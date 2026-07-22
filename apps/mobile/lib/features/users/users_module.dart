import 'package:http/http.dart' as http;

import 'package:mobile/features/auth/infrastructure/token_storage.dart';
import 'package:mobile/features/users/infrastructure/remote/users_api_client.dart';
import 'package:mobile/features/users/presentation/controllers/role_requests_controller.dart';
import 'package:mobile/features/users/presentation/controllers/users_list_controller.dart';

class UsersModule {
  UsersModule({
    required this.apiClient,
    required this.usersController,
    required this.roleRequestsController,
  });

  final UsersApiClient apiClient;
  final UsersListController usersController;
  final RoleRequestsController roleRequestsController;

  factory UsersModule.create({
    required String baseUrl,
    required TokenStorage tokenStorage,
    required Future<bool> Function() refreshSession,
    http.Client? httpClient,
  }) {
    final apiClient = UsersApiClient(
      baseUrl: baseUrl,
      readAccessToken: () async {
        final session = await tokenStorage.getSession();
        return session?.accessToken;
      },
      refreshSession: refreshSession,
      httpClient: httpClient,
    );
    return UsersModule(
      apiClient: apiClient,
      usersController: UsersListController(apiClient: apiClient),
      roleRequestsController: RoleRequestsController(apiClient: apiClient),
    );
  }

  void dispose() {
    usersController.dispose();
    roleRequestsController.dispose();
  }
}
