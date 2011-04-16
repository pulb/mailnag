#!/bin/bash
main()
{
if [ -f ~/.mailnag/mailnag.log ]; then
	rm ~/.mailnag/mailnag.log
fi
cd `dirname $0`
python mailnag.py autostarted >> ~/.mailnag/mailnag.log 2>&1 &
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
