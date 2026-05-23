import random
import numpy as np


class PrioritizedReplayBuffer:

    def __init__(

        self,

        capacity,

        alpha=0.6
    ):

        self.capacity = capacity

        self.alpha = alpha

        self.memory = []

        self.priorities = []

        self.position = 0

    # ====================================
    # ADD EXPERIENCE
    # ====================================

    def push(

        self,

        state,

        action,

        reward,

        next_state,

        done
    ):

        max_priority = (

            max(self.priorities)

            if self.priorities

            else 1.0
        )

        experience = (

            state,

            action,

            reward,

            next_state,

            done
        )

        if len(self.memory) < self.capacity:

            self.memory.append(

                experience
            )

            self.priorities.append(

                max_priority
            )

        else:

            self.memory[
                self.position
            ] = experience

            self.priorities[
                self.position
            ] = max_priority

            self.position = (

                self.position + 1
            ) % self.capacity

    # ====================================
    # SAMPLE
    # ====================================

    def sample(

        self,

        batch_size,

        beta=0.4
    ):

        priorities = np.array(

            self.priorities
        )

        probabilities = (

            priorities

            **

            self.alpha
        )

        probabilities /= probabilities.sum()

        indices = np.random.choice(

            len(self.memory),

            batch_size,

            p=probabilities
        )

        samples = [

            self.memory[i]

            for i in indices
        ]

        total = len(self.memory)

        weights = (

            total

            *

            probabilities[indices]
        ) ** (-beta)

        weights /= weights.max()

        return (

            samples,

            indices,

            weights
        )

    # ====================================
    # UPDATE PRIORITIES
    # ====================================

    def update_priorities(

        self,

        indices,

        td_errors
    ):

        for idx, error in zip(

            indices,

            td_errors
        ):

            self.priorities[idx] = (

                abs(error)

                + 1e-5
            )

    # ====================================
    # LENGTH
    # ====================================

    def __len__(self):

        return len(self.memory)