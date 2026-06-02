class SaddlesApiFailure implements Exception {
  const SaddlesApiFailure({
    required this.code,
    required this.message,
    this.statusCode,
  });

  final String code;
  final String message;
  final int? statusCode;
}
