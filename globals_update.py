#!/usr/bin/python3

import gzip, struct, binascii, csv, sys

MAX_STR_SIZE=2000

def get_text(data, off):
    chars = [(x, y) for x, y in zip(data[off:off+MAX_STR_SIZE:2], data[off+1:off+MAX_STR_SIZE+1:2])]
    size = chars.index((0, 0))
    return data[off:off+size*2].decode('utf-16le')

def update_globals(data, textList):
    (fileSize, unk1, unk2, numEntries) = struct.unpack('<IIII', data[4:4*5])
    if data[:4] != b'STja':
        print("Invalid globals.bin subfile!");
        return []
    fileOff = 20
    # for each text offset, list the pointer offsets where it appears
    textOffPos = {}
    for i in range(numEntries):
        (ID, textOff) = struct.unpack('<II', data[fileOff:fileOff+8])
        textOffPos.setdefault(textOff, []).append((ID, fileOff+4))
        fileOff += 8
    outData = data[:fileOff]
    for (checkId, t), off in zip(textList, sorted(textOffPos.keys())):
        newOff = len(outData)
        found = False
        for (ID, x) in textOffPos[off]:
            outData = outData[:x] + struct.pack('<I', newOff) + outData[x+4:]
            if ID == checkId:
                found = True
        if not found:
            print("Found no ID %08x in original file, abort!" % ID)
            exit(1)
        outData += t.replace('\r','').encode('utf-16le') + b'\x00\x00'
    outData = outData[:4] + struct.pack('<I', len(outData)) + outData[8:]
    return outData

def decompress(fn):
    # some files don't seem to be gzipped
    try:
        with gzip.open(fn, "rb") as fd:
            data = fd.read()
        gzipped = True
    except:
        with open(fn, "rb") as fd:
            data = fd.read()
        gzipped = False
    textList = []
    with open(fn + '.csv', 'r', newline='', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        curLine = 1
        curEntry = 1
        for row in reader:
            try:
                textList.append([int(row[0], 16), row[1]])
                curLine += row[1].count('\n')
            except:
                print("Problem on entry %d or line %d, aborting" % (curEntry, curLine))
                exit(1)
            curEntry += 1
            curLine += 1
    if data[:4] != b'ELPK':
        print("Invalid magic!");
        exit(1)
    (size, unk1, unk2, numEntries) = struct.unpack('<IIII', data[4:20])
    print("size %08x unk1 %08x unk2 %08x numEntries %d" % (size, unk1, unk2, numEntries))
    outHeader = data[:20]
    outFiles = b''
    fileOff = 20 + numEntries * 12
    if fileOff % 32 != 0:
        padLen = 32 - (fileOff % 32)
        outFiles += padLen * b'\x00'
        fileOff += padLen
    curOff = 20
    for i in range(numEntries):
        (ID, offset, size) = struct.unpack('<III', data[curOff:curOff+12])
        print("* entry %d: ID %08x offset %08x size %08x" % (i, ID, offset, size))
        subfile = data[offset:offset+size]
        if ID == 0xec992fcf:
            outFile = update_globals(subfile, textList)
        else:
            print("Nothing to do for file %08x, not updating anything" % ID)
            outFile = subfile
        print(len(subfile), '->', len(outFile))
        outHeader += struct.pack('<III', ID, fileOff, len(outFile))
        padding = b''
        #if (fileOff + len(outFile)) % 32 != 0:
        #    padding = b'\x00' * (32 - ((fileOff + len(outFile)) % 32))
        #if len(outFile) % 8 != 0:
        #    padding = b'\x00' * 4
        padding = b'\x00' * (64 - (len(outFile) % 64))
        fileOff += len(outFile + padding)
        outFiles += outFile + padding
        curOff += 12
    
    outData = outHeader + outFiles
    # update file size
    outData = outData[:4] + struct.pack('<I', len(outData)) + outData[8:]

    if gzipped:
        with gzip.open(fn + '.out', 'wb') as outfd:
            outfd.write(outData)
    else:
        with open(fn + '.out', 'wb') as outfd:
            outfd.write(outData)


if __name__ == '__main__':
    decompress(sys.argv[1])

