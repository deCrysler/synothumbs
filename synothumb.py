#!/usr/bin/env python
# cd; mkdir mnt_photo
# sudo mount -t {synology-ip-address}:/volume1/photo mnt_photo/
# Author:       phillips321
# Co-authors:   devdogde, sirrahd, AndrewFreemantle
# License:      CC BY-SA 3.0
# Use:          home use only, commercial use by permission only
# Released:     www.phillips321.co.uk
# Instructions: www.fatlemon.co.uk/synothumbs
# Dependencies: Pillow, libjpeg, libpng, dcraw, ffmpeg
# Supports:     jpg, png, tif, bmp, cr2 (raw), mov, m4v, mp4
import os, sys, threading, time, subprocess, shlex
from queue import Queue
from PIL import Image, ImageChops  # PIL is provided by Pillow
from io import StringIO

#########################################################################
# Settings
#########################################################################
NumOfThreads = 8  # Number of threads
startTime = time.time()
imageExtensions = ['.jpg', '.png', '.jpeg', '.tif', '.bmp', '.cr2']  # possibly add other raw types?
videoExtensions = ['.mov', '.m4v', '.mp4']
xlName = "SYNOPHOTO_THUMB_XL.jpg";
oldxlName = "SYNOPHOTO:THUMB_XL.jpg";
xlSize = (1280, 1280)  # XtraLarge
lName = "SYNOPHOTO_THUMB_L.jpg";
oldlName = "SYNOPHOTO:THUMB_L.jpg";
lSize = (800, 800)  # Large
bName = "SYNOPHOTO_THUMB_B.jpg";
oldbName = "SYNOPHOTO:THUMB_B.jpg";
bSize = (640, 640)  # Big
mName = "SYNOPHOTO_THUMB_M.jpg";
oldmName = "SYNOPHOTO:THUMB_M.jpg";
mSize = (320, 320)  # Medium
smName = "SYNOPHOTO_THUMB_SM.jpg";
oldsmName = "SYNOPHOTO:THUMB_SM.jpg";
smSize = (240, 240)  # Small-Medium
sName = "SYNOPHOTO_THUMB_S.jpg";
oldsName = "SYNOPHOTO:THUMB_S.jpg";
sSize = (160, 160)  # Small
pName = "SYNOPHOTO_THUMB_PREVIEW.jpg";
oldpName = "SYNOPHOTO:THUMB_PREVIEW.jpg";
pSize = (120, 160)  # Preview, keep ratio, pad with black


