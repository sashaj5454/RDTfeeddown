from qtpy.QtWidgets import (
    QAbstractItemView,
    QFileDialog,
    QFileSystemModel,
    QListView,
    QListWidgetItem,
    QTreeView,
    QTreeWidgetItem,
    QWidget,
)

from rdtfeeddown.data_handler import load_rdtdata
from rdtfeeddown.validation_utils import validate_file_structure


def select_singleitem(
    parent: type,
    beam: str,
    title_text: str,
    b1entry: QWidget,
    b2entry: QWidget,
    input_path: str = "",
    filter_text: str = "All Files (*)",
    folder: bool = False,
):
    """
    Open a file dialog to select a single item (a file or folder).

    Parameters:
            parent (QWidget): The parent widget.
            default_dir (str): Directory where the dialog should start.
            title_text (str): The window title.
            filter_text (str): The filter string (e.g. "JSON Files (*.json);;All Files (*)").
            folder (bool): If True, dialog is configured to select directories.

    Returns:
            str or None: The selected file/folder path, or None if cancelled.
    """
    dialog = QFileDialog(parent)
    dialog.setWindowTitle(title_text)
    dialog.setDirectory(input_path)
    if folder:
        dialog.setFileMode(QFileDialog.Directory)
        dialog.setOption(QFileDialog.ShowDirsOnly, on=True)
    else:
        dialog.setFileMode(QFileDialog.ExistingFile)
    dialog.setNameFilter(filter_text)
    if dialog.exec_() == QFileDialog.Accepted:
        itempath = dialog.selectedFiles()[0]
    else:
        itempath = ""
    if beam == "LHCB1":
        b1entry.setText(itempath)
    elif beam == "LHCB2":
        b2entry.setText(itempath)
    else:
        return


def select_multiple_files(
    parent: type,
    default_dir: str,
    list_widget: QWidget,
    title: str = "Select Files",
    file_filter: str = "JSON Files (*.json)",
):
    """
    Open a file dialog to select multiple files.

    Parameters:
            parent (QWidget): The parent widget.
            default_dir (str): Directory where the dialog should start.
            title (str): The window title.
            file_filter (str): The filter string.

    Returns:
            list: List of selected file paths.
    """
    dialog = QFileDialog(parent)
    dialog.setWindowTitle(title)
    dialog.setDirectory(default_dir)
    dialog.setFileMode(QFileDialog.ExistingFiles)
    dialog.setNameFilter(file_filter)
    for view in dialog.findChildren((QListView, QTreeView)):
        view.setSelectionMode(QAbstractItemView.ExtendedSelection)
    if dialog.exec_() == QFileDialog.Accepted:
        selected_files = dialog.selectedFiles()
        for file in selected_files:
            if file not in [
                list_widget.item(i).text() for i in range(list_widget.count())
            ]:
                item = QListWidgetItem(file)
                item.setSelected(True)
                list_widget.addItem(item)
        return dialog.selectedFiles()
    return []


def select_folders(
    parent: type, default_dir: str, name_filter: str, list_widget: QWidget
):
    """
    Open a file dialog to select one or more directories.

    Parameters:
            parent (QWidget): The parent widget.
            default_dir (str): Directory where the dialog should start.
            name_filter (str): The filter for folder names.

    Returns:
            list: List of selected directory paths.
    """
    dialog = QFileDialog(parent)
    dialog.setOption(QFileDialog.DontUseNativeDialog, on=True)
    dialog.setFileMode(QFileDialog.Directory)
    dialog.setOption(QFileDialog.ShowDirsOnly, on=True)
    dialog.setDirectory(default_dir)
    dialog.setNameFilter(name_filter)
    for view in dialog.findChildren((QListView, QTreeView)):
        if isinstance(view.model(), QFileSystemModel):
            view.setSelectionMode(QAbstractItemView.ExtendedSelection)
    if dialog.exec_() == QFileDialog.Accepted:
        selected_dirs = dialog.selectedFiles()
        for directory in selected_dirs:
            if directory not in [
                list_widget.item(i).text() for i in range(list_widget.count())
            ]:
                list_widget.addItem(directory)


def select_multiple_treefiles(
    parent: type,
    tree_widget: QWidget,
    title: str = "Select Files",
    file_filter: str = "JSON Files (*.json)",
    saved_data: dict = None,
):
    """
    Allow the user to select multiple files and add them to the file tree widget.
    """
    dialog = QFileDialog(parent)
    dialog.setWindowTitle(title)
    dialog.setDirectory(
        parent.default_output_path
    )  # Use default output path, adjust if needed
    dialog.setFileMode(QFileDialog.ExistingFiles)
    dialog.setNameFilter(file_filter)

    # Enable multiple selection in the dialog
    for view in dialog.findChildren((QListView, QTreeView)):
        if isinstance(view.model(), QFileSystemModel):
            view.setSelectionMode(QAbstractItemView.ExtendedSelection)

    if dialog.exec_() == QFileDialog.Accepted:
        selected_files = dialog.selectedFiles()
        existing_files = [
            tree_widget.topLevelItem(i).text(
                0
            )  # Get the filename from the first column
            for i in range(tree_widget.topLevelItemCount())
        ]
        for file in selected_files:
            if file not in existing_files:
                saved_data[file] = load_rdtdata(file)
                valid = validate_file_structure(
                    saved_data[file],
                    ["beam", "ref", "file", "rdt", "rdt_plane", "knob_name"],
                    parent.log_error,
                )
                if not valid:
                    valid = validate_file_structure(
                        saved_data[file],
                        [
                            "beam",
                            "ref",
                            "rdt",
                            "rdt_plane",
                            "knob_name",
                        ],  # legacy compatibility
                        parent.log_error,
                    )
                    if not valid:
                        del saved_data[file]
                        continue
                parent.rdt = (
                    saved_data[file].get("metadata", {}).get("rdt", "Unknown RDT")
                )
                parent.rdt_plane = (
                    saved_data[file]
                    .get("metadata", {})
                    .get("rdt_plane", "Unknown Plane")
                )
                parent.corrector = (
                    saved_data[file]
                    .get("metadata", {})
                    .get("knob_name", "Unknown Corrector")
                )
                beam = saved_data[file].get("metadata", {}).get("beam", "Unknown Beam")
                item = QTreeWidgetItem(
                    [file, beam, parent.rdt, parent.rdt_plane, parent.corrector]
                )
                tree_widget.addTopLevelItem(item)
    return dialog.selectedFiles()
