WHITE = 0x01 #CHANGE to 0x00 if you want white text on a black BG, and 0x01 for black text on white BG

import os

if not os.path.exists(f"gfts/"):
    os.makedirs(f"gfts/")
filename = input("Enter a .gft file name here (no file format): ")

mode = int(input("Select mode (2 for a 16bit bitmap of the whole glyph grid, 3 for separate 16 bit bitmaps of glyphs: ")) #set to 1 for monochrome bitmap (NOT FUNCTIONAL), 2 for 16bit bitmap, 3 for separate glyphs
FUNNY = 2 #supposed to be 2 because there are 2 bytes per pixel, so all offsets need to be doubled, but other values make funny shapes sometimes (integers greater than 2 work) (ok maybe not that funny, but i set it to 16 at first and it took me a long time to realize that was the problem, so now i will use it for joy instead of confusion)
#-------------------------------------

#load font data into a byte array
with open(f"gfts/{filename}.GFT", "rb") as gft:
    fileData = gft.read()

#store header data, font char width array, and font graphic array
startingChar = fileData[0x24]
pixelChartOffset = int.from_bytes(fileData[0x4C:0x4E], "little")
pixelChartWidth = int.from_bytes(fileData[0x50:0x52], "little")
pixelChartHeight = int.from_bytes(fileData[0x52:0x54], "little")
rasterOffsets = fileData[0x54:pixelChartOffset]
pixelBytes = fileData[pixelChartOffset:]

#converts the 2 byte offset list into a list of offsets in integers, as well as a list of char widths as ints
rasterIntOffsets = []
rasterIntWidths = []
prevOffset = 0
for i in range(0, len(rasterOffsets), 2):
    currentOffset = int.from_bytes(rasterOffsets[i:i + 2], "little")
    rasterIntOffsets.append(currentOffset)
    if currentOffset != 0:
        rasterIntWidths.append(currentOffset - prevOffset)
    prevOffset = currentOffset

#makes a list of n bytearrays, where n = the height of the characters (jumps by width b/c after going W bytes, you end up at the start of the next line)
pixelChartLists = []
for i in range(0, len(pixelBytes), pixelChartWidth):
    pixelChartLists.append(pixelBytes[i:i + pixelChartWidth])

biglist = b''
counter = 0
revPixelChartLists = pixelChartLists[::-1]
revListBin = []


if mode == 1: #supposed to be for monochrome full charmap bitmaps, but doesn't work and may never work (prob should be less similar to 16 bit, idk how mono BMP works yet though)
    for i in revPixelChartLists: #for each bytearray (hz lines, reversed because BMP writes bottom to top)
        for byte in i:
            for bit in bin(byte)[2:].zfill(8):
                biglist += (int(bit) * 0xFF).to_bytes(1) * 2 #for 16 bit
        counter += 1
        # if counter % 2 == 0 and counter != 0:
        #   biglist += b'\x00\x00'
        ###for the filler, though theres prob a better way

#the next ifs turn the bytes containing pixel data into pixel data that will work for their respective BMP pixel resolutions
elif mode == 2: #for 16 bit full charmap bitmap
    for i in revPixelChartLists:
        for byte in i:
            for bit in bin(byte)[2:].zfill(8): #turn each byte into binary string
                biglist += ((int(bit) ^ WHITE) * 0xFF).to_bytes(1) *2 #for 16 bit: turn a 0 bit into \x00\x00, and a 1 bit into \xFF\xFF (via multiplying 1 by FF, then \x

elif mode == 3: #for individual glyphs, 16 bit
    for i in revPixelChartLists:
        for byte in i:
            for bit in bin(byte)[2:].zfill(8):
                biglist += ((int(bit) ^ WHITE) * 0xFF).to_bytes(1) *2 #same as mode 2, but a new step below appends each line individually so it's easier to iterate btwn em
        revListBin.append(biglist)
        biglist = b''

