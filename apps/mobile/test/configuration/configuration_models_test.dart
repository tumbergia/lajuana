import 'package:flutter_test/flutter_test.dart';
import 'package:mobile/features/configuration/domain/la_juana_configuration.dart';

void main() {
  test('AI response exposes only credential status', () {
    final configuration = AiConfiguration.fromJson({
      'enabled': true,
      'source': 'database',
      'version': 2,
      'routes': [
        {
          'position': 1,
          'service': 'groq',
          'model': 'model-a',
          'credential_configured': true,
        },
      ],
    });

    expect(configuration.routes.single.credentialConfigured, isTrue);
    expect(configuration.routes.single.model, 'model-a');
  });

  test('business location keeps Google Maps URL', () {
    final location = BusinessLocationConfiguration.fromJson({
      'name': 'La Juana',
      'address': 'Ruta',
      'municipality': 'Manizales',
      'directions': 'Sigue la vía',
      'latitude': 5.1,
      'longitude': -75.5,
      'google_maps_url': 'https://maps.google.com/?q=5.100000,-75.500000',
    });
    expect(location.googleMapsUrl, startsWith('https://maps.google.com/'));
  });
}
