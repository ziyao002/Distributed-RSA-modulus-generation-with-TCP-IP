import socket
from threading import Thread
import multiprocessing
from multiprocessing import Process
import gmpy2
import time
from gmpy2 import mpz
from queue import Queue

# P1:server, P2:server/client, P3:client
server_port1 = 9000
server_port2 = 8000
client_port2 = 8001
client_port31 = 7000
client_port32 = 7001


def rec_msg(tcp_socket, port_num, q12, q13):
    str_list = []
    while True:
        s_data = tcp_socket.recv(1024).decode('gb2312')
        if len(s_data) != 0:
            for item in s_data:
                str_list.append(item)
                if item == 'x':
                    str_data = "".join(str_list[0:-1])
                    # print("rec_data =", int(str_data), "port_num =", port_num)
                    str_list.clear()
                    if port_num == server_port1:
                        q12.put(int(str_data))
                    elif port_num == client_port32:
                        q13.put(int(str_data))
                    else:
                        raise Exception("Port number error!")


def send_msg(tcp_socket, port_num, flag_send_2_to_1, flag_send_2_to_3, data_2_to_1_queue, data_2_to_3_queue):
    while True:
        if port_num == server_port1 and flag_send_2_to_1.value:
            c_data = str(data_2_to_1_queue.get())+'x'
            tcp_socket.send(c_data.encode("gb2312"))
            # print("send_data =", data_2_to_1_queue.value, "port_num =", port_num)
            flag_send_2_to_1.value = 0
        elif port_num == client_port32 and flag_send_2_to_3.value:
            c_data = str(data_2_to_3_queue.get())+'x'
            tcp_socket.send(c_data.encode("gb2312"))
            # print("send_data =", data_2_to_3_queue.value, "port_num =", port_num)
            flag_send_2_to_3.value = 0
        else:
            pass
    # tcp_socket.close()


def worker(new_socket, port_num, flag_send_2_to_1, flag_send_2_to_3, data_2_to_1_queue, data_2_to_3_queue, q21, q23, connect_flag_23):
    if port_num == client_port32:
        connect_flag_23.value = 1
        print("Connected by P3")
    else:
        raise Exception("Connection error!")

    t_send = Thread(target=send_msg, args=(new_socket, port_num, flag_send_2_to_1, flag_send_2_to_3, data_2_to_1_queue, data_2_to_3_queue))
    t_rec = Thread(target=rec_msg, args=(new_socket, port_num, q21, q23))

    t_send.start()
    t_rec.start()

    t_send.join()
    t_rec.join()


def server(flag_send_2_to_1, flag_send_2_to_3, data_2_to_1_queue, data_2_to_3_queue, q21, q23, connect_flag_23):
    print("server start")
    host = socket.gethostname()
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, True)  # disable Nalge
    server_socket.bind((host, server_port2))
    server_socket.listen(5)

    while True:
        new_socket, port_num = server_socket.accept()
        new_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, True)  # disable Nalge
        p = Process(target=worker, args=(new_socket, port_num[1], flag_send_2_to_1, flag_send_2_to_3, data_2_to_1_queue, data_2_to_3_queue, q21, q23, connect_flag_23))
        p.start()
        new_socket.close()


def client(flag_send_2_to_1, flag_send_2_to_3, data_2_to_1_queue, data_2_to_3_queue, q21, q23, connect_flag_21):
    print("client start")
    host = socket.gethostname()
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    client_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, True)  # disable Nalge
    client_socket.bind((host, client_port2))
    client_socket.connect((host, server_port1))
    # client_socket.connect(('172.21.176.163', server_port1))
    connect_flag_21.value = 1
    print("Connect to P1")

    t_send = Thread(target=send_msg, args=(client_socket, server_port1, flag_send_2_to_1, flag_send_2_to_3, data_2_to_1_queue, data_2_to_3_queue))
    t_rec = Thread(target=rec_msg, args=(client_socket, server_port1, q21, q23))

    t_send.start()
    t_rec.start()

    t_send.join()
    t_rec.join()


