#!/usr/bin/python3

import gzip, struct, binascii, csv, sys

def update_kseq(data, textList):
    if data[:4] != b'KSEQ':
        print("Invalid kseq magic!", data[:16])
        return []
    # contains the list of offsets where there is text
    textOffs = set()
    (filesize, unk1, unk2) = struct.unpack('<III', data[4:16])
    # always the same
    if unk1 != 0x10052300:
        print("Invalid unk1")
    if unk2 != 0:
        print("Invalid unk2")
    # no idea what counts[2], counts[4], counts[5] are (they're maybe not even counts)
    counts = struct.unpack('<IIIIII', data[16:40])
    offset = 40
    # skip some unknown entries
    for i in range(counts[1]):
        offset += 8
    # skip some other unknown entries
    for i in range(counts[3]):
        offset += 8
    # this associates each text offset to the positions where the text is refered to
    textOffByOff = {}
    # these are the entries which are of interest, containing the pointers to the speaker's name & the dialogue contents
    for i in range(counts[0]):
        charnameData = data[offset+6:offset+8]
        # offset = -1 -> no speaker
        if charnameData != b'\xff\xff':
            off = struct.unpack('<H', charnameData)[0] * 4
            textOffByOff.setdefault(off, []).append(offset + 6)
        dialogueData = data[offset+8:offset+10]
        # offset = -1 -> no dialogue
        if dialogueData != b'\xff\xff':
            off = struct.unpack('<H', dialogueData)[0] * 4
            textOffByOff.setdefault(off, []).append(offset + 8)
        offset += 12
    minTextOff = sorted(textOffByOff.keys())[0]
    # keep the beginning of the file until the first text
    outData = data[:minTextOff]
    # output the texts
    for t, off in zip(textList, sorted(textOffByOff.keys())):
        print("putting text from offset %08x [%08x]" % (off, off // 4))
        newOff = len(outData) // 4
        for x in textOffByOff[off]:
            outData = outData[:x] + struct.pack('<H', newOff) + outData[x+2:]
        outData += t.replace('\r', '').encode('utf-16le') + b'\x00\x00'
        # addresses must be 4-aligned
        if len(outData) % 4 != 0:
            outData += b'\x00\x00'
    # update filesize
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
    textById = {}
    with open(fn + '.csv', 'r', newline='', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        curEntry = 1
        curLine = 1
        for row in reader:
            try:
                textById.setdefault(int(row[0], 16), []).append(row[1])
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
    curOff = 20
    for i in range(numEntries):
        (ID, offset, size) = struct.unpack('<III', data[curOff:curOff+12])
        print("* entry %d: ID %08x offset %08x size %08x" % (i, ID, offset, size))
        kseq = data[offset:offset+size]
        if ID not in textById:
            print("No text found for file %08x, not updating anything" % ID)
            outFile = kseq
        else:
            outFile = update_kseq(kseq, textById[ID])
        print(len(kseq), '->', len(outFile))
        #with open('tmp.%08x.in' % ID, 'wb') as fd2:
        #    fd2.write(kseq)
        #with open('tmp.%08x.out' % ID, 'wb') as fd2:
        #    fd2.write(outFile)
        outHeader += struct.pack('<III', ID, fileOff, len(outFile))
        padding = b''
        if len(outFile) % 8 != 0:
            padding = b'\x00\x00\x00\x00'
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

decompress(sys.argv[1])

