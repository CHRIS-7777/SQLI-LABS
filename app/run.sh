#!/usr/bin/env bash
# Helix Group SQLi lab controller:  ./run.sh start | stop | reset | status
cd "$(dirname "$0")" || exit 1
PIDFILE=data/app.pid
LOG=data/app.log

case "$1" in
  start)
    docker compose up -d >/dev/null 2>&1 || { echo "docker compose failed"; exit 1; }
    echo "[*] waiting for MySQL and MSSQL (first start can take a minute or two)..."
    python3 seed.py wait || exit 1
    [ -f data/.seeded ] || { echo "[*] seeding databases..."; python3 seed.py all || exit 1; }
    if [ -f "$PIDFILE" ] && kill -0 "$(cat $PIDFILE)" 2>/dev/null; then echo "[*] app already running"; exit 0; fi
    nohup python3 app.py >"$LOG" 2>&1 &
    echo $! >"$PIDFILE"
    sleep 2
    echo "[+] lab is up:  http://${HOST:-127.0.0.1}:${PORT:-8000}/"
    ;;
  stop)
    [ -f "$PIDFILE" ] && kill "$(cat $PIDFILE)" 2>/dev/null; rm -f "$PIDFILE"
    docker compose stop >/dev/null 2>&1
    echo "[+] stopped"
    ;;
  reset)
    rm -f data/.seeded
    "$0" start
    python3 seed.py all
    echo "[+] databases re-seeded"
    ;;
  status)
    docker compose ps
    [ -f "$PIDFILE" ] && kill -0 "$(cat $PIDFILE)" 2>/dev/null && echo "app: running (pid $(cat $PIDFILE))" || echo "app: stopped"
    ;;
  *)
    echo "usage: $0 {start|stop|reset|status}"
    ;;
esac
