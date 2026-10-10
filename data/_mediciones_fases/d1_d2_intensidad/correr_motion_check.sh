#!/bin/bash
# Corre motion_check.py (sin cambios) sobre los 11 videos de referencia.
# Salida en data/_mediciones_fases/d1_d2_intensidad/<carpeta>/ (no toca processed_data).
cd "$(dirname "$0")/../../.."
PY=${PY:-python}
$PY - <<'P' | while IFS='|' read carpeta video; do
import sys; sys.path.insert(0,'tests'); import referencia as r
for c,(v,_,_) in r.VIDEOS.items(): print(f"{c}|{v}")
P
  out=data/_mediciones_fases/d1_d2_intensidad/$carpeta
  [ -f "$out/movimiento_$(basename "${video%.*}").xlsx" ] && continue
  serie=$(ls data/processed_data/$carpeta/serie_temporal_*.xlsx | head -1)
  echo "=== $carpeta $(date +%T)"
  $PY scripts/motion_check.py --video "data/raw_videos/$video" --serie "$serie" --output-dir "$out"
done
