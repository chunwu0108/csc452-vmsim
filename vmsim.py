import argparse
import random as rand
import time


class Page:
    def __init__(self, addr, dirty):
        self.addr = addr
        self.dirty = dirty

    def __eq__(self, addr):
        return self.addr == addr

class Page_v2(Page):
    def __init__(self, addr, dirty):
        Page.__init__(self, addr, dirty)
        self.next = None
        self.ref = False

class Clock:
    def __init__(self, size):
        pass
    def add(self):
        pass
    def reset_ref(self):
        pass


page_fault = 0
mem_access = 0
write_disk = 0
frame_size = 1


def print_summary(alg):

    global page_fault
    global mem_access
    global write_disk
    global frame_size

    print("Algorithm: {}".format(alg))
    print("Number of frames:       " + str(frame_size).rjust(10))
    print("Total memory accesses:  " + str(mem_access).rjust(10))
    print("Total page faults:      " + str(page_fault).rjust(10))
    print("Total writes to disk:   " + str(write_disk).rjust(10))


def line_dissect(line, frame, alg_mem_access, alg_add):

    # Skip header
    if line[0] in "-=":
        return

    instr = line[0:2].strip()
    addr = line[3:].split(',')[0]

    if instr == 'I':  # READ
        alg_mem_access(frame, addr, alg_add, op='r')
    elif instr == 'L':  # LOAD (READ)
        alg_mem_access(frame, addr, alg_add, op='r')
    elif instr == 'S':  # STORE (WRITE)
        alg_mem_access(frame, addr, alg_add, op='w')
    elif instr == 'M':  # MODIFY (READ & WRITE)
        alg_mem_access(frame, addr, alg_add, op='r')
        alg_mem_access(frame, addr, alg_add, op='w')
    else:
        print("invalid instruction")


def frame_has(frame, addr):
    for x in frame:
        if x == addr:
            return x
    return None


def access_mem(frame, addr, alg_add, op="r"):

    global page_fault
    global mem_access
    global write_disk
    global frame_size

    dirty = False
    mem_access += 1

    # Check to see if the page is in the frame
    # return the page obj if found, else return None
    page = frame_has(frame, addr)

    # found in RAM
    if page != None:
        if op == 'w':
            page.dirty = True
        # DO NOTHING for read
    # page fault
    else:
        page_fault += 1
        if op == 'w':
            dirty = True
        write_disk += alg_add(frame, addr, dirty)


def fifo_add_alg(frame, addr, dirty):

    global frame_size
    p = Page(addr, dirty)
    write = 0  # write to the disk count

    # if the frame is full
    if len(frame) >= frame_size:
        if frame[0].dirty:
            write += 1
        del frame[0]
    frame.append(p)

    return write


def rand_add_alg(frame, addr, dirty):

    global frame_size
    p = Page(addr, dirty)
    write = 0  # write to the disk count

    r = rand.randint(0, frame_size - 1)
    # if the frame is full
    if len(frame) >= frame_size:
        if frame[r].dirty:
            write += 1
        del frame[r]
    frame.append(p)

    return write


def fifo(file):

    f_in = open(file, 'r')
    frame = []

    for line in f_in:
        line_dissect(line, frame, access_mem, fifo_add_alg)

    print_summary("FIFO")
    f_in.close()


def random(file):

    f_in = open(file, 'r')
    frame = []

    for line in f_in:
        line_dissect(line, frame, access_mem, rand_add_alg)

    print_summary("Random")
    f_in.close()


def opt(file):
    pass


def clock(file):
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

    global frame_size
    frame_size = args.n

    if args.a == "fifo":
        fifo(args.tracename)
    elif args.a == "rand":
        rand.seed(time.time())
        random(args.tracename)


if __name__ == "__main__":
    main()