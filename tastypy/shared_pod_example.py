from multiprocessing import Process
import tastypy

def worker(pod, proc_num, num_procs):
	for i in pod:
		if i%num_procs == proc_num:
			pod[i] = i**2

def run_multiproc():
	num_procs = 5
	init = [(i, None) for i in range(25)]
	pod = tastypy.SharedPOD('my.pod', init=init)
	procs = []
	for i in range(num_procs):
		proc = Process(target=worker, args=(pod, i, num_procs))
		proc.start()
		procs.append(proc)

	for proc in procs:
		proc.join()

	for key, val in pod.iteritems():
		print key, val

if __name__ == '__main__':
	run_multiproc()
