import random
import time
import itertools
import matplotlib.pyplot as plt

RANDOM_SEED = 42 # счетчик псевдослучайных чисел
random.seed(RANDOM_SEED)

# Пример набора продуктов (N наименований).
# Для каждого продукта: (name, price, calories, protein, fat, carbs)
# Значения примерные — реалистичные приближённые (калории в ккал, белки/жиры/углеводы в г)
PRODUCTS = [
    ("Chicken Breast (100g)", 150, 165, 31, 3.6, 0),    # Куриная грудка
    ("Rice (100g)", 40, 130, 2.7, 0.3, 28),             # Рис
    ("Apple (100g)", 25, 52, 0.3, 0.2, 14),             # Яблоко
    ("Egg (1 pc ~50g)", 20, 78, 6.3, 5.3, 0.6),         # Яйцо
    ("Milk (200ml)", 60, 122, 6.6, 5, 12),              # Молоко
    ("Olive oil (10g)", 15, 88, 0, 10, 0),              # Оливковое масло
    ("Oatmeal (100g)", 50, 389, 16.9, 6.9, 66),         # Овсянка
    ("Beef (100g)", 250, 250, 26, 15, 0),               # Говядина
    ("Broccoli (100g)", 35, 34, 2.8, 0.4, 7),           # Брокколи
    ("Banana (100g)", 20, 89, 1.1, 0.3, 23),            # Банан
    ("Cheese (30g)", 60, 120, 7, 9, 1),                 # Сыр
    ("Yogurt (150g)", 55, 95, 5, 3.5, 11),              # Йогурт
    ("Almonds (30g)", 80, 170, 6, 15, 6),               # Миндаль
    ("Potato (150g)", 30, 116, 2.6, 0.1, 26),           # Картофель
    ("Salmon (100g)", 300, 208, 20, 13, 0),             # Лосось
]

N = len(PRODUCTS)
m = 4  # характеристики: calories, protein, fat, carbs

# Целевая норма суммарных характеристик рациона
TARGET = {
    "calories": 2000,
    "protein": 75,
    "fat": 70,
    "carbs": 260
}

# Бюджет: сумма цен должна быть в пределах [min_price, max_price]
MIN_BUDGET = 300.0
MAX_BUDGET = 1200.0

# Количество продуктов в рационе (ровно k штук)
K = 7

# ================ Параметры генетического алгоритма =================
POPULATION_SIZE = 200 # размер популяции
P_CROSSOVER = 0.9 # вероятность скрещивания
P_MUTATION = 0.2 # вероятность мутации
MAX_GENERATIONS = 80 # макс кол поколений итераций работы алгоритма ( для проверки условия остановки )

# ================ Структуры =================
class FitnessMin():
    def __init__(self):
        # fitness будет 1/(1+deviation) — больше лучше
        self.values = [0.0] # хранит значение приспособленности

class Individual(list):
    def __init__(self, *args):
        super().__init__(*args)
        self.fitness = FitnessMin()

# ================ Функции оценки: характеристики, цена, deviation =================
def get_item_features(index):
    _, price, calories, protein, fat, carbs = PRODUCTS[index]
    return price, (calories, protein, fat, carbs)

def evaluate_selected(indices):
    """Возвращает (total_price, totals_tuple) для набора индексов"""
    total_price = 0.0
    totals = [0.0]*m
    for i in indices:
        price, features = get_item_features(i)
        total_price += price
        for j in range(m):
            totals[j] += features[j]
    return total_price, tuple(totals)

def deviation_from_target(totals):
    """Возвращает суммарное квадратичное отклонение относительно TARGET (чем меньше — тем лучше)"""
    dev = 0.0
    dev += (totals[0] - TARGET["calories"])**2
    dev += (totals[1] - TARGET["protein"])**2
    dev += (totals[2] - TARGET["fat"])**2
    dev += (totals[3] - TARGET["carbs"])**2
    return dev

# ================ Создание индивидуумов и популяции =================
def individualCreator():
    """Создаём бинарный вектор длины N с ровно K единицами"""
    ones = set(random.sample(range(N), K))
    ind = Individual([1 if i in ones else 0 for i in range(N)])
    return ind

def populationCreator(n=0):
    return [individualCreator() for _ in range(n)]

