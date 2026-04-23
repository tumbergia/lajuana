import 'package:flutter/material.dart';

import '../features/auth/application/bootstrap_session_use_case.dart';
import '../features/auth/application/change_password_use_case.dart';
import '../features/auth/application/enter_local_mode_use_case.dart';
import '../features/auth/application/get_current_local_session_use_case.dart';
import '../features/auth/application/logout_use_case.dart';
import '../features/auth/application/refresh_session_use_case.dart';
import '../features/auth/application/register_use_case.dart';
import '../features/auth/application/sign_in_use_case.dart';
import '../features/auth/application/sync_profile_from_remote_use_case.dart';
import '../features/auth/domain/auth_enums.dart';
import '../features/auth/infrastructure/connectivity/backend_reachability_service.dart';
import '../features/auth/infrastructure/connectivity/connectivity_service.dart';
import '../features/auth/infrastructure/connectivity/network_status_resolver.dart';
import '../features/auth/infrastructure/local/auth_database.dart';
import '../features/auth/infrastructure/repositories/auth_repository_impl.dart';
import '../features/auth/infrastructure/local/session_local_data_source.dart';
import '../features/auth/infrastructure/local/user_local_data_source.dart';
import '../features/auth/infrastructure/remote/auth_api_client.dart';
import '../features/auth/presentation/auth_controller.dart';
import '../features/auth/presentation/auth_routes.dart';
import '../features/auth/presentation/screens/change_password_screen.dart';
import '../features/auth/presentation/screens/login_screen.dart';
import '../features/auth/presentation/screens/register_screen.dart';
import '../features/auth/presentation/screens/session_view_screen.dart';
import 'bootstrap/startup_gate.dart';
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

  late final AuthController _authController;
  late final AuthApiClient _apiClient;

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
      bootstrapSessionUseCase: BootstrapSessionUseCase(repository),
      signInUseCase: SignInUseCase(repository),
      refreshSessionUseCase: RefreshSessionUseCase(repository),
      logoutUseCase: LogoutUseCase(repository),
      registerUseCase: RegisterUseCase(repository),
      changePasswordUseCase: ChangePasswordUseCase(repository),
      syncProfileFromRemoteUseCase: SyncProfileFromRemoteUseCase(repository),
      getCurrentLocalSessionUseCase: GetCurrentLocalSessionUseCase(repository),
      enterLocalModeUseCase: EnterLocalModeUseCase(repository),
      networkStatusResolver: networkStatusResolver,
    );
  }

  @override
  void dispose() {
    _authController.dispose();
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
