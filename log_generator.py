import time
import random
from datetime import datetime
 
LOG_FILE = "logs/app.log"
 
THREADS = ["t9524", "t8144", "t5416", "t4908", "t3024", "t6020", "t7812", "t3972"]
 
INFO_MESSAGES = [
    "Server started successfully",
    "SimpleCommandScheduler: removed command, queue length: {n}",
    "Loading configuration data",
    "Loading crew monthly data",
    "Saving data...",
    "Number of records saved/updated: {n}",
    "SaveModelData: cache update...done",
    "Model::Save: setting unchanged",
    "Init Thread: Log",
    "Init Thread: Database",
    "Starting Server...",
    "Loading grading year configuration data",
    "Connection established to database",
    "User session started: session_id={n}",
    "Request completed successfully in {n}ms",
    "Cache updated for module: crew_data",
    "Scheduler running, next job in {n}s",
]
 
DEBUG_MESSAGES = [
    "{{sql}} (sid: {n}) executing sql: SELECT * FROM CREW_DATA WHERE ID = {n}",
    "{{sql}} (sid: {n}) number of rows was {n}, created objects from rows in {n}.{n} ms",
    "{{changeinfo}} notify changeinfo: {n}/D. is a self triggered db update => dropping notify. size(s:{n}/n:{n})",
    "{{savetimer}} saving CrewChangeRoot took(ms):{n}.00",
    "{{savetimer}} saving CCrewFatigueData took(ms):{n}.00",
    "{{savetimer}} calling _logic.SetUnchanged<T>",
    "{{sql}} executing sql: SELECT CMO_PERS_NR FROM CREW_MONTH_DATA WHERE CMO_MONAT >= sysdate",
    "Entry: CCddServerImpl::GetPeriods persID = {n}",
    "Exit: CCddServerImpl::GetPeriods persID = {n}",
    "Entry: CServerController::GetXmlDutySheetsByFilter",
    "Processing request for thread {t}",
    "Memory usage: {n}MB / 512MB",
    "Cache hit ratio: {n}%",
]
 
WARNING_MESSAGES = [
    "High memory usage detected: {n}% of available heap",
    "Database connection pool running low: {n} connections remaining",
    "Response time exceeding threshold: {n}ms",
    "Retry attempt {n} for database operation",
    "Slow query detected: {n}ms for sql execution",
    "Connection timeout warning on sid: {n}",
    "Queue length growing: {n} pending items",
    "Disk space warning: {n}% used",
    "Cache miss rate high: {n}%",
    "Thread pool near capacity: {n}/{n} threads active",
]
 
ERROR_MESSAGES = [
    "Connection timeout on sid: {n} after {n}ms",
    "Database error: ORA-{n}: unique constraint violated",
    "Failed to save CCrewMonthlyData: transaction rollback",
    "NullPointerException in CServerController::GetXmlDutySheetsByFilter",
    "Socket connection refused on port {n}",
    "Authentication failed for session_id: {n}",
    "Critical: Unable to acquire database lock after {n} attempts",
    "Out of memory error in thread {t}",
    "File not found: config/settings_{n}.xml",
    "Unexpected error in SimpleCommandScheduler: queue corrupted",
]
 
 
def pick(messages, thread):
    msg = random.choice(messages)
    n = random.randint(1, 9999)
    return msg.replace("{n}", str(n)).replace("{t}", thread)
 
 
def write_log(level, thread, message):
    now = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
    line = f" [{now}], {thread}, {level}  {message}\n"
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line)
    print(line.strip())
 
 
def generate_batch():
    # Realistic distribution: lots of D and I, few W, rare E
    weights = {"D": 50, "I": 35, "W": 10, "E": 5}
    batch_size = random.randint(5, 20)
 
    for _ in range(batch_size):
        level = random.choices(
            list(weights.keys()),
            weights=list(weights.values())
        )[0]
        thread = random.choice(THREADS)
 
        if level == "I":
            msg = pick(INFO_MESSAGES, thread)
        elif level == "D":
            msg = pick(DEBUG_MESSAGES, thread)
        elif level == "W":
            msg = pick(WARNING_MESSAGES, thread)
        else:
            msg = pick(ERROR_MESSAGES, thread)
 
        write_log(level, thread, msg)
        time.sleep(random.uniform(0.05, 0.2))
 
 
if __name__ == "__main__":
    import os
    os.makedirs("logs", exist_ok=True)
 
    print("Log generator started. Writing to logs/app.log")
    print("Press Ctrl+C to stop.\n")
 
    # Write startup sequence
    thread = "t9524"
    write_log("I", thread, "*" * 60)
    write_log("I", thread, "Server Version: 4.15.0 x64")
    write_log("I", thread, "Starting Server...")
    write_log("I", thread, "Loading configuration.")
    write_log("I", thread, "Init Thread: Log")
    write_log("I", thread, "Init Thread: Database")
    write_log("I", thread, "Connection established to database")
 
    print("\nGenerating logs every 10 seconds...\n")
 
    while True:
        generate_batch()
        time.sleep(10)
 