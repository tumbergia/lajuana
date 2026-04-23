/// Etiquetas de rol de usuario en UI (alineado con [UserRole] de la API: admin, guide, unassigned).
String displayUserRoleLabel(String? role) {
  if (role == null || role.trim().isEmpty) return 'Sin rol';
  switch (role.trim().toLowerCase()) {
    case 'unassigned':
      return 'Sin rol';
    case 'admin':
      return 'Administrador';
    case 'guide':
      return 'Guía';
    default:
      return _prettifyUnknownRoleValue(role.trim());
  }
}

String _prettifyUnknownRoleValue(String raw) {
  final parts = raw.split('_').where((s) => s.isNotEmpty);
  if (parts.isEmpty) return raw;
  return parts
      .map(
        (p) => p.isEmpty
            ? p
            : '${p[0].toUpperCase()}${p.length > 1 ? p.substring(1).toLowerCase() : ''}',
      )
      .join(' ');
}
