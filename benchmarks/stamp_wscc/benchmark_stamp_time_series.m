% STAMP WSCC Load-1 1% conductance step, measured on a Multivac compute node.
% BENCH_OUTPUT_DIR and STAMP_ROOT are supplied by the Slurm job.
stamp_root = getenv('STAMP_ROOT');
output_dir = getenv('BENCH_OUTPUT_DIR');
if isempty(stamp_root) || isempty(output_dir)
    error('STAMP_ROOT and BENCH_OUTPUT_DIR must be set');
end
cd(fullfile(stamp_root, 'STAMP'));
path(pathdef); addpath(genpath(pwd));
caseName = 'WSCC_SG_GFOR_GFOL';
path_results = '02_results\';
fanals = 2;

setup_start = tic;
run set_file_names.m
run read_data.m
run preprocess_data.m
run get_parameters.m
set_breaker_state('line', 1, 'close')
run PF_results.m
run update_OP.m
run delta_slack_acdc.m
run generate_NET_with_Qneg.m
run generate_elements.m
input = {'NET.Rld1'};
select_all_outputs;
ss_sys = connect(l_blocks{:}, input, output); %#ok<NASGU>
run NET_initialization.m

% Generate an isolated model so the saved STAMP model is not changed.
nonlinear = 'WSCC_SG_GFOR_GFOL_time_benchmark';
run NET_layout_FORCE.m
run dependent_states.m
newSys = 1;
run param_nonlinear.m
set_param(nonlinear, 'Solver', 'ode1', 'FixedStep', '1e-5', 'StopTime', '0.3');
setup_seconds = toc(setup_start);

% First simulation warms Simulink compilation. Keep three measured repeats.
sim(nonlinear);
set_param(nonlinear, 'FastRestart', 'on');
seconds = zeros(3, 1);
for repetition = 1:3
    timer = tic;
    result = sim(nonlinear);
    seconds(repetition) = toc(timer);
    if repetition == 1
        speed = result.get('SG1_w');
        speed = speed(:) / (2*pi*50); % STAMP exports electrical rad/s.
        time_s = (0:numel(speed)-1)' * sim_config.Tsample;
        if ~exist(output_dir, 'dir'); mkdir(output_dir); end
        writematrix([time_s, speed], fullfile(output_dir, 'stamp_trajectory.csv'));
    end
end
set_param(nonlinear, 'FastRestart', 'off');
close_system(nonlinear, 0);
timings = table((1:3)', seconds, 'VariableNames', {'repetition', 'simulation_seconds'});
writetable(timings, fullfile(output_dir, 'stamp_timing.csv'));
writetable(table(setup_seconds, 'VariableNames', {'setup_seconds'}), ...
           fullfile(output_dir, 'stamp_setup.csv'));
fprintf('STAMP setup %.9g s; simulation median %.9g s; samples %d\n', ...
        setup_seconds, median(seconds), numel(speed));
