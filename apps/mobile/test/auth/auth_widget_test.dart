import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mobile/app/widgets/app_button.dart';
import 'package:mobile/app/widgets/app_card.dart';
import 'package:mobile/app/theme/app_theme.dart';
import 'package:mobile/auth/application/bootstrap_session_use_case.dart';
import 'package:mobile/auth/application/change_password_use_case.dart';
import 'package:mobile/auth/application/enter_local_mode_use_case.dart';
import 'package:mobile/auth/application/get_current_local_session_use_case.dart';
import 'package:mobile/auth/application/logout_use_case.dart';
import 'package:mobile/auth/application/refresh_session_use_case.dart';
import 'package:mobile/auth/application/register_use_case.dart';
import 'package:mobile/auth/application/sign_in_use_case.dart';
import 'package:mobile/auth/domain/auth_enums.dart';
import 'package:mobile/auth/domain/auth_models.dart';
import 'package:mobile/auth/presentation/auth_controller.dart';
import 'package:mobile/auth/presentation/auth_routes.dart';
import 'package:mobile/auth/presentation/screens/login_screen.dart';
import 'package:mobile/auth/presentation/screens/register_screen.dart';
import 'package:mobile/auth/presentation/screens/session_gate_screen.dart';

import 'test_fakes.dart';

