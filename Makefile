install:
	python3 setup.py install
	make clean

clean:
	rm -rf build
	rm -rf dist
	rm -rf fogbed.egg-info

update:
	make uninstall
	git pull
	make install

uninstall:
	rm -rf pox/
	rm -rf /usr/local/lib/python3.8/dist-packages/fogbed*
	rm -rf /usr/local/lib/python3.8/dist-packages/MaxiNet*/
	rm -rf /usr/local/lib/python3.8/dist-packages/Pyro4*/
	rm -rf /usr/local/share/MaxiNet