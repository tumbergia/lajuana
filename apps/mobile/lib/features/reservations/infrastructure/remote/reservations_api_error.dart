class ReservationsApiFailure implements Exception {
  const ReservationsApiFailure({
    required this.code,
    required this.message,
    this.statusCode,
  });

  final String code;
  final String message;
  final int? statusCode;
}
