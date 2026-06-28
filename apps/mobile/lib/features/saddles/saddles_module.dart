import 'package:http/http.dart' as http;

import 'package:mobile/app/sync/outbox_repository.dart';
import 'package:mobile/features/auth/infrastructure/token_storage.dart';
import 'domain/repositories/saddles_repository.dart';
import 'infrastructure/remote/saddles_api_client.dart';
import 'infrastructure/repositories/saddles_repository_impl.dart';
import 'presentation/controllers/saddles_list_controller.dart';

class SaddlesModule {
  SaddlesModule({
    required this.repository,
    required this.listController,
  });

  final SaddlesRepository repository;
  final SaddlesListController listController;

  factory SaddlesModule.create({
    required String baseUrl,
    required TokenStorage tokenStorage,
    required Future<bool> Function() refreshSession,
    required OutboxRepository outbox,
    http.Client? httpClient,
  }) {
    final apiClient = SaddlesApiClient(
      baseUrl: baseUrl,
      readAccessToken: () async {
        final session = await tokenStorage.getSession();
        return session?.accessToken;
      },
      refreshSession: refreshSession,
      httpClient: httpClient,
    );

    final repository = SaddlesRepositoryImpl(
      apiClient: apiClient,
      outbox: outbox,
    );

    final listController = SaddlesListController(
      repository: repository,
    );

    return SaddlesModule(
      repository: repository,
      listController: listController,
    );
  }
}
