import numpy as np
from .analysis import polyfunction, calculate_avg_rdt_shift, arcBPMcheck, badBPMcheck
from pyqtgraph import ErrorBarItem, TextItem, PlotDataItem, mkBrush, mkPen
from qtpy.QtGui import QPainterPathStroker, QCursor, QPen
from qtpy.QtWidgets import QToolTip, QApplication
from .style import DARK_BACKGROUND_COLOR
from qtpy.QtCore import Qt

COLOR_LIST = ['#FFA500', '#87CEFA', '#00FA9A', '#FFFF00', '#00BFFF', '#FF4500', '#FF66CC']
b1_line_color = "#00ccff"
b2_line_color = 'r'

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

def find_min_max_y(axes):
	overall_y_min = float('inf')
	overall_y_max = float('-inf')

	for ax in axes:
		y_range = ax.getViewBox().viewRange()[1]
		y_min, y_max = y_range[0], y_range[1]
		overall_y_min = min(overall_y_min, y_min)
		overall_y_max = max(overall_y_max, y_max)
		print(overall_y_min, overall_y_max)

	# Now set each axis to use these common limits:
	for ax in axes:
		ax.getViewBox().setYRange(overall_y_min, overall_y_max)

def set_axis_label(axis, position, text, color="white"):
    """
    Set the axis label with consistent color for math text.
    """
    axis.setLabel(position, f"<span style='color:{color};'>{text}</span>")

def plot_ips(axes, label):
	for ax in axes:
		# Track which IP lines have been drawn on this axis
		if not hasattr(ax, '_ips_drawn'):
			ax._ips_drawn = set()

		x_min, x_max = ax.viewRange()[0]
		_, y_max = ax.viewRange()[1]

		for ip in range(1, 9):
			ip_str = f"IP{ip}"
			ip_x = IP_POS_DEFAULT[label][ip_str]
			# Only add a line if in current plot range and not already drawn
			if x_min <= ip_x <= x_max and ip_str not in ax._ips_drawn:
				ax.addLine(x=ip_x, pen=mkPen('w', style=Qt.DashLine))
				# draw the IP label with its own background
				text = TextItem(
					text=ip_str,
					color='w',
					anchor=(0.5, 0),
					fill=mkBrush(50, 50, 50, 200),   # semi‑transp. dark grey
					border=None                      # no border
				)
				text.setPos(ip_x, y_max * 1.25)
				ax.addItem(text)
				ax._ips_drawn.add(ip_str)

def plot_BPM(BPM, fulldata, rdt, rdt_plane, ax1=None, ax2=None, log_func=None):
	try:
		data = fulldata["data"]
		diffdata = data[BPM]['diffdata']
		fitdata = data[BPM]['fitdata']
		knob = fulldata["metadata"]["knob"]
		xing, re, im = [], [], []
		for x in range(len(diffdata)):
			xing.append(diffdata[x][0])
			re.append(diffdata[x][1])
			im.append(diffdata[x][2])

		xing = np.array(xing)
		re = np.array(re)
		im = np.array(im)

		xing_min = np.min(xing)
		xing_max = np.max(xing)
		xing_ran = xing_max - xing_min
		xfit = np.arange(xing_min, xing_max, xing_ran / 100.0)
		refit = polyfunction(xfit, fitdata[0][0], fitdata[0][1], fitdata[0][2])
		imfit = polyfunction(xfit, fitdata[3][0], fitdata[3][1], fitdata[3][2])

		if fulldata["metadata"]["beam"][-1] == "1":
			line_color = b1_line_color
		else:
			line_color = b2_line_color

		set_axis_label(ax1,'left', f"{BPM} ΔRe(f<sub>{rdt_plane},{rdt}</sub>)")
		ax1.setLabel('bottom', f"{knob} trim")
		ax1.plot(xfit, refit, pen=line_color)
		ax1.plot(xing, re, pen=None, symbol='x', symbolPen=line_color)

		set_axis_label(ax2, 'left', f"{BPM} ΔIm(f<sub>{rdt_plane},{rdt}</sub>)")
		ax2.setLabel('bottom', f"{knob} trim")
		ax2.plot(xfit, imfit, pen=line_color)
		ax2.plot(xing, im, pen=None, symbol='x', symbolPen=line_color)

		combined_min = min(np.min(re), np.min(im))
		combined_max = max(np.max(re), np.max(im))

		# Set both axes to use the same y-range
		ax1.setYRange(combined_min, combined_max)
		ax2.setYRange(combined_min, combined_max)
		
	except Exception as e:
		if log_func:
			log_func(f"Error plotting BPM {BPM}: {e}")
		else:
			print(f"Error plotting BPM {BPM}: {e}")
		return None