# ================ Fitness-функция (приведение ошибки к метрике пригодности) =================
def evaluateIndividual(individual):
    indices = [i for i, g in enumerate(individual) if g == 1] # Индексы где стоит 1
    total_price, totals = evaluate_selected(indices)
    # если вне бюджетных рамок — применим штраф (сильно ухудшаем приспособленность)
    if total_price < MIN_BUDGET or total_price > MAX_BUDGET:
        penalty = 1e6 + abs(total_price - (MIN_BUDGET+MAX_BUDGET)/2)*1e3
        dev = deviation_from_target(totals) + penalty
    else:
        dev = deviation_from_target(totals)
    fitness_value = 1.0 / (1.0 + dev)  # преобразование в приспособленность - максимизируем
    return (fitness_value,)

# ================ Клонирование  =================
def clone(value):
    ind = Individual(value[:])
    ind.fitness.values[0] = value.fitness.values[0]
    return ind

# ================ Отбор — турнир  =================
def selTournament(population, p_len, tournsize=3):
    offspring = [] # потомство
    for _ in range(p_len):
        contestants = random.sample(population, tournsize)
        winner = max(contestants, key=lambda ind: ind.fitness.values[0])
        offspring.append(winner)
    return offspring

# ================ Операторы скрещивания  =================
def cxOnePoint(child1, child2):
    s = random.randint(1, N-1)
    child1[s:], child2[s:] = child2[s:], child1[s:]
    # после скрещивания возможное нарушение ровно K единиц — чинится в repair_operator

def cxTwoPoint(child1, child2):
    a = random.randint(1, N-2)
    b = random.randint(a+1, N-1)
    child1[a:b], child2[a:b] = child2[a:b], child1[a:b]

def cxUniform(child1, child2, indpb=0.5):
    for i in range(N):
        if random.random() < indpb:
            child1[i], child2[i] = child2[i], child1[i]

# ================ Операторы мутации  =================
# точечная мутация
def mutFlipBit(mutant, indpb=0.05):
    for i in range(N):
        if random.random() < indpb:
            mutant[i] = 0 if mutant[i] == 1 else 1
# обменная мутация
def mutSwap(mutant):
    ones = [i for i, v in enumerate(mutant) if v == 1]
    zeros = [i for i, v in enumerate(mutant) if v == 0]
    if ones and zeros:
        i = random.choice(ones)
        j = random.choice(zeros)
        mutant[i], mutant[j] = mutant[j], mutant[i]
# перемешивающая мутация
def mutScramble(mutant):
    # (после ремонта нужно восстановить K)
    a = random.randint(0, N-2)
    b = random.randint(a+1, N-1)
    segment = mutant[a:b]
    random.shuffle(segment)
    mutant[a:b] = segment

# ================ Repair (восстановление ровно K единиц) =================
def repair_to_k(ind):
    """Если единиц больше K — убираем случайные лишние; если меньше — добавляем случайные нули."""
    current = sum(ind)
    if current > K:
        # убираем случайные лишние единицы
        ones = [i for i, v in enumerate(ind) if v == 1]
        remove = random.sample(ones, int(current - K))
        for i in remove:
            ind[i] = 0
    elif current < K:
        zeros = [i for i, v in enumerate(ind) if v == 0]
        add = random.sample(zeros, int(K - current))
        for i in add:
            ind[i] = 1
    # если равны — ничего не делаем

# ================ Основной цикл GA с возможностью выбора операторов =================
def run_ga(crossover_operator, mutation_operator, run_name="run", verbose=False):
    # инициализация
    population = populationCreator(POPULATION_SIZE)
    generationCounter = 0

    # оценка начальной популяции
    fitnessValues = list(map(evaluateIndividual, population))
    for ind, fv in zip(population, fitnessValues):
        ind.fitness.values = fv

    maxFitnessValues = []
    meanFitnessValues = []

    # цикл поколений
    while generationCounter < MAX_GENERATIONS:
        generationCounter += 1

        # селекция
        offspring = selTournament(population, len(population))
        offspring = list(map(clone, offspring))

        # скрещивание
        for child1, child2 in zip(offspring[::2], offspring[1::2]):
            if random.random() < P_CROSSOVER:
                crossover_operator(child1, child2)
                # ремонт - чтобы сохранить ровно K единиц
                repair_to_k(child1)
                repair_to_k(child2)

        # мутация
        for mutant in offspring:
            if random.random() < P_MUTATION:
                if mutation_operator == mutFlipBit:
                    mutation_operator(mutant, indpb=1.0/N)
                else:
                    mutation_operator(mutant)
                repair_to_k(mutant)

        # оценка
        freshFitness = list(map(evaluateIndividual, offspring))
        for ind, fv in zip(offspring, freshFitness):
            ind.fitness.values = fv

        population[:] = offspring

        fitnessValues = [ind.fitness.values[0] for ind in population]
        maxFitness = max(fitnessValues)
        meanFitness = sum(fitnessValues) / len(population)
        maxFitnessValues.append(maxFitness)
        meanFitnessValues.append(meanFitness)

        if verbose:
            best_index = fitnessValues.index(maxFitness)
            best = population[best_index]
            print(f"{run_name} Поколение {generationCounter}: Макс = {maxFitness:.8f}, Ср = {meanFitness:.8f}")

        # ранняя остановка если нашли идеальное решение (допустим отклонение 0)
        if maxFitnessValues[-1] > 1.0/(1.0+0.0) - 1e-12: #0.999999999999
            break

    # вернём популяцию + метрики
    return {
        "population": population,
        "max_values": maxFitnessValues,
        "mean_values": meanFitnessValues,
        "generations": generationCounter
    }

