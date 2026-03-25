"""
WDM (Wavelength Division Multiplexing) Optical Fiber Simulator
Data Communications Assignment — Nirma University, B.Tech CSE Sem IV
Course: 2CS202CC23 | CLO 2 & 4
Reference: Behrouz Forouzan, Introduction to Data Communication & Networking
"""

import sys
import numpy as np
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QSlider, QTabWidget, QGroupBox, QFormLayout,
    QComboBox, QSpinBox, QCheckBox, QListWidget, QListWidgetItem
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor
import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.patches as mpatches

#Constants (ITU-T standard wavelengths)
CWDM_WL = [1271, 1291, 1311, 1331, 1351, 1371, 1391, 1411]
DWDM_WL = [1530.3, 1531.1, 1531.9, 1532.7, 1533.5, 1534.3,
           1535.0, 1535.8, 1536.6, 1537.4, 1538.2, 1538.9,
           1539.8, 1540.6, 1541.4, 1542.1]
COLORS   = ['#e74c3c','#e67e22','#f1c40f','#2ecc71',
            '#1abc9c','#3498db','#9b59b6','#e91e63',
            '#ff5722','#00bcd4','#8bc34a','#ff9800',
            '#795548','#607d8b','#cddc39','#f06292']
ATTEN    = 0.2   
DISP     = 17.0  




class WDMSystem:
    def __init__(self):
        self.wavelengths   = []
        self.colors        = []
        self.data_rates    = []
        self.fiber_km      = 100.0
        self.noise_on      = True
        self.amp_on        = True
        self.mode          = 'CWDM'

    def setup(self, mode, n):
        self.mode = mode
        wls = CWDM_WL if mode == 'CWDM' else DWDM_WL
        self.wavelengths = wls[:n]
        self.colors      = COLORS[:n]
        self.data_rates  = [2.5 if mode == 'CWDM' else 10.0] * n

    def spectrum(self, at_rx=False):
        if not self.wavelengths:
            return np.array([]), np.array([])
        wl_min = min(self.wavelengths) - 25
        wl_max = max(self.wavelengths) + 25
        wl = np.linspace(wl_min, wl_max, 2000)
        psd = np.zeros_like(wl)
        bw  = 2.0
        for i, lam in enumerate(self.wavelengths):
            peak = 1.0
            if at_rx:
                loss = 10 ** (-ATTEN * self.fiber_km / 10)
                peak = loss * (10.0 if self.amp_on else 1.0)
            psd += peak * np.exp(-0.5 * ((wl - lam) / bw) ** 2)
        if self.noise_on:
            psd += np.abs(np.random.normal(0, 0.003, len(wl)))
        return wl, psd

    def pulse_broadening(self):
        dist = np.linspace(0, self.fiber_km * 1.5, 200)
        T0   = 50.0
        out  = {}
        for i, lam in enumerate(self.wavelengths):
            broad = np.sqrt(T0**2 + (DISP * dist * 0.1)**2)
            out[f'{lam:.0f}nm'] = (dist, broad, self.colors[i])
        return out

    def channel_signal(self, idx):
        t    = np.linspace(0, 8, 1000)
        n    = int(self.data_rates[idx] * 8)
        bits = np.random.randint(0, 2, max(n, 4))
        sps  = int(1000 / max(len(bits), 1))
        sig  = np.repeat(bits, sps)[:1000].astype(float)
        return t, sig

    def total_capacity(self):
        return sum(self.data_rates)




def make_fig(rows=1, cols=1, h=5):
    fig = Figure(figsize=(11, h), tight_layout=True)
    fig.patch.set_facecolor('#f5f5f5')
    axes = [fig.add_subplot(rows, cols, i + 1) for i in range(rows * cols)]
    for ax in axes:
        ax.set_facecolor('white')
        ax.grid(True, color='#dddddd', linewidth=0.8)
        ax.tick_params(labelsize=8)
    return fig, FigureCanvas(fig), axes




class WDMApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.sys   = WDMSystem()
        self.timer = QTimer()
        self.timer.timeout.connect(self._tick)
        self._t    = 0.0
        self.sys.setup('CWDM', 4)
        self._build_ui()
        self._refresh()

    def _build_ui(self):
        self.setWindowTitle('WDM Optical Fiber Simulator — Data Communications')
        self.setGeometry(100, 100, 1400, 800)

        root = QWidget()
        self.setCentralWidget(root)
        main = QHBoxLayout(root)

        
        ctrl = QWidget(); ctrl.setFixedWidth(240)
        cl   = QVBoxLayout(ctrl)

        cl.addWidget(QLabel('<b>WDM Simulator</b>'))
        cl.addWidget(QLabel('Data Communications — Nirma University'))

        mg = QGroupBox('WDM Mode')
        ml = QFormLayout(mg)
        self.mode_cb = QComboBox()
        self.mode_cb.addItems(['CWDM (20 nm spacing)', 'DWDM (<1 nm spacing)'])
        self.n_spin  = QSpinBox(); self.n_spin.setRange(2, 8); self.n_spin.setValue(4)
        ml.addRow('Mode:', self.mode_cb)
        ml.addRow('Channels:', self.n_spin)
        apply = QPushButton('Apply')
        apply.clicked.connect(self._apply)
        ml.addRow(apply)
        cl.addWidget(mg)

        fg = QGroupBox('Fiber')
        fl = QFormLayout(fg)
        self.len_sl  = QSlider(Qt.Orientation.Horizontal)
        self.len_sl.setRange(10, 1000); self.len_sl.setValue(100)
        self.len_lbl = QLabel('100 km')
        self.len_sl.valueChanged.connect(
            lambda v: [setattr(self.sys, 'fiber_km', float(v)),
                       self.len_lbl.setText(f'{v} km'), self._refresh()])
        fl.addRow('Length:', self.len_sl)
        fl.addRow('', self.len_lbl)
        fl.addRow('Attenuation:', QLabel('0.2 dB/km'))
        fl.addRow('Dispersion:', QLabel('17 ps/nm·km'))
        cl.addWidget(fg)

        og = QGroupBox('Options')
        ol = QVBoxLayout(og)
        self.noise_cb = QCheckBox('ASE Noise'); self.noise_cb.setChecked(True)
        self.amp_cb   = QCheckBox('EDFA Amplifier'); self.amp_cb.setChecked(True)
        self.noise_cb.toggled.connect(lambda v: [setattr(self.sys,'noise_on',v), self._refresh()])
        self.amp_cb.toggled.connect(lambda v: [setattr(self.sys,'amp_on',v), self._refresh()])
        ol.addWidget(self.noise_cb); ol.addWidget(self.amp_cb)
        cl.addWidget(og)

        cg = QGroupBox('Channels')
        cv = QVBoxLayout(cg)
        self.ch_list = QListWidget(); self.ch_list.setMaximumHeight(130)
        cv.addWidget(self.ch_list)
        cl.addWidget(cg)

        sg = QGroupBox('System Stats')
        sv = QFormLayout(sg)
        self.st_cap = QLabel('—')
        self.st_ch  = QLabel('—')
        self.st_sp  = QLabel('—')
        sv.addRow('Capacity:', self.st_cap)
        sv.addRow('Channels:', self.st_ch)
        sv.addRow('Spacing:', self.st_sp)
        cl.addWidget(sg)

        self.anim_btn = QPushButton('▶ Animate')
        self.anim_btn.clicked.connect(self._toggle_anim)
        cl.addWidget(self.anim_btn)

        ref_btn = QPushButton('↺ Refresh')
        ref_btn.clicked.connect(self._refresh)
        cl.addWidget(ref_btn)

        cl.addStretch(1)
        main.addWidget(ctrl)

        
        self.tabs = QTabWidget()

        t1 = QWidget(); l1 = QVBoxLayout(t1)
        self.sys_fig, self.sys_cv, _ = make_fig(h=6)
        l1.addWidget(self.sys_cv)
        self.tabs.addTab(t1, 'System Diagram')

        t2 = QWidget(); l2 = QVBoxLayout(t2)
        self.sp_fig, self.sp_cv, self.sp_ax = make_fig(rows=2, cols=1, h=7)
        l2.addWidget(self.sp_cv)
        self.tabs.addTab(t2, 'Optical Spectrum')

        t3 = QWidget(); l3 = QVBoxLayout(t3)
        self.sig_fig, self.sig_cv, self.sig_ax = make_fig(rows=2, cols=4, h=6)
        l3.addWidget(self.sig_cv)
        self.tabs.addTab(t3, 'Channel Signals')

        t4 = QWidget(); l4 = QVBoxLayout(t4)
        self.osnr_fig, self.osnr_cv, self.osnr_ax = make_fig(rows=1, cols=2, h=5)
        l4.addWidget(self.osnr_cv)
        self.tabs.addTab(t4, 'OSNR Analysis')

        t5 = QWidget(); l5 = QVBoxLayout(t5)
        self.dp_fig, self.dp_cv, self.dp_ax = make_fig(rows=1, cols=2, h=5)
        l5.addWidget(self.dp_cv)
        self.tabs.addTab(t5, 'Dispersion')

        main.addWidget(self.tabs)

    def _apply(self):
        mode = 'CWDM' if self.mode_cb.currentIndex() == 0 else 'DWDM'
        self.sys.setup(mode, self.n_spin.value())
        self._refresh()

    def _toggle_anim(self):
        if self.timer.isActive():
            self.timer.stop(); self.anim_btn.setText('▶ Animate')
        else:
            self._t = 0.0; self.timer.start(80); self.anim_btn.setText('⏹ Stop')

    def _tick(self):
        self._t += 0.1
        self._draw_system(self._t)
        self._draw_spectrum()

    def _refresh(self):
        self._update_sidebar()
        self._draw_system()
        self._draw_spectrum()
        self._draw_signals()
        self._draw_osnr()
        self._draw_dispersion()

    def _update_sidebar(self):
        self.ch_list.clear()
        for i, (wl, col) in enumerate(zip(self.sys.wavelengths, self.sys.colors)):
            item = QListWidgetItem(f'λ{i+1}  {wl:.1f} nm  · {self.sys.data_rates[i]}G')
            item.setForeground(QColor(col))
            self.ch_list.addItem(item)
        self.st_cap.setText(f'{self.sys.total_capacity():.0f} Gbps')
        self.st_ch.setText(str(len(self.sys.wavelengths)))
        if len(self.sys.wavelengths) >= 2:
            sp = abs(self.sys.wavelengths[1] - self.sys.wavelengths[0])
            self.st_sp.setText(f'{sp:.2f} nm')

    def _draw_system(self, t=0.0):
        fig = self.sys_fig; fig.clear()
        ax  = fig.add_subplot(111)
        ax.set_facecolor('#fafafa'); fig.patch.set_facecolor('#f5f5f5')
        n = len(self.sys.wavelengths)
        if n == 0: self.sys_cv.draw_idle(); return

        ys  = np.linspace(0.2, 0.8, n)
        mid = (ys[0] + ys[-1]) / 2
        ax.set_xlim(0, 10); ax.set_ylim(0, 1); ax.axis('off')

        ax.text(5, 0.95, f'WDM System — {self.sys.mode}  |  {self.sys.fiber_km:.0f} km fiber  |  {self.sys.total_capacity():.0f} Gbps capacity',
                ha='center', va='top', fontsize=11, fontweight='bold', color='#2c3e50')

        for i, (y, col) in enumerate(zip(ys, self.sys.colors)):
            ax.add_patch(mpatches.FancyBboxPatch((0.1, y-0.04), 1.1, 0.08,
                boxstyle='round,pad=0.01', fc='#ecf0f1', ec=col, lw=2))
            ax.text(0.65, y, f'Src {i+1}  {self.sys.wavelengths[i]:.0f}nm',
                    ha='center', va='center', fontsize=7.5, color=col, fontweight='bold')
            ax.plot([1.2, 2.6], [y, mid], color=col, lw=1.5, alpha=0.7)
            p  = (t * 0.6 + i * 0.25) % 1.0
            ax.plot(1.2 + p*(2.6-1.2), y + p*(mid-y), 'o', color=col, ms=7, zorder=5)

        ax.add_patch(mpatches.FancyBboxPatch((2.6, mid-0.13), 0.7, 0.26,
            boxstyle='round,pad=0.02', fc='#d6eaf8', ec='#2980b9', lw=2))
        ax.text(2.95, mid, 'Optical\nMUX', ha='center', va='center',
                fontsize=9, fontweight='bold', color='#2980b9')

        ax.plot([3.3, 6.7], [mid, mid], color='#f39c12', lw=10, alpha=0.25, solid_capstyle='round')
        ax.plot([3.3, 6.7], [mid, mid], color='#f39c12', lw=3, solid_capstyle='round')
        ax.text(5.0, mid-0.07, f'Single-Mode Optical Fiber  ({self.sys.fiber_km:.0f} km)  |  {ATTEN} dB/km  |  {DISP} ps/nm·km',
                ha='center', fontsize=7.5, color='#7f8c8d', style='italic')

        for i, col in enumerate(self.sys.colors):
            p  = (t * 0.5 + i * 0.18) % 1.0
            oy = (i - n/2) * 0.03
            ax.plot(3.3 + p*(6.7-3.3), mid+oy, 's', color=col, ms=5, alpha=0.85, zorder=6)

        if self.sys.amp_on:
            ax.add_patch(mpatches.FancyBboxPatch((4.65, mid-0.05), 0.7, 0.1,
                boxstyle='round,pad=0.01', fc='#eafaf1', ec='#27ae60', lw=1.8))
            ax.text(5.0, mid, 'EDFA', ha='center', va='center',
                    fontsize=8, fontweight='bold', color='#27ae60')

        ax.add_patch(mpatches.FancyBboxPatch((6.7, mid-0.13), 0.7, 0.26,
            boxstyle='round,pad=0.02', fc='#d6eaf8', ec='#2980b9', lw=2))
        ax.text(7.05, mid, 'Optical\nDEMUX', ha='center', va='center',
                fontsize=9, fontweight='bold', color='#2980b9')

        for i, (y, col) in enumerate(zip(ys, self.sys.colors)):
            ax.plot([7.4, 8.8], [mid, y], color=col, lw=1.5, alpha=0.7)
            p  = (t * 0.6 + i * 0.3 + 0.5) % 1.0
            ax.plot(7.4 + p*(8.8-7.4), mid + p*(y-mid), 'o', color=col, ms=7, zorder=5)
            ax.add_patch(mpatches.FancyBboxPatch((8.8, y-0.04), 1.05, 0.08,
                boxstyle='round,pad=0.01', fc='#ecf0f1', ec=col, lw=2))
            ax.text(9.33, y, f'Rx {i+1}  {self.sys.wavelengths[i]:.0f}nm',
                    ha='center', va='center', fontsize=7.5, color=col, fontweight='bold')

        self.sys_cv.draw_idle()

    def _draw_spectrum(self):
        for ax in self.sp_ax: ax.clear(); ax.grid(True, color='#ddd', lw=0.8)
        wl, tx = self.sys.spectrum(at_rx=False)
        wl, rx = self.sys.spectrum(at_rx=True)
        if not len(wl): self.sp_cv.draw_idle(); return
        for i, (lam, col) in enumerate(zip(self.sys.wavelengths, self.sys.colors)):
            mask = np.abs(wl - lam) < 8
            self.sp_ax[0].fill_between(wl[mask], tx[mask], alpha=0.7, color=col)
            self.sp_ax[0].axvline(lam, color=col, lw=1, ls='--', alpha=0.5)
            self.sp_ax[0].text(lam, max(tx[mask])*1.05 if any(mask) else 0.01,
                               f'{lam:.0f}', ha='center', fontsize=7, color=col)
            self.sp_ax[1].fill_between(wl[mask], rx[mask], alpha=0.7, color=col)
        self.sp_ax[0].plot(wl, tx, 'k-', lw=0.6, alpha=0.4)
        self.sp_ax[1].plot(wl, rx, 'k-', lw=0.6, alpha=0.4)
        self.sp_ax[0].set_title('TX Spectrum — After MUX (Fiber Input)', fontsize=9)
        self.sp_ax[1].set_title(f'RX Spectrum — After {self.sys.fiber_km:.0f} km + DEMUX', fontsize=9)
        for ax in self.sp_ax:
            ax.set_xlabel('Wavelength (nm)', fontsize=8)
            ax.set_ylabel('Power (a.u.)', fontsize=8)
        self.sp_cv.draw_idle()

    def _draw_signals(self):
        for ax in self.sig_ax: ax.clear(); ax.set_facecolor('white')
        for i in range(len(self.sig_ax)):
            if i < len(self.sys.wavelengths):
                t, s = self.sys.channel_signal(i)
                col  = self.sys.colors[i]
                self.sig_ax[i].plot(t, s, color=col, lw=1.5)
                self.sig_ax[i].fill_between(t, 0, s, alpha=0.2, color=col)
                self.sig_ax[i].set_title(f'λ{i+1}  {self.sys.wavelengths[i]:.0f} nm  ·  {self.sys.data_rates[i]}G', fontsize=8, color=col)
                self.sig_ax[i].set_xlabel('Time (ns)', fontsize=7)
                self.sig_ax[i].set_ylabel('Power', fontsize=7)
                self.sig_ax[i].grid(True, color='#ddd', lw=0.6)
            else:
                self.sig_ax[i].axis('off')
                self.sig_ax[i].text(0.5, 0.5, 'No Channel', ha='center', va='center',
                                    fontsize=8, color='#aaa', transform=self.sig_ax[i].transAxes)
        self.sig_cv.draw_idle()

    def _draw_osnr(self):
        for ax in self.osnr_ax: ax.clear(); ax.grid(True, color='#ddd', lw=0.8)
        dist = np.linspace(0, self.sys.fiber_km * 1.5, 200)
        th   = 15.0
        self.osnr_ax[0].axhline(th, color='red', lw=1.5, ls='--', label=f'Min OSNR ({th} dB)')
        self.osnr_ax[0].axhspan(0, th, alpha=0.06, color='red')
        for wl, col in zip(self.sys.wavelengths, self.sys.colors):
            osnrs = [58 - 5 - 10*np.log10(max(1, int(d/80))) for d in dist]
            self.osnr_ax[0].plot(dist, osnrs, color=col, lw=2, label=f'{wl:.0f}nm')
        self.osnr_ax[0].axvline(self.sys.fiber_km, color='black', lw=1.5, ls='-.', label='System length')
        self.osnr_ax[0].set_title('OSNR vs Distance', fontsize=9)
        self.osnr_ax[0].set_xlabel('Distance (km)', fontsize=8)
        self.osnr_ax[0].set_ylabel('OSNR (dB)', fontsize=8)
        self.osnr_ax[0].legend(fontsize=7); self.osnr_ax[0].set_ylim(0, 80)

        labels = [f'{w:.0f}nm' for w in self.sys.wavelengths]
        vals   = [58 - 5 - 10*np.log10(max(1, int(self.sys.fiber_km/80))) for _ in self.sys.wavelengths]
        bars   = self.osnr_ax[1].bar(labels, vals, color=self.sys.colors, edgecolor='white', lw=0.5, width=0.6)
        self.osnr_ax[1].axhline(th, color='red', lw=1.5, ls='--')
        for bar, v in zip(bars, vals):
            self.osnr_ax[1].text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.5, f'{v:.1f}', ha='center', fontsize=7.5)
        self.osnr_ax[1].set_title(f'Channel OSNR at {self.sys.fiber_km:.0f} km', fontsize=9)
        self.osnr_ax[1].set_xlabel('Channel', fontsize=8)
        self.osnr_ax[1].set_ylabel('OSNR (dB)', fontsize=8)
        self.osnr_cv.draw_idle()

    def _draw_dispersion(self):
        for ax in self.dp_ax: ax.clear(); ax.grid(True, color='#ddd', lw=0.8)
        for label, (dist, width, col) in self.sys.pulse_broadening().items():
            self.dp_ax[0].plot(dist, width, color=col, lw=2, label=label)
        self.dp_ax[0].axvline(self.sys.fiber_km, color='black', lw=1.5, ls='-.', label='System length')
        self.dp_ax[0].set_title('Chromatic Dispersion — Pulse Broadening', fontsize=9)
        self.dp_ax[0].set_xlabel('Distance (km)', fontsize=8)
        self.dp_ax[0].set_ylabel('Pulse Width (ps)', fontsize=8)
        self.dp_ax[0].legend(fontsize=7)

        t_ps = np.linspace(-150, 150, 500)
        T0   = 50.0
        T1   = np.sqrt(T0**2 + (DISP * self.sys.fiber_km * 0.1)**2)
        self.dp_ax[1].plot(t_ps, np.exp(-t_ps**2/(2*T0**2)), 'b-', lw=2, label=f'Input  T₀={T0:.0f} ps')
        self.dp_ax[1].fill_between(t_ps, np.exp(-t_ps**2/(2*T0**2)), alpha=0.15, color='blue')
        self.dp_ax[1].plot(t_ps, (T0/T1)*np.exp(-t_ps**2/(2*T1**2)), 'r-', lw=2, label=f'After {self.sys.fiber_km:.0f} km  T₁={T1:.1f} ps')
        self.dp_ax[1].fill_between(t_ps, (T0/T1)*np.exp(-t_ps**2/(2*T1**2)), alpha=0.15, color='red')
        self.dp_ax[1].set_title('Pulse Shape: Input vs Received', fontsize=9)
        self.dp_ax[1].set_xlabel('Time (ps)', fontsize=8)
        self.dp_ax[1].set_ylabel('Normalized Amplitude', fontsize=8)
        self.dp_ax[1].legend(fontsize=8)
        self.dp_cv.draw_idle()


def main():
    app = QApplication(sys.argv)
    win = WDMApp()
    win.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()