def plot_avg_rdt_shift(ax, data, line_color, rdt, rdt_plane, knob):
	"""
	Plot the average RDT shift and standard deviation for given data on the provided axis.
	"""
	xing, ampdat, stddat = calculate_avg_rdt_shift(data)
	set_axis_label(ax, 'left', f"√(ΔRe(f<sub>{rdt_plane},{rdt}</sub>)<sup>2</sup> + ΔIm(f<sub>{rdt_plane},{rdt}</sub>)<sup>2</sup>)")
	set_axis_label(ax, 'bottom', f"{knob} trim")
	ax.plot(xing, ampdat, pen=line_color, symbol='x', symbolPen=line_color)  # Plot the data points.
	error_item = ErrorBarItem(x=xing, y=ampdat, top=stddat, bottom=stddat, beam=0.1, pen=line_color)
	ax.addItem(error_item)

def plot_RDTshifts(b1data, b2data, rdt, rdt_plane, axes, knob, log_func=None):
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

		def plot_beam_data(axs, data, label, knob=knob):
			"""
			Plots the RDT shift data for a single beam into the three provided axes:
			axs[0] => Average re^2 + im^2
			axs[1] => dRe
			axs[2] => dIm
			"""
			# Unpack the axes
			ax_avg, ax_re, ax_im = axs
			 # Set title for the beam column
			ax_avg.setTitle(label)
			# Set labels for the real part plot
			if not ax_re.getAxis('left').labelText:  # Check if the Y-axis label is already set
				set_axis_label(ax_re, 'left', f'∂Re(f<sub>{rdt_plane},{rdt}</sub>)/∂knob')
			if not ax_re.getAxis('bottom').labelText:  # Check if the X-axis label is already set
				ax_re.setLabel('bottom', 'S', units='km')
			# Set labels for the imaginary part plot
			if not ax_im.getAxis('left').labelText:  # Check if the Y-axis label is already set
				set_axis_label(ax_im,'left', f'∂Im(f<sub>{rdt_plane},{rdt}</sub>)/∂knob')
			if not ax_im.getAxis('bottom').labelText:  # Check if the X-axis label is already set
				ax_im.setLabel('bottom', 'S', units='km')
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
			if label == "LHCB1":
				line_color = b1_line_color
			else:
				line_color = b2_line_color

			# Plot average re^2 + im^2
			plot_avg_rdt_shift(ax_avg, data, line_color, rdt, rdt_plane, knob)
			# Plot dRe with error bars
			error_re = ErrorBarItem(x=sdat, y=dredkdat, height=2*dredkerr, beam=0.1, pen=line_color)
			ax_re.addItem(error_re)
			ax_re.plot(sdat, dredkdat, pen=line_color, symbol='x', symbolPen=line_color)

			# Plot dIm with error bars
			error_im = ErrorBarItem(x=sdat, y=dimdkdat, height=2*dimdkerr, beam=0.1, pen=line_color)
			ax_im.addItem(error_im)
			ax_im.plot(sdat, dimdkdat, pen=line_color, symbol='x', symbolPen=line_color)

			plot_ips((ax_re, ax_im), label)



		# Case 1: Both Beam 1 and Beam 2 data
		if b1data and b2data:
			# LHCB1 on the left: (ax1, ax3, ax5)
			plot_beam_data((ax1, ax3, ax5), b1data, "LHCB1")
				
			# LHCB2 on the right: (ax2, ax4, ax6)
			plot_beam_data((ax2, ax4, ax6), b2data, "LHCB2")
			print("RE and IM")
			find_min_max_y((ax3, ax4, ax5, ax6))
			print("AVG")
			find_min_max_y((ax1, ax2))

		# Case 2: Only Beam 1 data given (b2data is None)
		elif b1data:
			plot_beam_data((ax1, ax2, ax3), b1data, "LHCB1")
			find_min_max_y((ax2, ax3))

		# Case 3: Only Beam 2 data given (b1data is None)
		elif b2data is not None:
			plot_beam_data((ax1, ax2, ax3), b2data, "LHCB2")
			find_min_max_y((ax2, ax3))

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
			ax_amp.setTitle(beam_label, pad=20)
			set_axis_label(ax_amp,'left', f'Δ|f<sub>{rdt_plane},{rdt}</sub>|')
			ax_amp.setLabel('bottom', 'S', units='km')
			set_axis_label(ax_re, 'left', f'ΔRe(f<sub>{rdt_plane},{rdt}</sub>)')
			ax_re.setLabel('bottom', 'S', units='km')
			set_axis_label(ax_im, 'left', f'ΔIm(f<sub>{rdt_plane},{rdt}</sub>)')
			ax_im.setLabel('bottom', 'S', units='km')
			# Get the crossing angles
			if not data:
				return
			xing = []
			first_bpm = next(iter(data.keys()), None)
			if first_bpm is not None:
				for entry in data[first_bpm]['diffdata']:
					xing.append(entry[0])
			hover_lines_amp = []
			hover_lines_re = []
			hover_lines_im = []
			# For each crossing angle, gather BPM data
			for i, angle in enumerate(xing):
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

				colour = COLOR_LIST[i % len(COLOR_LIST)]

				hover_scatter_amp = HoverLine(x=sdat, y=ampdat, label=f"XING angle = {angle}", pen=colour, symbol='x', symbolPen=colour)
				ax_amp.addItem(hover_scatter_amp)
				hover_lines_amp.append(hover_scatter_amp)
				hover_scatter_re = HoverLine(x=sdat, y=redat, label=f"XING angle = {angle}", pen=colour, symbol='x', symbolPen=colour)
				ax_re.addItem(hover_scatter_re)
				hover_lines_re.append(hover_scatter_re)
				hover_scatter_im = HoverLine(x=sdat, y=imdat, label=f"XING angle = {angle}", pen=colour, symbol='x', symbolPen=colour)
				ax_im.addItem(hover_scatter_im)
				hover_lines_im.append(hover_scatter_im)
		
			plot_ips((ax_amp, ax_re, ax_im), beam_label)
			return hover_lines_amp, hover_lines_re, hover_lines_im

		if b1data and b2data:
			# Plot B1 (left column)
			hover_lines_amp_b1, hover_lines_re_b1, hover_lines_im_b1=plot_single_beam(ax1, ax3, ax5, b1data, "LHCB1")
			install_closest_y_hover(ax1, hover_lines_amp_b1)
			install_closest_y_hover(ax3, hover_lines_re_b1)
			install_closest_y_hover(ax5, hover_lines_im_b1)
			# Plot B2 (right column)
			hover_lines_amp_b2, hover_lines_re_b2, hover_lines_im_b2=plot_single_beam(ax2, ax4, ax6, b2data, "LHCB2")
			install_closest_y_hover(ax2, hover_lines_amp_b2)
			install_closest_y_hover(ax4, hover_lines_re_b2)
			install_closest_y_hover(ax6, hover_lines_im_b2)
			find_min_max_y((ax3, ax4, ax5, ax6))
			find_min_max_y((ax1, ax2))
		elif b1data:
			# Only B1
			hover_lines_amp_b1, hover_lines_re_b1, hover_lines_im_b1 = plot_single_beam(ax1, ax2, ax3, b1data, "LHCB1")
			install_closest_y_hover(ax1, hover_lines_amp_b1)
			install_closest_y_hover(ax2, hover_lines_re_b1)
			install_closest_y_hover(ax3, hover_lines_im_b1)
			find_min_max_y((ax2, ax3))
		elif b2data:
			# Only B2
			hover_lines_amp_b2, hover_lines_re_b2, hover_lines_im_b2=plot_single_beam(ax1, ax2, ax3, b2data, "LHCB2")
			install_closest_y_hover(ax1, hover_lines_amp_b2)
			install_closest_y_hover(ax2, hover_lines_re_b2)
			install_closest_y_hover(ax3, hover_lines_im_b2)
			find_min_max_y((ax2, ax3))


	except Exception as e:
		if log_func:
			log_func(f"Error plotting f<sub>{rdt_plane},{rdt}</sub> RDT shift: {e}")
		else:
			print(f"Error plotting f$_{{{rdt_plane},{rdt}}}$ RDT shift: {e}")
		return None

	return

