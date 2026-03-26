import random
from collections import defaultdict

#Class for the Markov model to generate chord progressions
class MarkovChordModel:

  #Constructor
  def __init__(self):
      #Count transitions between chords
      self.transition_counts = defaultdict(lambda: defaultdict(int))
      #Store normalized probabilities
      self.transition_probs = {}

  #Train the Markov model:
  #This model learns from the dataset of chord progressions. It begins by looping through each progression
  #in the data, then looks at consecutive chords to count how many times each chord transitions to the next,
  #and then counts how many times each transition occurs.
  def train(self, progressions):
     
      for prog in progressions:
          for i in range(len(prog) - 1):
              current_chord = prog[i]
              next_chord = prog[i + 1]
              self.transition_counts[current_chord][next_chord] += 1

      self._normalize()

   #Converts counts to probabilities for us to use: For example, if "I" transitions to "IV"
   #10 times out of the 30 times we dictate, then the probability of this transition becomes 10/30 = 0.33
  def _normalize(self):
      for chord, next_chords in self.transition_counts.items():
          total = sum(next_chords.values())
          self.transition_probs[chord] = {
              next_chord: count / total
              for next_chord, count in next_chords.items()
          }

  #Generate a chord progression using the learned probabilities.
  #We begin with I (this may be changed later). Then, we loop through length - 1 times to build the progression.
  #Next, we look up the possible next chords and randomly select the next chord based on the learned probabilities.
  #We will repeat this until the desired length is reached.
  def generate(self, start="I", length=14):
      progression = [start]
      current_chord = start

      for _ in range(length - 1):
          if current_chord not in self.transition_probs:
              break
         
          next_chords = list(self.transition_probs[current_chord].keys())
          probabilities = list(self.transition_probs[current_chord].values())

          next_chord = random.choices(next_chords, probabilities)[0]
          progression.append(next_chord)
          current_chord = next_chord

      return progression


#Read the chord progression dataset from a text file and convert it into a list of chord progressions
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


#Main function to run the file/model
def main():
  #Load dataset
  data = load_progressions("models/data/chord_bases.txt")

  #Initialize model
  model = MarkovChordModel()

  #Train model
  model.train(data)

  #Accepting user input for the progression size
  user_input_row_amount = int(input("Enter the length of the progression:14 "))
 
  #Generate some chord progressions
  progression = model.generate(start="I", length=user_input_row_amount)
  print("Generated:", " ".join(progression))


if __name__ == "__main__":
  main()