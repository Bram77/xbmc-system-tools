import subprocess
import log
from inspect import stack

def run(command, returnBool = False):
    process = subprocess.Popen(command,
                shell=True,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                close_fds=True)
    output, error = process.communicate()
    if error.strip():
        log.error(error.strip(), stack()[0][3])
        return False
    log.debug(output.strip(), stack()[0][3])
    output = True if not output else output.strip()
    return True if returnBool else output


