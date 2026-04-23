enum LinkType {
  offline,
  mobile,
  wifi,
  other,
}

enum BackendReachability {
  reachable,
  unreachable,
  unknown,
}

class NetworkStatus {
  const NetworkStatus({
    required this.linkType,
    required this.backendReachability,
  });

  final LinkType linkType;
  final BackendReachability backendReachability;

  bool get hasSomeLink => linkType != LinkType.offline;

  bool get canReachBackend =>
      backendReachability == BackendReachability.reachable;

  bool get isProbablyOffline =>
      linkType == LinkType.offline &&
      backendReachability != BackendReachability.reachable;

  @override
  bool operator ==(Object other) {
    if (identical(this, other)) return true;
    return other is NetworkStatus &&
        other.linkType == linkType &&
        other.backendReachability == backendReachability;
  }

  @override
  int get hashCode => Object.hash(linkType, backendReachability);
}
