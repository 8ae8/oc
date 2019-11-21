import re
import subprocess
from threading import Thread
from time import sleep, time as now


def ping(ping_address, timeout):
    timeout_sec = timeout / 1000
    t0 = now()
    process = subprocess.Popen("ping -c 1 " + ping_address, stdout=subprocess.PIPE, shell=True)
    result = list()
    t = Thread(target=read_ping_output, args=(process, timeout_sec, result))
    t.start()

    while not result:
        t1 = now()
        if t1 - t0 > timeout_sec:
            return -1, -1
        sleep(0.01)
    if len(result) == 1:
        return -1, -1
    return result


def read_ping_output(process, timeout_sec, result):
    try:
        t0 = now()
        for i in range(10):
            t1 = now()
            if t1 - t0 > timeout_sec:
                return
            output = process.stdout.readline()
            if output:
                output = output.decode().strip()
                ttl = re.findall('ttl=(\d+)', output)
                time = re.findall('time=(.+) ms', output)
                if not ttl or not time:
                    continue
                result.append(ttl[0] if ttl else -1)
                result.append(float(time[0] if time else -1))
                return
            else:
                sleep(0.01)
    finally:
        if not result:
            result.append(None)
