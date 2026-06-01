import 'package:flutter/foundation.dart';

import '../../../../app/widgets/app_badge.dart';
import '../../domain/repositories/equine_repository.dart';
import '../../infrastructure/mappers/equine_mapper.dart';
import '../models/equine_view_models.dart';

enum EquinesSubroute { resumen, historial, disponibilidad, cuidado }

enum EquinesLoadState { idle, loading, success, error, empty }

class EquinesController extends ChangeNotifier {
  EquinesController({required EquineRepository repository})
      : _repository = repository;

  final EquineRepository _repository;

  EquinesSubroute _subroute = EquinesSubroute.resumen;
  EquinesLoadState _loadState = EquinesLoadState.idle;
  String _errorMessage = '';
  List<EquineRecord> _records = const [];
  List<EquineRecord> _allRecords = const [];

  EquinesSubroute get subroute => _subroute;
  EquinesLoadState get loadState => _loadState;
  String get errorMessage => _errorMessage;
  List<EquineRecord> get records => _records;

  void selectSubrouteByIndex(int index) {
    final next = EquinesSubroute.values[index];
    if (_subroute == next) return;
    _subroute = next;
    _applyFilter();
    notifyListeners();
  }

  void reset() {
    if (_subroute == EquinesSubroute.resumen) return;
    _subroute = EquinesSubroute.resumen;
    _applyFilter();
    notifyListeners();
  }

  Future<void> loadEquines() async {
    _loadState = EquinesLoadState.loading;
    _errorMessage = '';
    notifyListeners();

    try {
      final equines = await _repository.listEquines();
      if (equines.isEmpty) {
        _allRecords = const [];
        _records = const [];
        _loadState = EquinesLoadState.empty;
      } else {
        _allRecords =
            equines.map(EquineMapper.domainToRecord).toList(growable: false);
        _applyFilter();
        _loadState = EquinesLoadState.success;
      }
    } catch (e) {
      _errorMessage = e.toString();
      _loadState = EquinesLoadState.error;
    }
    notifyListeners();
  }

  void _applyFilter() {
    switch (_subroute) {
      case EquinesSubroute.resumen:
        _records = _allRecords;
      case EquinesSubroute.historial:
        // Historial: timeline — filtramos solo los que tienen lastServiceAt.
        _records = _allRecords;
      case EquinesSubroute.disponibilidad:
        _records = _allRecords
            .where((r) =>
                r.statusTone == AppBadgeTone.success ||
                r.statusTone == AppBadgeTone.primary)
            .toList(growable: false);
      case EquinesSubroute.cuidado:
        _records = _allRecords
            .where((r) =>
                r.statusTone == AppBadgeTone.warning ||
                r.statusTone == AppBadgeTone.danger)
            .toList(growable: false);
    }
  }
}
