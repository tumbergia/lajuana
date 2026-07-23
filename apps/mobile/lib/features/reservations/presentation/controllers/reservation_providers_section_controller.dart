import 'package:flutter/foundation.dart';

import 'package:mobile/app/errors/user_facing_error.dart';
import 'package:mobile_domain/src/reservations/reservation_provider_item.dart';
import 'package:mobile_domain/src/reservations/reservations_repository.dart';

enum ReservationProvidersLoadState { initial, loading, loaded, error, saving }

class ReservationProvidersSectionController extends ChangeNotifier {
  ReservationProvidersSectionController({
    required ReservationsRepository repository,
  }) : _repository = repository;

  final ReservationsRepository _repository;

  ReservationProvidersLoadState state = ReservationProvidersLoadState.initial;
  List<ReservationProviderItem> items = const [];
  String? errorMessage;
  String? reservationId;

  Future<void> load(String reservationId) async {
    this.reservationId = reservationId;
    state = ReservationProvidersLoadState.loading;
    errorMessage = null;
    notifyListeners();

    try {
      items = await _repository.getReservationProviders(reservationId);
      state = ReservationProvidersLoadState.loaded;
    } catch (error) {
      state = ReservationProvidersLoadState.error;
      errorMessage = userFacingError(
        error,
        fallback: 'No se pudieron cargar los proveedores de la reserva.',
      );
    }
    notifyListeners();
  }

  Future<List<ProviderCatalogItem>> loadCatalog({String? query}) {
    return _repository.listProviders(query: query, isActive: true);
  }

  Future<bool> addProvider({
    required String providerId,
    String? serviceLabel,
    String? notes,
  }) async {
    final id = reservationId;
    if (id == null) return false;

    state = ReservationProvidersLoadState.saving;
    notifyListeners();
    try {
      final created = await _repository.createReservationProvider(
        reservationId: id,
        providerId: providerId,
        serviceLabel: serviceLabel,
        notes: notes,
      );
      items = [...items, created];
      state = ReservationProvidersLoadState.loaded;
      notifyListeners();
      return true;
    } catch (error) {
      errorMessage = userFacingError(
        error,
        fallback: 'No se pudo agregar el proveedor.',
      );
      state = ReservationProvidersLoadState.error;
      notifyListeners();
      return false;
    }
  }

  Future<bool> updateProvider({
    required String reservationProviderId,
    String? serviceLabel,
    String? notes,
    String? status,
  }) async {
    final id = reservationId;
    if (id == null) return false;

    state = ReservationProvidersLoadState.saving;
    notifyListeners();
    try {
      final updated = await _repository.updateReservationProvider(
        reservationId: id,
        reservationProviderId: reservationProviderId,
        serviceLabel: serviceLabel,
        notes: notes,
        status: status,
      );
      items = [
        for (final item in items)
          if (item.reservationProviderId == reservationProviderId)
            updated
          else
            item,
      ];
      state = ReservationProvidersLoadState.loaded;
      notifyListeners();
      return true;
    } catch (error) {
      errorMessage = userFacingError(
        error,
        fallback: 'No se pudo actualizar el proveedor.',
      );
      state = ReservationProvidersLoadState.error;
      notifyListeners();
      return false;
    }
  }

  Future<bool> removeProvider(String reservationProviderId) async {
    final id = reservationId;
    if (id == null) return false;

    state = ReservationProvidersLoadState.saving;
    notifyListeners();
    try {
      await _repository.deleteReservationProvider(
        reservationId: id,
        reservationProviderId: reservationProviderId,
      );
      items = items
          .where((item) => item.reservationProviderId != reservationProviderId)
          .toList(growable: false);
      state = ReservationProvidersLoadState.loaded;
      notifyListeners();
      return true;
    } catch (error) {
      errorMessage = userFacingError(
        error,
        fallback: 'No se pudo quitar el proveedor.',
      );
      state = ReservationProvidersLoadState.error;
      notifyListeners();
      return false;
    }
  }
}
