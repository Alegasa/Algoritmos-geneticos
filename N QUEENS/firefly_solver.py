import random
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
import time

class NQueensProblem:
    def __init__(self, numOfQueens):
        self.numOfQueens = numOfQueens

    def getViolationsCount(self, positions):
        """Calcula el número de choques entre reinas (Fitness)."""
        if len(positions) != self.numOfQueens:
            raise ValueError("El tamaño de la lista debe ser igual a ", self.numOfQueens)

        violations = 0
        for i in range(len(positions)):
            for j in range(i + 1, len(positions)):
                # i, j son las columnas. positions[i], positions[j] son las filas.
                column1 = i
                row1 = positions[i]
                column2 = j
                row2 = positions[j]

                if abs(column1 - column2) == abs(row1 - row2):
                    violations += 1
        return violations

    def plotBoard(self, positions):
        """Dibuja el tablero usando el estilo y la imagen original."""
        if len(positions) != self.numOfQueens:
            raise ValueError("El tamaño de la lista debe ser igual a ", self.numOfQueens)

        fig, ax = plt.subplots()

        # 1. Dibujar el tablero de ajedrez (mismos colores del libro)
        board = np.zeros((self.numOfQueens, self.numOfQueens))
        board[::2, 1::2] = 1
        board[1::2, ::2] = 1
        
        # Colores originales: '#ffc794' (beige) y '#4c2f27' (marrón oscuro)
        ax.imshow(board, interpolation='none', cmap=mpl.colors.ListedColormap(['#ffc794', '#4c2f27']))

        # 2. Cargar la imagen de la reina
        # NOTA: Asegúrate de que 'queen-thumbnail.png' esté en la misma carpeta
        try:
            queenThumbnail = plt.imread("queen-thumbnail.png")
            # Ajuste para centrar la imagen en la casilla
            thumbnailSpread = 0.70 * np.array([-1, 1, -1, 1]) / 2  
            
            # Dibujar cada reina
            for i, j in enumerate(positions):
                # i es la columna, j es la fila (posición)
                ax.imshow(queenThumbnail, extent=[i, i, j, j] + thumbnailSpread)
                
        except FileNotFoundError:
            print("ADVERTENCIA: No se encontró 'queen-thumbnail.png'. Se usarán círculos en su lugar.")
            for i, j in enumerate(positions):
                ax.plot(i, j, 'o', color='gold', markersize=15, markeredgecolor='black')

        # 3. Configuración de ejes
        ax.set(xticks=list(range(self.numOfQueens)), yticks=list(range(self.numOfQueens)))
        ax.axis('image')
        plt.title(f"Solución Firefly: {self.getViolationsCount(positions)} Violaciones")
        return plt

class FireflyAlgorithm:
    def __init__(self, n_queens, pop_size, gamma=1.0):
        self.n_queens = n_queens
        self.pop_size = pop_size
        self.gamma = gamma   # Coeficiente de absorción de luz
        self.population = []
        self.fitnesses = []
        self.problem = NQueensProblem(n_queens)

    def init_population(self):
        self.population = [random.sample(range(self.n_queens), self.n_queens) for _ in range(self.pop_size)]
        self.fitnesses = [float('inf')] * self.pop_size

    def evaluate_all(self):
        for i in range(self.pop_size):
            self.fitnesses[i] = self.problem.getViolationsCount(self.population[i])

    def move_firefly(self, source_idx, target_idx):
        """Mueve una solución hacia otra mejor intercambiando posiciones."""
        source = self.population[source_idx]
        target = self.population[target_idx]
        new_pos = list(source)
        
        # Distancia de Hamming (cuántas reinas están en diferente lugar)
        diff_indices = [k for k in range(self.n_queens) if source[k] != target[k]]
        dist = len(diff_indices)
        
        if dist > 0:
            # Movimiento discreto: hacer swaps proporcionales a la distancia
            num_swaps = int(dist * 0.2) + 1 
            for _ in range(num_swaps):
                idx1, idx2 = random.sample(range(self.n_queens), 2)
                new_pos[idx1], new_pos[idx2] = new_pos[idx2], new_pos[idx1]
                
        return new_pos

    def run(self, max_generations):
        self.init_population()
        self.evaluate_all()
        
        history = []
        best_overall_fitness = float('inf')
        best_solution = None

        print(f"Ejecutando Firefly ({self.n_queens} Reinas)...")

        for t in range(max_generations):
            for i in range(self.pop_size):
                for j in range(self.pop_size):
                    
                    # Si la luciérnaga J es mejor que I, I se mueve hacia J
                    if self.fitnesses[j] < self.fitnesses[i]:
                        
                        dist = np.sum([1 for k in range(self.n_queens) if self.population[i][k] != self.population[j][k]])
                        beta = 1.0 * np.exp(-self.gamma * (dist ** 2))
                        
                        if random.random() < beta:
                            self.population[i] = self.move_firefly(i, j)
                            self.fitnesses[i] = self.problem.getViolationsCount(self.population[i])

            current_best = min(self.fitnesses)
            history.append(current_best)
            
            # Guardar el mejor histórico
            if current_best < best_overall_fitness:
                best_overall_fitness = current_best
                best_idx = self.fitnesses.index(current_best)
                best_solution = list(self.population[best_idx])
                
                # Si encontramos la solución perfecta, terminamos antes (Opcional)
                if best_overall_fitness == 0:
                    break

        return best_overall_fitness, best_solution, history, self.problem

if __name__ == "__main__":
    random.seed(42)
    # --- PARÁMETROS ---
    N_QUEENS = 16       # Puedes cambiar a 16
    POPULATION = 50       
    GENERATIONS = 50      
    
    # Iniciar Solver
    solver = FireflyAlgorithm(N_QUEENS, POPULATION)
    
    # Medir tiempo
    start_time = time.perf_counter()
    best_score, best_board, curve, problem_instance = solver.run(GENERATIONS)
    end_time = time.perf_counter()
    
    # Imprimir
    print("-" * 30)
    print(f"Tiempo Total: {end_time - start_time:.4f} s")
    print(f"Mejor Fitness: {best_score}")
    print("-" * 30)

    # 2. Visualización del Tablero (Estilo Original)
    if best_board:
        print("Abriendo visualización del tablero...")
        problem_instance.plotBoard(best_board).show()