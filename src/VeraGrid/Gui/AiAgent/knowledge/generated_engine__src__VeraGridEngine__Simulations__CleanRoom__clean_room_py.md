# VeraGridEngine Module: src/VeraGridEngine/Simulations/CleanRoom/clean_room.py

- Original source path: `src/VeraGridEngine/Simulations/CleanRoom/clean_room.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

Hierarchical country-scale load generator

## Module Surface

- Class count: 10
- Top-level function count: 30
- Representative imports: __future__, math, os, warnings, dataclasses, typing, matplotlib.pyplot, numpy, io, zipfile, json, torch, torch.nn, torch.nn.functional, torch.utils.data, VeraGridEngine.basic_structures

## Function: select_torch_device(prefer_cuda, verbose)

Select a safe torch device.

## Class: TimeGrid

- Bases: none
- Summary: Time grid diagnostics.

### Methods

- No methods detected.

## Function: infer_time_grid(timestamps, jitter_tol)

Infer dominant timestep and regularity from Unix timestamps.

## Function: calendar_features_unix(timestamps)

Compute resolution-independent calendar features from Unix timestamps.

## Function: ensure_2d_temp(temp)

Ensure temperature array has shape ``(T,R)``.

## Function: compute_aggregate(P)

Compute aggregate series from device matrix.

## Function: stable_shares(P, eps)

Compute per-time shares:

## Function: compute_month_index(timestamps)

Compute a month index ``0..11`` from Unix timestamps (approx).

## Class: AggregateBatch

- Bases: none
- Summary: Strongly-typed batch for the aggregate model.

### Methods

- `to(self, device)`
  Summary: Move tensors to device.

## Class: ShareBatch

- Bases: none
- Summary: Strongly-typed batch for the share model.

### Methods

- `to(self, device)`
  Summary: Move tensors to device.

## Class: AggregateDataset

- Bases: Dataset
- Summary: Random window dataset for aggregate model.

### Methods

- No methods detected.

## Class: ShareVectorDataset

- Bases: Dataset
- Summary: Dataset for simplex-constrained share vectors at time t.

### Methods

- No methods detected.

## Function: collate_aggregate(batch)

Stack AggregateBatch list into one AggregateBatch.

## Function: collate_share(batch)

Stack ShareBatch list into one ShareBatch.

## Class: SafeGRU

- Bases: nn.GRU
- Summary: GRU variant that disables cuDNN flatten_parameters path.

### Methods

- `_detect_flatten_safety(self)`
  Summary: Probe whether flatten_parameters() is safe on the current device.
- `forward(self, input, hx)`
  Summary: No docstring provided.

## Class: AggregateARModel

- Bases: nn.Module
- Summary: Aggregate one-step probabilistic model.

### Methods

- `forward(self, y_ctx, temp_hist, cal_t, temp_t)`
  Summary: :param y_ctx: Tensor ``(B,L)``.

## Class: ShareSoftmaxModel

- Bases: nn.Module
- Summary: Simplex-constrained share model.

### Methods

- `forward(self, cal_t, temp_dev_t, y_agg_t, region_id, chunk_size)`
  Summary: Compute logits for all devices.

## Function: gaussian_nll(y, mu, sigma)

Gaussian negative log-likelihood.

## Function: share_kl_loss(logits, target_share)

KL divergence between target shares and predicted shares.

## Function: train_aggregate_model(timestamps, P_agg, temp, context_len, steps, batch_size, lr, prefer_cuda, verbose, eps_agg)

Train the aggregate model.

## Function: train_share_softmax_model(timestamps, P, region_id, temp, steps, batch_size, lr, prefer_cuda, verbose, eps_share_denominator, eps_agg, chunk_size)

Train the simplex share model.

## Function: sample_aggregate(model, timestamps, temp, y_agg_init, seed, sigma_damp)

Sample y_agg(t) auto-regressively and return per-step effective sigma.

## Function: lognormal_mean_correction(y, sigma_eff)

Apply log-normal mean correction when mapping y to power:

## Function: anchor_log_mean_global(y_syn, y_real)

Anchor synthetic log-series to match the real mean (global).

## Function: anchor_log_mean_monthly(y_syn, y_real, timestamps)

Anchor synthetic log-series to match real mean per month.

## Function: sample_shares_softmax(model, timestamps, region_id, temp, y_agg, seed, logit_noise_std, chunk_size)

Sample shares s(t,:) using softmax(logits + noise), ensuring simplex constraints.

## Function: reconstruct_power_from_shares(P_agg, shares)

Reconstruct device powers from aggregate and shares.

## Function: save_artifact(path, payload)

Save payload via torch.save.

## Function: load_artifact(path, map_location)

Load payload via torch.load.

## Function: load_or_train_hierarchical(artifact_path, timestamps, P, region_id, temp, context_len, steps_agg, steps_share, batch_size_agg, batch_size_share, lr_agg, lr_share, prefer_cuda, verbose, eps_agg, eps_share_denominator, jitter_tol, share_chunk_size)

Load or train hierarchical artifact (aggregate + simplex shares).

## Function: generate_synthetic(agg_model, share_model, timestamps, P_real, region_id, temp, context_len, seed, eps_agg, sigma_damp, anchoring, logit_noise_std, share_chunk_size)

Generate synthetic aggregate and device series.

## Function: plot_losses(losses, title)

Plot training loss curve.

## Function: plot_aggregate_real_vs_syn(P_agg_real, P_agg_syn, max_points, title)

Plot aggregate series real vs synthetic.

## Function: plot_share_sum_sanity(P_syn, P_agg_syn, max_points, title)

Plot sanity check: sum_i P_syn(t,i) / P_agg_syn(t). Should be ~1.

## Function: plot_devices_real_vs_syn(P_real, P_syn, devices, max_points, title)

Plot selected devices real vs synthetic.

## Class: HierarchicalZipSpec

- Bases: none
- Summary: Serializable, future-safe spec for training and generation.

### Methods

- No methods detected.

## Class: HierarchicalZipArtifact

- Bases: none
- Summary: Orchestrates training, prediction, and durable ZIP save/load for the

### Methods

- `train(self, timestamps, P, region_id, temp)`
  Summary: Train both aggregate and share models.
- `predict(self, timestamps, temp, region_id, y_agg_init, seed)`
  Summary: Generate synthetic device powers (T,N).
- `save(self, zip_path)`
  Summary: Save a ZIP artifact containing:
- `load(cls, zip_path, map_location)`
  Summary: Load from a ZIP artifact produced by save().

## Function: demo()

No docstring provided.

## Function: _make_synthetic_demo_data(T, N, R, seed)

Create a small synthetic dataset so the demo can run standalone.

## Function: demo2()

No docstring provided.
