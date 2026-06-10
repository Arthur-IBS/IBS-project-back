import asyncio
import json
import os
import socket
from datetime import datetime
import pytz
 
# Config
LOG_FILE = "C:/Users/213685/Desktop/Python/logpro/logs/app.log"
POSITION_FILE = "agent_position.txt"
LOGSTASH_HOST = "localhost"
LOGSTASH_PORT = 5000
INTERVAL_SECONDS = 60
IST = pytz.timezone('Asia/Kolkata')
 
 
def get_last_position():
    if os.path.exists(POSITION_FILE):
        with open(POSITION_FILE, "r") as f:
            try:
                return int(f.read().strip())
            except:
                return 0
    return 0
 
 
def save_position(pos):
    with open(POSITION_FILE, "w") as f:
        f.write(str(pos))
 
 
def parse_line(line):
    try:
        line = line.strip()
        if not line.startswith('['):
            return None
 
        dt_str = line[1:20]
        timestamp = datetime.strptime(dt_str, "%d.%m.%Y %H:%M:%S")
        timestamp = IST.localize(timestamp)
 
        parts = line.split(', ', 2)
        if len(parts) < 3:
            return None
 
        thread = parts[1].strip()
        remainder = parts[2].strip()
        if not remainder:
            return None
 
        level = remainder[0]
        message = remainder[1:].strip()
 
        return {
            "log_timestamp": dt_str,
            "timestamp": timestamp.isoformat(),
            "thread": thread,
            "level": level,
            "message": message,
            "application": "logpro"
        }
    except:
        return None
 
 
def send_to_logstash(docs):
    if not docs:
        return
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.connect((LOGSTASH_HOST, LOGSTASH_PORT))
        for doc in docs:
            line = json.dumps(doc) + "\n"
            sock.sendto(line.encode("utf-8"), (LOGSTASH_HOST, LOGSTASH_PORT))
        sock.close()
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Sent {len(docs)} lines to Logstash")
    except Exception as e:
        print(f"[ERROR] Could not send to Logstash: {e}")
 
 
def read_new_lines():
    if not os.path.exists(LOG_FILE):
        print(f"[WARN] Log file not found: {LOG_FILE}")
        return []
 
    last_pos = get_last_position()
    current_size = os.path.getsize(LOG_FILE)
 
    # File was rotated or truncated
    if current_size < last_pos:
        print("[INFO] Log file reset detected, reading from beginning")
        last_pos = 0
 
    if current_size == last_pos:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] No new lines")
        return []
 
    docs = []
    current_line = ''
 
    with open(LOG_FILE, "r", encoding="utf-8", errors="ignore") as f:
        f.seek(last_pos)
 
        for raw_line in f:
            line = raw_line.rstrip('\n')
            stripped = line.strip()
 
            if not stripped:
                continue
 
            if stripped.startswith('['):
                if current_line:
                    parsed = parse_line(current_line)
                    if parsed:
                        docs.append(parsed)
                current_line = stripped
            else:
                current_line += ' ' + stripped
 
        # Process last accumulated line
        if current_line:
            parsed = parse_line(current_line)
            if parsed:
                docs.append(parsed)
 
        # Save position while file is still open
        new_pos = f.tell()
 
    save_position(new_pos)
    return docs
 
 
async def run_agent():
    print("=" * 50)
    print("LogPro Agent Started")
    print(f"Log file : {LOG_FILE}")
    print(f"Logstash : {LOGSTASH_HOST}:{LOGSTASH_PORT}")
    print(f"Interval : {INTERVAL_SECONDS} seconds")
    print("=" * 50)
 
    while True:
        try:
            docs = read_new_lines()
            if docs:
                send_to_logstash(docs)
        except Exception as e:
            print(f"[ERROR] Agent error: {e}")
 
        await asyncio.sleep(INTERVAL_SECONDS)
 
 
if __name__ == "__main__":
    asyncio.run(run_agent())
 