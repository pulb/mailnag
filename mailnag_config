#!/bin/bash
if [ ! -d ~/.mailnag ]; then
	mkdir ~/.mailnag
fi
if [ -f ~/.mailnag/mailnag_config.log ]; then
	rm ~/.mailnag/mailnag_config.log
fi
cd `dirname $0`
python mailnag_config.py >> ~/.mailnag/mailnag_config.log 2>&1
if [ $? -eq 0 ]; then
	# Restart mailnag.py
	if [ -f ~/.mailnag/mailnag.pid ]; then
		kill $(cat ~/.mailnag/mailnag.pid)
	fi
	if [ -f ~/.mailnag/mailnag.log ]; then
		rm ~/.mailnag/mailnag.log
	fi
	python mailnag.py >> ~/.mailnag/mailnag.log 2>&1 &
else
	echo mailnag-config discarded
fi
