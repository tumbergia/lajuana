import 'dart:html' as html;
import 'dart:typed_data';

/// Trigger a browser download via Blob + AnchorElement.
bool saveFile(Uint8List bytes, String filename, String contentType) {
  final blob = html.Blob([bytes], contentType);
  final url = html.Url.createObjectUrlFromBlob(blob);
  final anchor = html.AnchorElement(href: url)
    ..setAttribute('download', filename)
    ..style.display = 'none';
  html.document.body!.children.add(anchor);
  anchor.click();
  html.document.body!.children.remove(anchor);
  html.Url.revokeObjectUrl(url);
  return true;
}
