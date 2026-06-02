import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';

import '../features/auth/domain/auth_enums.dart';
import '../features/auth/infrastructure/connectivity/backend_reachability_service.dart';
import '../features/auth/infrastructure/connectivity/connectivity_service.dart';
import '../features/auth/infrastructure/connectivity/network_status_resolver.dart';
import '../features/auth/infrastructure/local/auth_database.dart';
import '../features/auth/infrastructure/repositories/auth_repository_impl.dart';
import '../features/auth/infrastructure/local/session_local_data_source.dart';
import '../features/auth/infrastructure/local/user_local_data_source.dart';
import '../features/auth/infrastructure/remote/auth_api_client.dart';
import '../features/auth/infrastructure/token_storage.dart';
import '../features/auth/presentation/auth_controller.dart';
import '../features/auth/presentation/auth_routes.dart';
import '../features/auth/presentation/screens/change_password_screen.dart';
import '../features/auth/presentation/screens/login_screen.dart';
import '../features/auth/presentation/screens/register_screen.dart';
import '../features/auth/presentation/screens/session_view_screen.dart';
import '../features/catalogs/catalogs.dart';
import '../features/equines/domain/repositories/equine_repository.dart';
import '../features/equines/infrastructure/local/equines_database.dart';
import '../features/equines/infrastructure/remote/equines_api_client.dart';
import '../features/equines/infrastructure/repositories/equine_repository_impl.dart';
import '../features/reservations/reservations_module.dart';
import 'bootstrap/dev_loader_screen.dart';
import 'bootstrap/startup_gate.dart';
import '../playground/widget_museum_screen.dart';
import 'shell/authenticated_shell.dart';
import 'theme/app_theme.dart';
import 'theme/app_theme_notifier.dart';

class LaJuanaApp extends StatefulWidget {
  const LaJuanaApp({super.key, required this.apiBaseUrl});

  final String apiBaseUrl;

  @override
  State<LaJuanaApp> createState() => _LaJuanaAppState();
}

class _LaJuanaAppState extends State<LaJuanaApp> {
  ThemeMode _themeMode = ThemeMode.dark;
  Color _themeVeilColor = const Color(0xFF131313);
  bool _isThemeTransitioning = false;
  static const Duration _themeTransitionDuration = Duration(milliseconds: 320);
  static const Duration _themeVeilVisibleDuration = Duration(milliseconds: 500);
  static const Duration _themeVeilFadeDuration = Duration(milliseconds: 180);
  static const double _themeVeilOpacity = 1.0;

  /// Dev/playground screens resolver — lazy loaded to avoid shipping in release.
  Widget Function(String routeName)? _devScreenResolver;

  late final AuthController _authController;
  late final AuthApiClient _apiClient;
  late final CatalogsModule _catalogsModule;
  late final ReservationsModule _reservationsModule;
  late final EquineRepository _equineRepository;

  @override
  void initState() {
    super.initState();
    _apiClient = AuthApiClient(baseUrl: widget.apiBaseUrl);
    final database = AuthDatabase.instance;
    final sessionDs = SessionLocalDataSource(database);
    final userDs = UserLocalDataSource(database);
    final repository = AuthRepositoryImpl(
      apiClient: _apiClient,
      sessionLocalDataSource: sessionDs,
      userLocalDataSource: userDs,
    );

    final connectivityService = ConnectivityPlusService();
    final reachabilityService = HttpBackendReachabilityService(
      baseUrl: widget.apiBaseUrl,
    );
    final networkStatusResolver = NetworkStatusResolver(
      connectivityService: connectivityService,
      backendReachabilityService: reachabilityService,
    );

    _authController = AuthController(
      authRepository: repository,
      networkStatusResolver: networkStatusResolver,
    );

    final catalogsApi = CatalogsSyncApi(
      baseUrl: widget.apiBaseUrl,
      readAccessToken: () async =>
          (await sessionDs.getCurrentSession())?.accessToken,
      refreshSession: () async {
        await _authController.refreshRequested();
        return _authController.authState == LocalAuthState.signedInVerified;
      },
    );
    final catalogsRepository = CatalogsRepository(
      database: CatalogsDatabase.instance,
      api: catalogsApi,
    );
    _catalogsModule = CatalogsModule(catalogsRepository);

    _reservationsModule = ReservationsModule.create(
      baseUrl: widget.apiBaseUrl,
      tokenStorage: SqliteTokenStorage(sessionDs),
      refreshSession: () async {
        await _authController.refreshRequested();
        return _authController.authState == LocalAuthState.signedInVerified;
      },
    );

    final equinesApiClient = EquinesApiClient(
      baseUrl: widget.apiBaseUrl,
      readAccessToken: () async =>
          (await sessionDs.getCurrentSession())?.accessToken,
      refreshSession: () async {
        await _authController.refreshRequested();
        return _authController.authState == LocalAuthState.signedInVerified;
      },
    );
    _equineRepository = EquineRepositoryImpl(
      apiClient: equinesApiClient,
      database: EquinesDatabase.instance,
    );

    if (!kReleaseMode) {
      _initDevScreenResolver();
    }
  }

