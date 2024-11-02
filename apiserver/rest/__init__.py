import os
import sys

root_directory = os.path.abspath('../')
lib_directory = os.path.abspath('../lib')
db_directory = os.path.abspath('../lib/db')
invest_lib_directory = os.path.abspath('./rest/invest')
sys.path.append(root_directory)
sys.path.append(lib_directory)
sys.path.append(db_directory)
sys.path.append(invest_lib_directory)


