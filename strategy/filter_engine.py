def passes_filters(stock):

    # Remove weak scores
    if stock["score"] < 60:
        return False

    # Remove sideways stocks
    if stock["trend"] == "SIDEWAYS":
        return False

    return True