def plot_dRDTdknob(b1data, b2data, rdt, rdt_plane, axes, knoblist=None, log_func=None):
	"""
	Updated: Plots RDT shifts on provided axes.
	Handles data with or without a "file" key structure.
	"""
	try:
		# When both beams are given, expecting 2x? layout.
		if b1data and b2data:
			ax1, ax2, ax3, ax4 = axes
		else:
			ax1, ax2 = axes

		def plot_beam_data(axs, data, label):
			ax_re, ax_im = axs

			ax_re.setTitle(label)
			hover_line_scatter_re = []
			hover_line_scatter_im = []

			# Set labels for the real part plot
			if not ax_re.getAxis('left').labelText:  # Check if the Y-axis label is already set
				set_axis_label(ax_re,'left', f'∂Re(f<sub>{rdt_plane},{rdt}</sub>)/∂knob')
			if not ax_re.getAxis('bottom').labelText:  # Check if the X-axis label is already set
				ax_re.setLabel('bottom', 'S', units='km')

			# Set labels for the imaginary part plot
			if not ax_im.getAxis('left').labelText:  # Check if the Y-axis label is already set
				set_axis_label(ax_im, 'left', f'∂Im(f<sub>{rdt_plane},{rdt}</sub>)/∂knob')
			if not ax_im.getAxis('bottom').labelText:  # Check if the X-axis label is already set
				ax_im.setLabel('bottom', 'S', units='km')


			# Determine data structure
			is_file_key_structure = isinstance(next(iter(data.values())), dict) and "data" in next(iter(data.values()))
			sdat, dredkdat, dimdkdat = [], [], []
			dredkerr, dimdkerr = [], []

			if is_file_key_structure:
				line_label = "Simulation"
				# Data has a "file" key structure
				for bpm in data[next(iter(data.keys()))]['data'].keys():
					if not arcBPMcheck(bpm) or badBPMcheck(bpm):
						continue
					re_opts, re_errs, im_opts, im_errs = 0, 0, 0, 0
					s = float(data[next(iter(data.keys()))]['data'][bpm]['s']) / 1000
					for file in data.keys():
						re_opt, im_opt = data[file]['data'][bpm]['diffdata']
						knob_name = data[file]['metadata']['knob_name']
						# Do a case-insensitive lookup for the knob widget.
						knob_value=0
						if knoblist is not None:
							knob_value = float(knoblist.get(knob_name, None))
							if knob_value is None:
								continue  # or handle the missing knob case
						re_opts += float(re_opt) * knob_value
						im_opts += float(im_opt) * knob_value
					sdat.append(s)
					dredkdat.append(re_opts)
					dredkerr.append(re_errs)
					dimdkdat.append(im_opts)
					dimdkerr.append(im_errs)


			else:
				line_label = "Measurement"
				# Data is directly a BPM dictionary
				for bpm in data['data'].keys():
					if not arcBPMcheck(bpm) or badBPMcheck(bpm):
						continue
					s = float(data['data'][bpm]['s']) / 1000
					re_opt, _, re_err, im_opt, _, im_err = data['data'][bpm]['fitdata']
					sdat.append(s)
					dredkdat.append(float(re_opt[1]))
					dredkerr.append(float(re_err[1]))
					dimdkdat.append(float(im_opt[1]))
					dimdkerr.append(float(im_err[1]))
			
			# Convert lists to numpy arrays
			sdat     = np.array(sdat)
			dredkdat = np.array(dredkdat)
			dimdkdat = np.array(dimdkdat)
			dredkerr = np.array(dredkerr)
			dimdkerr = np.array(dimdkerr)
			# Plot new data lines
			if line_label == "Simulation":
				hover_scattera = HoverLine(x=sdat, y=dredkdat, label=line_label, pen='g')
				ax_re.addItem(hover_scattera)
				hover_line_scatter_re.append(hover_scattera)
				hover_scatterb = HoverLine(x=sdat, y=dimdkdat, label=line_label, pen='g')
				ax_im.addItem(hover_scatterb)
				hover_line_scatter_im.append(hover_scatterb)
			else:
				if label == "LHCB1":
					line_color = b1_line_color
				else:
					line_color = b2_line_color
				# Plot dRe with error bars
				error_re = ErrorBarItem(x=sdat, y=dredkdat, height=2*dredkerr, beam=0.1, pen=line_color)
				ax_re.addItem(error_re)
				hover_scatter1 = HoverLine(x=sdat, y=dredkdat, label=line_label, pen=line_color, symbol='x', symbolPen=line_color)
				ax_re.addItem(hover_scatter1)
				hover_line_scatter_re.append(hover_scatter1)

				# Plot dIm with error bars
				error_im = ErrorBarItem(x=sdat, y=dimdkdat, height=2*dimdkerr, beam=0.1, pen=line_color)
				ax_im.addItem(error_im)
				hover_scatter2 = HoverLine(x=sdat, y=dimdkdat, label=line_label, pen=line_color, symbol='x', symbolPen=line_color)
				ax_im.addItem(hover_scatter2)
				hover_line_scatter_im.append(hover_scatter2)
			plot_ips((ax_re, ax_im), label)
			return hover_line_scatter_re, hover_line_scatter_im


		# Plot for both beams
		if b1data and b2data:
			hover_line_scatter_re_b1, hover_line_scatter_im_b1 = plot_beam_data((ax1, ax3), b1data, "LHCB1")
			install_closest_y_hover(ax1, hover_line_scatter_re_b1)
			install_closest_y_hover(ax3, hover_line_scatter_im_b1)

			hover_line_scatter_re_b2, hover_line_scatter_im_b2 =plot_beam_data((ax2, ax4), b2data, "LHCB2")
			install_closest_y_hover(ax2, hover_line_scatter_re_b2)
			install_closest_y_hover(ax4, hover_line_scatter_im_b2)
			find_min_max_y((ax1, ax2, ax3, ax4))
		elif b1data:
			hover_line_scatter_re_b1, hover_line_scatter_im_b1 = plot_beam_data((ax1, ax2), b1data, "LHCB1")
			install_closest_y_hover(ax1, hover_line_scatter_re_b1)
			install_closest_y_hover(ax2, hover_line_scatter_im_b1)
			find_min_max_y((ax1, ax2))
		elif b2data:
			hover_line_scatter_re_b2, hover_line_scatter_im_b2 =plot_beam_data((ax1, ax2), b2data, "LHCB2")
			install_closest_y_hover(ax1, hover_line_scatter_re_b2)
			install_closest_y_hover(ax2, hover_line_scatter_im_b2)
			find_min_max_y((ax1, ax2))
				

	except Exception as e:
		if log_func:
			log_func(f"Error plotting dRDTdknob for f<sub>{rdt_plane},{rdt}</sub>: {e}")
		else:
			print(f"Error plotting dRDTdknob for f$_{{{rdt_plane},{rdt}}}$: {e}")
		return None


