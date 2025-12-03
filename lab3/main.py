from neo4j import GraphDatabase
import random
import time
import numpy as np


# --- Модуль нечеткой логики ---
class FuzzyLogic:
    @staticmethod
    def triangular_mf(x, a, b, c):
        """Треугольная функция принадлежности"""
        return max(0, min((x - a) / (b - a), (c - x) / (c - b)) if b != a and c != b else 0)

    @staticmethod
    def trapezoidal_mf(x, a, b, c, d):
        """Трапециевидная функция принадлежности"""
        return max(0, min((x - a) / (b - a), 1, (d - x) / (d - c)) if b != a and d != c else 0)

    @staticmethod
    def fuzzify_temperature(temp):
        """Фаззификация температуры"""
        cold = FuzzyLogic.triangular_mf(temp, 0, 20, 40)
        warm = FuzzyLogic.triangular_mf(temp, 30, 50, 70)
        hot = FuzzyLogic.triangular_mf(temp, 60, 80, 100)
        return {'cold': cold, 'warm': warm, 'hot': hot}

    @staticmethod
    def fuzzify_cooking_progress(progress):
        """Фаззификация прогресса готовки"""
        start = FuzzyLogic.triangular_mf(progress, 0, 0, 30)
        middle = FuzzyLogic.triangular_mf(progress, 20, 50, 80)
        end = FuzzyLogic.triangular_mf(progress, 70, 100, 100)
        return {'start': start, 'middle': middle, 'end': end}

    @staticmethod
    def fuzzify_ingredient_amount(amount):
        """Фаззификация количества ингредиентов"""
        low = FuzzyLogic.triangular_mf(amount, 0, 0, 50)
        medium = FuzzyLogic.triangular_mf(amount, 30, 60, 90)
        high = FuzzyLogic.triangular_mf(amount, 70, 100, 100)
        return {'low': low, 'medium': medium, 'high': high}

    @staticmethod
    def defuzzify_heat_power(rules_output):
        """Дефаззификация мощности нагрева (центроидный метод)"""
        # Определяем выходные функции для мощности нагрева
        x = np.linspace(0, 100, 100)
        y = np.zeros_like(x, dtype=float)

        # Применяем правила (макс-мин композиция)
        for i, xi in enumerate(x):
            member_values = []

            # Правило 1: Если холодно И начало -> высокая мощность
            if 'cold_high' in rules_output:
                cold_high = min(rules_output.get('cold', 0), rules_output.get('start', 0))
                member_val = FuzzyLogic.triangular_mf(xi, 70, 85, 100)  # Высокая мощность
                member_values.append(min(cold_high, member_val))

            # Правило 2: Если тепло И середина -> средняя мощность
            if 'warm_medium' in rules_output:
                warm_medium = min(rules_output.get('warm', 0), rules_output.get('middle', 0))
                member_val = FuzzyLogic.triangular_mf(xi, 40, 60, 80)  # Средняя мощность
                member_values.append(min(warm_medium, member_val))

            # Правило 3: Если горячо И конец -> низкая мощность
            if 'hot_low' in rules_output:
                hot_low = min(rules_output.get('hot', 0), rules_output.get('end', 0))
                member_val = FuzzyLogic.triangular_mf(xi, 0, 15, 30)  # Низкая мощность
                member_values.append(min(hot_low, member_val))

            if member_values:
                y[i] = max(member_values)

        # Центроидный метод дефаззификации
        if np.sum(y) == 0:
            return 50  # Значение по умолчанию

        return np.sum(x * y) / np.sum(y)


