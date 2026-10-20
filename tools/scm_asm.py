#!/usr/bin/env python3
"""Minimal CLEO script assembler for GTA San Andreas (Android).

Compiles a small text language into a CLEO custom script (.csa / .csi).
Opcodes and parameter lists come from tools/sa_mobile_commands.json
(taken from the Sanny Builder library, sa_mobile edition). Arguments are
written in bytecode order; for commands marked "out_first" (CLEO touch
opcodes) the result variable comes first: GET_TOUCH_POINT_STATE 12@ 5 0

Source syntax (one instruction per line):
    // comment                  comment (also allowed at end of line)
    :Label                      label definition
    COMMAND_NAME arg arg ...    command by name (or 4-digit hex opcode)
    NOT COMMAND_NAME ...        negated condition
    #ifdef NAME / #else / #endif  conditional compilation (-D NAME)

Arguments:
    12@        local variable
    5  -1      integer
    1.5 -2.0   float (must contain a dot)
    'ABC'      short string (max 7 chars, 8 bytes)
    "abc"      long string (variable length)
    @Label     label reference (CLEO-relative jump)

Usage: scm_asm.py source.txt output.csi [-D CSA]
"""
import json
import os
import re
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

T_END, T_INT32, T_LVAR, T_INT8, T_INT16, T_FLOAT = 0x00, 0x01, 0x03, 0x04, 0x05, 0x06
T_STR8, T_STRVAR = 0x09, 0x0E

INT_TYPES = {"int", "bool", "label"}
STRING_TYPES = {"string", "gxt_key", "string128", "zone_key", "script_id"}


class AsmError(Exception):
    pass


def load_commands():
    with open(os.path.join(HERE, "sa_mobile_commands.json")) as f:
        cmds = json.load(f)["commands"]
    by_id = {v["id"]: dict(v, name=k) for k, v in cmds.items()}
    return cmds, by_id


def tokenize(line):
    tokens = []
    i = 0
    while i < len(line):
        c = line[i]
        if c.isspace():
            i += 1
        elif c in "'\"":
            j = line.index(c, i + 1)
            tokens.append(line[i:j + 1])
            i = j + 1
        else:
            j = i
            while j < len(line) and not line[j].isspace():
                j += 1
            tokens.append(line[i:j])
            i = j
    return tokens


def strip_comment(line):
    out, quote = [], None
    for i, c in enumerate(line):
        if quote:
            if c == quote:
                quote = None
        elif c in "'\"":
            quote = c
        elif line.startswith("//", i):
            break
        out.append(c)
    return "".join(out).strip()


def preprocess(lines, defines):
    stack = []
    for n, raw in enumerate(lines, 1):
        line = strip_comment(raw)
        if line.startswith("#ifdef"):
            stack.append(line.split()[1] in defines)
            continue
        if line == "#else":
            stack[-1] = not stack[-1]
            continue
        if line == "#endif":
            stack.pop()
            continue
        if all(stack) and line:
            yield n, line
    if stack:
        raise AsmError("unterminated #ifdef")


def kind_of(token):
    if re.fullmatch(r"\d+@", token):
        return "var"
    if token.startswith("@"):
        return "label"
    if token[0] in "'\"":
        return "string"
    if re.fullmatch(r"-?\d+\.\d*", token):
        return "float"
    if re.fullmatch(r"-?\d+", token):
        return "int"
    raise AsmError("bad argument %r" % token)


def encode_int(value):
    if -128 <= value <= 127:
        return struct.pack("<Bb", T_INT8, value)
    if -32768 <= value <= 32767:
        return struct.pack("<Bh", T_INT16, value)
    return struct.pack("<Bi", T_INT32, value)


