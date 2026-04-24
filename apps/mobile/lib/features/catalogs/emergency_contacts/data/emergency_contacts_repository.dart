import '../../data/catalogs_repository.dart';
import '../domain/emergency_contact.dart';

class EmergencyContactsRepository {
  const EmergencyContactsRepository(this._catalogsRepository);

  final CatalogsRepository _catalogsRepository;

  Future<List<CatalogEmergencyContact>> list() {
    return _catalogsRepository.listEmergencyContacts();
  }
}
