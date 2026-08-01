#!/usr/bin/env python3
"""Vendor and style AircraftShapesSVG assets for the NAIP Browser iPad map.

The upstream SVG files remain unchanged under third_party/. Styled SVG copies
are generated into the Xcode asset catalogue. Both forms remain GPL-3.0-or-later.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
VENDOR_ROOT = PROJECT_ROOT / "third_party" / "AircraftShapesSVG"
ASSET_CATALOG = (
    PROJECT_ROOT
    / "clients"
    / "ipad"
    / "NAIPBrowser"
    / "Resources"
    / "Assets.xcassets"
)
SWIFT_CATALOG = (
    PROJECT_ROOT
    / "clients"
    / "ipad"
    / "NAIPBrowser"
    / "Features"
    / "VectorMap"
    / "VATSIMAircraftGPLCatalog.generated.swift"
)

INKSCAPE_LABEL = "{http://www.inkscape.org/namespaces/inkscape}label"
SVG_PATH = "{http://www.w3.org/2000/svg}path"

ALIASES = {
    "A300": "A306",
    "A319": "A19N",
    "A330": "A333",
    "A350": "A359",
    "A380": "A388",
    "A220": "BCS3",
    "AN124": "A124",
    "AT43": "AT45",
    "AT72": "AT75",
    "AT73": "AT75",
    "AT76": "AT75",
    "B717": "B712",
    "B727": "B722",
    "B736": "B737",
    "B741": "B742",
    "B743": "B744",
    "B757": "B752",
    "B767": "B763",
    "B777": "B772",
    "B778": "B779",
    "B787": "B789",
    "DH8": "DH8D",
    "E175": "E170",
    "E190": "E195",
}

COMPONENT_FALLBACKS = {
    "generic": "Unidentified",
    "helicopter": "EC45",
    "glider": "SGUP",
    "bizjet": "C25B",
    "cessna-piston": "C172",
    "cessna-caravan": "C208",
    "piper-cirrus": "SR22",
    "pc12": "PC12",
    "beech-twin": "B350",
    "atr42": "AT45",
    "atr72": "AT75",
    "dash8": "DH8D",
    "saab340": "SF34",
    "ma60": "AT75",
    "y12": "BN2P",
    "y20": "C17",
    "crj": "CRJ9",
    "erj": "E170",
    "ejet": "E195",
    "fokker": "F50",
    "md80-family": "DC87",
    "dc10": "DC10",
    "md11": "MD11",
    "il62": "IL62",
    "il76": "IL76",
    "an124": "A124",
    "arj21": "E195",
    "c919": "A320",
    "a220": "BCS3",
    "a300": "A306",
    "a310": "A310",
    "a318": "A318",
    "a319": "A19N",
    "a320": "A320",
    "a321": "A321",
    "a330": "A333",
    "a340": "A346",
    "a350": "A359",
    "a380": "A388",
    "b717": "B712",
    "b727": "B722",
    "b737-classic": "B735",
    "b737-ng": "B738",
    "b737-max": "B38M",
    "b747": "B744",
    "b757": "B752",
    "b767": "B763",
    "b777": "B772",
    "b777-200": "B772",
    "b777-200lr-f": "B77L",
    "b777-300": "B773",
    "b777-300er": "B77W",
    "b777-8": "B779",
    "b777-9": "B779",
    "b787": "B789",
}


def git_output(repository: Path, *arguments: str) -> str:
    return subprocess.check_output(
        ["git", "-C", str(repository), *arguments], text=True
    ).strip()


def token(source_key: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "_", source_key).strip("_")


def style_name(source_key: str) -> str:
    return f"naip-vatsim-gpl-{token(source_key).lower()}"


def asset_name(source_key: str) -> str:
    return f"VATSIMGPL_{token(source_key)}"


def parse_style(value: str | None) -> dict[str, str]:
    result: dict[str, str] = {}
    for item in (value or "").split(";"):
        if ":" not in item:
            continue
        key, content = item.split(":", 1)
        result[key.strip()] = content.strip()
    return result


def styled_svg(source: Path) -> bytes:
    tree = ET.parse(source)
    root = tree.getroot()
    root.set("width", "44")
    root.set("height", "44")

    main_paths: set[ET.Element] = set()
    for group in root.iter():
        if group.get(INKSCAPE_LABEL) == "Pfade":
            main_paths.update(group.iter(SVG_PATH))

    all_paths = list(root.iter(SVG_PATH))
    if not main_paths and all_paths:
        main_paths.add(all_paths[0])

    for path in all_paths:
        properties = parse_style(path.get("style"))
        if path in main_paths:
            properties.update(
                {
                    "fill": "#20CFF5",
                    "fill-opacity": "1",
                    "fill-rule": "evenodd",
                    "stroke": "#0B3853",
                    "stroke-width": "1.15",
                    "stroke-linecap": "round",
                    "stroke-linejoin": "round",
                    "stroke-opacity": "1",
                }
            )
        else:
            properties.update(
                {
                    "fill": "none",
                    "stroke": "#0B3853",
                    "stroke-width": "0.72",
                    "stroke-linecap": "round",
                    "stroke-linejoin": "round",
                    "stroke-opacity": "1",
                }
            )
        path.set("style", ";".join(f"{key}:{value}" for key, value in properties.items()))

    root.insert(
        0,
        ET.Comment(
            " Derived for NAIP Browser from AircraftShapesSVG; colors and stroke widths modified. "
            " Licensed under GNU GPL-3.0-or-later. "
        ),
    )
    ET.indent(tree, space="  ")
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def vendor_upstream(
    upstream: Path,
    vendor_root: Path = VENDOR_ROOT,
    *,
    standalone: bool = False,
) -> tuple[str, str]:
    shapes_source = upstream / "Shapes SVG"
    if not shapes_source.is_dir() or not (upstream / "LICENSE").is_file():
        raise SystemExit(f"Not an AircraftShapesSVG checkout: {upstream}")

    vendor_root.mkdir(parents=True, exist_ok=True)
    destination = vendor_root / "Shapes SVG"
    if destination.exists():
        shutil.rmtree(destination)
    shutil.copytree(shapes_source, destination)
    shutil.copy2(upstream / "LICENSE", vendor_root / "LICENSE")
    shutil.copy2(upstream / "Catalogue.png", vendor_root / "Catalogue.png")
    upstream_readme_name = "UPSTREAM_README.md" if standalone else "README.md"
    shutil.copy2(upstream / "README.md", vendor_root / upstream_readme_name)

    revision = git_output(upstream, "rev-parse", "HEAD")
    revision_date = git_output(upstream, "log", "-1", "--format=%cI")
    upstream_note = (
        "# AircraftShapesSVG upstream provenance\n\n"
        "- Repository: https://github.com/RexKramer1/AircraftShapesSVG\n"
        "- NAIP corresponding source: "
        "https://github.com/Yinuoo66/NAIP-AircraftShapesSVG\n"
        f"- Vendored revision: `{revision}`\n"
        f"- Upstream revision date: `{revision_date}`\n"
        "- License: GNU GPL-3.0-or-later\n"
        "- Local modifications: generated app copies change fill, stroke color, "
        "and stroke width only; originals in `Shapes SVG/` are unchanged.\n"
    )
    (vendor_root / "UPSTREAM.md").write_text(upstream_note, encoding="utf-8")
    return revision, revision_date


def generate_assets(
    shapes_directory: Path,
    vendor_root: Path = VENDOR_ROOT,
    asset_catalog: Path | None = ASSET_CATALOG,
) -> list[str]:
    source_files = sorted(shapes_directory.glob("*.svg"), key=lambda path: path.stem)
    if not source_files:
        raise SystemExit(f"No SVG files found in {shapes_directory}")

    if asset_catalog is not None:
        for existing in asset_catalog.glob("VATSIMGPL_*.imageset"):
            shutil.rmtree(existing)
    derived_root = vendor_root / "NAIP Styled SVG"
    if derived_root.exists():
        shutil.rmtree(derived_root)
    derived_root.mkdir(parents=True)

    for source in source_files:
        source_key = source.stem
        generated_bytes = styled_svg(source)
        derived_source = derived_root / f"{source_key}.svg"
        derived_source.write_bytes(generated_bytes)
        if asset_catalog is not None:
            imageset = asset_catalog / f"{asset_name(source_key)}.imageset"
            imageset.mkdir(parents=True)
            generated_filename = f"{asset_name(source_key)}.svg"
            (imageset / generated_filename).write_bytes(generated_bytes)
            contents = {
                "images": [{"filename": generated_filename, "idiom": "universal"}],
                "info": {"author": "xcode", "version": 1},
                "properties": {"preserves-vector-representation": True},
            }
            (imageset / "Contents.json").write_text(
                json.dumps(contents, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
    source_keys = [path.stem for path in source_files]
    manifest = {
        "schema_version": "naip-aircraft-shapes-v1",
        "license": "GPL-3.0-or-later",
        "upstream_repository": "https://github.com/RexKramer1/AircraftShapesSVG",
        "entries": [
            {
                "source_key": source_key,
                "asset_name": asset_name(source_key),
                "style_name": style_name(source_key),
            }
            for source_key in source_keys
        ],
        "designator_aliases": ALIASES,
        "component_fallbacks": COMPONENT_FALLBACKS,
        "modifications": ["fill color", "stroke color", "stroke width"],
    }
    (vendor_root / "naip-manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return source_keys


def swift_string(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def generate_swift_catalog(source_keys: list[str], revision: str) -> None:
    entries = "\n".join(
        "        Entry(sourceKey: {source}, assetName: {asset}, styleName: {style}),".format(
            source=swift_string(source_key),
            asset=swift_string(asset_name(source_key)),
            style=swift_string(style_name(source_key)),
        )
        for source_key in source_keys
    )
    aliases = "\n".join(
        f"        {swift_string(key)}: {swift_string(value)},"
        for key, value in sorted(ALIASES.items())
    )
    fallbacks = "\n".join(
        f"        {swift_string(key)}: {swift_string(value)},"
        for key, value in sorted(COMPONENT_FALLBACKS.items())
    )
    swift = f'''// Generated by tools/vendor_aircraft_shapes_svg.py. Do not edit by hand.
// AircraftShapesSVG artwork and this derivative catalog are GPL-3.0-or-later.

import Foundation

enum VATSIMAircraftGPLCatalog {{
    struct Entry: Hashable, Sendable {{
        let sourceKey: String
        let assetName: String
        let styleName: String
    }}

    static let upstreamRevision = {swift_string(revision)}
    static let entries: [Entry] = [
{entries}
    ]

    private static let entryBySourceKey = Dictionary(
        uniqueKeysWithValues: entries.map {{ ($0.sourceKey, $0) }}
    )
    private static let sourceKeyByDesignator = Dictionary(
        uniqueKeysWithValues: entries.compactMap {{ entry -> (String, String)? in
            let uppercased = entry.sourceKey.uppercased()
            guard !uppercased.isEmpty,
                  uppercased.allSatisfy({{ $0.isLetter || $0.isNumber }})
            else {{ return nil }}
            return (uppercased, entry.sourceKey)
        }}
    )
    private static let aliases: [String: String] = [
{aliases}
    ]
    private static let componentFallbacks: [String: String] = [
{fallbacks}
    ]

    static func entry(forDesignator rawValue: String?) -> Entry? {{
        let designator = normalizedDesignator(rawValue)
        guard !designator.isEmpty else {{ return nil }}
        let sourceKey = sourceKeyByDesignator[designator] ?? aliases[designator]
        return sourceKey.flatMap {{ entryBySourceKey[$0] }}
    }}

    static func entry(forComponent component: VATSIMAircraftIconComponent) -> Entry? {{
        componentFallbacks[component.rawValue].flatMap {{ entryBySourceKey[$0] }}
    }}

    private static func normalizedDesignator(_ rawValue: String?) -> String {{
        let raw = rawValue?
            .uppercased()
            .trimmingCharacters(in: .whitespacesAndNewlines) ?? ""
        let value = String(raw.prefix {{ $0.isLetter || $0.isNumber }})
        if ["772", "773", "777", "778", "779", "77L", "77W"].contains(value) {{
            return "B\\(value)"
        }}
        return value
    }}
}}
'''
    SWIFT_CATALOG.write_text(swift, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--source-package-root",
        type=Path,
        help="Generate a standalone corresponding-source package at this path",
    )
    parser.add_argument("upstream", type=Path, help="AircraftShapesSVG Git checkout")
    arguments = parser.parse_args()
    standalone_root = (
        arguments.source_package_root.resolve()
        if arguments.source_package_root is not None
        else None
    )
    output_root = standalone_root or VENDOR_ROOT
    revision, _ = vendor_upstream(
        arguments.upstream.resolve(), output_root, standalone=standalone_root is not None
    )
    source_keys = generate_assets(
        output_root / "Shapes SVG",
        output_root,
        asset_catalog=None if standalone_root is not None else ASSET_CATALOG,
    )
    if standalone_root is None:
        generate_swift_catalog(source_keys, revision)
    print(f"Vendored and generated {len(source_keys)} AircraftShapesSVG icons at {revision}")


if __name__ == "__main__":
    main()
