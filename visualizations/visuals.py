import os
from collections import Counter, defaultdict
from itertools import chain
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

from models.markov_model import MarkovChordModel
from models.generate_chords_from_model import load_model_and_generate
from models.genetic_algo import generate_progression

#loading dataset (.txt), obtaining a list of chords
def load_progressions(filepath):
    progressions = []
    with open(filepath, "r") as file:
        for line in file:
            line = line.strip()
            if not line:
                continue
            chords = line.split()
            progressions.append(chords)
    return progressions


#Count transitions, convert them into probabilities, and use the output as "real" music
def build_reference_transitions(progressions):
    transitions = defaultdict(Counter)

    for prog in progressions:
        for i in range(len(prog) - 1):
            current_chord = prog[i]
            next_chord = prog[i + 1]
            transitions[current_chord][next_chord] += 1

    probs = {}
    for chord, next_chords in transitions.items():
        total = sum(next_chords.values())
        probs[chord] = {
            next_chord: count / total
            for next_chord, count in next_chords.items()
        }

    return probs

#Make folder for visuals if not already. there.
def ensure_figures_dir():
    os.makedirs("visualizations", exist_ok=True)

#Looking into how many unique chords are used
def diversity_score(progression):
    return len(set(progression))

#How often are chords repeated back to back
def repetition_score(progression):
    if len(progression) < 2:
        return 0.0
    repeats = sum(1 for i in range(1, len(progression)) if progression[i] == progression[i - 1])
    return repeats / (len(progression) - 1)

#Does this transition from one chord to the next likely exist in real data
def transition_validity_score(progression, reference_probs):
    if len(progression) < 2:
        return 0.0

    valid = 0
    total = len(progression) - 1

    for i in range(total):
        current_chord = progression[i]
        next_chord = progression[i + 1]

        if current_chord in reference_probs and next_chord in reference_probs[current_chord]:
            valid += 1

    return valid / total

#Heatmap of how often chords follow each other
def save_transition_matrix(reference_probs, filename):
    df = pd.DataFrame(reference_probs).fillna(0)

    plt.figure(figsize=(8, 6))
    sns.heatmap(df, annot=False, cmap="coolwarm")
    plt.title("Training Data Transition Matrix")
    plt.xlabel("Current Chord")
    plt.ylabel("Next Chord")
    plt.tight_layout()
    plt.savefig(f"visualizations/{filename}")
    plt.close()

#Determines which chords are favored among the models
def save_chord_distribution_comparison(markov_prog, lstm_prog, ga_prog, filename):
    markov_counts = Counter(markov_prog)
    lstm_counts = Counter(lstm_prog)
    ga_counts = Counter(ga_prog)

    all_chords = sorted(set(markov_counts) | set(lstm_counts) | set(ga_counts))

    markov_vals = [markov_counts.get(chord, 0) for chord in all_chords]
    lstm_vals = [lstm_counts.get(chord, 0) for chord in all_chords]
    ga_vals = [ga_counts.get(chord, 0) for chord in all_chords]

    x = np.arange(len(all_chords))
    width = 0.25

    plt.figure(figsize=(12, 6))
    plt.bar(x - width, markov_vals, width, label="Markov")
    plt.bar(x, lstm_vals, width, label="LSTM")
    plt.bar(x + width, ga_vals, width, label="Genetic Algorithm")

    plt.xticks(x, all_chords)
    plt.xlabel("Chord")
    plt.ylabel("Count")
    plt.title("Chord Frequency Comparison")
    plt.legend()
    plt.tight_layout()
    plt.savefig(f"visualizations/{filename}")
    plt.close()

#Illustrates how chords evolve over time
def save_sequence_comparison(markov_prog, lstm_prog, ga_prog, chord_to_int, filename):
    markov_numeric = [chord_to_int[c] for c in markov_prog]
    lstm_numeric = [chord_to_int[c] for c in lstm_prog]
    ga_numeric = [chord_to_int[c] for c in ga_prog]

    plt.figure(figsize=(12, 6))
    plt.plot(markov_numeric, label="Markov")
    plt.plot(lstm_numeric, label="LSTM", linestyle="dashed")
    plt.plot(ga_numeric, label="Genetic Algorithm", linestyle="dotted")

    plt.xlabel("Time Step")
    plt.ylabel("Chord Index")
    plt.title("Chord Sequence Comparison")
    plt.legend()
    plt.tight_layout()
    plt.savefig(f"visualizations/{filename}")
    plt.close()

