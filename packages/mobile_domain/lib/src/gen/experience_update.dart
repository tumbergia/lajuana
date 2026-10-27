// ignore_for_file: public_member_api_docs, constant_identifier_names
// GENERATED CODE -- DO NOT EDIT MANUALLY
// Generated from OpenAPI spec

/// AUTO-GENERATED from OpenAPI schema `ExperienceUpdateSchema`.

class ExperienceUpdate {
  final String? name;
  final String? subtitle;
  final String? description;
  final String? imageUrl;
  final String? level;
  final String? difficulty;
  final String? category;
  final String? status;
  final String? durationHours;
  final String? durationDays;
  final String? baseCapacity;
  final String? duration;
  final String? routeDetails;
  final String? pricing;
  final String? inclusions;
  final String? standardMaxParticipants;
  final String? minParticipants;
  final String? tags;
  final String? aliases;
  final String? isActive;

  const ExperienceUpdate({
    this.name,
    this.subtitle,
    this.description,
    this.imageUrl,
    this.level,
    this.difficulty,
    this.category,
    this.status,
    this.durationHours,
    this.durationDays,
    this.baseCapacity,
    this.duration,
    this.routeDetails,
    this.pricing,
    this.inclusions,
    this.standardMaxParticipants,
    this.minParticipants,
    this.tags,
    this.aliases,
    this.isActive,
  });

  factory ExperienceUpdate.fromJson(Map<String, dynamic> json) {
    return ExperienceUpdate(
      name: json['name'] as String?,
      subtitle: json['subtitle'] as String?,
      description: json['description'] as String?,
      imageUrl: json['image_url'] as String?,
      level: json['level'] as String?,
      difficulty: json['difficulty'] as String?,
      category: json['category'] as String?,
      status: json['status'] as String?,
      durationHours: json['duration_hours'] as String?,
      durationDays: json['duration_days'] as String?,
      baseCapacity: json['base_capacity'] as String?,
      duration: json['duration'] as String?,
      routeDetails: json['route_details'] as String?,
      pricing: json['pricing'] as String?,
      inclusions: json['inclusions'] as String?,
      standardMaxParticipants: json['standard_max_participants'] as String?,
      minParticipants: json['min_participants'] as String?,
      tags: json['tags'] as String?,
      aliases: json['aliases'] as String?,
      isActive: json['is_active'] as String?,
    );
  }

  Map<String, dynamic> toJson() => {
    'name': name,
    'subtitle': subtitle,
    'description': description,
    'image_url': imageUrl,
    'level': level,
    'difficulty': difficulty,
    'category': category,
    'status': status,
    'duration_hours': durationHours,
    'duration_days': durationDays,
    'base_capacity': baseCapacity,
    'duration': duration,
    'route_details': routeDetails,
    'pricing': pricing,
    'inclusions': inclusions,
    'standard_max_participants': standardMaxParticipants,
    'min_participants': minParticipants,
    'tags': tags,
    'aliases': aliases,
    'is_active': isActive,
  };
}