class DPaillier:
    def __init__(self, party_index):
        self.KeyLength = mpz(128)
        self.PartyIndex = party_index
        self.PartyNumber = 3
        self.PP = 0
        self.pi = 0
        self.qi = 0
        self.a1 = 0
        self.aa1 = 0
        self.b1 = 0
        self.bb1 = 0
        self.ppi = 0
        self.qqi = 0
        self.c0 = 0
        self.c1 = 0
        self.c2 = 0
        self.cc0 = 0
        self.cc1 = 0
        self.cc2 = 0
        self.Ni = 0
        self.N = 0
        self.Q = 0
        self.gg = 0

    def gen_coprime(self, x):
        while True:
            random_state = gmpy2.random_state(int(time.time()*100000))
            coprime = gmpy2.mpz_random(random_state, x)
            if gmpy2.gcd(coprime, x) == 1:
                return coprime

    def pick_pq(self):
        pq = mpz(2)
        random_state = gmpy2.random_state(int(time.time()*100000))
        if self.PartyIndex == 1:
            while gmpy2.f_mod(pq, 4) != 3 or (pq - pow(2, self.KeyLength - 1) <= 0):
                pq = gmpy2.mpz_random(random_state, pow(2, self.KeyLength))
        else:
            while gmpy2.f_mod(pq, 4) != 0 or (pq - pow(2, self.KeyLength - 1) <= 0):
                pq = gmpy2.mpz_random(random_state, pow(2, self.KeyLength))
        return pq

    def pick_pp(self):
        pp = gmpy2.next_prime(pow(gmpy2.mul(self.PartyNumber, gmpy2.mul(3, pow(2, self.KeyLength - 1))), 2))
        return pp

    def coefficient_generation(self):
        random_state = gmpy2.random_state(int(time.time()*100000))
        self.a1 = gmpy2.mpz_random(random_state, self.PP)
        random_state = gmpy2.random_state(int(time.time()*100000))
        self.aa1 = gmpy2.mpz_random(random_state, self.PP)
        random_state = gmpy2.random_state(int(time.time()*100000))
        self.b1 = gmpy2.mpz_random(random_state, self.PP)
        random_state = gmpy2.random_state(int(time.time()*100000))
        self.bb1 = gmpy2.mpz_random(random_state, self.PP)
        random_state = gmpy2.random_state(int(time.time()*100000))
        self.ppi = gmpy2.mpz_random(random_state, self.PP)
        random_state = gmpy2.random_state(int(time.time()*100000))
        self.qqi = gmpy2.mpz_random(random_state, self.PP)
        self.c0 = mpz(0)
        random_state = gmpy2.random_state(int(time.time()*100000))
        self.c1 = gmpy2.mpz_random(random_state, self.PP)
        random_state = gmpy2.random_state(int(time.time()*100000))
        self.c2 = gmpy2.mpz_random(random_state, self.PP)
        random_state = gmpy2.random_state(int(time.time()*100000))
        self.cc0 = gmpy2.mpz_random(random_state, self.PP)
        random_state = gmpy2.random_state(int(time.time()*100000))
        self.cc1 = gmpy2.mpz_random(random_state, self.PP)
        random_state = gmpy2.random_state(int(time.time()*100000))
        self.cc2 = gmpy2.mpz_random(random_state, self.PP)

    def compute_tuple(self):
        self.PP = self.pick_pp()
        # print("pick PP done")
        self.coefficient_generation()
        # print("coefficient generation done")

        pi1 = gmpy2.f_mod((self.pi + self.a1 * 1), self.PP)
        ppi1 = gmpy2.f_mod((self.ppi + self.aa1 * 1), self.PP)
        qi1 = gmpy2.f_mod((self.qi + self.b1 * 1), self.PP)
        qqi1 = gmpy2.f_mod((self.qqi + self.bb1 * 1), self.PP)
        hi1 = gmpy2.f_mod((self.c0 + self.c1 * 1 + self.c2 * 1 * 1), self.PP)
        hhi1 = gmpy2.f_mod((self.cc0 + self.cc1 * 1 + self.cc2 * 1 * 1), self.PP)

        pi2 = gmpy2.f_mod((self.pi + self.a1 * 2), self.PP)
        ppi2 = gmpy2.f_mod((self.ppi + self.aa1 * 2), self.PP)
        qi2 = gmpy2.f_mod((self.qi + self.b1 * 2), self.PP)
        qqi2 = gmpy2.f_mod((self.qqi + self.bb1 * 2), self.PP)
        hi2 = gmpy2.f_mod((self.c0 + self.c1 * 2 + self.c2 * 2 * 2), self.PP)
        hhi2 = gmpy2.f_mod((self.cc0 + self.cc1 * 2 + self.cc2 * 2 * 2), self.PP)

        pi3 = gmpy2.f_mod((self.pi + self.a1 * 3), self.PP)
        ppi3 = gmpy2.f_mod((self.ppi + self.aa1 * 3), self.PP)
        qi3 = gmpy2.f_mod((self.qi + self.b1 * 3), self.PP)
        qqi3 = gmpy2.f_mod((self.qqi + self.bb1 * 3), self.PP)
        hi3 = gmpy2.f_mod((self.c0 + self.c1 * 3 + self.c2 * 3 * 3), self.PP)
        hhi3 = gmpy2.f_mod((self.cc0 + self.cc1 * 3 + self.cc2 * 3 * 3), self.PP)

        return [[pi1, ppi1, qi1, qqi1, hi1, hhi1], [pi2, ppi2, qi2, qqi2, hi2, hhi2], [pi3, ppi3, qi3, qqi3, hi3, hhi3]]

    def send_pq_tuple(self, pq_tuple, send_party_index, flag_send_2_to_1, flag_send_2_to_3, data_2_to_1_queue, data_2_to_3_queue):
        for ctuple in pq_tuple:
            self.send_data(ctuple, send_party_index, flag_send_2_to_1, flag_send_2_to_3, data_2_to_1_queue, data_2_to_3_queue)

    def send_data(self, data, party_send_index, flag_send_2_to_1, flag_send_2_to_3, data_2_to_1_queue, data_2_to_3_queue):
        while True:
            if party_send_index == 1 and flag_send_2_to_1.value == 0:
                data_2_to_1_queue.put(data)
                flag_send_2_to_1.value = 1
                break
            elif party_send_index == 3 and flag_send_2_to_3.value == 0:
                data_2_to_3_queue.put(data)
                flag_send_2_to_3.value = 1
                break
            else:
                pass

    def receive_pq_tuple_list(self, self_pq_tuple_list, q21, q23):
        q21_list = []
        q23_list = []
        while True:
            while True:
                while not q21.empty():
                    q21_list.append(mpz(q21.get()))
                    if q21_list:
                        if q21_list[-1] == mpz(11112222):
                            break
                if q21_list:
                    if q21_list[-1] == mpz(11112222):
                        break
            while True:
                while not q23.empty():
                    q23_list.append(mpz(q23.get()))
                    if q23_list:
                        if q23_list[-1] == mpz(33332222):
                            break
                if q23_list:
                    if q23_list[-1] == mpz(33332222):
                        break
            break
        return [q21_list[0:-1], self_pq_tuple_list[1], q23_list[0:-1]]

    def receive_Ni_list(self, self_Ni, q21, q23):
        q21_list = []
        q23_list = []
        while True:
            while True:
                while not q21.empty():
                    q21_list.append(mpz(q21.get()))
                    if q21_list:
                        if q21_list[-1] == 11112222:
                            break
                if q21_list:
                    if q21_list[-1] == 11112222:
                        break
            while True:
                while not q23.empty():
                    q23_list.append(mpz(q23.get()))
                    if q23_list:
                        if q23_list[-1] == 33332222:
                            break
                if q23_list:
                    if q23_list[-1] == 33332222:
                        break
            break
        return [q21_list[0], self_Ni, q23_list[0]]

    def send_pq_tuple_list(self, pq_tuple_list, flag_send_2_to_1, flag_send_2_to_3, data_2_to_1_queue, data_2_to_3_queue):
        self.send_pq_tuple(pq_tuple_list[0], 1, flag_send_2_to_1, flag_send_2_to_3, data_2_to_1_queue, data_2_to_3_queue)
        self.send_data(22221111, 1, flag_send_2_to_1, flag_send_2_to_3, data_2_to_1_queue, data_2_to_3_queue)
        self.send_pq_tuple(pq_tuple_list[2], 3, flag_send_2_to_1, flag_send_2_to_3, data_2_to_1_queue, data_2_to_3_queue)
        self.send_data(22223333, 3, flag_send_2_to_1, flag_send_2_to_3, data_2_to_1_queue, data_2_to_3_queue)
        while True:
            if flag_send_2_to_3.value == 0:
                break

    def share_verification(self, received_pq_tuple_list):
        check_flag = 0
        if check_flag == 1:
            raise Exception("Share verification fails!")

    def N_verification(self, Ni_list):
        check_flag = 0
        if check_flag == 1:
            raise Exception("Share verification fails!")

    def compute_Ni(self, received_pq_tuple_list):
        Ni = gmpy2.f_mod(((received_pq_tuple_list[0][0] + received_pq_tuple_list[1][0] + received_pq_tuple_list[2][
            0]) * (received_pq_tuple_list[0][2] + received_pq_tuple_list[1][2] + received_pq_tuple_list[2][2]) + (
                                     received_pq_tuple_list[0][4] + received_pq_tuple_list[1][4] +
                                     received_pq_tuple_list[2][4])), self.PP)
        # print("Ni = ", Ni)
        return Ni

    def compute_N(self, Ni_list):
        L1 = mpz(int((0 - 2) * (0 - 3) / ((1 - 2) * (1 - 3))))
        L2 = mpz(int((0 - 1) * (0 - 3) / ((2 - 1) * (2 - 3))))
        L3 = mpz(int((0 - 1) * (0 - 2) / ((3 - 1) * (3 - 2))))
        self.N = gmpy2.f_mod(gmpy2.mul(Ni_list[0], L1) + gmpy2.mul(Ni_list[1], L2) + gmpy2.mul(Ni_list[2], L3), self.PP)
        # print("Ni_list = ", Ni_list)
        print("Candidate modulus = ", self.N)

    def send_Ni(self, Ni, flag_send_2_to_1, flag_send_2_to_3, data_2_to_1_queue, data_2_to_3_queue):
        self.send_data(Ni, 1, flag_send_2_to_1, flag_send_2_to_3, data_2_to_1_queue, data_2_to_3_queue)
        self.send_data(22221111, 1, flag_send_2_to_1, flag_send_2_to_3, data_2_to_1_queue, data_2_to_3_queue)
        self.send_data(Ni, 3, flag_send_2_to_1, flag_send_2_to_3, data_2_to_1_queue, data_2_to_3_queue)
        self.send_data(22223333, 3, flag_send_2_to_1, flag_send_2_to_3, data_2_to_1_queue, data_2_to_3_queue)
        while True:
            if flag_send_2_to_3.value == 0:
                break

    def receive_gg(self, q21):
        q21_list = []
        while True:
            while not q21.empty():
                q21_list.append(mpz(q21.get()))
                if q21_list:
                    if q21_list[-1] == 11112222:
                        break
            if q21_list:
                if q21_list[-1] == 11112222:
                    break
        ggt = q21_list[0]
        if gmpy2.jacobi(ggt, self.N) == 1:
            self.gg = ggt
        else:
            raise Exception("gg generation Error!")

    def receive_Q_list(self, q21, q23):
        q21_list = []
        q23_list = []
        while True:
            while not q21.empty():
                q21_list.append(mpz(q21.get()))
                if q21_list:
                    if q21_list[-1] == 11112222:
                        break
            if q21_list:
                if q21_list[-1] == 11112222:
                    break
        while True:
            while not q23.empty():
                q23_list.append(mpz(q23.get()))
                if q23_list:
                    if q23_list[-1] == 33332222:
                        break
            if q23_list:
                if q23_list[-1] == 33332222:
                    break
        return [q21_list[0], self.Q, q23_list[0]]

    def biprimality_check(self, flag_send_2_to_1, flag_send_2_to_3, data_2_to_1_queue, data_2_to_3_queue, q21, q23):
        self.receive_gg(q21)
        self.Q = gmpy2.powmod(self.gg, gmpy2.f_div(self.pi + self.qi, 4), self.N)

        self.send_data(self.Q, 1, flag_send_2_to_1, flag_send_2_to_3, data_2_to_1_queue, data_2_to_3_queue)
        self.send_data(22221111, 1, flag_send_2_to_1, flag_send_2_to_3, data_2_to_1_queue, data_2_to_3_queue)
        self.send_data(self.Q, 3, flag_send_2_to_1, flag_send_2_to_3, data_2_to_1_queue, data_2_to_3_queue)
        self.send_data(22223333, 3, flag_send_2_to_1, flag_send_2_to_3, data_2_to_1_queue, data_2_to_3_queue)
        while True:
            if flag_send_2_to_3.value == 0:
                break
        Q_list = self.receive_Q_list(q21, q23)
        # print("Q_list = ", Q_list)
        # print("Q_list = ", Q_list)

        Q1 = Q_list[0]
        Q2 = Q_list[1]
        Q3 = Q_list[2]
        Q2_inv = gmpy2.invert(Q2, self.N)
        Q3_inv = gmpy2.invert(Q3, self.N)

        biprimality_check = gmpy2.f_mod((Q1 * Q2_inv * Q3_inv), self.N) == gmpy2.f_mod(mpz(1), self.N) or gmpy2.f_mod(
            (Q1 * Q2_inv * Q3_inv), self.N) == gmpy2.f_mod(mpz(-1), self.N)
        return biprimality_check

    def start_sync(self, q21, q23):
        if self.PartyIndex == 1:
            self.send_data(99999999, 2, flag_send_2_to_1, flag_send_2_to_3, data_2_to_1_queue, data_2_to_3_queue)
            self.send_data(11112222, 2, flag_send_2_to_1, flag_send_2_to_3, data_2_to_1_queue, data_2_to_3_queue)
            self.send_data(99999999, 3, flag_send_2_to_1, flag_send_2_to_3, data_2_to_1_queue, data_2_to_3_queue)
            self.send_data(11113333, 3, flag_send_2_to_1, flag_send_2_to_3, data_2_to_1_queue, data_2_to_3_queue)
        elif self.PartyIndex == 2:
            self.send_data(99999999, 1, flag_send_2_to_1, flag_send_2_to_3, data_2_to_1_queue, data_2_to_3_queue)
            self.send_data(22221111, 1, flag_send_2_to_1, flag_send_2_to_3, data_2_to_1_queue, data_2_to_3_queue)
            self.send_data(99999999, 3, flag_send_2_to_1, flag_send_2_to_3, data_2_to_1_queue, data_2_to_3_queue)
            self.send_data(22223333, 3, flag_send_2_to_1, flag_send_2_to_3, data_2_to_1_queue, data_2_to_3_queue)
        elif self.PartyIndex == 3:
            self.send_data(99999999, 1, flag_send_2_to_1, flag_send_2_to_3, data_2_to_1_queue, data_2_to_3_queue)
            self.send_data(33331111, 1, flag_send_2_to_1, flag_send_2_to_3, data_2_to_1_queue, data_2_to_3_queue)
            self.send_data(99999999, 2, flag_send_2_to_1, flag_send_2_to_3, data_2_to_1_queue, data_2_to_3_queue)
            self.send_data(33332222, 2, flag_send_2_to_1, flag_send_2_to_3, data_2_to_1_queue, data_2_to_3_queue)
        else:
            raise Exception("PartyIndex Error!")

        while True:
            if flag_send_2_to_3.value == 0:
                break

        q21_list = []
        q23_list = []
        while True:
            while not q21.empty():
                q21_list.append(q21.get())
            if q21_list:
                if q21_list[-1] == 11112222:
                    break
        while True:
            while not q23.empty():
                q23_list.append(q23.get())
            if q23_list:
                if q23_list[-1] == 33332222:
                    break
        while True:
            if q21_list[0] == 99999999 and q23_list[0] == 99999999:
                break

    def distributed_RSA_modulus_generation(self, flag_send_2_to_1, flag_send_2_to_3, data_2_to_1_queue, data_2_to_3_queue, q21, q23):
        print("Distributed RSA modulus generation start")
        while True:
            self.pi = self.pick_pq()
            self.qi = self.pick_pq()
            # print("pick pq done")
            pq_tuple_list = self.compute_tuple()
            # print("send_pq_tuple_list = ", pq_tuple_list)
            # print("compute pq tuple done")
            self.send_pq_tuple_list(pq_tuple_list, flag_send_2_to_1, flag_send_2_to_3, data_2_to_1_queue, data_2_to_3_queue)
            # print("send pq tuple list done")
            received_pq_tuple_list = self.receive_pq_tuple_list(pq_tuple_list, q21, q23)
            # print("received_pq_tuple_list", received_pq_tuple_list)
            # print("receive pq tuple list done")
            self.share_verification(received_pq_tuple_list)
            Ni = self.compute_Ni(received_pq_tuple_list)
            # print("compute Ni done")
            self.send_Ni(Ni, flag_send_2_to_1, flag_send_2_to_3, data_2_to_1_queue, data_2_to_3_queue)
            # print("send Ni done")
            Ni_list = self.receive_Ni_list(Ni, q21, q23)
            # print("receive Ni list done")
            # print("Ni_list = ", Ni_list)
            self.N_verification(Ni_list)
            self.compute_N(Ni_list)
            # print("compute N done")
            if self.biprimality_check(flag_send_2_to_1, flag_send_2_to_3, data_2_to_1_queue, data_2_to_3_queue, q21, q23):
                break
            # print("biprimality check done")
            # self.start_sync(q21, q23)


