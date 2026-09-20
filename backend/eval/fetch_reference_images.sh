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
# IMPORTANT: this script does NOT verify licenses for you. Before using
# any downloaded image beyond your own local pipeline testing (e.g. in
# the demo video, in a public report), open the file's Commons page
# yourself and read its actual license tag -- do not trust the guess
# below.
#
# Usage:
#   cd backend/eval
#   ./fetch_reference_images.sh

set -euo pipefail

OUT_DIR="$(dirname "$0")/data/wikimedia_reference"
mkdir -p "$OUT_DIR"

# path,license_guess,verify_url
# license_guess is NOT verified -- see the header comment above.
CANDIDATES=$(cat <<'EOF'
Erythema_migrans_-_erythematous_rash_in_Lyme_disease_-_PHIL_9875.jpg|likely public domain (CDC/PHIL, US federal government work)|https://commons.wikimedia.org/wiki/File:Erythema_migrans_-_erythematous_rash_in_Lyme_disease_-_PHIL_9875.jpg
Bullseye_rash_linked_to_Lyme_disease.jpg|UNKNOWN -- check the page|https://commons.wikimedia.org/wiki/File:Bullseye_rash_linked_to_Lyme_disease.jpg
Bullseye_Lyme_Disease_Rash.jpg|UNKNOWN -- check the page|https://commons.wikimedia.org/wiki/File:Bullseye_Lyme_Disease_Rash.jpg
Lyme_Disease_Rash_on_5_year_old.jpg|UNKNOWN -- check the page|https://commons.wikimedia.org/wiki/File:Lyme_Disease_Rash_on_5_year_old.jpg
Erythema_migrans.jpg|UNKNOWN -- check the page|https://commons.wikimedia.org/wiki/File:Erythema_migrans.jpg
EOF
)

echo "$CANDIDATES" | while IFS='|' read -r filename license_guess verify_url; do
    echo "=== $filename ==="
    echo "License (unverified guess): $license_guess"
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