# --- Подключение к Neo4j ---
class Neo4jDB:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def setup_kitchen_ontology(self):

        with self.driver.session() as session:
            # Очистка базы
            session.run("MATCH (n) DETACH DELETE n")

            # Создание основных классов онтологии
            session.run("""
            CREATE (:Class {name: 'Рецепт'})
            CREATE (:Class {name: 'Ингредиент'})
            CREATE (:Class {name: 'КухонныйПрибор'})
            CREATE (:Class {name: 'Действие'})
            CREATE (:Class {name: 'Условие'})
            CREATE (:Class {name: 'НечеткоеПравило'})
            """)

            # Создание конкретных экземпляров
            session.run("""
            CREATE (суп:Рецепт {name: 'Суп', время_приготовления: 20})
            CREATE (макароны:Рецепт {name: 'Макароны', время_приготовления: 12})
            CREATE (омлет:Рецепт {name: 'Омлет', время_приготовления: 10})
            CREATE (рис:Рецепт {name: 'Рис', время_приготовления: 18})

            CREATE (вода:Ингредиент {name: 'Вода', количество: '1.5л'})
            CREATE (овощи:Ингредиент {name: 'Овощи', количество: '300г'})
            CREATE (картофель:Ингредиент {name: 'Картофель', количество: '200г'})
            CREATE (специи:Ингредиент {name: 'Специи', количество: 'по вкусу'})
            CREATE (макароны_инг:Ингредиент {name: 'Макароны', количество: '200г'})
            CREATE (яйца:Ингредиент {name: 'Яйца', количество: '3шт'})
            CREATE (рис_инг:Ингредиент {name: 'Рис', количество: '150г'})

            CREATE (плита:КухонныйПрибор {name: 'Плита', состояние: 'выключена', мощность: 0})
            CREATE (сковорода:КухонныйПрибор {name: 'Сковорода', состояние: 'не используется', температура: 0})
            CREATE (кастрюля:КухонныйПрибор {name: 'Кастрюля', состояние: 'не используется', температура: 0})
            """)

            # Создание связей между рецептами и ингредиентами
            session.run("""
            MATCH (суп:Рецепт {name: 'Суп'})
            MATCH (вода:Ингредиент {name: 'Вода'})
            MATCH (овощи:Ингредиент {name: 'Овощи'})
            MATCH (картофель:Ингредиент {name: 'Картофель'})
            MATCH (специи:Ингредиент {name: 'Специи'})
            CREATE (суп)-[:ТРЕБУЕТ_ИНГРЕДИЕНТ]->(вода)
            CREATE (суп)-[:ТРЕБУЕТ_ИНГРЕДИЕНТ]->(овощи)
            CREATE (суп)-[:ТРЕБУЕТ_ИНГРЕДИЕНТ]->(картофель)
            CREATE (суп)-[:ТРЕБУЕТ_ИНГРЕДИЕНТ]->(специи)
            """)

            # Добавление нечетких правил
            session.run("""
            CREATE (правило1:НечеткоеПравило {
                название: 'Регулировка нагрева по температуре',
                условие: 'температура И прогресс',
                действие: 'мощность нагрева',
                тип: 'нечеткое'
            })
            """)

    def add_cooking_rules(self):
        """Добавление правил приготовления в онтологию"""
        with self.driver.session() as session:
            # Правила для супа с нечеткой логикой
            soup_rules = [
                {"time": 1, "condition": "Начать приготовление", "action": "Включить плиту",
                 "message": "🔥 Плита включена, вода начинает нагреваться", "fuzzy_power": 80},
                {"time": 3, "condition": "Вода нагрета", "action": "Добавить овощи",
                 "message": "🥕 Овощи добавлены в суп", "fuzzy_power": 70},
                {"time": 5, "condition": "Овощи готовятся", "action": "Добавить картофель",
                 "message": "🥔 Картофель добавлен в суп", "fuzzy_power": 65},
                {"time": 8, "condition": "Картофель готовится", "action": "Добавить специи",
                 "message": "🧂 Специи добавлены", "fuzzy_power": 60},
                {"time": 12, "condition": "Ингредиенты готовы", "action": "Перемешать",
                 "message": "🥄 Суп перемешан", "fuzzy_power": 55},
                {"time": 15, "condition": "Суп кипит", "action": "Убавить огонь",
                 "message": "♨️ Огонь уменьшен для томления", "fuzzy_power": 40},
                {"time": 18, "condition": "Суп готовится", "action": "Проверить густоту",
                 "message": "💧 Проверка густоты супа", "fuzzy_power": 35},
                {"time": 20, "condition": "Приготовление завершено", "action": "Выключить плиту",
                 "message": "✅ Суп готов! Подавать к столу", "fuzzy_power": 0}
            ]

            for rule in soup_rules:
                session.run("""
                MATCH (рецепт:Рецепт {name: 'Суп'})
                CREATE (правило:Правило {
                    время: $time,
                    условие: $condition,
                    действие: $action,
                    сообщение: $message,
                    нечеткая_мощность: $fuzzy_power
                })
                CREATE (рецепт)-[:ИМЕЕТ_ПРАВИЛО]->(правило)
                """, time=rule["time"], condition=rule["condition"],
                            action=rule["action"], message=rule["message"],
                            fuzzy_power=rule["fuzzy_power"])

    def get_recipe_steps(self, recipe_name):
        """Получение шагов рецепта из базы знаний"""
        with self.driver.session() as session:
            result = session.run("""
            MATCH (р:Рецепт {name: $name})-[:ИМЕЕТ_ПРАВИЛО]->(п:Правило)
            RETURN п.время as time, п.условие as condition, 
                   п.действие as action, п.сообщение as message,
                   п.нечеткая_мощность as fuzzy_power
            ORDER BY п.время
            """, name=recipe_name)

            steps = []
            for record in result:
                steps.append({
                    "time": record["time"],
                    "condition": record["condition"],
                    "action": record["action"],
                    "message": record["message"],
                    "fuzzy_power": record["fuzzy_power"] if record["fuzzy_power"] else 50
                })

            if not steps:
                steps = self._get_local_recipe_steps(recipe_name)

            return steps

    def _get_local_recipe_steps(self, recipe_name):
        """Локальные рецепты (резервный вариант)"""
        recipes_db = {
            "Суп": [
                {"time": 1, "condition": "Начать приготовление", "action": "Включить плиту",
                 "message": "🔥 Плита включена, вода начинает нагреваться", "fuzzy_power": 80},
                {"time": 3, "condition": "Вода нагрета", "action": "Добавить овощи",
                 "message": "🥕 Овощи добавлены в суп", "fuzzy_power": 70},
                {"time": 5, "condition": "Овощи готовятся", "action": "Добавить картофель",
                 "message": "🥔 Картофель добавлен в суп", "fuzzy_power": 65},
                {"time": 8, "condition": "Картофель готовится", "action": "Добавить специи",
                 "message": "🧂 Специи добавлены", "fuzzy_power": 60},
                {"time": 12, "condition": "Ингредиенты готовы", "action": "Перемешать",
                 "message": "🥄 Суп перемешан", "fuzzy_power": 55},
                {"time": 15, "condition": "Суп кипит", "action": "Убавить огонь",
                 "message": "♨️ Огонь уменьшен для томления", "fuzzy_power": 40},
                {"time": 18, "condition": "Суп готовится", "action": "Проверить густоту",
                 "message": "💧 Проверка густоты супа", "fuzzy_power": 35},
                {"time": 20, "condition": "Приготовление завершено", "action": "Выключить плиту",
                 "message": "✅ Суп готов! Подавать к столу", "fuzzy_power": 0}
            ]
        }
        return recipes_db.get(recipe_name, [])

    def update_appliance_state(self, appliance_name, state, power=None, temperature=None):
        """Обновление состояния кухонного прибора"""
        with self.driver.session() as session:
            if power is not None:
                session.run("""
                MATCH (a:КухонныйПрибор {name: $name})
                SET a.состояние = $state, a.мощность = $power
                """, name=appliance_name, state=state, power=power)
            elif temperature is not None:
                session.run("""
                MATCH (a:КухонныйПрибор {name: $name})
                SET a.состояние = $state, a.температура = $temperature
                """, name=appliance_name, state=state, temperature=temperature)


