import 'dart:async';

import 'package:flutter/foundation.dart';
import 'package:flutter/services.dart';
import 'package:connectivity_plus/connectivity_plus.dart';

import '../domain/auth_enums.dart';

abstract class ConnectivityService {
  Future<ConnectivityState> current();
  Stream<ConnectivityState> observe();
}

class ConnectivityPlusService implements ConnectivityService {
  ConnectivityPlusService({Connectivity? connectivity})
    : _connectivity = connectivity ?? Connectivity();

  final Connectivity _connectivity;

  @override
  Future<ConnectivityState> current() async {
    try {
      final result = await _connectivity.checkConnectivity();
      return _map(result);
    } on MissingPluginException {
      // En web (o hot-restart inestable), el plugin stream puede no registrarse.
      // No bloqueamos Auth por esto: asumimos online.
      return kIsWeb ? ConnectivityState.online : ConnectivityState.offline;
    } catch (_) {
      return kIsWeb ? ConnectivityState.online : ConnectivityState.offline;
    }
  }

  @override
  Stream<ConnectivityState> observe() {
    if (kIsWeb) {
      // Evita `listen` sobre channel web cuando el plugin no está disponible.
      return Stream<int>.periodic(
        const Duration(seconds: 4),
        (tick) => tick,
      ).asyncMap((_) => current()).distinct();
    }
    return _safeObserve();
  }

  Stream<ConnectivityState> _safeObserve() async* {
    try {
      yield* _connectivity.onConnectivityChanged
          .map(_map)
          .transform(
            StreamTransformer<ConnectivityState, ConnectivityState>.fromHandlers(
              handleError: (
                Object error,
                StackTrace stackTrace,
                EventSink<ConnectivityState> sink,
              ) {
                sink.add(ConnectivityState.offline);
              },
            ),
          );
    } catch (_) {
      yield ConnectivityState.offline;
    }
  }

  ConnectivityState _map(List<ConnectivityResult> list) {
    final hasOnline = list.any((item) => item != ConnectivityResult.none);
    if (!hasOnline) return ConnectivityState.offline;
    final hasMobile = list.contains(ConnectivityResult.mobile);
    final hasWifi = list.contains(ConnectivityResult.wifi);
    if (hasMobile && !hasWifi) return ConnectivityState.unstable;
    return ConnectivityState.online;
  }
}
