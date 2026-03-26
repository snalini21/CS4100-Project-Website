import random
from collections import defaultdict, Counter
from itertools import chain


def build_transition_matrix(file_path):
    with open(file_path, 'r') as f:
        # more complex chords (ex: 'ger' as augmented 6th) show up in dataset, but i'd like to avoid them
        valid_chords = ['i', 'ii', 'iii', 'iv', 'v', 'vi', 'vii',
                        'I', 'II', 'III', 'IV', 'V', 'VI', 'VII']
        # chords are space separated; get it in a flattened list
        chords = list(chain(*[[c for c in l.strip().split() if c in valid_chords] for l in f.readlines()]))

    transitions = defaultdict(Counter)  # basic bigram for now
    for i in range(len(chords) - 1):
        transitions[chords[i]][chords[i + 1]] += 1

    # counts to probabilities
    probs = {}
    for chord, next_chords in transitions.items():
        total = sum(next_chords.values())
        probs[chord] = {nxt: count / total for nxt, count in next_chords.items()}
    return probs, list(set(chords))


# fitness
def calculate_fitness(progression, probs):
    score = 0
    for i in range(len(progression) - 1):
        current, nxt = progression[i], progression[i + 1]
        # reward transitions that show up often
        score += probs.get(current, {}).get(nxt, 0)
    return score


# genetic operators
def mutate(progression, all_chords, rate=0.1):
    if random.random() < rate:
        idx = random.randint(0, len(progression) - 1)
        progression[idx] = random.choice(all_chords)
    return progression


def crossover(parent1, parent2):
    point = random.randint(1, len(parent1) - 1)
    return parent1[:point] + parent2[point:]


# actual logic
def generate_progression(filepath, length=4, pop_size=20, gens=50):
    probs, all_chords = build_transition_matrix(filepath)
    population = [[random.choice(all_chords) for _ in range(length)] for _ in range(pop_size)]
    fitness_history = []

    for _ in range(gens):
        # sort by fitness
        population = sorted(population, key=lambda p: calculate_fitness(p, probs), reverse=True)
        
        # track fitness
        best_overall_fitness = calculate_fitness(population[0], probs)
        fitness_history.append(best_overall_fitness)
        
        next_gen = population[:2]

        while len(next_gen) < pop_size:
            p1, p2 = random.sample(population[:10], 2)
            child = crossover(p1, p2)  # realistically this would be more random
            child = mutate(child, all_chords)
            next_gen.append(child)

        population = next_gen

    return population[0], fitness_history

