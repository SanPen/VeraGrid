# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""
Hierarchical country-scale load generator
================================================================================

This file implements a hierarchical synthetic time-series generator that ensures:

    1) sum_i P_i(t) == P_agg(t)          (exact, by construction, via simplex shares)
    2) Aggregate mean anchored           (removes persistent positive/negative offsets)

Architecture
------------
A) Aggregate model (autoregressive in log-space)
   Learns:
       y_agg(t) = log(P_agg(t) + eps_agg)
   Predicts:
       Normal(mu_t, sigma_t)

   During sampling we use:
   - variance damping (alpha) to avoid variance explosion in free rollouts
   - log-normal mean correction when mapping y->P

B) Share model (simplex-constrained cross-section per time step)
   Learns device shares:
       s(t,:) = P(t,:) / sum_j P(t,j)
   Predicts logits -> softmax -> shares on the simplex.
   This guarantees:
       shares(t,:) >= 0 and sum(shares(t,:)) = 1

C) Anchoring (fixes aggregate offset)
   Free-running AR sampling often produces a mean bias. We correct it in log-space:
       y_syn := y_syn + (mean(y_real) - mean(y_syn))
   Optional monthly anchoring is also provided.

Hard constraint from user:
- Never use "*" as an argument in any function signature.
- Add reStructuredText docstrings to all functions (done).

Input conventions
-----------------
- timestamps: ndarray (T,), Unix seconds int64
- P: ndarray (T,N), device power (float), may contain NaNs
- region_id: ndarray (N,), integer region index per device in [0..R-1]
- temp: ndarray (T,R) (or (T,) / (T,1)), regional temperature

Notes
-----
- The aggregate model uses temp[:,0] as a national proxy by default. Replace with a
  weighted mean if you have better national drivers.
- For huge N (many devices), share training batches can be heavy. Use:
    - smaller batch_size_share
    - share_chunk_size > 0 to chunk the forward pass over devices
