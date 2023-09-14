#!/usr/bin/env python3

### dns-zone-list-parser
### A Python daemon to transform a list of zones exported from PowerDNS into
### bind slave zone files

### ev1z.be - Distributed under MIT License

# --------------------------------------------------------------------------- #

### Imports
import time
import os
import subprocess
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# --------------------------------------------------------------------------- #

### Define file handler
class watchUploads:
    # Set the directory on watch
    watchDirectory = "./uploads"
 
    def __init__(self):
        self.observer = Observer()
 
    def run(self):

        # Remove lock file if present
        if os.path.exists("./lock.file"):
            os.remove('./lock.file')

        event_handler = Handler()
        self.observer.schedule(event_handler, self.watchDirectory, recursive = False)
        self.observer.start()

        try:
            while True:
                time.sleep(5)
        except:
            self.observer.stop()
            print("Observer Stopped")

        self.observer.join()
 
 
class Handler(FileSystemEventHandler):
 
    @staticmethod
    def on_any_event(event):
        if event.is_directory:
            return None
        elif event.event_type == 'created':
            # A file create is followed by a modify, so we only react once
            return None
        elif event.event_type == 'modified':

            if os.path.exists("./lock.file"):
                print("Zone list file updated but lock active - No action.")
                return None

            print("Zone list file updated.")

            # Create lock file
            lock_file = open("./lock.file", 'w')
            lock_file.write('')
            lock_file.close()

            # Sleep 5 seconds to allow write to finish
            time.sleep(5) 

            # Read the zones file line by line and create the slave zone file
            exported_zones_file = open('./uploads/pdns.dump', 'r')
            zones = exported_zones_file.readlines()

            # Strip endlines from zones files
            zones = [z.strip() for z in zones] 

            for zone in zones:

                print("Processing zone " + zone + ".")

                # Slave zone file is created by substitution from the template
                template_file = open("./slave-zone-template", 'r')
                zone_file = open("./zones/zone." + zone + ".conf", 'w')

                for line in template_file:
                    line = line.replace("%ZONE%", zone)
                    zone_file.write(line)

                zone_file.close()
                template_file.close()

            exported_zones_file.close()

            # Look for removed zones
            existing_files = os.listdir("./zones")
            # Remove subdirectories if any
            existing_files = [f for f in existing_files if os.path.isfile("./zones/"+f)]
            
            for file in existing_files:
                existing_zone = file.strip("db.")
                if existing_zone not in zones:
                    print("Zone " + existing_zone + " removed from master, deleting slave zone file.")
                    os.remove("./zones/" + file)

            if os.path.exists("./post-update.sh"):
                subprocess.run(["./post-update.sh"], shell=True)

            print("Processing finished.")

            # Remove lock file if present
            if os.path.exists("./lock.file"):
                os.remove('./lock.file')


# --------------------------------------------------------------------------- #

### Main routine
if __name__ == '__main__':
    watch = watchUploads()
    watch.run()
