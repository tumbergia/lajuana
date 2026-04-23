import 'dart:async' show StreamSubscription, unawaited;

import 'package:flutter/foundation.dart';

import '../application/bootstrap_session_use_case.dart';
import '../application/change_password_use_case.dart';
import '../application/enter_local_mode_use_case.dart';
import '../application/get_current_local_session_use_case.dart';
import '../application/logout_use_case.dart';
import '../application/refresh_session_use_case.dart';
import '../application/register_use_case.dart';
import '../application/sign_in_use_case.dart';
import '../application/sync_profile_from_remote_use_case.dart';
import '../domain/auth_enums.dart';
import '../domain/auth_models.dart';
import '../infrastructure/connectivity/network_models.dart';
import '../infrastructure/connectivity/network_status_resolver.dart';

class AuthController extends ChangeNotifier {
  AuthController({
    required BootstrapSessionUseCase bootstrapSessionUseCase,
    required SignInUseCase signInUseCase,
    required RefreshSessionUseCase refreshSessionUseCase,
    required LogoutUseCase logoutUseCase,
    required RegisterUseCase registerUseCase,
    required ChangePasswordUseCase changePasswordUseCase,
    required SyncProfileFromRemoteUseCase syncProfileFromRemoteUseCase,
    required GetCurrentLocalSessionUseCase getCurrentLocalSessionUseCase,
    required EnterLocalModeUseCase enterLocalModeUseCase,
    required NetworkStatusResolver networkStatusResolver,
  }) : _bootstrapSessionUseCase = bootstrapSessionUseCase,
       _signInUseCase = signInUseCase,
       _refreshSessionUseCase = refreshSessionUseCase,
       _logoutUseCase = logoutUseCase,
       _registerUseCase = registerUseCase,
       _changePasswordUseCase = changePasswordUseCase,
       _syncProfileFromRemoteUseCase = syncProfileFromRemoteUseCase,
       _getCurrentLocalSessionUseCase = getCurrentLocalSessionUseCase,
       _enterLocalModeUseCase = enterLocalModeUseCase,
       _networkStatusResolver = networkStatusResolver;

  final BootstrapSessionUseCase _bootstrapSessionUseCase;
  final SignInUseCase _signInUseCase;
  final RefreshSessionUseCase _refreshSessionUseCase;
  final LogoutUseCase _logoutUseCase;
  final RegisterUseCase _registerUseCase;
  final ChangePasswordUseCase _changePasswordUseCase;
  final SyncProfileFromRemoteUseCase _syncProfileFromRemoteUseCase;
  final GetCurrentLocalSessionUseCase _getCurrentLocalSessionUseCase;
  final EnterLocalModeUseCase _enterLocalModeUseCase;
  final NetworkStatusResolver _networkStatusResolver;

  StreamSubscription<NetworkStatus>? _networkSub;
  bool _didStart = false;

  bool isBootstrapping = true;
  bool isLoading = false;
  NetworkStatus networkStatus = const NetworkStatus(
    linkType: LinkType.other,
    backendReachability: BackendReachability.unknown,
  );
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

    networkStatus = await _networkStatusResolver.current();
    _networkSub = _networkStatusResolver.observe().listen(_onNetworkStatus);

    try {
      final snapshot = await _bootstrapSessionUseCase();
      _applySnapshot(snapshot);
      _clearError();
    } on AuthFailure catch (failure) {
      _applyFailure(failure);
    } finally {
      isBootstrapping = false;
      notifyListeners();
    }
  }

  void _onNetworkStatus(NetworkStatus next) {
    networkStatus = next;
    notifyListeners();
    if (next.linkType != LinkType.offline &&
        authState == LocalAuthState.signedInLocalUnverified) {
      unawaited(refreshRequested());
    }
  }

  Future<void> loginSubmitted({
    required String email,
    required String password,
  }) async {
    _startLoading();
    try {
      final snapshot = await _signInUseCase(email: email, password: password);
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
      await _logoutUseCase();
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
      final snapshot = await _refreshSessionUseCase();
      _applySnapshot(snapshot);
      _clearError();
    } on AuthFailure catch (failure) {
      _applyFailure(failure);
    } finally {
      _stopLoading();
    }
  }

  /// GET /auth/me (y reintento vía refresh si 401). No usar en bucle.
  Future<void> profileRefreshRequested() async {
    if (networkStatus.linkType == LinkType.offline) return;
    if (authState != LocalAuthState.signedInVerified) return;
    _startLoading();
    try {
      final snapshot = await _syncProfileFromRemoteUseCase();
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
        return 'No fue posible alcanzar el servidor';
      case 'network.timeout':
        return 'El servidor no respondio a tiempo';
      case 'network.http_error':
        return 'Hubo un error de comunicacion con el servidor';
      case 'network.invalid_response':
        return 'Respuesta invalida del servidor';
      case 'network.invalid_payload':
        return 'Datos invalidos del servidor';
      case 'auth.requires_internet':
        return 'Esta operacion requiere conexion real con el servidor';
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
    _networkSub?.cancel();
    super.dispose();
  }
}