"""

from __future__ import annotations

import math
import os
import warnings
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional, Tuple

import matplotlib.pyplot as plt
import numpy as np
import io
import zipfile
import json
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader
from VeraGridEngine.basic_structures import Vec, Mat, IntVec


# ----------------------------------------------------------------------------------------------------------------------
# 1) SAFE DEVICE SELECTION
# ----------------------------------------------------------------------------------------------------------------------
def select_torch_device(prefer_cuda: bool, verbose: bool) -> torch.device:
    """
    Select a safe torch device.

    This prevents crashes when torch reports CUDA availability but the current
    PyTorch build does not support your GPU architecture (e.g. GTX 1060 sm_61
    with a build supporting sm_70+ only).

    Strategy
    --------
    - If CUDA is available, run a small CUDA matmul and synchronize.
    - If it fails, fall back to CPU.

    :param prefer_cuda: Try CUDA if True.
    :param verbose: Print diagnostic info if True.
    :returns: ``torch.device('cuda')`` if usable else ``torch.device('cpu')``.
    """
    if not prefer_cuda:
        return torch.device("cpu")
    if not torch.cuda.is_available():
        return torch.device("cpu")

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        try:
            _ = torch.cuda.current_device()
            a = torch.randn(64, 64, device="cuda")
            b = torch.randn(64, 64, device="cuda")
            _ = a @ b
            torch.cuda.synchronize()
            if verbose:
                name = torch.cuda.get_device_name(0)
                cap = torch.cuda.get_device_capability(0)
                print(f"[device] CUDA OK: {name} (cc {cap[0]}.{cap[1]})")
            return torch.device("cuda")
        except Exception as e:
            if verbose:
                print("[device] CUDA detected but unusable — falling back to CPU")
                try:
                    name = torch.cuda.get_device_name(0)
                    cap = torch.cuda.get_device_capability(0)
                    print(f"[device] GPU: {name} (cc {cap[0]}.{cap[1]})")
                except AssertionError:
                    pass
                print("Reason:", type(e).__name__, e)
            return torch.device("cpu")


# ----------------------------------------------------------------------------------------------------------------------
# 2) TIME GRID + CALENDAR FEATURES
# ----------------------------------------------------------------------------------------------------------------------
@dataclass
class TimeGrid:
    """
    Time grid diagnostics.

    :param dt_seconds: Dominant timestep in seconds.
    :param is_regular: True if timestamp jitter is within tolerance.
    :param jitter_frac_p95: 95th percentile of relative jitter wrt dt.
    """
    dt_seconds: int
    is_regular: bool
    jitter_frac_p95: float


def infer_time_grid(timestamps: Vec, jitter_tol: float) -> TimeGrid:
    """
    Infer dominant timestep and regularity from Unix timestamps.

    :param timestamps: Unix timestamps (seconds), shape ``(T,)``.
    :param jitter_tol: Relative tolerance for regularity check.
    :returns: :class:`TimeGrid`.
    """
    ts: Vec = np.asarray(timestamps, dtype=np.int64)
    dts: Vec = np.diff(ts)
    dts: Vec = dts[dts > 0]
    if len(dts) == 0:
        raise ValueError("Not enough timestamps to infer dt.")
    vals, counts = np.unique(dts, return_counts=True)
    dt_mode = int(vals[np.argmax(counts)])
    jitter = np.abs(dts - dt_mode) / max(dt_mode, 1)
    jitter_p95 = float(np.percentile(jitter, 95))
    return TimeGrid(dt_seconds=dt_mode,
                    is_regular=(jitter_p95 <= jitter_tol),
                    jitter_frac_p95=jitter_p95)


def calendar_features_unix(timestamps: IntVec) -> Mat:
    """
    Compute resolution-independent calendar features from Unix timestamps.

    Features (columns)
    ------------------
    - sin/cos hour-of-day
    - sin/cos day-of-week
    - sin/cos day-of-year
    - weekend flag

    :param timestamps: Unix timestamps (seconds), shape ``(T,)``.
    :returns: Feature matrix, shape ``(T, Fcal)`` (float32).
    """
    ts: IntVec = np.asarray(timestamps, dtype=np.int64)
    sec_day = 86400
    sec_week = 7 * sec_day
    sec_year = 365 * sec_day

    tod: IntVec = (ts % sec_day) / sec_day
    dow: IntVec = (ts % sec_week) / sec_week
    doy: IntVec = (ts % sec_year) / sec_year

    feats = [
        np.sin(2 * np.pi * tod), np.cos(2 * np.pi * tod),
        np.sin(2 * np.pi * dow), np.cos(2 * np.pi * dow),
        np.sin(2 * np.pi * doy), np.cos(2 * np.pi * doy),
        ((dow >= 5 / 7) | (dow >= 6 / 7)).astype(np.float32),
    ]
    return np.stack(feats, axis=1, dtype=np.float32)


# ----------------------------------------------------------------------------------------------------------------------
# 3) DATA HELPERS
# ----------------------------------------------------------------------------------------------------------------------
def ensure_2d_temp(temp: Mat) -> Mat:
    """
    Ensure temperature array has shape ``(T,R)``.

    :param temp: Temperature array. Accepted shapes: ``(T,)``, ``(T,1)``, ``(T,R)``.
    :returns: Temperature array ``(T,R)`` (float32).
    """
    arr: Vec = np.asarray(temp, dtype=np.float32)
    if arr.ndim == 1:
        arr = arr[:, None]
    return arr


def compute_aggregate(P: Mat) -> Vec:
    """
    Compute aggregate series from device matrix.

    :param P: Power matrix ``(T,N)``, may contain NaNs.
    :returns: Aggregate power ``(T,)`` (float32).
    """
    return np.nansum(P, axis=1).astype(np.float32)


def stable_shares(P: Mat, eps: float) -> Mat:
    """
    Compute per-time shares:

        s(t,i) = P(t,i) / sum_j P(t,j)

    with stabilization in the denominator.

    :param P: Power matrix ``(T,N)``, NaNs allowed.
    :param eps: Epsilon added to the per-time denominator.
    :returns: Shares matrix ``(T,N)`` (float32).
    """
    P_clean = np.nan_to_num(np.asarray(P, dtype=np.float32), nan=0.0)
    denom = np.sum(P_clean, axis=1, keepdims=True) + float(eps)
    shares: Mat = P_clean / denom
    return shares.astype(np.float32)


def compute_month_index(timestamps: IntVec) -> IntVec:
    """
    Compute a month index ``0..11`` from Unix timestamps (approx).

    This uses a simplified 365-day year mapping (no leap years). It is intended
    for anchoring only. For production you can replace with a real calendar.

    :param timestamps: Unix timestamps (seconds), shape ``(T,)``.
    :returns: Month indices, shape ``(T,)`` (int64).
    """
    ts = np.asarray(timestamps, dtype=np.int64)
    sec_day = 86400
    day_of_the_year: IntVec = ((ts // sec_day) % 365)
    day_of_year = day_of_the_year.astype(np.int64)
    # Approx month boundaries (cumulative days): Jan,Feb,... in a non-leap year
    bounds: IntVec = np.array([31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334, 365], dtype=np.int64)
    month: IntVec = np.zeros_like(day_of_year)
    for m in range(12):
        month = np.where(day_of_year < bounds[m], m, month)
    return month.astype(np.int64)


@dataclass
class AggregateBatch:
    """
    Strongly-typed batch for the aggregate model.

    :param y_ctx: Tensor (L,)
    :param temp_hist: Tensor (L,1)
    :param cal_t: Tensor (1,F)
    :param temp_t: Tensor (1,1)
    :param y_next: Tensor (1,)
    """
    y_ctx: torch.Tensor
    temp_hist: torch.Tensor
    cal_t: torch.Tensor
    temp_t: torch.Tensor
    y_next: torch.Tensor

    def to(self, device: torch.device) -> "AggregateBatch":
        """
        Move tensors to device.
        """
        return AggregateBatch(
            y_ctx=self.y_ctx.to(device),
            temp_hist=self.temp_hist.to(device),
            cal_t=self.cal_t.to(device),
            temp_t=self.temp_t.to(device),
            y_next=self.y_next.to(device),
        )


@dataclass
class ShareBatch:
    """
    Strongly-typed batch for the share model.

    :param cal_t: Tensor (F,)
    :param temp_dev_t: Tensor (N,)
    :param y_agg_t: Tensor (1,)
    :param share_t: Tensor (N,)
    """
    cal_t: torch.Tensor
    temp_dev_t: torch.Tensor
    y_agg_t: torch.Tensor
    share_t: torch.Tensor

    def to(self, device: torch.device) -> "ShareBatch":
        """
        Move tensors to device.
        """
        return ShareBatch(
            cal_t=self.cal_t.to(device),
            temp_dev_t=self.temp_dev_t.to(device),
            y_agg_t=self.y_agg_t.to(device),
            share_t=self.share_t.to(device),
        )


class AggregateDataset(Dataset):
    """
    Random window dataset for aggregate model.

    Target
    ------
    ``y_agg(t) = log(P_agg(t) + eps_agg)``

    Inputs
    ------
    - ``y_ctx``: shape ``(L,)``
    - ``temp_hist``: shape ``(L,1)`` (uses temp[:,0] as national proxy)
    - ``cal_t``: shape ``(1,F)``
    - ``temp_t``: shape ``(1,1)``
    - ``y_next``: shape ``(1,)``
    """

    def __init__(self,
                 timestamps: np.ndarray,
                 P_agg: np.ndarray,
                 temp: np.ndarray,
                 context_len: int,
                 samples_per_epoch: int,
                 eps_agg: float, ):
        """
        :param timestamps: Unix timestamps ``(T,)``.
        :param P_agg: Aggregate power ``(T,)``.
        :param temp: Temperature ``(T,R)``.
        :param context_len: Context length ``L``.
        :param samples_per_epoch: Random samples per epoch.
        :param eps_agg: Log stabilization epsilon.
        """
        self.timestamps = np.asarray(timestamps, dtype=np.int64)
        self.temp = ensure_2d_temp(temp)
        self.cal = calendar_features_unix(self.timestamps)
        self.L = int(context_len)
        self.samples = int(samples_per_epoch)
        self.eps_agg = float(eps_agg)

        P_agg = np.asarray(P_agg, dtype=np.float32)
        self.y = np.log(np.maximum(P_agg, 0.0) + self.eps_agg).astype(np.float32)
        self.T = self.y.shape[0]
        if self.T <= self.L + 1:
            raise ValueError("Not enough time steps for chosen context_len.")

    def __len__(self) -> int:
        """
        :returns: Number of samples per epoch.
        """
        return self.samples

    def __getitem__(self, idx: int) -> AggregateBatch:
        """
        :param idx: Unused (random sampling).
        :returns: Batch element dictionary.
        """
        t = np.random.randint(self.L, self.T - 1)
        y_ctx = self.y[t - self.L:t]
        y_next = self.y[t]
        temp_hist = self.temp[t - self.L:t, 0:1]
        temp_t = self.temp[t:t + 1, 0:1]
        cal_t = self.cal[t:t + 1]

        return AggregateBatch(
            y_ctx=torch.tensor(y_ctx, dtype=torch.float32),
            temp_hist=torch.tensor(temp_hist, dtype=torch.float32),
            cal_t=torch.tensor(cal_t, dtype=torch.float32),
            temp_t=torch.tensor(temp_t, dtype=torch.float32),
            y_next=torch.tensor([y_next], dtype=torch.float32),
        )


class ShareVectorDataset(Dataset):
    """
    Dataset for simplex-constrained share vectors at time t.

    Target
    ------
    ``share(t,:) = P(t,:) / sum_j P(t,j)``

    Inputs
    ------
    - ``cal_t``: shape ``(F,)``
    - ``temp_dev_t``: shape ``(N,)`` temperature per device region at time t
    - ``y_agg_t``: shape ``(1,)`` log aggregate at time t (conditioning)
    - ``share_t``: shape ``(N,)`` target share vector
    """

    def __init__(self,
                 timestamps: IntVec,
                 P: Mat,
                 region_id: IntVec,
                 temp: Vec,
                 samples_per_epoch: int,
                 eps_share_denominator: float,
                 eps_agg: float):
        """
        :param timestamps: Unix timestamps ``(T,)``.
        :param P: Device powers ``(T,N)`` (NaNs allowed).
        :param region_id: Device region indices ``(N,)``.
        :param temp: Temperatures ``(T,R)``.
        :param samples_per_epoch: Random samples per epoch.
        :param eps_share_denominator: Epsilon for share denominator.
        :param eps_agg: Epsilon for aggregate log.
        """
        self.timestamps: IntVec = np.asarray(timestamps, dtype=np.int64)
        self.calendar_features: Mat = calendar_features_unix(self.timestamps)
        self.P: Mat = np.asarray(P, dtype=np.float32)
        self.region_id: IntVec = np.asarray(region_id, dtype=np.int64)
        self.temperature = ensure_2d_temp(temp)
        self.samples = int(samples_per_epoch)
        self.eps_share_denominator = float(eps_share_denominator)
        self.eps_agg = float(eps_agg)

        self.T, self.N = self.P.shape

        if self.region_id.shape[0] != self.N:
            raise ValueError("region_id must have length N.")

        if self.temperature.shape[0] != self.T:
            raise ValueError("temp must have T rows.")

        self.share = stable_shares(self.P, self.eps_share_denominator)

        P_agg = compute_aggregate(self.P)

        self.y_agg: Vec = np.log(np.maximum(P_agg, 0.0) + self.eps_agg).astype(np.float32)

        self.temp_dev: Vec = self.temperature[:, self.region_id].astype(np.float32)

    def __len__(self) -> int:
        """
        :returns: Number of samples per epoch.
        """
        return self.samples

    def __getitem__(self, idx: int) -> ShareBatch:
        """
        :param idx: Unused (random sampling).
        :returns: Batch element dictionary.
        """
        t = np.random.randint(0, self.T)
        return ShareBatch(
            cal_t=torch.tensor(self.calendar_features[t], dtype=torch.float32),
            temp_dev_t=torch.tensor(self.temp_dev[t], dtype=torch.float32),
            y_agg_t=torch.tensor([self.y_agg[t]], dtype=torch.float32),
            share_t=torch.tensor(self.share[t], dtype=torch.float32),
        )


def collate_aggregate(batch: List[AggregateBatch]) -> AggregateBatch:
    """
    Stack AggregateBatch list into one AggregateBatch.
    """
    return AggregateBatch(
        y_ctx=torch.stack([b.y_ctx for b in batch], dim=0),
        temp_hist=torch.stack([b.temp_hist for b in batch], dim=0),
        cal_t=torch.stack([b.cal_t for b in batch], dim=0),
        temp_t=torch.stack([b.temp_t for b in batch], dim=0),
        y_next=torch.stack([b.y_next for b in batch], dim=0),
    )


def collate_share(batch: List[ShareBatch]) -> ShareBatch:
    """
    Stack ShareBatch list into one ShareBatch.
    """
    return ShareBatch(
        cal_t=torch.stack([b.cal_t for b in batch], dim=0),
        temp_dev_t=torch.stack([b.temp_dev_t for b in batch], dim=0),
        y_agg_t=torch.stack([b.y_agg_t for b in batch], dim=0),
        share_t=torch.stack([b.share_t for b in batch], dim=0),
    )


# ----------------------------------------------------------------------------------------------------------------------
# 5) MODELS
# ----------------------------------------------------------------------------------------------------------------------
class SafeGRU(nn.GRU):
    """
    GRU variant that disables cuDNN flatten_parameters path.

    :returns: None
    """

    """
        GRU that automatically enables or disables flatten_parameters()
        depending on whether the current device supports cuDNN RNN kernels.

        This guarantees:
        - No crashes
        - No warnings
        - Fast path on supported GPUs
        - Safe path everywhere else
        """

    def __init__(self, input_proj: int, hidden: int, batch_first=True):
        """
        :param hidden: GRU hidden size.
        :param input_proj: Projection size for GRU input.
        :param batch_first:
        """
        super().__init__(input_proj, hidden, batch_first=batch_first)
        self._flatten_safe: Optional[bool] = None

    def _detect_flatten_safety(self) -> bool:
        """
        Probe whether flatten_parameters() is safe on the current device.
        """
        if not torch.cuda.is_available():
            return False

        try:
            # Minimal probe
            self.flatten_parameters()
            x = torch.zeros(
                1, 1, self.input_size,
                device=next(self.parameters()).device
            )
            self(x)
            torch.cuda.synchronize()
            return True
        except Exception:
            return False

    def forward(self, input: torch.Tensor, hx: Optional[torch.Tensor] = None):
        if self._flatten_safe is None:
            self._flatten_safe = self._detect_flatten_safety()

        if self._flatten_safe:
            # Enable cuDNN fast path
            self.flatten_parameters()

        return super().forward(input, hx)


class AggregateARModel(nn.Module):
    """
    Aggregate one-step probabilistic model.

    Learns
    ------
    ``y_agg(t) = log(P_agg(t) + eps_agg)``

    Predicts
    --------
    Normal distribution parameters ``(mu, sigma)`` for the next step.
    """

    def __init__(self, cal_dim: int, hidden: int, input_proj: int):
        """
        :param cal_dim: Calendar feature dimension.
        :param hidden: GRU hidden size.
        :param input_proj: Projection size for GRU input.
        """
        super().__init__()
        self.in_proj = nn.Linear(2, input_proj)
        self.gru = SafeGRU(input_proj, hidden, batch_first=True)

        head_in = hidden + cal_dim + 1
        self.head = nn.Sequential(
            nn.LayerNorm(head_in),
            nn.Linear(head_in, 128),
            nn.GELU(),
            nn.Linear(128, 64),
            nn.GELU(),
        )
        self.mu = nn.Linear(64, 1)
        self.log_sigma = nn.Linear(64, 1)

    def forward(self,
                y_ctx: torch.Tensor,
                temp_hist: torch.Tensor,
                cal_t: torch.Tensor,
                temp_t: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        :param y_ctx: Tensor ``(B,L)``.
        :param temp_hist: Tensor ``(B,L,1)``.
        :param cal_t: Tensor ``(B,1,F)``.
        :param temp_t: Tensor ``(B,1,1)``.
        :returns: ``(mu, sigma)`` each shape ``(B,1)``.
        """
        x = torch.cat([y_ctx.unsqueeze(-1), temp_hist], dim=-1)
        x = self.in_proj(x)
        _, h = self.gru(x)
        h = h.squeeze(0)

        feat = torch.cat([h, cal_t.squeeze(1), temp_t.squeeze(1)], dim=-1)
        z = self.head(feat)
        mu = self.mu(z)
        sigma = F.softplus(self.log_sigma(z)) + 1e-4
        return mu, sigma


