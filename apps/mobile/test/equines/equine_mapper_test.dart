import 'package:flutter_test/flutter_test.dart';
import 'package:mobile_domain/src/equines/equine.dart';
import 'package:mobile_domain/src/equines/equine_experience_fit.dart';
import 'package:mobile_domain/src/equines/equine_operational_status.dart';
import 'package:mobile_domain/src/equines/equine_timeline_entry.dart';
import 'package:mobile/features/equines/infrastructure/mappers/equine_mapper.dart';
import 'package:mobile/features/equines/infrastructure/remote/equine_dtos.dart';

void main() {
  group('EquineMapper.dtoToDomain', () {
    test('maps full DTO correctly', () {
      final dto = EquineDto(
        id: 'equine-1',
        name: 'Pegaso',
        species: 'mule',
        sex: 'male',
        breed: 'Criolla',
        operationalStatus: 'available',
        isAvailable: true,
        weightKg: 350.0,
        maxRiderWeightKg: 80.0,
        experienceFit: 'beginner',
      );
      final result = EquineMapper.dtoToDomain(dto);
      expect(result.id, 'equine-1');
      expect(result.name, 'Pegaso');
      expect(result.operationalStatus, EquineOperationalStatus.available);
      expect(result.isAvailable, true);
      expect(result.experienceFit, EquineExperienceFit.beginner);
    });

    test('maps minimal DTO with defaults', () {
      final dto = EquineDto(id: 'e1', name: 'Minimal');
      final result = EquineMapper.dtoToDomain(dto);
      expect(result.id, 'e1');
      expect(result.name, 'Minimal');
      expect(result.operationalStatus, EquineOperationalStatus.available);
      expect(result.experienceFit, isNull);
    });

    test('maps in_service status correctly', () {
      final dto = EquineDto(
        id: 'e2',
        name: 'EnServicio',
        operationalStatus: 'in_service',
      );
      final result = EquineMapper.dtoToDomain(dto);
      expect(result.operationalStatus, EquineOperationalStatus.inService);
    });

    test('maps injured status correctly', () {
      final dto = EquineDto(
        id: 'e3',
        name: 'Lesionado',
        operationalStatus: 'injured',
      );
      final result = EquineMapper.dtoToDomain(dto);
      expect(result.operationalStatus, EquineOperationalStatus.injured);
    });

    test('maps retired status correctly', () {
      final dto = EquineDto(
        id: 'e4',
        name: 'Retirado',
        operationalStatus: 'retired',
      );
      final result = EquineMapper.dtoToDomain(dto);
      expect(result.operationalStatus, EquineOperationalStatus.retired);
    });

    test('maps unknown operational status to unavailable', () {
      final dto = EquineDto(
        id: 'e5',
        name: 'Unknown',
        operationalStatus: 'invalid_value',
      );
      final result = EquineMapper.dtoToDomain(dto);
      expect(result.operationalStatus, EquineOperationalStatus.unavailable);
    });

    test('parses Decimal weight from string', () {
      final dto = EquineDto(
        id: 'e6',
        name: 'Decimal',
        weightKg: 350.5,
      );
      final result = EquineMapper.dtoToDomain(dto);
      expect(result.weightKg, 350.5);
    });

    test('handles null optional fields without crashing', () {
      final dto = EquineDto(id: 'e7', name: 'NullFields');
      final result = EquineMapper.dtoToDomain(dto);
      expect(result.breed, isNull);
      expect(result.weightKg, isNull);
      expect(result.maxRiderWeightKg, isNull);
      expect(result.coatColor, isNull);
      expect(result.gait, isNull);
      expect(result.experienceFit, isNull);
      expect(result.restUntil, isNull);
    });
  });

  group('EquineMapper.domainToRecord', () {
    test('maps Equine to EquineRecord correctly', () {
      final equine = Equine(
        id: 'e1',
        name: 'Pegaso',
        operationalStatus: EquineOperationalStatus.available,
        isAvailable: true,
      );
      final record = EquineMapper.domainToRecord(equine);
      expect(record.id, 'e1');
      expect(record.name, 'Pegaso');
      expect(record.statusLabel, 'Disponible');
      expect(record.isAvailable, true);
    });

    test('maps resting equine with restUntil', () {
      final equine = Equine(
        id: 'e2',
        name: 'Descanso',
        operationalStatus: EquineOperationalStatus.resting,
        restUntil: DateTime(2026, 6, 5),
      );
      final record = EquineMapper.domainToRecord(equine);
      expect(record.statusLabel, 'Descanso');
      expect(record.summary, contains('05/06'));
    });
  });

  group('EquineMapper.domainToDetailRecord', () {
    test('maps Equine to EquineDetailRecord with all fields', () {
      final equine = Equine(
        id: 'e1',
        name: 'Pegaso',
        species: 'horse',
        breed: 'Andaluz',
        sex: 'male',
        weightKg: 450.0,
        operationalStatus: EquineOperationalStatus.available,
        experienceFit: EquineExperienceFit.intermediate,
      );
      final detail = EquineMapper.domainToDetailRecord(equine);
      expect(detail.id, 'e1');
      expect(detail.name, 'Pegaso');
      expect(detail.species, 'horse');
      expect(detail.breed, 'Andaluz');
      expect(detail.statusLabel, 'Disponible');
    });
  });

  group('EquineMapper.timelineEntryDtoToDomain', () {
    test('maps timeline DTO correctly', () {
      final dto = EquineTimelineEntryDto(
        id: 'log-1',
        source: 'service_log',
        eventType: 'arrival',
        happenedAt: '2026-06-01T10:00:00Z',
        title: 'Llegada a la finca',
        reservationId: 'res-001',
        notes: 'Sin novedades',
      );
      final entry = EquineMapper.timelineEntryDtoToDomain(dto);
      expect(entry.id, 'log-1');
      expect(entry.eventType, 'arrival');
      expect(entry.title, 'Llegada a la finca');
      expect(entry.reservationId, 'res-001');
      expect(entry.notes, 'Sin novedades');
    });

    test('handles missing optional fields', () {
      final dto = EquineTimelineEntryDto(
        id: 'log-2',
        source: 'service_log',
        eventType: 'checkpoint',
        happenedAt: '2026-06-01T12:00:00Z',
        title: 'Punto de control',
      );
      final entry = EquineMapper.timelineEntryDtoToDomain(dto);
      expect(entry.id, 'log-2');
      expect(entry.reservationId, isNull);
      expect(entry.notes, isNull);
    });
  });

  group('EquineMapper.timelineEntryToLogbookEntry', () {
    test('maps arrival entry to completed state', () {
      final entry = EquineTimelineEntry(
        id: 'log-1',
        source: 'service_log',
        eventType: 'arrival',
        happenedAt: DateTime(2026, 6, 1, 10),
        title: 'Llegada',
      );
      final logEntry = EquineMapper.timelineEntryToLogbookEntry(entry);
      expect(logEntry.title, 'Llegada');
      expect(logEntry.dateLabel, '01/06/2026 · 10:00');
    });

    test('maps incident to warning state', () {
      final entry = EquineTimelineEntry(
        id: 'log-2',
        source: 'service_log',
        eventType: 'incident',
        happenedAt: DateTime(2026, 6, 1),
        title: 'Incidencia',
        notes: 'Tropiezó',
      );
      final logEntry = EquineMapper.timelineEntryToLogbookEntry(entry);
      expect(logEntry.observations, 'Tropiezó');
    });

    test('surfaces structured detail for a care event', () {
      final entry = EquineTimelineEntry(
        id: 'evt-1',
        source: 'equine_event',
        eventType: 'weight',
        happenedAt: DateTime(2026, 6, 2, 9),
        title: 'Control de peso',
        performedBy: 'Vet. Ana',
        measuredWeightKg: 420,
      );
      final logEntry = EquineMapper.timelineEntryToLogbookEntry(entry);
      final details = logEntry.details;
      expect(details, isNotNull);
      String valueFor(String label) =>
          details!.firstWhere((d) => d.label == label).value;
      expect(valueFor('Tipo'), 'Peso');
      expect(valueFor('Realizado por'), 'Vet. Ana');
      expect(valueFor('Peso'), '420 kg');
      // El badge lleva el tipo de evento cuando no está pendiente.
      expect(logEntry.badge, isNotNull);
    });

    test('flags pending sync entries in the badge', () {
      final entry = EquineTimelineEntry(
        id: 'evt-2',
        source: 'equine_event',
        eventType: 'note',
        happenedAt: DateTime(2026, 6, 3, 8),
        title: 'Nota',
        syncPending: true,
      );
      final logEntry = EquineMapper.timelineEntryToLogbookEntry(entry);
      expect(logEntry.badge?.label, 'Pendiente');
    });
  });
}