#for writing full charmaps, vars are for data in BMP header, and data is from the prev if statement land
if mode == 1 or mode == 2:
    if not os.path.exists(f"fullfonts/"):
        os.makedirs(f"fullfonts/")
    with open(f"fullfonts/{filename}_fullAAA.bmp", "wb") as bmp:
        # bytearrays to put in bmp
        try:
            bmpFileLength = (0x36 + len(biglist)).to_bytes(2, "little", signed=False)
        except OverflowError:
            bmpFileLength = b'\x00\x00'
            print(f"image is too big to give the bmp a file length in the header (will still work, just no data for you, still if you were curious it would have been {0x36 + len(biglist)} bytes long)")
        bmpFileWidth = (pixelChartWidth * 8).to_bytes(4, "little", signed=False)  # *8 to account for there being 8 pixels in a byte, *2 for the filler bytes
        bmpFileHeight = pixelChartHeight.to_bytes(4, "little", signed=False)
        bmpPixelLength = len(biglist).to_bytes(4, "little", signed=False)
        if mode == 2:
            bmp.write(b'BM' + bmpFileLength + b'\x00\x00\x00\x00\x00\x006\x00\x00\x00(\x00\x00\x00' + bmpFileWidth + bmpFileHeight + b'\x01\x00\x10\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00' + biglist) #16 bit bitmap
        elif mode == 1:
            bmp.write(b'BM' + bmpFileLength + b'\x00\x00\x00\x00\x00\x006\x00\x00\x00(\x00\x00\x00' + bmpFileWidth + bmpFileHeight + b'\x01\x00\x01\x00\x00\x00\x00\x00' + bmpPixelLength + b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\xFF\xFF\x00\x00\x00\x00\x00' + biglist) #monochrome bmp, WIP
            #

if mode == 3:
    bmpFileLength = (0x36 + len(biglist)).to_bytes(2, "little", signed=False)
    bmpFileWidth = (pixelChartWidth * 8).to_bytes(4, "little",signed=False)  # *8 to account for there being 8 pixels in a byte, *2 for the filler bytes
    bmpFileHeight = pixelChartHeight.to_bytes(4, "little", signed=False)

    for i in range(len(rasterIntWidths)):
        if rasterIntWidths[i] % 2 == 1:
            filler = True
        else:
            filler = False
        if rasterIntWidths[i] != 1:
            if not os.path.exists(f"glyphs/"):
                os.makedirs(f"glyphs/")
            with open(f"glyphs/glyph%03d.bmp" %(i+startingChar), "wb") as bmp:  #%s.bmp" %(str(hex(i+startingChar))[2:].upper().zfill(4)), "wb") as bmp:
                bmp.write(b'BM' + bmpFileLength + b'\x00\x00\x00\x00\x00\x006\x00\x00\x00(\x00\x00\x00' + rasterIntWidths[i].to_bytes(4, "little") + bmpFileHeight + b'\x01\x00\x10\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00') #16 bit bitmap
                for pixelLine in range(pixelChartHeight):
                    #print(revListBin[pixelLine][rasterIntOffsets[i] * FUNNY:rasterIntOffsets[i + 1] * FUNNY])
                    bmp.write(revListBin[pixelLine][rasterIntOffsets[i] * FUNNY:rasterIntOffsets[i + 1] * FUNNY]) #from the reversed list of bytearrays, take the pixellineth array and take the bytes from the current offset to the next offset
                    if filler == True: #there needs to be an even amount of pixels each line ig? idk maybe
                        bmp.write(b'\x00\x00')

#### png maker
from PIL import Image
import glob

if mode == 3:
    if input("Do you want to convert the images in glyphs to PNGs? (if no, input nothing): " != ""):
        if not os.path.exists(f"pngs/"):
            os.makedirs(f"pngs/")
        count = startingChar #some fonts may not start on space
        for bitmapChar in glob.glob("glyphs/*.bmp"):
            #Image.open(bitmapChar).save(f"pngland/uni{str(hex(count)[2:]).upper().zfill(4)}.png") #{str(hex(i))[2:].zfill(4).upper()}.png")
            Image.open(bitmapChar).save(f"pngs/glyph{str(count).zfill(3)}.png") #{str(hex(i))[2:].zfill(4).upper()}.png")
            count += 1