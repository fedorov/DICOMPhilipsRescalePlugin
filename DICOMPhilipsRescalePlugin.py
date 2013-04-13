import os
import string
from __main__ import vtk, qt, ctk, slicer
from DICOMLib import DICOMPlugin
from DICOMLib import DICOMLoadable

#
# This is the plugin to handle translation of DICOM objects
# that can be represented as multivolume objects
# from DICOM files into MRML nodes.  It follows the DICOM module's
# plugin architecture.
#

class DICOMPhilipsRescalePluginClass(DICOMPlugin):
  """ MV specific interpretation code
  """

  def __init__(self,epsilon=0.01):
    super(DICOMPhilipsRescalePluginClass,self).__init__()
    self.loadType = "PhilipsRescaledVolume"

    self.tags['seriesInstanceUID'] = "0020,000E"
    self.tags['seriesDescription'] = "0008,103E"
    self.tags['position'] = "0020,0032"
    self.tags['studyDescription'] = "0008,1030"

    # tags used to rescale the values
    self.philipsVolumeTags = {}
    self.philipsVolumeTags['ScaleIntercept'] = "2005,100d"
    self.philipsVolumeTags['ScaleSlope'] = "2005,100e"
    self.philipsVolumeTags['Manufacturer'] = "0008,0070"

    for tagName,tagVal in self.philipsVolumeTags.iteritems():
      self.tags[tagName] = tagVal

    self.epsilon = epsilon

  def examine(self,fileLists):
    """ Returns a list of DICOMLoadable instances
    corresponding to ways of interpreting the 
    fileLists parameter.
    """
    loadables = []
    allfiles = []
    scalarVolumePlugin = slicer.modules.dicomPlugins['DICOMScalarVolumePlugin']()
    for files in fileLists:
      isPhilips = True
      for f in files:
        manufacturer = slicer.dicomDatabase.fileValue(f, self.tags['Manufacturer'])
        if string.find(manufacturer, 'Philips') == -1:
          isPhilips = False
          break
      if not isPhilips:
        continue
      loadables += scalarVolumePlugin.examine([files])
      loadables[-1].name = loadables[-1].name+' with Philips rescaling applied'

    return loadables

  def load(self,loadable):
    """Load the selection as a scalar volume, but rescale the values
    """

    scalarVolumePlugin = slicer.modules.dicomPlugins['DICOMScalarVolumePlugin']()
    vNode = scalarVolumePlugin.loadFilesWithArchetype(loadable.files, loadable.name)

    if vNode:
      # convert to float pixel type
      intercept = slicer.dicomDatabase.fileValue(loadable.files[0], self.tags['ScaleIntercept'])
      slope = slicer.dicomDatabase.fileValue(loadable.files[0], self.tags['ScaleSlope'])

      rescale = vtk.vtkImageShiftScale()
      rescale.SetShift(-1.*float(intercept))
      rescale.SetScale(1./float(slope))
      rescale.SetOutputScalarTypeToFloat()
      rescale.SetInput(vNode.GetImageData())
      rescale.Update()

      imageData = vtk.vtkImageData()
      imageData.DeepCopy(rescale.GetOutput())

      # Note: the assumption here is that intercept/slope are identical for all
      # slices in the series. According to Tom Chenevert, this is typically the
      # case: "The exception is when there are multiple image types in a series,
      # such as real, imaginary, magnitude and phase images all stored in the
      # series.  But this is not common."
      vNode.SetAndObserveImageData(imageData)

    return vNode

#
# DICOMPhilipsRescalePlugin
#

class DICOMPhilipsRescalePlugin:
  """
  This class is the 'hook' for slicer to detect and recognize the plugin
  as a loadable scripted module
  """
  def __init__(self, parent):
    parent.title = "DICOM Philips Volume Rescale+Import Plugin"
    parent.categories = ["Developer Tools.DICOM Plugins"]
    parent.contributors = ["Andrey Fedorov, BWH"]
    parent.helpText = """
    This plugin addresses an issue with some images produced by Philips
    scanners, where the values stored in PixelData need to be rescaled using
    the information saved in the private tags to obtain quantitative
    measuremenes. The rescale formula is the following:
    QuantitativeValue = [SV-ScInt] / ScSlp,
    where SV = stored DICOM pixel value, ScInt = Scale Intercept =
    (2005,100d), ScSlp = (2005,100e)
    This information was provided by Tom Chenevert, U.Michigan, as part of NCI
    Quantitative Imaging Network Bioinformatics Working Group activities.
    """
    parent.acknowledgementText = """
    This DICOM Plugin was developed by 
    Andrey Fedorov, BWH.
    and was partially funded by NIH grant U01CA151261.
    """

    # don't show this module - it only appears in the DICOM module
    parent.hidden = True

    # Add this extension to the DICOM module's list for discovery when the module
    # is created.  Since this module may be discovered before DICOM itself,
    # create the list if it doesn't already exist.
    try:
      slicer.modules.dicomPlugins
    except AttributeError:
      slicer.modules.dicomPlugins = {}
    slicer.modules.dicomPlugins['DICOMPhilipsRescalePlugin'] = DICOMPhilipsRescalePluginClass

#
#

class DICOMPhilipsRescalePluginWidget:
  def __init__(self, parent = None):
    self.parent = parent
    
  def setup(self):
    # don't display anything for this widget - it will be hidden anyway
    pass

  def enter(self):
    pass
    
  def exit(self):
    pass