def encode_arg(token, ptype, is_output, labels, lineno):
    kind = kind_of(token)
    if is_output and kind != "var":
        raise AsmError("line %d: output %r must be a variable" % (lineno, token))
    if kind == "var":
        index = int(token[:-1])
        if index > 33:
            raise AsmError("line %d: local variable %s out of range" % (lineno, token))
        return struct.pack("<BH", T_LVAR, index)
    if ptype == "label" and kind != "label":
        raise AsmError("line %d: expected label, got %r" % (lineno, token))
    if kind == "label":
        if ptype != "label":
            raise AsmError("line %d: unexpected label %r" % (lineno, token))
        if labels is None:
            return struct.pack("<Bi", T_INT32, 0)
        name = token[1:]
        if name not in labels:
            raise AsmError("line %d: unknown label %r" % (lineno, name))
        if labels[name] == 0:
            raise AsmError("line %d: label at offset 0 cannot be jumped to" % lineno)
        return struct.pack("<Bi", T_INT32, -labels[name])
    if kind == "float":
        if ptype not in ("float", "any"):
            raise AsmError("line %d: float %s given for int parameter" % (lineno, token))
        return struct.pack("<Bf", T_FLOAT, float(token))
    if kind == "int":
        if ptype == "float":
            raise AsmError("line %d: int %s given for float parameter (write %s.0)"
                           % (lineno, token, token))
        if ptype in STRING_TYPES:
            raise AsmError("line %d: int given for string parameter" % lineno)
        return encode_int(int(token))
    # cp1251 lets Russian text reach the game font (SanLTD localisation)
    text = token[1:-1].encode("cp1251")
    if ptype not in STRING_TYPES and ptype != "any":
        raise AsmError("line %d: string given for %s parameter" % (lineno, ptype))
    if token[0] == "'":
        if len(text) > 7:
            raise AsmError("line %d: short string %r longer than 7 chars" % (lineno, token))
        return bytes([T_STR8]) + text.ljust(8, b"\0")
    if len(text) > 255:
        raise AsmError("line %d: string too long" % lineno)
    return bytes([T_STRVAR, len(text)]) + text


def assemble(lines, defines=()):
    cmds, by_id = load_commands()
    program = list(preprocess(lines, set(defines)))

    def emit(labels):
        out = bytearray()
        found = {}
        conditions_left = None  # conditions still expected after IF
        for lineno, line in program:
            if line.startswith(":"):
                name = line[1:]
                if name in found:
                    raise AsmError("line %d: duplicate label %r" % (lineno, name))
                if conditions_left is not None:
                    raise AsmError("line %d: label inside IF block" % lineno)
                found[name] = len(out)
                continue
            tokens = tokenize(line)
            negate = False
            if tokens[0] == "NOT":
                negate = True
                tokens = tokens[1:]
            name, args = tokens[0], tokens[1:]
            if re.fullmatch(r"[0-9A-Fa-f]{4}", name):
                cmd = by_id.get(name.upper())
            else:
                cmd = cmds.get(name)
                cmd = dict(cmd, name=name) if cmd else None
            if cmd is None:
                raise AsmError("line %d: unknown or unsupported command %r" % (lineno, name))
            if negate and not cmd["cond"]:
                raise AsmError("line %d: NOT used on non-condition %s" % (lineno, cmd["name"]))
            params = [(t, False) for t in cmd["in"]] + [(t, True) for t in cmd["out"]]
            if cmd.get("out_first"):
                params = params[len(cmd["in"]):] + params[:len(cmd["in"])]
            if "arguments" in cmd["in"]:
                raise AsmError("line %d: variadic commands are not supported" % lineno)
            if len(args) != len(params):
                raise AsmError("line %d: %s expects %d arguments, got %d"
                               % (lineno, cmd["name"], len(params), len(args)))
            if conditions_left is not None:
                if conditions_left > 0:
                    if not cmd["cond"]:
                        raise AsmError("line %d: %s is not a condition" % (lineno, cmd["name"]))
                    conditions_left -= 1
                elif cmd["name"] != "GOTO_IF_FALSE":
                    raise AsmError("line %d: GOTO_IF_FALSE expected after conditions" % lineno)
                else:
                    conditions_left = None
            elif cmd["cond"]:
                raise AsmError("line %d: condition %s outside IF" % (lineno, cmd["name"]))
            if cmd["name"] == "IF":
                n = int(args[0])
                if 0 <= n <= 7:
                    conditions_left = n + 1
                elif 21 <= n <= 27:
                    conditions_left = n - 19
                else:
                    raise AsmError("line %d: bad IF argument %d" % (lineno, n))
            opcode = int(cmd["id"], 16) | (0x8000 if negate else 0)
            out += struct.pack("<H", opcode)
            for token, (ptype, is_output) in zip(args, params):
                out += encode_arg(token, ptype, is_output, labels, lineno)
        return bytes(out), found

    _, labels = emit(None)
    code, labels2 = emit(labels)
    assert labels == labels2
    return code


def main(argv):
    defines = []
    files = []
    i = 0
    while i < len(argv):
        if argv[i] == "-D":
            defines.append(argv[i + 1])
            i += 2
        else:
            files.append(argv[i])
            i += 1
    if len(files) != 2:
        print(__doc__)
        return 2
    with open(files[0], encoding="utf-8") as f:  # strings -> cp1251
        lines = f.read().splitlines()
    try:
        code = assemble(lines, defines)
    except AsmError as e:
        print("%s: error: %s" % (files[0], e), file=sys.stderr)
        return 1
    with open(files[1], "wb") as f:
        f.write(code)
    print("%s -> %s (%d bytes)" % (files[0], files[1], len(code)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
