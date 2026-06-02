import 'package:mobile/features/catalogs/experiences/data/experience_repository.dart';
import 'package:mobile/features/catalogs/experiences/domain/experience.dart';

import 'data/catalog_sync_status_helpers.dart';
import 'fake_catalogs_repository.dart';

/// Fake [ExperienceRepository] for testing [ExperiencesController].
///
/// Uses a [FakeCatalogsRepository] internally — all methods used by the
/// controller are overridden so the internal catalog repo is never hit.
class FakeExperienceRepository extends ExperienceRepository {
  FakeExperienceRepository({
    this.returnEmpty = false,
    this.throwOnList = false,
    this.throwOnDeactivate = false,
  }) : super(FakeCatalogsRepository());

  final bool returnEmpty;
  final bool throwOnList;
  final bool throwOnDeactivate;

  int listCallCount = 0;

  static final _sampleExperience = CatalogExperience(
    id: 'exp-1',
    name: 'Cabalgata Básica',
    slug: 'cabalgata-basica',
    description: 'Un paseo a caballo de 2 horas',
    level: 'basic',
    isActive: true,
    syncStatus: catalogSyncStatusSynced,
    tags: const [],
  );

  @override
  Future<List<CatalogExperience>> list() async {
    listCallCount++;
    if (throwOnList) throw Exception('List error');
    if (returnEmpty) return [];
    return [_sampleExperience];
  }

  @override
  Future<void> deactivate(String id) async {
    if (throwOnDeactivate) throw Exception('Deactivate error');
  }
}
