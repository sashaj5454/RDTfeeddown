import matplotlib.pyplot as plt
import numpy as np
from .analysis import polyfunction, calculate_avg_rdt_shift, arcBPMcheck, badBPMcheck

IP_POS_DEFAULT = {
	"LHCB1": {
		'IP1': 23.51936962,
		'IP2': 0.192923,
		'IP3': 3.525207216,
		'IP4': 6.857491433,
		'IP5': 10.18977565,
		'IP6': 13.52221223,
		'IP7': 16.85464882,
		'IP8': 20.1758654,
	},
	"LHCB2": {
		'IP1': 3.195252584,
		'IP2': 6.5275368,
		'IP3': 9.859973384,
		'IP4': 13.19240997,
		'IP5': 16.52484655,
		'IP6': 19.85713077,
		'IP7': 23.18941498,
		'IP8': 26.5104792,
	}
}

def plot_BPM(BPM, fulldata, rdt, rdt_plane, ax1=None, ax2=None, log_func=None):
	try:
		data = fulldata["data"]
		diffdata = data[BPM]['diffdata']
		fitdata = data[BPM]['fitdata']
		xing, re, im = [], [], []
		# print(diffdata)
		for x in range(len(diffdata)):
			xing.append(diffdata[x][0])
			re.append(diffdata[x][1])
			im.append(diffdata[x][2])

		xing = np.array(xing)
		re = np.array(re)
		im = np.array(im)

		if ax1 is None or ax2 is None:
			fig, (ax1, ax2) = plt.subplots(2, 1, sharey=False)
		else:
			fig = ax1.figure

		xing_min = np.min(xing)
		xing_max = np.max(xing)
		xing_ran = xing_max - xing_min
		xfit = np.arange(xing_min, xing_max, xing_ran / 100.0)
		refit = polyfunction(xfit, fitdata[0][0], fitdata[0][1], fitdata[0][2])
		imfit = polyfunction(xfit, fitdata[3][0], fitdata[3][1], fitdata[3][2])

		ax1.set_ylabel(f"{BPM} Re($f_{{{rdt_plane},{rdt}}}$)")
		ax1.set_xlabel("Knob trim")
		ax1.plot(xfit, refit)
		ax1.plot(xing, re, 'ro')

		ax2.set_ylabel(f"{BPM} Im($f_{{{rdt_plane},{rdt}}}$)")
		ax2.set_xlabel("Knob trim")
		ax2.plot(xfit, imfit)
		ax2.plot(xing, im, 'ro')

		plt.tight_layout(pad=2.0, h_pad=5.0)
	except Exception as e:
		if log_func:
			log_func(f"Error plotting BPM {BPM}: {e}")
		else:
			print(f"Error plotting BPM {BPM}: {e}")
		return None

	return fig

def plot_avg_rdt_shift(ax, data, rdt, rdt_plane):
	"""
	Plot the average RDT shift and standard deviation for given data on the provided axis.
	"""
	xing, ampdat, stddat = calculate_avg_rdt_shift(data)
	ax.set_ylabel(f"sqrt($\\Delta$Re$f_{{{rdt_plane},{rdt}}}^2$+$\\Delta$Im$f_{{{rdt_plane},{rdt}}}^2$)")
	ax.set_xlabel(f"Knob trim")
	ax.plot(xing, ampdat)
	plt.tight_layout(pad=2.0, h_pad=5.0)
	ax.errorbar(xing, ampdat, yerr=stddat, fmt='ro')

