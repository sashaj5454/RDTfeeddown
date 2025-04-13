
def load_selected_files(self):
		self.plot_progress.show()
		QtWidgets.QApplication.processEvents()
		# Load selected file paths from the validation files list into the loaded files list
		selected_files = [self.validation_files_list.item(i).text() for i in range(self.validation_files_list.count()) 
						if self.validation_files_list.item(i).isSelected()]
		self.loaded_files_list.clear()
		loaded_output_data = []
		for file in selected_files:
			self.loaded_files_list.addItem(file)
			data = load_RDTdata(file)
			loaded_output_data.append(data)
		results = group_datasets(loaded_output_data, self.log_error)
		if len(results) < 4:
			QMessageBox.critical(self, "Error", "Not enough data from group_datasets.")
			return
		self.b1rdtdata, self.b2rdtdata, self.rdt, self.rdt_plane = results
		if self.b1rdtdata is None and self.b2rdtdata is None:
			self.loaded_files_list.clear()
			return