import 'package:mobile/features/auth/domain/auth_enums.dart';
import 'package:mobile/features/auth/infrastructure/connectivity/backend_reachability_service.dart';
import 'package:mobile/features/auth/infrastructure/connectivity/connectivity_service.dart';
import 'package:mobile/features/auth/infrastructure/connectivity/network_status_resolver.dart';
import 'package:mobile/features/auth/infrastructure/local/auth_database.dart';
import 'package:mobile/features/auth/infrastructure/local/session_local_data_source.dart';
import 'package:mobile/features/auth/infrastructure/local/user_local_data_source.dart';
import 'package:mobile/features/auth/infrastructure/remote/auth_api_client.dart';
import 'package:mobile/features/auth/infrastructure/repositories/auth_repository_impl.dart';
import 'package:mobile/features/auth/infrastructure/token_storage.dart';
import 'package:mobile/features/auth/presentation/auth_controller.dart';
import 'package:mobile/features/assignments/assignments_module.dart';
import 'package:mobile/features/catalogs/catalogs_module.dart';
import 'package:mobile/features/catalogs/data/catalogs_database.dart';
import 'package:mobile/features/catalogs/data/catalogs_repository.dart';
import 'package:mobile/features/catalogs/data/catalogs_sync_api.dart';
import 'package:mobile_domain/src/equines/equine_event_repository.dart';
import 'package:mobile_domain/src/equines/equine_repository.dart';
import 'package:mobile/features/equines/infrastructure/local/equines_database.dart';
import 'package:mobile/features/equines/infrastructure/remote/equines_api_client.dart';
import 'package:mobile/features/equines/infrastructure/repositories/equine_event_repository_impl.dart';
import 'package:mobile/features/equines/infrastructure/repositories/equine_repository_impl.dart';
import 'package:mobile/features/reservations/reservations_module.dart';
import 'package:mobile/features/saddles/saddles_module.dart';

/// Value object holding all initialized application dependencies.
class AppDependencies {
  const AppDependencies({
    required this.authController,
    required this.apiClient,
    required this.catalogsModule,
    required this.reservationsModule,
    required this.saddlesModule,
    required this.assignmentsModule,
    required this.equineRepository,
    required this.equineEventRepository,
  });

  final AuthController authController;
  final AuthApiClient apiClient;
  final CatalogsModule catalogsModule;
  final ReservationsModule reservationsModule;
  final SaddlesModule saddlesModule;
  final AssignmentsModule assignmentsModule;
  final EquineRepository equineRepository;
  final EquineEventRepository equineEventRepository;

  /// Dispose controllers that need explicit cleanup.
  void dispose() {
    authController.dispose();
    reservationsModule.listController.dispose();
    saddlesModule.listController.dispose();
  }
}

/// Creates all application dependencies from [apiBaseUrl].
///
/// Extracted from app.dart initState to separate DI wiring from widget
/// lifecycle (W3.2 del plan de mejora).
Future<AppDependencies> createDependencies(String apiBaseUrl) async {
  // ── Auth chain ──
  final apiClient = AuthApiClient(baseUrl: apiBaseUrl);
  final database = AuthDatabase.instance;
  final sessionDs = SessionLocalDataSource(database);
  final userDs = UserLocalDataSource(database);
  final repository = AuthRepositoryImpl(
    apiClient: apiClient,
    sessionLocalDataSource: sessionDs,
    userLocalDataSource: userDs,
  );

  final connectivityService = ConnectivityPlusService();
  final reachabilityService = HttpBackendReachabilityService(
    baseUrl: apiBaseUrl,
  );
  final networkStatusResolver = NetworkStatusResolver(
    connectivityService: connectivityService,
    backendReachabilityService: reachabilityService,
  );

  final authController = AuthController(
    authRepository: repository,
    networkStatusResolver: networkStatusResolver,
  );

  // ── Shared refresh session closure ──
  Future<bool> refreshSession() async {
    await authController.refreshRequested();
    return authController.authState == LocalAuthState.signedInVerified;
  }

  Future<String?> readAccessToken() async {
    return (await sessionDs.getCurrentSession())?.accessToken;
  }

  // ── Catalogs module ──
  final catalogsApi = CatalogsSyncApi(
    baseUrl: apiBaseUrl,
    readAccessToken: readAccessToken,
    refreshSession: refreshSession,
  );
  final catalogsRepository = CatalogsRepository(
    database: CatalogsDatabase.instance,
    api: catalogsApi,
  );
  final catalogsModule = CatalogsModule(catalogsRepository);

  // ── Core modules (reservations, saddles, assignments) ──
  final tokenStorage = SqliteTokenStorage(sessionDs);

  final reservationsModule = ReservationsModule.create(
    baseUrl: apiBaseUrl,
    tokenStorage: tokenStorage,
    refreshSession: refreshSession,
  );

  final saddlesModule = SaddlesModule.create(
    baseUrl: apiBaseUrl,
    tokenStorage: tokenStorage,
    refreshSession: refreshSession,
  );

  final assignmentsModule = AssignmentsModule.create(
    baseUrl: apiBaseUrl,
    tokenStorage: tokenStorage,
    refreshSession: refreshSession,
  );

  // ── Equine module ──
  final equinesApiClient = EquinesApiClient(
    baseUrl: apiBaseUrl,
    readAccessToken: readAccessToken,
    refreshSession: refreshSession,
  );
  final equinesDatabase = EquinesDatabase.instance;
  final equineRepository = EquineRepositoryImpl(
    apiClient: equinesApiClient,
    database: equinesDatabase,
  );
  final equineEventRepository = EquineEventRepositoryImpl(
    apiClient: equinesApiClient,
    database: equinesDatabase,
  );

  return AppDependencies(
    authController: authController,
    apiClient: apiClient,
    catalogsModule: catalogsModule,
    reservationsModule: reservationsModule,
    saddlesModule: saddlesModule,
    assignmentsModule: assignmentsModule,
    equineRepository: equineRepository,
    equineEventRepository: equineEventRepository,
  );
}
