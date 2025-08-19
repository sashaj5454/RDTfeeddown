Validation
==========

.. image:: figures/ValidationScreenshot.png
   :width: 500

The :tab:`Validation` tab of the GUI provides a way to load data in the format created by the :tab:`Input <input.html>` tab, and display it to validate it.

Input Fields Explained
----------------------

- :guilabel:`Add Files`:
  Add the generated files from the :tab:`Input <input.html>` tab of the GUI containing the RDT data you want to plot (this simply adds the filenames to a list).

- :guilabel:`Load Selected Files for Plotting`:
  Load the selected files to display their data in the plotting tabs (this then checks that the files are compatible to be plotted together). The loaded files will be displayed in the box below the button.
  
Plotting Tabs Explained
-----------------------

- :tab:`BPM`:
  This tab displays the RDT as a function of crossing angle for a BPM of your choice.

.. note::
  You can search for a BPM by typing its name in the search box and pressing the :guilabel:`Search BPM` - this just checks if the BPM exists in the list of BPMs. Either pressing :kbd:`Enter` or :guilabel:`Plot BPM` will plot the RDT at that BPM as a function of crossing angle.

- :tab:`RDT`:
  This tab displays the RDT as a function of position *s* for all crossing angles.

- :tab:`RDT shift`:
  This tab displays the average RDT shift as a function of crossing angle.

.. warning::

   Ignore the error message below for both the :tab:`RDT` and :tab:`RDT shift` tab, if you only have RDT data from one beam loaded (in this example it would only be LHCB1 data) - this should not affect the plotting.

   .. code-block:: text

      Error accessing LHCB2 RDT data: 'NoneType' object is not subscriptable
