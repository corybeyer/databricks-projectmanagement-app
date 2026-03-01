Run the PM Hub test suite using pytest.

## Arguments

$ARGUMENTS — optional filter for which tests to run (e.g., `callbacks`, `services`, `repos`, `pages`, `charts`).

## Instructions

Run the test suite with:

```
/c/Users/coryb/anaconda3/python.exe -m pytest tests/ -v --tb=short
```

If `$ARGUMENTS` is provided, map it to a test directory:
- `callbacks` → `tests/test_callbacks/`
- `services` → `tests/test_services/`
- `repos` or `repositories` → `tests/test_repositories/`
- `pages` → `tests/test_pages/`
- `charts` → `tests/test_charts/`

For example, if `$ARGUMENTS` is `callbacks`, run:
```
/c/Users/coryb/anaconda3/python.exe -m pytest tests/test_callbacks/ -v --tb=short
```

If `$ARGUMENTS` doesn't match a known directory, pass it directly as a pytest filter:
```
/c/Users/coryb/anaconda3/python.exe -m pytest tests/ -v --tb=short -k "$ARGUMENTS"
```

Always set `USE_SAMPLE_DATA=true` in the environment before running.

After the run, show a summary:
- Total tests passed / failed / errors
- If any failures, show the failure details
- If all pass, confirm with the count
