import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:mobile/features/auth/infrastructure/connectivity/network_models.dart';
import 'package:mobile/features/auth/infrastructure/connectivity/network_status_resolver.dart';
import 'package:mobile/features/auth/presentation/auth_controller.dart';
import 'package:mobile/features/voice_assistant/domain/assistant_ask_result.dart';
import 'package:mobile/features/voice_assistant/infrastructure/remote/voice_assistant_api_client.dart';
import 'package:mobile/features/voice_assistant/presentation/controllers/voice_assistant_controller.dart';
import 'package:mobile/features/voice_assistant/presentation/navigation/voice_assistant_navigation.dart';
import 'package:mobile/features/voice_assistant/presentation/widgets/admin_voice_sheet.dart';
import 'package:mobile_ui/src/theme/app_theme.dart';
import 'package:mobile_ui/src/widgets/app_text_field.dart';
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

void main() {
  testWidgets('AdminVoiceSheet hides input when answered and shows structured rows',
      (tester) async {
    final controller = VoiceAssistantController(
      apiClient: VoiceAssistantApiClient(
        baseUrl: 'http://localhost:8000/api/v1',
        readAccessToken: () async => 'token',
        refreshSession: () async => false,
        httpClient: MockClient((_) => Completer<http.Response>().future),
      ),
    );

    final navigation = VoiceAssistantNavigation(
      authController: AuthController(
        authRepository: FakeAuthRepository(),
        networkStatusResolver: NetworkStatusResolver(
          connectivityService: FakeConnectivityService(LinkType.wifi),
          backendReachabilityService: FakeBackendReachabilityService(
            BackendReachability.reachable,
          ),
        ),
      ),
      equineRepository: _FakeEquineRepository(),
      equineEventRepository: _FakeEquineEventRepository(),
    );

    await tester.pumpWidget(
      MaterialApp(
        theme: AppTheme.dark(),
        home: Builder(
          builder: (hostContext) {
            return AdminVoiceSheet(
              controller: controller,
              hostContext: hostContext,
              navigation: navigation,
              onClose: () {},
            );
          },
        ),
      ),
    );

    await tester.pump();

    controller.phase = VoicePhase.answered;
    controller.result = AssistantAskResult(
      traceId: 't1',
      action: 'tool_call',
      toolName: 'admin_list_reservations',
      response: 'Se ha encontrado 1 reserva payment_received',
      toolOutput: {
        'total': 1,
        'reservations': [
          {
            'reservation_id': 'abc',
            'code': 'R-1',
            'status': 'payment_received',
            'experience_name': 'Cabalgata Basica',
            'holder_name': 'Juan',
            'requested_date': '2026-07-05',
            'participant_count': 1,
            'payment_status': 'received',
            'experience_id': 'exp',
          },
        ],
      },
    );
    controller.notifyListeners();
    await tester.pumpAndSettle();

    expect(find.byType(AppTextField), findsNothing);
    expect(find.text('1 reserva encontrado.'), findsOneWidget);
    expect(find.text('CABALGATA BASICA'), findsOneWidget);
    expect(find.text('Pago recibido'), findsOneWidget);
    expect(
      find.textContaining('payment_received'),
      findsNothing,
    );

    controller.dispose();
  });
}
