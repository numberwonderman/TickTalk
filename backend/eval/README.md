# Fairness eval harness

Measures whether the OpenCV segmentation/feature-extraction stage
(`backend/app/vision/`) behaves consistently across Fitzpatrick skin-tone
groups. See the module docstring in `harness.py` for the honest scope: this
does not measure Lyme-detection accuracy (we don't have EM-labeled data —
see `docs/DATASETS.md`), only whether the *segmentation itself* works
evenly, which is a real, checkable question on its own.

## Status

The harness is built and unit-tested against synthetic images
(`backend/tests/test_eval_harness.py`) — that proves the aggregation logic
is correct, not that the pipeline is actually fair. It hasn't been run
against real data yet because DDI/PASSION/Fitzpatrick17k haven't been
downloaded into this repo (`docs/DATASETS.md` Milestone 1).

## Running it once you have real data

1. Get images from one or more of the datasets in `docs/DATASETS.md`,
   re-verifying each one's license/access terms at the source first.
2. Build a manifest CSV next to them:

   ```csv
   image_path,fitzpatrick_skin_type,lesion_present
   ddi/images/000001.png,V,true
   ddi/images/000002.png,II,true
   ```

   (`fitzpatrick_skin_type` should come from the dataset's own labels —
   DDI and PASSION both provide this; don't infer skin tone from the image
   yourself, per the brief's requirement that fairness reporting use real
   ground truth.)

3. Run:

   ```bash
   cd backend
   PYTHONPATH=. python eval/harness.py path/to/manifest.csv --out report.csv
   ```

4. The printed report groups by skin type and shows segmentation detection
   rate plus mean feature values per group. A >15 percentage point gap in
   detection rate between groups prints a fairness flag — treat that as a
   blocker, not a footnote, if it shows up.
