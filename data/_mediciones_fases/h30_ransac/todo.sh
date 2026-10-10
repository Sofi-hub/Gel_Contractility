cd /home/claude/w/repo
for var in k2 k4 trials1000; do
while IFS='|' read c v; do
  o=/home/claude/w/h30/$var/$c; mkdir -p $o
  s=$(date +%s); python3 /home/claude/w/h30/correr.py $var "$v" $o > $o/main.log 2>&1
  echo "$var $c $(( $(date +%s)-s ))s" >> /home/claude/w/h30/progreso.txt
done < /home/claude/w/v11/lista.txt
done
echo FIN >> /home/claude/w/h30/progreso.txt
