import argparse
import random as rand
import time


class Page:
    '''
    This is a page object that keeps track
    of the current state of a page
    '''

    def __init__(self, dirty):
        self.dirty = dirty
        self.valid = False


class Node:
    '''
    This is a node object used in the clock alg
    ref = referenced
    '''

    def __init__(self, addr):
        self.addr = addr
        self.next = None
        self.ref = False


class Clock:
    '''
    This is the clock object, give a size of the frame
    and the page_table (list type)
    '''

    def __init__(self, size, page_table):
        self.head = Node(None)
        self.page_table = page_table

        # Creates size number of nodes and make a
        # circular path
        temp = self.head
        for i in range(size - 1):
            temp.next = Node(None)
            temp = temp.next
        temp.next = self.head

    def add(self, addr, op):
        '''
        Give an address and and operation ('r' for read)
        or ('w', for write) and this function will check
        if the address is in the frame already or not. If not
        it will follow the clock alg page replacement
        '''
        global page_fault
        global frame_size

        # Extract the last 21 bit address from the
        # given 32 bit
        hex_int = int("0x" + addr, 16)
        addr_22 = hex_int // (2**11)

        page_table = self.page_table

        # if the clock has the address
        temp = self.head
        for i in range(frame_size):
            # found in the frame
            if temp.addr == addr_22:
                if op == 'w':
                    page_table[addr_22].dirty = True
                temp.ref = True
                return
            temp = temp.next

        # when the address is not found in the clock
        # evict a frame
        page_fault += 1

        # check the first non-referenced page after head
        temp = self.head
        for i in range(frame_size + 1):
            # found the first non-referenced page
            if (temp.addr == None) or (not temp.ref):
                self.__evict_page(temp, addr_22, op)
                return
            temp.ref = False
            temp = temp.next

    def __evict_page(self, node, addr, op):
        '''
        This is a private function to remove the page
        from the frame, and add in the new one
        '''
        global write_disk

        # if the current frame is filled
        if node.addr != None:
            # clean up the old page from the page table
            old_page = self.page_table[node.addr]
            if old_page.dirty:
                write_disk += 1
            old_page.dirty = False
            old_page.valid = False

        new_page = self.page_table[addr]

        # Make the new page as valid
        if op == 'w':
            new_page.dirty = True
        else:
            new_page.dirty = False
        new_page.valid = True

        # set the current node to the new address
        node.ref = False
        node.addr = addr

        # move the "hand" of the clock to the next node
        self.head = node.next

        return


# global var used for results
page_fault = 0
mem_access = 0
write_disk = 0
frame_size = 1

# this is a dict that keeps track of which page number
# is used on the n-th instruction
page_number_used = {}
curr_line_num = 1


def print_summary(alg):
    '''
    This function prints the result
    '''
    global page_fault
    global mem_access
    global write_disk
    global frame_size

    print("Algorithm: {}".format(alg))
    print("Number of frames:       " + str(frame_size).rjust(10))
    print("Total memory accesses:  " + str(mem_access).rjust(10))
    print("Total page faults:      " + str(page_fault).rjust(10))
    print("Total writes to disk:   " + str(write_disk).rjust(10))


def line_dissect(line, page_table, frame, alg_add):
    '''
    This function read a line and extracts the information needed
    It takes a page table, current frame, and the name of the 
    algorithm used top evict pages
    '''

    global curr_line_num
    global mem_access

    # Skip header
    if line[0] in "-=" or line[2] != ' ':
        return

    # split the instruction type and address
    instr = line[0:2].strip()
    addr = line[3:].split(',')[0]

    if instr == 'I':  # READ
        access_mem(page_table, frame, addr, alg_add, op='r')
    elif instr == 'L':  # LOAD (READ)
        access_mem(page_table, frame, addr, alg_add, op='r')
        mem_access += 1
    elif instr == 'S':  # STORE (WRITE)
        access_mem(page_table, frame, addr, alg_add, op='w')
        mem_access += 1
    elif instr == 'M':  # MODIFY (READ & WRITE)
        access_mem(page_table, frame, addr, alg_add, op='r')
        access_mem(page_table, frame, addr, alg_add, op='w')
        mem_access += 1
    else:
        print("invalid instruction")
        return

    curr_line_num += 1


def page_table_has(table, addr):
    '''
    This checks if the address is valid in the page table
    '''
    if table[addr].valid:
        return table[addr]
    return None


def access_mem(page_table, frame, addr, alg_add, op="r"):
    '''
    This function access the memory and checks if the address
    is in mem or not. If not it will cause a page fault and 
    evict a page based on the algoritm
    '''
    global page_fault
    global write_disk
    global frame_size

    dirty = False

    # for clock alg only
    if type(frame) == Clock:
        frame.add(addr, op)
        return

    # Check to see if the page is in the frame
    # return the page obj if found, else return None
    hex_int = int("0x" + addr, 16)
    addr_22 = hex_int // (2**11)
    page = page_table_has(page_table, addr_22)

    # found in Frame
    if page != None:
        if op == 'w':
            page.dirty = True
        # DO NOTHING for read

    # page fault
    else:
        page_fault += 1
        if op == 'w':
            dirty = True
        # call the given alg function to replace a frame
        write_disk += alg_add(page_table, frame, addr, dirty)


