import time
import math


def is_prime(n):
    for i in range(2, math.floor(math.sqrt(n))):
        if n % i == 0:
            return False
    return True


def find_max_prime(timeout):
    max_prime = i = 1
    start = time.time()
    while time.time() - start < timeout:
        if is_prime(i) and i > max_prime:
            max_prime = i
        i += 1
    print(max_prime)


if __name__ == '__main__':
    find_max_prime(5)
