all: main # set up the default

SRC = config.py \
      findwave.py \
      inputchan.py \
      level.py \
      plot.py \
      rawwaves.py \
      report.py \
      resamples.py \
      sched.py \
      spectra.py \
      stats.py \
      util.py \
      watch.py \
      main.py


OBJ = $(SRC:.py=.pyc)

LINT = $(SRC:.py=.pylint)

%.pylint: %.py .pylintrc
	/usr/bin/pylint $<
	touch $<lint

.phony: clean

clean: 
	-rm *.pylint *.pyc lint

lint: $(LINT)
	touch lint

test: $(SRC) lint
	/usr/bin/python $(PFLAGS) main.py # this makes the $@.pyc files


main: $(SRC) lint
	/usr/bin/python $(PFLAGS) main.py -i 0829a.csv	# this makes the $@.pyc files
#	/usr/bin/python $(PFLAGS) main.py -i 0829-0909.csv	# this makes the $@.pyc files
#	/usr/bin/python $(PFLAGS) main.py -i 0911-0929.csv	# this makes the $@.pyc files
#	/usr/bin/python $(PFLAGS) main.py -i 0929-1005.csv	# this makes the $@.pyc files
