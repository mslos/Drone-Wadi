init:
	pip install -r requirements.txt

test:
	export DEVELOPMENT=False && export TESTING=True && export HARDWARE_TEST=False && python setup.py nosetests --rednose

run-dev:
	export DEVELOPMENT=True && export TESTING=False && export HARDWARE_TEST=False && python avionics

run-prod:
	export DEVELOPMENT=False && export TESTING=False && export HARDWARE_TEST=False && python3 avionics

run-hardware-test:
	export DEVELOPMENT=False && export TESTING=False && export HARDWARE_TEST=True && python avionics

clean:
	kill $(lsof -t -i :14540) && kill $(lsof -t -i :14550) && kill $(lsof -t -i :14560)
