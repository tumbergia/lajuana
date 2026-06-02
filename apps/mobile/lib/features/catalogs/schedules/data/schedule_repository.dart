import 'package:mobile/features/catalogs/data/catalogs_repository.dart';
import 'package:mobile/features/catalogs/schedules/domain/schedule.dart';
import 'package:mobile/features/catalogs/schedules/domain/schedule_status.dart';

class ScheduleRepository {
  const ScheduleRepository(this._catalogsRepository);

  final CatalogsRepository _catalogsRepository;

  Future<List<CatalogSchedule>> list() => _catalogsRepository.listSchedules();

  Future<CatalogSchedule?> getById(String id) =>
      _catalogsRepository.getScheduleById(id);

  Future<void> create({
    required String experienceId,
    required String dateIso,
    required String startTime,
    required bool isActive,
    required int capacityTotal,
    required int reservedSlots,
    required int internalSlots,
    required int blockedSlots,
    required bool customRequestOnly,
    String? notes,
  }) {
    return _catalogsRepository.createSchedule(
      experienceId: experienceId,
      dateIso: dateIso,
      startTime: startTime,
      isActive: isActive,
      capacityTotal: capacityTotal,
      reservedSlots: reservedSlots,
      internalSlots: internalSlots,
      blockedSlots: blockedSlots,
      customRequestOnly: customRequestOnly,
      notes: notes,
    );
  }

  Future<void> update({
    required String id,
    required bool isActive,
    required int capacityTotal,
    required int reservedSlots,
    required int internalSlots,
    required int blockedSlots,
    required CatalogScheduleStatus status,
    required bool customRequestOnly,
    String? notes,
  }) {
    return _catalogsRepository.updateSchedule(
      id: id,
      isActive: isActive,
      capacityTotal: capacityTotal,
      reservedSlots: reservedSlots,
      internalSlots: internalSlots,
      blockedSlots: blockedSlots,
      status: status,
      customRequestOnly: customRequestOnly,
      notes: notes,
    );
  }

  Future<void> deactivate(String id) =>
      _catalogsRepository.deactivateSchedule(id);
}
