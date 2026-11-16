# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""POM 33.10 section 15.1.1 defines USRSWS without an equipment ID. Built-in schemas follow the generator model data sheets."""
from VeraGridEngine.IO.raw.psse_auxiliary import PsseVersion
from VeraGridEngine.IO.raw.versioned.base.auxiliary import FeatureSupport
from VeraGridEngine.IO.raw.versioned.base.dyr import (
    RawDyr, DynamicModelSchema, UserDynamicModelSchema, UserModelType)


class RawDyrV33(RawDyr):
    """PSS/E 33 DYR data; inherit only unchanged grammar."""

    __slots__ = ()

    def __init__(self, source: str = '<dyr>') -> None:
        """Select the documented PSS/E 33 grammar.

        :param source: Diagnostic source label.
        """
        super().__init__(source, PsseVersion.V33)
        self.usr_sws2_support = FeatureSupport.NO
        # POM 33.10 section 15.1.1 lists renewable IC codes 101 through 107.
        self.torque_model_support = FeatureSupport.NO

    def get_model_schema(self, model: str) -> DynamicModelSchema | None:
        """Own the release-specific actuator/exciter constant order.

        :param model: Source model identifier, case insensitive.
        :return: Explicit reviewed layout or unchanged common schema.
        """
        if model.upper() == 'CGEN1':
            # PSS/E 33.10 Model Library pages 1-11–1-12: 27 direct CONs.
            return DynamicModelSchema(
                'CGEN1', (
                    'H','S10','S12','LLD','LAD','RFD','LFD','RMD1','LMD1','RKD1',
                    'LKD1','RMD2','LMD2','RKD2','LKD2','LLQ','LAQ','RKQ3','LKQ3',
                    'RMQ1','LMQ1','RKQ1','LKQ1','RMQ2','LMQ2','RKQ2','LKQ2',
                ),
            )
        elif model.upper() == 'GAST2A':
            # PSS/E 33.10 Model Library section 7.7 defines 31 ordered CONs.
            return DynamicModelSchema(
                'GAST2A', (
                    'W','X','Y','Z','ETD','TCD','TRATE','T','MAX','MIN','ECR',
                    'K3','A','B','C','TAUF','KF','K5','K4','T3','T4','TAUT','T5',
                    'AF1','BF1','AF2','BF2','CF2','TR','K6','TC',
                ),
            )
        elif model.upper() == 'TGOV2':
            # Model Library 33.10 section 7.35 documents the same 11-CON order.
            return DynamicModelSchema(
                'TGOV2', ('R','T1','VMAX','VMIN','K','T3','DT','TT','TA','TB','TC'),
            )
        elif model.upper() == 'BBGOV1':
            # Model Library 33.10 section 7.1 specifies seventeen direct CONs.
            return DynamicModelSchema(
                'BBGOV1', ('FCUT','KS','KLS','KG','KP','TN','KD','TD','T4','K2',
                           'T5','K3','T6','T1','SWITCH','PMAX','PMIN'),
            )
        elif model.upper() == 'PSS4B':
            # Model Library 33.10 section 3.11 specifies 75 direct CONs.
            return DynamicModelSchema(
                'PSS4B', (
                    'CL_I','DL_I','AL_I','BL_I','BW_L_I1','W_L_I1','BW_L_I2','W_L_I2',
                    'TH','AH','BH','M','BW_H1','W_H1','BW_H2','W_H2',
                    'KL1','KL11','TL1','TL2','TL3','TL4','TL5','TL6',
                    'KL2','KL17','TL7','TL8','TL9','TL10','TL11','TL12',
                    'KL','VLmax','VLmin','KI1','KI11','TI1','TI2','TI3','TI4','TI5','TI6',
                    'KI2','KI17','TI7','TI8','TI9','TI10','TI11','TI12',
                    'KI','VImax','VImin','KH1','KH11','TH1','TH2','TH3','TH4','TH5','TH6',
                    'KH2','KH17','TH7','TH8','TH9','TH10','TH11','TH12',
                    'KH','VHmax','VHmin','VSTMAX','VSTMIN',
                ),
            )
        elif model.upper() == 'BEPSST':
            # PSS/E 33.10 Model Library section 3.1 lists five ICONs and 21 CONs.
            return DynamicModelSchema(
                'BEPSST',
                ('K1','K2','T1','T2','T3','T4','T5','T6','T7','T8','T9','T10',
                 'LSMAX','LSMIN','VCU','VCL','K','T11','T12','CRT','CLIM'),
                ('ICS1','IB1','IC2','IB2','ITS'),
            )
        elif model.upper() == 'OSTB2T':
            # PSS/E 33.10 Model Library section 3.5 lists 20 direct CONs.
            return DynamicModelSchema('OSTB2T', (
                'K','TS','T1_T3','T3','T2_T4','T4','HLIM','LLIM','KANG','TANG',
                'VNGMX','VMGMX','T_ON','T_OFF','VSMX','VSMN','DWTHR','ETHR',
                'EFDTHR','TSEAL',
            ))
        elif model.upper() == 'OSTB5T':
            # PSS/E 33.10 Model Library section 3.6 lists 20 direct CONs.
            return DynamicModelSchema('OSTB5T', (
                'K','TS','T1','T2','T3_T4','T4','HLIM','LLIM','KANG','TANG',
                'VNGMX','VMGMX','T_ON','T_OFF','VSMX','VSMN','DWTHR','ETHR',
                'EFDTHR','TSEAL',
            ))
        elif model.upper() == 'WESGOV':
            # Model Library 33.10 section 7.46: direct nine-CON digital governor.
            return DynamicModelSchema(
                'WESGOV', ('DTC','DTP','DROOP','KP','TI','T1','T2','ALIM','TPE'),
            )
        elif model.upper() == 'TGOV3':
            # Model Library 33.10 section 7.36 documents the direct 18-CON form.
            return DynamicModelSchema(
                'TGOV3', ('K','T1','T2','T3','UO','UC','PMAX','PMIN','T4','K1',
                          'T5','K2','T6','K3','TA','TB','TC','PRMAX'),
            )
        elif model.upper() == 'TGOV4':
            # Model Library 33.10 section 7.38 defines three ICONs and 52 CONs.
            return DynamicModelSchema(
                'TGOV4', (
                    'K','T1','T2','T3','UO','UC','KCAL','T4','K1','T5','K2','T6',
                    'PRMAX','KP','KI','TFUEL','TFD1','TFD2','KB','CB','TIV','UOIV',
                    'UCIV','R','OFFSET','CV_POSITION_DEMAND','CV2_OFFSET','CV3_OFFSET',
                    'CV4_OFFSET','IV_POSITION_DEMAND','IV2_OFFSET','CV_VALVE',
                    'IV_VALVE','CV_CLOSE_START','CV_CLOSE_RATE','CV1_CLOSED_TIME',
                    'CV2_CLOSED_TIME','CV3_CLOSED_TIME','CV4_CLOSED_TIME',
                    'IV_CLOSE_START','IV_CLOSE_RATE','IV1_CLOSED_TIME','IV2_CLOSED_TIME',
                    'TRPLU','PLU_RATE_LEVEL','TIMER','PLU_UNBALANCE_LEVEL','TREVA',
                    'EVA_RATE_LEVEL','EVA_UNBALANCE_LEVEL','MIN_LOAD_REFERENCE',
                    'LOAD_REFERENCE_RAMP_RATE',
                ), ('NCV','NIV','MODE'),
            )
        elif model.upper() == 'TGOV5':
            # Model Library 33.10 section 7.39 defines a linked machine and 49 CONs.
            return DynamicModelSchema(
                'TGOV5', (
                    'K','T1','T2','T3','UO','UC','VMAX','VMIN','T4','K1','K2',
                    'T5','K3','K4','T6','K5','K6','T7','K7','K8','K9','K10','K11',
                    'K12','K13','K14','RMAX','RMIN','LMAX','LMIN','C1','C2','C3',
                    'B','CB','KI','TI','TR','TR1','CMAX','CMIN','TD','TF','TW','PSP',
                    'TMW','KL','KMW','DELTA_PE',
                ), ('JBUS','M'), character_icon_names=('M',),
            )
        elif model.upper() == 'BUDCZT':
            # Model Library 33.10 section 6.4 puts TA before TE.
            return DynamicModelSchema('BUDCZT',('KP','KA','KE','TR','TI','TA','TE','URMAX','URMIN','EFDMAX','EFDMIN'))
        elif model.upper() == 'MAXEX2':
            # Model Library 33.10 section 5.2 documents the mode and ten CONs.
            return DynamicModelSchema(
                'MAXEX2', ('RATED','LEVEL1','TIME1','LEVEL2','TIME2','LEVEL3',
                           'TIME3','DESIRED_LEVEL','KMX','VLOW'), ('M',),
            )
        elif model.upper() == 'MAXEX1':
            # Model Library 33.10 section 5.1 DYR syntax carries ten CONs and no ICON.
            return DynamicModelSchema(
                'MAXEX1', ('EFDRATED','EFD1','TIME1','EFD2','TIME2','EFD3',
                           'TIME3','EFDDES','KMX','VLOW'),
            )
        elif model.upper() in ('FRQTPAT', 'VTGTPAT'):
            # PSS/E 33.10 Model Library sections 31.1-31.2 document these MINS layouts.
            relay_parameters: tuple[str, ...]
            if model.upper() == 'FRQTPAT':
                relay_parameters = ('FL', 'FU', 'TP', 'TB')
            else:
                relay_parameters = ('VL', 'VU', 'TP', 'TB')
            return DynamicModelSchema(
                model.upper(), relay_parameters, ('MBUS', 'GBUS', 'ID'),
            )
        elif model.upper() == 'ST6B':
            # Model Library 33.10 section 6.60: OEL selector and sixteen CONs.
            return DynamicModelSchema(
                'ST6B', ('TR','KPA','KIA','KDA','TDA','VAMAX','VAMIN','KFF',
                         'KM','KCI','KLR','ILR','VRMAX','VRMIN','KG','TG'),
                ('OEL',),
            )
        elif model.upper() == 'COMPCC':
            # Model Library 33.10 section 2.3: M is unit 2's character ID at IBUS.
            return DynamicModelSchema('COMPCC', ('R1','X1','R2','X2'), ('M',), ('M',))
        elif model.upper() == 'UEL1':
            # Model Library 33.10 section 4.4 documents the direct 15-CON UEL1.
            return DynamicModelSchema(
                'UEL1',
                ('KUR','KUC','KUF','VURMAX','VUCMAX','KUI','KUL','VUIMAX',
                 'VUIMIN','TU1','TU2','TU3','TU4','VULMAX','VULMIN'),
            )
        else:
            return super().get_model_schema(model)

    def get_auxiliary_signal_schema(self, model: str) -> DynamicModelSchema | None:
        """Return the 33.10 frequency auxiliary-signal record layout.

        :param model: Source model name, case-insensitive.
        :return: Explicit auxiliary layout or None.
        """
        if model.upper() == 'CPAAUT':
            return DynamicModelSchema('CPAAUT', ('CM','TB','TA','PMAX','PMIN'), ('BUS',))
        else:
            return super().get_auxiliary_signal_schema(model)

    def get_user_model_schema(self, name: str) -> UserDynamicModelSchema | None:
        """Select explicitly reviewed 33.10 renewable and governor wrappers.

        :param name: Exact source user-subroutine identifier, case insensitive.
        :return: Reviewed layout/allocation contract or None for unreviewed routines.
        """
        if name.upper() == 'REGCAU1':
            # Model Library 33.10 section 17.2: IC,IT,NI,NC,NS,NV = 101,1,1,14,3,4.
            return UserDynamicModelSchema(DynamicModelSchema('REGCAU1',
                ('TG','RRPWR','BRKPT','ZEROX','LVPL1','VOLIM','LVPNT1','LVPNT0',
                 'IOLIM','TFLTR','KHV','IQRMAX','IQRMIN','ACCEL'),('LVPLSW',)),
                UserModelType.RENEWABLE_GENERATOR,1,3,4)
        elif name.upper() == 'REECAU1':
            # Model Library 33.10 section 18.2: six ICONs and 45 CONs.
            return UserDynamicModelSchema(DynamicModelSchema('REECAU1',
                ('VDIP','VUP','TRV','DBD1','DBD2','KQV','IQH1','IQL1','VREF0',
                 'IQFRZ','THLD','THLD2','TP','QMAX','QMIN','VMAX','VMIN','KQP',
                 'KQI','KVP','KVI','VBIAS','TIQ','DPMAX','DPMIN','PMAX','PMIN',
                 'IMAX','TPORD','VQ1','IQ1','VQ2','IQ2','VQ3','IQ3','VQ4','IQ4',
                 'VP1','IP1','VP2','IP2','VP3','IP3','VP4','IP4'),
                ('VCBUS','PFFLAG','VFLAG','QFLAG','PFLAG','PQFLAG')),
                UserModelType.RENEWABLE_ELECTRICAL,0,6,9)
        elif name.upper() == 'WTDTAU1':
            # Model Library 33.10 section 19.4: 103,0,0,5,4,3.
            return UserDynamicModelSchema(DynamicModelSchema('WTDTAU1',
                ('H','DAMP','HTFRAC','FREQ1','DSHAFT')),
                UserModelType.RENEWABLE_TURBINE,0,4,3)
        elif name.upper() == 'WTARAU1':
            # Model Library 33.10 section 21.2: 105,0,0,2,0,1.
            return UserDynamicModelSchema(DynamicModelSchema('WTARAU1',
                ('KA','THETA0')),
                UserModelType.RENEWABLE_AERODYNAMIC,0,0,1)
        elif name.upper() == 'WTPTAU1':
            # Model Library 33.10 section 20.3: 104,0,0,10,3,1.
            return UserDynamicModelSchema(DynamicModelSchema('WTPTAU1',
                ('KIW','KPW','KIC','KPC','KCC','TP','TETAMAX','TETAMIN','RTETAMAX','RTETAMIN')),
                UserModelType.RENEWABLE_PITCH,0,3,1)
        elif name.upper() == 'WTTQAU1':
            # Model Library 33.10 section 32.2 uses machine-other IC=505.
            return UserDynamicModelSchema(DynamicModelSchema('WTTQAU1',
                ('KPP','KIP','TP','TWREF','TEMAX','TEMIN','P1','SPD1',
                 'P2','SPD2','P3','SPD3','P4','SPD4','TRATE'),('TFLAG',)),
                UserModelType.MACHINE_OTHER,0,3,3)
        elif name.upper() == 'CCOMP4U1':
            # Model Library 33.10 section 2.1: 2,0,6,7,0,5 cross-current wrapper.
            return UserDynamicModelSchema(DynamicModelSchema(
                'CCOMP4U1', ('K1','K2','K3','K4','KC','VMAX','VMIN'),
                ('BUS2','ID2','BUS3','ID3','BUS4','ID4'), ('ID2','ID3','ID4'),
            ), UserModelType.COMPENSATOR,0,0,5)
        elif name.upper() == 'TGOV3DU':
            # Model Library 33.10 section 7.37 omits NI=0 from its five-field header.
            return UserDynamicModelSchema(DynamicModelSchema('TGOV3DU',
                ('K','T1','T2','T3','UO','UC','PMAX','PMIN','T4','K1','T5','K2',
                 'T6','K3','TA','TB','TC','PRMAX','DBH','DBL','TRATE')),
                UserModelType.GOVERNOR,0,6,3)
        elif name.upper() == 'WESGOVDU':
            # Model Library 33.10 section 7.47 omits NI=0 from its five-field header.
            return UserDynamicModelSchema(DynamicModelSchema('WESGOVDU',
                ('DTC','DTP','DROOP','KP','TI','T1','T2','ALIM','TPE',
                 'DBH','DBL','TRATE')),
                UserModelType.GOVERNOR,0,3,7)
        elif name.upper() in ('REPCAU1','REPCTAU1'):
            # Model Library 33.10 section 22.1: type-4/type-3 plant wrappers.
            return UserDynamicModelSchema(DynamicModelSchema(name.upper(),
                ('TFLTR','KP','KI','TFT','TFV','VFRZ','RC','XC','KC','EMAX',
                 'EMIN','DBD1','DBD2','QMAX','QMIN','KPG','KIG','TP','FDBD1',
                 'FDBD2','FEMAX','FEMIN','PMAX','PMIN','TG','DDN','DUP'),
                ('VCBUS','FROMBUS','TOBUS','CKT','VCFLAG','REFFLAG','FFLAG'),
                ('CKT',)),UserModelType.RENEWABLE_AUXILIARY,0,7,9)
        else:
            pass
        contracts: dict[str,tuple[str,int,int]] = dict(TGOV1DU=('TGOV1',2,2), GASTDU=('GAST',3,2),
            HYGOVDU=('HYGOV',4,3), HYGOV2DU=('HYGOV2',6,2), IEESGODU=('IEESGO',5,2))
        contract: tuple[str,int,int] | None = contracts.get(name.upper(),None)
        if contract is not None:
            parent: DynamicModelSchema | None = self.get_model_schema(contract[0])
            if parent is None:
                return None
            else:
                return UserDynamicModelSchema(DynamicModelSchema(name.upper(),
                    parent.parameters+('DBH','DBL','TRATE')),UserModelType.GOVERNOR,0,contract[1],contract[2])
        elif name.upper() == 'DEGOV1DU':
            engine: DynamicModelSchema | None = self.get_model_schema('DEGOV1')
            if engine is None:
                return None
            else:
                return UserDynamicModelSchema(DynamicModelSchema('DEGOV1DU',
                    engine.parameters+('DBH','DBL','TRATE'),engine.icon_names),UserModelType.GOVERNOR,0,6,15)
        elif name.upper() == 'PIDGOVDU':
            pid: DynamicModelSchema | None = self.get_model_schema('PIDGOV')
            if pid is None:
                return None
            else:
                return UserDynamicModelSchema(DynamicModelSchema('PIDGOVDU',pid.parameters+('DBH','DBL','TRATE'),pid.icon_names),UserModelType.GOVERNOR,0,7,2)
        elif name.upper() == 'GGOV1DU':
            base: DynamicModelSchema | None = self.get_model_schema('GGOV1')
            if base is None:
                return None
            else:
                layout: DynamicModelSchema = DynamicModelSchema('GGOV1DU', base.parameters+('DBH','DBL'),
                    base.icon_names, base.character_icon_names, base.signed_icon_names)
                return UserDynamicModelSchema(layout, UserModelType.GOVERNOR, 0, 10, 22)
        elif name.upper() == 'IEEEG1SDU':
            steam: DynamicModelSchema | None = self.get_model_schema('IEEEG1')
            if steam is None:
                return None
            else:
                return UserDynamicModelSchema(DynamicModelSchema('IEEEG1SDU',
                    steam.parameters+('DBH','DBL','TRATE')), UserModelType.GOVERNOR, 0, 6, 3)
        elif name.upper() == 'IEEEG3DU':
            hydro: DynamicModelSchema | None = self.get_model_schema('IEEEG3')
            if hydro is None:
                return None
            else:
                return UserDynamicModelSchema(DynamicModelSchema('IEEEG3DU',
                    hydro.parameters+('DBH','DBL','TRATE')), UserModelType.GOVERNOR, 0, 4, 2)
        else:
            return None
