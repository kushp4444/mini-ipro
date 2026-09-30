"""Load a DICOM CT series into a 3D numpy volume.

A CT scan is one DICOM *series*: hundreds of slice files that we sort along the
scan axis and stack. Intensities are converted to Hounsfield Units (HU), the
standard CT scale where air = -1000, water = 0.
"""
import numpy as np
import pydicom
from pathlib import Path


def load_series(series_dir):
    """Read every .dcm in a directory, sort head->toe, stack into a volume.

    Returns (volume, meta) where volume is a 3D int16 array in Hounsfield Units
    and meta is a dict of geometry info used by the QC stage.
    """
    series_dir = Path(series_dir)
    files = [pydicom.dcmread(str(f)) for f in sorted(series_dir.glob("*.dcm"))]
    if not files:
        raise ValueError(f"No DICOM files found in {series_dir}")

    # Sort slices by physical position along the scan axis
    files.sort(key=lambda d: float(d.ImagePositionPatient[2]))

    volume = np.stack([d.pixel_array for d in files]).astype(np.float32)

    # Rescale to Hounsfield Units: HU = pixel * slope + intercept
    slope = float(getattr(files[0], "RescaleSlope", 1))
    intercept = float(getattr(files[0], "RescaleIntercept", 0))
    volume = (volume * slope + intercept).astype(np.int16)

    meta = {
        "n_slices": len(files),
        "rows": int(files[0].Rows),
        "columns": int(files[0].Columns),
        "slice_thickness": float(getattr(files[0], "SliceThickness", 0)),
        "positions": [float(d.ImagePositionPatient[2]) for d in files],
        "patient_id": str(getattr(files[0], "PatientID", "unknown")),
    }
    return volume, meta
