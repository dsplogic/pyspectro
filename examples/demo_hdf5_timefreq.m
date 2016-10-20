%% Test data file
% The following file contains data acquired from the spectrometer.
testfile = './data/acq_data_100_measurements.hdf5';

%% Data file format
% Data is stored in the HDF5 file in a simple format.  
% 
% Each Acquisiton is stored in a group, allowing multiple acquisitons
% to be stored in one file.  Each acquisiton group contains three datasets:
% 
% * *fftdata:* Measurement results
% * *msrmnt_num:* Measurement number (id)
% * *num_averages:* Number of accumulated spectra.
%
% Each acquisiton group also contains a 'count' attribute indicating the
% number of measurements recorded for the acquisition.
%
% The contents of the testfile serves as an example:
h5disp(testfile)

%% Reading data from file

% Get name of first acquisition group
info = h5info(testfile);
groupName = info.Groups(1).Name;
disp(['Found acquisiton ' groupName]);

% Get acquired data
measurement_count = h5readatt(testfile,groupName,'count');
fftdata      = h5read(testfile,[groupName '/fftdata']);
msrmt_num    = h5read(testfile,[groupName '/msrmt_num']);
num_averages = h5read(testfile,[groupName '/num_averages']);

%% Plot results
[NfftDiv2,~]  = size(fftdata);
F = (0:(NfftDiv2-1)) * 1000./NfftDiv2;
T = 0:measurement_count-1;
waterfall(T, F, 10*log10(fftdata))
xlabel('Time')
ylabel('Frequency (MHz)')
axis tight
view(90, 90)
