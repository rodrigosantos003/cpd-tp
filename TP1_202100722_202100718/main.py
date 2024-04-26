import math
import multiprocessing
import time


def is_prime(n):
    if n <= 1:
        return False
    if n == 2 or n == 3:
        return True
    if n % 2 == 0:
        return False
    for i in range(3, int(math.sqrt(n)) + 1, 2):
        if n % i == 0:
            return False
    return True


def find_max_prime(timeout, shared_max_prime, lock, value, step):
    start_time = time.time()

    while time.time() - start_time < timeout:
        if value > shared_max_prime.value:
            if is_prime(value):
                with lock:
                    shared_max_prime.value = value
        else:
            value = shared_max_prime.value

        value += step


if __name__ == '__main__':
    with multiprocessing.Manager() as manager:
        max_prime = manager.Value('i', 1)
        lock = manager.Lock()
        num_processes = 8

        processes = []

        for x in range(num_processes):
            step = 100 ** x
            start_value = max_prime.value + x * step

            p = multiprocessing.Process(target=find_max_prime, args=[30, max_prime, lock, start_value, step])
            processes.append(p)
            p.start()

        for p in processes:
            p.join()

        print(max_prime.value, "(", len(str(max_prime.value)), ")")
