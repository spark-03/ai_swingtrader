import pandas as pd

from rl.environment import TradingEnvironment
from strategy.signal_engine import generate_signal


class RLDatasetGenerator:

    def __init__(self, df):

        self.df = df

        self.env = TradingEnvironment(df)

        self.dataset = []

    # ====================================
    # CONVERT SIGNAL TO ACTION
    # ====================================

    def signal_to_action(self, signal):

        if signal == "BUY":

            return 1

        elif signal == "SELL":

            return 2

        return 0

    # ====================================
    # GENERATE DATASET
    # ====================================

    def generate(self):

        state = self.env.reset()

        for i in range(50, len(self.df) - 1):

            current_df = self.df.iloc[:i]

            signal_data = generate_signal(current_df)

            action = self.signal_to_action(
                signal_data["signal"]
            )

            next_state, reward, done = self.env.step(action)

            transition = {

                "state": state.tolist(),

                "action": action,

                "reward": reward,

                "next_state": next_state.tolist(),

                "done": done
            }

            self.dataset.append(transition)

            state = next_state

            if done:

                break

        return pd.DataFrame(self.dataset)