import 'dart:typed_data';

/// Stub: no-op fallback when neither io nor html are available.
Future<bool> saveFile(Uint8List bytes, String filename, String contentType) async {
  throw UnsupportedError('saveFile no disponible en esta plataforma.');
}
