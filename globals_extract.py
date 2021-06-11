#!/usr/bin/python3

import gzip, struct, binascii, csv, sys

MAX_STR_SIZE=2000

def get_text(data, off):
    chars = [(x, y) for x, y in zip(data[off:off+MAX_STR_SIZE:2], data[off+1:off+MAX_STR_SIZE+1:2])]
    size = chars.index((0, 0))
    return data[off:off+size*2].decode('utf-16le')

def parse_globals(data):
    (fileSize, unk1, unk2, numEntries) = struct.unpack('<IIII', data[4:4*5])
    if data[:4] != b'STja':
        print("Invalid globals.bin subfile!");
        return []
    fileOff = 20
    textOffSet = set()
    textId = {}
    for i in range(numEntries):
        (ID, textOff) = struct.unpack('<II', data[fileOff:fileOff+8])
        textOffSet.add(textOff)
        textId[textOff] = ID
        fileOff += 8
    textList = []
    for x in sorted(textOffSet):
        textList.append(['%08x' % textId[x], get_text(data, x)])
    return textList

def decompress(fn):
    # some files don't seem to be gzipped
    try:
        with gzip.open(fn, "rb") as fd:
            data = fd.read()
    except:
        with open(fn, "rb") as fd:
            data = fd.read()
    if data[:4] != b'ELPK':
        print("Invalid magic!");
        exit(1)
    (size, unk1, unk2, numEntries) = struct.unpack('<IIII', data[4:20])
    print("size %08x unk1 %08x unk2 %08x numEntries %d" % (size, unk1, unk2, numEntries))
    curOff = 20
    csvData = []
    for i in range(numEntries):
        (ID, offset, size) = struct.unpack('<III', data[curOff:curOff+12])
        print("* entry %d: ID %08x offset %08x size %08x" % (i, ID, offset, size))
        subfile = data[offset:offset+size]
        if ID == 0xec992fcf:
            print("extracting globals file")
            for text in parse_globals(subfile):
                csvData.append(text)
        else:
            print("ignoring")
        curOff += 12
    with open(fn + '.csv', 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        for x in csvData:
            writer.writerow(x)

if __name__ == '__main__':
    decompress(sys.argv[1])

