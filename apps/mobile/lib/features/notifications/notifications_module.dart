import 'package:mobile/features/auth/infrastructure/token_storage.dart';
import 'package:mobile/features/notifications/domain/notifications_repository.dart';
import 'package:mobile/features/notifications/infrastructure/notifications_api_client.dart';
import 'package:mobile/features/notifications/presentation/controllers/notifications_controller.dart';

class NotificationsModule {
  const NotificationsModule({
    required this.repository,
    required this.controller,
  });

  final NotificationsRepository repository;
  final NotificationsController controller;

  factory NotificationsModule.create({
    required String baseUrl,
    required TokenStorage tokenStorage,
    required Future<bool> Function() refreshSession,
  }) {
    final apiClient = NotificationsApiClient(
      baseUrl: baseUrl,
      readAccessToken: () async {
        final session = await tokenStorage.getSession();
        return session?.accessToken;
      },
      refreshSession: refreshSession,
    );
    final repository = NotificationsRepositoryImpl(apiClient: apiClient);
    final controller = NotificationsController(repository: repository);
    return NotificationsModule(
      repository: repository,
      controller: controller,
    );
  }

  void dispose() {
    controller.dispose();
  }
}