#########################################################################
# Images Class
#########################################################################
class convertImage(threading.Thread):
    def __init__(self, queueIMG, badImageFileList):
        threading.Thread.__init__(self)
        self.queueIMG = queueIMG
        self.badImageFileList = badImageFileList

    def run(self):
        while True:
            try:
                self.imagePath = self.queueIMG.get()
                self.imageDir, self.imageName = os.path.split(self.imagePath)
                self.thumbDir = os.path.join(self.imageDir, "@eaDir", self.imageName)
                status = "Skipping"

                if not os.path.isfile(os.path.join(self.thumbDir, pName)) or \
                        not os.path.isfile(os.path.join(self.thumbDir, sName)) or \
                        not os.path.isfile(os.path.join(self.thumbDir, smName)) or \
                        not os.path.isfile(os.path.join(self.thumbDir, mName)) or \
                        not os.path.isfile(os.path.join(self.thumbDir, bName)) or \
                        not os.path.isfile(os.path.join(self.thumbDir, lName)) or \
                        not os.path.isfile(os.path.join(self.thumbDir, xlName)):

                    status = "Working on"
                    if os.path.isdir(self.thumbDir) != 1:
                        try:
                            os.makedirs(self.thumbDir)
                        except:
                            continue

                    # Following if statements converts raw images using dcraw first
                    if os.path.splitext(self.imagePath)[1].lower() == ".cr2":
                        self.dcrawcmd = "dcraw -c -b 8 -q 0 -w -H 5 '%s'" % self.imagePath
                        self.dcraw_proc = subprocess.Popen(shlex.split(self.dcrawcmd), stdout=subprocess.PIPE)
                        self.raw = StringIO(self.dcraw_proc.communicate()[0])
                        self.image = Image.open(self.raw)
                    else:
                        self.image = Image.open(self.imagePath)

                    ###### Check image orientation and rotate if necessary
                    ## code adapted from: http://www.lifl.fr/~riquetd/auto-rotating-pictures-using-pil.html
                    try:
                        self.exif = self.image._getexif()
                    except:
                        pass

                    if self.exif:

                        self.orientation_key = 274  # cf ExifTags
                        if self.orientation_key in self.exif:
                            self.orientation = self.exif[self.orientation_key]

                            rotate_values = {
                                3: 180,
                                6: 270,
                                8: 90
                            }

                            try:
                                if self.orientation in rotate_values:
                                    self.image = self.image.rotate(rotate_values[self.orientation], expand=True)
                            except:
                                pass

                    #### end of orientation part

                    try:
                        if not os.path.isfile(os.path.join(self.thumbDir, xlName)):
                            self.image.thumbnail(xlSize, Image.ANTIALIAS)
                            self.image.save(os.path.join(self.thumbDir, xlName), quality=90)
                        if not os.path.isfile(os.path.join(self.thumbDir, lName)):
                            self.image.thumbnail(lSize, Image.ANTIALIAS)
                            self.image.save(os.path.join(self.thumbDir, lName), quality=90)
                        if not os.path.isfile(os.path.join(self.thumbDir, bName)):
                            self.image.thumbnail(bSize, Image.ANTIALIAS)
                            self.image.save(os.path.join(self.thumbDir, bName), quality=90)
                        if not os.path.isfile(os.path.join(self.thumbDir, mName)):
                            self.image.thumbnail(mSize, Image.ANTIALIAS)
                            self.image.save(os.path.join(self.thumbDir, mName), quality=90)
                        if not os.path.isfile(os.path.join(self.thumbDir, smName)):
                            self.image.thumbnail(smSize, Image.ANTIALIAS)
                            self.image.save(os.path.join(self.thumbDir, smName), quality=90)
                        if not os.path.isfile(os.path.join(self.thumbDir, sName)):
                            self.image.thumbnail(sSize, Image.ANTIALIAS)
                            self.image.save(os.path.join(self.thumbDir, sName), quality=90)
                        if not os.path.isfile(os.path.join(self.thumbDir, pName)):
                            self.image.thumbnail(pSize, Image.ANTIALIAS)
                            # pad out image
                            self.image_size = self.image.size
                            self.preview_img = self.image.crop((0, 0, pSize[0], pSize[1]))
                            self.offset_x = max((pSize[0] - self.image_size[0]) / 2, 0)
                            self.offset_y = max((pSize[1] - self.image_size[1]) / 2, 0)
                            self.preview_img = ImageChops.offset(self.preview_img, int(self.offset_x),int(self.offset_y))  # offset has to be integer, not float
                            self.preview_img.save(os.path.join(self.thumbDir, pName), quality=90)

                    except IOError:
                        ## image file is corrupt / can't be read / or we can't write to the mounted share
                        with open(self.badImageFileList, "a") as badFileList:
                            badFileList.write(self.imagePath + '\n')

                print("  [- | %s] %s %s" % (time.strftime('%X'), status, self.imagePath))
            except:
                continue
            finally:
                self.queueIMG.task_done()



