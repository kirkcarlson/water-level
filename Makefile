all: main # set up the default

SRC = average.py \
      cluster.py \
      config.py \
      dominant.py \
      findwave.py \
      highlow.py \
      influx.py \
      inputchan.py \
      lowpass.py \
      mysched.py \
      report.py \
      resamples.py \
      stats.py \
      trap.py \
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
