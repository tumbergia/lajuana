/// Mapea [EquineOperationalStatus] del backend.
enum EquineOperationalStatus {
  available,
  resting,
  inService,
  injured,
  retired,
  unavailable,
  restricted;

  static EquineOperationalStatus fromApi(String value) {
    switch (value) {
      case 'available':
        return EquineOperationalStatus.available;
      case 'resting':
        return EquineOperationalStatus.resting;
      case 'in_service':
        return EquineOperationalStatus.inService;
      case 'injured':
        return EquineOperationalStatus.injured;
      case 'retired':
        return EquineOperationalStatus.retired;
      case 'unavailable':
        return EquineOperationalStatus.unavailable;
      case 'restricted':
        return EquineOperationalStatus.restricted;
      default:
        return EquineOperationalStatus.unavailable;
    }
  }
}
