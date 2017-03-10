#file to be loaded on RasPi@CameraTrap that backs up photos
#camerabu = camera back up
#loaded an option into sudo nano /etc/ssh/ssh_config and append ServerAliveInterval 60

import subprocess as sp


arg_backup = " -avP --update --backup --backup-dir=backup --chmod=ugo=rwX --remove-source-files"
camera_path = " /media/usbhdd/DCIM/"
backup_path = " /home/pi/Desktop/BackUp/*"

status_makedirectory = sp.call("mkdir -v /home/pi/Desktop/BackUp/", shell=True)
status_del = sp.call("rm -vr"+ backup_path, shell=True)
status_backup = sp.call("sudo rsync" + arg_backup + camera_path + " /home/pi/Desktop/BackUp/", shell=True)
