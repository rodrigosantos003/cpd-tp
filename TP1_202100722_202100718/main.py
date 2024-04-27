import math
import multiprocessing
import time


def is_prime(n):
    """
    Check if a number is prime, using trial division.
    :param n: Number to check
    :return: True if the number is prime, False otherwise
    """
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
    """
    Find the maximum prime number in a given range.
    :param timeout: Time limit for the worker
    :param shared_max_prime: Maximum prime number found so far
    :param lock: Lock to access the shared maximum prime number
    :param value: Value to search
    :param step: Value to increment the search
    :return: None
    """
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
        # Max prime number
        max_prime = manager.Value('i', 1)

        # Lock to access the shared maximum prime number
        smp_lock = manager.Lock()

        # Number of processes
        num_processes = 8

        # Timeout for each worker
        worker_timeout = 30

        # Multiprocessing pool
        with multiprocessing.Pool(num_processes) as pool:
            pool.starmap(find_max_prime,
                         [(worker_timeout,
                           max_prime,
                           smp_lock,
                           (1 + x * (100 ** x)),  # Start value
                           (100 ** x))  # Step
                          for x in range(num_processes)])

        # Print the maximum prime number found
        print(max_prime.value, "(", len(str(max_prime.value)), ")")
