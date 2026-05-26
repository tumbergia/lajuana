import 'dart:typed_data';

/// Stub: no-op fallback when neither io nor html are available.
bool saveFile(Uint8List bytes, String filename, String contentType) {
  throw UnsupportedError('saveFile no disponible en esta plataforma.');
}
