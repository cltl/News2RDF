rm -rf logs && mkdir logs
rm -rf signalmedia_big_rdf && mkdir signalmedia_big_rdf

python conversion.py -f 1 -t 100000 -s 1000 > logs/log1.out 2> logs/log1.err &
sleep 5
python conversion.py -f 100001 -t 200000 -s 1000 > logs/log2.out 2> logs/log2.err &
sleep 5
python conversion.py -f 200001 -t 300000 -s 1000 > logs/log3.out 2> logs/log3.err &
sleep 5
python conversion.py -f 300001 -t 400000 -s 1000 > logs/log4.out 2> logs/log4.err &
sleep 5
python conversion.py -f 400001 -t 500000 -s 1000 > logs/log5.out 2> logs/log5.err &
sleep 5
python conversion.py -f 500001 -t 600000 -s 1000 > logs/log6.out 2> logs/log6.err &
sleep 5
python conversion.py -f 600001 -t 700000 -s 1000 > logs/log7.out 2> logs/log7.err &
sleep 5
python conversion.py -f 700001 -t 800000 -s 1000 > logs/log8.out 2> logs/log8.err &
sleep 5
python conversion.py -f 800001 -t 900000 -s 1000 > logs/log9.out 2> logs/log9.err &
sleep 5
python conversion.py -f 900001 -t 1000000 -s 1000 > logs/log10.out 2> logs/log10.err &
