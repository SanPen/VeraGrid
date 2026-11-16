# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""Equation-backed CGMES IEEE ST4B compound-source excitation template."""

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.excitation_systems.st4b import (
    CompoundPiExciterParameters,
    build_st4b_template,
)
from VeraGridEngine.Utils.Symbolic.symbolic import Var


class ExcIEEEST4BParameters:
    """Exact scalar fields declared by the canonical ExcIEEEST4B RDF class."""

    __slots__ = (
        'kpr', 'kir', 'ta', 'vrmax', 'vrmin', 'kpm', 'kim', 'vmmax', 'vmmin',
        'kg', 'kp', 'thetap', 'ki', 'kc', 'xl', 'vbmax',
    )

    def __init__(
            self,
            kpr: float = 2.0,
            kir: float = 1.0,
            ta: float = 0.05,
            vrmax: float = 5.0,
            vrmin: float = -5.0,
            kpm: float = 1.0,
            kim: float = 1.0,
            vmmax: float = 1.0,
            vmmin: float = 0.0,
            kg: float = 1.0,
            kp: float = 2.0,
            thetap: float = 0.0,
            ki: float = 0.1,
            kc: float = 0.1,
            xl: float = 0.1,
            vbmax: float = 5.0,
    ) -> None:
        """Store CGMES scalars using the native physical reference defaults.

        :param kpr: Voltage-loop proportional gain.
        :param kir: Voltage-loop integral gain.
        :param ta: Regulator output lag time in seconds.
        :param vrmax: Outer regulator maximum.
        :param vrmin: Outer regulator minimum.
        :param kpm: Field-loop proportional gain.
        :param kim: Field-loop integral gain.
        :param vmmax: Inner regulator maximum.
        :param vmmin: Inner regulator minimum.
        :param kg: Field-voltage feedback gain.
        :param kp: Potential-transformer ratio.
        :param thetap: Potential-transformer phase angle in degrees.
        :param ki: Current-compounding ratio.
        :param kc: Commutation loading coefficient.
        :param xl: Transformer leakage reactance.
        :param vbmax: Maximum rectified supply voltage.
        """
        self.kpr: float = kpr
        self.kir: float = kir
        self.ta: float = ta
        self.vrmax: float = vrmax
        self.vrmin: float = vrmin
        self.kpm: float = kpm
        self.kim: float = kim
        self.vmmax: float = vmmax
        self.vmmin: float = vmmin
        self.kg: float = kg
        self.kp: float = kp
        self.thetap: float = thetap
        self.ki: float = ki
        self.kc: float = kc
        self.xl: float = xl
        self.vbmax: float = vbmax


def build_exc_i_e_e_e_s_t4_b_template(
        vfactory: VarFactory,
        name: str | None = None,
        parameters: ExcIEEEST4BParameters | None = None,
) -> RmsModelTemplate:
    """Build ST4B equations and expose canonical RDF fields as events.

    :param vfactory: Factory allocating model variables.
    :param name: Optional unique runtime name.
    :param parameters: Parsed CGMES values or reference defaults.
    :return: Equation-backed ST4B graph with terminal voltage/current ports.
    """
    settings: ExcIEEEST4BParameters = (
        ExcIEEEST4BParameters() if parameters is None else parameters
    )
    template_name: str = 'ExcIEEEST4B' if name is None else name
    template: RmsModelTemplate = build_st4b_template(
        vf=vfactory,
        name=template_name,
        parameters=CompoundPiExciterParameters(
            tr=0.0,
            kpr=settings.kpr,
            kir=settings.kir,
            vrmax=settings.vrmax,
            vrmin=settings.vrmin,
            ta=settings.ta,
            kpm=settings.kpm,
            kim=settings.kim,
            vmmax=settings.vmmax,
            vmmin=settings.vmmin,
            kg=settings.kg,
            kp=settings.kp,
            ki=settings.ki,
            vbmax=settings.vbmax,
            kc=settings.kc,
            xl=settings.xl,
            thetap=settings.thetap,
        ),
    )
    template.comment = 'CGMES ExcIEEEST4B compound-source cascaded PI excitation model'
    parameter_fields: tuple[str, ...] = (
        'kpr', 'kir', 'ta', 'vrmax', 'vrmin', 'kpm', 'kim', 'vmmax', 'vmmin',
        'kg', 'kp', 'thetap', 'ki', 'kc', 'xl', 'vbmax',
    )
    for parameter_name in parameter_fields:
        parameter_var: Var = vfactory.add_var(
            f'ExcIEEEST4B.{parameter_name}_{template_name}',
        )
        template.block.event_dict[parameter_var] = vfactory.add_const(value=None)
    return template
