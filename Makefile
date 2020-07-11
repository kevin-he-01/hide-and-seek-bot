INCLUDE = bot.py kit.py opponent.py vision.py
SHELL=bash

submit:
	./submit.sh $(INCLUDE)

clean:
	rm -rf out/{*.py,*.zip,__pycache__/}