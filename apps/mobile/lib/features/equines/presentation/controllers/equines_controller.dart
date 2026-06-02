import 'package:flutter/foundation.dart';

import '../../domain/models/equine.dart';
import '../../domain/models/equine_operational_status.dart';
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

  EquineOperationalStatus? _statusFilter;
  DateTime? _lastSyncedAt;

  String? _selectedEquineId;
  EquineDetailRecord? _selectedDetail;

  EquinesSubroute get subroute => _subroute;
  EquinesLoadState get loadState => _loadState;
  String get errorMessage => _errorMessage;
  List<EquineRecord> get records => _records;
  bool get hasAnyRecords => _allEquines.isNotEmpty;
  String? get selectedEquineId => _selectedEquineId;
  EquineDetailRecord? get selectedDetail => _selectedDetail;

  EquineMetrics get metrics {
    final total = _allEquines.length;
    if (total == 0) return const EquineMetrics(total: 0, available: 0, blocked: 0);
    var available = 0;
    var blocked = 0;
    for (final e in _allEquines) {
      if (e.isAvailable && e.operationalStatus == EquineOperationalStatus.available) {
        available++;
      } else if (e.operationalStatus == EquineOperationalStatus.unavailable ||
          e.operationalStatus == EquineOperationalStatus.injured ||
          e.operationalStatus == EquineOperationalStatus.retired ||
          e.operationalStatus == EquineOperationalStatus.restricted) {
        blocked++;
      }
    }
    return EquineMetrics(total: total, available: available, blocked: blocked);
  }

  DateTime? get lastSyncedAt => _lastSyncedAt;

  EquineOperationalStatus? get statusFilter => _statusFilter;

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

  void setStatusFilter(EquineOperationalStatus? status) {
    if (_statusFilter == status) return;
    _statusFilter = status;
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
        // Cargar última sincronización en background.
        loadLastSyncedAt();
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

  Future<void> loadLastSyncedAt() async {
    try {
      final dt = await _repository.getLastSyncedAt();
      if (dt != null) {
        _lastSyncedAt = dt;
        notifyListeners();
      }
    } catch (_) {
      // Ignorar errores de lectura de metadatos.
    }
  }

  void _applyFilter() {
    // Primero aplica filtro de subruta.
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
    // Luego aplica filtro de estado operativo si está activo.
    if (_statusFilter != null) {
      _records = _records.where((r) {
        // Buscar el equine correspondiente para obtener su estado operativo real.
        final equine = _allEquines.where((e) => e.id == r.id).firstOrNull;
        return equine?.operationalStatus == _statusFilter;
      }).toList(growable: false);
    }
  }
}
