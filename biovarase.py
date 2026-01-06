#!/usr/bin/env python3
# -*- coding: utf-8 -*-
""" This is the launcher module of Biovarase."""
import sys
#print(sys.path)
#print(sys.executable)
import views.login as login

__author__ = "1966bc aka giuseppe costanzi"
__copyright__ = "Copyleft"
__credits__ = ["hal9000",]
__license__ = "GNU GPL Version 3, 29 June 2007"
__version__ = "4.2"
__maintainer__ = "1966bc"
__email__ = "giuseppecostanzi@gmail.com"
__date__ = "HIEMS MMXXV"
__status__ = "Production"

if __name__ == "__main__":
    login.main()