# ================ Полный перебор (комбинации C(N,K)) =================
def exhaustive_search():
    best_dev = float("inf")
    best_combo = None
    combos_checked = 0
    start = time.time()
    for combo in itertools.combinations(range(N), K):
        combos_checked += 1
        total_price, totals = evaluate_selected(combo)
        # учитываем бюджет: если вне — пропускаем
        if total_price < MIN_BUDGET or total_price > MAX_BUDGET:
            continue
        dev = deviation_from_target(totals)
        if dev < best_dev:
            best_dev = dev
            best_combo = combo
    elapsed = time.time() - start
    return best_combo, best_dev, combos_checked, elapsed

# ================ Эксперименты: разные операторы =================
experiments = [
    ("Одноточечный кроссовер + побитовая мутация", cxOnePoint, mutFlipBit),
    ("Одноточечный кроссовер + обменная мутация", cxOnePoint, mutSwap),
    ("Двухточечный кроссовер + побитовая мутация", cxTwoPoint, mutFlipBit),
    ("Двухточечный кроссовер + перемешивающая мутация", cxTwoPoint, mutScramble),
    ("Равномерный кроссовер + обменная мутация", cxUniform, mutSwap),
    ("Равномерный кроссовер + перемешивающая мутация", cxUniform, mutScramble),
]


results = {}
start_all = time.time()
for name, cx_op, mut_op in experiments:
    print(f"\n=== Запуск эксперимента: {name} ===")
    res = run_ga(cx_op, mut_op, run_name=name, verbose=True)
    results[name] = res

end_all = time.time()

# ================ Вывод результатов: графики (макс каждого эксперимента) =================
plt.figure(figsize=(10, 6))
for name, data in results.items():
    plt.plot(data["max_values"], label=f"{name} max")
    plt.plot(data["mean_values"], label=f"{name} mean", linestyle="--")
plt.xlabel("Поколение")
plt.ylabel("Приспособленность")
plt.title("Сравнение экспериментов: макс и средняя приспособленность")
plt.legend(loc='best', fontsize='small')
plt.grid(True)
plt.show()

# ================ Подробный вывод лучшего найденного решения для каждого эксперимента =================
def print_solution_from_population(pop):
    fitnessValues = [ind.fitness.values[0] for ind in pop]
    best_index = fitnessValues.index(max(fitnessValues))
    best = pop[best_index]
    indices = [i for i, v in enumerate(best) if v == 1]
    total_price, totals = evaluate_selected(indices)
    dev = deviation_from_target(totals)
    print("Итоговая приспособленность:", best.fitness.values[0])
    print("Отклонение (сумма квадратов):", dev)
    print("Цена:", total_price)
    print("Выбранные продукты:")
    for i in indices:
        print("  -", PRODUCTS[i][0])
    return {
        "indices": indices,
        "price": total_price,
        "totals": totals,
        "dev": dev,
        "fitness": best.fitness.values[0]
    }

summary = {}
for name, data in results.items():
    print(f"\n--- Результат для {name} ---")
    summary[name] = print_solution_from_population(data["population"])

# ================ Полный перебор для сравнения  =================
print("\n=== Запуск полного перебора для сравнения ===")
combo, best_dev, combos_checked, elapsed = exhaustive_search()
if combo is None:
    print("Не найдено допустимых комбинаций в бюджетном диапазоне.")
else:
    total_price, totals = evaluate_selected(combo)
    print("Комбинация лучшая (перебор):")
    for i in combo:
        print("  -", PRODUCTS[i][0])
    print("Цена:", total_price)
    print("Отклонение (сумма квадратов):", best_dev)
print(f"Комбинаций проверено: {combos_checked}, время: {elapsed:.3f} сек")


