# -*- Makefile -*-

-include $(buildTop)/share/dws/prefix.mk

srcDir        ?= .
installTop    ?= $(VIRTUAL_ENV)
binDir        ?= $(installTop)/bin

PYTHON        := $(binDir)/python
CXXFLAGS      += -g

bins          := podofo-flatform

install::
	cd $(srcDir) && $(PYTHON) ./setup.py --quiet \
		build -b $(CURDIR)/build install

podofo-flatform: podofo-flatform.cc \
    -lpodofo -lfreetype -lfontconfig -ljpeg -lcrypto -lidn -lz

-include $(buildTop)/share/dws/suffix.mk
