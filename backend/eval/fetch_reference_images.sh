#!/usr/bin/env bash
# Pulls a small set of candidate erythema migrans reference images from
# Wikimedia Commons, for sanity-testing the OpenCV pipeline against real
# photos (not synthetic ones) -- NOT for the fairness harness, since none
# of these have Fitzpatrick skin-tone ground truth attached (single stock
# photos, not a labeled dataset). See docs/DATASETS.md for the real
# datasets to use for that.
#
# Written to run OUTSIDE the Claude Code sandbox -- that environment's
# network policy blocks commons.wikimedia.org entirely (confirmed via the
# agent proxy status: "gateway answered 403 to CONNECT (policy denial)"),
# so this script couldn't be run or verified from there. Run it yourself
# and check its output before trusting it.
#
# Update 2026-09-20 (Brett, checked all 5 Commons pages directly): all
# five are now license-verified. Summary -- see per-file entries below
# for the full text:
#   - 2 CDC/PHIL images: public domain, no credit legally required
#     (courtesy credit requested).
#   - 2 CC BY-SA images (Bullseye_Lyme_Disease_Rash.jpg,
#     Lyme_Disease_Rash_on_5_year_old.jpg): usable with a credit line
#     wherever they appear. Share-alike terms apply if an image is
#     edited/built into derivative work (e.g. incorporated into the demo
#     video) rather than just displayed as-is -- if that happens, credit
#     AND the share-alike license need to travel with it.
#   - Erythema_migrans.jpg: public domain, but it's a 200x200px medical
#     illustration, not a photo -- limited value for pipeline testing or
#     the demo.
#   - TASTE FLAG: Lyme_Disease_Rash_on_5_year_old.jpg is a photo of a
#     real child's arm. License permits use, but think about whether it
#     belongs in a public demo video regardless -- a license clearing use
#     isn't the same as it being the right call to feature a minor's
#     photo in competition materials. Worth the team's judgment call, not
#     just a license check, before it goes in anything public-facing.
#
# All five are cleared for local pipeline testing regardless. For
# anything public-facing (video, report), credit lines are needed for
# the 2 CC BY-SA images; the taste question above is separate from the
# license question.
#
# Usage:
#   cd backend/eval
#   ./fetch_reference_images.sh

set -euo pipefail

OUT_DIR="$(dirname "$0")/data/wikimedia_reference"
mkdir -p "$OUT_DIR"

# path,license,verify_url
# All five rows are now verified (Brett, 2026-09-20) -- see header comment.
CANDIDATES=$(cat <<'EOF'
Erythema_migrans_-_erythematous_rash_in_Lyme_disease_-_PHIL_9875.jpg|CONFIRMED public domain (CDC/PHIL #9875, James Gathany; courtesy credit requested, not required)|https://commons.wikimedia.org/wiki/File:Erythema_migrans_-_erythematous_rash_in_Lyme_disease_-_PHIL_9875.jpg
Bullseye_rash_linked_to_Lyme_disease.jpg|CONFIRMED public domain (CDC/PHIL #9874, James Gathany)|https://commons.wikimedia.org/wiki/File:Bullseye_rash_linked_to_Lyme_disease.jpg
Bullseye_Lyme_Disease_Rash.jpg|CC BY-SA 2.5, author Hannah Garrison -- credit line required; share-alike applies if built into derivative work|https://commons.wikimedia.org/wiki/File:Bullseye_Lyme_Disease_Rash.jpg
Lyme_Disease_Rash_on_5_year_old.jpg|CC BY-SA 3.0, author Ltshears -- credit line required, share-alike applies. TASTE FLAG: real photo of a child's arm -- license =/= appropriate for public demo use, use judgment|https://commons.wikimedia.org/wiki/File:Lyme_Disease_Rash_on_5_year_old.jpg
Erythema_migrans.jpg|CONFIRMED public domain (CDC, US federal government work) -- but only 200x200px and a medical illustration, not a photo; limited practical value|https://commons.wikimedia.org/wiki/File:Erythema_migrans.jpg
EOF
)

echo "$CANDIDATES" | while IFS='|' read -r filename license verify_url; do
    echo "=== $filename ==="
    echo "License: $license"
    echo "Verify at: $verify_url"

    # Wikimedia's Special:FilePath redirects to the current full-res file
    # for any File: page, without needing the API or a page-scrape.
    src_url="https://commons.wikimedia.org/wiki/Special:FilePath/${filename}"
    dest="$OUT_DIR/$filename"

    if curl -sSL --fail -o "$dest" "$src_url"; then
        echo "Downloaded to $dest"
    else
        echo "FAILED to download $filename -- skipping"
        rm -f "$dest"
    fi
    echo
done

echo "Done. Review each image's actual Commons page before using it for"
echo "anything beyond local pipeline testing. Images are in $OUT_DIR"
echo "(gitignored -- do not commit third-party images into the repo)."
