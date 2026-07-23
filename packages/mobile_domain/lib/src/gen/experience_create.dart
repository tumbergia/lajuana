// ignore_for_file: public_member_api_docs, constant_identifier_names
// GENERATED CODE -- DO NOT EDIT MANUALLY
// Generated from OpenAPI spec

/// AUTO-GENERATED from OpenAPI schema `ExperienceCreateSchema`.

import 'experience_category.dart';
import 'experience_difficulty.dart';
import 'experience_level.dart';
import 'experience_status.dart';

class ExperienceCreate {
  final String name;
  final String slug;
  final String? subtitle;
  final String description;
  final String? imageUrl;
  final ExperienceLevel level;
  final ExperienceDifficulty? difficulty;
  final ExperienceCategory? category;
  final ExperienceStatus? status;
  final String? durationHours;
  final String? durationDays;
  final String? baseCapacity;
  final String? duration;
  final String? routeDetails;
  final String? pricing;
  final String? inclusions;
  final String? standardMaxParticipants;
  final String? minParticipants;
  final List<String>? tags;
  final List<String>? aliases;
  final bool? isActive;

  const ExperienceCreate({
    required this.name,
    required this.slug,
    this.subtitle,
    required this.description,
    this.imageUrl,
    required this.level,
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

  factory ExperienceCreate.fromJson(Map<String, dynamic> json) {
    return ExperienceCreate(
      name: json['name'] as String,
      slug: json['slug'] as String,
      subtitle: json['subtitle'] as String?,
      description: json['description'] as String,
      imageUrl: json['image_url'] as String?,
      level: (json['level'] as String).toExperienceLevel(),
      difficulty: json['difficulty'] != null
          ? (json['difficulty'] as String).toExperienceDifficulty()
          : null,
      category: json['category'] != null
          ? (json['category'] as String).toExperienceCategory()
          : null,
      status: json['status'] != null
          ? (json['status'] as String).toExperienceStatus()
          : null,
      durationHours: json['duration_hours'] as String?,
      durationDays: json['duration_days'] as String?,
      baseCapacity: json['base_capacity'] as String?,
      duration: json['duration'] as String?,
      routeDetails: json['route_details'] as String?,
      pricing: json['pricing'] as String?,
      inclusions: json['inclusions'] as String?,
      standardMaxParticipants: json['standard_max_participants'] as String?,
      minParticipants: json['min_participants'] as String?,
      tags: (json['tags'] as List<dynamic>?)?.cast<String>(),
      aliases: (json['aliases'] as List<dynamic>?)?.cast<String>(),
      isActive: json['is_active'] as bool?,
    );
  }

  Map<String, dynamic> toJson() => {
    'name': name,
    'slug': slug,
    'subtitle': subtitle,
    'description': description,
    'image_url': imageUrl,
    'level': level.toJson(),
    'difficulty': difficulty?.toJson(),
    'category': category?.toJson(),
    'status': status?.toJson(),
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