void main() {
  AuthController buildController(
    FakeAuthRepository repo,
    FakeConnectivityService connectivity,
  ) {
    return AuthController(
      bootstrapSessionUseCase: BootstrapSessionUseCase(repo),
      signInUseCase: SignInUseCase(repo),
      refreshSessionUseCase: RefreshSessionUseCase(repo),
      logoutUseCase: LogoutUseCase(repo),
      registerUseCase: RegisterUseCase(repo),
      changePasswordUseCase: ChangePasswordUseCase(repo),
      getCurrentLocalSessionUseCase: GetCurrentLocalSessionUseCase(repo),
      enterLocalModeUseCase: EnterLocalModeUseCase(repo),
      connectivityService: connectivity,
    );
  }

  testWidgets('SessionGate decide login when signed_out', (tester) async {
    final repo = FakeAuthRepository()
      ..bootstrapResult = AuthSessionSnapshot(
        authState: LocalAuthState.signedOut,
        currentUser: null,
        hasLocalSession: false,
        hasPendingSync: false,
        isOfflineRestricted: false,
      );
    final connectivity = FakeConnectivityService(ConnectivityState.online);
    final controller = buildController(repo, connectivity);

    await tester.pumpWidget(
      MaterialApp(
        theme: AppTheme.dark(),
        routes: {
          AuthRoutes.login: (_) => const Scaffold(body: Text('login-screen')),
          AuthRoutes.home: (_) => const Scaffold(body: Text('home-screen')),
        },
        home: SessionGateScreen(controller: controller),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.text('login-screen'), findsOneWidget);
    await connectivity.dispose();
    controller.dispose();
  });

  testWidgets('Login deshabilita submit con formulario incompleto', (
    tester,
  ) async {
    final repo = FakeAuthRepository();
    final connectivity = FakeConnectivityService(ConnectivityState.online);
    final controller = buildController(repo, connectivity);

    await tester.pumpWidget(
      MaterialApp(
        theme: AppTheme.dark(),
        routes: {
          AuthRoutes.home: (_) => const Scaffold(body: Text('home-screen')),
        },
        home: LoginScreen(controller: controller),
      ),
    );
    await tester.pump();

    final loginButton = tester.widget<AppButton>(
      find.widgetWithText(AppButton, 'INICIAR SESION'),
    );
    expect(loginButton.onPressed, isNull);
    expect(find.byType(AppCard), findsNothing);
    expect(find.text('Acceso operativo'), findsNothing);
    expect(find.text('Sesion verificada'), findsNothing);
    expect(repo.lastConnectivity, isNull);

    await connectivity.dispose();
    controller.dispose();
  });

  testWidgets('Login centra logo y titulo con logo arriba', (tester) async {
    final repo = FakeAuthRepository();
    final connectivity = FakeConnectivityService(ConnectivityState.online);
    final controller = buildController(repo, connectivity);

    await tester.pumpWidget(
      MaterialApp(
        theme: AppTheme.dark(),
        routes: {
          AuthRoutes.home: (_) => const Scaffold(body: Text('home-screen')),
        },
        home: LoginScreen(controller: controller),
      ),
    );
    await tester.pump();

    final logoFinder = find.byKey(const Key('login_logo'));
    final titleFinder = find.byKey(const Key('login_title'));
    expect(logoFinder, findsOneWidget);
    expect(titleFinder, findsOneWidget);

    final scaffoldFinder = find.byType(Scaffold);
    final screenWidth = tester.getSize(scaffoldFinder).width;
    final screenCenterX = screenWidth / 2;
    final logoCenter = tester.getCenter(logoFinder);
    final titleCenter = tester.getCenter(titleFinder);
    final logoTop = tester.getTopLeft(logoFinder).dy;
    final titleTop = tester.getTopLeft(titleFinder).dy;

    expect((logoCenter.dx - screenCenterX).abs(), lessThan(2));
    expect((titleCenter.dx - screenCenterX).abs(), lessThan(2));
    expect(logoTop, lessThan(titleTop));
    expect(find.text('Iniciar sesion'), findsOneWidget);

    await connectivity.dispose();
    controller.dispose();
  });

  testWidgets('Login mantiene boton de sesion local cuando hay sesion local', (
    tester,
  ) async {
    final repo = FakeAuthRepository();
    final connectivity = FakeConnectivityService(ConnectivityState.online);
    final controller = buildController(repo, connectivity);
    controller.hasLocalSession = true;

    await tester.pumpWidget(
      MaterialApp(
        theme: AppTheme.dark(),
        routes: {
          AuthRoutes.home: (_) => const Scaffold(body: Text('home-screen')),
        },
        home: LoginScreen(controller: controller),
      ),
    );
    await tester.pump();

    expect(
      find.widgetWithText(AppButton, 'CONTINUAR CON SESION LOCAL'),
      findsOneWidget,
    );

    await connectivity.dispose();
    controller.dispose();
  });

  testWidgets('Login muestra link de registro y navega a registro', (
    tester,
  ) async {
    final repo = FakeAuthRepository();
    final connectivity = FakeConnectivityService(ConnectivityState.online);
    final controller = buildController(repo, connectivity);

    await tester.pumpWidget(
      MaterialApp(
        theme: AppTheme.dark(),
        routes: {
          AuthRoutes.home: (_) => const Scaffold(body: Text('home-screen')),
          AuthRoutes.register: (_) =>
              const Scaffold(body: Text('register-screen')),
        },
        home: LoginScreen(controller: controller),
      ),
    );
    await tester.pump();

    expect(find.byKey(const Key('login_register_link')), findsOneWidget);
    expect(find.text('No tienes cuenta?'), findsOneWidget);
    expect(find.text('Registrate'), findsOneWidget);
    await tester.tap(find.text('Registrate'));
    await tester.pumpAndSettle();
    expect(find.text('register-screen'), findsOneWidget);

    await connectivity.dispose();
    controller.dispose();
  });

  testWidgets('Register usa layout sin card y sin badge de conectividad', (
    tester,
  ) async {
    final repo = FakeAuthRepository();
    final connectivity = FakeConnectivityService(ConnectivityState.online);
    final controller = buildController(repo, connectivity);

    await tester.pumpWidget(
      MaterialApp(
        theme: AppTheme.dark(),
        routes: {
          AuthRoutes.login: (_) => const Scaffold(body: Text('login-screen')),
        },
        home: RegisterScreen(controller: controller),
      ),
    );
    await tester.pump();

    expect(find.byType(AppCard), findsNothing);
    expect(find.text('Cuenta de acceso'), findsNothing);
    expect(find.text('Sesion verificada'), findsNothing);
    expect(find.text('Registro'), findsOneWidget);

    await connectivity.dispose();
    controller.dispose();
  });

  testWidgets('Register centra logo y titulo con logo arriba', (tester) async {
    final repo = FakeAuthRepository();
    final connectivity = FakeConnectivityService(ConnectivityState.online);
    final controller = buildController(repo, connectivity);

    await tester.pumpWidget(
      MaterialApp(
        theme: AppTheme.dark(),
        routes: {
          AuthRoutes.login: (_) => const Scaffold(body: Text('login-screen')),
        },
        home: RegisterScreen(controller: controller),
      ),
    );
    await tester.pump();

    final logoFinder = find.byKey(const Key('register_logo'));
    final titleFinder = find.byKey(const Key('register_title'));
    expect(logoFinder, findsOneWidget);
    expect(titleFinder, findsOneWidget);

    final scaffoldFinder = find.byType(Scaffold);
    final screenWidth = tester.getSize(scaffoldFinder).width;
    final screenCenterX = screenWidth / 2;
    final logoCenter = tester.getCenter(logoFinder);
    final titleCenter = tester.getCenter(titleFinder);
    final logoTop = tester.getTopLeft(logoFinder).dy;
    final titleTop = tester.getTopLeft(titleFinder).dy;

    expect((logoCenter.dx - screenCenterX).abs(), lessThan(2));
    expect((titleCenter.dx - screenCenterX).abs(), lessThan(2));
    expect(logoTop, lessThan(titleTop));

    await connectivity.dispose();
    controller.dispose();
  });

  testWidgets('Register muestra link de login y navega', (tester) async {
    final repo = FakeAuthRepository();
    final connectivity = FakeConnectivityService(ConnectivityState.online);
    final controller = buildController(repo, connectivity);

    await tester.pumpWidget(
      MaterialApp(
        theme: AppTheme.dark(),
        routes: {
          AuthRoutes.login: (_) => const Scaffold(body: Text('login-screen')),
        },
        home: RegisterScreen(controller: controller),
      ),
    );
    await tester.pump();

    expect(find.byKey(const Key('register_login_link')), findsOneWidget);
    expect(find.text('Ya tienes cuenta?'), findsOneWidget);
    expect(find.text('Inicia sesion'), findsOneWidget);

    await tester.ensureVisible(find.text('Inicia sesion'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Inicia sesion'));
    await tester.pumpAndSettle();
    expect(find.text('login-screen'), findsOneWidget);

    await connectivity.dispose();
    controller.dispose();
  });

  testWidgets('Login muestra loader durante envío', (tester) async {
    final repo = FakeAuthRepository()
      ..signInDelay = const Duration(milliseconds: 400);
    final connectivity = FakeConnectivityService(ConnectivityState.online);
    final controller = buildController(repo, connectivity);

    await tester.pumpWidget(
      MaterialApp(
        theme: AppTheme.dark(),
        routes: {
          AuthRoutes.home: (_) => const Scaffold(body: Text('home-screen')),
        },
        home: LoginScreen(controller: controller),
      ),
    );

    final future = controller.loginSubmitted(
      email: 'user@x.com',
      password: 'password123',
    );
    await tester.pump();

    expect(find.widgetWithText(AppButton, 'INGRESANDO...'), findsOneWidget);
    await tester.pump(const Duration(milliseconds: 500));
    await future;
    await tester.pump();

    await connectivity.dispose();
    controller.dispose();
  });

  testWidgets('Register respeta política de volver a login con éxito', (
    tester,
  ) async {
    final repo = FakeAuthRepository();
    final connectivity = FakeConnectivityService(ConnectivityState.online);
    final controller = buildController(repo, connectivity);

    await tester.pumpWidget(
      MaterialApp(
        theme: AppTheme.dark(),
        routes: {
          AuthRoutes.login: (_) => const Scaffold(body: Text('login-screen')),
        },
        home: RegisterScreen(controller: controller),
      ),
    );

    await tester.enterText(find.byType(TextField).at(0), 'Nombre');
    await tester.enterText(find.byType(TextField).at(1), 'user@x.com');
    await tester.enterText(find.byType(TextField).at(2), 'password123');
    await tester.enterText(find.byType(TextField).at(3), 'password123');

    await controller.registerSubmitted(
      fullName: 'Nombre',
      email: 'user@x.com',
      password: 'password123',
    );
    await tester.pumpAndSettle();

    expect(find.text('login-screen'), findsOneWidget);

    await connectivity.dispose();
    controller.dispose();
  });

  testWidgets('Login muestra mensaje de error y no el code', (tester) async {
    final repo = FakeAuthRepository()
      ..signInFailure = AuthFailure(
        code: 'auth.password_missmatch',
        message: 'La contraseña actual no es válida.',
        statusCode: 400,
      );
    final connectivity = FakeConnectivityService(ConnectivityState.online);
    final controller = buildController(repo, connectivity);

    await tester.pumpWidget(
      MaterialApp(
        theme: AppTheme.dark(),
        routes: {
          AuthRoutes.home: (_) => const Scaffold(body: Text('home-screen')),
        },
        home: LoginScreen(controller: controller),
      ),
    );

    await controller.loginSubmitted(email: 'user@x.com', password: 'bad');
    await tester.pumpAndSettle();

    expect(find.text('La contraseña actual no es válida.'), findsOneWidget);
    expect(find.text('auth.password_missmatch'), findsNothing);

    await connectivity.dispose();
    controller.dispose();
  });
}
