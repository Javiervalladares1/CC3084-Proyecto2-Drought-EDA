"""Arquitectura LSTM, cargada solo en el proceso de la red neuronal."""
import torch
from torch import nn

from .data import SEQ_CHANNELS, STATIC_CHANNELS


class WaterLSTM(nn.Module):
    def __init__(self, window=6, hidden_size=32, head_size=32, dropout=.1):
        super().__init__()
        self.window = window
        self.sequence_width = len(SEQ_CHANNELS)
        self.lstm = nn.LSTM(self.sequence_width, hidden_size, batch_first=True)
        self.head = nn.Sequential(nn.Linear(hidden_size + len(STATIC_CHANNELS), head_size),
                                  nn.ReLU(), nn.Dropout(dropout), nn.Linear(head_size, 1))

    def forward(self, x):
        split = self.window * self.sequence_width
        sequence = x[:, :split].reshape(-1, self.window, self.sequence_width)
        _, (hidden, _) = self.lstm(sequence)
        return self.head(torch.cat([hidden[-1], x[:, split:]], dim=1)).squeeze(-1)
