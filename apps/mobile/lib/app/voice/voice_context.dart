enum VoiceContext { inicio, reservas, equinos, clientes, mas }

extension VoiceContextX on VoiceContext {
  String get label {
    switch (this) {
      case VoiceContext.inicio:
        return 'Inicio';
      case VoiceContext.reservas:
        return 'Reservas';
      case VoiceContext.equinos:
        return 'Equinos';
      case VoiceContext.clientes:
        return 'Clientes';
      case VoiceContext.mas:
        return 'Más';
    }
  }

  String get guidanceText {
    switch (this) {
      case VoiceContext.inicio:
        return 'Toca para hablar';
      case VoiceContext.reservas:
        return 'Habla sobre reservas';
      case VoiceContext.equinos:
        return 'Habla sobre equinos';
      case VoiceContext.clientes:
        return 'Habla sobre clientes';
      case VoiceContext.mas:
        return 'Habla para navegar';
    }
  }

  String get transcriptHint {
    switch (this) {
      case VoiceContext.inicio:
        return 'Lo que digas aparecerá aquí';
      case VoiceContext.reservas:
        return 'Ej: mostrar pendientes o crear reserva';
      case VoiceContext.equinos:
        return 'Ej: ver historial o registrar actividad';
      case VoiceContext.clientes:
        return 'Ej: buscar cliente o registrar participante';
      case VoiceContext.mas:
        return 'Ej: abrir configuración o reportes';
    }
  }
}
