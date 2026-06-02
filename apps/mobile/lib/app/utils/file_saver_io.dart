import 'dart:io';
import 'dart:typed_data';

import 'package:flutter/foundation.dart';

/// Save bytes to a temporary file (mobile/desktop).
///
/// Uses [Directory.systemTemp] instead of [Directory.current] for
/// cross-platform compatibility. Write is async to avoid blocking.
Future<bool> saveFile(Uint8List bytes, String filename, String contentType) async {
  try {
    final dir = Directory.systemTemp;
    final file = File('${dir.path}${Platform.pathSeparator}$filename');
    await file.writeAsBytes(bytes);
    debugPrint('[file_saver] Saved ${file.lengthSync()} bytes to ${file.path}');
    return true;
  } catch (e) {
    debugPrint('[file_saver] Failed to save file: $e');
    return false;
  }
}
