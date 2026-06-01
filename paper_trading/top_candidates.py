import pandas as pd

df = pd.read_csv("logs/live_candidates.csv")

top3 = df.head(3).copy()

top3.to_csv(
    "logs/top3_candidates.csv",
    index=False
)

print(top3[
    ["rank","symbol","pqs","last_price"]
])
