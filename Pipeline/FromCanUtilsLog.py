import re

def canUtilsToTSV(filename):
    outFileName = filename + ".tsv"
    with open(outFileName, "w") as outFile:
        with open(filename, "r") as file:
            linePattern = re.compile(r"\((\d+.\d+)\)\s+[^\s]+\s+(.{3}|.{8})#([0-9A-F]+)")

            while True:
                line = file.readline()
                if not line:
                    return outFileName
                tokens = linePattern.search(line).groups()

                # write delta time
                writeLine = tokens[0]

                # write arb id
                writeLine += '\t' + tokens[1]

                # write dlc
                bytes = int(len(tokens[2]) / 2)
                writeLine += '\t' + str(bytes)

                # write bytes
                for b in range(bytes):
                    writeLine += '\t' + tokens[2][b*2:b*2+2]

                outFile.write(writeLine + '\n')
