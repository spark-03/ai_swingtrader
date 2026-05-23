import torch
import torch.nn as nn


class DQN(nn.Module):

    def __init__(

        self,

        state_size,

        action_size

    ):

        super(DQN, self).__init__()

        # ====================================
        # NETWORK
        # ====================================

        self.network = nn.Sequential(

            nn.Linear(state_size, 128),

            nn.ReLU(),

            nn.Linear(128, 128),

            nn.ReLU(),

            nn.Linear(128, action_size)
        )

    # ====================================
    # FORWARD PASS
    # ====================================

    def forward(self, x):

        return self.network(x)