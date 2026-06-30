// ignore_for_file: public_member_api_docs, constant_identifier_names
// GENERATED CODE -- DO NOT EDIT MANUALLY
// Generated from OpenAPI spec

/// AUTO-GENERATED from OpenAPI schema `ExperienceResponseSchema`.

import 'experience_category.dart';
import 'experience_difficulty.dart';
import 'experience_level.dart';
import 'experience_status.dart';

class Experience {

  final int version;
  final DateTime createdAt;
  final DateTime updatedAt;
  final String? deletedAt;
  final String id;
  final String name;
  final String slug;
  final String subtitle;
  final String description;
  final String imageUrl;
  final ExperienceLevel level;
  final ExperienceDifficulty difficulty;
  final ExperienceCategory category;
  final ExperienceStatus status;
  final String durationHours;
  final String durationDays;
  final String baseCapacity;
  final String duration;
  final String routeDetails;
  final String pricing;
  final String inclusions;
  final String standardMaxParticipants;
  final String minParticipants;
  final List<String> tags;
  final List<String> aliases;
  final bool isActive;

  const Experience(
    {
    required this.version,
    required this.createdAt,
    required this.updatedAt,
    this.deletedAt,
    required this.id,
    required this.name,
    required this.slug,
    required this.subtitle,
    required this.description,
    required this.imageUrl,
    required this.level,
    required this.difficulty,
    required this.category,
    required this.status,
    required this.durationHours,
    required this.durationDays,
    required this.baseCapacity,
    required this.duration,
    required this.routeDetails,
    required this.pricing,
    required this.inclusions,
    required this.standardMaxParticipants,
    required this.minParticipants,
    required this.tags,
    required this.aliases,
    required this.isActive,
    }
  );

  factory Experience.fromJson(Map<String, dynamic> json) {
    return Experience(
      version: json['version'] as int,
      createdAt: DateTime.parse(json['created_at'] as String),
      updatedAt: DateTime.parse(json['updated_at'] as String),
      deletedAt: json['deleted_at'] as String?,
      id: json['id'] as String,
      name: json['name'] as String,
      slug: json['slug'] as String,
      subtitle: json['subtitle'] as String,
      description: json['description'] as String,
      imageUrl: json['image_url'] as String,
      level: (json['level'] as String).toExperienceLevel(),
      difficulty: (json['difficulty'] as String).toExperienceDifficulty(),
      category: (json['category'] as String).toExperienceCategory(),
      status: (json['status'] as String).toExperienceStatus(),
      durationHours: json['duration_hours'] as String,
      durationDays: json['duration_days'] as String,
      baseCapacity: json['base_capacity'] as String,
      duration: json['duration'] as String,
      routeDetails: json['route_details'] as String,
      pricing: json['pricing'] as String,
      inclusions: json['inclusions'] as String,
      standardMaxParticipants: json['standard_max_participants'] as String,
      minParticipants: json['min_participants'] as String,
      tags: (json['tags'] as List<dynamic>?)
        ?.cast<String>() ?? [],
      aliases: (json['aliases'] as List<dynamic>?)
        ?.cast<String>() ?? [],
      isActive: json['is_active'] as bool,
    );
  }

  Map<String, dynamic> toJson() => {
    'version': version,
    'created_at': createdAt.toIso8601String(),
    'updated_at': updatedAt.toIso8601String(),
    'deleted_at': deletedAt,
    'id': id,
    'name': name,
    'slug': slug,
    'subtitle': subtitle,
    'description': description,
    'image_url': imageUrl,
    'level': level.toJson(),
    'difficulty': difficulty.toJson(),
    'category': category.toJson(),
    'status': status.toJson(),
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
