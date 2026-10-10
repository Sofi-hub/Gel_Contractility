cd /home/claude/w/repo
python3 - <<'PY' > /home/claude/w/v11/lista.txt
import sys; sys.path.insert(0,'tests'); import referencia as ref
for c,(v,_,_) in ref.VIDEOS.items(): print(c+"|"+str(ref.CRUDOS/v))
PY
while IFS='|' read c v; do
  o=/home/claude/w/v11/$c; mkdir -p $o
  python3 /home/claude/w/v11/correr.py "$v" $o $o/info.json > $o/main.log 2>&1
  echo "$c listo $(date +%H:%M)" >> /home/claude/w/v11/progreso.txt
done < /home/claude/w/v11/lista.txt
echo FIN >> /home/claude/w/v11/progreso.txt
