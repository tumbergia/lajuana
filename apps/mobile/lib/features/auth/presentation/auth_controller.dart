import 'dart:async' show StreamSubscription, unawaited;

import 'package:flutter/foundation.dart';

import 'package:mobile/features/auth/domain/auth_enums.dart';
import 'package:mobile/features/auth/domain/auth_models.dart';
import 'package:mobile/features/auth/domain/auth_repository.dart';
import 'package:mobile/features/auth/infrastructure/connectivity/network_models.dart';
import 'package:mobile/features/auth/infrastructure/connectivity/network_status_resolver.dart';

class AuthController extends ChangeNotifier {
  AuthController({
    required AuthRepository authRepository,
    required NetworkStatusResolver networkStatusResolver,
  })  : _authRepository = authRepository,
        _networkStatusResolver = networkStatusResolver;

  final AuthRepository _authRepository;
  final NetworkStatusResolver _networkStatusResolver;

  StreamSubscription<NetworkStatus>? _networkSub;
  bool _didStart = false;

  // TODO: Encapsulate into AuthState value object — direct public field
  // access is a temporary pattern used across many widgets.
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
      final snapshot = await _authRepository.bootstrapSession();
      _applySnapshot(snapshot);
      _clearError();
    } on AuthFailure catch (failure) {
      _applyFailure(failure);
    } catch (_) {
      // Excepción de red no mapeada (p.ej. ClientException): si hay sesión
      // local, entramos en modo offline en lugar de expulsar al login.
      final localSnapshot = await _authRepository.enterLocalMode();
      if (localSnapshot.hasLocalSession) {
        _applySnapshot(localSnapshot);
      }
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
      final snapshot = await _authRepository.signIn(email: email, password: password);
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
      await _authRepository.logout();
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
      final snapshot = await _authRepository.refreshSession();
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
      final snapshot = await _authRepository.syncProfileFromRemote();
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
      await _authRepository.register(
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
      await _authRepository.changePassword(
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
      final session = await _authRepository.getCurrentLocalSession();
      if (session == null) {
        throw AuthFailure(
          code: 'auth.local_session_unavailable',
          message: 'No hay sesion local disponible',
        );
      }
      final snapshot = await _authRepository.enterLocalMode();
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
