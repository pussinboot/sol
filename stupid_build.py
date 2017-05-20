import sys
import os
import subprocess


def rebuild():
    subprocess.call([sys.executable, 'setup.py', 'install'], shell=True)


fname_to_do_what = {
}

if __name__ == '__main__':
    if len(sys.argv) > 1:
        rebuild()
        fname = os.path.split(sys.argv[1])[1]

        if fname in fname_to_do_what:
            fname_to_do_what[fname]()