def fifo_add_alg(page_table, frame, addr, dirty):
    '''
    This is the FIFO alg to replace a page, remove the first
    element of the list and append a new address at the end
    '''
    global frame_size

    # extract the 21 bit address
    hex_int = int("0x" + addr, 16)
    addr_22 = hex_int // (2**11)

    # update the new page in the page table as valid
    if dirty:
        page_table[addr_22].dirty = True
    page_table[addr_22].valid = True
    write = 0  # write to the disk count

    # if the frame is full, remove the first one
    if len(frame) >= frame_size:
        if page_table[frame[0]].dirty:
            write += 1
        page_table[frame[0]].valid = False
        page_table[frame[0]].dirty = False
        del frame[0]

    # add a new address to the frame
    frame.append(addr_22)

    return write  # 1 if wrote to mem, otherwise 0


def rand_add_alg(page_table, frame, addr, dirty):
    '''
    This is the random alg, randomly select one from
    the frame to be removed
    '''

    global frame_size

    # extract the 21 bit address
    hex_int = int("0x" + addr, 16)
    addr_22 = hex_int // (2**11)

    # update the new page in the page table as valid
    if dirty:
        page_table[addr_22].dirty = True
    page_table[addr_22].valid = True
    write = 0  # write to the disk count

    # pick a random number
    r = rand.randint(0, frame_size - 1)
    # if the frame is full
    if len(frame) >= frame_size:
        if page_table[frame[r]].dirty:
            write += 1
        page_table[frame[r]].valid = False
        page_table[frame[r]].dirty = False
        del frame[r]

    # add a new address to the frame
    frame.append(addr_22)

    return write  # 1 if wrote to mem, otherwise


def opt_add_alg(page_table, frame, addr, dirty):
    '''
    This is the Optimization alg to replace a frame,
    this requires a future knowledge to predict which frame
    to replace as the optimal result (minimal page fault)
    '''
    global frame_size
    global page_number_used

    # extracts the 21 bit address
    hex_int = int("0x" + addr, 16)
    addr_22 = hex_int // (2**11)

    # update the page to valid
    if dirty:
        page_table[addr_22].dirty = True
    page_table[addr_22].valid = True
    write = 0  # write to the disk count

    # if the frame is full
    if len(frame) >= frame_size:
        # find the next frame to remove, the frame that is used
        # in the furthest future (The max line number from the dict)
        max_line_num = 0
        target_addr = None

        # dubug
        curr_l = curr_line_num

        for x in frame:
            # remove line numbers that are less than the current
            while (len(page_number_used[str(x)]) != 0
                   and page_number_used[str(x)][0] < curr_line_num):
                del page_number_used[str(x)][0]

            # if the list of line numbers for that address is empty,
            # then it means that this address is not longer be used in the future
            # evict this page
            if len(page_number_used[str(x)]) == 0:
                target_addr = x
                break

            # if the address is still being used in the future,
            # see if the line number is the max
            else:
                if page_number_used[str(x)][0] > max_line_num:
                    max_line_num = page_number_used[str(x)][0]
                    target_addr = x

        # reset the old page
        if page_table[target_addr].dirty:
            write += 1
        page_table[target_addr].valid = False
        page_table[target_addr].dirty = False
        del frame[frame.index(target_addr)]

    # add a new address to the frame
    frame.append(addr_22)

    return write  # 1 if wrote to mem, otherwise


def fifo(file):
    '''
    The FIFO started function
    '''
    f_in = open(file, 'r')
    # create a page table and empty frame
    page_table = []
    for i in range(2**32 // 2**11):
        page_table.append(Page(False))
    frame = []

    # read each line in the file
    for line in f_in:
        line_dissect(line, page_table, frame, fifo_add_alg)

    print_summary("FIFO")
    f_in.close()


def random(file):

    f_in = open(file, 'r')
    # create a page table and empty frame
    page_table = []
    for i in range(2**32 // 2**11):
        page_table.append(Page(False))
    frame = []

    # read each line in the file
    for line in f_in:
        line_dissect(line, page_table, frame, rand_add_alg)

    print_summary("Random")
    f_in.close()


def opt(file):

    global page_number_used

    # fill in the dict of when each page number is used
    # a dict that contains the order of when each address is being used
    f_in = open(file, 'r')
    instr_num = 1
    for line in f_in:
        if line[0] in "-=" or line[2] != ' ':
            continue
        addr = line[3:].split(',')[0]
        hex_int = int("0x" + addr, 16)
        addr_22 = hex_int // (2**11)
        if not str(addr_22) in page_number_used:
            page_number_used[str(addr_22)] = [instr_num]
        else:
            page_number_used[str(addr_22)].append(instr_num)
        if line[1] == 'M':
            page_number_used[str(addr_22)].append(instr_num)
        instr_num += 1

    # reset the file
    f_in.seek(0)

    # create a page table and empty frame
    page_table = []
    for i in range(2**32 // 2**11):
        page_table.append(Page(False))
    frame = []

    # read each line
    for line in f_in:
        line_dissect(line, page_table, frame, opt_add_alg)

    print_summary("Optimization")
    f_in.close()


def clock(file):

    global frame_size

    f_in = open(file, 'r')

    # create a page table and empty frame
    page_table = []
    for i in range(2**32 // 2**11):
        page_table.append(Page(False))
    # frame using a clock object
    frame = Clock(frame_size, page_table)

    # read each line
    for line in f_in:
        line_dissect(line, page_table, frame, None)

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
    elif args.a == "opt":
        opt(args.tracename)
    else:
        print("Please enter -a ('fifo'|'rand'|'clock'|'opt')")


if __name__ == "__main__":
    main()