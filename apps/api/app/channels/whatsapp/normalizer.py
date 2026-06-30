import re


def normalize_phone(phone: str) -> str:
    digits = re.sub(r"\D+", "", phone or "")
    if not digits:
        raise ValueError("empty_phone")
    return f"+{digits}"


def build_conversation_id(channel: str, normalized_phone: str) -> str:
    return f"{channel}:{normalized_phone}"


# WhatsApp interpreta markdown ligero en el cuerpo del mensaje:
#   *palabra*      -> negrita
#   _palabra_      -> cursiva
#   ~palabra~      -> tachado
#   ```palabra```  -> monoespaciado
# Cuando el LLM emite estos marcadores de forma no balanceada o por descuido,
# WhatsApp los renderiza como fragmentos sueltos que rompen la lectura y, en
# algunos clientes, insertan saltos de línea alrededor de cada acento
# (patrón observado que deforma "Básica" -> "B\nP\nsica" tras copiar/pegar).
# Para garantizar texto plano y legible, eliminamos aquí todo este markup.
_WHATSAPP_CODE_BLOCK = re.compile(r"```+")
_WHATSAPP_BOLD = re.compile(r"\*+([^*\n]+?)\*+")
_WHATSAPP_ITALIC = re.compile(r"(?<![\w])_([^_\n]+?)_(?![\w])")
_WHATSAPP_STRIKE = re.compile(r"(?<![\w])~([^~\n]+?)~(?![\w])")


def strip_whatsapp_markup(text: str) -> str:
    """Sanea el texto que se enviará a WhatsApp.

    - Elimina bloques monoespaciados ``\\`\\`\\`...\\`\\`\\` ``.
    - Desenvuelve negrita ``*x*`` / ``**x**`` conservando el contenido.
    - Desenvuelve cursiva ``_x_`` solo cuando rodea palabras (no en
      ``snake_case`` ni identificadores con ``_`` intermedios).
    - Desenvuelve tachado ``~x~`` de la misma forma.
    - Colapsa saltos de línea múltiples a un máximo de 2.
    - No altera acentos ni ningún otro carácter unicode.

    Devuelve el texto limpio listo para ``text.body``.
    """
    if not text:
        return text

    cleaned = _WHATSAPP_CODE_BLOCK.sub("", text)
    cleaned = _WHATSAPP_BOLD.sub(r"\1", cleaned)
    cleaned = _WHATSAPP_ITALIC.sub(r"\1", cleaned)
    cleaned = _WHATSAPP_STRIKE.sub(r"\1", cleaned)

    # Saltos de línea múltiples -> máximo un bloque en blanco (2 NL).
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)

    return cleaned.strip()
