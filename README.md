# Docs Folder

This folder serves two purposes:

- the GitHub Pages site itself
- the source materials and scripts used to build the map

## Live site

- [index.html](./index.html)
- [data](./data/)

The page loads the chunked GeoJSON files from `data/`.

## Source tree

- [Europopulation](./Europopulation/)
  - original ARDECO workspace moved under `docs/`
  - merge outputs
  - source boundaries
  - crosswalk files
  - original helper scripts

- [scripts](./scripts/)
  - wrapper scripts that point at `docs/Europopulation`
  - final Pages dataset build
  - GeoJSON chunk split

The older `original-data` and `supporting-data` folders are retained as copied snapshots, but `docs/Europopulation` is now the main source location.
