#!/usr/bin/env python3
"""Empacota os arquivos de cliente da instância, sem dados pessoais."""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
CONFIGS = (
    "MouseTweaks.cfg", "appleskin-client.toml", "entity_model_features.json",
    "entity_texture_features.json", "etf_warnings.json", "fml.toml",
    "iris-excluded.json", "iris.properties", "neoforge-client.toml",
    "neoforge-local.toml", "sodium-extra-options.json", "sodium-extra.properties",
    "sodium-mixins.properties", "sodium-options.json",
)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("minecraft", type=Path, help="Pasta .minecraft da instância 26.3")
    args = parser.parse_args()
    source = args.minecraft.resolve()
    components = json.loads((source.parent / "mmc-pack.json").read_text())["components"]
    versions = {c["uid"]: c["version"] for c in components}
    if versions.get("net.minecraft") != "26.3" or versions.get("net.neoforged") != "26.3.0.51-beta":
        parser.error("A instância deve usar Minecraft 26.3 e NeoForge 26.3.0.51-beta")
    files = {}
    for folder, suffixes in (("mods", (".jar",)), ("resourcepacks", (".zip",)),
                             ("shaderpacks", (".zip", ".txt"))):
        for path in sorted((source / folder).iterdir()):
            if path.is_file() and not path.is_symlink() and path.suffix in suffixes:
                files[path.relative_to(source).as_posix()] = path.read_bytes()
        if not any(name.startswith(folder + "/") for name in files):
            parser.error(f"Pasta {folder} vazia")
    for name in CONFIGS:
        files["config/" + name] = (source / "config" / name).read_bytes()
    files["options.txt"] = (source / "options.txt").read_bytes()
    files["servers.dat"] = (source / "servers.dat").read_bytes()
    expected_server = (b'\n\x00\x00\t\x00\x07servers\n\x00\x00\x00\x01'
                       b'\x01\x00\x06hidden\x00\x08\x00\x02ip\x00\x17minecraft.valc.cc:25565'
                       b'\x08\x00\x04name\x00\x04VALC\x00\x00')
    if files["servers.dat"] != expected_server:
        parser.error("servers.dat deve conter somente VALC em minecraft.valc.cc:25565")
    files["LEIA-ME.txt"] = (ROOT / "PACK-LEIA-ME.txt").read_bytes()
    manifest = {
        "minecraft": "26.3", "loader": "NeoForge", "loader_version": "26.3.0.51-beta",
        "server": "minecraft.valc.cc:25565",
        "files": [{"path": name, "size": len(data), "sha256": hashlib.sha256(data).hexdigest()}
                  for name, data in sorted(files.items())],
    }
    files["manifest.json"] = (json.dumps(manifest, indent=2, ensure_ascii=False) + "\n").encode()
    output = ROOT / "downloads" / "valc-26.3-neoforge.zip"
    output.parent.mkdir(exist_ok=True)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, data in sorted(files.items()):
            info = zipfile.ZipInfo(name, date_time=(2026, 10, 7, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, data)
    digest = hashlib.sha256(output.read_bytes()).hexdigest()
    output.with_suffix(".zip.sha256").write_text(f"{digest}  {output.name}\n")
    print(f"{output.name}: {output.stat().st_size / 1024 / 1024:.2f} MiB, {len(files)} arquivos")


if __name__ == "__main__":
    main()
