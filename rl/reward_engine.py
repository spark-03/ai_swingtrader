class RewardEngine:

    def __init__(self):

        # =========================
        # CONFIG
        # =========================

        self.transaction_cost = 0.0005

        self.overtrade_penalty = 0.0001

    # ====================================
    # CALCULATE REWARD
    # ====================================

    def calculate_reward(

        self,

        current_position,

        entry_price,

        current_price,

        action

    ):

        reward = 0

        # ====================================
        # LONG POSITION
        # ====================================

        if current_position == 1:

            reward = (
                current_price - entry_price
            ) / entry_price

        # ====================================
        # SHORT POSITION
        # ====================================

        elif current_position == -1:

            reward = (
                entry_price - current_price
            ) / entry_price

        # ====================================
        # TRANSACTION COST
        # ====================================

        if action in [1, 2]:

            reward -= self.transaction_cost

        # ====================================
        # OVERTRADING PENALTY
        # ====================================

        if action != 0:

            reward -= self.overtrade_penalty

        return reward