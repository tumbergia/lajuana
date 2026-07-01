import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:mobile/app/shell/authenticated_shell.dart';
import 'package:mobile_ui/src/theme/app_theme.dart';
import 'package:mobile_ui/src/widgets/app_button.dart';
import 'package:mobile/features/auth/domain/auth_enums.dart';
import 'package:mobile/features/auth/infrastructure/connectivity/network_models.dart';
import 'package:mobile/features/auth/infrastructure/connectivity/network_status_resolver.dart';
import 'package:mobile/features/auth/infrastructure/remote/auth_api_client.dart';
import 'package:mobile/features/auth/presentation/auth_controller.dart';
import 'package:mobile/features/voice_assistant/infrastructure/remote/voice_assistant_api_client.dart';
import 'package:mobile/features/voice_assistant/presentation/controllers/voice_assistant_controller.dart';
import 'package:mobile/features/voice_assistant/voice_assistant_module.dart';
import 'package:mobile_domain/src/equines/equine.dart';
import 'package:mobile_domain/src/equines/equine_event.dart';
import 'package:mobile_domain/src/equines/equine_event_repository.dart';
import 'package:mobile_domain/src/equines/equine_timeline_entry.dart';
import 'package:mobile_domain/src/equines/equine_repository.dart';

import '../auth/test_fakes.dart';

/// Stub mínimo para [EquineRepository] usado en tests del shell.
class _FakeEquineRepository implements EquineRepository {
  @override
  Future<List<Equine>> listEquines({
    String? operationalStatus,
    bool includeDeleted = false,
  }) async => [];

  @override
  Future<Equine> getEquineById(String equineId) async =>
      throw UnimplementedError('not used in shell test');

  @override
  Future<Equine> createEquine(Map<String, dynamic> data) async =>
      throw UnimplementedError('not used in shell test');

  @override
  Future<Equine> updateEquine(String equineId, Map<String, dynamic> data) async =>
      throw UnimplementedError('not used in shell test');

  @override
  Future<List<EquineTimelineEntry>> getEquineTimeline(String equineId) async => [];

  @override
  Future<List<Equine>> listAvailableForReservation(String reservationId) async => [];

  @override
  Future<Equine> deleteEquine(String equineId) async =>
      throw UnimplementedError('not used in shell test');

  @override
  Future<Equine> restoreEquine(String equineId) async =>
      throw UnimplementedError('not used in shell test');

  @override
  Future<DateTime?> getLastSyncedAt() async => null;
}

class _FakeEquineEventRepository implements EquineEventRepository {
  @override
  Future<EquineEvent> createEvent(
    String equineId,
    EquineEventCreatePayload payload,
  ) async =>
      throw UnimplementedError('not used in shell test');

  @override
  Future<int> flushPendingEvents({String? equineId}) async => 0;

  @override
  Future<int> countPendingEvents(String equineId) async => 0;

  @override
  Future<List<EquineEvent>> listPendingEvents(String equineId) async => [];
}

VoiceAssistantModule _fakeVoiceAssistantModule() {
  final apiClient = VoiceAssistantApiClient(
    baseUrl: 'http://test.local/api/v1',
    readAccessToken: () async => 'token',
    refreshSession: () async => true,
    httpClient: MockClient((_) async => http.Response('{}', 404)),
  );
  return VoiceAssistantModule(
    apiClient: apiClient,
    controller: VoiceAssistantController(apiClient: apiClient),
  );
}