def setup_blankcanvas(plot_widget):
	# default_bg = QApplication.palette().color(QPalette.Window)

	plot_widget.setBackground(DARK_BACKGROUND_COLOR)  # Set the background to a dark color
	# plot_widget.setBackground('w')  # Set the background to white
	# Optional: hide the axes for a completely blank white canvas
	plot_item = plot_widget.getPlotItem()
	plot_item.hideAxis('left')
	plot_item.hideAxis('bottom')

class HoverLine(PlotDataItem):
	def __init__(self, x, y, label, pen='w', **kwargs):
		self._plainLabel = label
		self._x = np.array(x)
		self._y = np.array(y)
		qp = mkPen(pen) if not isinstance(pen, QPen) else pen
		self._htmlColor = qp.color().name()
		super().__init__(x=x, y=y, pen=qp, **kwargs)
		for item in (self.curve, self.scatter):
			if item is None:
				continue
			item.setAcceptHoverEvents(True)
			item.setAcceptedMouseButtons(Qt.LeftButton | Qt.RightButton)
		self._hoverWidth = 0.01
		
	def shape(self):
		p = super().shape()
		s = QPainterPathStroker()
		s.setWidth(self._hoverWidth)
		return s.createStroke(p)

def install_closest_y_hover(ax, hover_lines):
    vb = ax.getViewBox()

    def mouseMoved(evt):
        if hasattr(evt, 'scenePos'):
            scene_pos = evt.scenePos()
        else:
            scene_pos = evt
        mousePoint = vb.mapSceneToView(scene_pos)
        mouse_x = mousePoint.x()
        mouse_y = mousePoint.y()
        best_label = None
        best_x = None
        best_y = None
        best_color = "white"
        min_dist = float('inf')
        for line in hover_lines:
            xdata, ydata = line.getData()
            if xdata is not None and len(xdata) > 0:
                if np.min(xdata) <= mouse_x <= np.max(xdata):
                    # Interpolate y for the exact mouse x
                    y_val = np.interp(mouse_x, xdata, ydata)
                    x_val = mouse_x
                    dist = abs(y_val - mouse_y)
                else:
                    # Mouse is outside data range, use closest point
                    idx = np.argmin(np.abs(xdata - mouse_x))
                    x_val = xdata[idx]
                    y_val = ydata[idx]
                    dist = abs(y_val - mouse_y)
                if dist < min_dist:
                    min_dist = dist
                    best_label = line._plainLabel
                    best_x = x_val
                    best_y = y_val
                    best_color = getattr(line, "_htmlColor", "white")
        if best_label is not None:
            html = (
                f"<span style='color:{best_color};white-space:nowrap;'>"
                f"{best_label}<br>x={best_x:.3f}, y={best_y:.3f}"
                "</span>"
            )
            QToolTip.showText(QCursor.pos(), html)
        else:
            QToolTip.hideText()

    vb.scene().sigMouseMoved.connect(mouseMoved)