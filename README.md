# NAIP Aircraft Shapes SVG source package

This directory contains the corresponding source for the GPL aircraft-shape
component used by the NAIP Browser VATSIM map layer.

## Origin and license

- Upstream: <https://github.com/RexKramer1/AircraftShapesSVG>
- Vendored revision: `0743718760c42a5e91801adc053b5b828a434a5e`
- License: GNU GPL-3.0-or-later; see `LICENSE`
- The upstream artwork is preserved unchanged in `Shapes SVG/`.

## NAIP modifications

`NAIP Styled SVG/` contains the preferred form for modification used by the
app. These files retain the upstream geometry and apply NAIP's cyan fill, dark
outline, line joins, and line caps. No outline geometry was hidden in a raster
conversion.

`naip-manifest.json` records all 182 source designators, generated asset/style
names, aliases, and component fallbacks. Runtime selection first tries the exact
ICAO aircraft designator received from the backend. It uses a component fallback
only when an exact source shape does not exist.

The upstream set contains separate shapes for `B772`, `B77L`, `B773`, `B77W`,
and `B779`. It does not contain `B778`, so `B778` is explicitly documented as
using the nearest available `B779` shape.

## Reproducing the generated files

Run the public generator against a checkout of the upstream repository:

```sh
python3 scripts/vendor_aircraft_shapes_svg.py /path/to/AircraftShapesSVG
```

The generated Swift lookup table and Xcode asset-catalog wrappers are build
artifacts in the application repository. The complete editable artwork,
transformation logic, and lookup manifest needed to reproduce the icon component
are included here.
