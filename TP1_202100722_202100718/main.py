import multiprocessing
import time


def is_prime(n):
    if n <= 1:
        return False
    elif n <= 3:
        return True
    elif n % 2 == 0 or n % 3 == 0:
        return False
    i = 5
    while i * i <= n:
        if n % i == 0 or n % (i + 2) == 0:
            return False
        i += 6
    return True


def find_max_prime(timeout, shared_max_prime, value):
    start_time = time.time()

    while time.time() - start_time < timeout:
        if is_prime(value):
            with shared_max_prime.get_lock():
                if value > shared_max_prime.value:
                    shared_max_prime.value = value
                else:
                    value = shared_max_prime.value

        value += 2


if __name__ == '__main__':
    max_prime = multiprocessing.Value('i', 2)

    processes = []

    for x in range(4):
        p = multiprocessing.Process(target=find_max_prime, args=[5, max_prime, (10 ** (x + 7) + 1)])
        processes.append(p)
        p.start()

    for p in processes:
        p.join()

    print(max_prime.value, "(", len(str(max_prime.value)), ")")
