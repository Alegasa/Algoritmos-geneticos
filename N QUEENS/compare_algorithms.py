import time
import random
import array
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# DEAP imports
from deap import base, creator, tools, algorithms

# --- 1. CLASE DEL PROBLEMA (El Árbitro Común) ---
class NQueensProblem:
    def __init__(self, numOfQueens):
        self.numOfQueens = numOfQueens

    def getViolationsCount(self, positions):
        # Misma función de fitness para ambos para ser justos
        violations = 0
        for i in range(len(positions)):
            for j in range(i + 1, len(positions)):
                column1 = i
                row1 = positions[i]
                column2 = j
                row2 = positions[j]
                if abs(column1 - column2) == abs(row1 - row2):
                    violations += 1
        return violations

# --- 2. SOLVER GENÉTICO (DEAP) ---
def run_genetic_algorithm(n_queens, pop_size, max_gen, seed=42):
    random.seed(seed)
    
    # Configuración DEAP (recreada localmente para evitar errores globales)
    if hasattr(creator, "FitnessMin"): del creator.FitnessMin
    if hasattr(creator, "Individual"): del creator.Individual
    
    creator.create("FitnessMin", base.Fitness, weights=(-1.0,))
    creator.create("Individual", array.array, typecode='i', fitness=creator.FitnessMin)
    
    toolbox = base.Toolbox()
    problem = NQueensProblem(n_queens)
    
    toolbox.register("randomOrder", random.sample, range(n_queens), n_queens)
    toolbox.register("individualCreator", tools.initIterate, creator.Individual, toolbox.randomOrder)
    toolbox.register("populationCreator", tools.initRepeat, list, toolbox.individualCreator)
    
    def evalQueens(individual):
        return problem.getViolationsCount(individual),

    toolbox.register("evaluate", evalQueens)
    toolbox.register("select", tools.selTournament, tournsize=2)
    toolbox.register("mate", tools.cxUniformPartialyMatched, indpb=2.0/n_queens)
    toolbox.register("mutate", tools.mutShuffleIndexes, indpb=1.0/n_queens)

    pop = toolbox.populationCreator(n=pop_size)
    stats = tools.Statistics(lambda ind: ind.fitness.values)
    stats.register("min", np.min)
    
    # Ejecución
    start_time = time.time()
    pop, logbook = algorithms.eaSimple(pop, toolbox, cxpb=0.9, mutpb=0.1, ngen=max_gen, stats=stats, verbose=False)
    end_time = time.time()
    
    best_ind = tools.selBest(pop, 1)[0]
    min_history = logbook.select("min")
    
    return {
        "name": "Genético (DEAP)",
        "best_fitness": best_ind.fitness.values[0],
        "time": end_time - start_time,
        "history": min_history,
        "best_sol": best_ind
    }

# --- 3. SOLVER LUCIÉRNAGA (Firefly) ---
class FireflyAlgorithm:
    def __init__(self, n_queens, pop_size, gamma=1.0):
        self.n_queens = n_queens
        self.pop_size = pop_size
        self.gamma = gamma
        self.problem = NQueensProblem(n_queens)
        self.population = []
        self.fitnesses = []

    def run(self, max_generations, seed=42):
        random.seed(seed)
        self.population = [random.sample(range(self.n_queens), self.n_queens) for _ in range(self.pop_size)]
        self.fitnesses = [self.problem.getViolationsCount(ind) for ind in self.population]
        
        history = []
        start_time = time.time()
        
        for t in range(max_generations):
            # Guardar mejor de esta generación para el historial
            history.append(min(self.fitnesses))
            
            for i in range(self.pop_size):
                for j in range(self.pop_size):
                    if self.fitnesses[j] < self.fitnesses[i]:
                        # Calcular movimiento
                        dist = np.sum([1 for k in range(self.n_queens) if self.population[i][k] != self.population[j][k]])
                        beta = 1.0 * np.exp(-self.gamma * (dist ** 2))
                        
                        if random.random() < beta:
                            # Mover i hacia j (Swap simple basado en distancia)
                            # Nota: Simplificado para asegurar permutación válida
                            new_pos = list(self.population[i])
                            swaps = int(dist * 0.1) + 1
                            for _ in range(swaps):
                                idx1, idx2 = random.sample(range(self.n_queens), 2)
                                new_pos[idx1], new_pos[idx2] = new_pos[idx2], new_pos[idx1]
                            
                            new_fitness = self.problem.getViolationsCount(new_pos)
                            # Aceptamos si mejora (o comportamiento estándar Firefly)
                            self.population[i] = new_pos
                            self.fitnesses[i] = new_fitness

        end_time = time.time()
        best_idx = np.argmin(self.fitnesses)
        
        return {
            "name": "Luciérnaga (Firefly)",
            "best_fitness": self.fitnesses[best_idx],
            "time": end_time - start_time,
            "history": history,
            "best_sol": self.population[best_idx]
        }

# --- 4. COMPARACIÓN PRINCIPAL ---
if __name__ == "__main__":
    # PARÁMETROS COMUNES
    N_QUEENS = 16
    POPULATION = 60   # Mismo tamaño para ambos
    GENERATIONS = 60# ismas iteraciones
    
    print(f"--- COMPARANDO ALGORITMOS (N={N_QUEENS}) ---")
    
    # 1. Correr Genético
    print("Ejecutando Genético...")
    res_ga = run_genetic_algorithm(N_QUEENS, POPULATION, GENERATIONS)
    
    # 2. Correr Luciérnaga
    print("Ejecutando Luciérnaga...")
    solver_fa = FireflyAlgorithm(N_QUEENS, POPULATION)
    res_fa = solver_fa.run(GENERATIONS)
    
    # 3. Mostrar Resultados Numéricos
    print("\n--- RESULTADOS ---")
    print(f"{'Algoritmo':<20} | {'Tiempo (s)':<10} | {'Mejor Fitness':<15} | {'Éxito?'}")
    print("-" * 60)
    
    for res in [res_ga, res_fa]:
        success = "SÍ" if res['best_fitness'] == 0 else "NO"
        print(f"{res['name']:<20} | {res['time']:.4f}     | {res['best_fitness']:<15} | {success}")

    # 4. Gráfica de Convergencia
    plt.figure(figsize=(10, 6))
    plt.plot(res_ga['history'], label='Genético (DEAP)', color='blue', linewidth=2)
    plt.plot(res_fa['history'], label='Luciérnaga (Firefly)', color='orange', linewidth=2, linestyle='--')
    
    plt.title(f'Comparación de Convergencia (N={N_QUEENS})')
    plt.xlabel('Generación')
    plt.ylabel('Violaciones (Fitness)')
    plt.legend()
    plt.grid(True)
    plt.show()

