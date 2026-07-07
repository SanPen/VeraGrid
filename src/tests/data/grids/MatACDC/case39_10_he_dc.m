%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%%%                                                                  %%%%%
%%%%    IEEE PES Power Grid Library - Optimal Power Flow - v23.09     %%%%%
%%%%          (https://github.com/power-grid-lib/pglib-opf)           %%%%%
%%%%               Benchmark Group - Typical Operations               %%%%%
%%%%                         10 - May - 2019                          %%%%%
%%%%                                                                  %%%%%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%
%   CASE39 Power flow data for 39 bus New England system.
%
%   Data taken from [1] with the following modifications/additions:
%
%       - renumbered gen buses consecutively (as in [2] and [4])
%       - added Pmin = 0 for all gens
%       - added Qmin, Qmax for gens at 31 & 39 (copied from gen at 35)
%       - added Vg based on V in bus data (missing for bus 39)
%       - added Vg, Pg, Pd, Qd at bus 39 from [2] (same in [4])
%       - added Pmax at bus 39: Pmax = Pg + 100
%       - added line flow limits and area data from [4]
%       - added voltage limits, Vmax = 1.06, Vmin = 0.94
%       - added identical quadratic generator costs
%       - increased Pmax for gen at bus 34 from 308 to 508
%         (assumed typo in [1], makes initial solved case feasible)
%       - re-solved power flow
% 
%   Notes:
%       - Bus 39, its generator and 2 connecting lines were added
%         (by authors of [1]) to represent the interconnection with
%         the rest of the eastern interconnect, and did not include
%         Vg, Pg, Qg, Pd, Qd, Pmin, Pmax, Qmin or Qmax.
%       - As the swing bus, bus 31 did not include and Q limits.
%       - The voltages, etc in [1] appear to be quite close to the
%         power flow solution of the case before adding bus 39 with
%         it's generator and connecting branches, though the solution
%         is not exact.
%       - Explicit voltage setpoints for gen buses are not given, so
%         they are taken from the bus data, however this results in two
%         binding Q limits at buses 34 & 37, so the corresponding
%         voltages have probably deviated from their original setpoints.
%       - The generator locations and types are as follows:
%           1   30      hydro
%           2   31      nuke01
%           3   32      nuke02
%           4   33      fossil02
%           5   34      fossil01
%           6   35      nuke03
%           7   36      fossil04
%           8   37      nuke04
%           9   38      nuke05
%           10  39      interconnection to rest of US/Canada
%
%   This is a solved power flow case, but it includes the following
%   violations:
%       - Pmax violated at bus 31: Pg = 677.87, Pmax = 646
%       - Qmin violated at bus 37: Qg = -1.37,  Qmin = 0
%
%   References:
%   [1] G. W. Bills, et.al., "On-Line Stability Analysis Study"
%       RP90-1 Report for the Edison Electric Institute, October 12, 1970,
%       pp. 1-20 - 1-35.
%       prepared by E. M. Gulachenski - New England Electric System
%                   J. M. Undrill     - General Electric Co.
%       "generally representative of the New England 345 KV system, but is
%        not an exact or complete model of any past, present or projected
%        configuration of the actual New England 345 KV system.
%   [2] M. A. Pai, Energy Function Analysis for Power System Stability,
%       Kluwer Academic Publishers, Boston, 1989.
%       (references [3] as source of data)
%   [3] Athay, T.; Podmore, R.; Virmani, S., "A Practical Method for the
%       Direct Analysis of Transient Stability," IEEE Transactions on Power
%       Apparatus and Systems , vol.PAS-98, no.2, pp.573-584, March 1979.
%       URL: http://ieeexplore.ieee.org/stamp/stamp.jsp?arnumber=4113518&isnumber=4113486
%       (references [1] as source of data)
%   [4] Data included with TC Calculator at http://www.pserc.cornell.edu/tcc/
%       for 39-bus system.
%   [5] DC grid data added from: Rimez, J., 2014. Optimal Operation of
%       Hybrid AC/DC Meshed Grids (Optimale uitbating van hybriede vermaasde
%       AC/DC netwerken), PhD Thesis, KU Leuven.
%     
%    
%
%   Created by Hakan Ergun in 2019.
%
%   Copyright (c) 1989 by The Institute of Electrical and Electronics Engineers (IEEE)
%   Licensed under the Creative Commons Attribution 4.0
%   International license, http://creativecommons.org/licenses/by/4.0/
%
%   Contact M.E. Brennan (me.brennan@ieee.org) for inquries on further reuse of
%   this dataset.
%
function [baseMVAac, baseMVAdc, pol, busdc, convdc, branchdc]= case39_10_he_dc
mpc.version = '2';
%% system MVA base
baseMVAac = 100;
baseMVAdc = 100;

%% dc grid topology
%colunm_names% dcpoles
pol=2;
% numbers of poles (1=monopolar grid, 2=bipolar grid)
%% bus data
%column_names%   busdc_i	busac_i	grid	Pdc	Vdc	basekVdc	Vdcmax	Vdcmin	Cdc
busdc = [
1	2	1	0	1	345	1.1	0.9	0;
2	9	1	0	1	345	1.1	0.9	0;
 3	10	1	0	1	345	1.1	0.9	0;
 4	18	1	0	1	345	1.1	0.9	0;
 5	26	1	0	1	345	1.1	0.9	0;
 6	29	1	0	1	345	1.1	0.9	0;
7	24	1	0	1	345	1.1	0.9	0;
8	14	1	0	1	345	1.1	0.9	0;
9	23	1	0	1	345	1.1	0.9	0;
10	13	1	0	1	345	1.1	0.9	0;

];

% %% converters
%column_names%   busdc_i	type_dc	type_ac	P_g	Q_g	Vtar	rtf	xtf	bf	rc	xc	basekVac	Vmmax	Vmmin	Imax	status	LossA	LossB	LossCrec	LossCinv

convdc = [
%1	1	1	-60	-40	1	1e-5	1e-5	0	1e-5	0	345	1.1	0.9	1.1	1	1.1033	0.887	2.885	2.885;
%2	1	1	-60	-40	1	1e-5	1e-5	0	1e-5	0   345	1.1	0.9	1.1	1	1.1033	0.887	2.885	2.885;
%3	1	1	-60	-40	1	1e-5	1e-5	0	1e-5	0	345	1.1	0.9	1.1	1	1.1033	0.887	2.885	2.885;
%4	2	1	-60	-40	1	1e-5	1e-5	0	1e-5	0	345	1.1	0.9	1.1	1	1.1033	0.887	2.885	2.885;
%5	1	1	-60	-40	1	1e-5	1e-5	0	1e-5	0	345	1.1	0.9	1.1	1	1.1033	0.887	2.885	2.885;
%6	1	1	-60	-40	1	1e-5	1e-5	0	1e-5	0	345	1.1	0.9	1.1	1	1.1033	0.887	2.885	2.885;
%7	1	1	-60	-40	1	1e-5	1e-5	0	1e-5	0	345	1.1	0.9	1.1	1	1.1033	0.887	2.885	2.885;
%8	1	1	-60	-40	1	1e-5	1e-5	0	1e-5	0	345	1.1	0.9	1.1	1	1.1033	0.887	2.885	2.885;
%9	1	1	-60	-40	1	1e-5	1e-5	0	1e-5	0	345	1.1	0.9	1.1	1	1.1033	0.887	2.885	2.885;
%10	1	1	-60	-40	1	1e-5	1e-5	0	1e-5	0	345	1.1	0.9	1.1	1	1.1033	0.887	2.885	2.885;

1	1	1	-60	-40	1	1e-7	1e-7	0	1e-7	0	345	1.1	0.9	1.1	1	1.1033	0.887	2.885	2.885;
2	1	1	-60	-40	1	1e-7	1e-7	0	1e-7	0   345	1.1	0.9	1.1	1	1.1033	0.887	2.885	2.885;
3	1	1	-60	-40	1	1e-7	1e-7	0	1e-7	0	345	1.1	0.9	1.1	1	1.1033	0.887	2.885	2.885;
4	2	1	-60	-40	1	1e-7	1e-7	0	1e-7	0	345	1.1	0.9	1.1	1	1.1033	0.887	2.885	2.885;
5	1	1	-60	-40	1	1e-7	1e-7	0	1e-7	0	345	1.1	0.9	1.1	1	1.1033	0.887	2.885	2.885;
6	1	1	-60	-40	1	1e-7	1e-7	0	1e-7	0	345	1.1	0.9	1.1	1	1.1033	0.887	2.885	2.885;
7	1	1	-60	-40	1	1e-7	1e-7	0	1e-7	0	345	1.1	0.9	1.1	1	1.1033	0.887	2.885	2.885;
8	1	1	-60	-40	1	1e-7	1e-7	0	1e-7	0	345	1.1	0.9	1.1	1	1.1033	0.887	2.885	2.885;
9	1	1	-60	-40	1	1e-7	1e-7	0	1e-7	0	345	1.1	0.9	1.1	1	1.1033	0.887	2.885	2.885;
10	1	1	-60	-40	1	1e-7	1e-7	0	1e-7	0	345	1.1	0.9	1.1	1	1.1033	0.887	2.885	2.885;
    ];

%% branches
%column_names%   fbusdc  tbusdc  r      l        c   rateA   rateB   rateC   status
branchdc = [
    1       2       0.01   0   0    100     100     100     1;
    2       3       0.01   0   0    100     100     100     1;
    1       4       0.01   0   0    100     100     100     1;
    2       4       0.01   0   0    100     100     100     1;
    2       4       0.01   0   0    100     100     100     1;
    1       5       0.01   0   0    100     100     100     1;
    5       6       0.01   0   0    100     100     100     1;
    5       7       0.01   0   0    100     100     100     1;
    7       4       0.01   0   0    100     100     100     1;
    4       8       0.01   0   0    100     100     100     1;
    8       9       0.01   0   0    100     100     100     1;
    8      10       0.01   0   0    100     100     100     1;
 ];

% INFO    : === Translation Options ===
% INFO    : Phase Angle Bound:           30.0 (deg.)
% INFO    : Gen Active Cost Model:       stat
% INFO    : Setting Flat Start
% INFO    : 
% INFO    : === Generator Classification Notes ===
% INFO    : NUC    1   -     3.97
% INFO    : COW    9   -    96.03
% INFO    : 
% INFO    : === Generator Active Cost Stat Model Notes ===
% INFO    : Updated Generator Cost: NUC - 0.2 0.3 0.01 -> 0 6.72477811338 0
% INFO    : Updated Generator Cost: COW - 0.2 0.3 0.01 -> 0 14.7076252515 0
% INFO    : Updated Generator Cost: COW - 0.2 0.3 0.01 -> 0 24.8047338223 0
% INFO    : Updated Generator Cost: COW - 0.2 0.3 0.01 -> 0 34.84464286 0
% INFO    : Updated Generator Cost: COW - 0.2 0.3 0.01 -> 0 24.6529938713 0
% INFO    : Updated Generator Cost: COW - 0.2 0.3 0.01 -> 0 32.306483114 0
% INFO    : Updated Generator Cost: COW - 0.2 0.3 0.01 -> 0 18.1574766212 0
% INFO    : Updated Generator Cost: COW - 0.2 0.3 0.01 -> 0 31.5501806971 0
% INFO    : Updated Generator Cost: COW - 0.2 0.3 0.01 -> 0 22.5031675377 0
% INFO    : Updated Generator Cost: COW - 0.2 0.3 0.01 -> 0 27.4344440931 0
% INFO    : 
% INFO    : === Generator Bounds Update Notes ===
% INFO    : 
% INFO    : === Base KV Replacement Notes ===
% INFO    : 
% INFO    : === Transformer Setting Replacement Notes ===
% WARNING : Transformer 23-36 connects the same voltage levels (345.0, 345.0) and has no phase shift, changing tap ratio 1.0 => 0.0
% INFO    : 
% INFO    : === Line Capacity Monotonicity Notes ===
% INFO    : 
% INFO    : === Voltage Setpoint Replacement Notes ===
% INFO    : Bus 1	: V=1.0393836, theta=-13.536602 -> V=1.0, theta=0.0
% INFO    : Bus 2	: V=1.0484941, theta=-9.7852666 -> V=1.0, theta=0.0
% INFO    : Bus 3	: V=1.0307077, theta=-12.276384 -> V=1.0, theta=0.0
% INFO    : Bus 4	: V=1.00446, theta=-12.626734 -> V=1.0, theta=0.0
% INFO    : Bus 5	: V=1.0060063, theta=-11.192339 -> V=1.0, theta=0.0
% INFO    : Bus 6	: V=1.0082256, theta=-10.40833 -> V=1.0, theta=0.0
% INFO    : Bus 7	: V=0.99839728, theta=-12.755626 -> V=1.0, theta=0.0
% INFO    : Bus 8	: V=0.99787232, theta=-13.335844 -> V=1.0, theta=0.0
% INFO    : Bus 9	: V=1.038332, theta=-14.178442 -> V=1.0, theta=0.0
% INFO    : Bus 10	: V=1.0178431, theta=-8.170875 -> V=1.0, theta=0.0
% INFO    : Bus 11	: V=1.0133858, theta=-8.9369663 -> V=1.0, theta=0.0
% INFO    : Bus 12	: V=1.000815, theta=-8.9988236 -> V=1.0, theta=0.0
% INFO    : Bus 13	: V=1.014923, theta=-8.9299272 -> V=1.0, theta=0.0
% INFO    : Bus 14	: V=1.012319, theta=-10.715295 -> V=1.0, theta=0.0
% INFO    : Bus 15	: V=1.0161854, theta=-11.345399 -> V=1.0, theta=0.0
% INFO    : Bus 16	: V=1.0325203, theta=-10.033348 -> V=1.0, theta=0.0
% INFO    : Bus 17	: V=1.0342365, theta=-11.116436 -> V=1.0, theta=0.0
% INFO    : Bus 18	: V=1.0315726, theta=-11.986168 -> V=1.0, theta=0.0
% INFO    : Bus 19	: V=1.0501068, theta=-5.4100729 -> V=1.0, theta=0.0
% INFO    : Bus 20	: V=0.99101054, theta=-6.8211783 -> V=1.0, theta=0.0
% INFO    : Bus 21	: V=1.0323192, theta=-7.6287461 -> V=1.0, theta=0.0
% INFO    : Bus 22	: V=1.0501427, theta=-3.1831199 -> V=1.0, theta=0.0
% INFO    : Bus 23	: V=1.0451451, theta=-3.3812763 -> V=1.0, theta=0.0
% INFO    : Bus 24	: V=1.038001, theta=-9.9137585 -> V=1.0, theta=0.0
% INFO    : Bus 25	: V=1.0576827, theta=-8.3692354 -> V=1.0, theta=0.0
% INFO    : Bus 26	: V=1.0525613, theta=-9.4387696 -> V=1.0, theta=0.0
% INFO    : Bus 27	: V=1.0383449, theta=-11.362152 -> V=1.0, theta=0.0
% INFO    : Bus 28	: V=1.0503737, theta=-5.9283592 -> V=1.0, theta=0.0
% INFO    : Bus 29	: V=1.0501149, theta=-3.1698741 -> V=1.0, theta=0.0
% INFO    : Bus 30	: V=1.0499, theta=-7.3704746 -> V=1.0, theta=0.0
% INFO    : Bus 31	: V=0.982, theta=0.0 -> V=1.0, theta=0.0
% INFO    : Bus 32	: V=0.9841, theta=-0.1884374 -> V=1.0, theta=0.0
% INFO    : Bus 33	: V=0.9972, theta=-0.19317445 -> V=1.0, theta=0.0
% INFO    : Bus 34	: V=1.0123, theta=-1.631119 -> V=1.0, theta=0.0
% INFO    : Bus 35	: V=1.0494, theta=1.7765069 -> V=1.0, theta=0.0
% INFO    : Bus 36	: V=1.0636, theta=4.4684374 -> V=1.0, theta=0.0
% INFO    : Bus 37	: V=1.0275, theta=-1.5828988 -> V=1.0, theta=0.0
% INFO    : Bus 38	: V=1.0265, theta=3.8928177 -> V=1.0, theta=0.0
% INFO    : Bus 39	: V=1.03, theta=-14.535256 -> V=1.0, theta=0.0
% INFO    : 
% INFO    : === Generator Setpoint Replacement Notes ===
% INFO    : Gen at bus 30	: Pg=250.0, Qg=161.762 -> Pg=520.0, Qg=270.0
% INFO    : Gen at bus 30	: Vg=1.0499 -> Vg=1.0
% INFO    : Gen at bus 31	: Pg=677.871, Qg=221.574 -> Pg=323.0, Qg=100.0
% INFO    : Gen at bus 31	: Vg=0.982 -> Vg=1.0
% INFO    : Gen at bus 32	: Pg=650.0, Qg=206.965 -> Pg=362.5, Qg=225.0
% INFO    : Gen at bus 32	: Vg=0.9841 -> Vg=1.0
% INFO    : Gen at bus 33	: Pg=632.0, Qg=108.293 -> Pg=326.0, Qg=125.0
% INFO    : Gen at bus 33	: Vg=0.9972 -> Vg=1.0
% INFO    : Gen at bus 34	: Pg=508.0, Qg=166.688 -> Pg=254.0, Qg=83.5
% INFO    : Gen at bus 34	: Vg=1.0123 -> Vg=1.0
% INFO    : Gen at bus 35	: Pg=650.0, Qg=210.661 -> Pg=343.5, Qg=100.0
% INFO    : Gen at bus 35	: Vg=1.0494 -> Vg=1.0
% INFO    : Gen at bus 36	: Pg=560.0, Qg=100.165 -> Pg=290.0, Qg=120.0
% INFO    : Gen at bus 36	: Vg=1.0636 -> Vg=1.0
% INFO    : Gen at bus 37	: Pg=540.0, Qg=-1.36945 -> Pg=282.0, Qg=125.0
% INFO    : Gen at bus 37	: Vg=1.0275 -> Vg=1.0
% INFO    : Gen at bus 38	: Pg=830.0, Qg=21.7327 -> Pg=432.5, Qg=75.0
% INFO    : Gen at bus 38	: Vg=1.0265 -> Vg=1.0
% INFO    : Gen at bus 39	: Pg=1000.0, Qg=78.4674 -> Pg=550.0, Qg=100.0
% INFO    : Gen at bus 39	: Vg=1.03 -> Vg=1.0
% INFO    : 
% INFO    : === Writing Matpower Case File Notes ===