#Compares model performance
def save_metric_comparison(metrics, filename):
    metric_names = list(metrics.keys())
    model_names = list(next(iter(metrics.values())).keys())

    x = np.arange(len(metric_names))
    width = 0.25

    plt.figure(figsize=(12, 6))

    for i, model_name in enumerate(model_names):
        values = [metrics[metric][model_name] for metric in metric_names]
        plt.bar(x + i * width, values, width, label=model_name)

    plt.xticks(x + width, metric_names)
    plt.ylabel("Score")
    plt.title("Model Metrics Comparison")
    plt.legend()
    plt.tight_layout()
    plt.savefig(f"visualizations/{filename}")
    plt.close()

#Fitness plot from genetic algorithm model
def save_ga_fitness(fitness_history, filename):
    plt.figure(figsize=(8, 5))
    plt.plot(fitness_history)
    plt.xlabel("Generation")
    plt.ylabel("Fitness")
    plt.title("GA Fitness over Generations")
    plt.tight_layout()
    plt.savefig(f'visualizations/{filename}')
    plt.close()


#Further adding onto visuals for presentation
def save_generated_progressions_text(markov_prog, lstm_prog, ga_prog, filename):
    with open(f"visualizations/{filename}", "w") as f:
        f.write("Generated Progressions\n\n")
        f.write("Markov:\n")
        f.write(" ".join(markov_prog))
        f.write("\n\n")

        f.write("LSTM:\n")
        f.write(" ".join(lstm_prog))
        f.write("\n\n")

        f.write("Genetic Algorithm:\n")
        f.write(" ".join(ga_prog))
        f.write("\n")

#Pipeline
def main():
    #Make sure folder exists
    ensure_figures_dir()

    #paths for data
    data_path = "models/data/chord_bases_1.txt"
    model_path = "models/model_states/chord_model_epoch_10.pth"
    data_meta_path = "models/data/chord_bases_processed.pt"

    #load data
    progressions = load_progressions(data_path)
    reference_probs = build_reference_transitions(progressions)

    #Chord mapping
    all_training_chords = list(chain.from_iterable(progressions))
    unique_chords = sorted(set(all_training_chords))
    chord_to_int = {chord: i for i, chord in enumerate(unique_chords)}

    #Run model (markov)
    markov_model = MarkovChordModel()
    markov_model.train(progressions)
    markov_prog = markov_model.generate(start="I", length=50)

    #Run model (lstm)
    seed = ["I", "V", "vi", "IV", "I", "V", "I", "I"]
    lstm_prog = load_model_and_generate(
        model_path,
        data_meta_path,
        seed_chords=seed,
        length=50
    )

    #Run model (ga)
    ga_prog, fitness_history = generate_progression(
        data_path,
        length=50
    )

    #metrics for computing
    metrics = {
        "Diversity": {
            "Markov": diversity_score(markov_prog),
            "LSTM": diversity_score(lstm_prog),
            "Genetic": diversity_score(ga_prog)
        },
        "Repetition": {
            "Markov": repetition_score(markov_prog),
            "LSTM": repetition_score(lstm_prog),
            "Genetic": repetition_score(ga_prog)
        },
        "Transition Validity": {
            "Markov": transition_validity_score(markov_prog, reference_probs),
            "LSTM": transition_validity_score(lstm_prog, reference_probs),
            "Genetic": transition_validity_score(ga_prog, reference_probs)
        }
    }

    #saving visuals as pngs and any progression texts
    save_transition_matrix(reference_probs, "training_transition_matrix.png")
    save_chord_distribution_comparison(
        markov_prog,
        lstm_prog,
        ga_prog,
        "chord_distribution_comparison.png"
    )
    save_sequence_comparison(
        markov_prog,
        lstm_prog,
        ga_prog,
        chord_to_int,
        "sequence_comparison.png"
    )
    save_metric_comparison(metrics, "metric_comparison.png")
    save_generated_progressions_text(
        markov_prog,
        lstm_prog,
        ga_prog,
        "generated_progressions.txt"
    )

    save_ga_fitness(fitness_history, "ga_fitness.png")

    print("Saved files to visualizations")
    print()
    print("Metric summary:")
    for metric_name, model_scores in metrics.items():
        print(metric_name)
        for model_name, score in model_scores.items():
            if isinstance(score, float):
                print(f"  {model_name}: {score:.4f}")
            else:
                print(f"  {model_name}: {score}")
        print()


if __name__ == "__main__":
    main()