void main() {
  AuthController buildController(
    FakeAuthRepository repo,
    FakeConnectivityService connectivity,
  ) {
    final networkStatusResolver = NetworkStatusResolver(
      connectivityService: connectivity,
      backendReachabilityService: FakeBackendReachabilityService(
        BackendReachability.reachable,
      ),
    );
    return AuthController(
      authRepository: repo,
      networkStatusResolver: networkStatusResolver,
    );
  }

  AuthApiClient buildContactsApiClient() {
    final mockClient = MockClient((request) async {
      if (request.url.path.endsWith('/config/emergency-contacts')) {
        return http.Response(
          jsonEncode({
            'items': [
              {
                'code': 'national_emergency',
                'name': 'Linea unica de emergencias',
                'description': 'Atencion nacional 24/7',
                'phone_number': '123',
                'category': 'security',
                'is_primary': true,
                'is_national': true,
              },
            ],
          }),
          200,
          headers: {'content-type': 'application/json'},
        );
      }
      return http.Response('Not found', 404);
    });

    return AuthApiClient(
      httpClient: mockClient,
      baseUrl: 'http://test.local/api/v1',
    );
  }

  testWidgets('Authenticated shell no renderiza FAB de sesion', (tester) async {
    final repo = FakeAuthRepository();
    final connectivity = FakeConnectivityService(LinkType.wifi);
    final controller = buildController(repo, connectivity)
      ..networkStatus = const NetworkStatus(
        linkType: LinkType.wifi,
        backendReachability: BackendReachability.reachable,
      );

    await tester.pumpWidget(
      MaterialApp(
        theme: AppTheme.dark(),
        home: AuthenticatedShell(
          authController: controller,
          contactsApiClient: buildContactsApiClient(),
          equineRepository: _FakeEquineRepository(),
          equineEventRepository: _FakeEquineEventRepository(),
          voiceAssistantModule: _fakeVoiceAssistantModule(),
        ),
      ),
    );
    await tester.pump();

    expect(find.byType(FloatingActionButton), findsNothing);

    await connectivity.dispose();
    controller.dispose();
  });

  testWidgets('Mas muestra opciones y ruta al navegar a vistas', (
    tester,
  ) async {
    final repo = FakeAuthRepository();
    final connectivity = FakeConnectivityService(LinkType.wifi);
    final controller = buildController(repo, connectivity)
      ..networkStatus = const NetworkStatus(
        linkType: LinkType.wifi,
        backendReachability: BackendReachability.reachable,
      );

    String? calledPhone;
    await tester.pumpWidget(
      MaterialApp(
        theme: AppTheme.dark(),
        home: AuthenticatedShell(
          authController: controller,
          contactsApiClient: buildContactsApiClient(),
          equineRepository: _FakeEquineRepository(),
          equineEventRepository: _FakeEquineEventRepository(),
          voiceAssistantModule: _fakeVoiceAssistantModule(),
          onCallRequested: (phone) async {
            calledPhone = phone;
            return true;
          },
        ),
      ),
    );
    await tester.pump();

    await tester.tap(find.byIcon(Icons.menu_rounded));
    await tester.pumpAndSettle();

    expect(find.text('PERFIL'), findsOneWidget);
    expect(find.text('CONTACTOS'), findsOneWidget);
    expect(find.text('OPCIONES ADICIONALES'), findsOneWidget);

    await tester.tap(find.text('PERFIL'));
    await tester.pumpAndSettle();

    expect(find.text('MAS'), findsWidgets);
    expect(find.text('PERFIL'), findsWidgets);
    expect(find.text('CAMBIAR CONTRASENA'), findsOneWidget);

    await tester.ensureVisible(find.text('VOLVER'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('VOLVER'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('CONTACTOS'));
    await tester.pumpAndSettle();

    expect(find.text('MAS'), findsWidgets);
    expect(find.text('CONTACTOS'), findsWidgets);
    expect(find.text('LINEA UNICA DE EMERGENCIAS'), findsOneWidget);
    expect(find.text('ATENCION NACIONAL 24/7'), findsOneWidget);
    expect(find.textContaining('TEL:'), findsNothing);

    await tester.tap(find.text('LINEA UNICA DE EMERGENCIAS'));
    await tester.pumpAndSettle();
    expect(calledPhone, '123');

    await connectivity.dispose();
    controller.dispose();
  });

  testWidgets('Perfil abre formulario y permite cambiar contrasena', (
    tester,
  ) async {
    final repo = FakeAuthRepository();
    final connectivity = FakeConnectivityService(LinkType.wifi);
    final controller = buildController(repo, connectivity)
      ..networkStatus = const NetworkStatus(
        linkType: LinkType.wifi,
        backendReachability: BackendReachability.reachable,
      );

    await tester.pumpWidget(
      MaterialApp(
        theme: AppTheme.dark(),
        home: AuthenticatedShell(
          authController: controller,
          contactsApiClient: buildContactsApiClient(),
          equineRepository: _FakeEquineRepository(),
          equineEventRepository: _FakeEquineEventRepository(),
          voiceAssistantModule: _fakeVoiceAssistantModule(),
        ),
      ),
    );
    await tester.pump();

    await tester.tap(find.byIcon(Icons.menu_rounded));
    await tester.pumpAndSettle();
    await tester.tap(find.text('PERFIL'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('CAMBIAR CONTRASENA'));
    await tester.pumpAndSettle();

    expect(find.text('MAS > PERFIL'), findsOneWidget);
    expect(find.text('CAMBIAR CONTRASENA'), findsOneWidget);

    final fields = find.byType(TextField);
    expect(fields, findsNWidgets(3));
    await tester.enterText(fields.at(0), 'Nueva1234');
    await tester.enterText(fields.at(1), 'Nueva1234');
    await tester.enterText(fields.at(2), 'Nueva1234');
    await tester.pumpAndSettle();

    final saveButtonFinder = find.byWidgetPredicate(
      (widget) => widget is AppButton && widget.label == 'Guardar',
    );
    expect(saveButtonFinder, findsOneWidget);
    final saveButton = tester.widget<AppButton>(saveButtonFinder);
    expect(saveButton.onPressed, isNotNull);
    saveButton.onPressed!.call();
    await tester.pumpAndSettle();

    expect(repo.didChangePassword, isTrue);

    await connectivity.dispose();
    controller.dispose();
  });

  testWidgets('Muestra overlay de reconexion durante refresh', (tester) async {
    final repo = FakeAuthRepository();
    final connectivity = FakeConnectivityService(LinkType.wifi);
    final controller = buildController(repo, connectivity)
      ..authState = LocalAuthState.signedInLocalUnverified
      ..networkStatus = const NetworkStatus(
        linkType: LinkType.wifi,
        backendReachability: BackendReachability.reachable,
      )
      ..isLoading = true;

    await tester.pumpWidget(
      MaterialApp(
        theme: AppTheme.dark(),
        home: AuthenticatedShell(
          authController: controller,
          contactsApiClient: buildContactsApiClient(),
          equineRepository: _FakeEquineRepository(),
          equineEventRepository: _FakeEquineEventRepository(),
          voiceAssistantModule: _fakeVoiceAssistantModule(),
        ),
      ),
    );
    await tester.pump();

    expect(find.text('Reconectando sesion...'), findsOneWidget);
    expect(find.byType(CircularProgressIndicator), findsWidgets);

    await connectivity.dispose();
    controller.dispose();
  });

  testWidgets('Reservas tab renderiza bottom nav', (tester) async {
    final repo = FakeAuthRepository();
    final connectivity = FakeConnectivityService(LinkType.wifi);
    final controller = buildController(repo, connectivity)
      ..networkStatus = const NetworkStatus(
        linkType: LinkType.wifi,
        backendReachability: BackendReachability.reachable,
      );

    await tester.pumpWidget(
      MaterialApp(
        theme: AppTheme.dark(),
        home: AuthenticatedShell(
          authController: controller,
          contactsApiClient: buildContactsApiClient(),
          equineRepository: _FakeEquineRepository(),
          equineEventRepository: _FakeEquineEventRepository(),
          voiceAssistantModule: _fakeVoiceAssistantModule(),
        ),
      ),
    );
    await tester.pump();

    // Bottom nav Reservas icon should be present
    final reservasIcon = find.byIcon(Icons.calendar_today_rounded);
    expect(reservasIcon, findsOneWidget);

    await connectivity.dispose();
    controller.dispose();
  });
}
