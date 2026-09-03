"""Generate a local CSV with the same contract as the Unity Catalog table."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from mock_data import generate_mock_journeys  # noqa: E402


if __name__ == "__main__":
    output = ROOT / "data" / "mock_bus_journeys.csv"
    output.parent.mkdir(exist_ok=True)
    frame = generate_mock_journeys()
    frame.to_csv(output, index=False)
    print(f"Wrote {len(frame):,} journeys to {output}")
