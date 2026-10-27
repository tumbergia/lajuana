import 'dart:async';
import 'dart:convert';

import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:mobile/features/voice_assistant/domain/assistant_ask_result.dart';
import 'package:mobile/features/voice_assistant/infrastructure/remote/voice_assistant_api_client.dart';
import 'package:mobile/features/voice_assistant/presentation/controllers/voice_assistant_controller.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  group('AssistantAskResult', () {
    test('needsConfirmation only when API flag is true', () {
      const result = AssistantAskResult(
        traceId: 't1',
        action: 'ask_clarifying_question',
        toolName: 'admin_cancel_reservation',
        response: '¿Confirmas?',
        needsConfirmation: true,
      );
      expect(result.needsConfirmation, isTrue);
      expect(result.isClarifying, isTrue);
    });

    test('clarifying with tool name is not confirmation without flag', () {
      const result = AssistantAskResult(
        traceId: 't1',
        action: 'ask_clarifying_question',
        toolName: 'admin_create_user',
        response: '¿Cuál es el correo?',
      );
      expect(result.needsConfirmation, isFalse);
    });

    test('clarifying without tool is not confirmation', () {
      const result = AssistantAskResult(
        traceId: 't1',
        action: 'ask_clarifying_question',
        response: '¿Cuál es el código?',
      );
      expect(result.needsConfirmation, isFalse);
    });

    test('fromJson needs_confirmation false by default', () {
      final result = AssistantAskResult.fromJson({
        'trace_id': 'abc',
        'action': 'ask_clarifying_question',
        'tool_name': 'admin_create_user',
        'response': '¿cuál es el correo electrónico?',
        'tool_output': {},
        'planner_output': {},
      });
      expect(result.needsConfirmation, isFalse);
      expect(result.isClarifying, isTrue);
    });

    test('fromJson reads needs_confirmation true', () {
      final result = AssistantAskResult.fromJson({
        'trace_id': 'abc',
        'action': 'ask_clarifying_question',
        'tool_name': 'admin_create_user',
        'response': '¿Confirmas?',
        'needs_confirmation': true,
        'tool_output': {},
        'planner_output': {},
      });
      expect(result.needsConfirmation, isTrue);
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
                'needs_confirmation': true,
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

    test(
      'maps missing-fields clarifying to needsInput not confirmation',
      () async {
        controller = VoiceAssistantController(
          apiClient: VoiceAssistantApiClient(
            baseUrl: 'http://localhost:8000/api/v1',
            readAccessToken: () async => 'token',
            refreshSession: () async => false,
            httpClient: MockClient(
              (_) async => http.Response(
                jsonEncode({
                  'trace_id': 't2',
                  'action': 'ask_clarifying_question',
                  'tool_name': 'admin_create_user',
                  'response': '¿cuál es el correo electrónico?',
                  'planner_output': {},
                  'tool_output': {},
                  'needs_confirmation': false,
                }),
                200,
              ),
            ),
          ),
        );
        controller.transcript = 'crea un usuario llamado Ana';
        await controller.sendTranscript();

        expect(controller.phase, VoicePhase.needsInput);
        expect(controller.result?.needsConfirmation, isFalse);
      },
    );

    test('keeps conversationId after cleanup pause', () async {
      controller = VoiceAssistantController(
        apiClient: VoiceAssistantApiClient(
          baseUrl: 'http://localhost:8000/api/v1',
          readAccessToken: () async => 'token',
          refreshSession: () async => false,
          httpClient: MockClient((_) => Completer<http.Response>().future),
        ),
      );
      controller.conversationId = 'mobile-voice-keep';
      await controller.cleanup();
      expect(controller.conversationId, 'mobile-voice-keep');
      expect(controller.phase, VoicePhase.idle);

      await controller.startNewConversation();
      expect(controller.conversationId, isNot('mobile-voice-keep'));
    });
  });
}
