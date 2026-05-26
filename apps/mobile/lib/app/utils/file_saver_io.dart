import 'dart:io';
import 'dart:typed_data';

/// Save bytes to the current working directory (desktop/mobile).
bool saveFile(Uint8List bytes, String filename, String contentType) {
  final dir = Directory.current;
  final file = File('${dir.path}${Platform.pathSeparator}$filename');
  file.writeAsBytesSync(bytes);
  return true;
}
