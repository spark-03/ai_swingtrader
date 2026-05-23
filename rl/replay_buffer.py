import random

from collections import deque


class ReplayBuffer:

    def __init__(self, max_size=100000):

        # ====================================
        # MEMORY BUFFER
        # ====================================

        self.buffer = deque(maxlen=max_size)

    # ====================================
    # STORE EXPERIENCE
    # ====================================

    def store(

        self,

        state,

        action,

        reward,

        next_state,

        done

    ):

        experience = (

            state,

            action,

            reward,

            next_state,

            done
        )

        self.buffer.append(experience)

    # ====================================
    # SAMPLE MINI-BATCH
    # ====================================

    def sample(self, batch_size):

        return random.sample(

            self.buffer,

            batch_size
        )

    # ====================================
    # CURRENT BUFFER SIZE
    # ====================================

    def size(self):

        return len(self.buffer)