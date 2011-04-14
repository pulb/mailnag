#!/bin/bash
if [ ! -d ~/.popper ]; then
	mkdir ~/.popper
fi
if [ -f ~/.popper/popper_config.log ]; then
	rm ~/.popper/popper_config.log
fi
cd `dirname $0`
python popper_config.py >> ~/.popper/popper_config.log 2>&1
if [ $? -eq 0 ]; then
	# Restart Popper.py
	if [ -f ~/.popper/popper.pid ]; then
		kill $(cat ~/.popper/popper.pid)
	fi
	if [ -f ~/.popper/popper.log ]; then
		rm ~/.popper/popper.log
	fi
	python popper.py >> ~/.popper/popper.log 2>&1 &
else
	echo Popper-Configurator discarded
fi
