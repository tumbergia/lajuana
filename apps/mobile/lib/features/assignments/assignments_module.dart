import 'package:http/http.dart' as http;

import 'package:mobile/features/auth/infrastructure/token_storage.dart';
import 'domain/repositories/assignments_repository.dart';
import 'infrastructure/local/assignments_local_data_source.dart';
import 'infrastructure/remote/assignments_api_client.dart';
import 'infrastructure/repositories/assignments_repository_impl.dart';

/// Module that wires up assignments feature dependencies.
class AssignmentsModule {
  AssignmentsModule({required this.repository});

  final AssignmentsRepository repository;

  factory AssignmentsModule.create({
    required String baseUrl,
    required TokenStorage tokenStorage,
    required Future<bool> Function() refreshSession,
    http.Client? httpClient,
    AssignmentsLocalDataSource? localDataSource,
  }) {
    final apiClient = AssignmentsApiClient(
      baseUrl: baseUrl,
      readAccessToken: () async {
        final session = await tokenStorage.getSession();
        return session?.accessToken;
      },
      refreshSession: refreshSession,
      httpClient: httpClient,
    );

    final repository = AssignmentsRepositoryImpl(
      api: apiClient,
      local: localDataSource ?? AssignmentsLocalDataSource(),
    );

    return AssignmentsModule(repository: repository);
  }
}
