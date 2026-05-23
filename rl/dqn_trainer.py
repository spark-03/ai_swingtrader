import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np

from copy import deepcopy


class DQNTrainer:

    def __init__(

        self,

        model,

        replay_buffer,

        gamma=0.99,

        learning_rate=0.001,

        target_update_freq=100
    ):

        # ====================================
        # MAIN NETWORK
        # ====================================

        self.model = model

        # ====================================
        # TARGET NETWORK
        # ====================================

        self.target_model = deepcopy(model)

        self.target_model.eval()

        # ====================================
        # REPLAY BUFFER
        # ====================================

        self.replay_buffer = replay_buffer

        # ====================================
        # RL SETTINGS
        # ====================================

        self.gamma = gamma

        self.target_update_freq = target_update_freq

        self.train_steps = 0

        # ====================================
        # LOSS FUNCTION
        # ====================================

        self.criterion = nn.MSELoss()

        # ====================================
        # OPTIMIZER
        # ====================================

        self.optimizer = optim.Adam(

            self.model.parameters(),

            lr=learning_rate
        )

    # ====================================
    # UPDATE TARGET NETWORK
    # ====================================

    def update_target_network(self):

        self.target_model.load_state_dict(

            self.model.state_dict()
        )

        print("\nTarget Network Updated")

    # ====================================
    # TRAIN STEP
    # ====================================

    def train_step(self, batch_size=32):

        # ====================================
        # CHECK BUFFER SIZE
        # ====================================

        if self.replay_buffer.size() < batch_size:

            return None

        # ====================================
        # SAMPLE BATCH
        # ====================================

        batch = self.replay_buffer.sample(

            batch_size
        )

        states = []
        actions = []
        rewards = []
        next_states = []
        dones = []

        # ====================================
        # EXTRACT DATA
        # ====================================

        for experience in batch:

            state, action, reward, next_state, done = experience

            states.append(state)

            actions.append(action)

            rewards.append(reward)

            next_states.append(next_state)

            dones.append(done)

        # ====================================
        # TO TENSORS
        # ====================================

        states = torch.FloatTensor(

            np.array(states)
        )

        actions = torch.LongTensor(actions)

        rewards = torch.FloatTensor(rewards)

        next_states = torch.FloatTensor(

            np.array(next_states)
        )

        dones = torch.FloatTensor(dones)

        # ====================================
        # CURRENT Q VALUES
        # ====================================

        current_q_values = self.model(states)

        current_q_values = current_q_values.gather(

            1,

            actions.unsqueeze(1)

        ).squeeze(1)

        # ====================================
        # DDQN TARGET
        # ====================================

        with torch.no_grad():

            # ====================================
            # MAIN NETWORK CHOOSES ACTION
            # ====================================

            next_actions = self.model(

                next_states
            ).argmax(1)

            # ====================================
            # TARGET NETWORK EVALUATES ACTION
            # ====================================

            next_q_values = self.target_model(

                next_states
            )

            next_q_values = next_q_values.gather(

                1,

                next_actions.unsqueeze(1)

            ).squeeze(1)

        # ====================================
        # TARGET Q VALUES
        # ====================================

        target_q_values = rewards + (

            self.gamma *

            next_q_values *

            (1 - dones)
        )

        # ====================================
        # LOSS
        # ====================================

        loss = self.criterion(

            current_q_values,

            target_q_values
        )

        # ====================================
        # BACKPROP
        # ====================================

        self.optimizer.zero_grad()

        loss.backward()

        self.optimizer.step()

        # ====================================
        # TARGET UPDATE
        # ====================================

        self.train_steps += 1

        if self.train_steps % self.target_update_freq == 0:

            self.update_target_network()

        return loss.item()