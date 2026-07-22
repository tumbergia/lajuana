import 'package:mobile/features/analytics/remote/analytics_api_client.dart';
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
import 'package:mobile/app/sync/outbox_repository.dart';
import 'package:mobile/app/sync/sync_database.dart';
import 'package:mobile/app/sync/sync_outbox_client.dart';
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
import 'package:mobile/features/providers/providers_module.dart';
import 'package:mobile/features/voice_assistant/voice_assistant_module.dart';
import 'package:mobile/features/configuration/configuration_module.dart';
import 'package:mobile/features/configuration/infrastructure/configuration_api_client.dart';
import 'package:mobile/features/notifications/notifications_module.dart';
import 'package:mobile/features/users/users_module.dart';

/// Value object holding all initialized application dependencies.
class AppDependencies {
  const AppDependencies({
    required this.authController,
    required this.apiClient,
    required this.analyticsApiClient,
    required this.catalogsModule,
    required this.reservationsModule,
    required this.saddlesModule,
    required this.providersModule,
    required this.assignmentsModule,
    required this.equineRepository,
    required this.equineEventRepository,
    required this.outbox,
    required this.voiceAssistantModule,
    required this.configurationModule,
    required this.notificationsModule,
    required this.usersModule,
  });

  final AuthController authController;
  final AuthApiClient apiClient;
  final AnalyticsApiClient analyticsApiClient;
  final CatalogsModule catalogsModule;
  final ReservationsModule reservationsModule;
  final SaddlesModule saddlesModule;
  final ProvidersModule providersModule;
  final AssignmentsModule assignmentsModule;
  final EquineRepository equineRepository;
  final EquineEventRepository equineEventRepository;
  final VoiceAssistantModule voiceAssistantModule;
  final LaJuanaConfigurationModule configurationModule;
  final NotificationsModule notificationsModule;
  final UsersModule usersModule;

  /// Cola de salida compartida para escrituras offline (asignaciones, saddles).
  final OutboxRepository outbox;

  /// Dispose controllers that need explicit cleanup.
  void dispose() {
    authController.dispose();
    reservationsModule.listController.dispose();
    saddlesModule.listController.dispose();
    providersModule.listController.dispose();
    voiceAssistantModule.controller.dispose();
    notificationsModule.dispose();
    usersModule.dispose();
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

  // ── Shared offline outbox ──
  final syncOutboxClient = SyncOutboxClient(
    baseUrl: apiBaseUrl,
    readAccessToken: readAccessToken,
    refreshSession: refreshSession,
  );
  final outbox = OutboxRepository(
    database: SyncDatabase.instance,
    api: syncOutboxClient,
  );

  // ── Core modules (reservations, saddles, assignments) ──
  final tokenStorage = SqliteTokenStorage(sessionDs);

  final reservationsModule = ReservationsModule.create(
    baseUrl: apiBaseUrl,
    tokenStorage: tokenStorage,
    refreshSession: refreshSession,
    outbox: syncOutboxClient,
  );

  final saddlesModule = SaddlesModule.create(
    baseUrl: apiBaseUrl,
    tokenStorage: tokenStorage,
    refreshSession: refreshSession,
    outbox: outbox,
  );

  final providersModule = ProvidersModule.create(
    baseUrl: apiBaseUrl,
    tokenStorage: tokenStorage,
    refreshSession: refreshSession,
    outbox: outbox,
  );

  final assignmentsModule = AssignmentsModule.create(
    baseUrl: apiBaseUrl,
    tokenStorage: tokenStorage,
    refreshSession: refreshSession,
    outbox: outbox,
  );

  // ── Analytics client ──
  final analyticsApiClient = AnalyticsApiClient(
    baseUrl: apiBaseUrl,
    readAccessToken: readAccessToken,
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
    outbox: outbox,
  );

  final voiceAssistantModule = VoiceAssistantModule.create(
    baseUrl: apiBaseUrl,
    tokenStorage: tokenStorage,
    refreshSession: refreshSession,
  );
  final configurationModule = LaJuanaConfigurationModule(
    ConfigurationApiClient(
      baseUrl: apiBaseUrl,
      readAccessToken: readAccessToken,
      refreshSession: refreshSession,
    ),
    reservationsRepository: reservationsModule.repository,
  );

  final notificationsModule = NotificationsModule.create(
    baseUrl: apiBaseUrl,
    tokenStorage: tokenStorage,
    refreshSession: refreshSession,
    outbox: outbox,
  );

  final usersModule = UsersModule.create(
    baseUrl: apiBaseUrl,
    tokenStorage: tokenStorage,
    refreshSession: refreshSession,
  );

  return AppDependencies(
    authController: authController,
    apiClient: apiClient,
    analyticsApiClient: analyticsApiClient,
    catalogsModule: catalogsModule,
    reservationsModule: reservationsModule,
    saddlesModule: saddlesModule,
    providersModule: providersModule,
    assignmentsModule: assignmentsModule,
    equineRepository: equineRepository,
    equineEventRepository: equineEventRepository,
    outbox: outbox,
    voiceAssistantModule: voiceAssistantModule,
    configurationModule: configurationModule,
    notificationsModule: notificationsModule,
    usersModule: usersModule,
  );
}
