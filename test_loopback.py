#!/usr/bin/env python3
#
# loopback test using ocra-pulseq
#

import numpy as np
import matplotlib.pyplot as plt
import pdb, sys
import experiment as ex
import flocra_pulseq.interpreter
st = pdb.set_trace

if __name__ == "__main__":
    lo_freq = 2.1 # MHz
    tx_t = 1.001 # us
    clk_t = 0.007 # ocra system clk for tx and gradients -- rx system clk depends on RP/STEMlab model
    num_grad_channels = 3
    grad_interval = 10.003 # us between [num_grad_channels] channel updates

    do_single_test = True
    do_jitter_test = True

    if len(sys.argv) > 1 and "jitter" in sys.argv:
        do_jitter_test = True
        do_single_test = False
    
    if False: # VN: this stuff belongs in a more sophisticated test, not test_loopback. TODO: refactor/remove
        gamma = 42570000 # Hz/T

        # value for tabletopMRI  gradient coil
        B_per_m_per_current = 0.02 # T/m/A, approximate value for tabletop gradient coil

        # values for gpa fhdo
        gpa_current_per_volt = 3.75 # A/V, theoretical value for gpa fhdo without 2.5 V offset!
        max_dac_voltage = 2.5

        # values for ocra1
        # max_dac_voltage = 5
        # gpa_current_per_volt = 3.75 # A/V, fill in value of gradient power amplifier here!

        max_Hz_per_m = max_dac_voltage * gpa_current_per_volt * B_per_m_per_current * gamma	
        # grad_max = max_Hz_per_m # factor used to normalize gradient amplitude, should be max value of the gpa used!	

    # factor used to normalise RF amplitude, should be max value in system used!
    # (I.e. if unknown, lower values will create larger RF signals, since ocra-pulseq normalises its outputs to this value)
    rf_amp_max = 16

    # as above - for GPA boards, should represent full-scale voltage (or current, if that's being measured)
    # ocra-pulseq normalises its outputs to this value
    grad_max = 10

    ps = flocra_pulseq.interpreter.PSInterpreter(rf_center=lo_freq*1e6,
                     rf_amp_max=rf_amp_max,
                     grad_max=grad_max,
                     clk_t=clk_t,
                     tx_t=tx_t,
                     grad_t=grad_interval,
                     tx_warmup=0)
    
    od, pd = ps.interpret('test_loopback.seq')         
    
    exp = ex.Experiment(lo_freq=lo_freq,
                        rx_t=pd['rx_t'],
                        assert_errors=False,
                        print_infos=True)
    exp.add_flodict(od)

    if False: # test sine for grad/tx
        x = np.linspace(0,2*np.pi, 100)
        ramp_sine = np.sin(2*x)
    
    if do_single_test:
        exp.run()
        
    if do_jitter_test:
        data = []
        trials = 1000
        for k in range(trials):
            d, s = exp.run()
            # TODO: retake when warnings occur due to timeouts etc
            data.append( d ) # Comment out this line to avoid running on the hardware
        
        taxis = np.arange(pd['readout_number'] + 1)*pd['rx_t']
        plt.figure(figsize=(10,9))

        good_data = []
        bad_data = []

        for d in data:
            if np.max(np.abs(d['rx0'])) < 0.1:
                bad_data.append(d['rx0'])
            else:
                good_data.append(d['rx0'])

        lgd = len(good_data)
        lbd = len(bad_data)
                
        plt.subplot(2,1,1)
        for d in good_data:
            plt.plot(taxis, d.real )
        plt.ylabel('loopback rx amplitude')
        plt.title('passing loopback data ({:d}/{:d}, {:.2f}%)'.format(lgd, lgd+lbd, 100*lgd/(lgd+lbd)))
        plt.grid(True)

        plt.subplot(2,1,2)
        for d in bad_data:
            plt.plot(taxis, d.real )
        plt.ylabel('loopback rx amplitude')
        plt.title('failing loopback data ({:d}/{:d}, {:.2f}%)'.format(lbd, lgd+lbd, 100*lbd/(lgd+lbd)))
        plt.grid(True)        
        
        plt.show()
