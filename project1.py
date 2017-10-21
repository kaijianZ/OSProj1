import sys


class Process(object):
    def __init__(self, info):
        self.proc_id = info[0]
        self.arr_t, self.burst_t, self.num_bursts, self.io_t = map(int,
                                                                   info[1:])
        self.ready_begin_t = self.arr_t
        self.state = 'READY'
        self.end_t = -1
        self.original_num_bursts = self.num_bursts
        self.remaining_t = self.burst_t

    def wait_t(self, t):
        return t - self.ready_begin_t


# return the string of the current items in queue
def print_queue(ready_q):
    if not ready_q:
        return '[Q <empty>]'
    str_q = '[Q'
    for process in ready_q:
        str_q += ' ' + process.proc_id
    return str_q + ']'


def arrive(processes, ready_q, t, srt=False):
    for process in processes:
        if process.arr_t == t and process not in ready_q:
            ready_q.append(process)
            if srt:
                ready_q.sort(key=lambda x: x.remaining_t)
            print('time {}ms: Process {} arrived and added to '
                  'ready queue {}'.format(t, process.proc_id
                                          , print_queue(ready_q)))


def io_arrive(io_q, ready_q, t, srt=False):
    return_v = False
    while len(io_q) and io_q[0].end_t == t:
        process = io_q[0]
        process.state = 'READY'
        process.ready_begin_t = t
        ready_q.append(process)
        if srt:
            ready_q.sort(key=lambda x: x.remaining_t)
        io_q.pop(0)
        print('time {}ms: Process {} completed I/O;'
              ' added to ready queue {}'.format(t, process.proc_id
                                                , print_queue(ready_q)))
        return_v = True
    return return_v


def finish_process(io_q, ready_q, t, running_p, t_cs, srt=False):
    def s(x):
        return 's' if x != 1 else ''

    running_p.remaining_t = running_p.burst_t

    print('time {}ms: Process {} completed a CPU burst; {} burst{}'
          ' to go {}'.format(t, running_p.proc_id, running_p.num_bursts,
                             s(running_p.num_bursts),
                             print_queue(ready_q)))
    if running_p.io_t != 0:
        io_q.append(running_p)
        running_p.end_t = int(t + running_p.io_t + t_cs / 2)
        io_q.sort(key=lambda x: x.end_t)
        print('time {}ms: Process {} switching out of CPU; will block'
              ' on I/O until time '
              '{}ms {}'.format(t, running_p.proc_id, running_p.end_t
                               , print_queue(ready_q)))
        running_p.state = 'BLOCKED'
    else:
        running_p.ready_begin_t = t
        running_p.state = 'READY'
        ready_q.append(running_p)
        if srt:
            ready_q.sort(key=lambda x: x.remaining_t)


def write_stat(output, status):
    output.write('-- average CPU burst time: {:.2f} ms\n'
                 '-- average wait time: {:.2f} ms\n'
                 '-- average turnaround time: {:.2f} ms\n'
                 '-- total number of context switches: {:d}\n'
                 '-- total number of'
                 ' preemptions: '.format(sum(status[0]) / len(status[0]),
                                         sum(status[1]) / len(status[1]),
                                         sum(status[2]) / len(status[2]),
                                         status[3]))


