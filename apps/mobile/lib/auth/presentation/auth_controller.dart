import 'dart:async';

import 'package:flutter/foundation.dart';

import '../application/bootstrap_session_use_case.dart';
import '../application/change_password_use_case.dart';
import '../application/enter_local_mode_use_case.dart';
import '../application/get_current_local_session_use_case.dart';
import '../application/logout_use_case.dart';
import '../application/refresh_session_use_case.dart';
import '../application/register_use_case.dart';
import '../application/sign_in_use_case.dart';
import '../domain/auth_enums.dart';
import '../domain/auth_models.dart';
import '../infrastructure/connectivity_service.dart';

class AuthController extends ChangeNotifier {
  AuthController({
    required BootstrapSessionUseCase bootstrapSessionUseCase,
    required SignInUseCase signInUseCase,
    required RefreshSessionUseCase refreshSessionUseCase,
    required LogoutUseCase logoutUseCase,
    required RegisterUseCase registerUseCase,
    required ChangePasswordUseCase changePasswordUseCase,
    required GetCurrentLocalSessionUseCase getCurrentLocalSessionUseCase,
    required EnterLocalModeUseCase enterLocalModeUseCase,
    required ConnectivityService connectivityService,
  }) : _bootstrapSessionUseCase = bootstrapSessionUseCase,
       _signInUseCase = signInUseCase,
       _refreshSessionUseCase = refreshSessionUseCase,
       _logoutUseCase = logoutUseCase,
       _registerUseCase = registerUseCase,
       _changePasswordUseCase = changePasswordUseCase,
       _getCurrentLocalSessionUseCase = getCurrentLocalSessionUseCase,
       _enterLocalModeUseCase = enterLocalModeUseCase,
       _connectivityService = connectivityService;

  final BootstrapSessionUseCase _bootstrapSessionUseCase;
  final SignInUseCase _signInUseCase;
  final RefreshSessionUseCase _refreshSessionUseCase;
  final LogoutUseCase _logoutUseCase;
  final RegisterUseCase _registerUseCase;
  final ChangePasswordUseCase _changePasswordUseCase;
  final GetCurrentLocalSessionUseCase _getCurrentLocalSessionUseCase;
  final EnterLocalModeUseCase _enterLocalModeUseCase;
  final ConnectivityService _connectivityService;

  StreamSubscription<ConnectivityState>? _connectivitySub;
  bool _didStart = false;

  bool isBootstrapping = true;
  bool isLoading = false;
  ConnectivityState connectivityState = ConnectivityState.offline;
  LocalAuthState authState = LocalAuthState.signedOut;
  UserLocal? currentUser;
  String? errorCode;
  String? errorMessage;
  String? noticeCode;
  String? noticeMessage;
  int errorEventId = 0;
  int noticeEventId = 0;
  bool isOfflineRestricted = false;
  bool hasLocalSession = false;
  bool hasPendingSync = false;

  Future<void> appStarted() async {
    if (_didStart) return;
    _didStart = true;
    isBootstrapping = true;
    notifyListeners();

    connectivityState = await _connectivityService.current();
    _connectivitySub = _connectivityService.observe().listen(
      connectivityChanged,
    );

    try {
      final snapshot = await _bootstrapSessionUseCase(connectivityState);
      _applySnapshot(snapshot);
      _clearError();
    } on AuthFailure catch (failure) {
      _applyFailure(failure);
    } finally {
      isBootstrapping = false;
      notifyListeners();
    }
  }

  Future<void> loginSubmitted({
    required String email,
    required String password,
  }) async {
    _startLoading();
    try {
      final snapshot = await _signInUseCase(
        email: email,
        password: password,
        connectivity: connectivityState,
      );
      _applySnapshot(snapshot);
      _clearError();
      noticeCode = null;
      noticeMessage = null;
    } on AuthFailure catch (failure) {
      _applyFailure(failure);
    } finally {
      _stopLoading();
    }
  }

  Future<void> logoutRequested() async {
    _startLoading();
    try {
      await _logoutUseCase(connectivity: connectivityState);
      authState = LocalAuthState.signedOut;
      currentUser = null;
      hasLocalSession = false;
      hasPendingSync = false;
      isOfflineRestricted = false;
      _clearError();
    } on AuthFailure catch (failure) {
      _applyFailure(failure);
    } finally {
      _stopLoading();
    }
  }

