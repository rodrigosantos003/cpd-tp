import time
import math


def is_prime(n):
    stop = math.floor(math.sqrt(n))
    for i in primes:
        if i > stop:
            return True
        if n % i == 0:
            return False
    return True


# primos até ao que escolhemos (neste caso 7)
primes = [2, 3, 5, 7]


def find_max_prime(timeout):
    primes_jumps = [2, 4, 2, 4, 6, 2, 6, 4, 2, 4, 6, 6, 2, 6, 4, 2, 6, 4, 6, 8, 4, 2, 4, 2, 4, 8, 6, 4, 6, 2, 4,
                    6, 2, 6, 6, 4, 2, 4, 6, 2, 6, 4, 2, 4, 2, 10, 2, 10]

    selected_jump = 0

    # max_prime tem que ser o primo a seguir ao que escolhemos
    # (visto que queremos começar com um primo para que a sequencia de saltos funcione)
    max_prime = i = 11

    start = time.time()

    while time.time() - start < timeout:
        if is_prime(i):
            max_prime = i
            primes.append(i)

        i += primes_jumps[selected_jump]
        selected_jump = (selected_jump + 1) % len(primes_jumps)

    print(max_prime)


if __name__ == '__main__':
    find_max_prime(5)
