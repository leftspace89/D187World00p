"""convert_fear_to_d187.py — convert a WorldEdit-Fear .World00p binary into
the District 187 (S2 SonSilah) magic.

Fear and D187 share the EXACT same binary format — header layout,
WorldModelsSection, RenderSection, SectorSection, ObjectSection,
BlindObjectDataSection.  The ONLY difference is the magic XOR value used
on the 8 count u32s of the WorldModelsSection header:

    FEAR    magic = 399
    D187    magic = 246

Everything else in the file is byte-identical between formats.

Usage:
    python convert_fear_to_d187.py <input.World00p> <output.World00p>
"""
import argparse
import os
import struct
import sys

FEAR_MAGIC = 399
D187_MAGIC = 246
WM_START_OFFSET = 56            # bytes 0..55 = header (version + 4 sec offs + 3 vec3)


def convert(in_path: str, out_path: str) -> None:
    with open(in_path, "rb") as f:
        buf = bytearray(f.read())

    if len(buf) < WM_START_OFFSET + 32:
        raise SystemExit(f"file too small ({len(buf)} bytes)")
    version = struct.unpack("<I", buf[0:4])[0]
    if version != 113:
        raise SystemExit(f"bad version {version} (expected 113)")

    # Skip wm_min(12) + wm_max(12) + count(4) + zero(4) at WM_START_OFFSET..+32
    off = WM_START_OFFSET + 12 + 12
    subdivision_count = struct.unpack("<I", buf[off:off+4])[0]
    off += 8
    flag_bytes = (subdivision_count + 7) // 8
    off += flag_bytes
    counts_off = off

    # Read the 8 magic-XOR'd count u32s under Fear magic, re-write under D187.
    fear_decoded = []
    for i in range(8):
        raw = struct.unpack("<I", buf[counts_off + i*4 : counts_off + i*4 + 4])[0]
        fear_decoded.append(raw ^ FEAR_MAGIC)

    bsp_name_count, bsp_names_length, plane_count, bsp_count, \
        node_count, polygon_count, vertex_ref_count, vertex_count = fear_decoded
    if not (1 <= bsp_count < 1000) or not (1 <= bsp_name_count < 5000):
        raise SystemExit(
            f"counts look implausible under FEAR magic — input may not be a "
            f"Fear .World00p.  Decoded: bsps={bsp_count} name_cnt={bsp_name_count}"
        )

    print(f"  input: {in_path}  ({len(buf)} bytes, version {version})")
    print(f"  decoded counts (FEAR magic):")
    print(f"    bsp_name_count={bsp_name_count}  bsp_names_length={bsp_names_length}")
    print(f"    plane_count={plane_count}  bsp_count={bsp_count}")
    print(f"    node_count={node_count}  polygon_count={polygon_count}")
    print(f"    vertex_ref_count={vertex_ref_count}  vertex_count={vertex_count}")

    for i, decoded in enumerate(fear_decoded):
        struct.pack_into("<I", buf, counts_off + i*4, decoded ^ D187_MAGIC)

    out_dir = os.path.dirname(out_path)
    if out_dir and not os.path.isdir(out_dir):
        os.makedirs(out_dir, exist_ok=True)
    with open(out_path, "wb") as f:
        f.write(buf)
    print(f"  output: {out_path}  ({len(buf)} bytes)")
    print(f"  re-encoded 8 WM counts: FEAR (399) -> D187 (246)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input", help="Fear-format .World00p (magic=399).")
    ap.add_argument("output", help="D187-format .World00p (magic=246).")
    args = ap.parse_args()
    convert(args.input, args.output)


if __name__ == "__main__":
    main()
