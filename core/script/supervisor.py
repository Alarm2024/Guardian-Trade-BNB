import subprocess
import time
import sys
from logger import get_logger

log = get_logger("Supervisor")

AGENTS = [
    ["python3", "/home/wyndhamdesert/script/proposal_monitor.py"],
    ["python3", "/home/wyndhamdesert/script/oracle_agent.py"]
]

def supervise():
    processes = []
    for agent in AGENTS:
        log.info(f"Starting agent: {' '.join(agent)}")
        processes.append(subprocess.Popen(agent))

    while True:
        for i, proc in enumerate(processes):
            if proc.poll() is not None:
                log.warning(f"Agent {AGENTS[i]} died. Restarting...")
                processes[i] = subprocess.Popen(AGENTS[i])
        time.sleep(10)

if __name__ == "__main__":
    try:
        supervise()
    except KeyboardInterrupt:
        log.info("Supervisor shutting down.")
        sys.exit(0)
