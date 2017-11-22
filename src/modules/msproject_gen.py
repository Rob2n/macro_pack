#!/usr/bin/env python
# encoding: utf-8

# Only enabled on windows
import sys
import os

if sys.platform == "win32":
    # Download and install pywin32 from https://sourceforge.net/projects/pywin32/files/pywin32/
    import win32com.client # @UnresolvedImport
    import winreg # @UnresolvedImport

import logging
from modules.mp_module import MpModule


class MSProjectGenerator(MpModule):
    """ Module used to generate MS Project file from working dir content"""
    
    def enableVbom(self):
        # Enable writing in macro (VBOM)
        # First fetch the application version
        objProject = win32com.client.Dispatch("MSProject.Application")
        self.version = objProject.Version
        # IT is necessary to exit office or value wont be saved
        objProject.Application.Quit()
        del objProject
        # Next change/set AccessVBOM registry value to 1
        keyval = "Software\\Microsoft\Office\\"  + self.version + "\\Project\\Security"
        logging.info("   [-] Set %s to 1..." % keyval)
        Registrykey = winreg.CreateKey(winreg.HKEY_CURRENT_USER,keyval)
        winreg.SetValueEx(Registrykey,"AccessVBOM",0,winreg.REG_DWORD,1) # "REG_DWORD"
        winreg.CloseKey(Registrykey)
        
    def disableVbom(self):
        # Disable writing in VBA project
        #  Change/set AccessVBOM registry value to 0
        keyval = "Software\\Microsoft\Office\\"  + self.version + "\\Project\\Security"
        logging.info("   [-] Set %s to 0..." % keyval)
        Registrykey = winreg.CreateKey(winreg.HKEY_CURRENT_USER,keyval)
        winreg.SetValueEx(Registrykey,"AccessVBOM",0,winreg.REG_DWORD,0) # "REG_DWORD"
        winreg.CloseKey(Registrykey)
        
    
    def run(self):
        logging.info(" [+] Generating MSProject project...")
        
        self.enableVbom()

        logging.info("   [-] Open MSProject project...")
        # open up an instance of Word with the win32com driver
        MSProject = win32com.client.Dispatch("MSProject.Application")
        project = MSProject.Projects.Add()
        # do the operation in background 
        MSProject.ActiveWindow.Visible = False
        
        logging.info("   [-] Inject VBA...")
        # Read generated files
        for vbaFile in self.getVBAFiles():
            if vbaFile == self.getMainVBAFile():       
                with open (vbaFile, "r") as f:
                    # Add the main macro- into ThisProject part of Word project
                    ProjectModule = project.VBProject.VBComponents("ThisProject")
                    macro=f.read()
                    ProjectModule.CodeModule.AddFromString(macro)
            else: # inject other vba files as modules
                with open (vbaFile, "r") as f:
                    macro=f.read()
                    ProjectModule = project.VBProject.VBComponents.Add(1)
                    ProjectModule.Name = os.path.splitext(os.path.basename(vbaFile))[0]
                    ProjectModule.CodeModule.AddFromString(macro)

        logging.info("   [-] Save MSProject project...")
        pjMPP = 0 # The file was saved with the current version of Microsoft Office MSProject.        
        project.SaveAs(self.outputFilePath,Format = pjMPP)
                    
        
        #MSProject.DisplayAlerts=False
        # Remove Informations
        logging.info("   [-] Remove hidden data and personal info...")
        project.RemovePersonalInformation = True 
        
        # save the project and close
        project.Save()
        project.Close()
        MSProject.Quit()
        # garbage collection
        del MSProject
        self.disableVbom()

        logging.info("   [-] Generated %s file path: %s" % (self.outputFileType, self.outputFilePath))
        
