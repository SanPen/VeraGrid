# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""POM 35.2 section 16.1.1; ReleaseNotes 35.0 section 7.4 adds USRSWS2 and retains USRSWS. Model aliases are never rewritten."""
from VeraGridEngine.IO.raw.psse_auxiliary import PsseVersion
from VeraGridEngine.IO.raw.versioned.base.dyr import (
    DynamicModelSchema, UserDynamicModelSchema, UserModelType,
)
from VeraGridEngine.IO.raw.versioned.base.auxiliary import FeatureSupport
from VeraGridEngine.IO.raw.versioned.v34.dyr import RawDyrV34


class RawDyrV35(RawDyrV34):
    """PSS/E 35 DYR data; inherit only unchanged grammar."""

    __slots__ = ()

    def __init__(self, source: str = '<dyr>') -> None:
        """Select the documented PSS/E 35 grammar.

        :param source: Diagnostic source label.
        """
        super().__init__(source)
        self.version = PsseVersion.V35
        self.usr_sws2_support = FeatureSupport.YES
        # POM 35.2 section 16.1.1 includes renewable torque calling sequence 108.
        self.torque_model_support = FeatureSupport.YES

    def get_model_schema(self, model: str) -> DynamicModelSchema | None:
        """Select the direct deadband-governor layout documented in this release.

        The earlier supplied library exposes a distinct user-model wrapper.
        That header is not interpreted as this direct built-in assignment.

        :param model: Source model identifier, case insensitive.
        :return: Explicit release schema or an unchanged inherited layout.
        """
        if model.upper() == 'CGEN1':
            # Model Library 35.2 section 1.3 retains the 27-CON circuit order.
            return DynamicModelSchema(
                'CGEN1', (
                    'H','S10','S12','LLD','LAD','RFD','LFD','RMD1','LMD1','RKD1',
                    'LKD1','RMD2','LMD2','RKD2','LKD2','LLQ','LAQ','RKQ3','LKQ3',
                    'RMQ1','LMQ1','RKQ1','LKQ1','RMQ2','LMQ2','RKQ2','LKQ2',
                ),
            )
        elif model.upper() == 'GAST2A':
            # PSS/E 35.2 Model Library section 7.7 retains the 31-CON order.
            return DynamicModelSchema(
                'GAST2A', (
                    'W','X','Y','Z','ETD','TCD','TRATE','T','MAX','MIN','ECR',
                    'K3','A','B','C','TAUF','KF','K5','K4','T3','T4','TAUT','T5',
                    'AF1','BF1','AF2','BF2','CF2','TR','K6','TC',
                ),
            )
        elif model.upper() == 'FRQTPAT':
            # Model Library 35.2 section 32.1 defines the MINS relay record.
            return DynamicModelSchema(
                'FRQTPAT', ('FL','FU','TP','TB'), ('MBUS','GBUS','ID'),
                character_icon_names=('ID',),
            )
        elif model.upper() == 'VTGTPAT':
            # Model Library 35.2 section 32.4 defines the MINS relay record.
            return DynamicModelSchema(
                'VTGTPAT', ('VL','VU','TP','TB'), ('MBUS','GBUS','ID'),
                character_icon_names=('ID',),
            )
        elif model.upper() == 'BBGOV1':
            # Model Library 35.2 section 7.1 keeps the seventeen-CON layout.
            return DynamicModelSchema(
                'BBGOV1', ('FCUT','KS','KLS','KG','KP','TN','KD','TD','T4','K2',
                           'T5','K3','T6','T1','SWITCH','PMAX','PMIN'),
            )
        elif model.upper() == 'PSS4B':
            # Model Library 35.2 section 3.12 retains the 75-CON direct record.
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
        elif model.upper() == 'TGOV3D':
            # Model Library 35.2 section 7.44 extends TGOV3 with three CONs.
            return DynamicModelSchema(
                'TGOV3D', ('K','T1','T2','T3','UO','UC','PMAX','PMIN','T4','K1',
                           'T5','K2','T6','K3','TA','TB','TC','PRMAX','DBH','DBL','TRATE'),
            )
        elif model.upper() == 'TGOV4':
            # Model Library 35.2 section 7.45 defines three input ICONs and 52 CONs.
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
            # Model Library 35.2 section 7.46 retains the linked-machine 49-CON order.
            return DynamicModelSchema(
                'TGOV5', (
                    'K','T1','T2','T3','UO','UC','VMAX','VMIN','T4','K1','K2',
                    'T5','K3','K4','T6','K5','K6','T7','K7','K8','K9','K10','K11',
                    'K12','K13','K14','RMAX','RMIN','LMAX','LMIN','C1','C2','C3',
                    'B','CB','KI','TI','TR','TR1','CMAX','CMIN','TD','TF','TW','PSP',
                    'TMW','KL','KMW','DELTA_PE',
                ), ('JBUS','M'), character_icon_names=('M',),
            )
        elif model.upper() == 'WESGOV':
            # Model Library 35.2 section 7.53: direct nine-CON record.
            return DynamicModelSchema(
                'WESGOV', ('DTC','DTP','DROOP','KP','TI','T1','T2','ALIM','TPE'),
            )
        elif model.upper() == 'WESGOVD':
            # Model Library 35.2 section 7.54 adds two droop deadbands and TRATE.
            return DynamicModelSchema(
                'WESGOVD', ('DTC','DTP','DROOP','KP','TI','T1','T2','ALIM','TPE',
                            'DBH','DBL','TRATE'),
            )
        else:
            pass
        deadband_parents: dict[str,str] = dict(DEGOV1D='DEGOV1', GASTD='GAST', IEESGOD='IEESGO', HYGOVD='HYGOV', HYGOV2D='HYGOV2', PIDGOVD='PIDGOV', TGOV1D='TGOV1')
        parent_name: str | None = deadband_parents.get(model.upper(),None)
        if parent_name is not None:
            parent: DynamicModelSchema | None = super().get_model_schema(parent_name)
            if parent is None:
                return None
            else:
                return DynamicModelSchema(model.upper(),parent.parameters+('DBH','DBL','TRATE'),
                    parent.icon_names,parent.character_icon_names,parent.signed_icon_names)
        elif model.upper() in ('AC6C','AC6C2'):
            fields: tuple[str,...] = ('TR','KA','TA','TK','TB','TC','VAMAX','VAMIN','VRMAX','VRMIN','TE','VFELIM','KH','VHMAX','TH','TJ','KC','KD','KE','E1','SE1','E2','SE2','VFEMAX','VEMIN')
            icons: tuple[str,...] = ('OEL','UEL','LIMIT_DEPENDENCY') if model.upper() == 'AC6C2' else ('OEL','UEL')
            return DynamicModelSchema(model.upper(),fields,icons)
        elif model.upper() == 'AC9C':
            # Model Library 35.2 section 6.14: four ICONs and 42 ordered CONs.
            return DynamicModelSchema('AC9C',
                ('TR','KPR','KIR','KDR','TDR','VPIDMAX','VPIDMIN','KPA','KIA',
                 'VAMAX','VAMIN','KA','TA','VRMAX','VRMIN','KF','TF','KFW',
                 'VFWMAX','VFWMIN','SCT','KC','KD','KE','TE','VFEMAX','VEMIN','E1',
                 'SE1','E2','SE2','KP','KI1','KI2','KC1','KC2','XL','THETAP',
                 'VB1MAX','VB2MAX','VLIM1','VLIM2'),
                ('OEL','UEL','SCL','SW1'))
        elif model.upper() == 'AC11C':
            # Model Library 35.2 section 6.15: five ICONs and 36 ordered CONs.
            return DynamicModelSchema('AC11C',
                ('TR','KPA','TIA','KPU','TIU','KB','TB','KPO','TIO','VRSMAX',
                 'VRSMIN','VRMAX','VRMIN','VAMAX','VAMIN','TE','KC','KD','KE',
                 'VFEMAX','VEMIN','E1','SE1','E2','SE2','KP','KI1','XL','THETAP',
                 'KC1','VB1MAX','KI2','KC2','VB2MAX','KBOOST','VBOOST'),
                ('PSS','OEL','UEL','SCL','SW1'))
        elif model.upper() == 'AC3C':
            # Model Library 35.2 section 6.3 has a 28-CON table and a 22-CON
            # sample record; preserve both without resolving PID activation.
            return DynamicModelSchema(
                'AC3C',
                ('TR','TB','TC','KA','TA','VAMAX','VAMIN','TE','VEMIN','KR',
                 'KF','TF','KN','EFDN','KC','KD','KE','VFEMAX','E1','SE1','E2',
                 'SE2','KPA','KIA','KDA','TDA','VPIDMAX','VPIDMIN'),
                ('OEL','UEL'), alternative_parameter_counts=(22,),
            )
        elif model.upper() == 'COMPCC':
            # Model Library 35.2 section 2.3: M identifies machine 2 at IBUS.
            return DynamicModelSchema('COMPCC', ('R1','X1','R2','X2'), ('M',), ('M',))
        elif model.upper() == 'CCOMP4A':
            # Model Library 35.2 section 2.1: each linked unit has a bus
            # number and a quoted machine identifier before the seven CONs.
            return DynamicModelSchema(
                'CCOMP4A', ('K1','K2','K3','K4','KC','VMAX','VMIN'),
                ('BUS2','ID2','BUS3','ID3','BUS4','ID4'),
                ('ID2','ID3','ID4'),
            )
        elif model.upper() == 'REGCA1':
            # Model Library 35.2 section 17.3: direct converter record, not
            # the earlier REGCAU1 user-model allocation wrapper.
            return DynamicModelSchema('REGCA1',
                ('TG','RRPWR','BRKPT','ZEROX','LVPL1','VOLIM','LVPNT1','LVPNT0',
                 'IOLIM','TFLTR','KHV','IQRMAX','IQRMIN','ACCEL'),
                ('LVPLSW',))
        elif model.upper() == 'DERA1':
            # Model Library 35.2 section 17.1: direct DER converter record.
            return DynamicModelSchema(
                'DERA1',
                ('TRV','TRF','DBD1','DBD2','KQV','VREF0','TP','TIQ','DDN','DUP',
                 'FDBD1','FDBD2','FEMAX','FEMIN','PMAX','PMIN','DPMAX','DPMIN',
                 'TPORD','KPG','KIG','IMAX','VL0','VL1','VH0','VH1','TVL0','TVL1',
                 'TVH0','TVH1','VRFRAC','FL','FH','TFL','TFH','TG','RRPWR','TV',
                 'VPR','IQHL','IQLL'),
                ('PFFLAG','FREQFLAG','PQFLAG','GENFLAG','VTRIPFLAG','FTRIPFLAG'),
            )
        elif model.upper() == 'REECC1':
            # Model Library 35.2 section 18.4: battery electrical-control model.
            return DynamicModelSchema(
                'REECC1',
                ('VDIP','VUP','TRV','DBD1','DBD2','KQV','IQH1','IQL1','VREF0',
                 'TP','QMAX','QMIN','VMAX','VMIN','KQP','KQI','KVP','KVI','TIQ',
                 'DPMAX','DPMIN','PMAX','PMIN','IMAX','TPORD','VQ1','IQ1','VQ2',
                 'IQ2','VQ3','IQ3','VQ4','IQ4','VP1','IP1','VP2','IP2','VP3',
                 'IP3','VP4','IP4','T','SOCINI','SOCMAX','SOCMIN'),
                ('VCBUS','PFFLAG','VFLAG','QFLAG','PQFLAG'),
            )
        elif model.upper() in ('CIM5AL','CIM5AR','CIM5BL','CIM5OW','CIM5ZN'):
            # Model Library 35.2 section 9.2: single/double-cage CIM5 load motor.
            return DynamicModelSchema(
                model.upper(),
                ('RA','XA','XM','R1','X1','R2','X2','E1','SE1','E2','SE2',
                 'MBASE','PMULT','H','VI','TI','TB','D','TNOM'),
                ('IT',),
            )
        elif model.upper() in ('CIM6AL','CIM6AR','CIM6BL','CIM6OW','CIM6ZN'):
            # Model Library 35.2 section 9.3: polynomial torque CIM6 load motor.
            return DynamicModelSchema(
                model.upper(),
                ('RA','XA','XM','R1','X1','R2','X2','E1','SE1','E2','SE2',
                 'MBASE','PMULT','H','VI','TI','TB','A','B','D','E','C0','TNOM'),
                ('IT',),
            )
        elif model.upper() in ('CIMWAL','CIMWAR','CIMWBL','CIMWOW','CIMWZN'):
            # Model Library 35.2 section 9.4: WECC torque CIMW load motor.
            return DynamicModelSchema(
                model.upper(),
                ('RA','XA','XM','R1','X1','R2','X2','E1','SE1','E2','SE2',
                 'MBASE','PMULT','H','VI','TI','TB','A','B','D','E'),
                ('IT',),
            )
        elif model.upper() in ('CIMTR1', 'CIMTR2', 'CIMTR3', 'CIMTR4'):
            # Model Library 35.2 sections 1.4–1.7 list distinct direct-record
            # tails for generator/motor role and the sixth-state variants.
            induction_fields: tuple[str, ...] = (
                'TP', 'TPP', 'H', 'X', 'XP', 'XPP', 'XL', 'E1', 'SE1', 'E2', 'SE2',
            )
            if model.upper() == 'CIMTR1':
                return DynamicModelSchema('CIMTR1', induction_fields + ('SWITCH',), ('MEMORY',))
            elif model.upper() == 'CIMTR2':
                return DynamicModelSchema('CIMTR2', induction_fields + ('D',), ('MEMORY',))
            elif model.upper() == 'CIMTR3':
                return DynamicModelSchema('CIMTR3', induction_fields + ('SWITCH', 'SYNPOW'), ('MEMORY',))
            else:
                return DynamicModelSchema('CIMTR4', induction_fields + ('D', 'SYNTOR'), ('MEMORY',))
        elif model.upper() == 'TGOV3':
            # Model Library 35.2 section 7.43: modified Type 1 with fast valving.
            return DynamicModelSchema(
                'TGOV3', ('K','T1','T2','T3','UO','UC','PMAX','PMIN','T4','K1',
                          'T5','K2','T6','K3','TA','TB','TC','PRMAX'),
            )
        elif model.upper() == 'MAXEX2':
            # Model Library 35.2 section 5.3: mode plus ten ordered limiter constants.
            return DynamicModelSchema(
                'MAXEX2', ('RATED','LEVEL1','TIME1','LEVEL2','TIME2','LEVEL3',
                           'TIME3','DESIRED_LEVEL','KMX','VLOW'), ('M',),
            )
        elif model.upper() == 'MAXEX1':
            # Model Library 35.2 section 5.2 DYR syntax carries ten CONs and no ICON.
            return DynamicModelSchema(
                'MAXEX1', ('EFDRATED','EFD1','TIME1','EFD2','TIME2','EFD3',
                           'TIME3','EFDDES','KMX','VLOW'),
            )
        elif model.upper() == 'ST6B':
            # Model Library 35.2 section 6.79: OEL selector and sixteen CONs.
            return DynamicModelSchema(
                'ST6B', ('TR','KPA','KIA','KDA','TDA','VAMAX','VAMIN','KFF',
                         'KM','KCI','KLR','ILR','VRMAX','VRMIN','KG','TG'),
                ('OEL',),
            )
        elif model.upper() == 'UEL2C':
            # Model Library 35.2 section 4.6: four ICONs and 47 ordered CONs.
            return DynamicModelSchema(
                'UEL2C',
                ('TUV','TUP','TUQ','KUI','KUL','VUIMAX','VUIMIN','KUF','KFB','TUL',
                 'TU1','TU2','TU3','TU4','P0','Q0','P1','Q1','P2','Q2','P3','Q3',
                 'P4','Q4','P5','Q5','P6','Q6','P7','Q7','P8','Q8','P9','Q9',
                 'P10','Q10','VULMAX','VULMIN','VBIAS','KFIX','TADJ','TQREF',
                 'VUELMAX2','VUELMIN2','VUELMAX1','VUELMIN1','XQ'),
                ('K1','K2','THIRD_QUADRANT','GAIN_REDUCTION'),
            )
        elif model.upper() == 'ST9C':
            # Model Library 35.2 section 6.84: four ICONs and eighteen CONs.
            return DynamicModelSchema(
                'ST9C', ('TR','TCD','TBD','ZA','KA','KU','TA','TAUEL','VRMAX','VRMIN',
                         'KAS','TAS','KP','THETAP','KI','XL','KC','VBMAX'),
                ('OEL','UEL','SCL','SW1'),
            )
        elif model.upper() == 'ST10C':
            # Model Library 35.2 section 6.85: five ICONs and 25 ordered CONs.
            return DynamicModelSchema(
                'ST10C', ('TR','KR','TC1','TB1','TC2','TB2','TUC1','TUB1',
                          'TUC2','TUB2','TOC1','TOB1','TOC2','TOB2','VRSMAX',
                          'VRSMIN','VRMAX','VRMIN','T1','KP','KC','KI','XL',
                          'THETAP','VBMAX'),
                ('PSS','OEL','UEL','SCL','SW1'),
            )
        elif model.upper() == 'ST8C':
            # Model Library 35.2 section 6.83: four ICONs and 24 ordered CONs.
            return DynamicModelSchema(
                'ST8C', ('TR','KPR','KIR','VPIMAX','VPIMIN','KPA','KIA','VAMAX',
                         'VAMIN','KA','TA','VRMAX','VRMIN','KF','TF','KC1','KP',
                         'KI1','XL','THETAP','VB1MAX','KC2','KI2','VB2MAX'),
                ('OEL','UEL','SCL','SW1'),
            )
        elif model.upper() == 'TGOV2':
            # Model Library 35.2 section 7.42: four-state fast-valving governor.
            return DynamicModelSchema(
                'TGOV2', ('R','T1','VMAX','VMIN','K','T3','DT','TT','TA','TB','TC'),
            )
        elif model.upper() == 'OEL2C':
            # Model Library 35.2 section 5.4: two selector ICONs and 41 CONs.
            return DynamicModelSchema(
                'OEL2C',
                ('TC1OEL','TB1OEL','TC2OEL','TB2OEL','KPOEL','KIOEL','KDOEL','TDOEL',
                 'VOELMAX3','VOELMIN3','VOELMAX2','VOELMIN2','VOELMAX1','VOELMIN1',
                 'IRESET','TEN','TOFF','ITHOFF','KSCALE','TROEL','KACT','ITFPU','IINST',
                 'ILIM','TAOEL','C1','K1','C2','K2','VINVMAX','VINVMIN','FixedRU','FixedRD',
                 'TFCL','TMAX','TMIN','KFB','KRD','KRU','KZRU','IFDRATED'),
                ('INPUT','SW1'),
            )
        elif model.upper() == 'UEL1':
            # Model Library 35.2 section 4.4: direct 15-CON IEEE 421.5 limiter.
            return DynamicModelSchema(
                'UEL1',
                ('KUR','KUC','KUF','VURMAX','VUCMAX','KUI','KUL','VUIMAX',
                 'VUIMIN','TU1','TU2','TU3','TU4','VULMAX','VULMIN'),
            )
        elif model.upper() == 'PSS6C':
            # Model Library 35.2 section 3.13: four ICONs and thirty CONs.
            return DynamicModelSchema(
                'PSS6C',
                ('T1','KS2','T2','KS1','T3','MACC','T4','TD','K0','K1','K2','K3','K4',
                 'TI1','TI2','KI3','TI3','KI4','TI4','KS','VSL1MAX','VSL1MIN','VSL2MAX',
                 'VSL2MIN','VSTMAX','VSTMIN','PSSON','PSSOFF','XCOMP','TCOMP'),
                ('ICS1','REMBUS1','ICS2','REMBUS2'),
            )
        elif model.upper() == 'BEPSST':
            # PSS/E 35.2 Model Library section 3.1 retains the 33.10 contract.
            return DynamicModelSchema(
                'BEPSST',
                ('K1','K2','T1','T2','T3','T4','T5','T6','T7','T8','T9','T10',
                 'LSMAX','LSMIN','VCU','VCL','K','T11','T12','CRT','CLIM'),
                ('ICS1','IB1','IC2','IB2','ITS'),
            )
        elif model.upper() == 'OSTB2T':
            # PSS/E 35.2 Model Library section 3.5 retains the 20-CON order.
            return DynamicModelSchema('OSTB2T', (
                'K','TS','T1_T3','T3','T2_T4','T4','HLIM','LLIM','KANG','TANG',
                'VNGMX','VMGMX','T_ON','T_OFF','VSMX','VSMN','DWTHR','ETHR',
                'EFDTHR','TSEAL',
            ))
        elif model.upper() == 'OSTB5T':
            # PSS/E 35.2 Model Library section 3.6 retains the 20-CON order.
            return DynamicModelSchema('OSTB5T', (
                'K','TS','T1','T2','T3_T4','T4','HLIM','LLIM','KANG','TANG',
                'VNGMX','VMGMX','T_ON','T_OFF','VSMX','VSMN','DWTHR','ETHR',
                'EFDTHR','TSEAL',
            ))
        elif model.upper() == 'HYGOVR1':
            # PSS/E 35.2 Model Library section 7.20, pages 351–352.
            return DynamicModelSchema('HYGOVR1', (
                'DB1','ERR','TD','T1','T2','T3','T4','T5','T6','T7','T8',
                'KP','R','TT','KG','TP','VELOPEN','VELCLOSE','PMAX','PMIN',
                'DB2','TW','AT','DTURB','QNL','TRATE',
            ))
        elif model.upper() in ('AC6A','ESAC6A'):
            # Model Library 35.2 sections 6.6/6.30 list 23 CONs for both.
            # AC6A's sample record says J through J+20, contradicting its table.
            return DynamicModelSchema(model.upper(),
                ('TR','KA','TA','TK','TB','TC','VAMAX','VAMIN','VRMAX','VRMIN',
                 'TE','VFELIM','KH','VHMAX','TH','TJ','KC','KD','KE','E1','SE1',
                 'E2','SE2'))
        elif model.upper() == 'REECA1':
            # Model Library 35.2 section 18.2, direct six-ICON assignment.
            return DynamicModelSchema('REECA1',
                ('VDIP','VUP','TRV','DBD1','DBD2','KQV','IQH1','IQL1','VREF0',
                 'IQFRZ','THLD','THLD2','TP','QMAX','QMIN','VMAX','VMIN','KQP',
                 'KQI','KVP','KVI','VBIAS','TIQ','DPMAX','DPMIN','PMAX','PMIN',
                 'IMAX','TPORD','VQ1','IQ1','VQ2','IQ2','VQ3','IQ3','VQ4','IQ4',
                 'VP1','IP1','VP2','IP2','VP3','IP3','VP4','IP4'),
                ('VCBUS','PFFLAG','VFLAG','QFLAG','PFLAG','PQFLAG'))
        elif model.upper() == 'WTDTA1':
            # Model Library 35.2 section 19.4: direct five-CON drive train.
            return DynamicModelSchema('WTDTA1',('H','DAMP','HTFRAC','FREQ1','DSHAFT'))
        elif model.upper() == 'WT12T1':
            # Model Library 35.2 section 19.2: Type 1/2 five-CON shaft.
            return DynamicModelSchema('WT12T1',('H','DAMP','HTFRAC','FREQ1','DSHAFT'))
        elif model.upper() == 'WT1G1':
            # Model Library 35.2 section 17.6: Type 1 induction generator.
            return DynamicModelSchema('WT1G1',
                ('TPO','TPPO','X','XP','XPP','XL','E1','SE1','E2','SE2'))
        elif model.upper() == 'WT2G1':
            # Model Library 35.2 section 17.7: Type 2 rotor-resistance generator.
            return DynamicModelSchema('WT2G1',
                ('XA','XM','X1','R_ROT_MACH','R_ROT_MAX','E1','SE1','E2','SE2',
                 'POWER_REF_1','POWER_REF_2','POWER_REF_3','POWER_REF_4','POWER_REF_5',
                 'SLIP_1','SLIP_2','SLIP_3','SLIP_4','SLIP_5'))
        elif model.upper() == 'WT2E1':
            # Model Library 35.2 section 18.6: Type 2 resistance controller.
            return DynamicModelSchema('WT2E1',
                ('TSP','TPE','TI','KP','ROTRV_MAX','ROTRV_MIN'))
        elif model.upper() == 'WTARA1':
            # Model Library 35.2 section 21.3: direct pitch-response record.
            return DynamicModelSchema('WTARA1',('KA','THETA0'))
        elif model.upper() == 'WT12A1':
            # Model Library 35.2 section 21.1: Type 1/2 pseudo governor.
            return DynamicModelSchema('WT12A1',
                ('DROOP','KP','TI','T1','T2','TP','LIMMAX','LIMMIN'))
        elif model.upper() == 'WTPTA1':
            # Model Library 35.2 section 20.3: direct Type 3 pitch record.
            return DynamicModelSchema('WTPTA1',
                ('KIW','KPW','KIC','KPC','KCC','TP','TETAMAX','TETAMIN','RTETAMAX','RTETAMIN'))
        elif model.upper() == 'WTTQA1':
            # Model Library 35.2 section 22.1: one TFLAG and fifteen CONs.
            return DynamicModelSchema('WTTQA1',
                ('KPP','KIP','TP','TWREF','TEMAX','TEMIN','P1','SPD1',
                 'P2','SPD2','P3','SPD3','P4','SPD4','TRATE'),('TFLAG',))
        elif model.upper() in ('REPCA1','REPCTA1'):
            # Model Library 35.2 section 23.2: type-4/type-3 plant controls
            # share a record layout, but not their downstream command path.
            return DynamicModelSchema(model.upper(),
                ('TFLTR','KP','KI','TFT','TFV','VFRZ','RC','XC','KC','EMAX',
                 'EMIN','DBD1','DBD2','QMAX','QMIN','KPG','KIG','TP','FDBD1',
                 'FDBD2','FEMAX','FEMIN','PMAX','PMIN','TG','DDN','DUP'),
                ('VCBUS','FROMBUS','TOBUS','CKT','VCFLAG','REFFLAG','FFLAG'),
                ('CKT',))
        elif model.upper() == 'AC7C':
            return DynamicModelSchema('AC7C',('TR','KPR','KIR','KDR','TDR','VRMAX','VRMIN','KPA','KIA','VAMAX','VAMIN','KP','KL','KF1','KF2','KF3','TF3','KC','KD','KE','TE','VFEMAX','VEMIN','E1','SE1','E2','SE2','KI','XL','THETAP','KC1','VBMAX','KR'),('OEL','UEL','SCL','PSS','SW1','SW2'))
        elif model.upper() == 'ST6C':
            return DynamicModelSchema('ST6C',('TR','KPA','KIA','KDA','TDA','VAMAX','VAMIN','KFF','KM','KCI','KLR','ILR','VRMAX','VRMIN','KG','TG','VMMAX','VMMIN','TA','KP','KI','XL','THETAP','KC','VBMAX'),('OEL','UEL','SCL','SW1'))
        elif model.upper() == 'DC4C':
            return DynamicModelSchema('DC4C',('TR','KPR','KJR','KDR','TDR','VRMAX','VRMIN','KA','TA','KE','TE','KF','TF','VEMIN','E1','SE1','E2','SE2','KP','KI','XL','THETAP','KC1','VBMAX'),('OEL','UEL','SCL','SW1'))
        elif model.upper() == 'AC8C':
            return DynamicModelSchema('AC8C',('TR','KPR','KIR','KDR','TDR','VPIDMAX','VPIDMIN','KA','TA','VRMAX','VRMIN','KC','KD','KE','TE','VFEMAX','VEMIN','E1','SE1','E2','SE2','KP','KI','XL','THETAP','KC1','VBMAX'),('OEL','UEL','SCL','PSS','SW1'))
        elif model.upper() == 'ST5C':
            return DynamicModelSchema('ST5C',('TR','TC1','TB1','TC2','TB2','KR','VRMAX','VRMIN','T1','KC','TUC1','TUB1','TUC2','TUB2','TOC1','TOB1','TOC2','TOB2'),('OEL','UEL'))
        elif model.upper() == 'ST4C':
            return DynamicModelSchema('ST4C',('TR','KPR','KIR','VRMAX','VRMIN','KPM','KIM','VMMAX','VMMIN','TA','VAMAX','VAMIN','KG','TG','VGMAX','KP','KI','XL','THETAP','KC','VBMAX'),('PSS','OEL','UEL','SCL','SW1'))
        elif model.upper() == 'ST7C':
            return DynamicModelSchema('ST7C',('TR','TG','TF','VMAX','VMIN','KPA','VRMAX','VRMIN','KH','KL','TC','TB','KIA','TIA','TA'),('OEL','UEL'))
        elif model.upper() == 'ST1C':
            return DynamicModelSchema('ST1C',('TR','VIMAX','VIMIN','TC','TB','TC1','TB1','KA','TA','VAMAX','VAMIN','VRMAX','VRMIN','KC','KF','TF','KLR','ILR'),('UEL','VOS','OEL'))
        elif model.upper() == 'AC5C':
            return DynamicModelSchema('AC5C',('TR','KA','TA','VRMAX','VRMIN','KE','TE','KF','TF1','TF2','TF3','E1','SE1','E2','SE2','KC','KD','VFEMAX','VEMIN'),('OEL','UEL'))
        elif model.upper() == 'AC1C':
            return DynamicModelSchema('AC1C',('TR','TB','TC','KA','TA','VAMAX','VAMIN','TE','KF','TF','KC','KD','KE','E1','SE1','E2','SE2','VRMAX','VRMIN','VFEMAX','VEMIN'),('OEL','UEL'))
        elif model.upper() == 'AC2C':
            return DynamicModelSchema('AC2C',('TR','TB','TC','KA','TA','VAMAX','VAMIN','KB','VRMAX','VRMIN','TE','VFEMAX','KH','KF','TF','KC','KD','KE','E1','SE1','E2','SE2','VEMIN'),('OEL','UEL'))
        elif model.upper() == 'AC4C':
            return DynamicModelSchema('AC4C',('TR','VIMAX','VIMIN','TC','TB','KA','TA','VRMAX','VRMIN','KC'),('OEL','UEL'))
        elif model.upper() in ('DC1C','DC2C'):
            return DynamicModelSchema(model.upper(),('TR','KA','TA','TB','TC','VRMAX','VRMIN','KE','TE','KF','TF','E1','SE1','E2','SE2','VEMAX','VEMIN'),('OEL','UEL'))
        elif model.upper() == 'PSS2C':
            return DynamicModelSchema('PSS2C',('TW1','TW2','T6','TW3','TW4','T7','KS2','KS3','T8','T9','KS1','T1','T2','T3','T4','T10','T11','VS1MAX','VS1MIN','VS2MAX','VS2MIN','VSTMAX','VSTMIN','T12','T13','PSSON','PSSOFF','XCOMP','TCOMP'),('ICS1','REMBUS1','ICS2','REMBUS2','M','N'))
        elif model.upper() == 'BUDCZT':
            # Model Library 35.2 section 6.17 puts TE before TA.
            return DynamicModelSchema('BUDCZT',('KP','KA','KE','TR','TI','TE','TA','URMAX','URMIN','EFDMAX','EFDMIN'))
        elif model.upper() == 'GGOV1D':
            base: DynamicModelSchema | None = super().get_model_schema('GGOV1')
            if base is None:
                return None
            else:
                return DynamicModelSchema('GGOV1D', base.parameters+('DBH', 'DBL'),
                    base.icon_names, base.character_icon_names, base.signed_icon_names)
        elif model.upper() == 'IEEEG1D':
            return DynamicModelSchema('IEEEG1D', ('K', 'T1', 'T2', 'T3', 'UO', 'UC', 'PMAX', 'PMIN',
                'T4', 'K1', 'K2', 'T5', 'K3', 'K4', 'T6', 'K5', 'K6', 'T7', 'K7', 'K8',
                'DBH', 'DBL', 'TRATE'), ('JBUS', 'JD'), ('JD',))
        elif model.upper() == 'IEEEG3D':
            return DynamicModelSchema('IEEEG3D', ('TG', 'TP', 'UO', 'UC', 'PMAX', 'PMIN',
                'SIGMA', 'DELTA', 'TR', 'TW', 'A11', 'A13', 'A21', 'A23', 'DBH', 'DBL', 'TRATE'))
        else:
            return super().get_model_schema(model)

    def get_auxiliary_signal_schema(self, model: str) -> DynamicModelSchema | None:
        """Select the PSS/E 35.2 frequency auxiliary-signal contract.

        :param model: Source model identifier, case-insensitive.
        :return: CPAAUT's release-owned layout or an unchanged inherited layout.
        """
        if model.upper() == 'CPAAUT':
            # Model Library 35.2 section 12.2 preserves the 33.10 record signature.
            return DynamicModelSchema('CPAAUT', ('CM','TB','TA','PMAX','PMIN'), ('BUS',))
        else:
            return super().get_auxiliary_signal_schema(model)

    def get_user_model_schema(self, name: str) -> UserDynamicModelSchema | None:
        """Select reviewed PSS/E 35.2 user load and control wrappers.

        :param name: Exact user-subroutine identifier.
        :return: Reviewed layout/allocation or inherited unreviewed result.
        """
        if name.upper() == 'WT12A1U_B':
            # Model Library 35.2 section 21.2: 105,0,1,14,3,2.
            return UserDynamicModelSchema(DynamicModelSchema('WT12A1U_B',
                ('TR','RMAX','RMIN','T0','PMIN','PSET','VT1','T1','VT2','T2',
                 'VT3','T3','VT4','T4'),('RESERVED',)),
                UserModelType.RENEWABLE_AERODYNAMIC,0,3,2)
        elif name.upper() == 'PSS7C':
            # Model Library 35.2 section 3.14: 3,0,6,32,19,5 allocation.
            return UserDynamicModelSchema(DynamicModelSchema('PSS7C', (
                'TW1','KW2','T6','TW3','TW4','T7','KS2','KS3','T8','T9',
                'KS1','K0','K1','K2','K3','K4','TI1','TI2','KI3','TI3','KI4','TI4',
                'VSL1MAX','VSL1MIN','VSL2MAX','VSL2MIN','VSTMAX','VSTMIN','PSSON',
                'PSSOFF','XCOMP','TCOMP',
            ), (
                'ICS1','REMBUS1','ICS2','REMBUS2','M','N',
            )), UserModelType.STABILIZER, 0, 19, 5)
        elif name.upper() == 'AC8BBU2':
            # Model Library 35.2 section 6.12: 4,0,5,35,7,9 allocation.
            return UserDynamicModelSchema(DynamicModelSchema('AC8BBU2', (
                'TR','KPR','KIR','KDR','TDR','VPIDMAX','VPIDMIN','KA','TA',
                'VRMAX','VRMIN','KC','KD','KE','TE','VFEMAX','VEMIN','E1','SE1',
                'E2','SE2','KP','THETAP','KI','XL','KC1','VBMAX','DB','KPL',
                'KIL','KDL','TDL','VPIDLMAX','VPIDLMIN','TOUTER',
            ), (
                'PSS_ENTRY','UEL_ENTRY','OEL_ENTRY','SW1','OUTER_BUS',
            )), UserModelType.EXCITER, 0, 7, 9)
        elif name.upper() in (
                'CMLDBLU2','CMLDOWU2','CMLDZNU2','CMLDARU2','CMLDALU2'):
            # Model Library 35.2 section 9.6: USRLOD, IC=12, NR=48, 2 ICONs,
            # 133 CONs, 27 states and 146 VARs.
            cmld_parameters: tuple[str, ...] = (
                'LOAD_MVA_BASE','BSHUNT','RFDR','XFDR','FB','XXF','TFIXHS','TFIXLS',
                'LTC','TMIN','TMAX','TSTEP','VMIN','VMAX','TD','TC','RCMP','XCMP',
                'FMA','FMB','FMC','FMD','FEL','PFEL','VD1','VD2','PFS','P1E','P1C',
                'P2E','P2C','PFRQ','Q1E','Q1C','Q2E','Q2C','QFRQ',
                'MTYPA','LFMA','RAA','LSA','LPA','LPPA','TPOA','TPPOA','HA','ETRQA',
                'VTR1A','TTR1A','FTR1A','VRC1A','TRC1A','VTR2A','TTR2A','FTR2A',
                'VRC2A','TRC2A','MTYPB','LFMB','RAB','LSB','LPB','LPPB','TPOB',
                'TPPOB','HB','ETRQB','VTR1B','TTR1B','FTR1B','VRC1B','TRC1B',
                'VTR2B','TTR2B','FTR2B','VRC2B','TRC2B','MTYPC','LFMC','RAC',
                'LSC','LPC','LPPC','TPOC','TPPOC','HC','ETRQC','VTR1C','TTR1C',
                'FTR1C','VRC1C','TRC1C','VTR2C','TTR2C','FTR2C','VRC2C','TRC2C',
                'TSTALL','TRESTART','TV','TF','COMPLF','COMPPF','VSTALL','RSTALL',
                'XSTALL','LFADJ','KP1','NP1','KQ1','NQ1','KP2','NP2','KQ2','NQ2',
                'VBRK','FRST','VRST','CMPKPF','CMPKQF','VC1OFF','VC2OFF','VC1ON',
                'VC2ON','TTH','TH1T','TH2T','FUVR','UVTR1','TTR1','UVTR2','TTR2',
                'FEL_RESTART',
            )
            scope_call_types: dict[str, int] = dict(BL=1, OW=2, ZN=3, AR=4, AL=5)
            scope: str = name.upper()[-4:-2]
            call_type: int = scope_call_types[scope]
            layout: DynamicModelSchema = DynamicModelSchema(
                name.upper(), cmld_parameters, ('INTERNAL_STORAGE_1','INTERNAL_STORAGE_2'),
            )
            return UserDynamicModelSchema(
                layout, UserModelType.LOAD, call_type, 27, 146, reserved_icon_count=48,
            )
        elif name.upper() in (
                'ACMTBLU1','ACMTOWU1','ACMTZNU1','ACMTARU1','ACMTALU1'):
            # Model Library 35.2 section 9.1: USRLOD, IC=12, NR=16, 0 ICONs,
            # 35 CONs, 9 states and 29 VARs.
            acmt_parameters: tuple[str, ...] = (
                'TSTALL','TRESTART','TV','TF','COMPLF','COMPPF','VSTALL','RSTALL',
                'XSTALL','LFADJ','KP1','NP1','KQ1','NQ1','KP2','NP2','KQ2','NQ2',
                'VBRK','FRST','VRST','CMPKPF','CMPKQF','VC1OFF','VC2OFF','VC1ON',
                'VC2ON','TTH','TH1T','TH2T','FUVR','UVTR1','TTR1','UVTR2','TTR2',
            )
            scope_call_types: dict[str, int] = dict(BL=1, OW=2, ZN=3, AR=4, AL=5)
            scope = name.upper()[-4:-2]
            call_type = scope_call_types[scope]
            layout = DynamicModelSchema(name.upper(), acmt_parameters)
            return UserDynamicModelSchema(
                layout, UserModelType.LOAD, call_type, 9, 29, reserved_icon_count=16,
            )
        else:
            return super().get_user_model_schema(name)
