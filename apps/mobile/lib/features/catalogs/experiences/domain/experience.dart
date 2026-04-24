import '../../../catalogs/data/catalog_sync_status.dart';

class CatalogExperienceDuration {
  const CatalogExperienceDuration({
    required this.activityMinutes,
    required this.routeMinutes,
    this.displayText,
  });

  final int activityMinutes;
  final int routeMinutes;
  final String? displayText;
}

class CatalogExperienceRouteDetails {
  const CatalogExperienceRouteDetails({
    this.distanceKm,
    required this.terrain,
    this.terrainNotes,
  });

  final double? distanceKm;
  final String terrain;
  final String? terrainNotes;
}

class CatalogExperiencePricingTier {
  const CatalogExperiencePricingTier({
    required this.minParticipants,
    required this.maxParticipants,
    required this.pricePerPerson,
  });

  final int minParticipants;
  final int maxParticipants;
  final int pricePerPerson;
}

class CatalogExperiencePricing {
  const CatalogExperiencePricing({
    required this.currency,
    required this.tiers,
    required this.pricesAreNet,
    this.pricingNotes,
  });

  final String currency;
  final List<CatalogExperiencePricingTier> tiers;
  final bool pricesAreNet;
  final String? pricingNotes;
}

class CatalogExperienceInclusions {
  const CatalogExperienceInclusions({required this.items, this.displayText});

  final List<String> items;
  final String? displayText;
}

class CatalogExperience {
  const CatalogExperience({
    required this.id,
    required this.name,
    required this.slug,
    required this.description,
    required this.level,
    required this.isActive,
    required this.syncStatus,
    this.subtitle,
    this.imageUrl,
    this.difficulty,
    this.category,
    this.status,
    this.duration,
    this.routeDetails,
    this.pricing,
    this.inclusions,
    this.standardMaxParticipants,
    this.minParticipants,
    this.tags = const <String>[],
    this.durationHours,
    this.durationDays,
    this.baseCapacity,
    this.remoteId,
    this.versionRemote,
    this.syncError,
    this.updatedAtRemote,
  });

  final String id;
  final String? remoteId;
  final String name;
  final String slug;
  final String? subtitle;
  final String description;
  final String? imageUrl;
  final String level;
  final String? difficulty;
  final String? category;
  final String? status;
  final CatalogExperienceDuration? duration;
  final CatalogExperienceRouteDetails? routeDetails;
  final CatalogExperiencePricing? pricing;
  final CatalogExperienceInclusions? inclusions;
  final int? standardMaxParticipants;
  final int? minParticipants;
  final List<String> tags;
  final int? durationHours;
  final int? durationDays;
  final int? baseCapacity;
  final bool isActive;
  final CatalogSyncStatus syncStatus;
  final int? versionRemote;
  final String? syncError;
  final DateTime? updatedAtRemote;
}
