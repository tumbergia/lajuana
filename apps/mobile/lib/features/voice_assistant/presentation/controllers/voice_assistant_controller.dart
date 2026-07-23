import 'dart:async';

import 'package:flutter/foundation.dart';
import 'package:speech_to_text/speech_recognition_error.dart';
import 'package:speech_to_text/speech_recognition_result.dart';
import 'package:speech_to_text/speech_to_text.dart';

import 'package:mobile/app/errors/user_facing_error.dart';

import '../../domain/assistant_ask_result.dart';
import '../../domain/voice_platform_support.dart';
import '../../infrastructure/remote/voice_assistant_api_client.dart';
import '../../infrastructure/remote/voice_assistant_api_error.dart';

enum VoicePhase {
  idle,
  listening,
  processing,
  answered,
  awaitingConfirmation,
  needsInput,
  handoff,
  error,
}

enum VoiceProcessingStage { analyzing, planning, executing }

class VoiceAssistantController extends ChangeNotifier {
  VoiceAssistantController({required VoiceAssistantApiClient apiClient})
    : _apiClient = apiClient;

  final VoiceAssistantApiClient _apiClient;
  final SpeechToText _speech = SpeechToText();

  VoicePhase phase = VoicePhase.idle;
  VoiceProcessingStage processingStage = VoiceProcessingStage.analyzing;
  String transcript = '';
  AssistantAskResult? result;
  String? errorMessage;
  String? conversationId;
  bool _speechReady = false;
  bool _isListening = false;
  Timer? _processingTimer;
  DateTime? _processingStartedAt;
  bool speechSupported = VoicePlatformSupport.supportsNativeSpeech;
  bool get allowsManualInput =>
      !speechSupported || VoicePlatformSupport.requiresExplicitListenGesture;

  bool get isProcessing => phase == VoicePhase.processing;

  bool get canSend =>
      transcript.trim().isNotEmpty &&
      (phase == VoicePhase.listening ||
          phase == VoicePhase.idle ||
          phase == VoicePhase.answered ||
          phase == VoicePhase.needsInput);

  bool get isListening => _isListening;

  String get processingStatusLabel => switch (processingStage) {
    VoiceProcessingStage.analyzing => 'Analizando instrucción…',
    VoiceProcessingStage.planning => 'Planificando acción…',
    VoiceProcessingStage.executing => 'Ejecutando herramienta…',
  };

  Future<void> beginSession() async {
    conversationId ??=
        'mobile-voice-${DateTime.now().toUtc().millisecondsSinceEpoch}';
    transcript = '';
    result = null;
    errorMessage = null;
    phase = VoicePhase.idle;
    notifyListeners();

    if (!speechSupported) {
      return;
    }

    if (!_speechReady) {
      _speechReady = await _speech.initialize(
        onStatus: _onSpeechStatus,
        onError: _onSpeechError,
        debugLogging: kDebugMode,
      );
      if (!_speechReady) {
        speechSupported = false;
        _setError(VoicePlatformSupport.unsupportedSpeechHint);
        return;
      }
    }

    if (VoicePlatformSupport.requiresExplicitListenGesture) {
      return;
    }

    await startListening();
  }

  Future<void> startListening() async {
    if (phase == VoicePhase.processing) return;

    if (!speechSupported) {
      errorMessage = VoicePlatformSupport.unsupportedSpeechHint;
      phase = VoicePhase.idle;
      notifyListeners();
      return;
    }

    if (!_speechReady) {
      _speechReady = await _speech.initialize(
        onStatus: _onSpeechStatus,
        onError: _onSpeechError,
        debugLogging: kDebugMode,
      );
      if (!_speechReady) {
        speechSupported = false;
        _setError(VoicePlatformSupport.unsupportedSpeechHint);
        return;
      }
    }

    if (_isListening) return;

    errorMessage = null;
    if (phase == VoicePhase.answered ||
        phase == VoicePhase.needsInput ||
        phase == VoicePhase.handoff) {
      transcript = '';
      result = null;
    }
    phase = VoicePhase.listening;
    notifyListeners();

    final localeId = await _resolveSpanishLocaleId();
    final started = await _speech.listen(
      onResult: _onSpeechResult,
      listenOptions: SpeechListenOptions(
        localeId: localeId,
        partialResults: true,
        listenMode: ListenMode.confirmation,
        cancelOnError: true,
        pauseFor: const Duration(seconds: 3),
      ),
    );

    if (!started) {
      speechSupported = false;
      _setError(VoicePlatformSupport.unsupportedSpeechHint);
    }
  }

