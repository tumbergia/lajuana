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
      durationHours: durationHours,
      durationDays: durationDays,
      baseCapacity: baseCapacity,
      isActive: isActive,
    );
  }

  Future<void> update({
    required String id,
    required String name,
    required String description,
    required String level,
    required bool isActive,
    int? durationHours,
    int? durationDays,
    int? baseCapacity,
  }) {
    return _catalogsRepository.updateExperience(
      id: id,
      name: name,
      description: description,
      level: level,
      isActive: isActive,
      durationHours: durationHours,
      durationDays: durationDays,
      baseCapacity: baseCapacity,
    );
  }

  Future<void> deactivate(String id) =>
      _catalogsRepository.deactivateExperience(id);
}
