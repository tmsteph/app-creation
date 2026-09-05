#!/usr/bin/env python3
"""Tiny compiler for the Human language prototype.

Human is an experiment in human-first, agent-native programming. The v0
compiler intentionally targets ordinary Python and has no third-party
runtime dependencies.
"""
from __future__ import annotations

import argparse
import ast
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional


class HumanSyntaxError(ValueError):
    pass


@dataclass
class Field:
    name: str
    default: Optional[str] = None


@dataclass
class DataType:
    name: str
    fields: List[Field] = field(default_factory=list)


@dataclass
class Event:
    name: str
    statements: List[str] = field(default_factory=list)


@dataclass
class Program:
    app: str
    data_types: List[DataType] = field(default_factory=list)
    events: List[Event] = field(default_factory=list)


IDENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
ASSIGN = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)\.([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.+)$")


def parse(source: str) -> Program:
    lines = source.splitlines()
    program: Optional[Program] = None
    current_data: Optional[DataType] = None
    current_event: Optional[Event] = None

    for number, raw in enumerate(lines, 1):
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        if "\t" in raw[:indent]:
            raise HumanSyntaxError(f"line {number}: use spaces, not tabs")
        text = raw.strip()

        if indent == 0:
            current_data = None
            current_event = None
            if text.startswith("app "):
                if program is not None:
                    raise HumanSyntaxError(f"line {number}: app may only be declared once")
                name = text[4:].strip()
                if not IDENT.match(name):
                    raise HumanSyntaxError(f"line {number}: invalid app name {name!r}")
                program = Program(app=name)
            elif text.startswith("data ") and text.endswith(":"):
                if program is None:
                    raise HumanSyntaxError(f"line {number}: declare app before data")
                name = text[5:-1].strip()
                if not IDENT.match(name):
                    raise HumanSyntaxError(f"line {number}: invalid data name {name!r}")
                current_data = DataType(name=name)
                program.data_types.append(current_data)
            elif text.startswith("when ") and text.endswith(":"):
                if program is None:
                    raise HumanSyntaxError(f"line {number}: declare app before events")
                name = text[5:-1].strip()
                if not name:
                    raise HumanSyntaxError(f"line {number}: event name cannot be empty")
                current_event = Event(name=name)
                program.events.append(current_event)
            else:
                raise HumanSyntaxError(f"line {number}: expected app, data, or when")
            continue

        if indent < 4 or indent % 4:
            raise HumanSyntaxError(f"line {number}: blocks use four-space indentation")
        if program is None:
            raise HumanSyntaxError(f"line {number}: declare app first")

        if current_data is not None:
            if "=" in text:
                name, default = [part.strip() for part in text.split("=", 1)]
                if not IDENT.match(name):
                    raise HumanSyntaxError(f"line {number}: invalid field name {name!r}")
                try:
                    ast.literal_eval(default)
                except (ValueError, SyntaxError):
                    raise HumanSyntaxError(
                        f"line {number}: defaults must be Python-style literals in v0"
                    ) from None
                current_data.fields.append(Field(name, default))
            else:
                if not IDENT.match(text):
                    raise HumanSyntaxError(f"line {number}: invalid field name {text!r}")
                current_data.fields.append(Field(text))
        elif current_event is not None:
            current_event.statements.append(text)
        else:
            raise HumanSyntaxError(f"line {number}: indented line is outside a block")

    if program is None:
        raise HumanSyntaxError("missing app declaration")
    return program


def _slug(text: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9_]+", "_", text.strip().lower()).strip("_")
    return slug or "event"


def _compile_statement(statement: str) -> str:
    match = ASSIGN.match(statement)
    if match:
        obj, attr, value = match.groups()
        try:
            ast.literal_eval(value)
        except (ValueError, SyntaxError):
            raise HumanSyntaxError(
                f"assignment values must be literals in v0: {statement!r}"
            ) from None
        return f"    {obj}.{attr} = {value}"
    escaped = repr(statement)
    return f"    runtime.action({escaped}, locals())"


def compile_python(program: Program) -> str:
    out: List[str] = [
        '"""Generated by the Human v0 compiler. Edit the .human source instead."""',
        "from dataclasses import dataclass",
        "",
        "",
        "class Runtime:",
        "    def __init__(self):",
        "        self.actions = []",
        "",
        "    def action(self, name, context):",
        "        record = {\"action\": name, \"context\": sorted(k for k in context if not k.startswith(\"__\"))}",
        "        self.actions.append(record)",
        "        return record",
        "",
    ]

    for data in program.data_types:
        out.extend(["@dataclass", f"class {data.name}:"])
        if not data.fields:
            out.append("    pass")
        else:
            required = [f for f in data.fields if f.default is None]
            optional = [f for f in data.fields if f.default is not None]
            for item in required + optional:
                default = "" if item.default is None else f" = {item.default}"
                out.append(f"    {item.name}: object{default}")
        out.append("")

    handlers = []
    for event in program.events:
        func = f"when_{_slug(event.name)}"
        handlers.append((event.name, func))
        out.extend([f"def {func}(runtime, **context):", "    globals().update({})"])
        for data in program.data_types:
            out.append(f"    {data.name} = context.get({data.name!r})")
        if event.statements:
            for statement in event.statements:
                compiled = _compile_statement(statement)
                assign = ASSIGN.match(statement)
                if assign:
                    obj = assign.group(1)
                    out.append(f"    if {obj} is None:")
                    out.append(f"        raise ValueError({('event requires '+obj)!r})")
                out.append(compiled)
        else:
            out.append("    pass")
        out.append("")

    out.append("EVENTS = {")
    for name, func in handlers:
        out.append(f"    {name!r}: {func},")
    out.extend([
        "}",
        "",
        f"APP = {program.app!r}",
        "",
        "def emit(event, runtime=None, **context):",
        "    runtime = runtime or Runtime()",
        "    try:",
        "        handler = EVENTS[event]",
        "    except KeyError:",
        "        raise KeyError(f\"unknown event: {event}\") from None",
        "    handler(runtime, **context)",
        "    return runtime",
        "",
    ])
    return "\n".join(out)


def compile_source(source: str) -> str:
    return compile_python(parse(source))


def main() -> int:
    parser = argparse.ArgumentParser(description="Compile Human source into Python")
    parser.add_argument("source", type=Path)
    parser.add_argument("-o", "--output", type=Path)
    args = parser.parse_args()

    generated = compile_source(args.source.read_text())
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(generated)
    else:
        print(generated)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
