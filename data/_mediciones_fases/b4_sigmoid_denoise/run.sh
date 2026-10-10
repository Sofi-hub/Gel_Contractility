cd /home/claude/w/orig
for v in "Video_prueba:data/raw_videos/Video_prueba.mp4" "Video_063:data/raw_videos/OK-20260904T142817Z-1-001/OK/Video_063_CTRL1_5V.mp4"; do
 n=${v%%:*}; p=${v#*:}
 for m in base sigmoid denoise; do
  ex=""; [ $m = sigmoid ] && ex="--edge-method sigmoid"; [ $m = denoise ] && ex="--denoise"
  o=/home/claude/w/b4/$n/$m; mkdir -p $o
  s=$(date +%s); python3 main.py --video "$p" --output-dir $o --base-tiempo pts --procesos 2 $ex > $o/main.log 2>&1
  echo "$n $m $(( $(date +%s)-s )) s" >> /home/claude/w/b4/tiempos.txt
 done
done
echo FIN >> /home/claude/w/b4/tiempos.txt
