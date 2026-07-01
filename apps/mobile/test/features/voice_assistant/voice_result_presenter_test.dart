import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mobile/features/voice_assistant/presentation/helpers/voice_date_format.dart';
import 'package:mobile/features/voice_assistant/presentation/helpers/voice_display_labels.dart';
import 'package:mobile/features/voice_assistant/presentation/navigation/voice_assistant_navigation.dart';
import 'package:mobile/features/voice_assistant/presentation/widgets/voice_result_presenter.dart';
import 'package:mobile/features/auth/presentation/auth_controller.dart';
import 'package:mobile/features/auth/infrastructure/connectivity/network_models.dart';
import 'package:mobile/features/auth/infrastructure/connectivity/network_status_resolver.dart';
import 'package:mobile_domain/src/equines/equine_event_repository.dart';
import 'package:mobile_domain/src/equines/equine_repository.dart';

import '../../auth/test_fakes.dart';

class _FakeEquineRepository implements EquineRepository {
  @override
  dynamic noSuchMethod(Invocation invocation) => super.noSuchMethod(invocation);
}

class _FakeEquineEventRepository implements EquineEventRepository {
  @override
  dynamic noSuchMethod(Invocation invocation) => super.noSuchMethod(invocation);
}

VoiceAssistantNavigation _buildNavigation() {
  final networkStatusResolver = NetworkStatusResolver(
    connectivityService: FakeConnectivityService(LinkType.wifi),
    backendReachabilityService: FakeBackendReachabilityService(
      BackendReachability.reachable,
    ),
  );
  return VoiceAssistantNavigation(
    authController: AuthController(
      authRepository: FakeAuthRepository(),
      networkStatusResolver: networkStatusResolver,
    ),
    equineRepository: _FakeEquineRepository(),
    equineEventRepository: _FakeEquineEventRepository(),
  );
}

void main() {
  late VoiceAssistantNavigation navigation;
  late BuildContext hostContext;

  setUpAll(() {
    TestWidgetsFlutterBinding.ensureInitialized();
  });

  setUp(() {
    navigation = _buildNavigation();
  });

  testWidgets('admin_list_reservations produces Spanish summary and row',
      (tester) async {
    await tester.pumpWidget(
      MaterialApp(
        home: Builder(
          builder: (context) {
            hostContext = context;
            return const SizedBox.shrink();
          },
        ),
      ),
    );

    final structured = VoiceResultPresenter.present(
      toolName: 'admin_list_reservations',
      toolOutput: {
        'total': 1,
        'reservations': [
          {
            'reservation_id': 'abc123',
            'code': 'TEST-WHATSAPP',
            'status': 'payment_received',
            'experience_name': 'Cabalgata Basica',
            'holder_name': 'Juan Perez',
            'requested_date': '2026-07-05',
            'participant_count': 2,
            'payment_status': 'received',
            'experience_id': 'exp1',
          },
        ],
      },
      navigation: navigation,
      hostContext: hostContext,
      closeSheet: () {},
    );

    expect(structured, isNotNull);
    expect(structured!.summary, '1 reserva encontrado.');
    expect(structured.items, hasLength(1));
    expect(structured.items.first.title, 'Cabalgata Basica');
    expect(structured.items.first.statusLabel, 'Pago recibido');
    expect(structured.items.first.subtitle, contains('5 jul 2026'));
    expect(structured.items.first.onTap, isNotNull);
  });

  test('admin_list_users is read-only', () {
    final structured = VoiceResultPresenter.present(
      toolName: 'admin_list_users',
      toolOutput: {
        'total': 1,
        'users': [
          {
            'user_id': 'u1',
            'full_name': 'Admin User',
            'email': 'admin@lajuana.co',
            'role': 'admin',
            'is_active': true,
          },
        ],
      },
      navigation: navigation,
      hostContext: _DummyContext(),
      closeSheet: () {},
    );

    expect(structured!.items.first.statusLabel, 'Administrador');
    expect(structured.items.first.onTap, isNull);
  });

  test('unknown tool returns null', () {
    final structured = VoiceResultPresenter.present(
      toolName: 'admin_unknown_tool',
      toolOutput: const {},
      navigation: navigation,
      hostContext: _DummyContext(),
      closeSheet: () {},
    );
    expect(structured, isNull);
  });

  group('voice_date_format', () {
    test('formatVoiceDate parses ISO date', () {
      expect(formatVoiceDate('2026-07-05'), '5 jul 2026');
    });
  });

  group('voice_display_labels', () {
    test('voiceReservationStatusLabel maps snake_case', () {
      expect(
        voiceReservationStatusLabel('payment_received'),
        'Pago recibido',
      );
    });
  });
}

class _DummyContext extends Fake implements BuildContext {}
