from django.core.management.base import BaseCommand
from django.db import transaction
from api.models import LogConfig, LogEntry
from datetime import datetime
import pytz
 
IST = pytz.timezone('Asia/Kolkata')
 
 
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
            'timestamp': timestamp,
            'level': level,
            'thread': thread,
            'message': message,
        }
    except:
        return None
 
 
class Command(BaseCommand):
    help = 'Import all log file contents into database'
 
    def handle(self, *args, **kwargs):
        try:
            config = LogConfig.objects.get(id=1)
        except LogConfig.DoesNotExist:
            self.stdout.write('No log location configured. Run POST /api/config/ first.')
            return
 
        file_path = config.location
        self.stdout.write(f'Reading file: {file_path}')
 
        batch = []
        batch_size = 5000
        total = 0
        skipped = 0
 
        LogEntry.objects.all().delete()
        self.stdout.write('Cleared existing entries.')
 
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            current_line = ''
 
            for line in f:
                line = line.rstrip('\n')
                stripped = line.strip()
 
                if not stripped:
                    continue
 
                if stripped.startswith('['):
                    if current_line:
                        parsed = parse_line(current_line)
                        if parsed:
                            batch.append(LogEntry(**parsed))
                            total += 1
                        else:
                            skipped += 1
 
                        if len(batch) >= batch_size:
                            with transaction.atomic():
                                LogEntry.objects.bulk_create(batch)
                            self.stdout.write(f'Inserted {total} rows...')
                            batch = []
 
                    current_line = stripped
                else:
                    current_line += ' ' + stripped
 
            # process last line
            if current_line:
                parsed = parse_line(current_line)
                if parsed:
                    batch.append(LogEntry(**parsed))
                    total += 1
                else:
                    skipped += 1
 
        if batch:
            with transaction.atomic():
                LogEntry.objects.bulk_create(batch)
 
        self.stdout.write(
            self.style.SUCCESS(
                f'Done. Imported {total} rows. Skipped {skipped} lines.'
            )
        )
 