#!/usr/bin/env python3
"""
OpenAPI → Dart model generator.

Generates Dart model classes (with fromJson/toJson) from a FastAPI OpenAPI spec.

Usage:
    python tools/openapi_gen/generate_models.py --spec http://localhost:8000/openapi.json
    python tools/openapi_gen/generate_models.py --spec-file apps/api/openapi.json
    python tools/openapi_gen/generate_models.py --spec-file apps/api/openapi.json --filter Equine,Saddle

Output:
    packages/mobile_domain/lib/src/gen/<snake_case_name>.dart
    packages/mobile_domain/lib/src/gen/gen.dart (barrel)

Type mapping:
    Python → Dart
    str    → String
    int    → int
    float  → double
    bool   → bool
    Decimal→ double (with // Decimal comment)
    datetime → DateTime
    date   → DateTime (with // date-only comment)
    list[T]  → List<T>
    dict   → Map<String, dynamic>
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Optional

# ─── Type mapping ───────────────────────────────────────────────────────────

PYTHON_TO_DART = {
    "string": "String",
    "integer": "int",
    "number": "double",
    "boolean": "bool",
    "array": "List",
    "object": "Map<String, dynamic>",
}

# Enums we know about that should be emitted as Dart enums
KNOWN_ENUMS = {
    "EquineSpecies", "EquineSex", "EquineLocationStatus",
    "ReservationStatus", "AssignmentStatus", "SyncStatus",
    "LinkType", "BackendReachability", "LocalAuthState",
    "HealthStatus", "ServiceLogEventType",
}

# Schemas to skip (internal/utility types not useful as mobile models)
SKIP_SCHEMAS = {
    "ApiErrorResponse", "ApiSuccessResponse", "PaginationMeta",
    "ValidationError", "HttpError", "ErrorResponse",
    "BulkActionSchema", "BatchUpdateSchema", "BatchAssignmentItemSchema",
    "AdminAskRequest", "AskRequest", "AskResponse",
    "WhatsappWebhook", "WhatsappMessage",
    "ConversationSession",
    "SyncMetadata", "SyncDeltaRequest", "SyncDeltaResponse",
}

# Schema name suffix → Dart name mapping
SUFFIX_REMOVE = ["Schema", "Request", "Response"]


def to_dart_name(schema_name: str, all_schemas: set[str] | None = None) -> str:
    """Convert OpenAPI schema name to Dart class name.

    Avoids name collisions: if stripping a suffix would create a name that
    already exists as another schema (e.g. ParticipantFormLinkStatusResponse
    stripping to ParticipantFormLinkStatus which conflicts with the enum
    ParticipantFormLinkStatus), keep the suffix or append 'Model'.
    """
    name = schema_name
    for suffix in SUFFIX_REMOVE:
        if name.endswith(suffix) and len(name) > len(suffix):
            candidate = name[: -len(suffix)]
            # Check if stripped name would collide with another schema
            if all_schemas and candidate in all_schemas:
                # Name already exists as a different schema — keep the suffix
                pass
            else:
                name = candidate
    return name


def to_field_name(prop_name: str) -> str:
    """Convert snake_case to camelCase for Dart field names."""
    parts = prop_name.split("_")
    return parts[0] + "".join(p.capitalize() for p in parts[1:])


def resolve_ref(ref: str, spec: dict) -> dict:
    """Resolve a $ref like '#/components/schemas/EquineResponseSchema'."""
    if not ref:
        return {}
    path = ref.lstrip("#/").split("/")
    obj = spec
    for part in path:
        if isinstance(obj, dict):
            obj = obj.get(part, {})
        else:
            return {}
    return obj


def find_enum_schemas(spec: dict) -> set[str]:
    """Find all schemas that are string enums."""
    enums: set[str] = set()
    schemas = spec.get("components", {}).get("schemas", {})
    all_names: set[str] = set(schemas.keys())
    for name, schema in schemas.items():
        if schema.get("type") == "string" and "enum" in schema:
            enums.add(to_dart_name(name, all_names))
    return enums


def get_dart_type(
    prop_name: str,
    prop_schema: dict,
    spec: dict,
    schemas_in_scope: set[str],
    enum_names: set[str] | None = None,
    all_schema_names: set[str] | None = None,
) -> str:
    """Map an OpenAPI property schema to a Dart type string."""
    if enum_names is None:
        enum_names = find_enum_schemas(spec)
    if all_schema_names is None:
        all_schema_names = set(spec.get("components", {}).get("schemas", {}).keys())

    if "$ref" in prop_schema:
        resolved = resolve_ref(prop_schema["$ref"], spec)
        ref_name = prop_schema["$ref"].split("/")[-1]
        dart_name = to_dart_name(ref_name, all_schema_names)
        if resolved.get("type") == "string" and "enum" in resolved:
            return dart_name
        if dart_name in schemas_in_scope:
            return dart_name
        if resolved.get("type") in ("object",) or resolved.get("properties"):
            return dart_name
        # Fallback
        return "String"

    ptype = prop_schema.get("type", "string")
    fmt = prop_schema.get("format", "")

    if ptype == "string" and "enum" in prop_schema:
        return to_dart_name(prop_name)  # Inline enum

    if ptype == "string":
        if fmt in ("date-time", "datetime"):
            return "DateTime"
        if fmt == "date":
            return "DateTime"  # date-only
        return "String"

    if ptype == "integer":
        return "int"

    if ptype == "number":
        if fmt == "decimal":
            return "double"  # comment added later
        return "double"

    if ptype == "boolean":
        return "bool"

    if ptype == "array":
        items = prop_schema.get("items", {})
        inner = get_dart_type(prop_name, items, spec, schemas_in_scope)
        return f"List<{inner}>"

    if ptype == "object":
        if prop_schema.get("additionalProperties"):
            inner = "dynamic"
            if isinstance(prop_schema["additionalProperties"], dict):
                inner = get_dart_type(
                    prop_name, prop_schema["additionalProperties"], spec, schemas_in_scope
                )
            return f"Map<String, {inner}>"
        return "Map<String, dynamic>"

    return "dynamic"


def is_required(prop_name: str, required_list: list) -> bool:
    return prop_name in required_list


# ─── Dart code generation ───────────────────────────────────────────────────

def snake_to_dart_file(name: str) -> str:
    """Convert CamelCase to snake_case for file names."""
    result = re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()
    return result


def generate_enum(
    schema_name: str,
    schema: dict,
    spec: dict,
    all_schema_names: set[str] | None = None,
) -> str:
    """Generate a Dart enum from an OpenAPI schema with enum values."""
    if all_schema_names is None:
        all_schema_names = set(spec.get("components", {}).get("schemas", {}).keys())
    dart_name = to_dart_name(schema_name, all_schema_names)
    values = schema.get("enum", [])

    # Create enum key mapping
    key_map = {}
    for val in values:
        enum_key = val.upper() if val.isupper() else val.upper().replace("-", "_").replace(" ", "_")
        key_map[enum_key] = val

    lines = [f"/// AUTO-GENERATED from OpenAPI schema `{schema_name}`.", ""]
    lines.append(f"enum {dart_name} {{")
    for enum_key, val in key_map.items():
        lines.append(f"  @JsonValue('{val}')")
        lines.append(f"  {enum_key}({json.dumps(val)}),")
    lines.append(";")
    lines.append("")
    lines.append(f"  final String value;")
    lines.append(f"  const {dart_name}(this.value);")
    lines.append("}")
    lines.append("")
    lines.append(f"extension {dart_name}X on {dart_name} {{")
    lines.append(f"  String toJson() => value;")
    lines.append("}")
    lines.append("")
    lines.append(f"extension {dart_name}Parse on String {{")
    lines.append(f"  {dart_name} to{dart_name}() => {dart_name}.values.firstWhere(")
    lines.append(f"    (e) => e.value == this,")
    lines.append(f"    orElse: () => throw ArgumentError('Unknown {dart_name}: ${{this}}'),")
    lines.append(f"  );")
    lines.append("}")
    lines.append("")

    return "\n".join(lines)


def generate_model(
    schema_name: str,
    schema: dict,
    spec: dict,
    schemas_in_scope: set[str],
    enum_names: set[str] | None = None,
    all_schema_names: set[str] | None = None,
) -> Optional[str]:
    """Generate a Dart model class from an OpenAPI schema."""
    if enum_names is None:
        enum_names = find_enum_schemas(spec)
    if all_schema_names is None:
        all_schema_names = set(spec.get("components", {}).get("schemas", {}).keys())

    if schema.get("type") == "string" and "enum" in schema:
        return generate_enum(schema_name, schema, spec, all_schema_names)

    if schema.get("type") != "object" and not schema.get("properties"):
        return None

    dart_name = to_dart_name(schema_name, all_schema_names)
    properties = schema.get("properties", {})
    required_list = schema.get("required", [])

    if not properties:
        return None

    # Track which other generated files this model depends on
    needed_imports: set[str] = set()
    # All generated class names (both enums and models) in this run
    all_generated: set[str] = schemas_in_scope | enum_names

    lines = [f"/// AUTO-GENERATED from OpenAPI schema `{schema_name}`.", ""]

    # ── Fields (first pass to collect imports) ──
    for pname, pschema in properties.items():
        dtype = get_dart_type(pname, pschema, spec, schemas_in_scope, enum_names)
        # Extract base type name (strip List<>, trailing ?)
        base = dtype
        if base.startswith("List<"):
            base = base[5:-1]
        if base.endswith("?"):
            base = base[:-1]
        # If base type is another generated model (and not self), add import
        if base in all_generated and base != dart_name:
            needed_imports.add(base)

    # Add imports for referenced generated files
    for ref_name in sorted(needed_imports):
        file_name = snake_to_dart_file(ref_name)
        lines.append(f"import '{file_name}.dart';")
    if needed_imports:
        lines.append("")

    lines.append(f"class {dart_name} {{")
    lines.append("")

    # ── Fields ──
    for pname, pschema in properties.items():
        fname = to_field_name(pname)
        dtype = get_dart_type(pname, pschema, spec, schemas_in_scope, enum_names)
        req = is_required(pname, required_list)

        # Add comment for special types
        comment = ""
        pfmt = pschema.get("format", "")
        if pfmt == "decimal":
            comment = "  // Decimal in Python"
        elif pfmt == "date":
            comment = "  // date-only (no time)"

        if req:
            lines.append(f"  final {dtype} {fname};{comment}")
        else:
            lines.append(f"  final {dtype}? {fname};{comment}")

    lines.append("")

    # ── Constructor ──
    lines.append(f"  const {dart_name}(")
    lines.append("    {")
    for pname, pschema in properties.items():
        fname = to_field_name(pname)
        dtype = get_dart_type(pname, pschema, spec, schemas_in_scope, enum_names)
        req = is_required(pname, required_list)
        if req:
            lines.append(f"    required this.{fname},")
        else:
            lines.append(f"    this.{fname},")
    lines.append("    }")
    lines.append("  );")
    lines.append("")

    # ── fromJson factory ──
    lines.append(f"  factory {dart_name}.fromJson(Map<String, dynamic> json) {{")
    lines.append(f"    return {dart_name}(")
    for pname, pschema in properties.items():
        fname = to_field_name(pname)
        req = is_required(pname, required_list)
        dtype = get_dart_type(pname, pschema, spec, schemas_in_scope, enum_names)
        json_key = pname

        if dtype == "String":
            if req:
                lines.append(f"      {fname}: json['{json_key}'] as String,")
            else:
                lines.append(f"      {fname}: json['{json_key}'] as String?,")
        elif dtype == "int":
            if req:
                lines.append(f"      {fname}: json['{json_key}'] as int,")
            else:
                lines.append(f"      {fname}: json['{json_key}'] as int?,")
        elif dtype == "double":
            if req:
                lines.append(f"      {fname}: (json['{json_key}'] as num).toDouble(),")
            else:
                lines.append(f"      {fname}: (json['{json_key}'] as num?)?.toDouble(),")
        elif dtype == "bool":
            if req:
                lines.append(f"      {fname}: json['{json_key}'] as bool,")
            else:
                lines.append(f"      {fname}: json['{json_key}'] as bool?,")
        elif dtype == "DateTime":
            if req:
                lines.append(f"      {fname}: DateTime.parse(json['{json_key}'] as String),")
            else:
                lines.append(f"      {fname}: json['{json_key}'] != null ? DateTime.parse(json['{json_key}'] as String) : null,")
        elif dtype.startswith("List<"):
            inner = dtype[5:-1]  # Extract inner type
            lines.append(f"      {fname}: (json['{json_key}'] as List<dynamic>?)")
            if inner == "String":
                lines.append(f"        ?.cast<String>()" + ("," if not req else " ?? [],"))
            elif inner == "int":
                lines.append(f"        ?.cast<int>()" + ("," if not req else " ?? [],"))
            elif inner == "double":
                lines.append(f"        ?.map((e) => (e as num).toDouble()).toList()" + ("," if not req else " ?? [],"))
            else:
                lines.append(f"        ?.map((e) => {inner}.fromJson(e as Map<String, dynamic>)).toList()" + ("," if not req else " ?? [],"))
        elif dtype == "Map<String, dynamic>":
            lines.append(f"      {fname}: json['{json_key}'] { 'as Map<String, dynamic>' if req else 'as Map<String, dynamic>?' },")
        elif dtype in enum_names:
            # Enum type: parse from String
            if req:
                lines.append(f"      {fname}: (json['{json_key}'] as String).to{dtype}(),")
            else:
                lines.append(f"      {fname}: json['{json_key}'] != null ? (json['{json_key}'] as String).to{dtype}() : null,")
        elif dtype.endswith("?"):
            base = dtype[:-1]
            if base in enum_names:
                lines.append(f"      {fname}: json['{json_key}'] != null ? (json['{json_key}'] as String).to{base}() : null,")
            else:
                lines.append(f"      {fname}: json['{json_key}'] != null ? {base}.fromJson(json['{json_key}'] as Map<String, dynamic>) : null,")
        else:
            if req:
                if dtype in enum_names:
                    lines.append(f"      {fname}: (json['{json_key}'] as String).to{dtype}(),")
                else:
                    lines.append(f"      {fname}: {dtype}.fromJson(json['{json_key}'] as Map<String, dynamic>),")
            else:
                if dtype in enum_names:
                    lines.append(f"      {fname}: json['{json_key}'] != null ? (json['{json_key}'] as String).to{dtype}() : null,")
                else:
                    lines.append(f"      {fname}: json['{json_key}'] != null ? {dtype}.fromJson(json['{json_key}'] as Map<String, dynamic>) : null,")
    lines.append("    );")
    lines.append("  }")
    lines.append("")

    # ── toJson method ──
    lines.append(f"  Map<String, dynamic> toJson() => {{")
    for pname, pschema in properties.items():
        fname = to_field_name(pname)
        dtype = get_dart_type(pname, pschema, spec, schemas_in_scope, enum_names)
        req = is_required(pname, required_list)
        json_key = pname

        if dtype == "DateTime":
            if req:
                lines.append(f"    '{json_key}': {fname}.toIso8601String(),")
            else:
                lines.append(f"    '{json_key}': {fname}?.toIso8601String(),")
        elif dtype in enum_names:
            # Enum: serialize as string
            if req:
                lines.append(f"    '{json_key}': {fname}.toJson(),")
            else:
                lines.append(f"    '{json_key}': {fname}?.toJson(),")
        elif dtype.startswith("List<"):
            inner = dtype[5:-1]
            if inner in enum_names:
                lines.append(f"    '{json_key}': {fname}?.map((e) => e.toJson()).toList(),")
            elif inner not in ("String", "int", "double", "bool", "dynamic") and "fromJson" in str(pschema.get("items", {})):
                lines.append(f"    '{json_key}': {fname}?.map((e) => e.toJson()).toList(),")
            else:
                lines.append(f"    '{json_key}': {fname},")
        elif dtype.endswith("?"):
            base = dtype[:-1]
            if base in enum_names:
                lines.append(f"    '{json_key}': {fname}?.toJson(),")
            elif base in ("String", "int", "double", "bool", "DateTime"):
                lines.append(f"    '{json_key}': {fname},")
            else:
                lines.append(f"    '{json_key}': {fname}?.toJson(),")
        else:
            if dtype in enum_names:
                lines.append(f"    '{json_key}': {fname}.toJson(),")
            else:
                lines.append(f"    '{json_key}': {fname},")
    lines.append("  };")
    lines.append("")
    lines.append("}")

    return "\n".join(lines)


# ─── Main ────────────────────────────────────────────────────────────────────

def load_openapi_spec(spec_path: str, spec_url: str | None) -> dict:
    """Load spec from file or URL."""
    if spec_url:
        import urllib.request
        with urllib.request.urlopen(spec_url) as resp:
            return json.loads(resp.read().decode())
    with open(spec_path) as f:
        return json.load(f)


def openapi_to_dart():
    parser = argparse.ArgumentParser(description="Generate Dart models from OpenAPI spec")
    parser.add_argument("--spec", help="URL to OpenAPI JSON (e.g. http://localhost:8000/openapi.json)")
    parser.add_argument("--spec-file", default="apps/api/openapi.json", help="Path to OpenAPI JSON file")
    parser.add_argument("--filter", help="Comma-separated schema name patterns (e.g. 'Equine,Saddle')")
    parser.add_argument("--output-dir", default="packages/mobile_domain/lib/src/gen",
                        help="Output directory for generated Dart files")
    args = parser.parse_args()

    # Load spec
    if args.spec:
        print(f"Loading spec from URL: {args.spec}")
        spec = load_openapi_spec("", args.spec)
    else:
        spec_file = args.spec_file or "apps/api/openapi.json"
        print(f"Loading spec from file: {spec_file}")
        spec = load_openapi_spec(spec_file, None)

    schemas = spec.get("components", {}).get("schemas", {})
    if not schemas:
        print("ERROR: No schemas found in OpenAPI spec")
        sys.exit(1)

    all_schema_names: set[str] = set(schemas.keys())

    # Determine schema filter
    filter_patterns = []
    if args.filter:
        filter_patterns = [p.strip() for p in args.filter.split(",")]

    # Find all schema names that match the filter
    in_scope: set[str] = set()
    for name in schemas:
        if name in SKIP_SCHEMAS:
            continue
        dart_name = to_dart_name(name, all_schema_names)
        if filter_patterns:
            if any(p.lower() in name.lower() or p.lower() in dart_name.lower() for p in filter_patterns):
                in_scope.add(dart_name)
        else:
            in_scope.add(dart_name)

    if not in_scope:
        print("No schemas matched the filter.")
        sys.exit(1)

    # Generate files
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    generated_files: list[str] = []
    generated_enums: list[str] = []
    generated_classes: list[str] = []
    used_dart_names: dict[str, str] = {}  # dart_name → original schema name

    for name, schema in sorted(schemas.items()):
        dart_name = to_dart_name(name, all_schema_names)
        if dart_name not in in_scope:
            continue
        if name in SKIP_SCHEMAS:
            continue

        # Handle naming collision: if two schemas produce the same dart_name,
        # keep the one with the original schema name
        if dart_name in used_dart_names:
            prev = used_dart_names[dart_name]
            # Both produce same name — keep original name for both
            # by appending a suffix
            file_name_base = snake_to_dart_file(dart_name)
            # Only the first occurrence keeps the clean name
            # The second gets a disambiguation suffix
            prev_is_raw = prev == dart_name or prev.endswith(dart_name)
            this_is_raw = name == dart_name or name.endswith(dart_name)
            if not prev_is_raw and this_is_raw:
                # Current one is the raw name (enum), keep it
                used_dart_names[dart_name] = name
                # Rename previous schema's file
                pass
            # For simplicity: just skip the duplicate (it's already generated)
            # This works because the enum name takes priority
            continue

        used_dart_names[dart_name] = name

        result = generate_model(name, schema, spec, in_scope, all_schema_names=all_schema_names)
        if result is None:
            continue

        # Check if it's an enum
        is_enum = schema.get("type") == "string" and "enum" in schema
        file_name = snake_to_dart_file(dart_name) + ".dart"
        file_path = out_dir / file_name

        with open(file_path, "w") as f:
            f.write("// ignore_for_file: public_member_api_docs, constant_identifier_names\n")
            f.write("// GENERATED CODE -- DO NOT EDIT MANUALLY\n")
            f.write("// Generated from OpenAPI spec\n")
            f.write("\n")
            if is_enum:
                f.write("import 'package:json_annotation/json_annotation.dart';\n\n")
            f.write(result)
            f.write("\n")

        if is_enum:
            generated_enums.append(dart_name)
        else:
            generated_classes.append(dart_name)
        generated_files.append(file_name)
        print(f"  [OK] {file_name} -> {dart_name}")

    # Generate barrel file (deduplicated)
    barrel_path = out_dir / "gen.dart"
    seen_files: set[str] = set()
    with open(barrel_path, "w") as f:
        f.write("// GENERATED CODE -- DO NOT EDIT MANUALLY\n")
        f.write("// Generated from OpenAPI spec\n")
        f.write("\n")
        # Order: enums first, then classes
        for dart_name in sorted(generated_enums):
            file_name = snake_to_dart_file(dart_name) + ".dart"
            if file_name not in seen_files:
                seen_files.add(file_name)
                f.write(f"export '{file_name}';\n")
        for dart_name in sorted(generated_classes):
            file_name = snake_to_dart_file(dart_name) + ".dart"
            if file_name not in seen_files:
                seen_files.add(file_name)
                f.write(f"export '{file_name}';\n")

    print(f"\n-- Summary --")
    print(f"  Output: {out_dir}")
    print(f"  Enums:  {len(generated_enums)}")
    print(f"  Models: {len(generated_classes)}")
    print(f"  Files:  {len(generated_files)}")

    # Print list of generated classes
    if generated_classes:
        print(f"\n  Generated classes:")
        for c in sorted(generated_classes):
            print(f"    - {c}")


if __name__ == "__main__":
    openapi_to_dart()
