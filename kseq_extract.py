#!/usr/bin/python3

import gzip, struct, binascii, csv, sys

def get_text(data, off):
    chars = [(x, y) for x, y in zip(data[off::2], data[off+1::2])]
    size = chars.index((0, 0))
    return data[off:off+size*2].decode('utf-16le')

def parse_kseq(data):
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
    # these are the entries which are of interest, containing the pointers to the speaker's name & the dialogue contents
    for i in range(counts[0]):
        charnameData = data[offset+6:offset+8]
        # offset = -1 -> no speaker
        if charnameData != b'\xff\xff':
            textOffs.add(struct.unpack('<H', charnameData)[0] * 4)
        dialogueData = data[offset+8:offset+10]
        # offset = -1 -> no dialogue
        if dialogueData != b'\xff\xff':
            textOffs.add(struct.unpack('<H', dialogueData)[0] * 4)
        offset += 12
    return [get_text(data, off) for off in sorted(textOffs)]

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
        kseq = data[offset:offset+size]
        #with open('tmp.%08x' % ID, 'wb') as fd:
        #    fd.write(kseq) 
        for text in parse_kseq(kseq):
            csvData.append(['%08x' % ID, text])
        curOff += 12
    with open(fn + '.csv', 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        for x in csvData:
            writer.writerow(x)


if __name__ == '__main__':
    decompress(sys.argv[1])