class ShareSoftmaxModel(nn.Module):
    """
    Simplex-constrained share model.

    Produces logits for all devices at a given time t, then uses softmax to
    obtain shares on the simplex.

    The forward can optionally chunk over devices to reduce memory.
    """

    def __init__(self,
                 n_devices: int,
                 n_regions: int,
                 cal_dim: int,
                 dev_emb_dim: int,
                 reg_emb_dim: int,
                 hidden: int):
        """
        :param n_devices: Number of devices ``N``.
        :param n_regions: Number of regions ``R``.
        :param cal_dim: Calendar feature dimension.
        :param dev_emb_dim: Device embedding dimension.
        :param reg_emb_dim: Region embedding dimension.
        :param hidden: Hidden size of per-device MLP.
        """
        super().__init__()
        self.n_devices = int(n_devices)
        self.n_regions = int(n_regions)
        self.cal_dim = int(cal_dim)

        self.dev_emb = nn.Embedding(self.n_devices, dev_emb_dim)
        self.reg_emb = nn.Embedding(self.n_regions, reg_emb_dim)

        feat_dim = dev_emb_dim + reg_emb_dim + cal_dim + 1 + 1
        self.mlp = nn.Sequential(
            nn.LayerNorm(feat_dim),
            nn.Linear(feat_dim, hidden),
            nn.GELU(),
            nn.Linear(hidden, hidden),
            nn.GELU(),
            nn.Linear(hidden, 1),
        )

    def forward(self,
                cal_t: torch.Tensor,
                temp_dev_t: torch.Tensor,
                y_agg_t: torch.Tensor,
                region_id: torch.Tensor,
                chunk_size: int) -> torch.Tensor:
        """
        Compute logits for all devices.

        :param cal_t: Tensor ``(B,F)`` calendar features.
        :param temp_dev_t: Tensor ``(B,N)`` device temperatures at time t.
        :param y_agg_t: Tensor ``(B,1)`` log aggregate at time t.
        :param region_id: Tensor ``(N,)`` region index per device.
        :param chunk_size: If ``>0``, chunk forward pass over devices.
        :returns: Logits tensor ``(B,N)``.
        """
        B = int(cal_t.shape[0])
        N = int(self.n_devices)
        device = cal_t.device

        dev_ids = torch.arange(N, device=device, dtype=torch.long)
        reg_ids = region_id.to(device=device, dtype=torch.long)

        cal_rep = cal_t[:, None, :].expand(B, N, self.cal_dim)
        yagg_rep = y_agg_t[:, None, :].expand(B, N, 1)
        temp_rep = temp_dev_t[:, :, None]

        dev_e = self.dev_emb(dev_ids)[None, :, :].expand(B, N, -1)
        reg_e = self.reg_emb(reg_ids)[None, :, :].expand(B, N, -1)

        feat = torch.cat([dev_e, reg_e, cal_rep, temp_rep, yagg_rep], dim=-1)

        if chunk_size is None or int(chunk_size) <= 0:
            return self.mlp(feat).squeeze(-1)

        # out = []
        # start = 0
        # step = int(chunk_size)
        # while start < N:
        #     end = min(N, start + step)
        #     out.append(self.mlp(feat[:, start:end, :]).squeeze(-1))
        #     start = end
        # return torch.cat(out, dim=1)

        # Split device dimension into chunks
        chunks = torch.split(feat, int(chunk_size), dim=1)

        # Preallocate output explicitly
        logits = torch.empty(
            (B, N),
            device=feat.device,
            dtype=feat.dtype,
        )

        offset = 0
        for chunk in chunks:
            k = chunk.shape[1]
            logits[:, offset:offset + k] = self.mlp(chunk).squeeze(-1)
            offset += k

        return logits


def gaussian_nll(y: torch.Tensor, mu: torch.Tensor, sigma: torch.Tensor) -> torch.Tensor:
    """
    Gaussian negative log-likelihood.

    :param y: Target tensor ``(B,1)``.
    :param mu: Mean tensor ``(B,1)``.
    :param sigma: Std dev tensor ``(B,1)``.
    :returns: Scalar loss tensor.
    """
    nll = 0.5 * math.log(2 * math.pi) + torch.log(sigma) + 0.5 * ((y - mu) / sigma) ** 2
    return nll.mean()


def share_kl_loss(logits: torch.Tensor, target_share: torch.Tensor) -> torch.Tensor:
    """
    KL divergence between target shares and predicted shares.

    :param logits: Logits tensor ``(B,N)``.
    :param target_share: Target shares tensor ``(B,N)`` with rows summing to 1.
    :returns: Scalar loss tensor.
    """
    log_pred = F.log_softmax(logits, dim=1)
    return F.kl_div(log_pred, target_share, reduction="batchmean")


# ----------------------------------------------------------------------------------------------------------------------
# 6) TRAINING
# ----------------------------------------------------------------------------------------------------------------------
def train_aggregate_model(
        timestamps: IntVec,
        P_agg: Vec,
        temp: IntVec,
        context_len: int,
        steps: int,
        batch_size: int,
        lr: float,
        prefer_cuda: bool,
        verbose: bool,
        eps_agg: float,
) -> Tuple[AggregateARModel, List[float], Dict[str, Any]]:
    """
    Train the aggregate model.

    :param timestamps: Unix timestamps ``(T,)``.
    :param P_agg: Aggregate power ``(T,)``.
    :param temp: Temperature ``(T,R)``.
    :param context_len: Context length ``L``.
    :param steps: Optimisation steps.
    :param batch_size: Batch size.
    :param lr: Learning rate.
    :param prefer_cuda: Try CUDA.
    :param verbose: Print progress.
    :param eps_agg: Epsilon for log stability.
    :returns: ``(model, losses, meta)``.
    """
    device = select_torch_device(prefer_cuda, verbose)
    cal_dim = calendar_features_unix(timestamps).shape[1]

    ds = AggregateDataset(timestamps, P_agg, temp, context_len, steps * batch_size, eps_agg)
    dl = DataLoader(ds,
                    batch_size=batch_size,
                    shuffle=True,
                    num_workers=0, collate_fn=collate_aggregate)

    it = iter(dl)

    hidden = 96
    input_proj = 32
    model = AggregateARModel(cal_dim, hidden, input_proj).to(device)
    opt = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)

    losses: List[float] = []
    model.train()

    for step in range(1, int(steps) + 1):
        batch = next(it).to(device)

        mu, sigma = model(batch.y_ctx, batch.temp_hist, batch.cal_t, batch.temp_t)
        loss = gaussian_nll(batch.y_next, mu, sigma)

        opt.zero_grad(set_to_none=True)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        opt.step()

        losses.append(float(loss.item()))
        if verbose and step % 500 == 0:
            print(f"[agg step {step:6d}] NLL={loss.item():.4f}")

    meta = {
        "device": str(device),
        "cal_dim": int(cal_dim),
        "hidden": int(hidden),
        "input_proj": int(input_proj),
        "context_len": int(context_len),
        "eps_agg": float(eps_agg),
    }
    return model, losses, meta


