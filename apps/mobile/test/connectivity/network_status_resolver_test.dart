import 'package:flutter_test/flutter_test.dart';
import 'package:mobile/features/auth/infrastructure/connectivity/backend_reachability_service.dart';
import 'package:mobile/features/auth/infrastructure/connectivity/network_models.dart';
import 'package:mobile/features/auth/infrastructure/connectivity/network_status_resolver.dart';

import '../auth/test_fakes.dart';

void main() {
  test('offline no consulta reachability (unknown)', () async {
    final connectivity = FakeConnectivityService(LinkType.offline);
    var reachabilityChecks = 0;
    final reachability = _CountingReachability(
      onCheck: () => reachabilityChecks++,
    );
    final resolver = NetworkStatusResolver(
      connectivityService: connectivity,
      backendReachabilityService: reachability,
    );

    final status = await resolver.current();

    expect(status.linkType, LinkType.offline);
    expect(status.backendReachability, BackendReachability.unknown);
    expect(reachabilityChecks, 0);

    await connectivity.dispose();
  });

  test('con enlace consulta reachability', () async {
    final connectivity = FakeConnectivityService(LinkType.wifi);
    final reachability = FakeBackendReachabilityService(
      BackendReachability.reachable,
    );
    final resolver = NetworkStatusResolver(
      connectivityService: connectivity,
      backendReachabilityService: reachability,
    );

    final status = await resolver.current();

    expect(status.linkType, LinkType.wifi);
    expect(status.canReachBackend, isTrue);

    await connectivity.dispose();
  });
}

class _CountingReachability implements BackendReachabilityService {
  _CountingReachability({required this.onCheck});

  final void Function() onCheck;

  @override
  Future<BackendReachability> check() async {
    onCheck();
    return BackendReachability.reachable;
  }
}