def plot_RDTshifts(b1data, b2data, rdt, rdt_plane, axes, log_func=None):
	"""
	Plots RDT shifts. Handles three layouts:
	1) Only b1data provided: 3x1 figure (Beam 1 only).
	2) Only b2data provided: 3x1 figure (Beam 2 only).
	3) Both b1data and b2data: 3x2 figure (b1 on left, b2 on right).
	"""
	try:
		if b1data and b2data:
			ax1, ax2, ax3, ax4, ax5, ax6 = axes
		else:
			ax1, ax2, ax3 = axes

		def plot_beam_data(axs, data, label):
			"""
			Plots the RDT shift data for a single beam into the three provided axes:
			axs[0] => Average re^2 + im^2
			axs[1] => dRe
			axs[2] => dIm
			"""
			# Unpack the axes
			ax_avg, ax_re, ax_im = axs

			 # Set title for the beam column
			ax_avg.set_title(label, pad=20)

			# Collect data for dRe/dknob and dIm/dknob
			sdat, dredkdat, dimdkdat = [], [], []
			dredkerr, dimdkerr = [], []
			for bpm in data.keys():
				if not arcBPMcheck(bpm) or badBPMcheck(bpm):
					continue
				s = data[bpm]['s']/1000
				# [re_opt, re_cov, re_err, im_opt, im_cov, im_err]
				re_opt, _, re_err, im_opt, _, im_err = data[bpm]['fitdata']
				# re_opt[1] => slope in re polynomial fit, re_err[1] => error in that slope
				sdat.append(s)
				dredkdat.append(re_opt[1])
				dredkerr.append(re_err[1])
				dimdkdat.append(im_opt[1])
				dimdkerr.append(im_err[1])

			sdat     = np.array(sdat)
			dredkdat = np.array(dredkdat)
			dimdkdat = np.array(dimdkdat)
			dredkerr = np.array(dredkerr)
			dimdkerr = np.array(dimdkerr)

			# Plot average re^2 + im^2
			plot_avg_rdt_shift(ax_avg, data, rdt, rdt_plane)

			# Plot dRe
			ax_re.set_ylabel(f'$\partial$Re$f_{{{rdt_plane},{rdt}}}$/$\partial$knob')
			ax_re.set_xlabel(f'S [km]')
			ax_re.plot(sdat, dredkdat)
			ax_re.errorbar(sdat, dredkdat, yerr=dredkerr, fmt='ro')

			# Plot dIm
			ax_im.set_ylabel(f'$\partial$Im$f_{{{rdt_plane},{rdt}}}$/$\partial$knob')
			ax_im.set_xlabel(f'S [km]')
			ax_im.plot(sdat, dimdkdat)
			ax_im.errorbar(sdat, dimdkdat, yerr=dimdkerr, fmt='ro')

			for ax_ in (ax_re, ax_im):
				# Retrieve the current y-limits from the Axes object
				y_min, y_max = ax_.get_ylim()
				for ip in range(1, 9):
					ip_x = IP_POS_DEFAULT[label][f"IP{ip}"]
					ax_.axvline(x=ip_x, color="black", linestyle="--")
					ax_.text(ip_x, y_max * 1.05, f"IP{ip}", rotation=0, va="bottom", ha="center")
				plt.tight_layout(pad=2.0, h_pad=5.0)

		# Case 1: Both Beam 1 and Beam 2 data
		if b1data is not None and b2data is not None:
			# LHCB1 on the left: (ax1, ax3, ax5)
			plot_beam_data((ax1, ax3, ax5), b1data, "LHCB1")
			# LHCB2 on the right: (ax2, ax4, ax6)
			plot_beam_data((ax2, ax4, ax6), b2data, "LHCB2")

		# Case 2: Only Beam 1 data given (b2data is None)
		if b1data is not None:
			plot_beam_data((ax1, ax2, ax3), b1data, "LHCB1")

		# Case 3: Only Beam 2 data given (b1data is None)
		if b2data is not None:
			plot_beam_data((ax1, ax2, ax3), b2data, "LHCB2")

	except Exception as e:
		if log_func:
			log_func(f"Error plotting f<sub>{rdt_plane},{rdt}</sub> RDT shift: {e}")
		else:
			print(f"Error plotting f$_{{{rdt_plane},{rdt}}}$ RDT shift: {e}")
		return None

	return

