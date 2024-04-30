import math
import multiprocessing
import time


def is_prime(n):
    """
    Check if a number is prime, using the form 6k+-1.
    :param n: Number to check
    :return: True if the number is prime, False otherwise
    """
    if n <= 1:
        return False
    elif n <= 3:
        return True
    elif n % 2 == 0 or n % 3 == 0:
        return False
    i = 5
    while i * i <= int(math.sqrt(n)):
        if n % i == 0 or n % (i + 2) == 0:
            return False
        i += 6
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
        worker_timeout = 60

        # Multiprocessing pool
        with multiprocessing.Pool(num_processes) as pool:
            pool.starmap(find_max_prime,
                         [(worker_timeout,
                           max_prime,
                           smp_lock,
                           (1 + p * (100 ** p)),  # Start value
                           (100 ** p))  # Step
                          for p in range(num_processes)])

        # Print the maximum prime number found
        print(f"{max_prime.value} ({len(str(max_prime.value))})")
