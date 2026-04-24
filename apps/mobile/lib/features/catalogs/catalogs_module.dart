import 'data/catalogs_repository.dart';
import 'emergency_contacts/data/emergency_contacts_repository.dart';
import 'experiences/data/experience_repository.dart';
import 'reservation_rules/data/reservation_rules_repository.dart';
import 'schedules/data/schedule_repository.dart';

class CatalogsModule {
  CatalogsModule(this.repository)
    : experiences = ExperienceRepository(repository),
      schedules = ScheduleRepository(repository),
      reservationRules = ReservationRulesRepository(repository),
      emergencyContacts = EmergencyContactsRepository(repository);

  final CatalogsRepository repository;
  final ExperienceRepository experiences;
  final ScheduleRepository schedules;
  final ReservationRulesRepository reservationRules;
  final EmergencyContactsRepository emergencyContacts;
}
