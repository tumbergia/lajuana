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

  String? _selectedEquineId;
  EquineDetailRecord? _selectedDetail;
  EquinesLoadState _detailLoadState = EquinesLoadState.idle;
  String _detailErrorMessage = '';

  EquinesSubroute get subroute => _subroute;
  EquinesLoadState get loadState => _loadState;
  String get errorMessage => _errorMessage;
  List<EquineRecord> get records => _records;
  String? get selectedEquineId => _selectedEquineId;
  EquineDetailRecord? get selectedDetail => _selectedDetail;
  EquinesLoadState get detailLoadState => _detailLoadState;
  String get detailErrorMessage => _detailErrorMessage;

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

  void selectEquine(String id) {
    if (_selectedEquineId == id) return;
    _selectedEquineId = id;
    _selectedDetail = null;
    _detailLoadState = EquinesLoadState.loading;
    notifyListeners();
    loadSelectedDetail();
  }

  Future<void> loadSelectedDetail() async {
    if (_selectedEquineId == null) return;
    _detailLoadState = EquinesLoadState.loading;
    notifyListeners();
    try {
      final equine = await _repository.getEquineById(_selectedEquineId!);
      _selectedDetail = EquineMapper.domainToDetailRecord(equine);
      _detailLoadState = EquinesLoadState.success;
    } catch (e) {
      _detailErrorMessage = e.toString();
      _detailLoadState = EquinesLoadState.error;
    }
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
        _selectedEquineId = null;
        _selectedDetail = null;
        _detailLoadState = EquinesLoadState.idle;
        _loadState = EquinesLoadState.empty;
      } else {
        _allRecords =
            equines.map(EquineMapper.domainToRecord).toList(growable: false);
        _applyFilter();
        _loadState = EquinesLoadState.success;
        // Auto-select first equine after load.
        if (_selectedEquineId == null) {
          _selectedEquineId = _records.first.id;
        }
        // Trigger detail load for selected equine.
        loadSelectedDetail();
      }
    } catch (e) {
      _errorMessage = e.toString();
      _selectedEquineId = null;
      _selectedDetail = null;
      _detailLoadState = EquinesLoadState.idle;
      _loadState = EquinesLoadState.error;
    }
    notifyListeners();
  }

  Future<bool> createEquine(Map<String, dynamic> data) async {
    try {
      await _repository.createEquine(data);
      await loadEquines(); // reload list
      return true;
    } catch (e) {
      _errorMessage = e.toString();
      _loadState = EquinesLoadState.error;
      notifyListeners();
      return false;
    }
  }

  Future<bool> updateEquine(String equineId, Map<String, dynamic> data) async {
    try {
      await _repository.updateEquine(equineId, data);
      // Reload detail
      if (_selectedEquineId == equineId) {
        await loadSelectedDetail();
      }
      await loadEquines(); // refresh list
      return true;
    } catch (e) {
      _detailErrorMessage = e.toString();
      _detailLoadState = EquinesLoadState.error;
      notifyListeners();
      return false;
    }
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
