import 'dart:async';
import 'dart:io';

import 'package:http/http.dart' as http;

import 'network_models.dart';

abstract class BackendReachabilityService {
  Future<BackendReachability> check();
}

class HttpBackendReachabilityService implements BackendReachabilityService {
  HttpBackendReachabilityService({
    required String baseUrl,
    http.Client? httpClient,
    this.timeout = const Duration(seconds: 3),
  }) : _http = httpClient ?? http.Client(),
       _healthUri = Uri.parse(
         '${baseUrl.replaceFirst(RegExp(r'/+$'), '')}/health',
       );

  final http.Client _http;
  final Uri _healthUri;
  final Duration timeout;

  @override
  Future<BackendReachability> check() async {
    final first = await _checkOnce();
    if (first != BackendReachability.unreachable) return first;

    await Future<void>.delayed(const Duration(milliseconds: 400));
    return _checkOnce();
  }

  Future<BackendReachability> _checkOnce() async {
    try {
      final response = await _http.get(_healthUri).timeout(timeout);
      if (response.statusCode >= 200 && response.statusCode < 500) {
        return BackendReachability.reachable;
      }
      return BackendReachability.unreachable;
    } on TimeoutException {
      return BackendReachability.unreachable;
    } on SocketException {
      return BackendReachability.unreachable;
    } on HttpException {
      return BackendReachability.unreachable;
    } on FormatException {
      return BackendReachability.unreachable;
    } catch (_) {
      return BackendReachability.unknown;
    }
  }
}
