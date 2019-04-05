import argparse
import random as rand
import time


class Page:
    def __init__(self, dirty):
        self.dirty = dirty
        self.valid = False


class Node:
    def __init__(self, addr):
        self.addr = addr
        self.next = None
        self.ref = False


class Clock:
    def __init__(self, size, page_table):
        self.head = Node(None)
        self.page_table = page_table
        temp = self.head
        for i in range(size - 1):
            temp.next = Node(None)
            temp = temp.next
        temp.next = self.head

    def add(self, addr, op):

        global page_fault

        hex_int = int("0x" + addr, 16)
        addr_22 = hex_int // (2**12)

        page_table = self.page_table

        # if the clock has the address
        if page_table[addr_22].valid:
            if op == 'w':
                page_table[addr_22].dirty = True
            page_table[addr_22].ref = True
            return

        # when the address is not found in the clock
        # evict a frame
        page_fault += 1

        # if the head is not referenced
        if (self.head.addr == None) or (not self.head.ref):
            self.__evict_page(self.head, addr_22, op)
            return
        else:
            page_table[self.head.addr].ref = False

        # check the first non-referenced page after head
        temp = self.head.next
        while (temp != self.head):
            if (temp.addr == None) or (not temp.ref):
                self.__evict_page(temp, addr_22, op)
                return
            page_table[temp.addr].ref = False
            temp = temp.next

    def __evict_page(self, node, addr, op):

        global write_disk

        if node.addr != None:
            old_page = self.page_table[node.addr]
            if old_page.dirty:
                write_disk += 1
            old_page.dirty = False
            old_page.valid = False

        new_page = self.page_table[addr]

        if op == 'w':
            new_page.dirty = True
        else:
            new_page.dirty = False
        new_page.valid = True

        node.ref = False
        node.addr = addr
        self.head = node

        return


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


def line_dissect(line, page_table, frame, alg_mem_access, alg_add):

    # Skip header
    if line[0] in "-=":
        return

    instr = line[0:2].strip()
    addr = line[3:].split(',')[0]

    if instr == 'I':  # READ
        alg_mem_access(page_table, frame, addr, alg_add, op='r')
    elif instr == 'L':  # LOAD (READ)
        alg_mem_access(page_table, frame, addr, alg_add, op='r')
    elif instr == 'S':  # STORE (WRITE)
        alg_mem_access(page_table, frame, addr, alg_add, op='w')
    elif instr == 'M':  # MODIFY (READ & WRITE)
        alg_mem_access(page_table, frame, addr, alg_add, op='r')
        alg_mem_access(page_table, frame, addr, alg_add, op='w')
    else:
        print("invalid instruction")


def page_table_has(table, addr):
    if table[addr].valid:
        return table[addr]
    return None


def access_mem(page_table, frame, addr, alg_add, op="r"):

    global page_fault
    global mem_access
    global write_disk
    global frame_size

    dirty = False
    mem_access += 1

    # for clock alg only
    if type(frame) == Clock:
        frame.add(addr, op)
        return

    # Check to see if the page is in the frame
    # return the page obj if found, else return None
    hex_int = int("0x" + addr, 16)
    addr_22 = hex_int // (2**12)
    page = page_table_has(page_table, addr_22)

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
        write_disk += alg_add(page_table, frame, addr, dirty)


def fifo_add_alg(page_table, frame, addr, dirty):

    global frame_size

    hex_int = int("0x" + addr, 16)
    addr_22 = hex_int // (2**12)

    page_table[addr_22].valid = True
    write = 0  # write to the disk count

    # if the frame is full
    if len(frame) >= frame_size:
        if page_table[frame[0]].dirty:
            write += 1
        page_table[frame[0]].valid = False
        page_table[frame[0]].dirty = False
        del frame[0]
    frame.append(addr_22)

    return write


def rand_add_alg(page_table, frame, addr, dirty):

    global frame_size

    hex_int = int("0x" + addr, 16)
    addr_22 = hex_int // (2**12)

    page_table[addr_22].valid = True
    write = 0  # write to the disk count

    r = rand.randint(0, frame_size - 1)
    # if the frame is full
    if len(frame) >= frame_size:
        if page_table[frame[r]].dirty:
            write += 1
        page_table[frame[r]].valid = False
        page_table[frame[r]].dirty = False
        del frame[r]
    frame.append(addr_22)

    return write


def fifo(file):

    f_in = open(file, 'r')
    page_table = []
    for i in range(2**32 // 2**12):
        page_table.append(Page(False))

    frame = []
    for line in f_in:
        line_dissect(line, page_table, frame, access_mem, fifo_add_alg)

    print_summary("FIFO")
    f_in.close()


def random(file):

    f_in = open(file, 'r')
    page_table = []
    for i in range(2**32 // 2**12):
        page_table.append(Page(False))

    frame = []
    for line in f_in:
        line_dissect(line, page_table, frame, access_mem, rand_add_alg)

    print_summary("Random")
    f_in.close()


def opt(file):
    pass


def clock(file):

    global frame_size

    f_in = open(file, 'r')

    page_table = []
    for i in range(2**32 // 2**12):
        page_table.append(Page(False))

    frame = Clock(frame_size, page_table)

    for line in f_in:
        line_dissect(line, page_table, frame, access_mem, None)

    print_summary("Clock")
    f_in.close()


def main():

    # Parsing args
    parser = argparse.ArgumentParser(description='Optional app description')
    parser.add_argument(
        '-n', type=int, required=True, help='A number of frames')
    parser.add_argument(
        '-a', required=True, help='An algorithm to use for page replacement')
    parser.add_argument('tracename', help='A file name to trace')
    args = parser.parse_args()

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
    elif args.a == "clock":
        clock(args.tracename)


if __name__ == "__main__":
    main()