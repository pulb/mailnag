#!/bin/bash
main()
{
if [ -f ~/.popper/popper.log ]; then
	rm ~/.popper/popper.log
fi
cd `dirname $0`
python popper.py autostarted >> ~/.popper/popper.log 2>&1 &
}

connection()
{
trap "exit 1" SIGTERM
while ! ping -c1 www.google.com 2>/dev/null 1>&2
	do
		sleep 4.2 # The answer to life, the universe and everything :-)
	done
kill %-
}

connection
main
