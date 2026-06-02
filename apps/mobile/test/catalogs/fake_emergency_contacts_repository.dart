import 'package:mobile/features/catalogs/emergency_contacts/data/emergency_contacts_repository.dart';
import 'package:mobile/features/catalogs/emergency_contacts/domain/emergency_contact.dart';

import 'fake_catalogs_repository.dart';

/// Fake [EmergencyContactsRepository] for testing [EmergencyContactsController].
class FakeEmergencyContactsRepository extends EmergencyContactsRepository {
  FakeEmergencyContactsRepository({
    this.returnEmpty = false,
    this.throwOnList = false,
  }) : super(FakeCatalogsRepository());

  final bool returnEmpty;
  final bool throwOnList;

  int listCallCount = 0;

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
  Future<List<CatalogEmergencyContact>> list() async {
    listCallCount++;
    if (throwOnList) throw Exception('List error');
    if (returnEmpty) return [];
    return [_sampleContact];
  }
}
