class AnalyticsApiFailure implements Exception {
  const AnalyticsApiFailure({
    required this.code,
    required this.message,
    this.statusCode,
  });

  final String code;
  final String message;
  final int? statusCode;
}
