REPLAY_DIR="/cygdrive/c/Games/World_of_Tanks/replays/"
OUTPUT_FILE="README.md"

echo "<12 HOURS>"  > ${OUTPUT_FILE}
echo "==========" >> ${OUTPUT_FILE}
python3 wots.py -n nunun_jp,llamananainc,rexasgomyway -o 12 ${REPLAY_DIR} >> ${OUTPUT_FILE}

echo ""                  >> ${OUTPUT_FILE}
echo "<0.9.8 and 0.9.7>" >> ${OUTPUT_FILE}
echo "=================" >> ${OUTPUT_FILE}
python3 wots.py -n nunun_jp,llamananainc,rexasgomyway -v 2  ${REPLAY_DIR} >> ${OUTPUT_FILE}

