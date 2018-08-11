init:
	pip3 install -r requirements.txt

test:
	export DEVELOPMENT=False && export TESTING=True && python3 setup.py nosetests --rednose

run-dev:
	export DEVELOPMENT=True && export TESTING=False && python avionics

run-prod:
	export DEVELOPMENT=False && export TESTING=False && python3 avionics

clean:
	kill $(lsof -t -i :14540) && kill $(lsof -t -i :14550) && kill $(lsof -t -i :14560)	
