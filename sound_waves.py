#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jun 13 09:40:17 2025

@author: phykc
"""

import numpy as np
import sounddevice as sd
import matplotlib.pyplot as plt
from scipy.signal import find_peaks
import tkinter as Tk
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg,  NavigationToolbar2Tk)
import matplotlib.animation as animation
import threading
from queue import Queue
import matplotlib.patches as patches
from math import pi

def plot_waves(size_fig=3):
    maxnumber=4
    fig, ax=plt.subplots(maxnumber, figsize=(size_fig,3))
    xdata=np.linspace(0, pi, num=200)
    
    for w in range(1,maxnumber+1):
        ax[maxnumber-w].plot(xdata, np.sin(xdata*w), color='black' )
        ax[maxnumber-w].plot(xdata, -1*np.sin(xdata*w), color='black' )
        ax[maxnumber-w].plot(xdata, [0]*len(xdata), '--', color='black' )
        ax[maxnumber-w].set_xlim(0, pi)
        ax[maxnumber-w].axis('off')
        ax[maxnumber-w].text(0,0.5, f'n={w}')
        
    fig.patches.append(
        patches.Rectangle(
            (0, 0.0),  # Lower-left corner in figure coords (0 to 1)
            0.125, 1,    # Width and height in figure coords
            transform=fig.transFigure,
            facecolor='black',
            alpha=0.2,
            edgecolor='black'
        )
    )
    fig.patches.append(
        patches.Rectangle(
            (0.9, 0),  # Lower-left corner in figure coords (0 to 1)
            0.125, 1,    # Width and height in figure coords
            transform=fig.transFigure,
            facecolor='black',
            alpha=0.2,
            edgecolor='black'
        )
    )
    
    return fig, ax


def record_and_plot(root,print_queue):    
    # ----- Configuration -------------------------------------------------
    DURATION  = 2.0         # seconds to record
    FS        = 44_100      # sampling rate (Hz)
    AMPLITUDE = 0.3         # output sine-wave amplitude
    # ---------------------------------------------------------------------
    print_queue.put('Listen­ing… Please make a sound')
    
    recording = sd.rec(int(DURATION * FS), samplerate=FS, channels=1, dtype='float32')
    sd.wait()                       # Blocking until recording is done
    recording = recording.squeeze() # Flatten to 1-D
    
    # ---------------------------------------------------------------------
    # 1. FFT to find dominant frequency
    N        = len(recording)
    freqs    = np.fft.rfftfreq(N, d=1/FS)
    spectrum = np.abs(np.fft.rfft(recording))
    
    # Zero-out DC component to avoid picking up 0 Hz
    spectrum[0] = 0
    peak_idx, _ = find_peaks(spectrum, height=spectrum.max()*0.2)  # simple peak pick
    if len(peak_idx) == 0:
        
        dialogbox.insert(Tk.END, 'No clear peak detected' + '\n')
        dominant_freq = 0.0
    else:
        dominant_freq = freqs[peak_idx[0]]
    
    
    print_queue.put(f"Dominant frequency ≈ {dominant_freq:0.1f} Hz")
    
    # ---------------------------------------------------------------------
    # 2. Generate a pure sine wave at the detected frequency
    t  = np.linspace(0, DURATION, int(FS * DURATION), endpoint=False)
    sine_wave = AMPLITUDE * np.sin(2 * np.pi * dominant_freq * t)
    
    # ---------------------------------------------------------------------
    # 3. Plot the first 20 ms of the recorded signal and the synthetic sine
    ms20 = int(0.02 * FS)  # samples in 20 ms
    
    fig, ax=plt.subplots(2,figsize=(9, 4))
    
    ax[0].set_title("Recorded waveform (first 20 ms)")
    ax[0].plot(t[:ms20]*1000, recording[:ms20])
    ax[0].set_ylabel("Amplitude")
    ax[0].set_xlabel("Time (ms)")
    
    
    ax[1].set_title(f"Sine wave at {dominant_freq:0.1f} Hz (20 ms sample)")
    ax[1].plot(t[:ms20]*1000, sine_wave[:ms20])
    ax[1].set_ylabel("Amplitude")
    ax[1].set_xlabel("Time (ms)")
    
    plt.tight_layout()
    
    window = Tk.Toplevel(root)
    window.title('Sound output')

    canvas1 = FigureCanvasTkAgg(fig, master=window)
    canvas1.draw()
    canvas1.get_tk_widget().pack()

    toolbar = NavigationToolbar2Tk(canvas1, window)
    toolbar.update()
    plt.close(fig)
    
    
    #  Play the synthesized tone back
    if dominant_freq > 0:
        print_queue.put("Playing back the synthesized tone…")
        sd.play(sine_wave, FS)
        sd.wait()

def plotwaves():
    sizes=[3, 9]
    for n in sizes:
        fig, ax=plot_waves(size_fig=n)
        window = Tk.Toplevel(root)
        window.title(f'Length = {n}')
    
        canvas1 = FigureCanvasTkAgg(fig, master=window)
        canvas1.draw()
        canvas1.get_tk_widget().pack()
    
        toolbar = NavigationToolbar2Tk(canvas1, window)
        toolbar.update()
        plt.close(fig)
    


def dialogue_queue_worker(stop_event, dialogbox, print_queue):
    while not stop_event.is_set():
        text = print_queue.get()
        dialogbox.configure(state='normal')
        dialogbox.insert(Tk.END, text + '\n')
        dialogbox.yview(Tk.END)
        dialogbox.configure(state='disabled')
        print_queue.task_done()

def run_soundthread(root, print_queue):
    soundthread = threading.Thread(
        target=record_and_plot,          
        args=(root, print_queue),
        daemon=True
    )
    soundthread.start()
    

print_queue=Queue()
stop_event = threading.Event()
root = Tk.Tk()
root.title('Dominant Frequency Analyser - Critchley')
dialogbox = Tk.Text(root, height=5, width=30, font=10, wrap=Tk.WORD)
dialogbox.pack()
workerthread = threading.Thread(
    target=dialogue_queue_worker,          
    args=(stop_event, dialogbox, print_queue),
    daemon=True
)

button_record=Tk.Button(root, text='Record Sound', command=lambda:run_soundthread(root, print_queue))
button_record.pack()
button_waves=Tk.Button(root, text='Create Diagram', command=plotwaves)
button_waves.pack()
workerthread.start()
root.mainloop()
