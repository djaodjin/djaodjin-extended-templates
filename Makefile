# -*- Makefile -*-

-include $(buildTop)/share/dws/prefix.mk

srcDir        ?= .
installTop    ?= $(VIRTUAL_ENV)
binDir        ?= $(installTop)/bin

PYTHON        := $(binDir)/python


install::
	cd $(srcDir) && $(PYTHON) ./setup.py --quiet \
		build -b $(CURDIR)/build install

initdb: install-conf

install-conf:: credentials site.conf

credentials: $(srcDir)/testsite/etc/credentials.conf
	[ -f $@ ] || \
		SECRET_KEY=`python -c 'import sys ; from random import choice ; sys.stdout.write("".join([choice("abcdefghijklmnopqrstuvwxyz0123456789!@#$%^*-_=+") for i in range(50)]))'` ; \
		sed -e "s,\%(SECRET_KEY)s,$${SECRET_KEY}," $< > $@

site.conf: $(srcDir)/testsite/etc/site.conf
	[ -f $@ ] || install -m 644 $< $@

-include $(buildTop)/share/dws/suffix.mk
