##################################
######## SHAZAMPI MACHINE ########
############# BY CK ##############
##################################

# --------------------------------
# --------Global settings---------
# Email data for shazam logs:
email_origin = "asdfasdf@gmail.com"
email_target = "asdfasdf@asdfasdf.com"
email_password = "yourpasswordhere"
# File directories for new recordings, already analyzed recordings and log files:
newrec_path = "/var/shazampi/new_recordings"
oldrec_path = "/var/shazampi/old_recordings"
log_path = "/var/shazampi/analysis_logs"
# Recording preferences (length of recorded files in seconds and sampling rate in hz):
respeaker_recordseconds = 12
respeaker_samplingrate = 32000

# Libraries and global variables for...
# ...internet connection check
import socket
# ...file identification/paths
import os, os.path
import fnmatch
# ...self-restart functionality
import sys
# ...time (logging & timestamps for files)
import time
# ...shazam functionality
import asyncio
from shazamio import Shazam
# ...email reporting
import smtplib
import glob
# ...recording functionality
import pyaudio
import wave
extension = ".wav"
# ...error handling
from ctypes import *
from contextlib import contextmanager
# ...button functionality

# Error handler functionality, which filters unnecessary prints from alsamixer
ERROR_HANDLER_FUNC = CFUNCTYPE(None, c_char_p, c_int, c_char_p, c_int, c_char_p)

def py_error_handler(filename, line, function, err, fmt):
    pass

c_error_handler = ERROR_HANDLER_FUNC(py_error_handler)

@contextmanager
def noalsaerr():
    asound = cdll.LoadLibrary('libasound.so')
    asound.snd_lib_error_set_handler(c_error_handler)
    yield
    asound.snd_lib_error_set_handler(None)

async def main():
    
 
    while True:

        if internet == "online":
            print("Pi is online. Ready to analyze.")

            # Load shazam and reset counters
            shazam = Shazam()
            newrec_file_counter = 0
            current_id_counter = 0
            current_success_counter = 0
            


            # Iterate through files with audio extension in 'new_recordings' directory and count
            for files in os.listdir(newrec_path):
                if files.endswith(extension):
                    newrec_file_counter += 1
            
            # Create log file
            file = open(log_path + "/logfile [" + current_timestamp + "].txt", "w")
            file.write("SHAZAM ANALYSIS LOG\n\nDate: " + current_date + "\nTime: " + current_time + "\n\n\n")

            # Iterate through files with audio extension in 'new_recordings' directory for shazam analysis
            for files in os.listdir(newrec_path):
                if files.endswith(extension):
                    # Count attempts
                    current_id_counter += 1
                    alldata = await shazam.recognize_song(newrec_path + "/" + files)
                    # Check if song has been identified
                    if 'track' in alldata:
                        # Get artist and track data
                        trackdata = alldata['track']
                        trackid = trackdata['subtitle'] + " - " + trackdata['title']
                        # Move file from 'new_recordings' to 'old_recordings' directory and rename to Track ID
                        os.replace(newrec_path + "/" + files, oldrec_path + "/" + trackid + " [Analyzed " + current_timestamp + "]" + extension)
                        # Count your successes
                        current_success_counter += 1
                        # Write to log file and print current analysis status
                        file.write("Track " + str(current_id_counter) + "/" + str(newrec_file_counter) + ": " + trackid + "\n")
                        print("Track " + str(current_id_counter) + "/" + str(newrec_file_counter) + " found: " + trackid)
                    else:
                        # Move file from 'new_recordings' to 'old_recordings' directory and rename to "Unidentified"
                        os.replace(newrec_path + "/" + files, oldrec_path + "/" + "Unidentified Track [Analyzed " + current_timestamp + "]" + extension)
                        # Write to log file and print current analysis status
                        file.write("Track " + str(current_id_counter) + "/" + str(newrec_file_counter) + ": Not found. \n")
                        print("Track " + str(current_id_counter) + "/" + str(newrec_file_counter) + " not found.")
                else:
                    continue
    
            # Write final status report to file and close it
            if current_id_counter >= 2:
                file.write("\n\nAnalysis Summary: " + str(current_success_counter) + " of " + str(current_id_counter) + " Tracks have been identified.")
                print("Analysis Summary: " + str(current_success_counter) + " of " + str(current_id_counter) + " Tracks have been identified.")
            else:
                file.write("\n\nAnalysis Summary: One Track has been identified.")
                print("Analysis Summary: One Track has been identified.")
            file.close
            print("Log file has been saved to the device.")
    
            # Get the textual content of the newest log file and paste it into a variable
            time.sleep(0.5)
            logfiles = list(filter(os.path.isfile, glob.glob(log_path + "/*")))
            logfiles.sort(key=lambda x: os.path.getmtime(x))
            newest_logfile_path = logfiles[-1]
    
            with open(newest_logfile_path, "r") as file:
                filecontent = file.read()
    
            # Send the contents of the newly filled variable by email using a gmail account
            subject = "Shazam Analyse vom " + current_date + " um " + current_time
            service = smtplib.SMTP('smtp.gmail.com', 587)
            service.starttls()
            service.login(email_origin, email_password)
            service.sendmail(email_origin, email_target, f"Subject: {subject}\n{filecontent}")
            service.quit         
            print("Button is operational again.\n----------------------------------------")
    

        # If not connected to the internet, record!
        else:
            print("Pi is offline. Ready to record (" + str(respeaker_recordseconds) + " seconds, " + str(respeaker_samplingrate)[:2] + " kHz).")
            

            # Define variables for the microphone HAT
            respeaker_deviceindex = 0
            respeaker_channels = 2 
            respeaker_width = 2
            
            # Reset counters
            newrec_file_counter = 0
    
            # Iterate through files with audio extension in 'new_recordings' directory + count and set filename for new recording file
            for files in os.listdir(newrec_path):
                if files.endswith(extension):
                    newrec_file_counter += 1     
            recoutput_filename = str(newrec_file_counter + 1) + extension

            # Enable error handling to get rid of sound card prints by alsamixer
            with noalsaerr():
                # Load pyaudio
                p = pyaudio.PyAudio()

                # Record audio
                print("Recording initiated.")
                stream = p.open(
                rate=respeaker_samplingrate,
                format=p.get_format_from_width(respeaker_width),
                channels=respeaker_channels,
                input=True,
                input_device_index=respeaker_deviceindex,)

                frames = []

                for i in range(0, int(respeaker_samplingrate / 1024 * respeaker_recordseconds)):
                    data = stream.read(1024)
                    frames.append(data)

                stream.stop_stream()
                stream.close()
                p.terminate()
            print("Recording finished.")
            
            # Write recorded audio to file
            wf = wave.open(newrec_path + "/" + recoutput_filename, 'wb')
            wf.setnchannels(respeaker_channels)
            wf.setsampwidth(p.get_sample_size(p.get_format_from_width(respeaker_width)))
            wf.setframerate(respeaker_samplingrate)
            wf.writeframes(b''.join(frames))
            wf.close()


loop = asyncio.get_event_loop()
loop.run_until_complete(main())
