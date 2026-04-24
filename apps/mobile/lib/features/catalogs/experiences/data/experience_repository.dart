import '../../data/catalogs_repository.dart';
import '../domain/experience.dart';

class ExperienceRepository {
  const ExperienceRepository(this._catalogsRepository);

  final CatalogsRepository _catalogsRepository;

  Future<List<CatalogExperience>> list() =>
      _catalogsRepository.listExperiences();

  Future<CatalogExperience?> getById(String id) =>
      _catalogsRepository.getExperienceById(id);

  Future<void> create({
    required String name,
    required String slug,
    required String description,
    required String level,
    String? subtitle,
    String? imageUrl,
    String? difficulty,
    String? category,
    String? status,
    CatalogExperienceDuration? duration,
    CatalogExperienceRouteDetails? routeDetails,
    CatalogExperiencePricing? pricing,
    CatalogExperienceInclusions? inclusions,
    int? standardMaxParticipants,
    int? minParticipants,
    List<String>? tags,
    int? durationHours,
    int? durationDays,
    int? baseCapacity,
    bool isActive = true,
  }) {
    return _catalogsRepository.createExperience(
      name: name,
      slug: slug,
      description: description,
      level: level,
      subtitle: subtitle,
      imageUrl: imageUrl,
      difficulty: difficulty,
      category: category,
      status: status,
      duration: _durationToMap(duration),
      routeDetails: _routeDetailsToMap(routeDetails),
      pricing: _pricingToMap(pricing),
      inclusions: _inclusionsToMap(inclusions),
      standardMaxParticipants: standardMaxParticipants,
      minParticipants: minParticipants,
      tags: tags,
      durationHours: durationHours,
      durationDays: durationDays,
      baseCapacity: baseCapacity,
      isActive: isActive,
    );
  }

  Future<void> update({
    required String id,
    required String name,
    required String slug,
    required String description,
    required String level,
    required bool isActive,
    String? subtitle,
    String? imageUrl,
    String? difficulty,
    String? category,
    String? status,
    CatalogExperienceDuration? duration,
    CatalogExperienceRouteDetails? routeDetails,
    CatalogExperiencePricing? pricing,
    CatalogExperienceInclusions? inclusions,
    int? standardMaxParticipants,
    int? minParticipants,
    List<String>? tags,
    int? durationHours,
    int? durationDays,
    int? baseCapacity,
  }) {
    return _catalogsRepository.updateExperience(
      id: id,
      name: name,
      slug: slug,
      description: description,
      level: level,
      subtitle: subtitle,
      imageUrl: imageUrl,
      difficulty: difficulty,
      category: category,
      status: status,
      duration: _durationToMap(duration),
      routeDetails: _routeDetailsToMap(routeDetails),
      pricing: _pricingToMap(pricing),
      inclusions: _inclusionsToMap(inclusions),
      standardMaxParticipants: standardMaxParticipants,
      minParticipants: minParticipants,
      tags: tags,
      isActive: isActive,
      durationHours: durationHours,
      durationDays: durationDays,
      baseCapacity: baseCapacity,
    );
  }

  Future<void> deactivate(String id) =>
      _catalogsRepository.deactivateExperience(id);
}

Map<String, dynamic>? _durationToMap(CatalogExperienceDuration? value) {
  if (value == null) return null;
  return <String, dynamic>{
    'activity_minutes': value.activityMinutes,
    'route_minutes': value.routeMinutes,
    'display_text': value.displayText,
  };
}

Map<String, dynamic>? _routeDetailsToMap(CatalogExperienceRouteDetails? value) {
  if (value == null) return null;
  return <String, dynamic>{
    'distance_km': value.distanceKm,
    'terrain': value.terrain,
    'terrain_notes': value.terrainNotes,
  };
}

Map<String, dynamic>? _pricingToMap(CatalogExperiencePricing? value) {
  if (value == null) return null;
  return <String, dynamic>{
    'currency': value.currency,
    'prices_are_net': value.pricesAreNet,
    'pricing_notes': value.pricingNotes,
    'tiers': value.tiers
        .map(
          (tier) => <String, dynamic>{
            'min_participants': tier.minParticipants,
            'max_participants': tier.maxParticipants,
            'price_per_person': tier.pricePerPerson,
          },
        )
        .toList(growable: false),
  };
}

Map<String, dynamic>? _inclusionsToMap(CatalogExperienceInclusions? value) {
  if (value == null) return null;
  return <String, dynamic>{
    'items': value.items,
    'display_text': value.displayText,
  };
}
