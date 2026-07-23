import 'package:http/http.dart' as http;

import 'package:mobile/app/sync/outbox_repository.dart';
import 'package:mobile/features/auth/infrastructure/token_storage.dart';
import 'package:mobile_domain/src/providers/providers_repository.dart';
import 'infrastructure/remote/providers_api_client.dart';
import 'infrastructure/repositories/providers_repository_impl.dart';
import 'presentation/controllers/providers_list_controller.dart';

class ProvidersModule {
  ProvidersModule({required this.repository, required this.listController});

  final ProvidersRepository repository;
  final ProvidersListController listController;

  factory ProvidersModule.create({
    required String baseUrl,
    required TokenStorage tokenStorage,
    required Future<bool> Function() refreshSession,
    required OutboxRepository outbox,
    http.Client? httpClient,
  }) {
    final apiClient = ProvidersApiClient(
      baseUrl: baseUrl,
      readAccessToken: () async {
        final session = await tokenStorage.getSession();
        return session?.accessToken;
      },
      refreshSession: refreshSession,
      httpClient: httpClient,
    );

    final repository = ProvidersRepositoryImpl(
      apiClient: apiClient,
      outbox: outbox,
    );

    final listController = ProvidersListController(repository: repository);

    return ProvidersModule(
      repository: repository,
      listController: listController,
    );
  }
}