if __name__ == "__main__":
    flag_send_2_to_1 = multiprocessing.Value('l', 0)
    flag_send_2_to_3 = multiprocessing.Value('l', 0)
    data_2_to_1_queue = multiprocessing.Queue()
    data_2_to_3_queue = multiprocessing.Queue()
    q21 = multiprocessing.Queue()
    q23 = multiprocessing.Queue()
    connect_flag_21 = multiprocessing.Value('h', 0)
    connect_flag_23 = multiprocessing.Value('h', 0)

    server_process = Process(target=server, args=(flag_send_2_to_1, flag_send_2_to_3, data_2_to_1_queue, data_2_to_3_queue, q21, q23, connect_flag_23))
    client_process = Process(target=client, args=(flag_send_2_to_1, flag_send_2_to_3, data_2_to_1_queue, data_2_to_3_queue, q21, q23, connect_flag_21))

    server_process.start()
    client_process.start()

    # wait for connection
    while True:
        if connect_flag_21.value and connect_flag_23.value:
            break

    # distributed Paillier key generation
    start = time.time()
    d_paillier = DPaillier(2)
    d_paillier.distributed_RSA_modulus_generation(flag_send_2_to_1, flag_send_2_to_3, data_2_to_1_queue, data_2_to_3_queue, q21, q23)
    stop = time.time()
    print("RSA modulus generation success")
    print("modulus = ", d_paillier.N)
    print("duration = ", stop - start, "seconds")



