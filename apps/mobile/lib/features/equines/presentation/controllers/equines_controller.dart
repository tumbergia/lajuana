import 'package:flutter/foundation.dart';

import '../../domain/models/equine.dart';
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

  /// Domain objects cacheados para derivar detail sin request extra.
  List<Equine> _allEquines = const [];

  String? _selectedEquineId;
  EquineDetailRecord? _selectedDetail;

  EquinesSubroute get subroute => _subroute;
  EquinesLoadState get loadState => _loadState;
  String get errorMessage => _errorMessage;
  List<EquineRecord> get records => _records;
  String? get selectedEquineId => _selectedEquineId;
  EquineDetailRecord? get selectedDetail => _selectedDetail;

  /// Siempre success porque el detail se deriva de memoria (no hay request).
  EquinesLoadState get detailLoadState => EquinesLoadState.success;
  String get detailErrorMessage => '';

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
    _selectedDetail = _buildDetailFromMemory(id);
    notifyListeners();
  }

  EquineDetailRecord? _buildDetailFromMemory(String id) {
    try {
      final equine = _allEquines.firstWhere((e) => e.id == id);
      return EquineMapper.domainToDetailRecord(equine);
    } catch (_) {
      return null;
    }
  }

  /// Expone buildDetailFromMemory para uso externo (ej. refresh post-update).
  void refreshSelectedDetail() {
    if (_selectedEquineId == null) return;
    _selectedDetail = _buildDetailFromMemory(_selectedEquineId!);
    notifyListeners();
  }

  Future<void> loadEquines() async {
    _loadState = EquinesLoadState.loading;
    _errorMessage = '';
    notifyListeners();

    try {
      final equines = await _repository.listEquines();
      if (equines.isEmpty) {
        _allEquines = const [];
        _allRecords = const [];
        _records = const [];
        _selectedEquineId = null;
        _selectedDetail = null;
        _loadState = EquinesLoadState.empty;
      } else {
        _allEquines = equines;
        _allRecords =
            equines.map(EquineMapper.domainToRecord).toList(growable: false);
        _applyFilter();
        _loadState = EquinesLoadState.success;
        // Auto-select first equine — detail se deriva de memoria, sin request.
        if (_selectedEquineId == null) {
          _selectedEquineId = _records.first.id;
          _selectedDetail = _buildDetailFromMemory(_selectedEquineId!);
        }
      }
    } catch (e) {
      _errorMessage = e.toString();
      _selectedEquineId = null;
      _selectedDetail = null;
      _loadState = EquinesLoadState.error;
    }
    notifyListeners();
  }

  Future<bool> createEquine(Map<String, dynamic> data) async {
    try {
      await _repository.createEquine(data);
      await loadEquines(); // reload list (incluye detail desde memoria)
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
      await loadEquines(); // refresh list (incluye detail desde memoria)
      return true;
    } catch (e) {
      _errorMessage = e.toString();
      _loadState = EquinesLoadState.error;
      notifyListeners();
      return false;
    }
  }

  void _applyFilter() {
    switch (_subroute) {
      case EquinesSubroute.resumen:
        _records = _allRecords;
      case EquinesSubroute.historial:
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
