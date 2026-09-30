# Data (git-ignored — nothing under here is ever committed)

## What to download

The **NSCLC-Radiomics** collection from The Cancer Imaging Archive (TCIA):

1. Go to https://www.cancerimagingarchive.net/collection/nsclc-radiomics/
2. Download with the **NBIA Data Retriever** (linked on the collection page).
   It's tens of GB for the full 422 patients — start with a subset while iterating
   (the pipeline's `--subset` flag handles this).
3. You need three things per patient:
   - the **CT series** (hundreds of `.dcm` slice files),
   - the **RTSTRUCT** file (the doctor's tumor outline),
   - the **clinical data** (survival time + event indicator per patient ID).

## Expected layout

```
data/raw/
├── <PATIENT_ID>/
│   ├── ct/          # the DICOM slice files
│   └── rtstruct.dcm # the tumor outline file
└── clinical.csv     # patient_id, survival time, event indicator columns
```

The NBIA downloader won't produce exactly this layout — reorganize once after
downloading, then update `src/pipeline.py::iter_patients` if your layout differs.

## Column names

Check your `clinical.csv`'s actual column names and set them when running the
survival stage:

```bash
python -m src.pipeline --stage survival --duration-col <time_col> --event-col <event_col>
```
