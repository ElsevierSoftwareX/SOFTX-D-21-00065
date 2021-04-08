import os

def set_rootdir(MICS_ROOTDIR):
    os.environ['MICS_ROOTDIR'] = str(MICS_ROOTDIR)

def get_rootdir():
    MICS_ROOTDIR = None
    if 'MICS_ROOTDIR' in os.environ:
        MICS_ROOTDIR = os.environ['MICS_ROOTDIR']
    return(MICS_ROOTDIR)