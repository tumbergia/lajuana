import 'package:flutter/material.dart';

import '../auth/application/bootstrap_session_use_case.dart';
import '../auth/application/change_password_use_case.dart';
import '../auth/application/enter_local_mode_use_case.dart';
import '../auth/application/get_current_local_session_use_case.dart';
import '../auth/application/logout_use_case.dart';
import '../auth/application/refresh_session_use_case.dart';
import '../auth/application/register_use_case.dart';
import '../auth/application/sign_in_use_case.dart';
import '../auth/domain/auth_enums.dart';
import '../auth/infrastructure/auth_repository_impl.dart';
import '../auth/infrastructure/connectivity_service.dart';
import '../auth/infrastructure/local/auth_database.dart';
import '../auth/infrastructure/local/session_local_data_source.dart';
import '../auth/infrastructure/local/user_local_data_source.dart';
import '../auth/infrastructure/remote/auth_api_client.dart';
import '../auth/presentation/auth_controller.dart';
import '../auth/presentation/auth_routes.dart';
import '../auth/presentation/screens/authenticated_home_screen.dart';
import '../auth/presentation/screens/change_password_screen.dart';
import '../auth/presentation/screens/login_screen.dart';
import '../auth/presentation/screens/register_screen.dart';
import '../auth/presentation/screens/session_gate_screen.dart';
import '../auth/presentation/screens/session_view_screen.dart';
import 'theme/app_theme.dart';
import 'theme/app_theme_notifier.dart';

class LaJuanaApp extends StatefulWidget {
  const LaJuanaApp({super.key});

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

  @override
  void initState() {
    super.initState();
    final database = AuthDatabase.instance;
    final sessionDs = SessionLocalDataSource(database);
    final userDs = UserLocalDataSource(database);
    final repository = AuthRepositoryImpl(
      apiClient: AuthApiClient(),
      sessionLocalDataSource: sessionDs,
      userLocalDataSource: userDs,
    );

    _authController = AuthController(
      bootstrapSessionUseCase: BootstrapSessionUseCase(repository),
      signInUseCase: SignInUseCase(repository),
      refreshSessionUseCase: RefreshSessionUseCase(repository),
      logoutUseCase: LogoutUseCase(repository),
      registerUseCase: RegisterUseCase(repository),
      changePasswordUseCase: ChangePasswordUseCase(repository),
      getCurrentLocalSessionUseCase: GetCurrentLocalSessionUseCase(repository),
      enterLocalModeUseCase: EnterLocalModeUseCase(repository),
      connectivityService: ConnectivityPlusService(),
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
        screen = SessionGateScreen(controller: _authController);
        break;
      case AuthRoutes.login:
        screen = LoginScreen(controller: _authController);
        break;
      case AuthRoutes.register:
        screen = RegisterScreen(controller: _authController);
        break;
      case AuthRoutes.home:
        screen = canAccessAuthenticated
            ? AuthenticatedHomeScreen(controller: _authController)
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
        screen = SessionGateScreen(controller: _authController);
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
