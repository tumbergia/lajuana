/// Generic action state machine for controller operations.
///
/// Eliminates duplicated idle/loading/success/error patterns across
/// all action controllers (F2, W3.5 del plan de mejora).
///
/// Usage:
/// ```dart
/// ActionState<String> approveState = ActionState.idle();
/// approveState = ActionState.loading();
/// approveState = ActionState.success('ok');
/// approveState = ActionState.error('ERR_01', 'Something failed');
/// approveState = approveState.reset();
/// ```
enum ActionStatus { idle, loading, success, error }

class ActionState<T> {
  final ActionStatus status;
  final String? errorCode;
  final String? errorMessage;
  final T? data;

  const ActionState._({
    this.status = ActionStatus.idle,
    this.errorCode,
    this.errorMessage,
    this.data,
  });

  factory ActionState.idle() => const ActionState._();

  factory ActionState.loading() => const ActionState._(
        status: ActionStatus.loading,
      );

  factory ActionState.success([T? data]) => ActionState._(
        status: ActionStatus.success,
        data: data,
      );

  factory ActionState.error(String code, String message) => ActionState._(
        status: ActionStatus.error,
        errorCode: code,
        errorMessage: message,
      );

  bool get isIdle => status == ActionStatus.idle;
  bool get isLoading => status == ActionStatus.loading;
  bool get isSuccess => status == ActionStatus.success;
  bool get isError => status == ActionStatus.error;

  ActionState<T> reset() => ActionState.idle();
}
