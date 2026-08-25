# VeraGrid documentation

The documentation is built using sphinx.

1. Install [requirements.txt](requirements.txt) to be able to do it.
2. Run [make.py](make.py)
3. Inspect the [build](build) directory
4. Open [index.html](build/html/index.html) 
5. Navigate and see if it is what you wanted.


How to build the automatic API code docs:

`sphinx-apidoc -o ./rst_source/api/auto ../src/VeraGridEngine --tocfile modules`

This will automatically create the files at [doc/rst_source/api/auto](rst_source/api/auto)


The build configuration is stored at [conf.py](conf.py)