def subset_combos(s):
    # start at range 2 because we do not need the emptyset or single sources
    return [combo for r in range(2, len(s) + 1) for combo in itertools.combinations(s, r)]