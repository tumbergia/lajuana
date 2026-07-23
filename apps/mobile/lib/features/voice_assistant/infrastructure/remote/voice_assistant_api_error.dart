class VoiceAssistantApiFailure implements Exception {
  VoiceAssistantApiFailure({
    required this.code,
    required this.message,
    this.statusCode,
  });

  final String code;
  final String message;
  final int? statusCode;

  @override
  String toString() => message;
}
