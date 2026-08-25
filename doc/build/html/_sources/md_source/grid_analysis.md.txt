# 🔎 Grid analysis

VeraGrid includes a grid analysis dashboard that combines structural checks, issue grouping,
safe auto-fixes, and sigma stability information in one place.

## What the analysis does

The dashboard inspects the current grid model and reports findings such as:

- inconsistent or suspicious input values
- values outside accepted ranges
- topology or modelling warnings
- non-converging sigma analysis
- buses whose sigma points fall outside the sigma stability curve

The findings are grouped by:

- severity
- message
- object type

This makes it easier to see repeated problem families such as line data issues,
bus-level sigma issues, or transformer parameter inconsistencies.

## Severity classes

The grid analysis dashboard uses four severity classes:

- `Error`
- `Warning`
- `Information`
- `Divergence`

The `critical findings` count shown in the dashboard is:

```text
critical = errors + divergences
```

## Dashboard score

The dashboard computes an `issue score` in the interval `[0, 100]`.
This score depends on the number of findings and their severity.

The weighted penalty is:

```text
penalty =
  12.0 * errors +
   4.0 * warnings +
   0.1 * information +
  16.0 * divergences
```

The penalty is then scaled by the size of the grid:

```text
asset_scale = max(3.0, sqrt(asset_count) * 1.8)
issue_score = 100.0 - ((penalty / asset_scale) * 10.0)
```

Finally, the score is clamped to the interval `[0, 100]`.

This scaling avoids punishing large systems only because they contain more assets.

### Counted assets

The asset count used by the score includes:

- buses
- lines
- two-winding transformers
- windings
- loads
- generators
- batteries
- static generators
- shunts

## Sigma contribution

If sigma analysis is available, VeraGrid also computes a `sigma score`.

The sigma score is based on:

- the minimum sigma distance
- the mean sigma distance

The normalized sigma margin is:

```text
normalized_margin = ((0.65 * min_distance) + (0.35 * mean_distance)) / 0.25
sigma_score = clamp(normalized_margin * 100.0, 0.0, 100.0)
```

If sigma does not converge, VeraGrid subtracts `20` points from the sigma score.

## Final score and grade

If sigma is available, the final score is:

```text
overall_score = round(0.75 * issue_score + 0.25 * sigma_score)
```

If sigma is not available, the final score is simply:

```text
overall_score = round(issue_score)
```

The grade mapping is:

- `A`: score `>= 90`
- `B`: score `>= 80`
- `C`: score `>= 70`
- `D`: score `>= 60`
- `F`: score `< 60`

## Safe fixes

Some findings are marked as auto-fixable.
These are issues for which VeraGrid can apply a deterministic correction from the dashboard.

Examples include:

- clamping values to accepted ranges
- correcting negative values where they are not allowed
- fixing inverted ranges
- correcting transformer virtual tap assignments

Only the findings recognized as safe deterministic fixes are affected by the
`Fix safe issues` action.
