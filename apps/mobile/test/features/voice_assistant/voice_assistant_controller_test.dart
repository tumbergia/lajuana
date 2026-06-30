import 'dart:async';
import 'dart:convert';

import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:mobile/features/voice_assistant/domain/assistant_ask_result.dart';
import 'package:mobile/features/voice_assistant/infrastructure/remote/voice_assistant_api_client.dart';
import 'package:mobile/features/voice_assistant/presentation/controllers/voice_assistant_controller.dart';

void main() {
  group('AssistantAskResult', () {
    test('needsConfirmation when clarifying with tool name', () {
      const result = AssistantAskResult(
        traceId: 't1',
        action: 'ask_clarifying_question',
        toolName: 'admin_cancel_reservation',
        response: '¿Confirmas?',
      );
      expect(result.needsConfirmation, isTrue);
      expect(result.isClarifying, isTrue);
    });

    test('clarifying without tool is not confirmation', () {
      const result = AssistantAskResult(
        traceId: 't1',
        action: 'ask_clarifying_question',
        response: '¿Cuál es el código?',
      );
      expect(result.needsConfirmation, isFalse);
    });

    test('fromJson parses tool and planner output maps', () {
      final result = AssistantAskResult.fromJson({
        'trace_id': 'abc',
        'action': 'tool_call',
        'tool_name': 'admin_list_equines',
        'response': 'Listo',
        'tool_output': {'total': 3},
        'planner_output': {'confidence': 0.9},
      });
      expect(result.toolOutput['total'], 3);
      expect(result.plannerOutput['confidence'], 0.9);
    });
  });

  group('VoiceAssistantController', () {
    late VoiceAssistantController controller;

    tearDown(() {
      controller.dispose();
    });

    test('enters analyzing stage while awaiting API', () async {
      controller = VoiceAssistantController(
        apiClient: VoiceAssistantApiClient(
          baseUrl: 'http://localhost:8000/api/v1',
          readAccessToken: () async => 'token',
          refreshSession: () async => false,
          httpClient: MockClient((_) => Completer<http.Response>().future),
        ),
      );
      controller.transcript = 'listar reservas';
      unawaited(controller.sendTranscript());
      await Future<void>.delayed(Duration.zero);

      expect(controller.phase, VoicePhase.processing);
      expect(controller.processingStage, VoiceProcessingStage.analyzing);
    });

    test('maps confirmation response to awaitingConfirmation', () async {
      controller = VoiceAssistantController(
        apiClient: VoiceAssistantApiClient(
          baseUrl: 'http://localhost:8000/api/v1',
          readAccessToken: () async => 'token',
          refreshSession: () async => false,
          httpClient: MockClient(
            (_) async => http.Response(
              jsonEncode({
                'trace_id': 't1',
                'action': 'ask_clarifying_question',
                'tool_name': 'admin_cancel_reservation',
                'response': '¿Confirmas cancelar la reserva?',
                'planner_output': {},
                'tool_output': {},
              }),
              200,
            ),
          ),
        ),
      );
      controller.transcript = 'cancelar reserva ABC';
      await controller.sendTranscript();

      expect(controller.phase, VoicePhase.awaitingConfirmation);
      expect(controller.result?.needsConfirmation, isTrue);
    });
  });
}
