#!/usr/bin/env bash
# Publish only after verifying the uploaded PDF and checksum.
set -euo pipefail
source scripts/lib/common.sh
: "${GH_REPO:?}" "${TAG:?}" "${COMMIT:?}" "${BUILD_DIR:?}"
is_strict_semver "$TAG" || die "Invalid version: $TAG"
[ "$(jq -r '.commit' "$BUILD_DIR/build-info.json")" = "$COMMIT" ] || die "Build commit mismatch"
asset="${GH_REPO#*/}-$TAG.pdf"
work="$(mktemp -d)"
cp "$BUILD_DIR/main.pdf" "$work/$asset"
(cd "$work" && sha256sum "$asset" > "$asset.sha256")
digest="$(cut -d' ' -f1 "$work/$asset.sha256")"
[ "$digest" = "$(jq -r '.pdfs.a4.sha256' "$BUILD_DIR/build-info.json")" ] || die "Build checksum mismatch"

if gh api "repos/$GH_REPO/git/ref/tags/$TAG" > /dev/null 2>&1; then
  [ "$(tag_commit "$GH_REPO" "$TAG")" = "$COMMIT" ] || die "Tag points to another commit"
else
  gh api -X POST "repos/$GH_REPO/git/refs" -f ref="refs/tags/$TAG" -f sha="$COMMIT" > /dev/null
fi

# A failed upload can be retried at the same commit without replacing a published release.
if gh release view "$TAG" --json isDraft --jq '.isDraft' > "$work/draft" 2>/dev/null; then
  [ "$(cat "$work/draft")" = true ] || die "Version is already published"
else
  printf '微積分の体系的解説 %s\n\nCommit: %s\nBuild: %s\n\nPDFとSHA-256を同梱しています。\n' \
    "$TAG" "$COMMIT" "$(jq -r '.built_at' "$BUILD_DIR/build-info.json")" > "$work/notes.md"
  gh release create "$TAG" --draft --target "$COMMIT" --title "$TAG" --notes-file "$work/notes.md"
fi
gh release upload "$TAG" "$work/$asset" "$work/$asset.sha256" --clobber
mkdir -p "$work/verify"
gh release download "$TAG" --pattern '*.pdf' --pattern '*.pdf.sha256' --dir "$work/verify"
gh api "repos/$GH_REPO/releases/tags/$TAG" > "$work/release.json"
python3 scripts/verify-release-assets.py "$work/verify" --release-json "$work/release.json"
cmp "$work/$asset.sha256" "$work/verify/$asset.sha256"
[ "$(tag_commit "$GH_REPO" "$TAG")" = "$COMMIT" ] || die "Tag moved during publishing"
gh release edit "$TAG" --draft=false --latest
