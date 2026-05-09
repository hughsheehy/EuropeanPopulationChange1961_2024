# European Population Change 1961–2024

An interactive web map visualizing population changes across European local administrative units (LAUs) over six decades.

## Features

- **Interactive map** powered by MapLibre GL
- **Historical data** from 1961 to 2024 based on ARDECO dataset
- **LAU boundaries** covering multiple boundary versions (2011, 2021, 2024)
- **Population decline visualization** with color-coded regions
- **Responsive design** for desktop and mobile

## Live Site

View the map: [GitHub Pages deployment](https://hughsheehy.github.io/EuropeanPopulationChange1961_2024/)

## Project Structure

```
.
├── index.html                 # Main map application
├── data/                      # Pre-processed GeoJSON chunks for the map
├── Europopulation/            # Primary source materials
│   ├── ARDECO datasets        # Population time-series data
│   ├── LAU boundary files     # Administrative unit boundaries
│   ├── Processed outputs      # Merged and crosswalked datasets
│   └── Helper scripts         # Data transformation utilities
├── scripts/                   # Dataset build and processing pipeline
├── original-data/             # Snapshot of original source data
└── supporting-data/           # Auxiliary datasets and crosswalks
```

## Data Sources

- **ARDECO** (Analysis of Regional Dynamics in the European Union Concerning Objective 1): European population and regional economic data
- **LAU Boundaries**: Eurostat LAU administrative unit boundaries (2011, 2021, 2024 versions)
- **UK crosswalks**: Custom mapping for UK local authority changes

## Technical Stack

- **Frontend**: MapLibre GL (vector maps), vanilla JavaScript
- **Data format**: GeoJSON (chunked for performance)
- **Styling**: Custom CSS with gradient backgrounds
- **Hosting**: GitHub Pages
- **Storage**: Large files managed with Git LFS

## Setup & Development

### Prerequisites
- Git (with Git LFS support)
- Python 3.10+ (for data processing, optional)

### Installation

```bash
git clone https://github.com/hughsheehy/EuropeanPopulationChange1961_2024.git
cd EuropeanPopulationChange1961_2024
git lfs install  # Set up Git LFS
git lfs pull     # Download large data files
```

### Running Locally

Open `index.html` in a modern web browser, or use a local server:

```bash
python -m http.server 8000
# Visit http://localhost:8000
```

### Data Processing

The `scripts/` directory contains Python utilities for:
- Building the map dataset from source ARDECO files
- Simplifying GeoJSON for web performance
- Splitting data into manageable chunks (the `ARDECO_change_*_part*.geojson` files loaded by the map)
- Creating crosswalks for boundary changes

To regenerate the map data:

```bash
python scripts/build_pages_map_dataset.py
```

This generates the chunked GeoJSON files that the map loads.

## Large Files & Storage

### On GitHub (Git LFS)
The map requires the following files to function, stored with **Git LFS** (~113 MB):
- `data/ARDECO_change_1961_2024_part1.geojson` – 34 MB
- `data/ARDECO_change_1961_2024_part2.geojson` – 31 MB
- `data/ARDECO_change_1961_2024_part3.geojson` – 36 MB
- `ARDECO_Local_Population_Time-Series–1961-2024.csv` files – 5.7 MB each

When you clone with `git lfs pull`, these files are automatically downloaded.

### Local Only (Not on GitHub)
Large source/processing files (>100MB) are excluded from version control:
- Full merged GeoJSON files (ARDECO and LAU boundaries)
- High-resolution boundary files
- Complete hybrid datasets

These remain on your local machine for data processing but are not pushed to GitHub. Regenerate them using `scripts/build_pages_map_dataset.py` if needed.

## Contributing

This is a personal research project. For feedback or issues, please open a GitHub issue.

## License

Data sources (ARDECO, Eurostat) are subject to their respective open data licenses.
