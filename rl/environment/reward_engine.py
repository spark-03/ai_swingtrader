class RewardEngine:

    def __init__(self):

        pass

    # ====================================
    # REWARD FUNCTION
    # ====================================

    def calculate(

        self,

        realized_pnl_percent,

        holding_steps,

        trade_closed,

        profitable_trade,

        stop_loss_hit,

        trailing_exit,

        market_quality
    ):

        reward = 0.0

        # ====================================
        # NO TRADE YET
        # ====================================

        if not trade_closed:

            # tiny hold reward only
            reward += 0.001

            # slight bonus for strong setups
            if market_quality > 30:

                reward += 0.002

            return reward

        # ====================================
        # REALIZED PNL
        # ====================================

        reward += (

            realized_pnl_percent * 100
        )

        # ====================================
        # BIG WINNER BONUS
        # ====================================

        if realized_pnl_percent > 0.03:

            reward += 5

        if realized_pnl_percent > 0.05:

            reward += 10

        if realized_pnl_percent > 0.08:

            reward += 20

        # ====================================
        # BIG LOSS PENALTY
        # ====================================

        if realized_pnl_percent < -0.02:

            reward -= 8

        if realized_pnl_percent < -0.04:

            reward -= 15

        # ====================================
        # PROFITABLE TRADE BONUS
        # ====================================

        if profitable_trade:

            reward += 2

        # ====================================
        # STOP LOSS PENALTY
        # ====================================

        if stop_loss_hit:

            reward -= 5

        # ====================================
        # TRAILING EXIT BONUS
        # ====================================

        if trailing_exit and profitable_trade:

            reward += 3

        # ====================================
        # LONG HOLD BONUS
        # ====================================

        if profitable_trade:

            if holding_steps > 20:

                reward += 2

            if holding_steps > 50:

                reward += 5

        return reward