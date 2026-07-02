import 'dart:async';

import 'package:http/http.dart' as http;
import 'package:mobile/features/catalogs/data/catalogs_database.dart';
import 'package:mobile/features/catalogs/data/catalogs_repository.dart';
import 'package:mobile/features/catalogs/data/catalogs_sync_api.dart';
import 'package:mobile/features/catalogs/emergency_contacts/domain/emergency_contact.dart';
import 'package:mobile/features/catalogs/experiences/domain/experience.dart';
import 'package:mobile/features/catalogs/reservation_rules/domain/reservation_rules.dart';

import 'data/catalog_sync_status_helpers.dart';

/// Fake [CatalogsRepository] for testing catalogs controllers.
///
/// Configurable via named parameters:
/// - [returnEmptyExperiences] / [returnEmptyContacts] / etc.
/// - [throwOnListExperiences] / [throwOnRefresh] / etc.
///
/// Tracks call counts for all refresh/sync methods.
class FakeCatalogsRepository extends CatalogsRepository {
  FakeCatalogsRepository({
    this.returnEmptyExperiences = false,
    this.returnEmptyContacts = false,
    this.throwOnListExperiences = false,
    this.throwOnListContacts = false,
    this.throwOnGetRules = false,
    this.throwOnRefresh = false,
    this.throwOnSync = false,
    this.throwOnUpdate = false,
  }) : super(
          database: CatalogsDatabase.instance,
          api: CatalogsSyncApi(
            baseUrl: 'http://test.local',
            readAccessToken: _dummyToken,
            refreshSession: _dummyRefresh,
            httpClient: http.Client(),
          ),
        );

  static Future<String?> _dummyToken() async => 'test-token';
  static Future<bool> _dummyRefresh() async => true;

  final bool returnEmptyExperiences;
  final bool returnEmptyContacts;
  final bool throwOnListExperiences;
  final bool throwOnListContacts;
  final bool throwOnGetRules;
  final bool throwOnRefresh;
  final bool throwOnSync;
  final bool throwOnUpdate;

  Completer<void>? refreshCompleter;

  int refreshExperiencesCallCount = 0;
  int refreshContactsCallCount = 0;
  int refreshRulesCallCount = 0;
  int syncNowCallCount = 0;
  int updateRulesCallCount = 0;

  // ── Experiences ──────────────────────────────────────────────

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
  Future<List<CatalogExperience>> listExperiences({
    bool includeInactive = false,
  }) async {
    if (throwOnListExperiences) throw Exception('List error');
    if (returnEmptyExperiences) return [];
    return [_sampleExperience];
  }

  @override
  Future<void> refreshExperiencesFromServer() async {
    refreshExperiencesCallCount++;
    if (throwOnRefresh) throw Exception('Refresh error');
    if (refreshCompleter != null) {
      await refreshCompleter!.future;
    }
  }

  // ── Emergency Contacts ───────────────────────────────────────

  static final _sampleContact = CatalogEmergencyContact(
    code: 'POL-01',
    name: 'Policía Nacional',
    description: 'Emergencias generales',
    phoneNumber: '123',
    category: 'security',
    isPrimary: true,
    isNational: true,
  );

  @override
  Future<List<CatalogEmergencyContact>> listEmergencyContacts() async {
    if (throwOnListContacts) throw Exception('List error');
    if (returnEmptyContacts) return [];
    return [_sampleContact];
  }

  @override
  Future<void> refreshEmergencyContactsFromServer() async {
    refreshContactsCallCount++;
    if (throwOnRefresh) throw Exception('Refresh error');
  }

  // ── Reservation Rules ────────────────────────────────────────

  static final _sampleRules = CatalogReservationRules(
    minDaysInAdvance: 1,
    requirePaymentProofForConfirmation: false,
    syncStatus: catalogSyncStatusSynced,
  );

  @override
  Future<CatalogReservationRules> getReservationRules() async {
    if (throwOnGetRules) throw Exception('Get rules error');
    return _sampleRules;
  }

  @override
  Future<void> refreshReservationRulesFromServer() async {
    refreshRulesCallCount++;
    if (throwOnRefresh) throw Exception('Refresh error');
  }

  @override
  Future<void> updateReservationRules({
    required int minDaysInAdvance,
    required bool requirePaymentProofForConfirmation,
  }) async {
    updateRulesCallCount++;
    if (throwOnUpdate) throw Exception('Update error');
  }

  // ── Generic Sync ─────────────────────────────────────────────

  @override
  Future<void> syncNow({bool includeFailed = true}) async {
    syncNowCallCount++;
    if (throwOnSync) throw Exception('Sync error');
  }
}
