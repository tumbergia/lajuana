// ignore_for_file: public_member_api_docs, constant_identifier_names
// GENERATED CODE -- DO NOT EDIT MANUALLY
// Generated from OpenAPI spec

/// AUTO-GENERATED from OpenAPI schema `BusinessLocationUpdateSchema`.

class BusinessLocationUpdate {
  final String? name;
  final String? address;
  final String? municipality;
  final String? directions;
  final double? latitude;
  final double? longitude;

  const BusinessLocationUpdate({
    this.name,
    this.address,
    this.municipality,
    this.directions,
    this.latitude,
    this.longitude,
  });

  factory BusinessLocationUpdate.fromJson(Map<String, dynamic> json) {
    return BusinessLocationUpdate(
      name: json['name'] as String?,
      address: json['address'] as String?,
      municipality: json['municipality'] as String?,
      directions: json['directions'] as String?,
      latitude: (json['latitude'] as num?)?.toDouble(),
      longitude: (json['longitude'] as num?)?.toDouble(),
    );
  }

  Map<String, dynamic> toJson() => {
    'name': name,
    'address': address,
    'municipality': municipality,
    'directions': directions,
    'latitude': latitude,
    'longitude': longitude,
  };
}
