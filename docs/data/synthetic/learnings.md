# Learnings — Synthetic Data

**Source:** `data/synthetic/`  
**Last updated:** 2026-05-27

---

## Technical patterns

### Deterministic generation with numpy

Use `numpy.random.default_rng(seed)` instead of `numpy.random.seed(seed)` for
generators that are self-contained and don't affect global state.

```python
rng = np.random.default_rng(42)
data = rng.normal(0, 1, 100)  # reproducible
```

### Pandera + pandas 3.x compatibility

Pandera 0.31.x works with pandas 3.0.3 on Python 3.13.5. However, the
coerce/strict configuration in DataFrameModel schemas should include
`strict = False` to allow future extra columns without breaking validation.

```python
class MySchema(pa.DataFrameModel):
    class Config:
        coerce = True
        strict = False  # tolerate future columns
```

### Feature row-count assertion

Always assert that feature outputs preserve source row counts:

```python
assert len(features) == len(skus), "Records were silently dropped"
```

This catches silent merge/groupby drops early.

### Log-normal for physical dimensions

SKU volumes and weights in real DCs span orders of magnitude. Log-normal
distributions model this more realistically than uniform:

```python
unit_volume = np.maximum(0.01, rng.lognormal(mean=3.0, sigma=1.5, size=n))
```

### Utilisation capping for reporting

When computing utilisation percentages, clip at 100% for reporting but
preserve over-capacity information in a separate flag:

```python
util_pct = np.clip(occupied / capacity * 100, 0, 100)
over_capacity = occupied > capacity
```

---

## Gotchas

| Gotcha | Context | Workaround |
|--------|---------|------------|
| Pandera `lazy=True` may fail if error format changes between versions | Validation | Catch `SchemaErrors` broadly and fall back to explicit checks |
| `fillna(0)` on integer columns changes dtype to float | Feature builder | Use `.fillna(0).astype(int)` for count columns |
| `.groupby().agg()` with named aggregation returns MultiIndex columns if tuples are mixed | Aggregation | Use `reset_index()` after `agg()` to flatten |
| Phase 1 processed outputs do not persist full SKU-location placement context | Diagnostics | Phase 2 reads processed outputs plus validated synthetic source dimensions without mutating synthetic data |
| Windows PowerShell may emit Graphify query output using `cp1252` | Graphify | Set `$env:PYTHONIOENCODING='utf-8'` before Graphify queries that print arrows or other Unicode |
| Prioritization can look like recommendation if labels are ambiguous | Scoring | Use `review_*` candidate action labels and repeat that scores are not optimal move recommendations |
| Inferred weights can become hidden business policy | Scoring | Store weights in a dataclass config and copy `inferred / pending confirmation` into outputs and docs |
