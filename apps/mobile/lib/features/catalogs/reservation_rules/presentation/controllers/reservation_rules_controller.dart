import 'dart:async' show unawaited;

import 'package:flutter/foundation.dart';

import 'package:mobile/app/errors/user_facing_error.dart';
import 'package:mobile/features/catalogs/data/catalogs_repository.dart';
import 'package:mobile/features/catalogs/reservation_rules/data/reservation_rules_repository.dart';
import 'package:mobile/features/catalogs/reservation_rules/domain/reservation_rules.dart';

class ReservationRulesController extends ChangeNotifier {
  ReservationRulesController({
    required ReservationRulesRepository repository,
    required CatalogsRepository catalogsRepository,
  }) : _repository = repository,
       _catalogsRepository = catalogsRepository;

  final ReservationRulesRepository _repository;
  final CatalogsRepository _catalogsRepository;

  bool isInitialLoading = false;
  bool isRefreshing = false;
  bool isSyncing = false;
  String? error;
  CatalogReservationRules? rules;

  bool get hasLocalData => rules != null;

  Future<void> loadLocalThenRefresh({bool refreshServer = true}) async {
    isInitialLoading = true;
    error = null;
    notifyListeners();
    try {
      rules = await _repository.get();
    } catch (e) {
      error = userFacingError(
        e,
        fallback: 'No se pudieron cargar las reglas de reserva.',
      );
    } finally {
      isInitialLoading = false;
      notifyListeners();
    }
    if (refreshServer) {
      unawaited(refreshFromServer());
    }
  }

  Future<void> refreshFromServer() async {
    if (isRefreshing) return;
    isRefreshing = true;
    error = null;
    notifyListeners();
    try {
      await _catalogsRepository.refreshReservationRulesFromServer();
      rules = await _repository.get();
    } catch (e) {
      error = userFacingError(
        e,
        fallback: 'No se pudieron actualizar las reglas de reserva.',
      );
    } finally {
      isRefreshing = false;
      notifyListeners();
    }
  }

  Future<void> update({
    required int minDaysInAdvance,
    required bool requirePaymentProofForConfirmation,
    required int reservationDraftTtlMinutes,
    required int minAge,
    required int maxAge,
  }) async {
    await _repository.update(
      minDaysInAdvance: minDaysInAdvance,
      requirePaymentProofForConfirmation: requirePaymentProofForConfirmation,
      reservationDraftTtlMinutes: reservationDraftTtlMinutes,
      minAge: minAge,
      maxAge: maxAge,
    );
    await loadLocalThenRefresh(refreshServer: false);
  }

  Future<void> syncNow() async {
    isSyncing = true;
    error = null;
    notifyListeners();
    try {
      await _catalogsRepository.syncNow();
      rules = await _repository.get();
    } catch (e) {
      error = userFacingError(
        e,
        fallback: 'No se pudieron sincronizar las reglas de reserva.',
      );
    } finally {
      isSyncing = false;
      notifyListeners();
    }
  }
}
