"""Compile every locale/*/LC_MESSAGES/*.po file into the .mo file Django reads.

Pure Python — works on Windows and on Render without installing GNU gettext
(Django's own `compilemessages` command needs gettext, which is a pain on Windows).

Usage:  python scripts/compile_translations.py

To change a Greek text: edit locale/el/LC_MESSAGES/django.po, run this script,
restart the server. (Render runs it automatically on every deploy.)
"""
import ast
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def parse_po(path):
    """Return {msgid: msgstr}; plural entries use 'singular\\x00plural' keys and
    '\\x00'-joined msgstr forms, exactly like the .mo format expects."""
    entries = {}
    msgctxt = msgid = msgid_plural = None
    msgstr = {}
    current = None
    fuzzy = False

    def flush():
        nonlocal msgctxt, msgid, msgid_plural, msgstr, fuzzy
        if msgid is not None and not fuzzy:
            key = msgid if msgctxt is None else msgctxt + '\x04' + msgid
            if msgid_plural is not None:
                forms = [msgstr.get(i, '') for i in range(len(msgstr))]
                if all(forms):
                    entries[key + '\x00' + msgid_plural] = '\x00'.join(forms)
            elif msgstr.get(0) or msgid == '':
                entries[key] = msgstr.get(0, '')
        msgctxt = msgid = msgid_plural = None
        msgstr = {}
        fuzzy = False

    for raw in path.read_text(encoding='utf-8').splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith('#,') and 'fuzzy' in line:
            flush()
            fuzzy = True
            continue
        if line.startswith('#'):
            continue
        if line.startswith('msgctxt '):
            if msgid is not None:
                flush()
            msgctxt = ast.literal_eval(line[8:])
            current = ('ctxt', None)
        elif line.startswith('msgid_plural '):
            msgid_plural = ast.literal_eval(line[13:])
            current = ('plural', None)
        elif line.startswith('msgid '):
            if msgid is not None:
                flush()
            msgid = ast.literal_eval(line[6:])
            current = ('id', None)
        elif line.startswith('msgstr['):
            idx = int(line[7:line.index(']')])
            msgstr[idx] = ast.literal_eval(line[line.index(']') + 2:])
            current = ('str', idx)
        elif line.startswith('msgstr '):
            msgstr[0] = ast.literal_eval(line[7:])
            current = ('str', 0)
        elif line.startswith('"'):
            text = ast.literal_eval(line)
            kind, idx = current
            if kind == 'ctxt':
                msgctxt += text
            elif kind == 'id':
                msgid += text
            elif kind == 'plural':
                msgid_plural += text
            else:
                msgstr[idx] += text
    flush()
    return entries


def write_mo(entries, path):
    keys = sorted(entries)
    ids = b''
    strs = b''
    offsets = []
    for k in keys:
        kb, vb = k.encode('utf-8'), entries[k].encode('utf-8')
        offsets.append((len(ids), len(kb), len(strs), len(vb)))
        ids += kb + b'\x00'
        strs += vb + b'\x00'
    n = len(keys)
    keystart = 7 * 4 + 16 * n
    valuestart = keystart + len(ids)
    koffsets, voffsets = [], []
    for o1, l1, o2, l2 in offsets:
        koffsets += [l1, o1 + keystart]
        voffsets += [l2, o2 + valuestart]
    output = struct.pack('Iiiiiii', 0x950412DE, 0, n, 7 * 4, 7 * 4 + n * 8, 0, 0)
    output += struct.pack(f'{len(koffsets)}i', *koffsets)
    output += struct.pack(f'{len(voffsets)}i', *voffsets)
    output += ids + strs
    path.write_bytes(output)


def main():
    po_files = sorted((ROOT / 'locale').glob('*/LC_MESSAGES/*.po'))
    if not po_files:
        print('No .po files found.')
        return 0
    for po in po_files:
        entries = parse_po(po)
        mo = po.with_suffix('.mo')
        write_mo(entries, mo)
        print(f'Compiled {po.relative_to(ROOT)} -> {mo.name} ({len(entries) - 1} messages)')
    return 0


if __name__ == '__main__':
    sys.exit(main())
