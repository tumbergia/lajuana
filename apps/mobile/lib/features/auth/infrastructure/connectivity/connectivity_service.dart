import 'dart:async';

import 'package:connectivity_plus/connectivity_plus.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter/services.dart';

import 'network_models.dart';

abstract class ConnectivityService {
  Future<LinkType> currentLinkType();
  Stream<LinkType> observeLinkType();
}

class ConnectivityPlusService implements ConnectivityService {
  ConnectivityPlusService({Connectivity? connectivity})
      : _connectivity = connectivity ?? Connectivity();

  final Connectivity _connectivity;

  @override
  Future<LinkType> currentLinkType() async {
    try {
      final result = await _connectivity.checkConnectivity();
      return _map(result);
    } on MissingPluginException {
      return LinkType.other;
    } catch (_) {
      return LinkType.other;
    }
  }

  @override
  Stream<LinkType> observeLinkType() {
    if (kIsWeb) {
      return Stream<int>.periodic(
        const Duration(seconds: 5),
        (tick) => tick,
      ).asyncMap((_) => currentLinkType()).distinct();
    }

    return _connectivity.onConnectivityChanged
        .map(_map)
        .handleError((Object? error, StackTrace stackTrace) {})
        .distinct();
  }

  LinkType _map(List<ConnectivityResult> results) {
    if (results.isEmpty) return LinkType.other;
    if (results.every((r) => r == ConnectivityResult.none)) {
      return LinkType.offline;
    }
    if (results.contains(ConnectivityResult.wifi)) {
      return LinkType.wifi;
    }
    if (results.contains(ConnectivityResult.mobile)) {
      return LinkType.mobile;
    }
    return LinkType.other;
  }
}