# --- Симулятор умной кухни с нечеткой логикой ---
class SmartKitchenSimulator:
    def __init__(self, db, recipe_name):
        self.db = db
        self.recipe_name = recipe_name
        self.recipe = self.db.get_recipe_steps(recipe_name)
        self.time_elapsed = 0
        self.step_index = 0
        self.fuzzy_logic = FuzzyLogic()
        self.current_temperature = 20  # Начальная температура
        self.current_power = 0

    def run(self):
        if not self.recipe:
            print(f"❌ Рецепт '{self.recipe_name}' не найден")
            return

        print(f"\n=== Умная кухня с нечеткой логикой: Приготовление {self.recipe_name} ===")

        self.show_ingredients()

        while self.step_index < len(self.recipe):
            self.time_elapsed += 1
            current_step = self.recipe[self.step_index]

            if self.time_elapsed == current_step["time"]:
                # Применяем нечеткую логику для определения мощности
                fuzzy_power = self.apply_fuzzy_logic(current_step)

                print(f"[{self.time_elapsed} мин] Условие: {current_step['condition']}")
                print(f"          Действие: {current_step['action']}")
                print(f"          Мощность нагрева: {fuzzy_power:.1f}% (нечеткая логика)")
                print(f"          {current_step['message']}")

                self.step_index += 1
                self.log_step_to_neo4j(current_step, fuzzy_power)

                # Обновляем состояние прибора
                self.db.update_appliance_state("Плита", "включена", fuzzy_power)
            else:
                # Симуляция изменения температуры на основе текущей мощности
                self.simulate_temperature_change()
                progress = (self.time_elapsed / self.recipe[-1]["time"]) * 100
                print(f"[{self.time_elapsed} мин] ... процесс готовки идет ... "
                      f"(Температура: {self.current_temperature:.1f}°C, Прогресс: {progress:.1f}%)")

            time.sleep(0.5)

        print(f"\n✅ {self.recipe_name} готов! Приятного аппетита!")
        self.log_completion_to_neo4j()

    def apply_fuzzy_logic(self, step):
        """Применение нечеткой логики для определения мощности нагрева"""
        # Фаззификация входных параметров
        progress = (self.time_elapsed / self.recipe[-1]["time"]) * 100

        temp_fuzzy = self.fuzzy_logic.fuzzify_temperature(self.current_temperature)
        progress_fuzzy = self.fuzzy_logic.fuzzify_cooking_progress(progress)

        # Формирование правил нечеткого вывода
        rules_output = {}

        # Правило 1: Если холодно И начало -> высокая мощность
        if temp_fuzzy['cold'] > 0 and progress_fuzzy['start'] > 0:
            rules_output['cold_high'] = min(temp_fuzzy['cold'], progress_fuzzy['start'])

        # Правило 2: Если тепло И середина -> средняя мощность
        if temp_fuzzy['warm'] > 0 and progress_fuzzy['middle'] > 0:
            rules_output['warm_medium'] = min(temp_fuzzy['warm'], progress_fuzzy['middle'])

        # Правило 3: Если горячо И конец -> низкая мощность
        if temp_fuzzy['hot'] > 0 and progress_fuzzy['end'] > 0:
            rules_output['hot_low'] = min(temp_fuzzy['hot'], progress_fuzzy['end'])

        # Дефаззификация
        fuzzy_power = self.fuzzy_logic.defuzzify_heat_power(rules_output)

        # Комбинируем с эталонной мощностью из базы знаний
        base_power = step.get("fuzzy_power", 50)
        combined_power = (fuzzy_power + base_power) / 2

        self.current_power = combined_power
        return combined_power

    def simulate_temperature_change(self):
        """Симуляция изменения температуры на основе мощности"""
        if self.current_power > 0:
            # Температура увеличивается пропорционально мощности
            temp_increase = self.current_power * 0.1
            self.current_temperature += temp_increase
        else:
            # Естественное охлаждение
            self.current_temperature -= 0.5

        # Ограничения температуры
        self.current_temperature = max(20, min(100, self.current_temperature))

    def show_ingredients(self):
        """Показать необходимые ингредиенты из базы знаний"""
        with self.db.driver.session() as session:
            result = session.run("""
            MATCH (р:Рецепт {name: $name})-[:ТРЕБУЕТ_ИНГРЕДИЕНТ]->(и:Ингредиент)
            RETURN и.name as name, и.количество as quantity
            """, name=self.recipe_name)

            print("Необходимые ингредиенты:")
            ingredients_found = False
            for record in result:
                print(f"  - {record['name']}: {record['quantity']}")
                ingredients_found = True

            if not ingredients_found:
                print("  (ингредиенты не найдены в базе знаний)")

    def log_step_to_neo4j(self, step, fuzzy_power):
        """Логирование выполненного шага в Neo4j"""
        try:
            with self.db.driver.session() as session:
                session.run("""
                CREATE (л:Лог {
                    рецепт: $recipe,
                    время: $time,
                    действие: $action,
                    сообщение: $message,
                    нечеткая_мощность: $fuzzy_power,
                    температура: $temperature,
                    timestamp: timestamp()
                })
                """, recipe=self.recipe_name, time=self.time_elapsed,
                            action=step["action"], message=step["message"],
                            fuzzy_power=fuzzy_power, temperature=self.current_temperature)
        except Exception as e:
            print(f"⚠️ Ошибка логирования: {e}")

    def log_completion_to_neo4j(self):
        """Логирование завершения приготовления"""
        try:
            with self.db.driver.session() as session:
                session.run("""
                CREATE (з:Завершение {
                    рецепт: $recipe,
                    общее_время: $total_time,
                    статус: 'успешно',
                    timestamp: timestamp()
                })
                """, recipe=self.recipe_name, total_time=self.time_elapsed)
        except Exception as e:
            print(f"⚠️ Ошибка логирования завершения: {e}")