  Future<void> refreshRequested() async {
    _startLoading();
    try {
      final snapshot = await _refreshSessionUseCase(
        connectivity: connectivityState,
      );
      _applySnapshot(snapshot);
      _clearError();
    } on AuthFailure catch (failure) {
      _applyFailure(failure);
    } finally {
      _stopLoading();
    }
  }

  Future<void> sessionExpired() async {
    authState = LocalAuthState.invalid;
    currentUser = null;
    hasLocalSession = false;
    isOfflineRestricted = false;
    errorCode = 'auth.session_expired';
    errorMessage = 'Tu sesion expiro';
    errorEventId++;
    notifyListeners();
  }

  Future<void> connectivityChanged(ConnectivityState nextState) async {
    connectivityState = nextState;
    notifyListeners();
    if (nextState == ConnectivityState.online &&
        authState == LocalAuthState.signedInLocalUnverified) {
      await refreshRequested();
    }
  }

  Future<void> registerSubmitted({
    required String fullName,
    required String email,
    required String password,
  }) async {
    _startLoading();
    try {
      await _registerUseCase(
        fullName: fullName,
        email: email,
        password: password,
        connectivity: connectivityState,
      );
      noticeCode = 'auth.register_success';
      noticeMessage = 'Cuenta creada. Inicia sesion.';
      noticeEventId++;
      _clearError();
    } on AuthFailure catch (failure) {
      _applyFailure(failure);
    } finally {
      _stopLoading();
    }
  }

  Future<void> changePasswordSubmitted({
    required String currentPassword,
    required String newPassword,
  }) async {
    _startLoading();
    try {
      await _changePasswordUseCase(
        currentPassword: currentPassword,
        newPassword: newPassword,
        connectivity: connectivityState,
      );
      noticeCode = 'auth.password_changed';
      noticeMessage = 'Contrasena actualizada.';
      noticeEventId++;
      _clearError();
    } on AuthFailure catch (failure) {
      _applyFailure(failure);
      if (failure.statusCode == 401) {
        await sessionExpired();
      }
    } finally {
      _stopLoading();
    }
  }

  Future<void> enterLocalSessionRequested() async {
    _startLoading();
    try {
      final session = await _getCurrentLocalSessionUseCase();
      if (session == null) {
        throw AuthFailure(
          code: 'auth.local_session_unavailable',
          message: 'No hay sesion local disponible',
        );
      }
      final snapshot = await _enterLocalModeUseCase();
      _applySnapshot(snapshot);
      _clearError();
    } on AuthFailure catch (failure) {
      _applyFailure(failure);
    } finally {
      _stopLoading();
    }
  }

  String? messageForCode(String? code) {
    switch (code) {
      case 'auth.register_success':
        return 'Cuenta creada. Inicia sesion.';
      case 'auth.password_changed':
        return 'Contrasena actualizada.';
      case 'auth.invalid_credentials':
        return 'Credenciales invalidas';
      case 'common.validation_error':
        return 'Datos invalidos';
      case 'network.unavailable':
        return 'Sin conexion';
      case 'auth.requires_internet':
        return 'Requiere internet';
      case 'auth.session_expired':
        return 'Tu sesion expiro';
      case 'auth.local_session_unavailable':
        return 'No hay sesion local';
      default:
        return null;
    }
  }

  void _applySnapshot(AuthSessionSnapshot snapshot) {
    authState = snapshot.authState;
    currentUser = snapshot.currentUser;
    hasLocalSession = snapshot.hasLocalSession;
    hasPendingSync = snapshot.hasPendingSync;
    isOfflineRestricted = snapshot.isOfflineRestricted;
  }

  void _applyFailure(AuthFailure failure) {
    errorCode = failure.code;
    errorMessage = failure.message;
    noticeCode = null;
    noticeMessage = null;
    errorEventId++;
  }

  void _clearError() {
    errorCode = null;
    errorMessage = null;
  }

  void clearNotice() {
    noticeCode = null;
    noticeMessage = null;
    notifyListeners();
  }

  void _startLoading() {
    _clearError();
    noticeCode = null;
    noticeMessage = null;
    isLoading = true;
    notifyListeners();
  }

  void _stopLoading() {
    isLoading = false;
    notifyListeners();
  }

  @override
  void dispose() {
    _connectivitySub?.cancel();
    super.dispose();
  }
}
