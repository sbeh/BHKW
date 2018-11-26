#!/bin/sh
set -o errexit
#set -o xtrace

alias diff='diff -U 1'

test ! -f data.json
test ! -f parse.js
test ! -f parse_regex.json
cp ../parse.js ../parse_regex.json .
trap 'rm data.json parse.js parse_regex.json' 0

cat >data.json <<EOF
{"time":1542886686555,"data":"TI: 1346 min F: 3562 rpm Tv: 44.9 Tr: 31.0 Ta: 1"}
{"time":1542886686708,"data":"02.7 Tt: 99.9 Tb: 57.7 h: 576 \n"}
{"time":1542886986567,"data":"TI: 1351 min F: 3512 rpm Tv: 44.9 Tr: 30.9 Ta: 103.2 Tt: 100.3 Tb: 57.7 h: 576 \n"}
{"time":1542887286630,"data":"TI: 1356 min F: 3529 rpm Tv: 45.1 Tr: 31.0 Ta: 103.3 Tt: 100.8 T"}
{"time":1542887286784,"data":"b: 57.7 h: 576 \n"}
EOF

node parse.js >data.log &
trap 'set +o errexit; kill %1; wait %1; rm data.json data.log parse.js parse_regex.json' 0

sleep 1
head -n 3 data.parsed | diff - data.log

echo -n '{"time":1542887586538,"data":"TI: 1361 min F: 3500 rpm Tv: 45.0 Tr: 31"}
{"time":1542887586692,"data":".0 Ta: 10' >>data.json
sleep 1
head -n 3 data.parsed | diff - data.log

echo -n '3.5 Tt: 100.8 Tb: 57.7 h' >>data.json
sleep 1
head -n 3 data.parsed | diff - data.log

cat >>data.json <<EOF
: 576 \n"}
{"time":1542887886665,"data":"TI: 1366 min F: 3536 rpm Tv: 45.1 Tr: 31.0 Ta: 103.3 Tt: 100.9 Tb: 58.0 h: 576 \n"}
EOF
sleep 1
diff data.parsed data.log

echo ===================
echo === TEST PASSED ===
echo ===================