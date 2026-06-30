import 'package:http/http.dart' as http;

import 'package:mobile/features/auth/infrastructure/token_storage.dart';
import 'infrastructure/remote/voice_assistant_api_client.dart';
import 'presentation/controllers/voice_assistant_controller.dart';

class VoiceAssistantModule {
  VoiceAssistantModule({
    required this.apiClient,
    required this.controller,
  });

  final VoiceAssistantApiClient apiClient;
  final VoiceAssistantController controller;

  factory VoiceAssistantModule.create({
    required String baseUrl,
    required TokenStorage tokenStorage,
    required Future<bool> Function() refreshSession,
    http.Client? httpClient,
  }) {
    final apiClient = VoiceAssistantApiClient(
      baseUrl: baseUrl,
      readAccessToken: () async {
        final session = await tokenStorage.getSession();
        return session?.accessToken;
      },
      refreshSession: refreshSession,
      httpClient: httpClient,
    );

    final controller = VoiceAssistantController(apiClient: apiClient);

    return VoiceAssistantModule(
      apiClient: apiClient,
      controller: controller,
    );
  }
}
