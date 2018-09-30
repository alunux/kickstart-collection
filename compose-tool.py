import os, platform, subprocess, sys, shutil
import hashlib
import distro
from azure.storage.blob import BlockBlobService, PublicAccess


SET_VER = distro.version()
SET_ARCH = platform.machine()
SET_PROJECT = 'Fedora-Custom-Live'
SET_VOLID = f'{SET_PROJECT}-{SET_VER}'
SET_BOOT = SET_PROJECT
SET_ISO = f'{SET_PROJECT}-{SET_VER}.iso'


class ImageIso:
    def __init__(self, ks, fedoraver=SET_VER, project=SET_PROJECT, volid=SET_VOLID,
                 bootname=SET_BOOT, filename=SET_ISO):
        self.proj = project
        self.volid = volid
        self.filename = filename
        self.fedoraver = str(fedoraver)
        self.bootname = bootname
        self.ks = self.flatten_ks(ks)


    def flatten_ks(self, ks):
        run_ksflatten = f'ksflatten --config {ks} -o flat-main.ks --version F{self.fedoraver}'
        ret = subprocess.run(run_ksflatten, capture_output=True, text=True, shell=True, encoding='utf-8')
        if ret.returncode != 0:
            print(f'Error: {ret.stderr}')
            sys.exit(ret.returncode)
        
        return 'flat-main.ks'


class ComposeEnv:
    def __init__(self, fedoraver=SET_VER, march=SET_ARCH, chrootdir=None):
        self.fedoraver = str(fedoraver)
        self.march = march
        self.chrootdir = chrootdir if chrootdir else f'/var/lib/mock/fedora-{self.fedoraver}-{self.march}/root'
        self.resultdir = f'{self.chrootdir}/var/lmc'
        self.mock = f'mock -r fedora-{self.fedoraver}-{self.march}'


    def setup_builder(self):
        print('Setup builder environment...')
        
        run_init_chroot = f'{self.mock} --rootdir={self.chrootdir} --init'
        ret = subprocess.run(run_init_chroot, capture_output=True, text=True, shell=True, encoding='utf-8')
        if ret.returncode != 0:
            print(f'CMD: {run_init_chroot}')
            print(f'ERROR: {ret.stderr}')
            sys.exit(ret.returncode)

        builder_tools = (
                'lorax-lmc-novirt '
                'vim-minimal '
                'pykickstart '
                'git'
        )

        run_install_deps = f'{self.mock} --rootdir={self.chrootdir} --install {builder_tools}'
        ret = subprocess.run(run_install_deps, capture_output=True, text=True, shell=True, encoding='utf-8')
        if ret.returncode != 0:
            print(f'ERROR: {ret.stderr}')
            sys.exit(ret.returncode)

    
    def compose_iso(self, iso, resultdir=None):
        print('Composing ISO...')

        if not isinstance(iso, ImageIso):
            print('ERROR: need ImageIso object, not {type(iso)}')
            sys.exit(-1)

        if iso.fedoraver != self.fedoraver:
            print(f'ERROR: Fedora version is not matching in ImageIso and ComposeEnv')
            print(f'       ImageIso: Fedora {iso.fedoraver}')
            print(f'       ComposeEnv: Fedora {self.fedoraver}')
            sys.exit(-2)
        
        if os.path.exists(self.chrootdir) != os.path.isdir(self.chrootdir):
            print('ERROR: there is no chroot directory')
            sys.exit(-3)

        shutil.move('flat-main.ks', f'{self.chrootdir}/tmp')

        livemedia_creator = (
            f'livemedia-creator --ks /tmp/{iso.ks} --no-virt --resultdir /var/lmc --project {iso.proj}'
            f' --make-iso --volid {iso.volid} --iso-only --iso-name {iso.filename} --releasever {iso.fedoraver}'
            f' --title {iso.bootname} --macboot'
        )

        run_compose_iso = f'{self.mock} --rootdir={self.chrootdir} --shell --old-chroot "{livemedia_creator}"'
        ret = subprocess.run(run_compose_iso, stderr=subprocess.STDOUT, text=True, shell=True, encoding='utf-8')
        if ret.returncode != 0:
            print(f'ERROR: {ret.stderr}')
            sys.exit(ret.returncode)

        iso_save_dest = resultdir if resultdir else os.getcwd()
        
        if os.path.exists(iso_save_dest) and os.path.isdir(iso_save_dest):
            shutil.copy2(f'{self.resultdir}/{iso.filename}', iso_save_dest)
        else:
            print(f'ERROR: {iso_save_dest} should be a directory and exists')
        
        result = f'{iso_save_dest}/{iso.filename}'
        print(f'ISO has been composed.\nResult: {result}')
        return result


    def clean(self):
        print('Clean builder environment...')
        
        run_init_chroot = f'{self.mock} --rootdir={self.chrootdir} --clean'
        ret = subprocess.run(run_init_chroot, capture_output=True, text=True, shell=True, encoding='utf-8')
        if ret.returncode != 0:
            print(f'ERROR: {ret.stderr}')
            sys.exit(ret.returncode)


class AzureBlobService(BlockBlobService):
    def progress_cb(self, current, total):
        progress = 100 * (float(current)/float(total))
        print(f'Uploading... ({progress:.{2}f} %)', end='\r')


    def upload(self, container, filepath):
        self.create_blob_from_path(container, filepath.rsplit('/')[-1], filepath, progress_callback=self.progress_cb)
        print('Uploaded!')


def find_main_ks(ksdir='.'):
    mainks = 'main.ks'
    if mainks in os.listdir(ksdir) and os.path.isfile(f'{ksdir}/{mainks}'):
        return f'{ksdir}/{mainks}'


def main():
    img = ImageIso(
        ks=find_main_ks('gnome-minimal-spin'),
        fedoraver=28,
        project='Fedora-GNOME-Min-Live',
        volid='Fedora-GNOME-Min-28',
        bootname='Fedora-GNOME-Min-Live',
        filename='Fedora-GNOME-Min-Live-28.iso'
    )

    builder = ComposeEnv(
        fedoraver=28,
        march='x86_64'
    )

    builder.setup_builder()
    iso_result = builder.compose_iso(img)
    builder.clean()
    
    az_acc = os.getenv('AZURE_STORAGE_ACC')
    az_acc_key = os.getenv('AZURE_STORAGE_ACC_KEY')
    az_blob = AzureBlobService(account_name=az_acc, account_key=az_acc_key)
    az_blob.upload('myiso', iso_result)


if __name__ == '__main__':
    main()
