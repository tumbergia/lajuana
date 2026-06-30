import 'dart:typed_data';

import 'package:flutter_test/flutter_test.dart';
import 'package:mobile_domain/src/reservations/reservation_log_note_detail.dart';
import 'package:mobile_domain/src/reservations/reservation_log_photo_input.dart';
import 'package:mobile_domain/src/reservations/reservation_log_photo_upload.dart';
import 'package:mobile_domain/src/reservations/reservation_timeline_entry.dart';
import 'package:mobile_domain/src/reservations/reservations_repository.dart';
import 'package:mobile/features/reservations/presentation/controllers/reservation_logs_section_controller.dart';

class _FakeTimelineRepository implements ReservationsRepository {
  _FakeTimelineRepository({
    this.timeline = const [],
    this.throwOnLoad = false,
  });

  List<ReservationTimelineEntry> timeline;
  bool throwOnLoad;
  int createCount = 0;
  int deleteCount = 0;

  @override
  Future<List<ReservationTimelineEntry>> getReservationTimeline(
    String reservationId,
  ) async {
    if (throwOnLoad) throw Exception('Timeline error');
    return timeline;
  }

  @override
  Future<void> createReservationLogNote({
    required String reservationId,
    required String notes,
    List<ReservationLogPhotoInput> photos = const [],
  }) async {
    createCount++;
    timeline = [
      ReservationTimelineEntry(
        id: 'service_log:new',
        source: 'service_log',
        kind: 'note',
        happenedAt: DateTime(2026, 6, 2, 12),
        title: 'Nota manual',
        description: notes,
        editable: true,
        deletable: true,
        serviceLogId: 'log-new',
      ),
      ...timeline,
    ];
  }

  @override
  Future<void> updateReservationLogNote({
    required String logId,
    required String notes,
    List<ReservationLogPhotoInput>? photos,
  }) async {}

  @override
  Future<void> deleteReservationLogEntry({required String logId}) async {
    deleteCount++;
    timeline = timeline.where((e) => e.serviceLogId != logId).toList();
  }

  @override
  Future<ReservationLogNoteDetail> getReservationLogNote(String logId) async {
    return ReservationLogNoteDetail(id: logId, notes: '');
  }

  @override
  Future<ReservationLogPhotoUpload> uploadReservationLogPhoto({
    required String reservationId,
    required Uint8List bytes,
    required String filename,
    required String contentType,
  }) async {
    return ReservationLogPhotoUpload(
      storageKey: 'service_logs/$reservationId/test.jpg',
      filename: filename,
      contentType: contentType,
      sizeBytes: bytes.length,
    );
  }

  @override
  Future<Uint8List> downloadReservationLogPhoto({
    required String logId,
    required int photoIndex,
  }) async {
    return Uint8List(0);
  }

  @override
  dynamic noSuchMethod(Invocation invocation) => super.noSuchMethod(invocation);
}

void main() {
  group('ReservationLogsSectionController', () {
    test('load fetches timeline entries', () async {
      final repo = _FakeTimelineRepository(
        timeline: [
          ReservationTimelineEntry(
            id: 'audit:1',
            source: 'audit_log',
            kind: 'payment_proof.approved',
            happenedAt: DateTime(2026, 6, 1, 10),
            title: 'Pago aprobado',
          ),
        ],
      );
      final controller = ReservationLogsSectionController(repository: repo);

      await controller.load('res-1');

      expect(controller.state, ReservationLogsLoadState.loaded);
      expect(controller.entries, hasLength(1));
      expect(controller.entries.first.title, 'Pago aprobado');
    });

    test('createNote reloads timeline', () async {
      final repo = _FakeTimelineRepository();
      final controller = ReservationLogsSectionController(repository: repo);

      await controller.load('res-1');
      final ok = await controller.createNote('Cliente llegó tarde');

      expect(ok, isTrue);
      expect(repo.createCount, 1);
      expect(controller.entries.first.description, 'Cliente llegó tarde');
    });

    test('deleteEntry removes note', () async {
      final repo = _FakeTimelineRepository(
        timeline: [
          ReservationTimelineEntry(
            id: 'service_log:1',
            source: 'service_log',
            kind: 'note',
            happenedAt: DateTime(2026, 6, 2, 12),
            title: 'Nota manual',
            description: 'Borrar',
            serviceLogId: 'log-1',
            deletable: true,
          ),
        ],
      );
      final controller = ReservationLogsSectionController(repository: repo);

      await controller.load('res-1');
      final ok = await controller.deleteEntry('log-1');

      expect(ok, isTrue);
      expect(repo.deleteCount, 1);
      expect(controller.entries, isEmpty);
    });
  });
}
