import os
import sys


# http://stackoverflow.com/questions/6796492/temporarily-redirect-stdout-stderr
class RedirectStdStreams(object):
    def __init__(self, stdout=None, stderr=None):
        self._stdout = stdout or sys.stdout
        self._stderr = stderr or sys.stderr

    def __enter__(self):
        self.old_stdout, self.old_stderr = sys.stdout, sys.stderr
        self.old_stdout.flush(); self.old_stderr.flush()
        sys.stdout, sys.stderr = self._stdout, self._stderr

    def __exit__(self, exc_type, exc_value, traceback):
        self._stdout.flush(); self._stderr.flush()
        sys.stdout = self.old_stdout
        sys.stderr = self.old_stderr

if __name__ == '__main__':

    # devnull = open(os.devnull, 'w')
    # print('Fubar')
    #
    # with RedirectStdStreams(stdout=devnull, stderr=devnull):
    #     print("You'll never see me")
    #
    # print("I'm back!")

    outfile = open('local_file.txt', 'w')
    print('Printing to stdout. See this in the terminal.')
    with RedirectStdStreams(stdout=outfile, stderr=outfile):
        print('Sending stdout and stderr to file. Did you see me?')
    print('Back to stdout. See this?')