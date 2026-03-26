import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
from itertools import chain
import os


# take in data, process it
def prepare_data(filepath, seq_length=16):
    processed_path = f'{filepath.replace(".txt", "")}_processed.pt'  # checkpointing
    if os.path.exists(processed_path):
        print(f"Loading existing pre-processed data from {processed_path}")
        checkpoint = torch.load(processed_path)
        return (checkpoint['X'], checkpoint['y'], checkpoint['vocab'],
                checkpoint['c2i'], checkpoint['i2c'])

    with open(filepath) as f:
        valid_chords = ['i', 'ii', 'iii', 'iv', 'v', 'vi', 'vii',
                        'I', 'II', 'III', 'IV', 'V', 'VI', 'VII']
        chords = list(chain(*[[c for c in l.strip().split() if c in valid_chords] for l in f.readlines()]))

    vocab = sorted(list(set(chords)))
    chord_to_int = {c: i for i, c in enumerate(vocab)}
    int_to_chord = {i: c for i, c in enumerate(vocab)}

    # runtime sucks if i use the whole dataset (len around 11mil)
    full_data = torch.LongTensor([chord_to_int[c] for c in chords])[:1000000]
    X = full_data.unfold(0, seq_length, 1)[:-1]
    y = full_data[seq_length:]

    torch.save({  # save to file
        'X': X,
        'y': y,
        'vocab': vocab,
        'c2i': chord_to_int,
        'i2c': int_to_chord
    }, 'data/chord_bases_no_repeats_processed.pt')

    return X, y, vocab, chord_to_int, int_to_chord


# actual model
class ChordLSTM(nn.Module):
    def __init__(self, vocab_size, embed_dim, hidden_dim):
        super(ChordLSTM, self).__init__()
        self.embedding = nn.Embedding(vocab_size, embed_dim)
        # batch_first=True means input shape is (batch, seq, feature)
        self.lstm = nn.LSTM(embed_dim, hidden_dim, batch_first=True, num_layers=2)
        self.dropout = nn.Dropout(0.2)
        self.fc = nn.Linear(hidden_dim, vocab_size)

    def forward(self, x):
        embedded = self.embedding(x)
        lstm_out, (_, __) = self.lstm(embedded)
        # forward step
        last_time_step = lstm_out[:, -1, :]
        out = self.fc(self.dropout(last_time_step))
        return out


def train(model, X, y, epochs=10, batch_size=128, lr=0.001, save_dir='model_states'):
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model.to(device)

    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=lr)

    dataset = TensorDataset(X, y)
    loader = DataLoader(dataset, batch_size=batch_size, shuffle=True)

    print(f"Starting training on {device}...")

    for epoch in range(epochs):
        model.train()
        total_loss = 0

        for batch_idx, (data, target) in enumerate(loader):
            data, target = data.to(device), target.to(device)

            optimizer.zero_grad()
            output = model(data)
            loss = criterion(output, target)
            loss.backward()
            optimizer.step()

            log_interval = 100

            # Diagnostic Print
            if batch_idx % log_interval == 0 and batch_idx > 0:
                processed_samples = batch_idx * batch_size
                percent_complete = (batch_idx / len(loader)) * 100

                print(f"Epoch: {epoch + 1} [{processed_samples}/{len(X)}] "
                      f"({percent_complete:.1f}%)")

            total_loss += loss.item()

        avg_loss = total_loss / len(loader)
        print(f"Epoch {epoch + 1}/{epochs} - Loss: {avg_loss:.4f}")

        # Save model state
        if epoch % 2 == 1:
            checkpoint_path = os.path.join(save_dir, f"chord_model_no_repeats_epoch_{epoch + 1}.pth")
            torch.save(model.state_dict(), checkpoint_path)


def main():
    X, y, vocab, c2i, i2c = prepare_data('data/chord_bases_no_repeats.txt')
    model = ChordLSTM(vocab_size=len(vocab), embed_dim=64, hidden_dim=128)

    train(model, X, y, epochs=10)


if __name__ == '__main__':
    main()
