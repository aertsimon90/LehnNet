import socket
import threading
import LeCatchu
import time

class LehnNet_TCPSocket:
	def __init__(self, family=socket.AF_INET, engine=None, key="LehnNETCrypt", xbase=2, interval=1, iv=True, ivlength=256, ivxbase=2, ivinterval=1, s=None, create_psc=True, wcs=None):
		if not engine:
			engine = LeCatchu.LeCatchu_Engine(special_exchange=key)
		self.engine = engine
		self.key = key
		self.xbase = xbase
		self.interval = interval
		self.iv = iv
		self.ivlength = ivlength
		self.ivxbase = ivxbase
		self.ivinterval = ivinterval
		self.family = family
		self.wcs = wcs
		if not s:
			s = socket.socket(family, socket.SOCK_STREAM)
		self.s = s
		self.type = self.s.type
		self.proto = self.s.proto
		self.getsockname = self.s.getsockname
		self.getpeername = self.s.getpeername
		self.fileno = self.s.fileno
		self.shutdown = self.s.shutdown
		self.detach = self.s.detach
		self.setsockopt = self.s.setsockopt
		self.getsockopt = self.s.getsockopt
		self.settimeout = self.s.settimeout
		self.gettimeout = self.s.gettimeout
		self.setblocking = self.s.setblocking
		self.sendall = self.send
		self.bind = self.s.bind
		self.listen = self.s.listen
		self.sendto = self.s.sendto
		self.recvfrom = self.s.recvfrom
		if create_psc:
			self.psc = LeCatchu.ParallelStreamCipher(engine=self.engine, key=self.key, xbase=self.xbase, interval=self.interval, iv=self.iv, ivlength=self.ivlength, ivxbase=self.ivxbase, ivinterval=self.ivinterval)
	def accept(self, errors=False, retry=True):
		psc = LeCatchu.ParallelStreamCipher(engine=self.engine, key=self.key, xbase=self.xbase, interval=self.interval, iv=self.iv, ivlength=self.ivlength, ivxbase=self.ivxbase, ivinterval=self.ivinterval)
		c, addr = psc.accept_socket(self.s, errors=errors, retry=retry)
		client = LehnNet_TCPSocket(family=self.family, engine=self.engine, key=self.key, xbase=self.xbase, interval=self.interval, iv=self.iv, ivlength=self.ivlength, ivxbase=self.ivxbase, ivinterval=self.ivinterval, s=c, create_psc=False, wcs=self.wcs)
		client.psc = psc
		return client, addr
	def connect(self, addr):
		if self.wcs:
			self.psc.connect_socket(self.s, self.wcs)
			self.send(addr[0].encode("utf-8"))
			if self.recv(1) == b"1":
				self.send(str(addr[1]).encode("utf-8"))
				if self.recv(1) == b"1":
					return 0
				else:
					raise ValueError("Connection failed with WorldConnectServer.")
			else:
				raise ValueError("Connection failed with WorldConnectServer.")
		else:
			self.psc.connect_socket(self.s, addr)
			return 0
	def connect_ex(self, addr):
		try:
			self.connect(addr)
			return 0
		except Exception as e:
			try:
				return e.errno
			except:
				return 1
	def send(self, data):
		self.psc.send_socket(self.s, data)
	def recv(self, bufsize):
		return self.psc.recv_socket(self.s, bufsize)
	def recv_into(self, buffer, nbytes=None):
		if nbytes is None:
			nbytes = len(buffer)
		data = self.psc.recv_socket(self.s, nbytes)
		if not data:
			return 0
		read_len = len(data)
		buffer[:read_len] = data
		return read_len
	def close(self):
		self.s.close()
		self.psc = None
	def dup(self):
		s2 = LehnNet_TCPSocket(family=self.family, engine=self.engine, key=self.key, xbase=self.xbase, interval=self.interval, iv=self.iv, ivlength=self.ivlength, ivxbase=self.ivxbase, ivinterval=self.ivinterval, s=self.s.dup(), create_psc=False, wcs=self.wcs)
		s2.psc = self.psc
		return s2
	def share(self, *args, **kwargs):
		raise SystemError("Windows share is not supported in LehnNet.")

class LehnNet_WorldConnectServer: # Create WorldWideWeb TCP Proxy with LehnNet (LeTCPProxy)
	def __init__(self, s, addr=("0.0.0.0", 38483), backlog=None):
		if backlog is None:
			backlog = socket.SOMAXCONN
		self.s = s
		self.addr = addr
		self.engine = self.s.engine
		self.s.bind(addr)
		self.s.listen(backlog)
		self.run = True
		self.lock = threading.Lock()
		self.errors = []
		self.ts = []
		self.target_timeout = 3
		self.client_timeout = 3
		self.conn_timeout = 60
		self.perbuffersize = 4096
		self.nodatabreak = False
	def start(self, log=True):
		with self.lock:
			self.run = True
		print(f"Listening: {self.addr}")
		while self.run:
			try:
				client, addr = self.s.accept()
				if log:
					print(f"Connection: {addr}")
				client.settimeout(self.client_timeout)
				target = client.recv(1024).decode("utf-8")
				if log:
					print(f"Client requested target: {target} from {addr}")
				client.send(b"1")
				port = int(client.recv(5).decode("utf-8"))
				if log:
					print(f"Client requested port: {port} from {addr}")
				ss = socket.socket(self.s.family, socket.SOCK_STREAM)
				ss.settimeout(self.target_timeout)
				ss.connect((target, port))
				t = threading.Thread(target=self.listen_conn, args=(client, ss))
				t.start()
				with self.lock:
					self.ts.append(t)
				t = threading.Thread(target=self.listen_conn, args=(ss, client))
				t.start()
				with self.lock:
					self.ts.append(t)
				if log:
					print(f"Client request accepted. Listening upload/download for {addr} to ({target}, {port})")
				client.send(b"1")
			except Exception as e:
				with self.lock:
					self.errors.append(e)
				if log:
					print(f"Error: {e}")
	def stop(self):
		with self.lock:
			self.run = False
		for t in self.ts:
			try:
				t.join()
			except Exception as e:
				print(e)
	def listen_conn(self, s1, s2):
		last = time.time()
		while self.run:
			try:
				pack = s1.recv(self.perbuffersize)
				if pack:
					s2.sendall(pack)
					last = time.time()
				elif self.nodatabreak:
					break
			except Exception as e:
				with self.lock:
					self.errors.append(e)
				if time.time()-last > self.conn_timeout:
					break
		s1.close()
		s2.close()