  void updateTranscript(String value) {
    transcript = value;
    if (phase == VoicePhase.error && value.trim().isNotEmpty) {
      errorMessage = null;
      phase = VoicePhase.idle;
    }
    notifyListeners();
  }

  Future<void> stopListening() async {
    if (_isListening) {
      await _speech.stop();
    }
  }

  Future<void> sendTranscript() async {
    final message = transcript.trim();
    if (message.isEmpty || phase == VoicePhase.processing) return;

    await stopListening();
    await _sendMessage(message);
  }

  Future<void> confirmPendingAction() => _sendMessage('sí');

  Future<void> cancelPendingAction() => _sendMessage('no');

  Future<void> _sendMessage(String message) async {
    _stopProcessingTimer();
    phase = VoicePhase.processing;
    processingStage = VoiceProcessingStage.analyzing;
    _processingStartedAt = DateTime.now();
    errorMessage = null;
    _startProcessingTimer();
    notifyListeners();

    try {
      final response = await _apiClient.ask(
        message: message,
        conversationId: conversationId,
      );
      _applyResult(response);
    } on VoiceAssistantApiFailure catch (failure) {
      _setError(
        userFacingError(
          failure,
          fallback: 'No se pudo enviar el mensaje al asistente.',
        ),
      );
    } catch (e) {
      _setError(
        userFacingError(
          e,
          fallback: 'No se pudo enviar el mensaje al asistente.',
        ),
      );
    } finally {
      _stopProcessingTimer();
      notifyListeners();
    }
  }

  void _applyResult(AssistantAskResult response) {
    result = response;
    if (response.isHandoff) {
      phase = VoicePhase.handoff;
      return;
    }
    if (response.needsConfirmation) {
      phase = VoicePhase.awaitingConfirmation;
      return;
    }
    if (response.isClarifying) {
      phase = VoicePhase.needsInput;
      return;
    }
    phase = VoicePhase.answered;
  }

  void _startProcessingTimer() {
    _processingTimer?.cancel();
    _processingTimer = Timer.periodic(const Duration(milliseconds: 400), (_) {
      final started = _processingStartedAt;
      if (started == null || phase != VoicePhase.processing) return;

      final elapsed = DateTime.now().difference(started);
      final nextStage = elapsed.inMilliseconds < 1200
          ? VoiceProcessingStage.analyzing
          : elapsed.inMilliseconds < 3500
          ? VoiceProcessingStage.planning
          : VoiceProcessingStage.executing;

      if (nextStage != processingStage) {
        processingStage = nextStage;
        notifyListeners();
      }
    });
  }

  void _stopProcessingTimer() {
    _processingTimer?.cancel();
    _processingTimer = null;
    _processingStartedAt = null;
  }

  Future<void> speakAgain() async {
    transcript = '';
    result = null;
    errorMessage = null;
    await startListening();
  }

  Future<void> endSession() async {
    await cleanup();
    notifyListeners();
  }

  Future<void> cleanup() async {
    _stopProcessingTimer();
    await stopListening();
    conversationId = null;
    transcript = '';
    result = null;
    errorMessage = null;
    phase = VoicePhase.idle;
  }

  Future<String> _resolveSpanishLocaleId() async {
    final locales = await _speech.locales();
    if (locales.isEmpty) return 'es_ES';
    final spanish = locales.where((l) => l.localeId.startsWith('es')).toList();
    if (spanish.isEmpty) return locales.first.localeId;
    return spanish.first.localeId;
  }

  void _onSpeechResult(SpeechRecognitionResult speechResult) {
    transcript = speechResult.recognizedWords;
    notifyListeners();
  }

  void _onSpeechStatus(String status) {
    _isListening = status == 'listening';
    if (status == 'done' || status == 'notListening') {
      _isListening = false;
      if (phase == VoicePhase.listening) {
        phase = VoicePhase.idle;
        notifyListeners();
      }
    }
  }

  void _onSpeechError(SpeechRecognitionError error) {
    if (error.permanent) {
      _setError('Error de reconocimiento de voz: ${error.errorMsg}');
    }
  }

  void _setError(String message) {
    _stopProcessingTimer();
    errorMessage = message;
    phase = VoicePhase.error;
    _isListening = false;
    notifyListeners();
  }

  @override
  void dispose() {
    _stopProcessingTimer();
    unawaited(_speech.stop());
    super.dispose();
  }
}
