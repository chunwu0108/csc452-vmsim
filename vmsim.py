import argparse




def print_summary():
    pass

def fifo(frame_size, file):

    f_in = open(file, 'r')
    frame = []
    page_fault = 0
    mem_access = 0
    write_disk = 0

    for line in f_in:

        # Skip header
        if line[0] in "-=":
            continue

        instr = line[0:2].strip()

        if instr == 'I':
            pass
        elif instr == 'L':
            pass
        elif instr == 'S':
            pass
        else:
            print("invalid instruction")




    f_in.close()

def random(frame_size, file):
    pass

def opt(frame_size, file):
    pass

def clock(frame_size, file):
    pass



def main():

    # Parsing args
    parser = argparse.ArgumentParser(description='Optional app description')
    parser.add_argument(
        '-n', type=int, required=True, help='A number of frames')
    parser.add_argument(
        '-a', required=True, help='An algorithm to use for page replacement')
    parser.add_argument('tracename', help='A file name to trace')
    args = parser.parse_args()

    # Debug
    print("number of frames:", args.n)
    print("alg used:", args.a)
    print("filename:", args.tracename)

    # if the input algorithm isn't one of the following
    if not args.a.lower() in ['opt', 'clock', 'fifo', 'rand']:
        print(
            "Please choose 'opt', 'clock', 'fifo' or 'rand' for (-a) algorithm"
        )

    


if __name__ == "__main__":
    main()