def plot_RDT(b1data, b2data, rdt, rdt_plane, axes, log_func=None):
	"""
	Plots RDT data for LHCB1, LHCB2, or both. 
	- If both are provided, uses a 3x2 layout (B1 on the left, B2 on the right).
	- If only one is provided, uses a 3x1 layout.
	"""
	try:
		# Decide figure layout
		if b1data and b2data:
			ax1, ax2, ax3, ax4, ax5, ax6 = axes
		else:
			ax1, ax2, ax3 = axes

		def plot_single_beam(ax_amp, ax_re, ax_im, data, beam_label):
			"""
			Plots |f|, Re(f), and Im(f) vs. knob trim in three provided axes.
			"""
			# Get the crossing angles
			if not data:
				return
			xing = []
			first_bpm = next(iter(data.keys()), None)
			if first_bpm is not None:
				for entry in data[first_bpm]['diffdata']:
					xing.append(entry[0])

			 # Set title for the beam column
			ax_amp.set_title(beam_label, pad=20)

			# For each crossing angle, gather BPM data
			for angle in xing:
				sdat, ampdat, redat, imdat = [], [], [], []
				for bpm in data.keys():
					if not arcBPMcheck(bpm) or badBPMcheck(bpm):
						continue
					s = data[bpm]['s']/1000
					diffdata = data[bpm]['diffdata']
					for row in diffdata:
						if row[0] == angle:
							re_val = row[1]
							im_val = row[2]
							amp_val = np.sqrt(re_val**2 + im_val**2)
							sdat.append(s)
							ampdat.append(amp_val)
							redat.append(re_val)
							imdat.append(im_val)

				sdat = np.array(sdat)
				ampdat = np.array(ampdat)
				redat = np.array(redat)
				imdat = np.array(imdat)

				# Plot amplitude
				ax_amp.set_ylabel(f'$|f_{{{rdt_plane},{rdt}}}|$')
				ax_amp.set_xlabel(f'S [km]')
				ax_amp.plot(sdat, ampdat, marker='o')

				# Plot Delta Re
				ax_re.set_ylabel(f'ΔRe($f_{{{rdt_plane},{rdt}}}$)')
				ax_re.set_xlabel(f'S [km]')
				ax_re.plot(sdat, redat, marker='o')

				# Plot Delta Im
				ax_im.set_ylabel(f'ΔIm($f_{{{rdt_plane},{rdt}}}$)')
				ax_im.set_xlabel(f'S [km]')
				ax_im.plot(sdat, imdat, marker='o')

			for ax_ in (ax_amp, ax_re, ax_im):
				# Retrieve the current y-limits from the Axes object
				y_min, y_max = ax_.get_ylim()
				for ip in range(1, 9):
					ip_x = IP_POS_DEFAULT[beam_label][f"IP{ip}"]
					ax_.axvline(x=ip_x, color="black", linestyle="--")
					ax_.text(ip_x, y_max * 1.05, f"IP{ip}", rotation=0, va="bottom", ha="center")
				plt.tight_layout(pad=2.0, h_pad=5.0)

		if b1data and b2data:
			# Plot B1 (left column)
			plot_single_beam(ax1, ax3, ax5, b1data, "LHCB1")
			# Plot B2 (right column)
			plot_single_beam(ax2, ax4, ax6, b2data, "LHCB2")
		elif b1data:
			# Only B1
			plot_single_beam(ax1, ax2, ax3, b1data, "LHCB1")
		elif b2data:
			# Only B2
			plot_single_beam(ax1, ax2, ax3, b2data, "LHCB2")

	except Exception as e:
		if log_func:
			log_func(f"Error plotting f<sub>{rdt_plane},{rdt}</sub> RDT shift: {e}")
		else:
			print(f"Error plotting f$_{{{rdt_plane},{rdt}}}$ RDT shift: {e}")
		return None

	return