# Test Results

## Filter option coverage

| Option / flag        | Scenario exercised                                               | Result |
|----------------------|------------------------------------------------------------------|--------|
| `--include`          | Default recursive walk plus `./nested` prefix to target a folder | ✅ Pass |
| `--exclude`          | Directory exclusion including `./skip` prefix                    | ✅ Pass |
| `.gitignore`/`--not-ignore` | Respecting and bypassing `.gitignore` entries                  | ✅ Pass |
| `--max-size`         | Skipping files above the configured byte limit                   | ✅ Pass |
| `--binary-strict`    | Allowing noisy binary-like files with `--no-binary-strict`       | ✅ Pass |

## Command executed

- `pytest -q` (passes with coverage ≥ 90%)
