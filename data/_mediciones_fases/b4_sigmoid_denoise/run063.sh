cd /home/claude/w/orig
p=data/raw_videos/OK-20260904T142817Z-1-001/OK/Video_063_CTRL1_5V.mp4
for m in sigmoid denoise; do
  ex="--edge-method sigmoid"; [ $m = denoise ] && ex="--denoise"
  o=/home/claude/w/b4/Video_063/$m; rm -rf $o; mkdir -p $o
  s=$(date +%s); python3 main.py --video "$p" --output-dir $o --base-tiempo pts --procesos 2 $ex > $o/main.log 2>&1
  echo "Video_063 $m $(( $(date +%s)-s )) s" >> /home/claude/w/b4/tiempos.txt
done
