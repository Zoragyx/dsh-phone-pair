"""Add a classes.dex to an APK produced by `aapt2 link`.

aapt2 emits the resources + manifest zip; the dex has to be merged in afterwards. Every existing
entry keeps its original compression method (important: resources.arsc must stay uncompressed for
apps targeting API 30+).

usage: add_dex.py <resource.apk> <classes.dex> <out.apk>
"""
import shutil
import sys
import zipfile


def main(argv: list[str]) -> int:
    if len(argv) != 4:
        print(__doc__)
        return 2
    src, dex, dst = argv[1], argv[2], argv[3]

    with zipfile.ZipFile(src, "r") as zin:
        items = [(i, zin.read(i.filename)) for i in zin.infolist()]

    names = {info.filename for info, _ in items}
    if "classes.dex" in names:
        items = [(i, d) for i, d in items if i.filename != "classes.dex"]

    with zipfile.ZipFile(dst, "w") as zout:
        for info, data in items:
            new = zipfile.ZipInfo(info.filename, date_time=info.date_time)
            new.compress_type = info.compress_type
            new.external_attr = info.external_attr
            new.internal_attr = info.internal_attr
            new.create_system = info.create_system
            zout.writestr(new, data)
        dex_info = zipfile.ZipInfo("classes.dex", date_time=(2024, 1, 1, 0, 0, 0))
        dex_info.compress_type = zipfile.ZIP_DEFLATED
        with open(dex, "rb") as fh:
            zout.writestr(dex_info, fh.read())

    with zipfile.ZipFile(dst) as z:
        bad = z.testzip()
        if bad is not None:
            raise SystemExit(f"corrupt entry after repack: {bad}")
        print(f"packed {len(z.namelist())} entries -> {dst}")
        for info in z.infolist():
            method = "store" if info.compress_type == zipfile.ZIP_STORED else "deflate"
            print(f"    {info.filename:<40} {method:<8} {info.file_size:>8} B")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
