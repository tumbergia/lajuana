// ignore_for_file: public_member_api_docs, constant_identifier_names
// GENERATED CODE -- DO NOT EDIT MANUALLY
// Generated from OpenAPI spec

/// AUTO-GENERATED from OpenAPI schema `ExperienceRouteDetailsSchema`.

class ExperienceRouteDetails {
  final String? distanceKm;
  final String terrain;
  final String? terrainNotes;

  const ExperienceRouteDetails({
    this.distanceKm,
    required this.terrain,
    this.terrainNotes,
  });

  factory ExperienceRouteDetails.fromJson(Map<String, dynamic> json) {
    return ExperienceRouteDetails(
      distanceKm: json['distance_km'] as String?,
      terrain: json['terrain'] as String,
      terrainNotes: json['terrain_notes'] as String?,
    );
  }

  Map<String, dynamic> toJson() => {
    'distance_km': distanceKm,
    'terrain': terrain,
    'terrain_notes': terrainNotes,
  };
}
