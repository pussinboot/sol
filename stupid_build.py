import sys
import os
import subprocess


def rebuild(top_dir):
    os.chdir(top_dir)
    subprocess.call([sys.executable, 'setup.py', 'install'], shell=True)


fname_to_do_what = {
}

if __name__ == '__main__':
    if len(sys.argv) > 1:
        top_dir = os.path.split(sys.argv[0])[0]
        rebuild(top_dir)
        fname = os.path.split(sys.argv[1])[1]

        if fname in fname_to_do_what:
            fname_to_do_what[fname]()
        else:
            pass
            # subprocess.call(["sol"], shell=True) # not quite.. need to exec inside virtualenv
