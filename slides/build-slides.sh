#!/usr/bin/env sh
#
# Build every published Marp deck into the Antora attachments directory.
#
# Run it from slides/, or through `npm run build:html`, which is what CI does.
# The output is build output: site/modules/ROOT/attachments/ is gitignored and
# nothing here should ever be committed.
#
# Two things to know before editing this file.
#
# 1. Marp copies a relative image path into its HTML verbatim and never copies
#    the image file. So every directory a deck reaches with `../` has to be
#    mirrored under attachments/ at the same depth. That is what copy_assets
#    below does, and why the mirrored paths look redundant. See the section
#    "The one odd path, and why it is not a mistake" in site/README.md.
#
# 2. Decks under background/ emit one directory deeper than workshop decks, so
#    their `../` references need one more `..` than a workshop deck's. There are
#    two such references today, in background/governance/auth-sync-slides.md and
#    background/connectors/09-neo4j-connectors-slides.md.

set -eu

MARP="./node_modules/.bin/marp"
ATTACH="../site/modules/ROOT/attachments"
OUT="$ATTACH/slides"

# Workshop decks, in run-of-show order. One output directory per topic folder.
WORKSHOP_TOPICS="overview-business-story overview-knowledge-graph overview-lakehouse-to-graph overview-architecture overview-graphrag overview-agent overview-agent-memory overview-mcp"

build_decks() {
  for topic in $WORKSHOP_TOPICS; do
    echo "  building $topic"
    "$MARP" --allow-local-files -I "$topic" -o "$OUT/$topic"
  done

  # background/ is passed whole. Marp recurses and preserves the subdirectory
  # structure, so this emits background/connectors/, background/governance/ and
  # background/kg-construction/.
  echo "  building background"
  "$MARP" --allow-local-files -I background -o "$OUT/background"
}

copy_assets() {
  # slides/images/, reached as ../images/ from a workshop topic folder.
  mkdir -p "$OUT/images"
  cp images/* "$OUT/images/"

  # slides/databricks-in-depth/, reached as ../databricks-in-depth/ from a
  # workshop topic folder and as ../../databricks-in-depth/ from background/.
  # Both resolve to the same place, so one copy serves both.
  mkdir -p "$OUT/databricks-in-depth"
  cp databricks-in-depth/*.svg databricks-in-depth/*.png "$OUT/databricks-in-depth/"

  # slides/aircraft/, reached as ../aircraft/ from a workshop topic folder.
  mkdir -p "$OUT/aircraft"
  cp aircraft/*.svg "$OUT/aircraft/"

  # site/modules/ROOT/images/, reached as ../../site/modules/ROOT/images/.
  # Copied whole rather than file by file so that adding an image reference to a
  # deck cannot silently ship a broken link.
  mkdir -p "$ATTACH/site/modules/ROOT/images"
  cp ../site/modules/ROOT/images/*.svg "$ATTACH/site/modules/ROOT/images/"

  # The repository root images/, reached as ../../images/.
  mkdir -p "$ATTACH/images"
  cp ../images/*.svg "$ATTACH/images/"
}

# Start from empty. Stale HTML built from folders that have since been renamed
# is how the published site ended up serving decks nobody could find the source
# of, and a clean slate is the only thing that prevents a repeat.
echo "clearing $ATTACH"
rm -rf "$ATTACH"

echo "building decks"
build_decks

echo "copying assets"
copy_assets

echo "done. $(find "$OUT" -name '*.html' | wc -l | tr -d ' ') decks in $OUT"
