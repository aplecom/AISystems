import numpy as np
import matplotlib.pyplot as plt


def trapezoidal_membership(x, a, b, c, d):
    if x < a or x > d:
        return 0.0
    elif a <= x <= b:
        return (x - a) / (b - a)
    elif b < x < c:
        return 1.0
    elif c <= x <= d:
        return (d - x) / (d - c)

def fuzzy_complement(mu_values):
    return [1 - mu for mu in mu_values]

def main():
    # диапазон BMI
    x_values = np.linspace(10, 40, 200)

    print("Параметры трапециевидной функции принадлежности (a, b, c, d):")
    a = float(input("a = "))
    b = float(input("b = "))
    c = float(input("c = "))
    d = float(input("d = "))

    # Значение функции принадлежности ( нечеткое множество )
    mu_values = [trapezoidal_membership(x, a, b, c, d) for x in x_values]

    # Дополнение нечеткого множества
    complement_values = fuzzy_complement(mu_values)

    plt.figure(figsize=(10, 6))
    plt.plot(x_values, mu_values, label='Исходное нечеткое множество', color='blue')
    plt.plot(x_values, complement_values, label='Дополнение нечеткого множества', color='red', linestyle='--')
    plt.title("Дополнение нечеткого множества (трапециевидная функция)")
    plt.xlabel("BMI (индекс массы тела)")
    plt.ylabel("Степень принадлежности")
    plt.legend()
    plt.grid(True)
    plt.show()

if __name__ == "__main__":
    main()
