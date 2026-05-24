class RegimeClassifier:
    """Simple regime classifier for training filter.

    The RL training loop should avoid acting in regimes that are considered
    low‑quality or noisy. This classifier provides an ``is_acceptable`` method
    that returns ``True`` for regimes we want to allow trading in and ``False``
    otherwise.

    Currently the logic is straightforward:

    - Accept ``"trending"`` and ``"volatile"`` – these regimes typically offer
      clear direction or enough movement for the RL agent to learn.
    - Reject ``"choppy"``, ``"neutral"`` and any unknown regime – these are
      either sideways markets or unrecognised labels where taking action is
      risky.
    """

    def __init__(self):
        # Define the set of regimes that are considered acceptable for trading.
        self._acceptable = {"trending", "volatile"}

    def is_acceptable(self, regime: str) -> bool:
        """Return ``True`` if the given ``regime`` is allowed for trading.

        Parameters
        ----------
        regime: str
            The regime name returned by ``MarketRegimeDetector`` or other
            analysis components.
        """
        return regime in self._acceptable
