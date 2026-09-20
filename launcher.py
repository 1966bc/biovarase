#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# project:  biovarase
# authors:  Giuseppe Costanzi (1966bc)
# licence:  GPL-3.0-or-later, see LICENSE
# -----------------------------------------------------------------------------
import os
import sys
import inspect
import subprocess
from threading import Thread


class Launcher:
    def __init__(self):
        self.launch_result = None  

    def launch(self, path):
        # default: fallimento, verrà messo a True solo in caso di successo
        self.launch_result = False

        thread = Thread(target=self._open_file, args=(path,))
        thread.start()
        thread.join()  # Wait for the thread to complete

        return self.launch_result

    def _open_file(self, path):
        try:
            if not os.path.exists(path):
                # file inesistente → fallimento esplicito
                self.launch_result = False
                return

            if os.name == "posix":
                ret = subprocess.call(["xdg-open", path])
                # su Linux uso il codice di ritorno del comando
                self.launch_result = (ret == 0)
            elif os.name == "nt":  # Windows
                os.startfile(path)
                self.launch_result = True

        except (OSError, subprocess.SubprocessError) as e:
            self.on_log(inspect.stack()[0][3],
                        e,
                        type(e),
                        sys.modules[__name__])
            self.launch_result = False



def main():

    foo = Launcher()
    print(foo)
    input('end')
       
if __name__ == "__main__":
    main()                