#########################################################################
# Video Class
#########################################################################
class convertVideo(threading.Thread):
    def __init__(self, queueVID):
        threading.Thread.__init__(self)
        self.queueVID = queueVID

    def is_tool(self, name):
        try:
            devnull = open(os.devnull)
            subprocess.Popen([name], stdout=devnull, stderr=devnull).communicate()
        except OSError as e:
            if e.errno == os.errno.ENOENT:
                return False
        return True

    @property
    def run(self):
        while True:
            try:
                self.videoPath = self.queueVID.get()
                self.videoDir, self.videoName = os.path.split(self.videoPath)
                self.thumbDir = os.path.join(self.videoDir, "@eaDir", self.videoName)
                print("  [- | %s] Now working on %s" % (time.strftime('%X'), self.videoPath))
                if not os.path.isfile(os.path.join(self.thumbDir, smName)) or \
                        not os.path.isfile(os.path.join(self.thumbDir, mName)) or \
                        not os.path.isfile(os.path.join(self.thumbDir, xlName)):
                    if os.path.isdir(self.thumbDir) != 1:
                        try:
                            os.makedirs(self.thumbDir)
                        except:
                            continue
                    # Check video conversion command and convert video to flv
                    if self.is_tool("ffmpeg"):
                        self.ffmpegcmd = "ffmpeg -loglevel panic -i '%s' -y -ar 44100 -r 12 -ac 2 -f flv -qscale 5 -s 320x180 -aspect 320:180 '%s/SYNOPHOTO_FILM.flv'" % (
                            self.videoPath, self.thumbDir)  # ffmpeg replaced by avconv on ubuntu
                    elif self.is_tool("avconv"):
                        self.ffmpegcmd = "avconv -loglevel panic -i '%s' -y -ar 44100 -r 12 -ac 2 -f flv -qscale 5 -s 320x180 -aspect 320:180 '%s/SYNOPHOTO_FILM.flv'" % (
                            self.videoPath, self.thumbDir)
                    else:
                        return False
                    if not os.path.isfile(os.path.join(self.thumbDir, "SYNOPHOTO_FILM.flv")):
                        self.ffmpegproc = subprocess.Popen(shlex.split(self.ffmpegcmd), stdout=subprocess.PIPE)
                        self.ffmpegproc.communicate()[0]

                    # Create video thumbs
                    self.tempThumb = os.path.join("/tmp", os.path.splitext(self.videoName)[0] + ".jpg")
                    if self.is_tool("ffmpeg"):
                        # self.ffmpegcmdThumb = "ffmpeg -loglevel panic -i '%s' -y -an -ss 00:00:03 -an -r 1 -vframes 1 '%s'" % (self.videoPath,self.tempThumb) # ffmpeg replaced by avconv on ubuntu
                        self.ffmpegcmdThumb = "ffmpeg -loglevel panic -i '%s' -y -vf thumbnail,scale=w=320:h=-1 -frames:v 1 '%s'" % (
                            self.videoPath, self.tempThumb)
                    elif self.is_tool("avconv"):
                        self.ffmpegcmdThumb = "avconv -loglevel panic -i '%s' -y -vf thumbnail,scale=w=320:h=-1 -frames:v 1 '%s'" % (
                            self.videoPath, self.tempThumb)
                    else:
                        return False

                    self.ffmpegThumbproc = subprocess.Popen(shlex.split(self.ffmpegcmdThumb),
                                                            stdout=subprocess.PIPE)
                    self.ffmpegThumbproc.communicate()[0]
                    self.image = Image.open(self.tempThumb)
                    if not os.path.isfile(os.path.join(self.thumbDir, xlName)):
                        self.image.thumbnail(xlSize)
                        self.image.save(os.path.join(self.thumbDir, xlName))
                    if not os.path.isfile(os.path.join(self.thumbDir, mName)):
                        self.image.thumbnail(mSize)
                        self.image.save(os.path.join(self.thumbDir, mName))
                    if not os.path.isfile(os.path.join(self.thumbDir, smName)):
                        self.image.thumbnail(smSize)
                        self.image.save(os.path.join(self.thumbDir, smName))

                else:
                    print("    skip")
            except:
                continue
            finally:
                self.queueVID.task_done()



#########################################################################
# Main
#########################################################################
def main():
    queueIMG = Queue()
    queueVID = Queue()
    try:
        rootdir = sys.argv[1]
    except:
        print("Usage: %s directory" % sys.argv[0])
        sys.exit(0)

    # Finds all images of type in extensions array
    imageList = []
    videoList = []

    cnt = 0

    print("[+] Looking for images and videos and populating queues (This might take a while...)")
    for path, subFolders, files in os.walk(rootdir):
        if "@eaDir" in subFolders: subFolders.remove('@eaDir')

        print(path)
        if '@eaDir' not in path:
            for file in files:
                ext = os.path.splitext(file)[1].lower()
                added = '-'
                if file[0] != ".":  # maybe remove
                    if any(x in ext for x in imageExtensions):  # check if extensions matches ext
                        imageList.append(os.path.join(path, file))
                        added = 'i'
                    elif any(x in ext for x in videoExtensions):  # check if extensions matches ext
                        videoList.append(os.path.join(path, file))
                        added = 'v'

                sys.stdout.write(added)
                cnt = cnt + 1

                if cnt == 80:
                    sys.stdout.write('\n')
                    cnt = 0
                sys.stdout.flush()
            print("")

    if len(imageList) > 0:
        print("[+] We have found %i images in search directory" % len(imageList))
        do_images = input("\tDo you want to process them? (y/n) ") == "y"

        if do_images:
            # spawn a pool of threads
            for i in range(NumOfThreads):  # number of threads
                t = convertImage(queueIMG, os.path.join(rootdir, "synothumb-bad-file-list.txt"))
                t.setDaemon(True)
                t.start()

            # populate queue with Images
            for imagePath in imageList:
                queueIMG.put(imagePath)

            queueIMG.join()

    if len(videoList) > 0:
        print("[+] We have found %i videos in search directory" % len(videoList))
        do_videos = input("\tDo you want to process them? (y/n) ") == "y"

        if do_videos:
            # spawn a pool of threads
            for i in range(NumOfThreads):  # number of threads
                v = convertVideo(queueVID)
                v.setDaemon(True)
                v.start()

            # populate queueVID with Images
            for videoPath in videoList:
                queueVID.put(
                    videoPath)  # could we possibly put this instead of videoList.append(os.path.join(path,file))

            queueVID.join()

    endTime = time.time()
    print("Time to complete: %is" % (endTime - startTime))

    sys.exit(0)


if __name__ == "__main__":
    main()
