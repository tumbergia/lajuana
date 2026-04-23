import 'dart:async';

import 'backend_reachability_service.dart';
import 'connectivity_service.dart';
import 'network_models.dart';

class NetworkStatusResolver {
  NetworkStatusResolver({
    required ConnectivityService connectivityService,
    required BackendReachabilityService backendReachabilityService,
  })  : _connectivityService = connectivityService,
        _backendReachabilityService = backendReachabilityService;

  final ConnectivityService _connectivityService;
  final BackendReachabilityService _backendReachabilityService;

  Future<NetworkStatus> current() async {
    final linkType = await _connectivityService.currentLinkType();

    if (linkType == LinkType.offline) {
      return const NetworkStatus(
        linkType: LinkType.offline,
        backendReachability: BackendReachability.unknown,
      );
    }

    final reachability = await _backendReachabilityService.check();
    return NetworkStatus(
      linkType: linkType,
      backendReachability: reachability,
    );
  }

  Stream<NetworkStatus> observe() async* {
    yield await current();
    NetworkStatus? previous;
    await for (final status in _connectivityService
        .observeLinkType()
        .asyncMap((_) => current())) {
      if (previous != status) {
        previous = status;
        yield status;
      }
    }
  }
}
