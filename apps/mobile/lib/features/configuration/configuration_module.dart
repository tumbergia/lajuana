import 'package:mobile/features/configuration/infrastructure/configuration_api_client.dart';
import 'package:mobile_domain/src/reservations/reservations_repository.dart';

class LaJuanaConfigurationModule {
  const LaJuanaConfigurationModule(this.api, {this.reservationsRepository});
  final ConfigurationApiClient api;
  final ReservationsRepository? reservationsRepository;
}
