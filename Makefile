PORT ?= 5001

.PHONY: run restart kill

run:
	python3 app.py

kill:
	-lsof -ti:$(PORT) | xargs kill -9 2>/dev/null; true

restart: kill run
