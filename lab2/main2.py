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
    """Операция дополнения нечеткого множества"""
    return [1 - mu for mu in mu_values]

def main():
    x_values = np.linspace(10, 40, 400)

    #  параметры для каждой категории
    categories = {
        "Недостаточный вес": (10, 11, 17, 18.5),
        "Нормальный вес": (18.5, 19, 24, 25),
        "Избыточный вес": (25, 25, 29, 30),
        "Ожирение": (30, 31, 37, 40)
    }

    plt.figure(figsize=(12, 6))

    #  функции принадлежности
    for label, (a, b, c, d) in categories.items():
        mu_values = [trapezoidal_membership(x, a, b, c, d) for x in x_values]
        plt.plot(x_values, mu_values, linewidth=2, label=label)

    plt.title("Функции принадлежности для категорий BMI")
    plt.xlabel("BMI (индекс массы тела)")
    plt.ylabel("Степень принадлежности")
    plt.grid(True)
    plt.legend()
    plt.show()

    #  операция дополнения для "нормального веса"
    a, b, c, d = categories["Нормальный вес"]
    mu_values = [trapezoidal_membership(x, a, b, c, d) for x in x_values]
    complement_values = fuzzy_complement(mu_values)

    plt.figure(figsize=(12, 6))
    plt.plot(x_values, mu_values, label='Нормальный вес', color='blue', linewidth=2)
    plt.plot(x_values, complement_values, label='Дополнение (не нормальный вес)', color='red', linestyle='--', linewidth=2)
    plt.title("Операция дополнения нечеткого множества (пример для нормального веса)")
    plt.xlabel("BMI (индекс массы тела)")
    plt.ylabel("Степень принадлежности")
    plt.legend()
    plt.grid(True)
    plt.show()

if __name__ == "__main__":
    main()
