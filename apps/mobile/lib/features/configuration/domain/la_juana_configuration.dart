class AiEnvProvider {
  const AiEnvProvider({
    required this.available,
    this.provider = 'gemini',
    this.model,
    this.fallbackModels = const [],
    this.keysConfigured = 0,
  });

  final bool available;
  final String provider;
  final String? model;
  final List<String> fallbackModels;
  final int keysConfigured;

  factory AiEnvProvider.fromJson(Map<String, dynamic>? json) {
    if (json == null) {
      return const AiEnvProvider(available: false);
    }
    return AiEnvProvider(
      available: json['available'] as bool? ?? false,
      provider: json['provider'] as String? ?? 'gemini',
      model: json['model'] as String?,
      fallbackModels: (json['fallback_models'] as List? ?? const [])
          .map((e) => e.toString())
          .toList(growable: false),
      keysConfigured: json['keys_configured'] as int? ?? 0,
    );
  }
}

class AiRouteConfiguration {
  const AiRouteConfiguration({
    required this.position,
    this.service,
    this.model,
    this.credentialConfigured = false,
  });
  final int position;
  final String? service;
  final String? model;
  final bool credentialConfigured;

  factory AiRouteConfiguration.fromJson(Map<String, dynamic> json) =>
      AiRouteConfiguration(
        position: json['position'] as int,
        service: json['service'] as String?,
        model: json['model'] as String?,
        credentialConfigured: json['credential_configured'] as bool? ?? false,
      );
}

class AiConfiguration {
  const AiConfiguration({
    required this.enabled,
    required this.source,
    this.providerMode = 'env',
    this.mutedPhones = const [],
    required this.routes,
    this.envProvider = const AiEnvProvider(available: false),
    required this.version,
  });
  final bool enabled;
  final String source;
  final String providerMode;
  final List<String> mutedPhones;
  final List<AiRouteConfiguration> routes;
  final AiEnvProvider envProvider;
  final int version;

  bool get usesEnvProvider => providerMode != 'manual';

  factory AiConfiguration.fromJson(Map<String, dynamic> json) =>
      AiConfiguration(
        enabled: json['enabled'] as bool? ?? false,
        source: json['source'] as String? ?? 'unconfigured',
        providerMode: json['provider_mode'] as String? ?? 'env',
        mutedPhones: (json['muted_phones'] as List? ?? const [])
            .map((e) => e.toString())
            .toList(),
        routes: (json['routes'] as List? ?? const [])
            .map(
              (e) => AiRouteConfiguration.fromJson(
                Map<String, dynamic>.from(e as Map),
              ),
            )
            .toList(),
        envProvider: AiEnvProvider.fromJson(
          json['env_provider'] is Map
              ? Map<String, dynamic>.from(json['env_provider'] as Map)
              : null,
        ),
        version: json['version'] as int? ?? 1,
      );
}

class PaymentConfiguration {
  const PaymentConfiguration({
    required this.manualEnabled,
    required this.bank,
    required this.accountType,
    required this.accountNumber,
    required this.holderName,
    required this.holderId,
    required this.transferNote,
    required this.boldEnabled,
    this.boldUrl,
    required this.boldFee,
    required this.boldNote,
  });
  final bool manualEnabled;
  final String bank;
  final String accountType;
  final String accountNumber;
  final String holderName;
  final String holderId;
  final String transferNote;
  final bool boldEnabled;
  final String? boldUrl;
  final double boldFee;
  final String boldNote;
  factory PaymentConfiguration.fromJson(Map<String, dynamic> j) =>
      PaymentConfiguration(
        manualEnabled: j['manual_transfer_enabled'] as bool? ?? true,
        bank: j['account_bank'] as String? ?? '',
        accountType: j['account_type'] as String? ?? '',
        accountNumber: j['account_number'] as String? ?? '',
        holderName: j['account_holder_name'] as String? ?? '',
        holderId: j['account_holder_id'] as String? ?? '',
        transferNote: j['transfer_note'] as String? ?? '',
        boldEnabled: j['bold_enabled'] as bool? ?? false,
        boldUrl: j['bold_checkout_url'] as String?,
        boldFee: (j['bold_surcharge_percent'] as num? ?? 7).toDouble(),
        boldNote: j['bold_note'] as String? ?? '',
      );
}

class BusinessLocationConfiguration {
  const BusinessLocationConfiguration({
    required this.name,
    required this.address,
    required this.municipality,
    required this.directions,
    required this.latitude,
    required this.longitude,
    required this.googleMapsUrl,
  });
  final String name, address, municipality, directions, googleMapsUrl;
  final double latitude, longitude;
  factory BusinessLocationConfiguration.fromJson(Map<String, dynamic> j) =>
      BusinessLocationConfiguration(
        name: j['name'] as String? ?? 'La Juana',
        address: j['address'] as String? ?? '',
        municipality: j['municipality'] as String? ?? '',
        directions: j['directions'] as String? ?? '',
        latitude: (j['latitude'] as num? ?? 5.152583).toDouble(),
        longitude: (j['longitude'] as num? ?? -75.501472).toDouble(),
        googleMapsUrl: j['google_maps_url'] as String? ?? '',
      );
}