if __name__ == "__main__":
    file_name = sys.argv[1]
    with open(file_name, 'r') as f:
        text = f.read().split('\n')

    output_name = sys.argv[2]
    outfile = open(output_name, 'w')

    processes = []
    for i in text:
        i.strip()
        if len(i) and i[0] != '#':
            processes.append(Process(i.split('|')))

    ready_queue = []
    io_queue = []
    t = 0
    t_cs = 8
    start_t = -1
    end_t = -1
    running_p = None
    # [0:cpu_burst, 1:wait_time, 2:turn_around_time
    # 3:context_switches, 4: preemption]
    stat = [[], [], [], 0, 0]

    outfile.write('Algorithm FCFS')
    print('time {}ms: Simulator started for FCFS {}'.format(t, print_queue(
        ready_queue)))
    while len(processes):
        if running_p is not None \
                and running_p.remaining_t == 0:
            running_p.num_bursts -= 1
            if running_p.num_bursts == 0:
                print('time {}ms: Process {}'
                      ' terminated {}'.format(t, running_p.proc_id
                                              , print_queue(ready_queue)))
                processes.remove(running_p)
                running_p.remaining_t = -1
            else:
                finish_process(io_queue, ready_queue, t, running_p, t_cs)

            io_arrive(io_queue, ready_queue, t)
            end_t = t + int(t_cs / 2)
            continue
        else:
            if io_arrive(io_queue, ready_queue, t):
                continue

        if end_t == t:
            stat[2].append(t - running_p.ready_begin_t)
            running_p = None
            end_t = -1
            continue

        arrive(processes, ready_queue, t)

        if running_p is None and len(ready_queue):
            running_p = ready_queue[0]
            stat[0].append(running_p.burst_t)
            ready_queue.pop(0)
            stat[1].append(running_p.wait_t(t))
            stat[3] += 1
            start_t = t + int(t_cs / 2)

        if start_t == t:
            print('time {}ms: Process {} started'
                  ' using the CPU {}'.format(t, running_p.proc_id
                                             , print_queue(ready_queue)))
            running_p.state = 'RUNNING'

        if running_p is not None and running_p.state == 'RUNNING':
            running_p.remaining_t -= 1
        t += 1

    t += int(t_cs / 2)

    print('time {}ms: Simulator ended for FCFS'.format(t))
    print(stat)
    write_stat(outfile, stat)
    # start running SRT

    ready_queue = []
    io_queue = []
    t = 0
    t_cs = 8
    start_t = -1
    end_t = -1
    running_p = None

    processes = []
    for i in text:
        i.strip()
        if len(i) and i[0] != '#':
            processes.append(Process(i.split('|')))

    # [0:cpu_burst, 1:wait_time, 2:turn_around_time
    # 3:context_switches, 4: preemption]
    stat = [[], [], [], 0, 0]

    outfile.write('Algorithm SRT')
    print('time {}ms: Simulator started for SRT {}'.format(t, print_queue(
        ready_queue)))

    while len(processes):
        if running_p is not None \
                and running_p.remaining_t == 0:
            running_p.num_bursts -= 1
            if running_p.num_bursts == 0:
                print('time {}ms: Process {}'
                      ' terminated {}'.format(t, running_p.proc_id
                                              , print_queue(ready_queue)))
                processes.remove(running_p)
                running_p.remaining_t = -1
            else:
                finish_process(io_queue, ready_queue, t, running_p, t_cs, True)

            io_arrive(io_queue, ready_queue, t, True)
            end_t = t + int(t_cs / 2)
            continue
        else:
            if io_arrive(io_queue, ready_queue, t, True):
                continue

        if end_t == t:
            stat[2].append(t - running_p.ready_begin_t)
            running_p = None
            end_t = -1
            continue

        arrive(processes, ready_queue, t)

        if running_p is None and len(ready_queue):
            running_p = ready_queue.pop(0)
            stat[0].append(running_p.burst_t)
            stat[1].append(running_p.wait_t(t))
            stat[3] += 1
            start_t = t + int(t_cs / 2)

        if running_p is not None and len(ready_queue) and ready_queue[
            0].remaining_t < running_p.remaining_t\
                and running_p.state == 'RUNNING':
            ready_queue.append(running_p)
            running_p.state = 'READY'
            running_p = ready_queue.pop(0)
            ready_queue.sort(key=lambda x: x.remaining_t)
            start_t = t + t_cs

        if running_p is not None and start_t == t:
            print('time {}ms: Process {} started'
                  ' using the CPU {}'.format(t, running_p.proc_id
                                             , print_queue(ready_queue)))
            running_p.state = 'RUNNING'

        if running_p is not None and running_p.state == 'RUNNING':
            running_p.remaining_t -= 1
        t += 1

    t += int(t_cs / 2) - 1
