import psutil

def list_processes():
    processes = []
    for proc in psutil.process_iter(['pid', 'name']):
        processes.append(proc.info)
    return processes