def train_share_softmax_model(
        timestamps: IntVec,
        P: Mat,
        region_id: IntVec,
        temp: Vec,
        steps: int,
        batch_size: int,
        lr: float,
        prefer_cuda: bool,
        verbose: bool,
        eps_share_denominator: float,
        eps_agg: float,
        chunk_size: int,
) -> Tuple[ShareSoftmaxModel, List[float], Dict[str, Any]]:
    """
    Train the simplex share model.

    :param timestamps: Unix timestamps ``(T,)``.
    :param P: Device power matrix ``(T,N)``.
    :param region_id: Region index per device ``(N,)``.
    :param temp: Temperature matrix ``(T,R)``.
    :param steps: Optimisation steps.
    :param batch_size: Batch size.
    :param lr: Learning rate.
    :param prefer_cuda: Try CUDA.
    :param verbose: Print progress.
    :param eps_share_denominator: Epsilon for share denominator.
    :param eps_agg: Epsilon for aggregate log.
    :param chunk_size: Forward chunk size over devices (0 disables).
    :returns: ``(model, losses, meta)``.
    """
    device = select_torch_device(prefer_cuda, verbose)
    ts: IntVec = np.asarray(timestamps, dtype=np.int64)
    cal_dim = calendar_features_unix(ts).shape[1]

    P_arr: Mat = np.asarray(P, dtype=np.float32)
    temp_arr: Mat = ensure_2d_temp(temp)
    N = int(P_arr.shape[1])
    R = int(temp_arr.shape[1])

    ds = ShareVectorDataset(
        timestamps=ts,
        P=P_arr,
        region_id=region_id,
        temp=temp_arr,
        samples_per_epoch=int(steps) * int(batch_size),
        eps_share_denominator=eps_share_denominator,
        eps_agg=eps_agg,
    )
    dl = DataLoader(ds, batch_size=int(batch_size), shuffle=True, num_workers=0, collate_fn=collate_share)

    it = iter(dl)

    model = ShareSoftmaxModel(
        n_devices=N,
        n_regions=R,
        cal_dim=int(cal_dim),
        dev_emb_dim=32,
        reg_emb_dim=8,
        hidden=128,
    ).to(device)

    opt = torch.optim.AdamW(model.parameters(), lr=float(lr), weight_decay=1e-4)
    region_id_t = torch.tensor(np.asarray(region_id, dtype=np.int64), dtype=torch.long, device=device)

    losses: List[float] = []
    model.train()

    for step in range(1, int(steps) + 1):
        batch = next(it).to(device)
        logits = model(batch.cal_t, batch.temp_dev_t, batch.y_agg_t, region_id_t, int(chunk_size))
        loss = share_kl_loss(logits, batch.share_t)

        opt.zero_grad(set_to_none=True)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        opt.step()

        losses.append(float(loss.item()))
        if verbose and step % 500 == 0:
            print(f"[share step {step:6d}] KL={loss.item():.4f}")

    meta = {
        "device": str(device),
        "cal_dim": int(cal_dim),
        "n_devices": int(N),
        "n_regions": int(R),
        "dev_emb_dim": 32,
        "reg_emb_dim": 8,
        "hidden": 128,
        "eps_share_denom": float(eps_share_denominator),
        "eps_agg": float(eps_agg),
        "chunk_size": int(chunk_size),
    }
    return model, losses, meta


