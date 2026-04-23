class AuthFeatureFlags {
  const AuthFeatureFlags._();

  static const bool enableRegister = bool.fromEnvironment(
    'ENABLE_AUTH_REGISTER',
    defaultValue: false,
  );
}
