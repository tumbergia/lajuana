import 'package:http/http.dart' as http;

import 'package:mobile/app/sync/outbox_repository.dart';
import 'package:mobile/features/auth/infrastructure/token_storage.dart';
import 'domain/repositories/assignments_repository.dart';
import 'infrastructure/local/assignments_local_data_source.dart';
import 'infrastructure/remote/assignments_api_client.dart';
import 'infrastructure/repositories/assignments_repository_impl.dart';

/// Module that wires up assignments feature dependencies.
class AssignmentsModule {
  AssignmentsModule({required this.repository, required this.outbox});

  final AssignmentsRepository repository;

  /// Cola de salida compartida, usada por el board para encolar cambios
  /// (asignaciones/observaciones) cuando no hay conectividad.
  final OutboxRepository outbox;

  factory AssignmentsModule.create({
    required String baseUrl,
    required TokenStorage tokenStorage,
    required Future<bool> Function() refreshSession,
    required OutboxRepository outbox,
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

    return AssignmentsModule(repository: repository, outbox: outbox);
  }
}