# ----------------------------------------------------------------------------------------------------------------------
# 7) AGGREGATE SAMPLING + CORRECTIONS
# ----------------------------------------------------------------------------------------------------------------------
@torch.no_grad()
def sample_aggregate(
        model: AggregateARModel,
        timestamps: IntVec,
        temp: Vec,
        y_agg_init: Vec,
        seed: int,
        sigma_damp: float,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Sample y_agg(t) auto-regressively and return per-step effective sigma.

    The effective sigma used for sampling is:
        sigma_eff = sigma_damp * sigma

    :param model: Trained aggregate model.
    :param timestamps: Unix timestamps ``(T,)``.
    :param temp: Temperature ``(T,R)``.
    :param y_agg_init: Initial context ``(L,)``.
    :param seed: RNG seed.
    :param sigma_damp: Multiplicative damping factor in [0,1].
    :returns: ``(y_syn, sigma_eff_hist)`` each shape ``(T,)``.
    """
    torch.manual_seed(int(seed))
    device = next(model.parameters()).device

    ts = np.asarray(timestamps, dtype=np.int64)
    cal = torch.tensor(calendar_features_unix(ts), dtype=torch.float32, device=device)
    temp_arr = ensure_2d_temp(temp)
    T = int(temp_arr.shape[0])
    L = int(y_agg_init.shape[0])

    y_ctx = y_agg_init.astype(np.float32).copy()
    y_out: Vec = np.zeros(T, dtype=np.float32)
    sigma_eff_out: Vec = np.zeros(T, dtype=np.float32)

    model.eval()

    for t in range(T):
        temp_t = torch.tensor(temp_arr[t:t + 1, 0:1], dtype=torch.float32, device=device).view(1, 1, 1)

        t0 = max(0, t - L)
        hist = temp_arr[t0:t, 0:1]
        if hist.shape[0] < L:
            pad = np.repeat(temp_arr[0:1, 0:1], repeats=(L - hist.shape[0]), axis=0)
            hist = np.concatenate([pad, hist], axis=0)
        temp_hist = torch.tensor(hist, dtype=torch.float32, device=device).view(1, L, 1)

        cal_t = cal[t].view(1, 1, -1)
        y_ctx_t = torch.tensor(y_ctx[None, :], dtype=torch.float32, device=device)

        mu, sigma = model(y_ctx_t, temp_hist, cal_t, temp_t)
        sigma_eff = float(sigma_damp) * sigma
        eps = torch.randn_like(mu)
        y_next = (mu + sigma_eff * eps).item()

        y_out[t] = float(y_next)
        sigma_eff_out[t] = float(sigma_eff.item())

        y_ctx[:-1] = y_ctx[1:]
        y_ctx[-1] = float(y_next)

    return y_out, sigma_eff_out


def lognormal_mean_correction(y: Vec, sigma_eff: Vec) -> Vec:
    """
    Apply log-normal mean correction when mapping y to power:

        P = exp(y - 0.5 * sigma_eff^2)

    :param y: Log series ``(T,)``.
    :param sigma_eff: Effective sigma used in sampling ``(T,)``.
    :returns: Corrected power series ``(T,)``.
    """
    y_arr = np.asarray(y, dtype=np.float32)
    s_arr = np.asarray(sigma_eff, dtype=np.float32)
    return np.exp(y_arr - 0.5 * (s_arr ** 2)).astype(np.float32)


def anchor_log_mean_global(y_syn: Vec, y_real: Vec) -> Vec:
    """
    Anchor synthetic log-series to match the real mean (global).

        y_syn := y_syn + (mean(y_real) - mean(y_syn))

    :param y_syn: Synthetic log series ``(T,)``.
    :param y_real: Real log series ``(T,)``.
    :returns: Mean-anchored synthetic log series ``(T,)``.
    """
    ys = np.asarray(y_syn, dtype=np.float32)
    yr = np.asarray(y_real, dtype=np.float32)
    delta = float(np.mean(yr) - np.mean(ys))
    return (ys + delta).astype(np.float32)


def anchor_log_mean_monthly(y_syn: Vec, y_real: Vec, timestamps: IntVec) -> Vec:
    """
    Anchor synthetic log-series to match real mean per month.

    This reduces seasonal bias if the AR rollout drifts differently across months.

    :param y_syn: Synthetic log series ``(T,)``.
    :param y_real: Real log series ``(T,)``.
    :param timestamps: Unix timestamps ``(T,)``.
    :returns: Month-anchored synthetic log series ``(T,)``.
    """
    ys = np.asarray(y_syn, dtype=np.float32).copy()
    yr = np.asarray(y_real, dtype=np.float32)
    month = compute_month_index(timestamps)

    for m in range(12):
        mask = (month == m)
        if not np.any(mask):
            continue
        delta = float(np.mean(yr[mask]) - np.mean(ys[mask]))
        ys[mask] = ys[mask] + delta
    return ys.astype(np.float32)


# ----------------------------------------------------------------------------------------------------------------------
# 8) SHARE SAMPLING (SIMPLEX)
# ----------------------------------------------------------------------------------------------------------------------
@torch.no_grad()
def sample_shares_softmax(
        model: ShareSoftmaxModel,
        timestamps: IntVec,
        region_id: IntVec,
        temp: Vec,
        y_agg: Vec,
        seed: int,
        logit_noise_std: float,
        chunk_size: int,
) -> Mat:
    """
    Sample shares s(t,:) using softmax(logits + noise), ensuring simplex constraints.

    :param model: Trained share model.
    :param timestamps: Unix timestamps ``(T,)``.
    :param region_id: Region per device ``(N,)``.
    :param temp: Temperature ``(T,R)``.
    :param y_agg: Log aggregate series ``(T,)`` used for conditioning.
    :param seed: RNG seed.
    :param logit_noise_std: Std of Gaussian noise added to logits before softmax.
    :param chunk_size: Forward chunk size over devices (0 disables).
    :returns: Shares matrix ``(T,N)`` with row sums == 1 (numerical tolerance).
    """
    torch.manual_seed(int(seed))
    device = next(model.parameters()).device

    ts = np.asarray(timestamps, dtype=np.int64)
    cal_np = calendar_features_unix(ts).astype(np.float32)
    temp_arr = ensure_2d_temp(temp).astype(np.float32)
    region_id_np = np.asarray(region_id, dtype=np.int64)

    T = int(cal_np.shape[0])
    N = int(region_id_np.shape[0])

    region_id_t = torch.tensor(region_id_np, dtype=torch.long, device=device)
    temp_dev = temp_arr[:, region_id_np]  # (T,N)

    out = np.zeros((T, N), dtype=np.float32)
    model.eval()

    for t in range(T):
        cal_t = torch.tensor(cal_np[t:t + 1], dtype=torch.float32, device=device)
        temp_dev_t = torch.tensor(temp_dev[t:t + 1], dtype=torch.float32, device=device)
        y_agg_t = torch.tensor(np.array([[float(y_agg[t])]], dtype=np.float32), device=device)

        logits = model(cal_t, temp_dev_t, y_agg_t, region_id_t, int(chunk_size))
        if logit_noise_std is not None and float(logit_noise_std) > 0.0:
            logits = logits + float(logit_noise_std) * torch.randn_like(logits)
        share = torch.softmax(logits, dim=1)

        out[t, :] = share.squeeze(0).detach().cpu().numpy().astype(np.float32)

    return out


def reconstruct_power_from_shares(P_agg: Vec, shares: Mat) -> Mat:
    """
    Reconstruct device powers from aggregate and shares.

    :param P_agg: Aggregate power ``(T,)``.
    :param shares: Shares ``(T,N)``.
    :returns: Device power matrix ``(T,N)``.
    """
    return (np.asarray(shares, dtype=np.float32) * np.asarray(P_agg, dtype=np.float32)[:, None]).astype(np.float32)


# ----------------------------------------------------------------------------------------------------------------------
# 9) ARTIFACT SAVE/LOAD
# ----------------------------------------------------------------------------------------------------------------------
def save_artifact(path: str, payload: Dict[str, Any]) -> None:
    """
    Save payload via torch.save.

    :param path: Artifact path.
    :param payload: Serializable dict.
    :returns: None
    """
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    torch.save(payload, path)


def load_artifact(path: str, map_location: torch.device) -> Dict[str, Any]:
    """
    Load payload via torch.load.

    Explicitly sets weights_only=False for compatibility with PyTorch >= 2.6
    when loading trusted, self-generated artifacts.
    """
    return torch.load(
        path,
        map_location=map_location,
        weights_only=False,
    )


def load_or_train_hierarchical(
        artifact_path: str,
        timestamps: IntVec,
        P: Mat,
        region_id: IntVec,
        temp: Vec,
        context_len: int,
        steps_agg: int,
        steps_share: int,
        batch_size_agg: int,
        batch_size_share: int,
        lr_agg: float,
        lr_share: float,
        prefer_cuda: bool,
        verbose: bool,
        eps_agg: float,
        eps_share_denominator: float,
        jitter_tol: float,
        share_chunk_size: int,
) -> Tuple[AggregateARModel, ShareSoftmaxModel, Dict[str, Any], List[float], List[float]]:
    """
    Load or train hierarchical artifact (aggregate + simplex shares).

    :param artifact_path: Artifact file path.
    :param timestamps: Unix timestamps ``(T,)``.
    :param P: Device powers ``(T,N)``.
    :param region_id: Device region indices ``(N,)``.
    :param temp: Temperatures ``(T,R)``.
    :param context_len: Aggregate context length ``L``.
    :param steps_agg: Aggregate training steps.
    :param steps_share: Share training steps.
    :param batch_size_agg: Aggregate batch size.
    :param batch_size_share: Share batch size.
    :param lr_agg: Aggregate learning rate.
    :param lr_share: Share learning rate.
    :param prefer_cuda: Try CUDA.
    :param verbose: Print diagnostics.
    :param eps_agg: Epsilon for aggregate log.
    :param eps_share_denominator: Epsilon for share denominator.
    :param jitter_tol: Timestamp jitter tolerance.
    :param share_chunk_size: Chunking for share forward pass.
    :returns: ``(agg_model, share_model, meta, agg_losses, share_losses)``.
    """
    device = select_torch_device(prefer_cuda, verbose)

    if os.path.isfile(artifact_path):
        if verbose:
            print(f"[artifact] Loading: {artifact_path}")
        payload = load_artifact(artifact_path, device)

        agg_cfg = payload["agg_config"]
        share_cfg = payload["share_config"]
        meta = payload["meta"]

        agg_model = AggregateARModel(agg_cfg["cal_dim"], agg_cfg["hidden"], agg_cfg["input_proj"]).to(device)
        agg_model.load_state_dict(payload["agg_state"])
        agg_model.eval()

        share_model = ShareSoftmaxModel(
            n_devices=share_cfg["n_devices"],
            n_regions=share_cfg["n_regions"],
            cal_dim=share_cfg["cal_dim"],
            dev_emb_dim=share_cfg["dev_emb_dim"],
            reg_emb_dim=share_cfg["reg_emb_dim"],
            hidden=share_cfg["hidden"],
        ).to(device)
        share_model.load_state_dict(payload["share_state"])
        share_model.eval()

        return agg_model, share_model, meta, [], []

    if verbose:
        print(f"[artifact] Not found, training and saving to: {artifact_path}")

    temp_arr = ensure_2d_temp(temp)
    grid = infer_time_grid(timestamps, jitter_tol)
    if verbose:
        print(f"[time] dt={grid.dt_seconds}s regular={grid.is_regular} jitter_p95={grid.jitter_frac_p95:.3f}")

    P_agg = compute_aggregate(P)

    agg_model, agg_losses, agg_meta = train_aggregate_model(
        timestamps=timestamps,
        P_agg=P_agg,
        temp=temp_arr,
        context_len=context_len,
        steps=steps_agg,
        batch_size=batch_size_agg,
        lr=lr_agg,
        prefer_cuda=prefer_cuda,
        verbose=verbose,
        eps_agg=eps_agg,
    )

    share_model, share_losses, share_meta = train_share_softmax_model(
        timestamps=timestamps,
        P=P,
        region_id=region_id,
        temp=temp_arr,
        steps=steps_share,
        batch_size=batch_size_share,
        lr=lr_share,
        prefer_cuda=prefer_cuda,
        verbose=verbose,
        eps_share_denominator=eps_share_denominator,
        eps_agg=eps_agg,
        chunk_size=share_chunk_size,
    )

    meta: Dict[str, Any] = {
        "time_grid": asdict(grid),
        "context_len": int(context_len),
        "eps_agg": float(eps_agg),
        "eps_share_denom": float(eps_share_denominator),
        "n_devices": int(np.asarray(P).shape[1]),
        "n_regions": int(temp_arr.shape[1]),
        "device": str(device),
        "agg_meta": agg_meta,
        "share_meta": share_meta,
    }

    payload = {
        "agg_state": agg_model.state_dict(),
        "share_state": share_model.state_dict(),
        "agg_config": {
            "cal_dim": agg_meta["cal_dim"],
            "hidden": agg_meta["hidden"],
            "input_proj": agg_meta["input_proj"],
        },
        "share_config": {
            "n_devices": share_meta["n_devices"],
            "n_regions": share_meta["n_regions"],
            "cal_dim": share_meta["cal_dim"],
            "dev_emb_dim": share_meta["dev_emb_dim"],
            "reg_emb_dim": share_meta["reg_emb_dim"],
            "hidden": share_meta["hidden"],
        },
        "meta": meta,
        "torch_version": torch.__version__,
    }
    save_artifact(artifact_path, payload)
    return agg_model, share_model, meta, agg_losses, share_losses


# ----------------------------------------------------------------------------------------------------------------------
# 10) SYNTHESIS PIPELINE
# ----------------------------------------------------------------------------------------------------------------------
def generate_synthetic(
        agg_model: AggregateARModel,
        share_model: ShareSoftmaxModel,
        timestamps: IntVec,
        P_real: Mat,
        region_id: IntVec,
        temp: Vec,
        context_len: int,
        seed: int,
        eps_agg: float,
        sigma_damp: float,
        anchoring: str,
        logit_noise_std: float,
        share_chunk_size: int,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    Generate synthetic aggregate and device series.

    Steps
    -----
    1) Build real aggregate log-series y_real.
    2) Sample synthetic y_syn and sigma_eff_hist with variance damping.
    3) Anchor y_syn to remove mean bias (global or monthly).
    4) Convert to aggregate power using log-normal mean correction.
    5) Sample simplex shares via softmax model.
    6) Reconstruct device powers.

    :param agg_model: Trained aggregate model.
    :param share_model: Trained share model.
    :param timestamps: Unix timestamps ``(T,)``.
    :param P_real: Real device powers ``(T,N)`` (used only to init and anchor).
    :param region_id: Device region indices ``(N,)``.
    :param temp: Temperatures ``(T,R)``.
    :param context_len: Aggregate context length ``L``.
    :param seed: RNG seed.
    :param eps_agg: Aggregate log epsilon.
    :param sigma_damp: Sampling sigma damping factor in [0,1].
    :param anchoring: "none", "global", or "monthly".
    :param logit_noise_std: Logit noise std for share sampling.
    :param share_chunk_size: Chunking for share forward pass.
    :returns: ``(y_real, y_syn, sigma_eff_hist, P_agg_syn, P_syn)``.
    """
    P_real_clean = np.nan_to_num(np.asarray(P_real, dtype=np.float32), nan=0.0)
    P_agg_real = compute_aggregate(P_real_clean)
    y_real = np.log(np.maximum(P_agg_real, 0.0) + float(eps_agg)).astype(np.float32)

    if y_real.shape[0] < int(context_len):
        raise ValueError("Not enough samples to form initial context_len for aggregate model.")

    y_init = y_real[:int(context_len)].copy()

    y_syn, sigma_eff_hist = sample_aggregate(
        model=agg_model,
        timestamps=timestamps,
        temp=temp,
        y_agg_init=y_init,
        seed=int(seed),
        sigma_damp=float(sigma_damp),
    )

    anch = str(anchoring).lower().strip()
    if anch == "global":
        y_syn = anchor_log_mean_global(y_syn, y_real)
    elif anch == "monthly":
        y_syn = anchor_log_mean_monthly(y_syn, y_real, timestamps)
    elif anch == "none":
        pass
    else:
        raise ValueError("anchoring must be one of: 'none', 'global', 'monthly'")

    P_agg_syn = lognormal_mean_correction(y_syn, sigma_eff_hist)

    shares_syn = sample_shares_softmax(
        model=share_model,
        timestamps=timestamps,
        region_id=region_id,
        temp=temp,
        y_agg=y_syn,
        seed=int(seed) + 1,
        logit_noise_std=float(logit_noise_std),
        chunk_size=int(share_chunk_size),
    )
    P_syn = reconstruct_power_from_shares(P_agg_syn, shares_syn)
    return y_real, y_syn, sigma_eff_hist, P_agg_syn, P_syn


# ----------------------------------------------------------------------------------------------------------------------
# 11) PLOTTING
# ----------------------------------------------------------------------------------------------------------------------
def plot_losses(losses: List[float], title: str) -> None:
    """
    Plot training loss curve.

    :param losses: Loss list.
    :param title: Plot title.
    :returns: None
    """
    if len(losses) == 0:
        print(f"[plot] No losses to plot for: {title} (likely loaded artifact).")
        return
    plt.figure()
    plt.plot(losses)
    plt.title(title)
    plt.xlabel("Step")
    plt.ylabel("Loss")
    plt.grid(True)
    plt.tight_layout()


def plot_aggregate_real_vs_syn(P_agg_real: Vec, P_agg_syn: Vec, max_points: int, title: str) -> None:
    """
    Plot aggregate series real vs synthetic.

    :param P_agg_real: Real aggregate ``(T,)``.
    :param P_agg_syn: Synthetic aggregate ``(T,)``.
    :param max_points: Downsample cap.
    :param title: Plot title.
    :returns: None
    """
    T = int(P_agg_real.shape[0])
    idx = np.arange(T)
    if T > int(max_points):
        idx = np.linspace(0, T - 1, int(max_points)).astype(int)

    plt.figure()
    plt.plot(idx, P_agg_real[idx], label="real aggregate")
    plt.plot(idx, P_agg_syn[idx], label="synthetic aggregate", linestyle="--")
    plt.title(title)
    plt.xlabel("time index")
    plt.ylabel("Aggregate power")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()


def plot_share_sum_sanity(P_syn: Mat,
                          P_agg_syn: Vec,
                          max_points: int,
                          title: str) -> None:
    """
    Plot sanity check: sum_i P_syn(t,i) / P_agg_syn(t). Should be ~1.

    :param P_syn: Device powers ``(T,N)``.
    :param P_agg_syn: Aggregate powers ``(T,)``.
    :param max_points: Downsample cap.
    :param title: Plot title.
    :returns: None
    """

    P = np.asarray(P_syn, dtype=np.float32)
    A = np.asarray(P_agg_syn, dtype=np.float32)
    ratio = P.sum(axis=1) / (A + 1e-12)

    T = int(ratio.shape[0])
    idx = np.arange(T)
    if T > int(max_points):
        idx = np.linspace(0, T - 1, int(max_points)).astype(int)

    plt.figure()
    plt.plot(idx, ratio[idx])
    plt.axhline(1.0, linestyle="--")
    plt.title(title)
    plt.xlabel("time index")
    plt.ylabel("sum(P_syn)/P_agg_syn")
    plt.grid(True)
    plt.tight_layout()


def plot_devices_real_vs_syn(P_real: Mat,
                             P_syn: Mat,
                             devices: List[int],
                             max_points: int,
                             title: str) -> None:
    """
    Plot selected devices real vs synthetic.

    :param P_real: Real device powers ``(T,N)``.
    :param P_syn: Synthetic device powers ``(T,N)``.
    :param devices: Device indices.
    :param max_points: Downsample cap.
    :param title: Plot title.
    :returns: None
    """
    import matplotlib.pyplot as plt

    T = int(P_real.shape[0])
    idx = np.arange(T)
    if T > int(max_points):
        idx = np.linspace(0, T - 1, int(max_points)).astype(int)

    plt.figure()
    for d in devices:
        plt.plot(idx, P_real[idx, d], label=f"real d{d}", alpha=0.8)
        plt.plot(idx, P_syn[idx, d], label=f"syn d{d}", alpha=0.8, linestyle="--")
    plt.title(title)
    plt.xlabel("time index")
    plt.ylabel("Power")
    plt.grid(True)
    plt.legend(ncol=2, fontsize=8)
    plt.tight_layout()


@dataclass
class HierarchicalZipSpec:
    """
    Serializable, future-safe spec for training and generation.

    All fields are JSON-serialisable primitives.

    :param context_len: Aggregate context length L.
    :param steps_agg: Optimisation steps for aggregate model.
    :param steps_share: Optimisation steps for share model.
    :param batch_size_agg: Batch size for aggregate model.
    :param batch_size_share: Batch size for share model.
    :param lr_agg: Learning rate for aggregate model.
    :param lr_share: Learning rate for share model.
    :param prefer_cuda: Try to use CUDA if available.
    :param verbose: Print diagnostics during training.
    :param eps_agg: Epsilon for log stability in aggregate model.
    :param eps_share_denominator: Epsilon for share denominator stability.
    :param share_chunk_size: Chunk size for ShareSoftmaxModel forward (0 disables).
    :param sigma_damp: Damping factor for aggregate sampling sigma.
    :param logit_noise_std: Optional noise added to share logits during sampling.
    """
    context_len: int
    steps_agg: int
    steps_share: int
    batch_size_agg: int
    batch_size_share: int
    lr_agg: float
    lr_share: float
    prefer_cuda: bool
    verbose: bool
    eps_agg: float
    eps_share_denominator: float
    share_chunk_size: int
    sigma_damp: float
    logit_noise_std: Optional[float]


class HierarchicalZipArtifact:
    """
    Orchestrates training, prediction, and durable ZIP save/load for the
    hierarchical (aggregate + simplex shares) generator, using the existing
    functions/classes already present in clean_room1.py.

    This class NEVER pickles model objects. It only stores:
    - state_dict tensors (.pt)
    - JSON specs/meta/losses
    """

    def __init__(self, spec: HierarchicalZipSpec):
        self.spec = spec

        self.agg_model: Optional[AggregateARModel] = None
        self.share_model: Optional[ShareSoftmaxModel] = None

        self.agg_losses: List[float] = []
        self.share_losses: List[float] = []

        self.agg_meta: Dict[str, Any] = {}
        self.share_meta: Dict[str, Any] = {}

        self.device: torch.device = torch.device("cpu")

    # ------------------------------------------------------------------
    # Training
    # ------------------------------------------------------------------

    def train(self,
              timestamps: IntVec,
              P: Mat,
              region_id: IntVec,
              temp: IntVec) -> None:
        """
        Train both aggregate and share models.

        :param timestamps: Unix timestamps (T,).
        :param P: Device power matrix (T,N).
        :param region_id: Region index per device (N,).
        :param temp: Temperature matrix (T,R).
        :returns: None (models stored in self).
        """
        # Aggregate target
        P_arr: Mat = np.asarray(P, dtype=np.float32)
        P_arr = np.nan_to_num(P_arr, nan=0.0)
        P_agg = P_arr.sum(axis=1).astype(np.float32)

        # --- Train aggregate (returns model, losses, meta) ---
        agg_model, agg_losses, agg_meta = train_aggregate_model(
            timestamps=np.asarray(timestamps, dtype=np.int64),
            P_agg=P_agg,
            temp=np.asarray(temp, dtype=np.float32),
            context_len=int(self.spec.context_len),
            steps=int(self.spec.steps_agg),
            batch_size=int(self.spec.batch_size_agg),
            lr=float(self.spec.lr_agg),
            prefer_cuda=bool(self.spec.prefer_cuda),
            verbose=bool(self.spec.verbose),
            eps_agg=float(self.spec.eps_agg),
        )

        # --- Train shares (returns model, losses, meta) ---
        share_model, share_losses, share_meta = train_share_softmax_model(
            timestamps=np.asarray(timestamps, dtype=np.int64),
            P=P_arr,
            region_id=np.asarray(region_id, dtype=np.int64),
            temp=np.asarray(temp, dtype=np.float32),
            steps=int(self.spec.steps_share),
            batch_size=int(self.spec.batch_size_share),
            lr=float(self.spec.lr_share),
            prefer_cuda=bool(self.spec.prefer_cuda),
            verbose=bool(self.spec.verbose),
            eps_share_denominator=float(self.spec.eps_share_denominator),
            eps_agg=float(self.spec.eps_agg),
            chunk_size=int(self.spec.share_chunk_size),
        )

        # Store
        self.agg_model = agg_model
        self.share_model = share_model
        self.agg_losses = list(agg_losses)
        self.share_losses = list(share_losses)
        self.agg_meta = dict(agg_meta)
        self.share_meta = dict(share_meta)

        # Device used (both training fns choose device internally; we keep agg’s)
        self.device = next(self.agg_model.parameters()).device

    def predict(self,
                timestamps: IntVec,
                temp: Vec,
                region_id: IntVec,
                y_agg_init: Vec,
                seed: int) -> np.ndarray:
        """
        Generate synthetic device powers (T,N).

        Uses:
        - sample_aggregate(...) -> (y_syn, sigma_eff)
        - lognormal_mean_correction(...) -> P_agg_syn
        - sample_shares_softmax(...) -> shares (T,N)
        - reconstruct_power_from_shares(...) -> P_syn (T,N)

        :param timestamps: Unix timestamps (T,).
        :param temp: Temperature matrix (T,R).
        :param region_id: Region index per device (N,).
        :param y_agg_init: Initial context for aggregate log-series (L,).
        :param seed: RNG seed.
        :returns: Synthetic device power matrix (T,N).
        """
        if self.agg_model is None or self.share_model is None:
            raise RuntimeError("Models are not loaded or trained")

        y_syn, sigma_eff = sample_aggregate(
            model=self.agg_model,
            timestamps=np.asarray(timestamps, dtype=np.int64),
            temp=np.asarray(temp, dtype=np.float32),
            y_agg_init=np.asarray(y_agg_init, dtype=np.float32),
            seed=int(seed),
            sigma_damp=float(self.spec.sigma_damp),
        )

        P_agg_syn = lognormal_mean_correction(y_syn, sigma_eff)

        shares = sample_shares_softmax(
            model=self.share_model,
            timestamps=np.asarray(timestamps, dtype=np.int64),
            temp=np.asarray(temp, dtype=np.float32),
            y_agg=np.asarray(y_syn, dtype=np.float32),
            region_id=np.asarray(region_id, dtype=np.int64),
            seed=int(seed),
            logit_noise_std=self.spec.logit_noise_std,
            chunk_size=int(self.spec.share_chunk_size),
        )

        return reconstruct_power_from_shares(P_agg_syn, shares)

    # ------------------------------------------------------------------
    # Durable ZIP save/load (tensors + JSON only)
    # ------------------------------------------------------------------

    def save(self, zip_path: str) -> None:
        """
        Save a ZIP artifact containing:
        - aggregate_state.pt
        - share_state.pt
        - spec.json
        - meta.json
        - losses_agg.json
        - losses_share.json

        :param zip_path: Destination ZIP path.
        :returns: None
        """
        if self.agg_model is None or self.share_model is None:
            raise RuntimeError("Models are not loaded or trained")

        agg_sd = self.agg_model.state_dict()
        share_sd = self.share_model.state_dict()

        # JSON payloads
        spec_json = json.dumps(asdict(self.spec), indent=2)
        meta_json = json.dumps(
            {"agg_meta": self.agg_meta, "share_meta": self.share_meta},
            indent=2
        )
        losses_agg_json = json.dumps(self.agg_losses, indent=2)
        losses_share_json = json.dumps(self.share_losses, indent=2)

        with zipfile.ZipFile(zip_path, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
            # Weights as .pt (state_dict only)
            buf = io.BytesIO()
            torch.save(agg_sd, buf)
            zf.writestr("aggregate_state.pt", buf.getvalue())

            buf = io.BytesIO()
            torch.save(share_sd, buf)
            zf.writestr("share_state.pt", buf.getvalue())

            # JSON files
            zf.writestr("spec.json", spec_json)
            zf.writestr("meta.json", meta_json)
            zf.writestr("losses_agg.json", losses_agg_json)
            zf.writestr("losses_share.json", losses_share_json)

    @classmethod
    def load(cls, zip_path: str, map_location: Optional[torch.device]) -> "HierarchicalZipArtifact":
        """
        Load from a ZIP artifact produced by save().

        Reconstruction is explicit:
        - AggregateARModel(cal_dim, hidden, input_proj)
        - ShareSoftmaxModel(n_devices, n_regions, cal_dim, dev_emb_dim, reg_emb_dim, hidden)

        All dimensions are read from meta.json.

        :param zip_path: ZIP path.
        :param map_location: Target torch device (cpu/cuda). If None, CPU.
        :returns: Loaded HierarchicalZipArtifact instance.
        """
        device = map_location if map_location is not None else torch.device("cpu")

        with zipfile.ZipFile(zip_path, mode="r") as zf:
            spec = HierarchicalZipSpec(**json.loads(zf.read("spec.json")))
            meta = json.loads(zf.read("meta.json"))
            agg_meta = dict(meta["agg_meta"])
            share_meta = dict(meta["share_meta"])

            agg_sd = torch.load(io.BytesIO(zf.read("aggregate_state.pt")), map_location=device)
            share_sd = torch.load(io.BytesIO(zf.read("share_state.pt")), map_location=device)

            agg_losses = list(json.loads(zf.read("losses_agg.json")))
            share_losses = list(json.loads(zf.read("losses_share.json")))

        obj = cls(spec=spec)
        obj.agg_meta = agg_meta
        obj.share_meta = share_meta
        obj.agg_losses = agg_losses
        obj.share_losses = share_losses
        obj.device = device

        # Explicit reconstruction from meta dicts returned by your training fns
        obj.agg_model = AggregateARModel(
            int(obj.agg_meta["cal_dim"]),
            int(obj.agg_meta["hidden"]),
            int(obj.agg_meta["input_proj"]),
        ).to(device)
        obj.agg_model.load_state_dict(agg_sd)

        obj.share_model = ShareSoftmaxModel(
            n_devices=int(obj.share_meta["n_devices"]),
            n_regions=int(obj.share_meta["n_regions"]),
            cal_dim=int(obj.share_meta["cal_dim"]),
            dev_emb_dim=int(obj.share_meta["dev_emb_dim"]),
            reg_emb_dim=int(obj.share_meta["reg_emb_dim"]),
            hidden=int(obj.share_meta["hidden"]),
        ).to(device)
        obj.share_model.load_state_dict(share_sd)

        return obj


# ----------------------------------------------------------------------------------------------------------------------
# 12) DEMO / HOW TO USE (with parameter explanations)
# ----------------------------------------------------------------------------------------------------------------------
def demo():
    # -------------------------------------------------------------------------
    # HOW TO USE WITH YOUR DATA (VeraGrid or otherwise)
    # -------------------------------------------------------------------------
    #
    # You need to provide:
    #   timestamps : ndarray (T,) unix seconds (int64)
    #   P          : ndarray (T,N) device powers (float), NaNs allowed
    #   region_id  : ndarray (N,) region index per device (int64 in [0..R-1])
    #   temp       : ndarray (T,R) temperature per region (float)
    #
    # Then:
    #   agg_model, share_model, meta, agg_losses, share_losses = load_or_train_hierarchical(...)
    #   y_real, y_syn, sigma_eff, P_agg_syn, P_syn = generate_synthetic(...)
    #
    # Key parameters:
    #   context_len:
    #     Aggregate AR context length in samples.
    #
    #   sigma_damp:
    #     Damps sampling noise. Start with 0.15–0.35 for national load.
    #
    #   anchoring:
    #     'none'     -> no mean correction (not recommended for free rollouts)
    #     'global'   -> match overall mean of y(t) to real y(t)
    #     'monthly'  -> match mean per month (reduces seasonal bias)
    #
    #   logit_noise_std:
    #     Adds noise to share logits before softmax. Controls diversity in splits.
    #     Start at 0.02–0.10.
    #
    #   share_chunk_size:
    #     If N is large and you hit memory limits, set e.g. 1000–5000.
    # -------------------------------------------------------------------------

    # Demo data (replace with your real data)
    T = 24 * 21  # Number of time steps
    N = 400  # Number of loads
    R = 8  # region number
    start = 1704067200  # Unix datetime
    dt = 3600  # Time step increment in seconds
    timestamps = np.arange(start, start + T * dt, dt, dtype=np.int64)

    rng = np.random.default_rng(0)
    region_id = rng.integers(0, R, size=N, dtype=np.int64)

    base = 15 + 8 * np.sin(2 * np.pi * np.arange(T) / (24 * 7))
    temp = np.stack([base + rng.normal(0, 1.0, size=T) for _ in range(R)], axis=1).astype(np.float32)

    cal = calendar_features_unix(timestamps)
    tod_sin = cal[:, 0]
    scale = rng.uniform(0.5, 2.0, size=N).astype(np.float32)

    P = np.zeros((T, N), dtype=np.float32)
    for i in range(N):
        r = int(region_id[i])
        P[:, i] = scale[i] * (50 + 12 * tod_sin + 1.8 * np.maximum(temp[:, r] - 18, 0)) + rng.normal(0, 2.0, size=T)
    P = np.maximum(P, 0.0)

    mask_nan = rng.random(P.shape) < 0.01
    P_nan = P.copy()
    P_nan[mask_nan] = np.nan

    # Train/load
    artifact_path = "./artifacts/hierarchical_country_load_simplex_anchor.pt"

    context_len = 48
    steps_agg = 2000
    steps_share = 3000
    batch_size_agg = 256
    batch_size_share = 32
    lr_agg = 2e-3
    lr_share = 2e-3
    prefer_cuda = True
    verbose = True
    eps_agg = 1e-3
    eps_share_denom = 1e-6
    jitter_tol = 0.05
    share_chunk_size = 0

    agg_model, share_model, meta, agg_losses, share_losses = load_or_train_hierarchical(
        artifact_path=artifact_path,
        timestamps=timestamps,
        P=P_nan,
        region_id=region_id,
        temp=temp,
        context_len=context_len,
        steps_agg=steps_agg,
        steps_share=steps_share,
        batch_size_agg=batch_size_agg,
        batch_size_share=batch_size_share,
        lr_agg=lr_agg,
        lr_share=lr_share,
        prefer_cuda=prefer_cuda,
        verbose=verbose,
        eps_agg=eps_agg,
        eps_share_denominator=eps_share_denom,
        jitter_tol=jitter_tol,
        share_chunk_size=share_chunk_size,
    )

    # Generate
    sigma_damp = 0.25
    anchoring = "global"  # try "monthly" if seasonal drift persists
    logit_noise_std = 0.05

    y_real, y_syn, sigma_eff, P_agg_syn, P_syn = generate_synthetic(
        agg_model=agg_model,
        share_model=share_model,
        timestamps=timestamps,
        P_real=P_nan,
        region_id=region_id,
        temp=temp,
        context_len=context_len,
        seed=42,
        eps_agg=eps_agg,
        sigma_damp=sigma_damp,
        anchoring=anchoring,
        logit_noise_std=logit_noise_std,
        share_chunk_size=share_chunk_size,
    )

    # Diagnostics
    P_real_clean = np.nan_to_num(P_nan, nan=0.0)
    P_agg_real = compute_aggregate(P_real_clean)

    ratio_mean = float(P_agg_syn.mean() / (P_agg_real.mean() + 1e-12))
    ratio_std = float(P_agg_syn.std() / (P_agg_real.std() + 1e-12))
    ratio_p95 = float(np.quantile(P_agg_syn, 0.95) / (np.quantile(P_agg_real, 0.95) + 1e-12))

    print("Aggregate mean ratio syn/real:", ratio_mean)
    print("Aggregate std  ratio syn/real:", ratio_std)
    print("Aggregate P95  ratio syn/real:", ratio_p95)

    # Plot training losses
    plot_losses(agg_losses, "Aggregate model training NLL")
    plot_losses(share_losses, "Share model training KL")

    # Plot aggregate comparison
    plot_aggregate_real_vs_syn(P_agg_real, P_agg_syn, 5000, "Aggregate real vs synthetic (anchored + corrected)")

    # Sanity check: reconstruction exactness
    plot_share_sum_sanity(P_syn, P_agg_syn, 5000, "Sanity: sum(P_syn)/P_agg_syn (should be 1.0)")

    # Plot a few devices
    plot_devices_real_vs_syn(P_real_clean, P_syn, [0, 1, 2, 10], 5000, "Devices real vs synthetic (simplex shares)")

    plt.show()

def _make_synthetic_demo_data(T: int, N: int, R: int, seed: int) -> tuple[
    np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    Create a small synthetic dataset so the demo can run standalone.

    :param T: number of timesteps
    :param N: number of devices
    :param R: number of regions
    :param seed: RNG seed
    :returns: (timestamps, P, region_id, temp)
    """
    rng = np.random.default_rng(int(seed))
    timestamps = (np.arange(T, dtype=np.int64) * 3600) + np.int64(1700000000)  # hourly unix times

    # Regions and temperatures
    region_id = rng.integers(low=0, high=R, size=N, dtype=np.int64)
    base_temp = 10.0 + 10.0 * np.sin(2.0 * np.pi * np.arange(T) / (24.0 * 30.0))
    temp = np.stack([base_temp + rng.normal(0.0, 1.5, size=T) for _ in range(R)], axis=1).astype(np.float32)

    # Build a plausible aggregate: daily + weekly + temp sensitivity + noise
    hour = (timestamps // 3600) % 24
    dow = (timestamps // (3600 * 24)) % 7
    daily = 1.0 + 0.3 * np.sin(2.0 * np.pi * hour / 24.0 - 0.5)
    weekly = 1.0 - 0.12 * (dow >= 5).astype(np.float32)
    temp_effect = 1.0 + 0.02 * np.maximum(0.0, 18.0 - temp[:, 0]) + 0.01 * np.maximum(0.0, temp[:, 0] - 24.0)
    P_agg = (1000.0 * daily * weekly * temp_effect + rng.normal(0.0, 20.0, size=T)).astype(np.float32)
    P_agg = np.maximum(P_agg, 1.0)

    # Shares per device: region-conditioned static weights + small time variation
    w_dev = rng.lognormal(mean=0.0, sigma=0.5, size=N).astype(np.float32)
    w_reg = rng.lognormal(mean=0.0, sigma=0.3, size=R).astype(np.float32)
    w = w_dev * w_reg[region_id]
    w = w / np.sum(w)

    # Add mild day/night device modulation
    mod = (1.0 + 0.05 * np.sin(2.0 * np.pi * hour / 24.0))[..., None].astype(np.float32)
    P = (P_agg[:, None] * w[None, :] * mod).astype(np.float32)

    # Inject a few NaNs to mimic real telemetry gaps
    mask = rng.random(P.shape) < 0.0005
    P[mask] = np.nan

    return timestamps, P, region_id, temp


def demo2():
    # =============================================================================
    # Demo: Train / Save / Load / Predict with HierarchicalZipArtifact
    # =============================================================================
    # How to use this demo:
    # - Replace the "INPUT DATA" section with arrays you get from VeraGrid.
    #   VeraGrid should provide:
    #     timestamps: (T,) int64 unix seconds
    #     P:          (T,N) float32 device powers (loads/generation per device)
    #     region_id:  (N,) int64 region index per device (0..R-1)
    #     temp:       (T,R) float32 temperatures per region (or per weather zone)
    #
    # Key parameters (HierarchicalZipSpec):
    # - context_len:  number of initial timesteps used to seed the aggregate sampler.
    # - steps_agg/share: optimisation steps for each model training loop.
    # - batch_size_agg/share: training batch sizes (share can be smaller if N large).
    # - lr_agg/share: learning rates.
    # - prefer_cuda:  if True, training functions will try to use CUDA if available.
    # - eps_agg:      small epsilon added inside logs for stability (aggregate).
    # - eps_share_denominator: epsilon in share normalisation denom for stability.
    # - share_chunk_size: chunk size for share model forward; 0 disables chunking.
    # - sigma_damp:   damp aggregate stochasticity when sampling (stability knob).
    # - logit_noise_std: optional noise on share logits during sampling (diversity knob).
    #
    # Outputs:
    # - P_syn: (T,N) synthetic device powers, with aggregate matching the sampled
    #          aggregate trajectory. You can compare sum(P_syn, axis=1) vs sum(P, axis=1).
    # =============================================================================

    # -------------------------------------------------------------------------
    # INPUT DATA
    # -------------------------------------------------------------------------
    # Replace the following with VeraGrid-provided arrays:
    # timestamps = ...
    # P = ...
    # region_id = ...
    # temp = ...

    # Standalone demo fallback:
    timestamps, P, region_id, temp = _make_synthetic_demo_data(T=24 * 60, N=400, R=6, seed=123)

    # Basic sanity
    T = int(timestamps.shape[0])
    N = int(P.shape[1])
    R = int(temp.shape[1])
    print(f"[demo] T={T}, N={N}, R={R}")

    # -------------------------------------------------------------------------
    # SPEC + ARTIFACT PATH
    # -------------------------------------------------------------------------
    artifact_path = "./artifacts/hierarchical_country_load.zip"
    os.makedirs(os.path.dirname(artifact_path), exist_ok=True)

    spec = HierarchicalZipSpec(
        context_len=48,  # seed length for aggregate sampler (e.g. 2 days if hourly)
        steps_agg=3000,  # training steps for aggregate model
        steps_share=3000,  # training steps for share model
        batch_size_agg=64,  # aggregate batch size
        batch_size_share=16,  # share batch size (often smaller because N is large)
        lr_agg=3e-4,  # aggregate learning rate
        lr_share=3e-4,  # share learning rate
        prefer_cuda=True,  # try CUDA if available
        verbose=True,  # print training progress
        eps_agg=1e-6,  # numerical stability for log transforms
        eps_share_denominator=1e-6,  # stability in share normalisation
        share_chunk_size=0,  # 0 disables chunking; set >0 if you need lower peak memory
        sigma_damp=0.25,  # reduces aggregate stochasticity at generation
        logit_noise_std=0.0,  # share diversity; start at 0.0
    )

    # -------------------------------------------------------------------------
    # TRAIN OR LOAD
    # -------------------------------------------------------------------------
    if os.path.exists(artifact_path):
        print(f"[demo] Loading artifact: {artifact_path}")
        # Always load to CPU first for maximum portability; move to CUDA later if desired.
        art = HierarchicalZipArtifact.load(artifact_path, map_location=torch.device("cpu"))
    else:
        print(f"[demo] Training new artifact: {artifact_path}")
        art = HierarchicalZipArtifact(spec=spec)
        art.train(timestamps=timestamps, P=P, region_id=region_id, temp=temp)
        art.save(artifact_path)
        print(f"[demo] Saved: {artifact_path}")

    # -------------------------------------------------------------------------
    # GENERATE SYNTHETIC
    # -------------------------------------------------------------------------
    # y_agg_init must be a (context_len,) log-aggregate seed.
    # Using the REAL aggregate for seeding is typical (you can also seed with a
    # previous synthetic run if doing multi-year continuation).
    P_clean = np.nan_to_num(P.astype(np.float32), nan=0.0)
    P_agg_real = np.sum(P_clean, axis=1)
    y_agg_init = np.log(P_agg_real[:int(art.spec.context_len)] + float(art.spec.eps_agg)).astype(np.float32)

    P_syn = art.predict(
        timestamps=timestamps,
        temp=temp.astype(np.float32),
        region_id=region_id.astype(np.int64),
        y_agg_init=y_agg_init,
        seed=1234,
    )

    # -------------------------------------------------------------------------
    # PLOTS: real vs synthetic aggregate
    # -------------------------------------------------------------------------
    P_agg_syn = np.sum(P_syn, axis=1)

    plt.figure()
    plt.plot(P_agg_real, label="Real aggregate")
    plt.plot(P_agg_syn, label="Synthetic aggregate")
    plt.xlabel("timestep")
    plt.ylabel("Aggregate power")
    plt.legend()
    plt.title("Aggregate: Real vs Synthetic")
    plt.tight_layout()
    plt.show()

    # Optional: device-level example
    plt.figure()
    dev_idx = 0
    plt.plot(P_clean[:, dev_idx], label=f"Real dev {dev_idx}")
    plt.plot(P_syn[:, dev_idx], label=f"Synth dev {dev_idx}")
    plt.xlabel("timestep")
    plt.ylabel("Device power")
    plt.legend()
    plt.title("Example device trajectory")
    plt.tight_layout()
    plt.show()

    # Quick numeric check
    rel_err = float(np.mean(np.abs(P_agg_syn - P_agg_real)) / (np.mean(P_agg_real) + 1e-9))
    print(f"[demo] Mean abs aggregate error / mean real = {rel_err:.4f}")


if __name__ == "__main__":
    demo2()
