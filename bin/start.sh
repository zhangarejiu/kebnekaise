#!/usr/bin/env bash

cd ..
APPHOME=`pwd`
PYTHON_ENV='/usr/bin/python3'

rm -f ${APPHOME}/logs/.halt
#rm -fR ${APPHOME}/logs
mkdir -p ${APPHOME}/logs

${PYTHON_ENV} -m src.main ${APPHOME} &