  void _initDevScreenResolver() {
    _devScreenResolver = (String routeName) {
      // Deferred import pattern — dev screens only in non-release builds
      switch (routeName) {
        case AuthRoutes.devLoader:
          return const DevWidgetCatalogScreen();
        case AuthRoutes.widgetMuseum:
          return const WidgetMuseumScreen();
        default:
          return _PlaceholderWidget('Unknown dev route: $routeName');
      }
    };
  }

  Widget _resolveDevScreen(String routeName) {
    final resolver = _devScreenResolver;
    if (resolver != null) return resolver(routeName);
    return StartupGate(controller: _authController);
  }

  @override
  void dispose() {
    _authController.dispose();
    _reservationsModule.listController.dispose();
    super.dispose();
  }

  Future<void> _toggleTheme() async {
    if (_isThemeTransitioning) return;

    final nextMode = _themeMode == ThemeMode.dark
        ? ThemeMode.light
        : ThemeMode.dark;

    setState(() {
      _isThemeTransitioning = true;
      _themeVeilColor = nextMode == ThemeMode.light
          ? Colors.white
          : const Color(0xFF131313);
    });

    await Future<void>.delayed(_themeVeilFadeDuration);
    if (!mounted) return;

    setState(() {
      _themeMode = nextMode;
    });

    await Future<void>.delayed(_themeVeilVisibleDuration);
    if (!mounted) return;

    setState(() {
      _isThemeTransitioning = false;
    });
  }

  bool _isAuthenticated(LocalAuthState state) {
    return state == LocalAuthState.signedInVerified ||
        state == LocalAuthState.signedInLocalUnverified;
  }

  Route<dynamic> _buildRoute(RouteSettings settings) {
    final routeName = settings.name ?? AuthRoutes.sessionGate;
    final canAccessAuthenticated = _isAuthenticated(_authController.authState);
    late final Widget screen;

    switch (routeName) {
      case AuthRoutes.devLoader:
      case AuthRoutes.widgetMuseum:
        // Dev routes: block in release builds, lazy-load in debug
        if (kReleaseMode) {
          screen = StartupGate(controller: _authController);
        } else {
          screen = _resolveDevScreen(routeName);
        }
        break;
      case AuthRoutes.sessionGate:
        screen = StartupGate(controller: _authController);
        break;
      case AuthRoutes.login:
        screen = LoginScreen(controller: _authController);
        break;
      case AuthRoutes.register:
        screen = RegisterScreen(controller: _authController);
        break;
      case AuthRoutes.home:
        screen = canAccessAuthenticated
            ? AuthenticatedShell(
                authController: _authController,
                contactsApiClient: _apiClient,
                catalogsModule: _catalogsModule,
                reservationsModule: _reservationsModule,
                equineRepository: _equineRepository,
              )
            : LoginScreen(controller: _authController);
        break;
      case AuthRoutes.sessionView:
        screen = canAccessAuthenticated
            ? SessionViewScreen(controller: _authController)
            : LoginScreen(controller: _authController);
        break;
      case AuthRoutes.changePassword:
        screen = canAccessAuthenticated
            ? ChangePasswordScreen(controller: _authController)
            : LoginScreen(controller: _authController);
        break;
      default:
        screen = StartupGate(controller: _authController);
    }

    return MaterialPageRoute<void>(builder: (_) => screen, settings: settings);
  }

  @override
  Widget build(BuildContext context) {
    return AppThemeNotifier(
      onToggle: _toggleTheme,
      child: MaterialApp(
        title: 'La Juana',
        debugShowCheckedModeBanner: false,
        theme: AppTheme.light(),
        darkTheme: AppTheme.dark(),
        themeMode: _themeMode,
        initialRoute: AuthRoutes.sessionGate,
        onGenerateRoute: _buildRoute,
        themeAnimationDuration: _themeTransitionDuration,
        themeAnimationCurve: Curves.easeInOutCubicEmphasized,
        builder: (context, child) {
          final content = child ?? const SizedBox.shrink();
          return Stack(
            fit: StackFit.expand,
            children: [
              content,
              IgnorePointer(
                ignoring: true,
                child: AnimatedOpacity(
                  opacity: _isThemeTransitioning ? _themeVeilOpacity : 0,
                  duration: _themeVeilFadeDuration,
                  curve: Curves.easeOutCubic,
                  child: ColoredBox(color: _themeVeilColor),
                ),
              ),
            ],
          );
        },
      ),
    );
  }
}

/// Fallback widget when a dev screen is not available (release mode).
class _PlaceholderWidget extends StatelessWidget {
  const _PlaceholderWidget(this.message);
  final String message;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Dev Tools')),
      body: Center(child: Text(message)),
    );
  }
}
