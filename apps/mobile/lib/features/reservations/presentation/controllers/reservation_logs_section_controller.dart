import 'dart:typed_data';

import 'package:flutter/foundation.dart';

import 'package:mobile_domain/src/reservations/reservation_log_note_detail.dart';
import 'package:mobile_domain/src/reservations/reservation_log_photo_input.dart';
import 'package:mobile_domain/src/reservations/reservation_log_photo_upload.dart';
import 'package:mobile_domain/src/reservations/reservation_timeline_entry.dart';
import 'package:mobile_domain/src/reservations/reservations_repository.dart';

enum ReservationLogsLoadState { initial, loading, loaded, error, saving }

/// Estado de la subruta Bitácora en detalle de reserva.
class ReservationLogsSectionController extends ChangeNotifier {
  ReservationLogsSectionController({required ReservationsRepository repository})
    : _repository = repository;

  final ReservationsRepository _repository;

  ReservationLogsLoadState state = ReservationLogsLoadState.initial;
  List<ReservationTimelineEntry> entries = const [];
  String? errorMessage;
  String? reservationId;

  Future<void> load(String reservationId) async {
    this.reservationId = reservationId;
    state = ReservationLogsLoadState.loading;
    errorMessage = null;
    notifyListeners();

    try {
      entries = await _repository.getReservationTimeline(reservationId);
      state = ReservationLogsLoadState.loaded;
    } catch (error) {
      state = ReservationLogsLoadState.error;
      errorMessage = error.toString();
    }
    notifyListeners();
  }

  Future<ReservationLogNoteDetail?> loadNoteForEdit(String logId) async {
    try {
      return await _repository.getReservationLogNote(logId);
    } catch (error) {
      errorMessage = error.toString();
      notifyListeners();
      return null;
    }
  }

  Future<ReservationLogPhotoUpload?> uploadPhoto({
    required Uint8List bytes,
    required String filename,
    required String contentType,
  }) async {
    final id = reservationId;
    if (id == null) return null;

    try {
      return await _repository.uploadReservationLogPhoto(
        reservationId: id,
        bytes: bytes,
        filename: filename,
        contentType: contentType,
      );
    } catch (error) {
      errorMessage = error.toString();
      notifyListeners();
      return null;
    }
  }

  Future<Uint8List?> downloadPhoto({
    required String logId,
    required int photoIndex,
  }) async {
    try {
      return await _repository.downloadReservationLogPhoto(
        logId: logId,
        photoIndex: photoIndex,
      );
    } catch (error) {
      errorMessage = error.toString();
      notifyListeners();
      return null;
    }
  }

  Future<bool> createNote(
    String text, {
    List<ReservationLogPhotoInput> photos = const [],
  }) async {
    final id = reservationId;
    if (id == null || text.trim().isEmpty) return false;

    state = ReservationLogsLoadState.saving;
    notifyListeners();
    try {
      await _repository.createReservationLogNote(
        reservationId: id,
        notes: text.trim(),
        photos: photos,
      );
      await load(id);
      return true;
    } catch (error) {
      state = ReservationLogsLoadState.error;
      errorMessage = error.toString();
      notifyListeners();
      return false;
    }
  }

  Future<bool> updateNote({
    required String logId,
    required String text,
    List<ReservationLogPhotoInput>? photos,
  }) async {
    final id = reservationId;
    if (id == null || text.trim().isEmpty) return false;

    state = ReservationLogsLoadState.saving;
    notifyListeners();
    try {
      await _repository.updateReservationLogNote(
        logId: logId,
        notes: text.trim(),
        photos: photos,
      );
      await load(id);
      return true;
    } catch (error) {
      state = ReservationLogsLoadState.error;
      errorMessage = error.toString();
      notifyListeners();
      return false;
    }
  }

  Future<bool> deleteEntry(String logId) async {
    final id = reservationId;
    if (id == null) return false;

    state = ReservationLogsLoadState.saving;
    notifyListeners();
    try {
      await _repository.deleteReservationLogEntry(logId: logId);
      await load(id);
      return true;
    } catch (error) {
      state = ReservationLogsLoadState.error;
      errorMessage = error.toString();
      notifyListeners();
      return false;
    }
  }
}
