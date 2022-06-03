from math import factorial

def index(seq):
	counter = 0
	l = len(seq)
	f = factorial(l)
	work_seq = list(range(l))
	for i in range(l):
		f //= l - i
		w_i = work_seq.index(seq[i])
		counter += w_i * f
		del work_seq[w_i]
	return counter

def k_th_permutation(len_, k):
	seq = []
	base = list(range(len_))
	fac = factorial(len_)
	for i in range(len_):
		fac //= len_ - i
		digit_i = k // fac
		digit = base.pop(digit_i)
		k -= digit_i * fac
		seq.append(digit)
	return seq
