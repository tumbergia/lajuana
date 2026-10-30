import 'package:flutter_test/flutter_test.dart';
import 'package:mobile/app/api_base_url.dart';

void main() {
  group('requireProductionApiBaseUrl', () {
    test('accepts HTTPS and removes trailing slashes', () {
      expect(
        requireProductionApiBaseUrl('https://api.lajuana.co/api/v1///'),
        'https://api.lajuana.co/api/v1',
      );
    });

    test('rejects missing URL', () {
      expect(() => requireProductionApiBaseUrl(''), throwsStateError);
    });

    test('rejects HTTP and loopback URLs', () {
      expect(
        () => requireProductionApiBaseUrl('http://api.lajuana.co/api/v1'),
        throwsStateError,
      );
      expect(
        () => requireProductionApiBaseUrl('https://localhost/api/v1'),
        throwsStateError,
      );
    });
  });
}