# --- Основной запуск ---
if __name__ == "__main__":
    # Инициализация базы данных
    db = Neo4jDB("bolt://localhost:7687", "neo4j", "gjcnhtkznm")

    try:
        # Настройка онтологии
        print("Настройка онтологии умной кухни в Neo4j...")
        db.setup_kitchen_ontology()
        db.add_cooking_rules()
        print("✅ Онтология создана!")

        # Выбор рецепта
        available_recipes = ["Суп", "Макароны"]
        print(f"\nДоступные рецепты: {', '.join(available_recipes)}")

        choice = input("Выберите рецепт: ").strip().capitalize()

        if choice in available_recipes:
            # Запуск симулятора с нечеткой логикой
            simulator = SmartKitchenSimulator(db, choice)
            simulator.run()

            # Показать историю приготовления из Neo4j
            print(f"\n📊 История приготовления '{choice}' (с нечеткой логикой):")
            with db.driver.session() as session:
                result = session.run("""
                MATCH (л:Лог)
                WHERE л.рецепт = $recipe
                RETURN л.время as time, л.действие as action, 
                       л.сообщение as message, л.нечеткая_мощность as power,
                       л.температура as temperature
                ORDER BY л.время
                """, recipe=choice)

                logs_found = False
                for record in result:
                    print(f"  {record['time']} мин: {record['action']} - "
                          f"Мощность: {record['power']:.1f}% - "
                          f"Температура: {record['temperature']:.1f}°C")
                    logs_found = True

                if not logs_found:
                    print("  (история не найдена)")

        else:
            print("❌ Рецепт не найден в базе знаний")

    except Exception as e:
        print(f"❌ Ошибка: {e}")
        print("Проверьте подключение к Neo4j и правильность пароля")

    finally:
        db.close()