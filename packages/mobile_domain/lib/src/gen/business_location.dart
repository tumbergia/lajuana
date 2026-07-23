// ignore_for_file: public_member_api_docs, constant_identifier_names
// GENERATED CODE -- DO NOT EDIT MANUALLY
// Generated from OpenAPI spec

/// AUTO-GENERATED from OpenAPI schema `BusinessLocationSchema`.

class BusinessLocation {

  final String name;
  final String address;
  final String municipality;
  final String directions;
  final double latitude;
  final double longitude;
  final String googleMapsUrl;

  const BusinessLocation(
    {
    required this.name,
    required this.address,
    required this.municipality,
    required this.directions,
    required this.latitude,
    required this.longitude,
    required this.googleMapsUrl,
    }
  );

  factory BusinessLocation.fromJson(Map<String, dynamic> json) {
    return BusinessLocation(
      name: json['name'] as String,
      address: json['address'] as String,
      municipality: json['municipality'] as String,
      directions: json['directions'] as String,
      latitude: (json['latitude'] as num).toDouble(),
      longitude: (json['longitude'] as num).toDouble(),
      googleMapsUrl: json['google_maps_url'] as String,
    );
  }

  Map<String, dynamic> toJson() => {
    'name': name,
    'address': address,
    'municipality': municipality,
    'directions': directions,
    'latitude': latitude,
    'longitude': longitude,
    'google_maps_url': googleMapsUrl,
  };

}
