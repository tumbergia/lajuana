import 'package:flutter/foundation.dart';

import '../../domain/models/assignment_board.dart';
import '../../domain/repositories/assignments_repository.dart';

/// State of the assignment board for a reservation.
enum BoardLoadState { initial, loading, loaded, error }

/// Controller for the assignment board screen.
class AssignmentBoardController extends ChangeNotifier {
  final AssignmentsRepository _repository;

  AssignmentBoardController({required AssignmentsRepository repository})
      : _repository = repository;

  BoardLoadState _state = BoardLoadState.initial;
  AssignmentBoard? _board;
  String? _error;
  String? _reservationId;

  BoardLoadState get state => _state;
  AssignmentBoard? get board => _board;
  String? get error => _error;
  bool get isLoading => _state == BoardLoadState.loading;

  /// Load the board for a given reservation.
  Future<void> load({
    required String reservationId,
  }) async {
    _reservationId = reservationId;
    _state = BoardLoadState.loading;
    _error = null;
    notifyListeners();

    try {
      _board = await _repository.getBoard(reservationId);
      _state = BoardLoadState.loaded;
    } catch (e) {
      _error = e.toString();
      _state = BoardLoadState.error;
    }
    notifyListeners();
  }

  /// Refresh current board.
  Future<void> refresh() async {
    if (_reservationId != null) {
      await load(reservationId: _reservationId!);
    }
  }
}
