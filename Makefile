# -*- Makefile -*-

-include $(buildTop)/share/dws/prefix.mk

srcDir        ?= $(realpath .)
installTop    ?= $(if $(VIRTUAL_ENV),$(VIRTUAL_ENV),$(abspath $(srcDir))/.venv)
binDir        ?= $(installTop)/bin
libDir        ?= $(installTop)/lib
CONFIG_DIR    ?= $(installTop)/etc/testsite
LOCALSTATEDIR ?= $(installTop)/var
# because there is no site.conf
RUN_DIR       ?= $(abspath $(srcDir))

installDirs   ?= install -d
installFiles  ?= install -p -m 644
NPM           ?= npm
PYTHON        := python
PIP           := pip
TWINE         := twine

ASSETS_DIR    := $(srcDir)/htdocs/static
DB_NAME       ?= $(RUN_DIR)/db.sqlite

MANAGE        := TESTSITE_SETTINGS_LOCATION=$(CONFIG_DIR) RUN_DIR=$(RUN_DIR) $(PYTHON) manage.py

# Django 1.7,1.8 sync tables without migrations by default while Django 1.9
# requires a --run-syncdb argument.
# Implementation Note: We have to wait for the config files to be installed
# before running the manage.py command (else missing SECRECT_KEY).
RUNSYNCDB     = $(if $(findstring --run-syncdb,$(shell cd $(srcDir) && $(MANAGE) migrate --help 2>/dev/null)),--run-syncdb,)


install::
	cd $(srcDir) && $(PIP) install .


install-conf:: $(DESTDIR)$(CONFIG_DIR)/credentials \
                $(DESTDIR)$(CONFIG_DIR)/gunicorn.conf
	$(installDirs) $(DESTDIR)$(LOCALSTATEDIR)/db
	$(installDirs) $(DESTDIR)$(LOCALSTATEDIR)/run
	$(installDirs) $(DESTDIR)$(LOCALSTATEDIR)/log/gunicorn


