install:
	pip install Pyro4
	python3 setup.py install
	mkdir -p /usr/local/share/MaxiNet
	cp -rv fogbed/maxinet/Frontend/examples /usr/local/share/MaxiNet/
	chmod +x /usr/local/share/MaxiNet/examples/*
	cp share/MaxiNet-cfg-sample /usr/local/share/MaxiNet/MaxiNet.cfg
	cp share/maxinet_plot.py /usr/local/share/MaxiNet/

clean:
	-rm -rf build
	-rm -rf dist
	-rm -rf fogbed.egg-info

uninstall:
	rm -rf /usr/local/lib/python3.8/dist-packages/fogbed-*/
	rm -rf /usr/local/lib/python3.8/dist-packages/Pyro4*/
	rm -rf /usr/local/share/MaxiNet