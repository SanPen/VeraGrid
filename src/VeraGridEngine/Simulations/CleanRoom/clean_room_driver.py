# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

import numpy as np
from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from VeraGridEngine.enumerations import SimulationTypes
from VeraGridEngine.Simulations.driver_template import DriverTemplate
from VeraGridEngine.Simulations.CleanRoom.clean_room import HierarchicalZipSpec, HierarchicalZipArtifact


class CleanRoomDriver(DriverTemplate):
    __slots__ = ("artifact",)

    name = 'Clean room'
    tpe = SimulationTypes.CleanRoom_run

    def __init__(self, grid: MultiCircuit):
        """
        Clustering analysis driver constructor
        :param grid: MultiCircuit instance
        """
        DriverTemplate.__init__(self, grid=grid)

        self.artifact: HierarchicalZipArtifact | None = None

    def run(self):
        """
        Run thread
        """
        self.tic()
        self.report_progress(0.0)

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

        # TRAIN
        self.report_text(f"Training new artifact...")
        self.artifact = HierarchicalZipArtifact(spec=spec)
        self.artifact.train(timestamps=timestamps, P=P, region_id=region_id, temp=temp)
        # art.save(artifact_path)

        P_syn = self.artifact.predict(
            timestamps=timestamps,
            temp=temp.astype(np.float32),
            region_id=region_id.astype(np.int64),
            y_agg_init=y_agg_init,
            seed=1234,
        )

        self.toc()