dist::
	$(PYTHON) -m build
	$(TWINE) check dist/*
	$(TWINE) upload dist/*


build-assets: vendor-assets-prerequisites


clean:: clean-dbs
	[ ! -f $(srcDir)/package-lock.json ] || rm $(srcDir)/package-lock.json
	find $(srcDir) -name '__pycache__' -exec rm -rf {} +
	find $(srcDir) -name '*~' -exec rm -rf {} +

clean-dbs:
	[ ! -f $(DB_NAME) ] || rm $(DB_NAME)
	[ ! -f $(srcDir)/testsite-app.log ] || rm $(srcDir)/testsite-app.log
	rm -rf $(RUN_DIR)/themes $(srcDir)/htdocs/media


vendor-assets-prerequisites: $(srcDir)/testsite/package.json


$(DESTDIR)$(CONFIG_DIR)/credentials: $(srcDir)/testsite/etc/credentials
	$(installDirs) $(dir $@)
	@if [ ! -f $@ ] ; then \
		sed \
		-e "s,\%(SECRET_KEY)s,`$(PYTHON) -c 'import sys ; from random import choice ; sys.stdout.write("".join([choice("abcdefghijklmnopqrstuvwxyz0123456789!@#$%^*-_=+") for i in range(50)]))'`," \
			$< > $@ ; \
	else \
		echo "warning: We are keeping $@ intact but $< contains updates that might affect behavior of the testsite." ; \
	fi


$(DESTDIR)$(CONFIG_DIR)/gunicorn.conf: $(srcDir)/testsite/etc/gunicorn.conf
	$(installDirs) $(dir $@)
	[ -f $@ ] || sed \
		-e 's,%(LOCALSTATEDIR)s,$(LOCALSTATEDIR),' $< > $@


initdb: clean-dbs
	$(installDirs) $(dir $(DB_NAME))
	cd $(srcDir) && $(MANAGE) migrate $(RUNSYNCDB) --noinput
	cd $(srcDir) && $(MANAGE) loaddata testsite/fixtures/default-db.json
	$(installDirs) $(RUN_DIR)/themes/djaodjin-extended-templates
	$(installDirs) $(srcDir)/htdocs/media/vendor
	$(installFiles) $(ASSETS_DIR)/vendor/bootstrap.css $(srcDir)/htdocs/media/vendor

doc:
	$(installDirs) build/docs
	cd $(srcDir) && sphinx-build -b html ./docs $(PWD)/build/docs

vendor-assets-prerequisites: $(libDir)/.npm/djaodjin-extended-templates-packages


$(libDir)/.npm/djaodjin-extended-templates-packages: $(srcDir)/testsite/package.json
	$(installFiles) $^ $(libDir)
	$(NPM) install --loglevel verbose --cache $(libDir)/.npm --tmp $(libDir)/tmp --prefix $(libDir)
	$(installDirs) -d $(ASSETS_DIR)/fonts $(ASSETS_DIR)/../media/fonts $(ASSETS_DIR)/vendor/bootstrap/mixins $(ASSETS_DIR)/img/bootstrap-colorpicker
	$(installFiles) $(libDir)/node_modules/ace-builds/src/ace.js $(ASSETS_DIR)/vendor
	$(installFiles) $(libDir)/node_modules/ace-builds/src/ext-language_tools.js $(ASSETS_DIR)/vendor
	$(installFiles) $(libDir)/node_modules/ace-builds/src/ext-modelist.js $(ASSETS_DIR)/vendor
	$(installFiles) $(libDir)/node_modules/ace-builds/src/ext-emmet.js $(ASSETS_DIR)/vendor
	$(installFiles) $(libDir)/node_modules/ace-builds/src/theme-monokai.js $(ASSETS_DIR)/vendor
	$(installFiles) $(libDir)/node_modules/ace-builds/src/mode-html.js $(ASSETS_DIR)/vendor
	$(installFiles) $(libDir)/node_modules/ace-builds/src/mode-css.js $(ASSETS_DIR)/vendor
	$(installFiles) $(libDir)/node_modules/ace-builds/src/mode-javascript.js $(ASSETS_DIR)/vendor
	$(installFiles) $(libDir)/node_modules/ace-builds/src/worker-html.js $(ASSETS_DIR)/vendor
	$(installFiles) $(libDir)/node_modules/bootstrap/dist/css/bootstrap.css $(ASSETS_DIR)/vendor
	$(installFiles) $(libDir)/node_modules/bootstrap/dist/js/bootstrap.js $(ASSETS_DIR)/vendor
	$(installFiles) $(libDir)/node_modules/bootstrap-colorpicker/dist/img/bootstrap-colorpicker/*.png $(ASSETS_DIR)/img/bootstrap-colorpicker
	$(installFiles) $(libDir)/node_modules/bootstrap-colorpicker/dist/css/bootstrap-colorpicker.css $(ASSETS_DIR)/vendor
	$(installFiles) $(libDir)/node_modules/bootstrap-colorpicker/dist/js/bootstrap-colorpicker.js $(ASSETS_DIR)/vendor
	$(installFiles) $(libDir)/node_modules/dropzone/dist/dropzone.css $(ASSETS_DIR)/vendor
	$(installFiles) $(libDir)/node_modules/dropzone/dist/dropzone.js $(ASSETS_DIR)/vendor
	$(installFiles) $(libDir)/node_modules/font-awesome/css/font-awesome.css $(ASSETS_DIR)/vendor
	$(installFiles) $(libDir)/node_modules/font-awesome/fonts/* $(ASSETS_DIR)/fonts
	$(installFiles) $(libDir)/node_modules/hallo/dist/hallo.js $(ASSETS_DIR)/vendor
	$(installFiles) $(libDir)/node_modules/jquery/dist/jquery.js $(ASSETS_DIR)/vendor
	$(installFiles) $(libDir)/node_modules/jquery-ui-touch-punch/jquery.ui.touch-punch.js $(ASSETS_DIR)/vendor
	$(installFiles) $(libDir)/node_modules/jquery.selection/dist/jquery.selection.js $(ASSETS_DIR)/vendor
	$(installFiles) $(libDir)/node_modules/less/dist/less.js $(ASSETS_DIR)/vendor
	$(installFiles) $(libDir)/node_modules/pagedown/Markdown.Converter.js $(libDir)/node_modules/pagedown/Markdown.Sanitizer.js $(ASSETS_DIR)/vendor
	$(installFiles) $(libDir)/node_modules/rangy/lib/rangy-core.js $(ASSETS_DIR)/vendor
	$(installFiles) $(libDir)/node_modules/textarea-autosize/dist/jquery.textarea_autosize.js $(ASSETS_DIR)/vendor
	$(installFiles) $(libDir)/node_modules/vue/dist/vue.js $(ASSETS_DIR)/vendor
	touch $@


.PHONY: all check dist doc install
