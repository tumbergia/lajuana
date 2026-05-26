import 'package:http/http.dart' as http;

import '../auth/infrastructure/token_storage.dart';
import 'domain/repositories/reservations_repository.dart';
import 'infrastructure/local/reservations_database.dart';
import 'infrastructure/local/reservations_local_data_source.dart';
import 'infrastructure/remote/reservations_api_client.dart';
import 'infrastructure/repositories/reservations_repository_impl.dart';
import 'presentation/controllers/reservation_detail_controller.dart';
import 'presentation/controllers/reservations_list_controller.dart';

class ReservationsModule {
  ReservationsModule({
    required this.repository,
    required this.listController,
  });

  final ReservationsRepository repository;
  final ReservationsListController listController;

  factory ReservationsModule.create({
    required String baseUrl,
    required TokenStorage tokenStorage,
    required Future<bool> Function() refreshSession,
    http.Client? httpClient,
  }) {
    final database = ReservationsDatabase.instance;
    final localDataSource = ReservationsLocalDataSource(database);

    final apiClient = ReservationsApiClient(
      baseUrl: baseUrl,
      readAccessToken: () async {
        final session = await tokenStorage.getSession();
        return session?.accessToken;
      },
      refreshSession: refreshSession,
      httpClient: httpClient,
    );

    final repository = ReservationsRepositoryImpl(
      apiClient: apiClient,
      localDataSource: localDataSource,
    );

    final listController = ReservationsListController(
      repository: repository,
    );

    return ReservationsModule(
      repository: repository,
      listController: listController,
    );
  }

  ReservationDetailController createDetailController() {
    return ReservationDetailController(repository: repository);
  }
}
